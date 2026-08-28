# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
"""Regression tests: behaviour the documentation promises, pinned.

`test_loader.py` covers whether the parser is correct. This file covers
whether it still does what `docs/index.md` and `README.md` say it does —
a different question, and the one that silently stops being true.

Every assertion here corresponds to a specific written claim. If one fails,
either the code changed or the documentation is now wrong, and both are worth
stopping a merge for. The claim being pinned is named in each docstring so
that a future reader can decide which of the two to fix.

The examples and the benchmark are executed here too. A worked example that no
longer runs is worse than no example: it reads as verified and is not.
"""

from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from camt053_loader_mt940 import __version__, parse_mt940

ROOT = Path(__file__).resolve().parent.parent

STATEMENT = """:20:STMT-REGRESSION-1
:25:COBADEFFXXX/DE89370400440532013000
:28C:42/1
:60F:C260620EUR1000,00
:61:2606210621CR500,00NMSCREF1//SREF1
:86:Payment for invoice 123
:62F:C260621EUR1500,00
"""


@pytest.fixture()
def document():
    return parse_mt940(STATEMENT)


class TestDocumentedShape:
    """The field names `docs/index.md` tells a reader to use."""

    def test_message_type_is_the_camt053_equivalent(self, document) -> None:
        """Documented as "camt.053.001.08"; downstream dispatches on it."""
        assert document.message_type == "camt.053.001.08"

    def test_msg_id_comes_from_tag_20(self, document) -> None:
        assert document.msg_id == "STMT-REGRESSION-1"

    def test_account_is_split_into_iban_and_servicer(self, document) -> None:
        """`:25:` is `BIC/IBAN`; the docs promise both, separated."""
        account = document.statements[0].account
        assert account.iban == "DE89370400440532013000"
        assert account.servicer_bic == "COBADEFFXXX"

    def test_balances_run_opening_to_closing(self, document) -> None:
        balances = document.statements[0].balances
        assert len(balances) >= 2
        assert balances[0].amount == "1000.00"
        assert balances[-1].amount == "1500.00"

    def test_amount_decimal_is_a_decimal_not_a_float(self, document) -> None:
        """The docs tell readers to use this for arithmetic.

        If it ever became a float, every downstream reconciliation would
        acquire rounding error that no test in this package would catch.
        """
        entry = document.statements[0].entries[0]
        assert isinstance(entry.amount_decimal, Decimal)
        assert entry.amount_decimal == Decimal("500.00")

    def test_credit_debit_indicator_uses_iso_codes(self, document) -> None:
        assert (
            document.statements[0].entries[0].credit_debit_indicator == "CRDT"
        )

    def test_tag_86_lands_in_entry_details(self, document) -> None:
        entry = document.statements[0].entries[0]
        assert entry.details
        assert entry.details[0].additional_info == "Payment for invoice 123"

    def test_all_entries_is_a_method(self, document) -> None:
        """Documented with parentheses because it is callable.

        An earlier draft of the documentation had it as a property. Reading
        `document.all_entries` without calling it yields a bound method that
        is truthy and has no length — the mistake fails late and confusingly.
        """
        assert callable(document.all_entries)
        assert len(document.all_entries()) == 1

    def test_entries_with_reason_filters_by_a_given_code(
        self, document
    ) -> None:
        """Takes the reason code as an argument; it is not a bare accessor.

        Calling it with no argument raises TypeError, so documenting it
        without the parameter would send a reader straight into one.
        """
        statement = document.statements[0]
        assert statement.entries_with_reason("AC04") == []
        with pytest.raises(TypeError):
            statement.entries_with_reason()

    def test_to_dict_carries_the_documented_keys(self, document) -> None:
        assert set(document.to_dict()) >= {
            "creation_date_time",
            "message_type",
            "msg_id",
            "statements",
        }


class TestDocumentedLeniency:
    """What the parser accepts, which is the half nobody writes down."""

    def test_tag_20_is_required(self) -> None:
        """The one tag whose absence raises, and the error names it."""
        with pytest.raises(ValueError, match=r":20:"):
            parse_mt940(STATEMENT.replace(":20:STMT-REGRESSION-1\n", ""))

    def test_tag_25_is_optional_and_yields_a_none_account(self) -> None:
        """Pinned deliberately, and documented as a hazard.

        A statement with no `:25:` parses, and its entries belong to an
        account whose IBAN is None. Downstream that reconciles against it
        matches nothing, and the failure surfaces as an unexplained
        reconciliation break rather than as a parse error.

        Tightening this to a hard error is defensible, but it would be a
        breaking change for anyone relying on the leniency — so it should be
        a decision with a version bump behind it, not a quiet edit. This test
        is what forces that.
        """
        document = parse_mt940(
            STATEMENT.replace(":25:COBADEFFXXX/DE89370400440532013000\n", "")
        )
        account = document.statements[0].account
        assert account.iban is None
        assert account.servicer_bic is None
        # And the entries still parse, which is the part that surprises.
        assert len(document.statements[0].entries) == 1

    def test_a_malformed_balance_names_the_tag(self) -> None:
        with pytest.raises(ValueError, match=r":60F:"):
            parse_mt940(STATEMENT.replace(":60F:C260620EUR1000,00", ":60F:X"))

    def test_crlf_parses_identically_to_lf(self) -> None:
        """Documented: a file read on Windows parses the same."""
        assert (
            parse_mt940(STATEMENT.replace("\n", "\r\n")).to_dict()
            == parse_mt940(STATEMENT).to_dict()
        )

    def test_trailing_whitespace_is_tolerated(self) -> None:
        assert (
            parse_mt940(STATEMENT + "\n\n  \n").to_dict()
            == parse_mt940(STATEMENT).to_dict()
        )


class TestShippedArtefactsStillRun:
    """A worked example that no longer runs reads as verified and is not."""

    @pytest.mark.parametrize(
        "script",
        sorted(p.name for p in (ROOT / "examples").glob("*.py")),
    )
    def test_each_example_runs_clean(self, script: str) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "examples" / script)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"examples/{script} exited {result.returncode}:\n{result.stderr}"
        )
        assert result.stdout.strip(), f"examples/{script} printed nothing"

    def test_the_benchmark_runs_and_reports(self) -> None:
        """`--quick` exists so this stays a few seconds in CI."""
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "benches" / "bench_parse_mt940.py"),
                "--quick",
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, result.stderr

        import json

        rows = json.loads(result.stdout)
        assert rows, "the benchmark reported no measurements"
        for row in rows:
            assert row["entries"] > 0
            assert row["entries_per_s"] > 0


class TestVersion:
    def test_the_readme_and_docs_do_not_pin_a_stale_version(self) -> None:
        """A version in prose goes stale the release after it is written.

        This does not forbid mentioning the version — it forbids mentioning a
        *different* one, which is the failure mode that misleads a reader.
        """
        import re

        # Only version mentions attached to this package count. A prose
        # sentence about the versioning policy ("0.1.0 follows 0.0.999") is
        # not a stale version, and flagging it would train people to ignore
        # this test.
        pattern = re.compile(
            r"camt053[-_]loader[-_]mt940[ =@]*[=v ]?(\d+\.\d+\.\d+)"
        )
        for name in ("README.md", "docs/index.md"):
            path = ROOT / name
            if not path.exists():
                continue
            stale = {
                found
                for found in pattern.findall(path.read_text(encoding="utf-8"))
                if found != __version__
            }
            assert not stale, (
                f"{name} names {sorted(stale)}, but the package is "
                f"{__version__}"
            )

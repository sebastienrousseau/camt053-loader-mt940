# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Coverage-guided fuzzing of ``parse_mt940`` with Atheris.

The contract, the same one ``tests/test_fuzz.py`` checks with Hypothesis:
on any text the loader returns a ``ParsedDocument`` whose amounts are
numbers and whose dates exist, or raises ``ValueError``. Any other
exception, or a malformed amount or date in the result, is a crash that
libFuzzer reports and minimises.

An input that starts with ``:`` is parsed as MT940 text as it stands, so
the files in ``fuzz/corpus/`` (real-shaped statements and the inputs of
fixed bugs) are seeds and regression cases at once. Any other input is
decoded into a sequence of MT940 fields.

Run (Linux x86_64, Python 3.12 to 3.14)::

    pip install --require-hashes -r requirements/fuzz.txt
    pip install --no-deps -e .
    python fuzz/fuzz_parse_mt940.py fuzz/corpus -max_total_time=60
"""

import datetime
import sys
from decimal import Decimal

import atheris

with atheris.instrument_imports():
    from camt053.models import Statement

    from camt053_loader_mt940 import parse_mt940

TAGS = ["20", "25", "28C", "60F", "60M", "61", "86", "62F", "62M", "64", "65"]


def _text(data: bytes) -> tuple[str, bool]:
    """The MT940 payload and the ``strict`` flag this input encodes."""
    if data[:1] == b":":
        return data.decode("utf-8", "replace"), True
    fdp = atheris.FuzzedDataProvider(data)
    strict = fdp.ConsumeBool()
    fields = [
        f":{fdp.PickValueInList(TAGS)}:{fdp.ConsumeUnicodeNoSurrogates(48)}"
        for _ in range(fdp.ConsumeIntInRange(0, 16))
    ]
    return "\n".join(fields), strict


def _check_dates(statement: Statement) -> None:
    for balance in statement.balances:
        datetime.date.fromisoformat(balance.date)
    for entry in statement.entries:
        datetime.date.fromisoformat(entry.value_date)
        if entry.booking_date is not None:
            datetime.date.fromisoformat(entry.booking_date)


def test_one_input(data: bytes) -> None:
    """Parse one input and hold the result to the contract."""
    text, strict = _text(data)
    try:
        document = parse_mt940(text, strict=strict)
    except ValueError:
        return
    document.to_dict()
    for statement in document.statements:
        for item in [*statement.balances, *statement.entries]:
            Decimal(item.amount)
        try:
            _check_dates(statement)
        except ValueError as exc:
            raise AssertionError(f"impossible date in output: {exc}") from exc


def main() -> None:
    """Hand the harness to libFuzzer."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

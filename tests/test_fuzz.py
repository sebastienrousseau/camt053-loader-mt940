# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Property-based fuzzing of ``parse_mt940``: the contract on any input.

The loader takes whatever a bank, an SFTP drop or an agent hands it. On any
text it must either return a ``ParsedDocument`` whose money and dates are
well formed, or raise ``ValueError`` naming what was wrong. Anything else
(another exception, an amount that is not a number, a date that does not
exist) is a defect. ``fuzz/fuzz_parse_mt940.py`` holds Atheris to the same
contract in CI.
"""

from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from camt053_loader_mt940 import parse_mt940

FUZZ = settings(max_examples=400, deadline=None)
CORPUS = Path(__file__).resolve().parent.parent / "fuzz" / "corpus"

TAGS = ["20", "25", "28C", "60F", "60M", "61", "86", "62F", "62M", "64", "65"]
YYMMDD = st.text("0123456789", min_size=6, max_size=6)
MMDD = st.one_of(st.just(""), st.text("0123456789", min_size=4, max_size=4))
AMOUNTS = st.text("0123456789,", min_size=1, max_size=8)
BALANCE = st.builds(
    lambda dc, date, ccy, amt: f"{dc}{date}{ccy}{amt}",
    st.sampled_from(["C", "D"]),
    YYMMDD,
    st.sampled_from(["EUR", "GBP"]),
    AMOUNTS,
)
LINE = st.builds(
    lambda v, b, dc, amt, code, rest: f"{v}{b}{dc}{amt}{code}{rest}",
    YYMMDD,
    MMDD,
    st.sampled_from(["C", "D", "RC", "RD"]),
    AMOUNTS,
    st.sampled_from(["NTRF", "NMSC", "S123"]),
    st.text(max_size=20),
)
VALUES = st.one_of(
    st.text(max_size=40),
    BALANCE,
    LINE,
    st.sampled_from(["DE89370400440532013000", "COBADEFFXXX/12345", ""]),
)
HEADER = st.tuples(st.just("20"), st.text(min_size=1, max_size=10)).map(
    lambda t: [t, ("25", "DE89370400440532013000")]
)
BODY = st.lists(
    st.one_of(
        st.tuples(
            st.sampled_from(["60F", "60M", "62F", "62M", "64", "65"]), BALANCE
        ),
        st.tuples(st.just("61"), LINE),
        st.tuples(st.sampled_from(TAGS), VALUES),
    ),
    max_size=10,
)
FIELDS = st.builds(lambda head, body: head + body, HEADER, BODY)


def _payload(fields: list[tuple[str, str]]) -> str:
    return "".join(f":{tag}:{value}\n" for tag, value in fields)


def _is_number(text: str | None) -> bool:
    try:
        Decimal(text or "")
    except InvalidOperation:
        return False
    return True


def _is_date(text: str | None) -> bool:
    if text is None:
        return True
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _check(text: str, strict: bool) -> None:
    try:
        document = parse_mt940(text, strict=strict)
    except ValueError:
        return
    document.to_dict()
    for statement in document.statements:
        for balance in statement.balances:
            assert _is_number(balance.amount), balance.amount
            assert _is_date(balance.date), balance.date
        for entry in statement.entries:
            assert _is_number(entry.amount), entry.amount
            assert _is_date(entry.value_date), entry.value_date
            assert _is_date(entry.booking_date), entry.booking_date


@FUZZ
@given(text=st.text(max_size=400), strict=st.booleans())
def test_arbitrary_text(text: str, strict: bool) -> None:
    _check(text, strict)


@FUZZ
@given(fields=FIELDS, strict=st.booleans())
def test_mt940_shaped_fields(
    fields: list[tuple[str, str]], strict: bool
) -> None:
    _check(_payload(fields), strict)


@pytest.mark.parametrize(
    "seed", sorted(p.name for p in CORPUS.iterdir()), ids=str
)
@pytest.mark.parametrize("strict", [True, False])
def test_the_fuzz_corpus_replays(seed: str, strict: bool) -> None:
    """Every seed and fixed-bug input in fuzz/corpus, on every run."""
    _check((CORPUS / seed).read_text(encoding="utf-8"), strict)

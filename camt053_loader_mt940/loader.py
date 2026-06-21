# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""MT940 → camt.053 ParsedDocument loader.

The MT940 grammar handled here is the common-denominator subset
shipped by EU and UK commercial banks:

* ``:20:`` Transaction reference number
* ``:25:`` Account identification (optional BIC prefix + account)
* ``:28C:`` Statement / sequence number
* ``:60F:`` / ``:60M:`` Opening balance (Final / intermediary)
* ``:61:`` Statement line (one per booked entry, repeatable)
* ``:86:`` Information to account owner (attaches to the prior ``:61:``)
* ``:62F:`` / ``:62M:`` Closing balance
* ``:64:`` Closing available balance

Bank-specific extensions inside ``:86:`` (e.g. Deutsche Bank's
``?20``/``?30``/``?32`` GVC fields) are surfaced verbatim on the
entry's :class:`camt053.models.TransactionDetails.additional_info`
field; the loader does not attempt to interpret them.

Reversal detection: an MT940 ``:61:`` line whose debit/credit
indicator is ``RD`` (reversal debit) or ``RC`` (reversal credit) is
mapped to an :class:`~camt053.models.Entry` with
``reversal_indicator=True``.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from camt053.models import (
    Account,
    Balance,
    Entry,
    ParsedDocument,
    Statement,
    TransactionDetails,
)

__all__ = ["parse_mt940"]


# ─── Mapping tables ──────────────────────────────────────────────────────────

# MT940 debit/credit indicators on :61: lines:
# C  = Credit, D  = Debit
# RC = Reversal of credit, RD = Reversal of debit
_DC_TO_CAMT = {
    "C": ("CRDT", False),
    "D": ("DBIT", False),
    "RC": ("CRDT", True),
    "RD": ("DBIT", True),
}

# Balance type mapping. MT940 distinguishes Final vs Mid-statement
# (intermediate); camt.053 uses single OPBD/CLBD codes plus
# OPAV/CLAV for available balances.
_BALANCE_TAG_TO_TYPE = {
    "60F": "OPBD",
    "60M": "OPBD",
    "62F": "CLBD",
    "62M": "CLBD",
    "64": "CLAV",
    "65": "FWAV",
}


# ─── Regex helpers ───────────────────────────────────────────────────────────

# A field starts with :tag: at the beginning of a line. Tags are 2-3
# chars, optionally followed by a single letter (e.g. 60F, 28C).
_FIELD_HEAD_RE = re.compile(r"^:(\d{2}[A-Z]?):", re.MULTILINE)

# :60F:C240621EUR1000,00
#       ^DC ^YYMMDD ^CCY ^Amount
_BALANCE_RE = re.compile(
    r"^(?P<dc>C|D)(?P<date>\d{6})(?P<ccy>[A-Z]{3})(?P<amt>[\d,]+)$"
)

# :61:2406210621D1000,00N123ABC//REF1
#     ^vYYMMDD ^bMMDD (opt) ^DC ^Amt (comma-decimal)
#     ^TxCode ^Ref [+ opt //Customer ref]
_LINE_RE = re.compile(
    r"^(?P<vdate>\d{6})"
    r"(?P<bdate>\d{4})?"
    r"(?P<dc>RC|RD|C|D)"
    r"(?P<fund_code>[A-Z])?"
    r"(?P<amt>[\d,]+)"
    r"(?P<txcode>[A-Z][A-Z0-9]{3})"
    r"(?P<rest>.*)$"
)


# ─── Tokeniser ──────────────────────────────────────────────────────────────


def _iter_fields(text: str) -> Iterator[tuple[str, str]]:
    """Yield ``(tag, value)`` pairs from an MT940 payload.

    Values may span multiple lines; everything after a ``:tag:`` head
    up to (but not including) the next ``:tag:`` head is the value,
    with the leading tag stripped and trailing whitespace normalised.
    """
    matches = list(_FIELD_HEAD_RE.finditer(text))
    for index, match in enumerate(matches):
        tag = match.group(1)
        value_start = match.end()
        value_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )
        value = text[value_start:value_end].strip()
        yield tag, value


# ─── Field parsers ──────────────────────────────────────────────────────────


def _parse_balance(value: str, tag: str) -> Balance:
    """Parse a balance field (:60F: / :60M: / :62F: / :62M: / :64: / :65:)."""
    match = _BALANCE_RE.match(value)
    if not match:
        raise ValueError(f"Malformed balance field :{tag}:{value!r}")
    return Balance(
        type_code=_BALANCE_TAG_TO_TYPE[tag],
        amount=match.group("amt").replace(",", "."),
        currency=match.group("ccy"),
        credit_debit_indicator=("CRDT" if match.group("dc") == "C" else "DBIT"),
        date=_format_yymmdd(match.group("date")),
    )


def _parse_entry(value: str) -> Entry:
    """Parse a :61: statement line into an :class:`~camt053.models.Entry`."""
    # Reference details after the amount/code can be split on `//`
    # (bank ref // customer ref). Both halves are optional.
    match = _LINE_RE.match(value.replace("\n", ""))
    if not match:
        raise ValueError(f"Malformed :61: statement line {value!r}")
    indicator, is_reversal = _DC_TO_CAMT[match.group("dc")]
    rest = match.group("rest") or ""
    bank_ref, _, customer_ref = rest.partition("//")
    return Entry(
        reference=bank_ref.strip() or None,
        amount=match.group("amt").replace(",", "."),
        credit_debit_indicator=indicator,
        status="BOOK",
        booking_date=_format_yymmdd_with_year_hint(
            match.group("bdate"), match.group("vdate")
        ),
        value_date=_format_yymmdd(match.group("vdate")),
        account_servicer_ref=customer_ref.strip() or None,
        reversal_indicator=is_reversal,
    )


def _parse_account(value: str) -> Account:
    """Parse a :25: account-identification field.

    The field is ``[BIC/]<account>`` where the BIC prefix is optional
    and separated by a forward slash.
    """
    bic: str | None
    account: str
    if "/" in value:
        bic, _, account = value.partition("/")
        bic = bic.strip() or None
        account = account.strip()
    else:
        bic = None
        account = value.strip()
    # IBANs are 15-34 chars and start with two letters + two digits;
    # anything else is treated as a proprietary identifier.
    is_iban = bool(re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$", account))
    return Account(
        iban=account if is_iban else None,
        other_id=None if is_iban else account or None,
        servicer_bic=bic,
    )


def _format_yymmdd(value: str) -> str:
    """Format a 6-char ``YYMMDD`` date as ISO ``YYYY-MM-DD``.

    Years are interpreted with a sliding window: 00-79 → 20YY, 80-99 →
    19YY. This matches MT940 industry practice and is correct for any
    real statement date in the 1980-2079 range.
    """
    year = int(value[0:2])
    century = 2000 if year < 80 else 1900
    return f"{century + year:04d}-{value[2:4]}-{value[4:6]}"


def _format_yymmdd_with_year_hint(
    booking_mmdd: str | None,
    value_yymmdd: str,
) -> str | None:
    """Format the booking date, borrowing the year from the value date.

    MT940 :61: lines carry a 6-char value date (YYMMDD) and an
    optional 4-char booking date (MMDD); the booking date inherits
    its year from the value date.
    """
    if booking_mmdd is None:
        return None
    return _format_yymmdd(value_yymmdd[0:2] + booking_mmdd)


# ─── Top-level parser ───────────────────────────────────────────────────────


def parse_mt940(text: str) -> ParsedDocument:
    """Parse an MT940 payload into a :class:`~camt053.models.ParsedDocument`.

    Args:
        text: The MT940 payload as a string. Trailing whitespace and
            CRLF/LF differences are tolerated.

    Returns:
        A :class:`~camt053.models.ParsedDocument` whose
        ``message_type`` is ``"camt.053.001.08"`` (the closest direct
        camt.053 equivalent of an MT940 final-statement message).

    Raises:
        ValueError: If a required field is missing or a balance /
            statement line does not match the expected format. The
            error message identifies the offending field.
    """
    statement = Statement()
    msg_id: str | None = None
    last_entry: Entry | None = None

    for tag, value in _iter_fields(text):
        if tag == "20":
            msg_id = value or None
        elif tag == "25":
            statement.account = _parse_account(value)
        elif tag == "28C":
            statement.electronic_seq_nb = value
            statement.id = value
        elif tag in {"60F", "60M", "62F", "62M", "64", "65"}:
            statement.balances.append(_parse_balance(value, tag))
        elif tag == "61":
            entry = _parse_entry(value)
            statement.entries.append(entry)
            last_entry = entry
        elif tag == "86":
            _attach_additional_info(last_entry, value)
        # Unknown tags are silently ignored so future SWIFT additions
        # do not break parsing; the loader follows Postel's law here.

    if msg_id is None:
        raise ValueError("MT940 payload missing required :20: reference")

    return ParsedDocument(
        message_type="camt.053.001.08",
        msg_id=msg_id,
        statements=[statement],
    )


def _attach_additional_info(entry: Entry | None, value: str) -> None:
    """Attach :86: free-form info to the most recent entry as a detail."""
    if entry is None:
        # An :86: with no preceding :61: is malformed in practice but
        # not actively harmful; ignore it rather than aborting the
        # whole parse.
        return
    entry.details.append(TransactionDetails(additional_info=value))

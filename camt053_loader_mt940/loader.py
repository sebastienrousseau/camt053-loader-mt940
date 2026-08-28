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


# ─── Errors ─────────────────────────────────────────────────────────────────


class MissingMandatoryFieldError(ValueError):
    """A tag the MT940 specification requires was absent.

    Subclasses :class:`ValueError` deliberately. Every error this module
    raised before this class existed was a bare ``ValueError``, and callers
    already catch that; narrowing the type would have been a second breaking
    change on top of the one that matters.

    Attributes:
        tag: The MT940 tag at fault, without colons — ``"25"``.
        description: Its name in the specification.
    """

    def __init__(self, tag: str, description: str, problem: str) -> None:
        """Build the error.

        Args:
            tag: The MT940 tag at fault, without colons — ``"25"``.
            description: Its name in the specification.
            problem: What was wrong with it, as a clause completing
                "...and {problem}" — ``"it is absent"``.
        """
        self.tag = tag
        self.description = description
        super().__init__(
            f"Tag :{tag}: ({description}) is mandatory under the MT940 "
            f"specification, and {problem}. The resulting statement could "
            f"not be reconciled to an account. Pass strict=False if the "
            f"account is known from outside the file."
        )


#: Tags rejected under ``strict=True`` when absent *or* empty, as
#: ``(tag, description)``.
#:
#: Two traps are worth recording, because the obvious implementation falls
#: into both. Presence cannot be read from the assembled model —
#: ``Statement()`` starts with an empty ``Account()`` rather than ``None``,
#: so ``statement.account is not None`` is true whether or not ``:25:`` was
#: ever present, and a check written that way passes its own tests while
#: rejecting nothing. And presence of the tag is not enough either: a bare
#: ``:25:`` with no value parses to an account carrying no identifier at
#: all, which is the same unreconcilable statement by a different route.
#:
#: Only ``:25:`` is listed. ``:28C:`` (statement number), ``:60F:``
#: (opening balance) and ``:62F:`` (closing balance) are equally mandatory
#: under the MT940 specification, and are equally mandatory in the camt.053
#: model this loader targets — ``<Stmt><Id>`` is [1..1] and ``<Stmt><Bal>``
#: is [1..n]. All three are still accepted when absent, producing a
#: statement with a ``None`` id or a short balance list.
#:
#: That is a known gap, recorded here rather than left to be rediscovered.
#: Closing it is a matter of adding rows, but it widens the breaking change
#: beyond the one that was asked for, so it waits for a decision.
_MANDATORY_UNDER_STRICT: tuple[tuple[str, str], ...] = (
    ("25", "Account Identification"),
)


# ─── Top-level parser ───────────────────────────────────────────────────────


def parse_mt940(text: str, *, strict: bool = True) -> ParsedDocument:
    """Parse an MT940 payload into a :class:`~camt053.models.ParsedDocument`.

    Args:
        text: The MT940 payload as a string. Trailing whitespace and
            CRLF/LF differences are tolerated.
        strict: Reject a payload whose ``:25:`` is absent, empty, or
            carries a servicer BIC with no account number. Defaults to
            ``True``. Pass ``False`` only when the account is known from
            outside the file — a filename, or the SFTP folder it landed
            in — and will be attached afterwards.

    Returns:
        A :class:`~camt053.models.ParsedDocument` whose
        ``message_type`` is ``"camt.053.001.08"`` (the closest direct
        camt.053 equivalent of an MT940 final-statement message).

    Raises:
        MissingMandatoryFieldError: If ``:25:`` is absent or identifies
            no account, and ``strict`` is ``True``. A subclass of
            :class:`ValueError`.
        ValueError: If ``:20:`` is absent, or a balance or statement line
            does not match the expected format. The message identifies
            the offending tag.

    Note:
        ``strict`` currently governs ``:25:`` only. ``:28C:``, ``:60F:``
        and ``:62F:`` are equally mandatory under the MT940 specification
        and are still accepted when absent; that is a known gap rather
        than a decision, and widening the check is a one-line change to
        :data:`_MANDATORY_UNDER_STRICT`.
    """
    statement = Statement()
    msg_id: str | None = None
    last_entry: Entry | None = None
    seen: set[str] = set()

    for tag, value in _iter_fields(text):
        seen.add(tag)
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

    if strict:
        for tag, description in _MANDATORY_UNDER_STRICT:
            if tag not in seen:
                raise MissingMandatoryFieldError(
                    tag, description, "it is absent"
                )
        # A bare ``:25:`` is present but identifies nothing. The BIC alone
        # does not count: it names the servicer, not the account, and a
        # statement that says which bank but not which account reconciles
        # against just as little as one that says neither.
        account = statement.account
        if account is None or not (account.iban or account.other_id):
            raise MissingMandatoryFieldError(
                "25",
                "Account Identification",
                "it carries no account number",
            )

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

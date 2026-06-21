# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Tests for the camt053-loader-mt940 loader."""

from __future__ import annotations

import pytest

from camt053_loader_mt940 import __version__, parse_mt940


def _minimal_mt940() -> str:
    """Return a minimal valid MT940 payload covering every supported tag."""
    return (
        ":20:REF-1\n"
        ":25:COBADEFFXXX/DE89370400440532013000\n"
        ":28C:42/1\n"
        ":60F:C260620EUR1000,00\n"
        ":61:2606210621CR500,00NMSCREF1//CREF1\n"
        ":86:Customer payment\n"
        ":61:2606220622D200,00NMSCREF2//CREF2\n"
        ":62F:C260622EUR1300,00\n"
        ":64:C260622EUR1300,00\n"
    )


def test_version_exposed() -> None:
    """The package exposes a non-empty semantic-style version string."""
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 2


def test_minimum_payload_parses_to_document() -> None:
    """A minimal MT940 produces a ParsedDocument with one statement."""
    doc = parse_mt940(_minimal_mt940())
    assert doc.message_type == "camt.053.001.08"
    assert doc.msg_id == "REF-1"
    assert len(doc.statements) == 1


def test_account_parsing_with_bic_prefix() -> None:
    """:25: with BIC/account splits into servicer_bic + iban."""
    doc = parse_mt940(_minimal_mt940())
    account = doc.statements[0].account
    assert account.servicer_bic == "COBADEFFXXX"
    assert account.iban == "DE89370400440532013000"
    assert account.other_id is None


def test_account_parsing_without_bic_prefix() -> None:
    """:25: without BIC puts the value in iban if it looks IBAN-like."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":62F:C260620EUR1000,00\n"
    )
    doc = parse_mt940(mt940)
    assert doc.statements[0].account.iban == "DE89370400440532013000"
    assert doc.statements[0].account.servicer_bic is None


def test_proprietary_account_id_falls_through_to_other_id() -> None:
    """A non-IBAN account ID is stored on other_id, not iban."""
    mt940 = (
        ":20:REF\n"
        ":25:1234567890\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":62F:C260620EUR1000,00\n"
    )
    doc = parse_mt940(mt940)
    assert doc.statements[0].account.iban is None
    assert doc.statements[0].account.other_id == "1234567890"


def test_balances_carry_type_codes_and_amounts() -> None:
    """OPBD / CLBD / CLAV balances are extracted with type codes intact."""
    doc = parse_mt940(_minimal_mt940())
    balances = doc.statements[0].balances
    types = [b.type_code for b in balances]
    assert types == ["OPBD", "CLBD", "CLAV"]
    assert balances[0].amount == "1000.00"
    assert balances[0].currency == "EUR"
    assert balances[0].credit_debit_indicator == "CRDT"
    assert balances[0].date == "2026-06-20"


def test_intermediate_balance_tags_map_to_opbd_clbd() -> None:
    """:60M: / :62M: intermediate balances map to OPBD / CLBD."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60M:C260620EUR1000,00\n"
        ":62M:C260620EUR1000,00\n"
    )
    doc = parse_mt940(mt940)
    types = [b.type_code for b in doc.statements[0].balances]
    assert types == ["OPBD", "CLBD"]


def test_forward_available_balance_tag_65_recognised() -> None:
    """:65: forward-available-balance gets FWAV type code."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":62F:C260620EUR1000,00\n"
        ":65:C260623EUR1200,00\n"
    )
    doc = parse_mt940(mt940)
    types = [b.type_code for b in doc.statements[0].balances]
    assert types[-1] == "FWAV"


def test_entries_carry_amount_dc_and_dates() -> None:
    """Each :61: line becomes an Entry with parsed amount and dates."""
    doc = parse_mt940(_minimal_mt940())
    entries = doc.statements[0].entries
    assert len(entries) == 2
    assert entries[0].amount == "500.00"
    assert entries[0].credit_debit_indicator == "CRDT"
    assert entries[0].value_date == "2026-06-21"
    assert entries[0].booking_date == "2026-06-21"
    # SWIFT MT940 :61: line: `C`=credit, `R`=funds-code, `500,00`=amount,
    # `NMSC`=transaction-type code, `REF1`=bank ref, `CREF1`=customer ref.
    assert entries[0].reference == "REF1"
    assert entries[0].account_servicer_ref == "CREF1"
    assert entries[1].credit_debit_indicator == "DBIT"
    assert entries[1].amount == "200.00"


def test_reversal_indicators_rd_rc_set_flag() -> None:
    """Debit/credit codes RD and RC set reversal_indicator=True."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":61:2606210621RD100,00NMSCREVD//CR-D\n"
        ":61:2606210621RC50,00NMSCREVC//CR-C\n"
        ":62F:C260621EUR1050,00\n"
    )
    doc = parse_mt940(mt940)
    entries = doc.statements[0].entries
    assert [e.reversal_indicator for e in entries] == [True, True]
    assert [e.credit_debit_indicator for e in entries] == ["DBIT", "CRDT"]


def test_tag_86_attaches_as_additional_info_on_last_entry() -> None:
    """:86: attaches to the most recent :61: as a TransactionDetails row."""
    doc = parse_mt940(_minimal_mt940())
    first_entry = doc.statements[0].entries[0]
    assert len(first_entry.details) == 1
    assert first_entry.details[0].additional_info == "Customer payment"


def test_orphan_tag_86_without_preceding_entry_is_ignored() -> None:
    """:86: before any :61: is silently ignored (Postel's law)."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":86:Orphan info\n"
        ":62F:C260620EUR1000,00\n"
    )
    doc = parse_mt940(mt940)
    # Parse succeeds, no entries, no crash.
    assert doc.statements[0].entries == []


def test_missing_tag_20_raises() -> None:
    """A payload without :20: raises ValueError with a clear message."""
    mt940 = (
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":62F:C260620EUR1000,00\n"
    )
    with pytest.raises(ValueError, match=":20:"):
        parse_mt940(mt940)


def test_malformed_balance_raises_with_tag() -> None:
    """A malformed balance field raises ValueError mentioning the tag."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:JUNK\n"
        ":62F:C260620EUR1000,00\n"
    )
    with pytest.raises(ValueError, match="60F"):
        parse_mt940(mt940)


def test_malformed_statement_line_raises() -> None:
    """A :61: line that doesn't match the grammar raises ValueError."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":61:GARBAGE\n"
        ":62F:C260620EUR1000,00\n"
    )
    with pytest.raises(ValueError, match=":61:"):
        parse_mt940(mt940)


def test_unknown_tags_are_ignored() -> None:
    """Unknown :tag: values (e.g. :13D:) don't break parsing."""
    mt940 = (
        ":20:REF\n"
        ":13D:2606210000+0000\n"  # creation timestamp, unsupported
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":62F:C260620EUR1000,00\n"
    )
    doc = parse_mt940(mt940)
    assert doc.msg_id == "REF"


def test_19xx_year_window_for_old_dates() -> None:
    """YY ≥ 80 maps to 19YY (sliding-window convention)."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C950620EUR1000,00\n"
        ":62F:C950620EUR1000,00\n"
    )
    doc = parse_mt940(mt940)
    assert doc.statements[0].balances[0].date == "1995-06-20"


def test_entry_without_booking_date_only_carries_value_date() -> None:
    """A :61: line with no MMDD booking date leaves booking_date None."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":61:260621CR100,00NMSCREF//CR\n"
        ":62F:C260621EUR1100,00\n"
    )
    doc = parse_mt940(mt940)
    entry = doc.statements[0].entries[0]
    assert entry.value_date == "2026-06-21"
    assert entry.booking_date is None


def test_entry_without_customer_ref_leaves_servicer_ref_none() -> None:
    """A :61: line without `//CustomerRef` leaves account_servicer_ref None."""
    mt940 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":61:2606210621CR100,00NMSCREF\n"
        ":62F:C260621EUR1100,00\n"
    )
    doc = parse_mt940(mt940)
    entry = doc.statements[0].entries[0]
    assert entry.reference == "REF"
    assert entry.account_servicer_ref is None


def test_account_with_trailing_slash_only_bic_returns_empty_other_id() -> None:
    """A :25: like ``BIC/`` yields a BIC and a None account id."""
    mt940 = (
        ":20:REF\n"
        ":25:COBADEFFXXX/\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":62F:C260620EUR1000,00\n"
    )
    doc = parse_mt940(mt940)
    assert doc.statements[0].account.servicer_bic == "COBADEFFXXX"
    assert doc.statements[0].account.iban is None
    assert doc.statements[0].account.other_id is None


def test_empty_reference_on_tag_20_falls_through_to_none() -> None:
    """A :20: with empty value still raises (msg_id is required)."""
    mt940 = (
        ":20:\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":60F:C260620EUR1000,00\n"
        ":62F:C260620EUR1000,00\n"
    )
    with pytest.raises(ValueError, match=":20:"):
        parse_mt940(mt940)

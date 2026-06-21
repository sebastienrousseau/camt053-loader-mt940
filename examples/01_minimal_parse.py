# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Minimal example: parse a tiny MT940 payload and inspect the result.

Run with ``python examples/01_minimal_parse.py``.
"""

from camt053_loader_mt940 import parse_mt940

MT940 = """:20:STMT-DEMO-1
:25:COBADEFFXXX/DE89370400440532013000
:28C:42/1
:60F:C260620EUR1000,00
:61:2606210621CR500,00NMSCREF1//CREF1
:86:Customer payment for invoice 123
:62F:C260621EUR1500,00
"""


def main() -> None:
    """Parse the demo MT940 and print a one-line summary."""
    document = parse_mt940(MT940)
    statement = document.statements[0]
    print(f"msg_id        : {document.msg_id}")
    print(f"message_type  : {document.message_type}")
    print(f"account IBAN  : {statement.account.iban}")
    print(f"servicer BIC  : {statement.account.servicer_bic}")
    print(f"opening bal   : {statement.balances[0].amount}")
    print(f"closing bal   : {statement.balances[-1].amount}")
    print(f"entries       : {len(statement.entries)}")
    for entry in statement.entries:
        info = (
            entry.details[0].additional_info if entry.details else "(no info)"
        )
        print(
            f"  {entry.credit_debit_indicator} "
            f"{entry.amount} ref={entry.reference} :86:={info!r}"
        )


if __name__ == "__main__":
    main()

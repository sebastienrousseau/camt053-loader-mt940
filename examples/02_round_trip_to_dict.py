# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Parse MT940 and emit JSON via the camt053 model's ``to_dict``.

This example shows that an MT940-sourced document is shape-compatible
with a camt.053-XML-sourced document: every downstream consumer in
the suite (writer, validator, MCP server, LSP server) sees the same
data structure regardless of where the bytes came from.

Run with ``python examples/02_round_trip_to_dict.py``.
"""

import json

from camt053_loader_mt940 import parse_mt940

MT940 = """:20:STMT-DEMO-2
:25:DE89370400440532013000
:28C:1/1
:60F:C260620EUR1000,00
:61:2606210621D250,00NMSCDIRECTDEBIT//INV-77
:86:Mietzahlung
:61:2606220622RC50,00NMSCRETURNED//RET-77
:86:Returned by debtor
:62F:C260622EUR800,00
"""


def main() -> None:
    """Parse the demo MT940 and dump its dict shape as JSON."""
    document = parse_mt940(MT940)
    print(json.dumps(document.to_dict(), indent=2))


if __name__ == "__main__":
    main()

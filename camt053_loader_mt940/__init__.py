# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""MT940 → camt.053 loader for the camt053 suite.

SWIFT MT940 is the legacy customer-statement message that banks have
shipped for decades and that ISO 20022 camt.053 replaces. MT940 is
scheduled for retirement in November 2028, leaving a 2-year window
where SMEs, ERPs, and treasury middleware still produce MT940 but
downstream tooling expects camt.053.

This package bridges that gap: pass an MT940 text payload and get
back a :class:`camt053.models.ParsedDocument` with the same shape as
:func:`camt053.parse.statement_parser.parse_document`. Downstream
camt053 consumers (the writer, validator, reversal builder, MCP and
LSP servers) then work without further changes.
"""

from camt053_loader_mt940.loader import parse_mt940

__version__ = "0.0.9"

__all__ = ["parse_mt940", "__version__"]

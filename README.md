# camt053-loader-mt940: MT940 → camt.053 loader

<p align="center">
  <img src="https://cloudcdn.pro/camt053/v1/logos/camt053.svg" alt="camt053-loader-mt940 logo" width="128" />
</p>

[![PyPI Version][pypi-badge]][07]
[![Python Versions][python-versions-badge]][07]
[![License][license-badge]][01]
[![Tests][tests-badge]][tests-url]
[![Quality][quality-badge]][quality-url]

**Convert legacy SWIFT MT940 bank statements into the same
[`camt053`][core] data model as native camt.053 input.** A single
`parse_mt940(text)` call returns a `camt053.models.ParsedDocument`,
ready for every downstream consumer in the suite (writer, validator,
reversal builder, MCP and LSP servers).

> **Latest release: v0.0.1.** SWIFT MT940 is scheduled for retirement
> in **November 2028**. This loader bridges the 2-year window where
> banks still produce MT940 but downstream tooling expects camt.053.

## Contents

- [Overview](#overview)
- [Install](#install)
- [Quick Start](#quick-start)
- [Supported Fields](#supported-fields)
- [Examples](#examples)
- [Development](#development)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

## Overview

`camt053-loader-mt940` is a small, focused companion to the
[`camt053`][core] ISO 20022 cash-management library. It does one thing
well: parse the common-denominator MT940 grammar shipped by EU and UK
commercial banks, and hand back the same `ParsedDocument` shape that
the camt.053 XML parser produces. The rest of the suite then works
unchanged.

This package is part of the **camt053 suite**, a set of independently
installable packages that share the `camt053.services` layer:

- [`camt053`][core] - the core library (CLI + REST API)
- [`camt053-mcp`][mcp] - the **Model Context Protocol** server for AI agents
- [`camt053-lsp`][lsp] - the **Language Server Protocol** server for editors
- [`camt053-writer-xlsx`][writer] - Excel `.xlsx` writer for parsed statements
- `camt053-loader-mt940` - this package, the MT940 loader

## Install

`camt053-loader-mt940` runs on macOS, Linux, and Windows and requires
**Python 3.10+** and **pip**. It pulls in `camt053` automatically and
has no other runtime dependencies.

```bash
pip install camt053-loader-mt940
```

## Quick Start

```python
from camt053_loader_mt940 import parse_mt940

mt940 = """:20:STMT-REF-1
:25:COBADEFFXXX/DE89370400440532013000
:28C:42/1
:60F:C260620EUR1000,00
:61:2606210621CR500,00NMSCREF1//CREF1
:86:Customer payment for invoice 123
:62F:C260621EUR1500,00
"""

document = parse_mt940(mt940)

print(document.msg_id)
# STMT-REF-1
print(document.statements[0].account.iban)
# DE89370400440532013000
print(document.statements[0].balances[0].amount)
# 1000.00
```

That's a `camt053.models.ParsedDocument`, ready to feed to
[`camt053-writer-xlsx`][writer] (Excel output), the camt053 REST API,
or any other consumer in the suite.

## Supported Fields

| Tag | Meaning | Mapped to |
| :--- | :--- | :--- |
| `:20:` | Transaction reference number | `ParsedDocument.msg_id` |
| `:25:` | Account identification (`BIC/account` or `account`) | `Statement.account` (IBAN or proprietary `other_id` + optional `servicer_bic`) |
| `:28C:` | Statement / sequence number | `Statement.id` + `Statement.electronic_seq_nb` |
| `:60F:` / `:60M:` | Opening balance (Final / intermediary) | `Balance` with `type_code="OPBD"` |
| `:61:` | Statement line (booked entry) | `Entry` with `amount`, `credit_debit_indicator`, `value_date`, `booking_date`, `reference`, `account_servicer_ref` |
| `:86:` | Information to account owner | `TransactionDetails.additional_info` attached to the preceding entry |
| `:62F:` / `:62M:` | Closing balance | `Balance` with `type_code="CLBD"` |
| `:64:` | Closing available balance | `Balance` with `type_code="CLAV"` |
| `:65:` | Forward available balance | `Balance` with `type_code="FWAV"` |

### Reversal detection

A `:61:` line whose debit/credit indicator is **`RD`** (reversal of
debit) or **`RC`** (reversal of credit) becomes an `Entry` with
`reversal_indicator=True`. Direct support for SEPA / NACHA / CBPR+
return-reason mapping is on the v0.0.2 roadmap.

### Unknown fields

Unrecognised tags (e.g. `:13D:` creation timestamp, bank-specific
extensions) are **silently ignored**, so future SWIFT additions do
not break parsing. This follows Postel's law: be liberal in what you
accept.

### Out of scope

- **MT941 / MT942** intraday-balance and intermediate-statement messages.
  Add a separate loader if you need them; the data model supports it.
- **Bank-specific `:86:` sub-fields** (e.g. Deutsche Bank's
  `?20`/`?30`/`?32` GVC codes). The value is preserved verbatim in
  `additional_info`; downstream tooling can parse it if needed.
- **MT940-encrypted payloads.** Decrypt upstream before passing to
  this loader.

## Examples

Two runnable examples live in `examples/`:

- [`01_minimal_parse.py`](examples/01_minimal_parse.py) - the
  smallest valid MT940 + parse + inspect.
- [`02_round_trip_to_xlsx.py`](examples/02_round_trip_to_xlsx.py) -
  MT940 in, Excel `.xlsx` out (requires `camt053-writer-xlsx`).

Both are exercised in CI on every commit.

## Development

```bash
git clone https://github.com/sebastienrousseau/camt053-loader-mt940
cd camt053-loader-mt940
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                          # 100% line + branch coverage gate
interrogate camt053_loader_mt940  # 100% docstring gate
mypy camt053_loader_mt940       # strict
```

## License

Licensed under the [Apache License, Version 2.0][01]. Any contribution
submitted for inclusion shall be licensed as above, without additional
terms.

## Contributing

Contributions are welcome. Open an issue or PR on
[the repository](https://github.com/sebastienrousseau/camt053-loader-mt940).

## Acknowledgements

Built on the [`camt053`][core] ISO 20022 Bank Statement library. The
MT940 grammar follows the SWIFT User Handbook MT940 specification and
the common-denominator subset shipped by major EU and UK commercial
banks.

[01]: https://opensource.org/license/apache-2-0/
[07]: https://pypi.org/project/camt053-loader-mt940/
[core]: https://github.com/sebastienrousseau/camt053
[mcp]: https://github.com/sebastienrousseau/camt053-mcp
[lsp]: https://github.com/sebastienrousseau/camt053-lsp
[writer]: https://github.com/sebastienrousseau/camt053-writer-xlsx
[pypi-badge]: https://img.shields.io/pypi/v/camt053-loader-mt940.svg?style=for-the-badge
[python-versions-badge]: https://img.shields.io/pypi/pyversions/camt053-loader-mt940.svg?style=for-the-badge
[license-badge]: https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge
[tests-badge]: https://img.shields.io/github/actions/workflow/status/sebastienrousseau/camt053-loader-mt940/ci.yml?branch=main&label=Tests&style=for-the-badge
[tests-url]: https://github.com/sebastienrousseau/camt053-loader-mt940/actions/workflows/ci.yml
[quality-badge]: https://img.shields.io/badge/Coverage-100%25-brightgreen?style=for-the-badge
[quality-url]: https://github.com/sebastienrousseau/camt053-loader-mt940/actions/workflows/ci.yml

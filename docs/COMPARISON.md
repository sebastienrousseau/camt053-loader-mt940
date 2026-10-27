<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Comparison

What this compares: Python libraries that read SWIFT MT940. Checked on
2026-10-20 against `camt053-loader-mt940` at this commit and
[`mt-940`](https://pypi.org/project/mt-940/) 5.1.1, from the released
wheel's source and metadata.

| | camt053-loader-mt940 | mt-940 5.1.1 |
| :--- | :--- | :--- |
| Entry point | `parse_mt940(text, *, strict=True)` | `mt940.parse(src, ...)`, `mt940.parse_statements(src, ...)` |
| Input | `str` | file handle, filename, `str` or `bytes` |
| Output | `camt053.models.ParsedDocument`, the type camt053's camt.053 XML parser returns | `mt940.models.Transactions`, a sequence of `Transaction` |
| Multi-statement files | One `Statement` per `:20:`, always | `parse` merges into one `Transactions`; `parse_statements` returns one per `:20:` |
| Missing `:25:` | Rejected by default (`MissingMandatoryFieldError`); `strict=False` accepts it | Not checked here |
| Runtime dependencies | `camt053` | None (only optional extras) |
| Python | 3.11+ | 3.10+ |
| Licence | Apache-2.0 OR MIT | BSD-3-Clause |

## When to pick which

Pick this package when the statement is going into camt.053 tooling, the
camt053 validator, reversal builder, writer or MCP server, because the output
is already that model. Pick `mt-940` when you want MT940 data on its own
terms, need byte or file input handled for you, or need its processors and
custom tag parsers.

## Evidence

- `mt-940`: `mt940/parser.py` (`parse` returns `Transactions`;
  `parse_statements` splits on `:20:`), and the wheel's `METADATA`
  (`License-Expression: BSD-3-Clause`, `Requires-Python: >=3.10`, no
  non-extra `Requires-Dist`).
- `camt053-loader-mt940`: `camt053_loader_mt940/loader.py` and
  `tests/test_regression.py`.

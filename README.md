<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="https://cloudcdn.pro/camt053/v1/logos/camt053.svg" alt="camt053-loader-mt940 logo" width="128" />
</p>

<h1 align="center">camt053-loader-mt940</h1>

<p align="center">
  Turns SWIFT MT940 bank statements into the same camt053 ParsedDocument that native camt.053 XML produces.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/camt053-loader-mt940/actions"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/camt053-loader-mt940/ci.yml?style=for-the-badge&logo=github" alt="Build" height="28" /></a>
  <a href="https://pypi.org/project/camt053-loader-mt940/"><img src="https://img.shields.io/pypi/v/camt053-loader-mt940?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" height="28" /></a>
  <a href="docs/index.md"><img src="https://img.shields.io/badge/docs-source-blue?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" height="28" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/camt053-loader-mt940"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/camt053-loader-mt940?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" height="28" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/camt053-loader-mt940/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.11%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.11 or newer" height="28" /></a>
</p>

<p align="center">
  <img src=".github/demo.gif" alt="camt053-loader-mt940 demo: the MT940 text in examples/01_minimal_parse.py, the parsed statement it prints, then a statement without :25: rejected with MissingMandatoryFieldError" width="100%" />
</p>

---

## Contents

**Getting started**

- [Install](#install) — `pip`, one runtime dependency
- [Requirements](#requirements) — toolchain floor, platforms
- [Quick Start](#quick-start) — one call from MT940 text to a camt053 `ParsedDocument`

**The camt053-loader-mt940 ecosystem**

- [The camt053-loader-mt940 ecosystem](#the-camt053-loader-mt940-ecosystem) — the six packages of the camt053 suite

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance) — the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison) — short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks) — headline numbers; full table at [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features) — module-level capability list
- [Configuration](#configuration) — core options
- [Examples](#examples) — runnable example index

**Operational**

- [When not to use camt053-loader-mt940](#when-not-to-use-camt053-loader-mt940) — limitations
- [Development](#development) — make targets, CI
- [Security](#security) — guarantees and compliance
- [Documentation](#documentation) — all reference docs
- [Stability guarantees](#stability-guarantees) — SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```sh
pip install camt053-loader-mt940
```

> **Latest release: v0.0.25**: released in lockstep with the camt053
> suite at 0.0.25. Parsing is unchanged from 0.0.24.

The package pulls in [`camt053`][core] (0.0.24 or newer, below 1) and nothing
else. There is no command-line entry point: it is a library.

---

## Requirements

- Python 3.11 or newer, tested in CI on 3.11, 3.12, 3.13 and 3.14 on
  Linux ([toolchain policy](docs/POLICIES.md)).
- `camt053` 0.0.24 or newer on the 0.x line.
- Pure Python, so any platform CPython runs on; CI exercises Linux only.

---

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

print(document.msg_id)                          # STMT-REF-1
print(document.statements[0].account.iban)     # DE89370400440532013000
print(document.statements[0].balances[0].amount)  # 1000.00
```

`document` is a `camt053.models.ParsedDocument`, the type the camt053 XML
parser returns, so the camt053 validator, the reversal builder,
[`camt053-writer-xlsx`][writer], [`camt053-mcp`][mcp] and
[`camt053-lsp`][lsp] take it unchanged.

---

## The camt053-loader-mt940 ecosystem

This package is one of six in the camt053 suite. They release together at
one version, core first, and share the `camt053.models` data model.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [`camt053`][core] | Reads ISO 20022 camt.053, camt.052 and camt.054 statements and generates validated reversing entries | The core library this loader feeds |
| **`camt053-loader-mt940`** | SWIFT MT940 customer statements to a camt.053 `ParsedDocument` | A bank, ERP or middleware still emits MT940 |
| [`camt053-loader-mt942`][mt942] | SWIFT MT942 interim transaction reports to a camt.052 `ParsedDocument` | Intraday reports in MT942 |
| [`camt053-writer-xlsx`][writer] | Writes parsed statements to Excel `.xlsx` | Hand a statement to finance as a spreadsheet |
| [`camt053-mcp`][mcp] | MCP server exposing the library to AI agents, including MT940 migration | Agent workflows over statements |
| [`camt053-lsp`][lsp] | Language server for authoring camt053 reversing-entry data files | Editor support |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Parsing | `:20:`, `:25:`, `:28C:`, `:60F:`/`:60M:`, `:61:`, `:86:`, `:62F:`/`:62M:`, `:64:`, `:65:` | Supported |
| Files | Several statements in one payload, one `Statement` per `:20:` | Supported since 0.0.23 |
| Reversals | `RC`/`RD` lines become entries with `reversal_indicator=True` | Supported |
| Validation | Missing or empty `:20:`, missing `:25:` or one that names no account | Rejected (`strict=True` default) |
| Validation | Amounts that are not numbers, dates that do not exist | Rejected since 0.0.23 |
| Validation | Missing `:28C:`, `:60F:` or `:62F:` | Accepted today; a recorded gap |
| Narrative | Bank-specific `:86:` sub-fields (`?20`, `?30`, ...) | Kept verbatim, not interpreted |
| Return reasons | ISO `ExternalReturnReasonCode` for `RC`/`RD` lines | Not mapped |

---

## Ecosystem comparison

The established Python MT940 parser is [`mt-940`][mt-940]. It returns its own
`Transactions` collection; this package returns the camt053 model, so the
result goes straight into camt.053 tooling.

| Project | Output | Multi-statement files | Licence |
| :--- | :---: | :---: | :---: |
| **camt053-loader-mt940** | camt053 `ParsedDocument` | One `Statement` per `:20:` | Apache-2.0 OR MIT |
| `mt-940` 5.1.1 | `mt940.models.Transactions` | `parse_statements()`, one `Transactions` per `:20:` | BSD-3-Clause |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

`benches/bench_parse_mt940.py` sweeps entries per statement and statements
per file and reports nanoseconds per entry. The number to read is the
shape: it should stay flat as files grow. Nothing asserts a threshold,
because wall-clock timings are not comparable between machines; CI runs it
with `--quick` so it keeps working against the current API.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| One statement, 5,000 entries (466 KiB) | 35.2 ms, 7,043 ns/entry | Apple A18 Pro, CPython 3.12.14, shared machine |
| 200 statements, 20,000 entries (1.7 MiB) | 169.3 ms, 8,464 ns/entry | Apple A18 Pro, CPython 3.12.14, shared machine |
| Cost per entry, 5,000 entries vs 10 | 1.07x (linear) | same run |

See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for methodology and full results.

---

## Features

- **One function.** `parse_mt940(text, *, strict=True)` returns a
  `ParsedDocument` with `message_type` `"camt.053.001.08"`.
- **One statement per `:20:`.** A file that concatenates statements, one per
  account or per day, keeps each statement's account, balances and entries
  apart. `msg_id` is the first `:20:`.
- **Tag mapping.**

  | Tag | Meaning | Mapped to |
  | :--- | :--- | :--- |
  | `:20:` | Transaction reference number | starts a `Statement`; the first is `ParsedDocument.msg_id` |
  | `:25:` | Account identification (`BIC/account` or `account`) | `Statement.account` (`iban`, or `other_id`, plus `servicer_bic`) |
  | `:28C:` | Statement / sequence number | `Statement.id` and `Statement.electronic_seq_nb` |
  | `:60F:` / `:60M:` | Opening balance | `Balance`, `type_code="OPBD"` |
  | `:61:` | Statement line | `Entry` (amount, indicator, value and booking dates, references) |
  | `:86:` | Information to account owner | `TransactionDetails.additional_info` on the preceding entry |
  | `:62F:` / `:62M:` | Closing balance | `Balance`, `type_code="CLBD"` |
  | `:64:` | Closing available balance | `Balance`, `type_code="CLAV"` |
  | `:65:` | Forward available balance | `Balance`, `type_code="FWAV"` |

- **Errors name the tag.** `MissingMandatoryFieldError` (a `ValueError`,
  with `.tag` and `.description`) for a missing or empty `:25:`;
  `ValueError` for a missing `:20:` or a malformed balance or `:61:` line.
- **Unknown tags are ignored**, for example `:13D:`, so bank extensions do
  not break parsing.

---

## Configuration

One keyword-only option:

| Option | Default | Effect |
| :--- | :--- | :--- |
| `strict` | `True` | Reject a statement whose `:25:` is absent, empty, or names a servicer BIC with no account. Pass `strict=False` only when the account is known from outside the file (a filename, an SFTP folder) and will be attached afterwards. |

---

## Examples

- [`examples/01_minimal_parse.py`](examples/01_minimal_parse.py): parse a
  small MT940 statement and print its account, balances and entries.
- [`examples/02_round_trip_to_dict.py`](examples/02_round_trip_to_dict.py):
  parse, then `to_dict()` for JSON.

Both run in CI on every pull request, and in `tests/test_regression.py`.

---

## When not to use camt053-loader-mt940

- **You already have camt.053 XML.** Use the `camt053` parser directly.
- **You have MT942 interim reports.** Use
  [`camt053-loader-mt942`][mt942].
- **You need bank-specific `:86:` sub-fields parsed** (Deutsche Bank's
  `?20`/`?30`/`?32`, for example). The raw value is kept in
  `additional_info` for you to parse.
- **You need ISO return-reason codes on `RC`/`RD` lines.** They are flagged
  with `reversal_indicator=True` but not mapped to `ExternalReturnReasonCode`.
- **You need `:28C:`, `:60F:` and `:62F:` enforced.** They are mandatory
  in MT940 but still accepted when absent.
- **Your MT940 arrives PGP-encrypted.** Decrypt it first; the loader takes
  plaintext.

---

## Development

```bash
git clone https://github.com/sebastienrousseau/camt053-loader-mt940
cd camt053-loader-mt940
python -m venv .venv && . .venv/bin/activate
pip install --require-hashes -r requirements/test.txt -r requirements/lint.txt
pip install --no-deps -e .
make check
```

`make check` runs ruff, `reuse lint`, mypy in strict mode, the complexity
ceilings, the version-agreement check, pytest with a 100% line and branch
coverage gate, interrogate at 100% docstring coverage, the benchmark and
the examples. CI also runs the dependency audit (`pip-audit`), Atheris fuzzing of
`parse_mt940` (two minutes per change, thirty weekly, seeded from
`fuzz/corpus/`), CodeQL, OpenSSF Scorecard, the DCO check and a daily Suite
Consistency check against PyPI. See [`DEVELOPMENT.md`](DEVELOPMENT.md) and
[`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Security

The loader parses text: it reads no files, opens no sockets and parses no
XML, so the XXE surface lives in the `camt053` core. Field patterns are
anchored with bounded quantifiers, parsing is linear in the input, and
input outside the grammar (including amounts that are not numbers and dates
that do not exist) is rejected with a `ValueError` naming the tag. The
parser is fuzzed with Atheris in CI and with Hypothesis in the test suite.
Releases are published from a signed tag through PyPI Trusted Publishing,
with SLSA build provenance, sigstore signatures and a CycloneDX SBOM.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

[User manual](docs/index.md) · [API reference](docs/index.md#the-api) ·
[Developer guide](DEVELOPMENT.md) ·
[Family map](#the-camt053-loader-mt940-ecosystem) ·
[Changelog](CHANGELOG.md) · [Toolchain policy](docs/POLICIES.md)

---

## Stability guarantees

The project is pre-1.0 and versions advance in `0.0.1` steps, in lockstep
with the camt053 suite. The breaking axis is `parse_mt940`'s signature and
the `ParsedDocument` it produces for a given input: a change to that output
is breaking even when no signature moves, and the changelog calls it out
(0.0.18 rejecting a missing `:25:`; 0.0.23 splitting multi-statement files,
rejecting malformed amounts and dates, and dating year-end bookings). The Python floor moves only as described in the
[toolchain policy](docs/POLICIES.md).

---

## License

This project is dual-licensed under either:

* Apache License, Version 2.0 ([`LICENSE-APACHE`](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
* MIT License ([`LICENSE-MIT`](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

at your option. Dependencies keep their own licences.

[core]: https://github.com/sebastienrousseau/camt053
[mcp]: https://github.com/sebastienrousseau/camt053-mcp
[lsp]: https://github.com/sebastienrousseau/camt053-lsp
[writer]: https://github.com/sebastienrousseau/camt053-writer-xlsx
[mt942]: https://github.com/sebastienrousseau/camt053-loader-mt942
[mt-940]: https://pypi.org/project/mt-940/

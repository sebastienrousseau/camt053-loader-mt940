# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`camt053`](https://github.com/sebastienrousseau/camt053)
suite (`camt053`, `camt053-mcp`, `camt053-lsp`, `camt053-writer-xlsx`); a
`0.0.X` release of this package targets the `0.0.X` release of `camt053`.

## [0.0.1] - 2026-06-21

### Added

Initial release of `camt053-loader-mt940`, a SWIFT MT940 → camt.053
`ParsedDocument` loader. Companion to the
[`camt053`](https://github.com/sebastienrousseau/camt053) core library.

Public API: a single function `parse_mt940(text)` that returns the
same `camt053.models.ParsedDocument` shape as
`camt053.parse.statement_parser.parse_document`, so every downstream
consumer in the suite works without further changes.

#### Supported MT940 fields

- `:20:` Transaction reference number
- `:25:` Account identification (BIC + account or account only)
- `:28C:` Statement / sequence number
- `:60F:` / `:60M:` Opening balance (Final / intermediary)
- `:61:` Statement line (debit/credit, optional funds code,
  transaction-type code, bank reference, customer reference)
- `:86:` Information to account owner (attaches to the preceding entry)
- `:62F:` / `:62M:` Closing balance
- `:64:` Closing available balance
- `:65:` Forward available balance

Reversal detection: `:61:` lines with debit/credit code `RD` or `RC`
are mapped to entries with `reversal_indicator=True`.

#### Why this exists

SWIFT MT940 is officially retiring in November 2028. Until then, SMEs,
ERPs, and treasury middleware still produce MT940 while downstream
tooling expects camt.053. This package bridges that two-year window.

#### Quality

- 100% line + branch coverage enforced via `--cov-fail-under=100`.
- 100% docstring coverage enforced via `interrogate`.
- Type-checked with `mypy --strict`.
- Two runnable end-to-end examples exercised in CI.

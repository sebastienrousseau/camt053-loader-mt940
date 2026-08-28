# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`camt053`](https://github.com/sebastienrousseau/camt053)
suite (`camt053`, `camt053-mcp`, `camt053-lsp`, `camt053-writer-xlsx`); a
`0.0.X` release of this package targets the `0.0.X` release of `camt053`.

## [0.0.17] - 2026-08-28

The first repository brought onto the **suite conformance gate**, and the
template for the other 31.

### Added

- **`tests/test_suite_conformance.py`** — 33 invariants shared by every
  repository in the suite, vendored from one canonical copy and checksummed
  by its own test. Each assertion exists because the suite has already
  shipped the failure it describes: a release published with `__version__`
  reporting the previous version, an extra that could not be installed, an
  advisory fix bumped in the tree but never tagged, a package that sat at
  73% coverage because nothing was watching. None were visible from inside
  the repository that carried them.

  Editing the vendored copy fails `test_this_file_is_the_canonical_copy` by
  design — no repository can quietly weaken a shared gate.

- **`benches/bench_parse_mt940.py`** — throughput across the two axes that
  actually move: entries within a statement, and statements within a file.

  It asserts no timing threshold, because wall-clock numbers are not
  comparable between machines. What it exposes is **shape**: the `ns/entry`
  column stays flat if the parser is linear and climbs if it has gone
  superlinear — the failure no unit test sees and a month-end file finds.
  CI runs `--quick`, so a benchmark that stops compiling fails the build
  instead of rotting into documentation that reads as verified.

- **`tests/test_regression.py`** — every claim the documentation makes,
  pinned. Separate from `test_loader.py` on purpose: that asks whether the
  parser is correct, this asks whether it still does what the README and
  docs say, which is the thing that silently stops being true. The examples
  and the benchmark are executed here too.

- **`docs/index.md`** and **`CONTRIBUTING.md`**.

### Fixed

- **The documentation described an API that does not exist.** Writing the
  regression tests surfaced two errors in the draft docs, both of which
  would have sent a reader straight into a `TypeError`:
  `document.all_entries` and `statement.entries_with_reason` are methods,
  not properties, and the latter takes a reason code.

- **The `parse_mt940` docstring overstates what it rejects.** It says a
  `ValueError` is raised "if a required field is missing". Only `:20:` is
  actually required. **A statement with no `:25:` parses successfully into
  an account whose IBAN and BIC are both `None`** — entries that belong to
  no account, which reconcile against nothing and surface as an unexplained
  break rather than a parse error.

  The behaviour is left as it is: tightening it would break anyone relying
  on the leniency, and that deserves to be a decision rather than a quiet
  edit. It is now documented as a hazard, with the defensive check spelled
  out, and pinned by a test that forces any future change to be deliberate.

### Changed

- CI lints and formats `benches/` alongside everything else, and runs the
  benchmark.
- `tests/test_suite_conformance.py` is excluded from the formatter. It is
  generated, and the suite uses three different line lengths — letting each
  repository reformat it would make the shared checksum unsatisfiable.

## [0.0.16] - 2026-08-21

Suite release with `camt053` 0.0.16. No functional change in this
package.

### Changed

- **Version aligned to the suite.** Every package in the `camt053`
  suite ships the same number, so there is no compatibility table to
  consult. See `camt053.suite`, which a daily job checks against PyPI.

- **The `camt053` floor moves to `>=0.0.16`,** from `>=0.0.6` — a bound
  that had not been revisited in nine releases, because it still
  resolved and so never complained.

### Added

- **A version-sync test.** `pyproject.toml` and `__init__.py` state the
  version independently and nothing compared them, so a release could
  ship with the two disagreeing. It nearly did: the first attempt at
  this release landed `__init__.py` at 0.0.16 against a `pyproject.toml`
  still on 0.0.14, and every check passed.

## [0.0.14] - 2026-07-16

### Changed

- **Version** — suite-wide lockstep bump to `0.0.14`, targeting the
  `0.0.14` release of `camt053`. Dependency refresh only (the
  `camt053 >= 0.0.6, < 1` constraint already admits `0.0.14`); no
  functional changes.

## [0.0.13] - 2026-07-16

### Added

- **Load/stress test suite** (`tests/test_stress.py`, marker `perf`,
  excluded from the default coverage-gated run): sustained concurrent
  MT940 → camt.053 conversions, a 10,000-entry statement bound, and a
  `tracemalloc` soak loop asserting bounded memory growth.

### Changed

- **Version** — suite-wide lockstep bump to `0.0.13` (aligning with
  the `camt053` suite; `0.0.10`–`0.0.12` were not released for this
  package). No functional changes.

## [0.0.9] - 2026-06-27

### Changed

- **Version** — suite-wide lockstep bump to `0.0.9`. No functional changes.

## [0.0.7] - 2026-06-22

### Added

First PyPI release of `camt053-loader-mt940`, a SWIFT MT940 → camt.053
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

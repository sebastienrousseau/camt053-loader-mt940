<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`camt053`](https://github.com/sebastienrousseau/camt053)
suite (`camt053`, `camt053-lsp`, `camt053-mcp`, `camt053-loader-mt940`,
`camt053-loader-mt942`, `camt053-writer-xlsx`), which releases every member
together at one version, core first.

## [0.0.24] - 2026-10-27

The camt053 suite's 0.0.24 release, core first. Every member drops
Python 3.10 and requires the 0.0.24 core. Parsing is unchanged.

### Removed

- **Python 3.10 is no longer supported; the floor is 3.11.** This is a
  decision for the whole camt053 suite: 3.10 reaches end of life in
  October 2026, and current Hypothesis releases need 3.11. The CI matrix
  is 3.11 to 3.14, ruff and mypy target 3.11, the `tomli` backport and
  the 3.10 `tomllib` fallback in `scripts/check_suite_consistency.py` are
  gone, and every hash-pinned `requirements/*.txt` is compiled for 3.11.
  On 3.10, pip keeps resolving 0.0.23.

## [0.0.23] - 2026-10-20

The camt053 suite's 0.0.23 release, which brings every member back to one
version after `camt053-mcp` published 0.0.22 alone. Four parser fixes that
change what some inputs produce, fuzzing that found two of them, and the
repository brought up to the family's supply-chain, licensing and
documentation standard.

### Fixed

- **A file carrying several MT940 statements now returns one `Statement`
  per `:20:`.** It used to return a single statement holding every entry
  and balance in the file under the last `:25:` account, with the last
  `:28C:` as its id and the last `:20:` as `msg_id`, and an `:86:` opening
  a later statement was appended to the previous statement's last entry.
  `docs/index.md` already documented one statement per `:20:`. This changes
  the output for multi-statement input, so it is called out here as a
  behaviour change; a single-statement payload parses exactly as before.
  `msg_id` is now the first `:20:`, and `strict` and the `:20:` check apply
  to every statement.
- **Amounts that are not numbers are rejected.** The pattern `[\d,]+`
  accepted `1,2,3` as the amount `"1.2.3"` and a bare `,` as `"."`, whose
  `amount_decimal` is `None`. An amount is now at least one integer digit and
  at most one decimal comma; anything else raises `ValueError` naming the
  tag. `1000,00`, `1000,` and `7` parse as before.
- **A booking date across the year end takes the right year.** A `:61:`
  booking date is `MMDD` and borrowed the value date's year, so a 2 January
  booking of a 31 December value date landed on 2 January of the same year,
  twelve months early. It now takes the year, of the value date's and the
  one either side, nearest the value date.
- **Dates that do not exist are rejected.** Any six digits were a date:
  `000000` became `2000-00-00` and `260230` became 30 February, in balances
  and in `:61:` value and booking dates. They now raise `ValueError` naming
  the tag.
- `scripts/check_suite_consistency.py` compared this tree with the
  `camt053` core's PyPI release instead of this package's, so a 0.0.23
  tree that was never tagged here would have passed once the core shipped.
  It is now the shared lockstep copy with `THIS = "camt053-loader-mt940"`.
  The scheduled Suite Consistency run has been red since 2026-10-05
  (`camt053-mcp` 0.0.22 against 0.0.20); it clears when the suite
  publishes 0.0.23.

### Changed

- **Requires `camt053` 0.0.23 or newer** (was 0.0.16), still below 1. The
  suite releases core first at one version, and core 0.0.23 is the first
  to floor its advised dependencies (`fastapi` 0.109.1 for PYSEC-2024-38,
  `starlette` 1.3.1, `cryptography` 50.0.0 and others); a lower floor here
  let an older core resolve, and an affected `fastapi` with it.
  `scripts/verify_versions.py` now fails when the floor in
  `pyproject.toml` or `requirements/*.in` is not this version.
- `parse_mt940` is split into helpers under the complexity ceilings; no
  behaviour change beyond the fix above.
- Release workflow: every action pinned by commit SHA, build tooling from
  hash-pinned requirements with `--no-isolation`, the GitHub release titled
  `camt053-loader-mt940 <version>` instead of the tag, every version source
  checked before building, a CycloneDX SBOM attached, and PEP 740
  attestations uploaded to PyPI.
- README rewritten to the family template, with a rendered demo; it no
  longer claims Apache-2.0 only, a 0.0.14 latest release or an example that
  does not exist.
- SPDX headers say `Apache-2.0 OR MIT` everywhere (most said `Apache-2.0`),
  and the wheel carries the MIT classifier beside the Apache one.

### Added

- Fuzzing: an Atheris harness (`fuzz/fuzz_parse_mt940.py`, two minutes per
  change and thirty weekly in CI) and Hypothesis property tests
  (`tests/test_fuzz.py`) holding `parse_mt940` to one contract on any
  input, with a seed and fixed-bug corpus in `fuzz/corpus/` replayed on
  every test run. They found the amount and date defects above.
- CI installs from hash-pinned `requirements/*.txt`, pins every action by
  SHA, and audits every requirements file with `pip-audit`.
- OpenSSF Scorecard, DCO, "Version sources agree" and Complexity workflows
  and jobs. `scripts/verify_versions.py` checks `pyproject.toml`,
  `__version__`, this changelog, `CITATION.cff`, `releases/`, the README
  callout, `SECURITY.md` and the `camt053` floor.
  `scripts/check_complexity.py` holds cyclomatic 10, cognitive 15, Halstead
  30 and 60 lines per function against an empty baseline.
- `reuse lint` compliance (`LICENSES/`, `REUSE.toml`), `CITATION.cff`,
  Dependabot version updates, a pull request template, issue templates,
  `CODEOWNERS`, `CODE_OF_CONDUCT.md`, `DEVELOPMENT.md`, a `Makefile`, and
  `docs/POLICIES.md`, `docs/COMPARISON.md`, `docs/BENCHMARKS.md`.

### Known gap

Unchanged from 0.0.18: `:28C:`, `:60F:` and `:62F:` are still accepted when
absent.

## [0.0.20] - 2026-08-29

Aligns the `camt053` suite on one version number, and adds the scheduled
drift check this repository was missing.

### Added

- `scripts/check_suite_consistency.py` and a scheduled `Suite
  Consistency` workflow compare this tree, and every published member of
  the suite, against PyPI. A member left a release behind still installs
  and still passes its own tests; only the index disagrees, and only if
  somebody looks.

### Changed

- Version aligned to `0.0.20` across all six `camt053` packages, which
  had drifted to `0.0.18`, `0.0.18`, `0.0.19`, `0.0.18`, `0.0.16` and
  `0.0.16`.
- Refreshed the vendored `tests/test_suite_conformance.py` to the
  current canonical copy.

## [0.0.18] - 2026-08-28

**Breaking.** A statement whose `:25:` does not identify an account is now
rejected instead of parsed.

### Changed

- **`parse_mt940` rejects a missing or empty `:25:` by default.** It
  previously returned a `ParsedDocument` whose account carried a `None`
  IBAN and BIC — entries belonging to no account.

  That output was invalid twice over. `:25:` is mandatory under the SWIFT
  MT940 specification, and `<Stmt><Acct>` is `[1..1]` in the camt.053 model
  this loader exists to produce, so the document could never have passed
  schema validation downstream. It also had no business use: a statement
  with no account cannot be routed or booked by an ERP.

  The practical cost was worse than the theory. The `None` account was a
  poison pill that pushed `if account is None` onto every consumer —
  `camt053-writer-xlsx`, `camt053-mcp`, any agent calling them — and anyone
  following the quick start into `document.statements[0].account.iban` got
  `AttributeError: 'NoneType' object has no attribute 'iban'` deep inside
  their own code rather than a clear message at the parse boundary.

- **Three shapes are rejected, not one.** Seeing the tag is not the same as
  being told which account, so a bare `:25:` and a `:25:BIC/` carrying a
  servicer but no account number are refused alongside the absent case. A
  presence-only check would have been defeated by either.

  A proprietary account number is still accepted: the rule is that *some*
  identifier is present, not that it is an IBAN.

### Added

- **`strict` keyword argument**, defaulting to `True`. Pass `strict=False`
  for genuinely non-compliant legacy feeds where the account is known from
  the filename or the SFTP folder and will be attached afterwards.

  Keyword-only on purpose: `parse_mt940(text, False)` raises `TypeError`
  rather than quietly reinstating the old behaviour at a call site that
  looks like it is passing an option.

- **`MissingMandatoryFieldError`**, exported from the package. It subclasses
  `ValueError` deliberately — every error this module raised before now was
  a bare `ValueError`, and callers already catch that. Narrowing the type
  would have been a second breaking change on top of the one that matters.
  It carries `.tag` and `.description`.

### Known gap

`:28C:`, `:60F:` and `:62F:` are equally mandatory under MT940, and equally
mandatory in camt.053 — `<Stmt><Id>` is `[1..1]` and `<Stmt><Bal>` is
`[1..n]`. All three are still accepted when absent. `strict` does not yet
cover them; extending it is a matter of adding rows to
`_MANDATORY_UNDER_STRICT`, but it widens the breaking change beyond what was
decided, so it waits.

### Migration

If you parse statements from a source that omits `:25:`, either pass
`strict=False` and attach the account yourself, or fix the source. Catching
`ValueError` already works; catch `MissingMandatoryFieldError` to
distinguish this case.

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

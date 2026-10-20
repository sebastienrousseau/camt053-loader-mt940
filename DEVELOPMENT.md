<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Development

## Toolchain

Python 3.10 or newer ([toolchain policy](docs/POLICIES.md)). CI installs
every tool from hash-pinned files under `requirements/`; do the same
locally so you run what CI runs:

```sh
python -m venv .venv && . .venv/bin/activate
pip install --require-hashes -r requirements/test.txt -r requirements/lint.txt
pip install --no-deps -e .
```

`pip install -e ".[dev]"` also works and resolves the same tools without
hashes.

## Every CI gate, locally

| CI job | Local command |
| :--- | :--- |
| Test (3.10 to 3.14) | `make test` (pytest, 100% line and branch coverage; interrogate, 100% docstrings) |
| Benchmark and examples | `make benchmark examples` |
| Lint & Type Check | `make lint type-check` (ruff, ruff format, `reuse lint`, mypy strict) |
| Complexity | `make complexity` (needs `requirements/complexity.txt`) |
| Dependency audit | `make audit` (needs `requirements/audit.txt`) |
| Fuzz (Atheris) | `make fuzz` (Linux x86_64 only, needs `requirements/fuzz.txt`); `tests/test_fuzz.py` replays `fuzz/corpus/` and runs the same contract with Hypothesis anywhere |
| Version sources agree | `make verify-versions` |
| Release Notes Present | `releases/v<version>.md` must exist |
| DCO | every commit carries `Signed-off-by:` (`git commit -s`) |

`make check` runs all of these except the audit, which needs network
access, and Atheris, which needs Linux x86_64. CodeQL, OpenSSF Scorecard and the daily Suite Consistency check
(`python3 scripts/check_suite_consistency.py`, which queries PyPI) run only
on GitHub.

## Complexity ceilings

Per function: cyclomatic 10, cognitive 15, Halstead difficulty 30, 60
lines; 500 lines per file. `complexity-baseline.json` records offenders
that predate the gate (none today) and may only shrink:
`python scripts/check_complexity.py --update` rewrites it after an
improvement, never to absorb a regression.

## Dependencies

Edit a `requirements/*.in` file, then `make pip-compile` (needs
[uv](https://docs.astral.sh/uv/)) to regenerate the `.txt` beside it.
Commit both.

## Tests

- `tests/test_loader.py`: the parse, valid and malformed.
- `tests/test_regression.py`: what the documentation promises, plus the
  examples and the benchmark run as subprocesses.
- `tests/test_stress.py`: large payloads, marked `perf` and excluded by
  default; run with `pytest -m perf --no-cov`.
- `tests/test_fuzz.py`: the parser's contract on any input (Hypothesis),
  and a replay of every seed and fixed-bug input in `fuzz/corpus/`.
- `tests/test_check_*.py`, `tests/test_verify_versions.py`: the scripts in
  `scripts/`.
- `tests/test_suite_conformance.py`: vendored from one canonical copy
  shared across the suite. Do not edit it here.

## Releases

The camt053 suite releases all six members at one version, core first.
A release is a `feat/v<version>` branch whose pull request carries the
version bump in `pyproject.toml`, `camt053_loader_mt940/__init__.py`,
`CITATION.cff`, the README's latest-release callout, a `CHANGELOG.md`
section and `releases/v<version>.md`. After it merges, a signed annotated
tag `v<version>` with the message `camt053-loader-mt940 v<version>`
triggers `release.yml`: build, SLSA provenance, SBOM, the GitHub release
titled `camt053-loader-mt940 <version>`, PyPI Trusted Publishing and
sigstore signatures.

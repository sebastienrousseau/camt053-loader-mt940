<!-- SPDX-License-Identifier: Apache-2.0 -->

# Security Policy

## Supported versions

This package follows the [`camt053`](https://github.com/sebastienrousseau/camt053)
suite cadence. Security patches are issued for the latest minor of
the latest major. While pre-`1.0`, that means **the latest released
0.0.x and the immediately prior 0.0.x** receive security fixes; older
0.0.x versions do not.

| Version | Status | Receives security fixes? |
| :--- | :--- | :--- |
| `0.0.1` (latest) | Current | ✅ Yes |
| _none yet_ | - | - |

## Reporting a vulnerability

**Do not open a public issue for security reports.**

Use one of the following private channels:

1. **GitHub Private Vulnerability Reporting (preferred)**
   <https://github.com/sebastienrousseau/camt053-loader-mt940/security/advisories/new>
2. **Email**: `security@camt053.com`

**Acknowledgement**: within 48 hours. **Triage**: within 7 days.
**Fix windows**: critical 7 days, high 30 days, medium 60 days, low
best-effort.

## Security posture

### Scope

This package exposes one function, `parse_mt940(text)`, that converts
a SWIFT MT940 text payload into a `camt053.models.ParsedDocument`. It
does **not** parse XML, validate against schemas, write files, or
make network calls. Untrusted input is regex-bounded to a small set
of expected MT940 field shapes; anything outside that grammar is
rejected with a `ValueError`.

### Threat model

| Surface | How it's handled |
| :--- | :--- |
| **XML / XXE / billion-laughs** | Out of scope. MT940 is a flat text format with no XML envelope. |
| **Catastrophic regex backtracking** | The field regexes are anchored (`^`) and use bounded quantifiers (`\d{6}`, `[A-Z]{3}`, `[A-Z0-9]{3}`). No nested unbounded groups. |
| **Path traversal** | The loader does not touch the filesystem. Callers pass strings, not paths. |
| **Resource exhaustion** | Parsing is O(input size). Callers concerned about hostile input should impose an upstream byte cap. |
| **Bank-specific `:86:` sub-fields** | Value is preserved verbatim as `additional_info`. The loader does not interpret or execute any embedded content. |
| **Dependency CVEs** | `camt053 >= 0.0.5, < 1` is the only runtime dep. Pinned via PyPI and audited by GitHub Dependabot. |

### Cryptography status

This package implements **no** cryptographic functionality. MT940
payloads sometimes arrive in PGP envelopes; decrypt upstream before
passing to this loader.

### Supply chain

- **PyPI Trusted Publishing** (OIDC, no long-lived tokens).
- **Sigstore attestations** for sdist + wheel via
  `pypa/gh-action-pypi-publish`.
- **Signed git tags**: every release tag is signed with the
  maintainer's SSH key.
- **No `--no-verify` or `--allow-unverified` shortcuts** in any
  release workflow.

## Contact

- **GitHub Private Vulnerability Reporting (preferred):**
  <https://github.com/sebastienrousseau/camt053-loader-mt940/security/advisories/new>
- **Email:** `security@camt053.com`

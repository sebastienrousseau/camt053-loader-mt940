<!-- SPDX-License-Identifier: Apache-2.0 -->

# Getting support

Thanks for using `camt053-loader-mt940`. Here's the fastest way to
get help, by need.

## Read first

- **[README.md](README.md)** - install, quick start, the supported
  MT940 field table, the reversal-detection rule.
- **[`examples/`](examples/)** - two runnable scripts exercised in CI.

## Questions & how-to

Open a [GitHub Discussion](https://github.com/sebastienrousseau/camt053-loader-mt940/discussions)
with:

- Python version + OS
- `camt053-loader-mt940` version + `camt053` version
- A minimal MT940 payload that reproduces the issue (sensitive
  values redacted)
- The full error output

Cross-package questions (e.g. how does the loader interact with
camt053-writer-xlsx?) are welcome on the parent's
[Discussions](https://github.com/sebastienrousseau/camt053/discussions).

## Bugs

Open an [issue](https://github.com/sebastienrousseau/camt053-loader-mt940/issues/new)
with:

- The same triage data as above
- The exact MT940 payload (anonymised) the parser refused to handle
- Expected vs. actual behaviour

## Feature requests

Likely categories:

- **MT941 / MT942** intraday / intermediate-statement messages -
  out of scope for v0.0.1; open an issue to gauge demand.
- **Bank-specific `:86:` sub-fields** (e.g. Deutsche Bank `?20`/`?30`)
  - out of scope for the loader; the raw value is preserved in
  `additional_info` so you can parse it downstream.
- **Encrypted MT940** - out of scope; decrypt upstream with `pgp` /
  `gpg` and feed plaintext.
- **Direct ISO return-reason mapping** for `RD` / `RC` lines - on
  the v0.0.2 roadmap.

Anything else? Open an issue.

## Security

**Do not** open public issues for vulnerabilities. Follow the
private disclosure process in [SECURITY.md](SECURITY.md).

## Support tiers

This package is open source under Apache-2.0. There is no paid
support tier.

- **Community support** (issues / discussions / PRs): best effort.
- **Commercial support**: not available today. Contact
  `support@camt053.com` so the maintainer can gauge demand.

## The camt053 suite

This package is one of five:

- [`camt053`](https://github.com/sebastienrousseau/camt053) - core
  library, CLI, REST API
- [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp)
  - MCP server (AI agents)
- [`camt053-lsp`](https://github.com/sebastienrousseau/camt053-lsp)
  - Language Server (editors)
- [`camt053-writer-xlsx`](https://github.com/sebastienrousseau/camt053-writer-xlsx)
  - Excel writer for parsed statements
- [`camt053-loader-mt940`](https://github.com/sebastienrousseau/camt053-loader-mt940)
  - **MT940 loader (this package)**

Issues spanning multiple packages can be filed against `camt053`
(the core); the maintainer will route them.

## Supported versions

| Version | Supported? |
| :--- | :--- |
| 0.0.1 (latest) | ✅ |

Requires Python 3.10+ and `camt053 >= 0.0.5`.

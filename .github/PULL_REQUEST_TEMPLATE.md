<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!--
Pull request template, from ~/Code/PR-TEMPLATE.md. Keep the sections and
their order, and fill every {{PLACEHOLDER}} from real evidence.
  - Open with a two-line BLUF: line 1 begins "This PR " and says what it
    does; line 2 says why it matters. Put a blank line after each.
  - No em dash characters anywhere in the body: use commas, colons,
    parentheses or a spaced hyphen.
  - Direct, concrete, no filler. No tool-attribution footer.
  - Title in Conventional Commits form (feat:, fix:, docs:, ci:, ...).
  - Every commit is signed and signed off (git commit -S -s); the DCO
    check fails a commit without Signed-off-by.
-->

This PR {{announces what it does, in one plain line}}.

{{BLUF_LINE_2: why it matters or the outcome, in one plain line}}

## Highlights ⭐️

* **{{HEADLINE}}**: {{one or two plain sentences on what changed for the user}}.
* **{{HEADLINE}}**: {{one or two plain sentences}}.

## What's Changed

* `{{COMMIT_SUBJECT}}` by @{{AUTHOR}}

{{OPTIONAL: a few detail bullets naming files and the concrete change}}

## Validation

* `make check`: {{result, with numbers: tests passed, coverage}}.
* `python -m build --no-isolation && twine check --strict dist/*`: {{result}}.

## Checksums

SHA-256 of the artifacts produced by `python -m build --no-isolation` on this branch:

```text
{{SHA256}}  dist/camt053_loader_mt940-{{VERSION}}-py3-none-any.whl
{{SHA256}}  dist/camt053_loader_mt940-{{VERSION}}.tar.gz
```

**Full Changelog**: https://github.com/sebastienrousseau/camt053-loader-mt940/compare/{{PREVIOUS_TAG}}...{{BRANCH_OR_TAG}}

---
name: Bug report
about: Report a defect so we can reproduce and fix it
title: "bug: "
labels: ["bug"]
assignees: []
---
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

## Summary

A clear and concise description of the bug.

## Steps to Reproduce

1. ...
2. ...
3. ...

```python
# Minimal, self-contained snippet that triggers the bug: the MT940 text
# (redacted of account numbers and names) and the parse_mt940 call.
```

## Expected Behaviour

What you expected to happen.

## Actual Behaviour

What actually happened. Include the full traceback, and the `tag` of any
`MissingMandatoryFieldError` raised.

## Environment

- camt053-loader-mt940 version:
- camt053 version:
- Python version:
- Operating system:
- Installation method (pip / source):

## Additional Context

Add any other context here: the bank that produced the file, or which
fields look wrong in the resulting `ParsedDocument`.

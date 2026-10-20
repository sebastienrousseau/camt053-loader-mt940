#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Fail when the release version is restated differently anywhere.

Single source of truth: ``version`` in ``pyproject.toml``. The same string
must appear as:

* ``__version__`` in ``camt053_loader_mt940/__init__.py``;
* a ``## [X.Y.Z]`` heading in ``CHANGELOG.md``;
* ``version:`` in ``CITATION.cff``;
* the heading of ``releases/vX.Y.Z.md``, which release.yml publishes;
* the "Latest release: vX.Y.Z" callout in ``README.md``, when present;
* the "(latest)" row of the supported-versions table in ``SECURITY.md``.

This package has published a release whose ``__version__`` disagreed with
its metadata (0.0.16), and a README and a security policy announcing a
release six versions old.
Standard library only, so the workflow needs no install.

Usage: python3 scripts/verify_versions.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_INIT = "camt053_loader_mt940/__init__.py"


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else None


def _read(root: Path, name: str) -> str | None:
    path = root / name
    return path.read_text(encoding="utf-8") if path.exists() else None


def pyproject_version(root: Path) -> str:
    """The version ``pyproject.toml`` declares: the source of truth."""
    text = _read(root, "pyproject.toml") or ""
    version = _search(r'^version\s*=\s*"([^"]+)"', text)
    if version is None:
        raise SystemExit("pyproject.toml has no version field")
    return version


def _dunder(root: Path, expected: str) -> list[str]:
    found = _search(
        r'^__version__\s*=\s*"([^"]+)"', _read(root, PACKAGE_INIT) or ""
    )
    if found == expected:
        return []
    return [f"{PACKAGE_INIT}: __version__ is {found}"]


def _changelog(root: Path, expected: str) -> list[str]:
    text = _read(root, "CHANGELOG.md") or ""
    if f"\n## [{expected}]" in f"\n{text}":
        return []
    return [f"CHANGELOG.md: no ## [{expected}] heading"]


def _citation(root: Path, expected: str) -> list[str]:
    text = _read(root, "CITATION.cff")
    if text is None:
        return ["CITATION.cff: missing"]
    found = _search(r'^version:\s*"?([^"\s]+)"?', text)
    return [] if found == expected else [f"CITATION.cff: version is {found}"]


def _release_notes(root: Path, expected: str) -> list[str]:
    name = f"releases/v{expected}.md"
    text = _read(root, name)
    if text is None:
        return [f"{name}: missing"]
    heading = next(
        (line for line in text.splitlines() if line.startswith("# ")), ""
    )
    if heading.endswith(f" v{expected}"):
        return []
    return [f"{name}: heading does not name v{expected}"]


def _readme(root: Path, expected: str) -> list[str]:
    found = _search(
        r"Latest release: v(\d+\.\d+\.\d+)", _read(root, "README.md") or ""
    )
    if found is None or found == expected:
        return []
    return [f"README.md: latest release is v{found}"]


def _security(root: Path, expected: str) -> list[str]:
    found = _search(
        r"^\| `(\d+\.\d+\.\d+)` \(latest\)", _read(root, "SECURITY.md") or ""
    )
    if found == expected:
        return []
    return [f"SECURITY.md: latest supported version is {found}"]


def problems(root: Path = ROOT) -> list[str]:
    """Every restatement of the version that disagrees with pyproject."""
    expected = pyproject_version(root)
    checks = (
        _dunder,
        _changelog,
        _citation,
        _release_notes,
        _readme,
        _security,
    )
    return [problem for check in checks for problem in check(root, expected)]


def main() -> int:
    """Compare every restatement of the version and report."""
    expected = pyproject_version(ROOT)
    found = problems(ROOT)
    for problem in found:
        print(f"ERROR: {problem}")
    if found:
        return 1
    print(f"OK: every version source agrees on {expected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

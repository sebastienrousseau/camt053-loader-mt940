# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every restatement of the release version is checked, and each drift fails.

The tree is copied into a temporary directory and one source at a time is
moved off the version, so each check is seen to catch its own drift.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCES = (
    "pyproject.toml",
    "CHANGELOG.md",
    "CITATION.cff",
    "README.md",
    "camt053_loader_mt940/__init__.py",
)


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "verify_versions", ROOT / "scripts" / "verify_versions.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A copy of every version-bearing file, plus the release notes."""
    for name in SOURCES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, target)
    shutil.copytree(ROOT / "releases", tmp_path / "releases")
    return tmp_path


def _version(root: Path) -> str:
    return str(_script().pyproject_version(root))


def _rewrite(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {path.name}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_the_tree_agrees() -> None:
    assert _script().problems(ROOT) == []


def test_main_reports_ok(capsys: pytest.CaptureFixture[str]) -> None:
    assert _script().main() == 0
    assert "OK" in capsys.readouterr().out


def test_a_stale_dunder_version_fails(tree: Path) -> None:
    v = _version(tree)
    _rewrite(
        tree / "camt053_loader_mt940/__init__.py",
        f'__version__ = "{v}"',
        '__version__ = "0.0.1"',
    )
    assert _script().problems(tree) == [
        "camt053_loader_mt940/__init__.py: __version__ is 0.0.1"
    ]


def test_a_missing_changelog_heading_fails(tree: Path) -> None:
    v = _version(tree)
    _rewrite(tree / "CHANGELOG.md", f"## [{v}]", "## [9.9.9]")
    assert _script().problems(tree) == [f"CHANGELOG.md: no ## [{v}] heading"]


def test_a_stale_citation_fails(tree: Path) -> None:
    v = _version(tree)
    _rewrite(tree / "CITATION.cff", f'version: "{v}"', 'version: "0.0.1"')
    assert _script().problems(tree) == ["CITATION.cff: version is 0.0.1"]


def test_missing_release_notes_fail(tree: Path) -> None:
    v = _version(tree)
    (tree / "releases" / f"v{v}.md").unlink()
    assert _script().problems(tree) == [f"releases/v{v}.md: missing"]


def test_release_notes_for_another_version_fail(tree: Path) -> None:
    v = _version(tree)
    _rewrite(
        tree / "releases" / f"v{v}.md",
        f"camt053-loader-mt940 v{v}",
        "camt053-loader-mt940 v0.0.1",
    )
    assert _script().problems(tree) == [
        f"releases/v{v}.md: heading does not name v{v}"
    ]


def test_a_stale_readme_callout_fails(tree: Path) -> None:
    v = _version(tree)
    _rewrite(
        tree / "README.md",
        f"Latest release: v{v}",
        "Latest release: v0.0.1",
    )
    assert _script().problems(tree) == ["README.md: latest release is v0.0.1"]


def test_a_missing_citation_is_reported(tree: Path) -> None:
    (tree / "CITATION.cff").unlink()
    assert _script().problems(tree) == ["CITATION.cff: missing"]

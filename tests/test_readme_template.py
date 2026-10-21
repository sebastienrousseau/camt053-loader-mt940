# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""README.md keeps the shape every repository in the family shares.

The canonical layout is ``~/Code/README-TEMPLATE.md``: the same top-level
headings in the same order, a badge row of ``height="28"`` images, the
demo under it, and no ``{{PLACEHOLDER}}`` left unfilled.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
PROJECT = "camt053-loader-mt940"

HEADINGS = [
    "Contents",
    "Install",
    "Requirements",
    "Quick Start",
    f"The {PROJECT} ecosystem",
    "Capabilities at a glance",
    "Ecosystem comparison",
    "Benchmarks",
    "Features",
    "Configuration",
    "Examples",
    f"When not to use {PROJECT}",
    "Development",
    "Security",
    "Documentation",
    "Stability guarantees",
    "License",
]


def _text() -> str:
    return README.read_text(encoding="utf-8")


def test_top_level_headings_follow_the_template() -> None:
    found = re.findall(r"^## (.+)$", _text(), re.MULTILINE)
    assert found == HEADINGS


def test_no_template_placeholder_is_left() -> None:
    assert re.findall(r"\{\{[A-Z0-9_]+[^}]*\}\}", _text()) == []


def test_every_badge_is_28_pixels_high() -> None:
    row = _text().split('<p align="center">')[3]
    badges = re.findall(r"<img [^>]*>", row)
    assert len(badges) >= 6
    assert all('height="28"' in badge for badge in badges)


def test_the_demo_sits_under_the_badges_and_exists() -> None:
    demo = _text().split('<p align="center">')[4]
    assert 'src=".github/demo.gif"' in demo
    assert (ROOT / ".github" / "demo.gif").is_file()
    assert (ROOT / ".github" / "demo.tape").is_file()

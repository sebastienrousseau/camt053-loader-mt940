#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
"""Throughput of :func:`parse_mt940` as statements grow.

Why this and not something else: a bank statement file is the one input whose
size the caller does not control. An ERP exporting a month of activity for a
busy account produces thousands of ``:61:`` entries in a single ``:20:``
statement, and a treasury system polling several accounts hands over a file
containing many statements. Those are the two axes that move in practice, so
they are the two this measures.

What it is watching for is **shape, not speed**. A parser that is linear in
entries stays usable as the file grows; one that is quadratic — because some
lookup rescans the entries already parsed — looks fine on the fixtures and
falls over on a real month-end file. The ``ns/entry`` column is the number to
read: it should stay roughly flat across the sizes. If it climbs with size,
the parser has become superlinear and no unit test will tell you.

Run::

    python benches/bench_parse_mt940.py
    python benches/bench_parse_mt940.py --json      # machine-readable
    python benches/bench_parse_mt940.py --quick     # what CI runs

Timings are wall-clock on one machine and are not comparable between
machines, so nothing here asserts a threshold. CI runs ``--quick`` to prove
the benchmark still executes against the current API; a benchmark that has
silently stopped compiling is worse than none, because it reads as coverage
that does not exist.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from camt053_loader_mt940 import parse_mt940  # noqa: E402

HEADER = """:20:BENCH-{n}
:25:COBADEFFXXX/DE89370400440532013000
:28C:1/1
:60F:C260620EUR0,00
"""

ENTRY = """:61:2606210621CR{amount},00NMSCREF{i}//CREF{i}
:86:Benchmark entry {i} for throughput measurement
"""

FOOTER = ":62F:C260621EUR{total},00\n"


def build_statement(entries: int, index: int = 0) -> str:
    """One MT940 statement carrying ``entries`` transaction lines."""
    body = "".join(
        ENTRY.format(amount=(i % 900) + 100, i=i) for i in range(entries)
    )
    total = sum((i % 900) + 100 for i in range(entries))
    return HEADER.format(n=index) + body + FOOTER.format(total=total)


def build_file(statements: int, entries_each: int) -> str:
    """A multi-statement payload, as a treasury poller would produce."""
    return "".join(
        build_statement(entries_each, index) for index in range(statements)
    )


def measure(payload: str, repeats: int) -> dict[str, float]:
    """Best-of timing. The minimum is the least noisy estimator here.

    The mean is dragged around by whatever else the machine is doing; the
    minimum is the closest thing to the work actually required.
    """
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        document = parse_mt940(payload)
        samples.append(time.perf_counter() - start)
    entries = sum(len(s.entries) for s in document.statements)
    best = min(samples)
    return {
        "entries": entries,
        "bytes": len(payload),
        "best_s": best,
        "median_s": statistics.median(samples),
        "entries_per_s": entries / best if best else 0.0,
        "ns_per_entry": (best * 1e9 / entries) if entries else 0.0,
    }


def run(quick: bool) -> list[dict]:
    """Sweep both axes: entries per statement, then statements per file."""
    if quick:
        entry_sizes, file_sizes, repeats = [10, 100], [(4, 25)], 2
    else:
        entry_sizes = [10, 100, 1_000, 5_000]
        file_sizes = [(10, 100), (50, 100), (200, 100)]
        repeats = 5

    results = []
    for size in entry_sizes:
        row = measure(build_statement(size), repeats)
        row |= {"case": "one statement", "statements": 1, "entries_each": size}
        results.append(row)
    for statements, each in file_sizes:
        row = measure(build_file(statements, each), repeats)
        row |= {
            "case": "many statements",
            "statements": statements,
            "entries_each": each,
        }
        results.append(row)
    return results


def render(results: list[dict]) -> None:
    print(
        f"{'case':<17}{'stmts':>6}{'entries':>9}{'KiB':>8}"
        f"{'best ms':>10}{'entries/s':>12}{'ns/entry':>11}"
    )
    print("-" * 73)
    for row in results:
        print(
            f"{row['case']:<17}{row['statements']:>6}{row['entries']:>9}"
            f"{row['bytes'] / 1024:>8.1f}{row['best_s'] * 1e3:>10.2f}"
            f"{row['entries_per_s']:>12,.0f}{row['ns_per_entry']:>11,.0f}"
        )
    single = [r for r in results if r["case"] == "one statement"]
    if len(single) >= 2:
        drift = single[-1]["ns_per_entry"] / single[0]["ns_per_entry"]
        print(
            f"\nns/entry at {single[-1]['entries']:,} entries is {drift:.2f}x "
            f"the cost at {single[0]['entries']:,}. Flat is linear; a number "
            f"that grows with size means the parser has gone superlinear."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

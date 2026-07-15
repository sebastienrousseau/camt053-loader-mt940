# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Load / stress tests for the MT940 → camt.053 loader.

These tests carry the ``perf`` marker and are excluded from the
default coverage-gated run (see ``addopts`` in ``pyproject.toml``),
mirroring the parent ``camt053`` suite convention. Run them
explicitly with::

    pytest -m perf --no-cov tests/test_stress.py

Three angles are covered:

* sustained concurrent conversions (thread pool, zero-error + p95
  latency assertion),
* a single very large statement (thousands of ``:61:``/``:86:``
  pairs) within a generous wall-clock bound,
* a soak loop asserting bounded memory growth via ``tracemalloc``.

All bounds are deliberately generous so the suite stays green on
slow CI runners; they exist to catch order-of-magnitude regressions
(quadratic parsing, unbounded caching), not micro-slowdowns.
"""

from __future__ import annotations

import gc
import statistics
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor

import pytest

from camt053_loader_mt940 import parse_mt940

pytestmark = pytest.mark.perf

# ─── Payload builders ────────────────────────────────────────────────


def _build_payload(n_entries: int) -> str:
    """Return a valid MT940 payload with ``n_entries`` :61:/:86: pairs."""
    lines = [
        ":20:STRESS-REF-1",
        ":25:COBADEFFXXX/DE89370400440532013000",
        ":28C:42/1",
        ":60F:C260620EUR10000,00",
    ]
    for i in range(n_entries):
        dc = "C" if i % 2 == 0 else "D"
        lines.append(
            f":61:2606210621{dc}R{100 + i % 900},00NMSCBANKREF{i}//CUSTREF{i}"
        )
        lines.append(f":86:Payment detail line {i} / invoice INV-{i:06d}")
    lines.append(":62F:C260622EUR10000,00")
    lines.append(":64:C260622EUR10000,00")
    return "\n".join(lines) + "\n"


def _check_document(payload: str, n_entries: int) -> None:
    """Parse ``payload`` and assert the converted document is sound."""
    doc = parse_mt940(payload)
    assert doc.message_type == "camt.053.001.08"
    assert doc.msg_id == "STRESS-REF-1"
    statement = doc.statements[0]
    assert len(statement.entries) == n_entries
    assert len(statement.balances) == 3


# ─── Sustained concurrent conversions ────────────────────────────────


def test_sustained_concurrent_conversions_zero_errors_p95() -> None:
    """32 workers x 400 conversions: zero errors, generous p95 latency.

    Each task parses a 25-entry statement and validates the result.
    A single conversion takes well under a millisecond on any modern
    machine, so the 250 ms p95 bound only trips on order-of-magnitude
    regressions (e.g. accidental quadratic tokenisation or a lock
    serialising the pure-function parser).
    """
    workers = 32
    iterations = 400
    n_entries = 25
    payload = _build_payload(n_entries)
    latencies: list[float] = []
    errors: list[BaseException] = []

    def _task(_: int) -> float:
        start = time.perf_counter()
        _check_document(payload, n_entries)
        return time.perf_counter() - start

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_task, i) for i in range(iterations)]
        for future in futures:
            exc = future.exception()
            if exc is not None:
                errors.append(exc)
            else:
                latencies.append(future.result())

    assert errors == [], f"{len(errors)} conversion(s) failed: {errors[:3]}"
    assert len(latencies) == iterations
    p95 = statistics.quantiles(latencies, n=20)[18]
    assert p95 < 0.25, f"p95 latency {p95 * 1000:.2f} ms exceeds 250 ms"


# ─── Large single statement ──────────────────────────────────────────


def test_large_statement_parses_within_wall_clock_bound() -> None:
    """A 10,000-entry statement converts correctly within 20 seconds.

    Parsing is linear in the number of fields; 10k entries take well
    under a second in practice. The generous bound guards against a
    regression to super-linear behaviour in the tokeniser.
    """
    n_entries = 10_000
    payload = _build_payload(n_entries)
    start = time.perf_counter()
    doc = parse_mt940(payload)
    elapsed = time.perf_counter() - start

    statement = doc.statements[0]
    assert len(statement.entries) == n_entries
    # Every :86: attached to its preceding :61:.
    assert all(len(e.details) == 1 for e in statement.entries)
    first, last = statement.entries[0], statement.entries[-1]
    assert first.reference == "BANKREF0"
    assert first.account_servicer_ref == "CUSTREF0"
    assert last.reference == f"BANKREF{n_entries - 1}"
    assert elapsed < 20.0, f"10k-entry parse took {elapsed:.2f}s (> 20s)"


# ─── Soak / memory growth ────────────────────────────────────────────


def test_soak_loop_memory_growth_is_bounded() -> None:
    """300 repeated conversions do not accumulate memory.

    The parser is a pure function with no module-level caches, so
    steady-state heap usage must stay flat: after a warm-up phase,
    300 further conversions may not grow traced memory by more than
    5 MiB (a single parsed 50-entry document is a few tens of KiB,
    so a leak of one document per iteration would trip this easily).
    """
    n_entries = 50
    payload = _build_payload(n_entries)

    tracemalloc.start()
    try:
        for _ in range(50):  # warm-up: interned strings, regex cache
            _check_document(payload, n_entries)
        gc.collect()
        baseline, _ = tracemalloc.get_traced_memory()

        for _ in range(300):
            _check_document(payload, n_entries)
        gc.collect()
        current, _ = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    growth = current - baseline
    limit = 5 * 1024 * 1024
    assert growth < limit, (
        f"traced memory grew by {growth / 1024:.0f} KiB over 300 "
        f"iterations (limit {limit / 1024:.0f} KiB)"
    )

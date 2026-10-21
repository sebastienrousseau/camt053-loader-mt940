<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Benchmarks

## Method

[`benches/bench_parse_mt940.py`](../benches/bench_parse_mt940.py) builds
synthetic MT940 payloads along the two axes that grow in practice: entries
in one statement (a month of activity on a busy account) and statements in
one file (a poller collecting several accounts). For each size it parses the
payload five times and reports the best wall-clock time and nanoseconds per
entry.

The figure to read is `ns/entry` across sizes. Flat means parsing is linear
in the input; a number that climbs with size means it has gone
superlinear. Absolute times are for one machine and are not comparable with
another, so CI asserts no threshold; it runs `--quick` to keep the
benchmark working against the current API.

```sh
python benches/bench_parse_mt940.py           # this table
python benches/bench_parse_mt940.py --json    # machine-readable
```

## Results

2026-10-20, commit `d774474`, Apple A18 Pro, CPython 3.12.14, camt053
0.0.20. The machine was shared and busy (load average about 28 during the
run), so treat the absolute numbers as an upper bound.

| Case | Statements | Entries | KiB | Best ms | Entries/s | ns/entry |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| one statement | 1 | 10 | 1.0 | 0.07 | 152,284 | 6,567 |
| one statement | 1 | 100 | 8.9 | 0.53 | 188,206 | 5,313 |
| one statement | 1 | 1,000 | 90.6 | 5.60 | 178,463 | 5,603 |
| one statement | 1 | 5,000 | 465.6 | 35.21 | 141,994 | 7,043 |
| many statements | 10 | 1,000 | 88.6 | 6.31 | 158,433 | 6,312 |
| many statements | 50 | 5,000 | 443.1 | 35.94 | 139,124 | 7,188 |
| many statements | 200 | 20,000 | 1,772.5 | 169.28 | 118,150 | 8,464 |

`ns/entry` at 5,000 entries is 1.07x the cost at 10: linear.

Splitting a file into one statement per `:20:` (0.0.23) did not change the
cost. Interleaved runs of the 0.0.20 and 0.0.23 parsers on one
20,000-entry statement, 40 each, gave a best of 8,492 and 8,102 ns/entry.

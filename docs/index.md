# camt053-loader-mt940

Turn a SWIFT **MT940** customer statement into the same object the rest of the
`camt053` suite already works with. One function, one argument.

```python
from camt053_loader_mt940 import parse_mt940

document = parse_mt940(mt940_text)
```

## Why this exists

MT940 retires in **November 2028**. Until then there is a gap that most
treasury stacks fall into: the bank, the ERP, or the middleware still emits
MT940, while everything downstream — validators, writers, reconciliation —
expects camt.053.

Rather than a converter with its own object model, this returns
`camt053.models.ParsedDocument`, the exact type
`camt053.parse.statement_parser.parse_document` returns. Every downstream
consumer in the suite — the writer, the validator, the reversal builder, the
MCP and LSP servers — then works unchanged. **The conversion is invisible to
the code after it**, which is the whole point.

## The API

### `parse_mt940(text: str) -> ParsedDocument`

| | |
|---|---|
| **`text`** | The MT940 payload. Trailing whitespace and CRLF/LF differences are tolerated, so a file read on Windows and one read on Linux parse identically. |
| **Returns** | A `ParsedDocument` whose `message_type` is `"camt.053.001.08"` — the closest direct camt.053 equivalent of an MT940 final-statement message. |
| **Raises** | `ValueError` if `:20:` is absent, or if a balance or statement line does not match the expected format. **The message names the offending tag**, because a statement file that fails to parse at 3am is only actionable if the error says which line. See [What is *not* rejected](#what-is-not-rejected). |

## What you get back

```python
document.msg_id             # from :20:
document.message_type       # "camt.053.001.08"
document.creation_date_time
document.statements         # one per :20: block
document.all_entries()      # method, not a property
document.to_dict()          # plain dict, JSON-ready
```

Each statement:

```python
statement.id                   # from :28C:
statement.electronic_seq_nb
statement.account              # .iban, .servicer_bic
statement.balances             # opening :60F: through closing :62F:
statement.entries              # one per :61:
statement.entries_with_reason("AC04")  # entries carrying that return reason
```

Each entry:

```python
entry.amount, entry.amount_decimal   # str and Decimal
entry.currency
entry.credit_debit_indicator         # "CRDT" | "DBIT"
entry.booking_date, entry.value_date
entry.reference                      # from :61:
entry.account_servicer_ref
entry.details                        # :86: narrative
entry.reason_code                    # return reason, when present
entry.is_returnable
entry.reversal_indicator
entry.status
```

Use `amount_decimal`, not `amount`, for anything arithmetic. `amount` is the
string as it appeared; `amount_decimal` is a `Decimal`. Money in a float is a
rounding error waiting for a reconciliation to find it.

## What is *not* rejected

`:20:` is the only tag whose absence raises. **`:25:` is optional**, and a
payload without it parses successfully to an account whose `iban` and
`servicer_bic` are both `None`:

```python
document = parse_mt940(payload_without_25)
document.statements[0].account.iban    # None — entries belong to no account
```

That is deliberate leniency, not an oversight, and it is pinned by a
regression test so a future change has to be a decision rather than an
accident. But **check it if you reconcile**: entries attributed to a `None`
account will match nothing, and the failure shows up as an unexplained
reconciliation break rather than as a parse error.

```python
if document.statements[0].account.iban is None:
    raise ValueError("statement carries no :25: account identification")
```

## Field mapping

| MT940 tag | Meaning | Where it lands |
|---|---|---|
| `:20:` | Transaction reference | `document.msg_id` |
| `:25:` | Account identification | `statement.account.iban`, `.servicer_bic` |
| `:28C:` | Statement / sequence number | `statement.id`, `.electronic_seq_nb` |
| `:60F:` | Opening balance | `statement.balances[0]` |
| `:61:` | Statement line | one `Entry` |
| `:86:` | Information to account owner | `entry.details` |
| `:62F:` | Closing balance | `statement.balances[-1]` |

## Worked examples

Both run standalone with no arguments:

- [`examples/01_minimal_parse.py`](../examples/01_minimal_parse.py) — parse a
  small payload and print a summary.
- [`examples/02_round_trip_to_dict.py`](../examples/02_round_trip_to_dict.py) —
  parse, then `to_dict()` for JSON.

## Performance

[`benches/bench_parse_mt940.py`](../benches/bench_parse_mt940.py) sweeps the
two axes that actually move: entries within one statement, and statements
within one file.

```sh
python benches/bench_parse_mt940.py
```

Read the **`ns/entry`** column, not the totals. Flat across sizes means the
parser is linear and a month-end file will be fine. A number that climbs with
size means it has gone superlinear — the failure a unit test cannot see, and
the one a real statement file finds.

Nothing there asserts a threshold, because wall-clock timings are not
comparable between machines. CI runs it with `--quick` so a benchmark that has
stopped compiling against the current API fails the build instead of quietly
rotting.

## Errors

`ValueError` carries the field that failed:

```python
try:
    document = parse_mt940(payload)
except ValueError as exc:
    print(exc)   # names the tag and what was wrong with it
```

There is no partial-parse mode. A statement that half-parsed would produce
balances that do not reconcile against entries, and silently wrong financial
data is worse than a refusal.

## Related

| Package | What it does |
|---|---|
| [`camt053`](https://pypi.org/project/camt053/) | The parser, models and validator this feeds |
| [`camt053-loader-mt942`](https://pypi.org/project/camt053-loader-mt942/) | The same bridge for interim statements |
| [`camt053-writer-xlsx`](https://pypi.org/project/camt053-writer-xlsx/) | `ParsedDocument` to a spreadsheet |
| [`camt053-mcp`](https://pypi.org/project/camt053-mcp/) | The same operations as agent tools |

## Licence

Apache-2.0 OR MIT, at your option.

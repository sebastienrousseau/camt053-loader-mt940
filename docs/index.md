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

### `parse_mt940(text: str, *, strict: bool = True) -> ParsedDocument`

| | |
|---|---|
| **`text`** | The MT940 payload. Trailing whitespace and CRLF/LF differences are tolerated, so a file read on Windows and one read on Linux parse identically. |
| **`strict`** | Default `True`. Rejects a statement whose `:25:` is absent, empty, or names a servicer BIC with no account number. Pass `False` only when the account is known from outside the file. |
| **Returns** | A `ParsedDocument` whose `message_type` is `"camt.053.001.08"` — the closest direct camt.053 equivalent of an MT940 final-statement message. |
| **Raises** | `MissingMandatoryFieldError` (a `ValueError`) if `:25:` identifies no account under `strict`. `ValueError` if `:20:` is absent, or a balance or statement line does not match the expected format. **The message names the offending tag**, because a statement file that fails to parse at 3am is only actionable if the error says which line. |

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

## Mandatory fields

`:20:` and `:25:` are both required. `:25:` has been enforced since **0.0.18**;
before that a statement without it parsed into an account whose IBAN was
`None`.

```python
from camt053_loader_mt940 import MissingMandatoryFieldError, parse_mt940

try:
    document = parse_mt940(payload)
except MissingMandatoryFieldError as exc:
    print(exc.tag)   # "25"
```

**Why it is an error rather than a `None`.** `:25:` is mandatory in the MT940
specification, and `<Stmt><Acct>` is `[1..1]` in the camt.053 model this
loader targets — so the old output was not a valid `ParsedDocument` either. A
statement with no account cannot be routed or booked by an ERP, so passing it
downstream added no value and pushed a defensive `if account is None` onto
every consumer. Anyone following the quick start straight into
`document.statements[0].account.iban` got `AttributeError: 'NoneType' object
has no attribute 'iban'` deep in their own code instead of a clear message at
the boundary.

Three shapes are rejected, not one. Seeing the tag is not the same as being
told which account:

| `:25:` | Result |
|---|---|
| absent | rejected — *is absent* |
| `:25:` (bare) | rejected — *carries no account number* |
| `COBADEFFXXX/` | rejected — names the bank, not the account |
| `COBADEFFXXX/DE89…` | accepted |
| `DE89…` | accepted |
| `1234567890` | accepted — not every account has an IBAN |

### `strict=False`

For genuinely non-compliant legacy feeds where the account comes from the
filename or the SFTP folder rather than the file:

```python
document = parse_mt940(payload, strict=False)
document.statements[0].account.iban = known_iban   # your obligation now
```

It is keyword-only, so `parse_mt940(text, False)` raises `TypeError` rather
than quietly reinstating the old behaviour at a call site that looks like it
is passing an option.

### Still accepted, and arguably should not be

`:28C:`, `:60F:` and `:62F:` are equally mandatory under MT940, and equally
mandatory in camt.053 — `<Stmt><Id>` is `[1..1]`, `<Stmt><Bal>` is `[1..n]`.
All three are currently accepted when absent, producing a statement with a
`None` id or a short balance list. `strict` does not yet cover them. That is a
recorded gap rather than a decision.

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

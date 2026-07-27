# The merge issue: an append-only ledger was rewritten wholesale

**Symptom.** At 05:38Z on 2026-07-27, all three open PRs — #212, #203 and
#181 — went un-mergeable in the same minute, on the same file.  None of them
had touched each other's work.

**Cause.** PR #198 merged at 05:38:51Z carrying this on
`results/cycle_telemetry_purchase.jsonl`:

```
26  25  results/cycle_telemetry_purchase.jsonl
```

Twenty-six insertions and twenty-five deletions, on a file that can only ever
gain one line.  #198 re-serialized all 25 existing rows with **default**
separators —

```
{"axis": "purchase", "batch_size": 1, ...}      # what landed
{"axis":"purchase","batch_size":1,...}          # what the tool emits
```

— and inserted its own row at position 24 rather than appending it.  Every
open PR appends a *canonical* row to the *canonical* base, so after the
rewrite every one of the 26 lines collided.  A ledger that only ever gains a
line cannot conflict; one that gets rewritten conflicts with everything in
flight.

**Nothing was lost.**  All 25 prior rows survive under their
`(sha, branch, ts)` identity; the file gained exactly one genuine row.  This
was a formatting-and-ordering defect, not data loss, and it is recorded that
way rather than as something worse.

## The fix

`results/cycle_telemetry_purchase.jsonl` is rewritten back to what
`tools/cycle_telemetry.serialize_row` emits (`sort_keys=True`,
`separators=(",", ":")`) in the original append order, with #198's row moved
to the tail.  The result restores the pre-#198 prefix **byte-for-byte** —
verified, not asserted — so against `2b17aeab` the file reads as the one-line
append it always should have been, and the open PRs' telemetry conflicts
disappear.

This commit's own diff is necessarily another 26/26 rewrite.  That is the
last one: the teeth below make the next one red.

## Why the teeth did not catch it

`tests/test_cycle_telemetry.py` had three tests on canonical serialization,
and all three stayed green throughout.  Every one of them builds a row, calls
`ct.serialize_row`, and asserts on the string it gets back:

```python
line = ct.serialize_row(row)
assert ", " not in line and ": " not in line
```

**Testing the encoder proves the encoder.**  The committed artifact — the
thing that actually merges — was never read.  So the file could sit 26/26
rows non-canonical without a single assertion noticing.

This is the same shape as the defect #198 itself fixed and wrote a lesson
about (*a tooth parameterized over one of two symmetric callers certifies the
caller it skips*), one layer down: a tooth pointed at the producer certifies
nothing about the product.

Two teeth added, each mutation-verified to bite on its own defect and only
its own:

| tooth | mutation | result |
|---|---|---|
| `test_committed_ledger_rows_are_canonically_serialized` | restore main's non-canonical file | reds, alone |
| `test_committed_ledger_is_append_shaped` | duplicate the tail row | reds, alone |

Both are parameterized over all three axes (`corpus`, `purchase`,
`watchdog`), so the two ledgers that were already clean stay pinned rather
than merely happening to be right.

## What was checked and found clean

Every `results/*.jsonl` was audited for the same drift.  Only
`cycle_telemetry_purchase.jsonl` had it.

`results/lessons.jsonl` reads as non-canonical under the telemetry
definition and **is not a defect**: `tools/lessons.py:153` writes
`json.dumps(row, sort_keys=True)` with default separators by design, and its
history is pure appends (`1/0`, `3/0`, `4/0`, `2/0`, `2/0`).  Its conflicts
in #212 and #203 are ordinary append-append collisions — one line each side,
resolved by taking both — and would have happened with or without #198.

## Bounds

No ceremony-reserved path in the diff: `kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/`
untouched.  No carrier, node class, operator word or trust root grows; P5 not
promoted.  No park recorded or lifted; no refusal recorded.  Lean-free.

Gate: `CGB_LEAN=0 python3 -m pytest tests/ -q` → **1979 passed, 42 skipped**.

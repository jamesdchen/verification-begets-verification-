# C3 cycle 25 — the derived route named five signals and handed the driver a re-wedge

**Product: a selection defect, measured on the live tree and closed
mechanically.**  No source lands and no reading is authored, deliberately: the
first command the brief printed would have laid down seven subjects that
**cannot** return to ready, and authoring them is the cycle-05 re-wedge rather
than a cycle.  The 23 genuinely paid subjects stay as carried-over demand,
and the next cycle is the first that can consume them correctly.

## What happened, in order

Cycle 24 merged; this firing claimed, passed the yield re-query, and read the
brief.  `NEXT-SELECTION` routed `unblocked` — 23 paid subjects, five signals,
one runnable command each, in the derived (alphabetical) order:

```
python3 tools/intake_from_frontier.py --unblocked refused:definition-biconditional --take 8
python3 tools/intake_from_frontier.py --unblocked refused:function-symbol --take 8
python3 tools/intake_from_frontier.py --unblocked refused:iff-connective --take 8
python3 tools/intake_from_frontier.py --unblocked refused:not-connective --take 8
python3 tools/intake_from_frontier.py --unblocked refused:symbolic-exponent --take 8
```

The first command applied cleanly and laid down seven sources (130–136).  They
were **discarded unauthored**, because reading their refusal history first is
what the ledger is for:

| # | node | signals filed | unmet by any landed purchase |
|---|---|---|---|
| 130 | `03_Parity_and_Divisibility#definition-001` | definition-biconditional, **exists-only-shape** | `exists-only-shape` |
| 131 | `#definition-002` | definition-biconditional, **exists-only-shape** | `exists-only-shape` |
| 132 | `#definition-003` | definition-biconditional, **exists-only-shape** | `exists-only-shape` |
| 133 | `#definition-004` | definition-biconditional, **exists-only-shape** | `exists-only-shape` |
| 134 | `#definition-005` | definition-biconditional, **defined-predicate**, **mod-operator** | both |
| 135 | `04_Proofs_with_Structure_II#definition-001` | definition-biconditional, **predicate-variable** | `predicate-variable` |
| 136 | `09_Sets#definition-003` | definition-biconditional, **set-membership** | `set-membership` |

Landed purchases meet exactly `definition-biconditional`, `function-symbol`,
`iff-connective`, `not-connective`, `symbolic-exponent`.  **Every one of the
seven is held by something else.**  The group's returnable count is **zero**.

Cycle 19 already knew this by hand — `wp_c17_readings.py` records the same
subjects being *skipped* for the same reason, and names the cause: "the
selection rule is the frontier's own precedence, applied by hand because
`intake_from_frontier --unblocked` does not apply it."  What was a note in a
docstring is now a mechanism.

## Why the derived route pointed at it

The two instruments disagree at different granularities, and both are
individually correct:

* `purchase_frontier.refill_projection` counts **subjects**, and it counts
  them right: `awaiting_unblock_run = 23`, listed subject-by-subject in
  `awaiting_unblock_subjects`.  Its own honesty note states the rule —
  *"a subject carrying several refusals returns only when ALL of them are
  met, which is why a row can name a group and refill nothing from it."*
* `supply_status._next_selection` names **signals**: every met signal whose
  `refused:` group still holds live nodes.  Per group that is true.
* `intake_from_frontier --unblocked` then selects **that group's nodes**,
  intersecting with nothing.

So the count was right, the route was right, and the selection was wrong — and
because the printed order is alphabetical, `definition-biconditional` is what
an unattended driver reaches **first**.  This was not a latent hazard: it fired
on this firing, on the real tree, on the first command.

## The distance between the two readings

Distinct subjects across the five routed groups: **40**.  Subjects whose whole
refusal set is met: **23**.  Seventeen group memberships are decoration.

| routed group | nodes | returnable | held |
|---|---|---|---|
| `refused:definition-biconditional` | 7 | **0** | 7 |
| `refused:function-symbol` | 16 | 11 | 5 (complex-carrier ×2, set-symbolic-bound, real-carrier, bigop-symbolic-bound+filtered-bigop) |
| `refused:iff-connective` | 8 | 6 | 2 (exists-only-shape, set-membership) |
| `refused:not-connective` | 6 | 3 | 3 (set-membership ×3) |
| `refused:symbolic-exponent` | 12 | 11 | 1 (`fermats_little`, mod-operator) |

## The fix

`--unblocked` now reads `results/purchase_frontier.json` and intersects the
named group with `refill_projection.awaiting_unblock_subjects` — the set the
projection **already** derives and the brief already counts.  The instrument
that knew the rule becomes the filter; no second implementation of precedence
is introduced, so the two cannot drift apart.

Three properties, each deliberate:

* **Every drop is a NOTE.**  A held subject prints `HELD <corpus>/<node>` and
  the signal rule; a group that refills nothing prints `refills NOTHING —
  … That is a live-demand reading, not an empty group`.  A group whose demand
  is still live must never look like a group that is finished.
* **An unreadable projection RAISES.**  Failing open would silently restore
  the exact selection the change forbids, so absence is an error, not an empty
  precedence set.
* **`--ready` is untouched.**  The precedence is an unblocked-mode reading.

Verified live, both directions: `--unblocked refused:definition-biconditional`
now selects nothing and says why; `--unblocked refused:symbolic-exponent`
selects its 8 and holds `formal_book/fermats_little` by name.

## Verification

Two teeth in `tests/test_intake_from_frontier.py`, **mutation-verified**, each
redding exactly its own and nothing else:

| mutation | tooth that reds |
|---|---|
| drop the intersection (select the whole group) | `test_unblocked_holds_a_node_carrying_an_unmet_signal` |
| return an empty set instead of raising on a missing projection | `test_unblocked_refuses_to_select_without_the_precedence_input` |

`tools/regen_downstream.py` re-ran the whole DAG: **every derived artifact is
byte-identical**, which is the intended reading — this changes what the tool
*offers*, never what the corpus *measures*.  Ready stays 11, portfolio stays
7 corpora / 1952 nodes, and `registration.json` is **not** re-baselined,
because no source landed and no census number moved.  No refusal row is
written either: nothing was measured through the gate, and a selection defect
is not a reading (honesty rules — a subject not taken is not a subject
refused).

## Carried-over demand

The 23 paid subjects are untouched and now correctly reachable:
**`symbolic-exponent` 11, `function-symbol` 11, `iff-connective` 6,
`not-connective` 3** (23 distinct; the groups overlap).  The next cycle's
`NEXT-SELECTION` will route `unblocked` again and its first command will now
select real work.  `refused:definition-biconditional` will keep printing
`refills NOTHING` until `exists-only-shape`, `predicate-variable`,
`set-membership`, `defined-predicate` or `mod-operator` is purchased —
which is a **purchase-axis** call, not this loop's, and the five of them are
now legible as priced demand rather than as a group that looks collectable
and is not.

Probe verdict this container: `lean-local`.  Per-commit gate run as
`CGB_LEAN=0 python3 -m pytest tests/ -q` per CLAUDE.md.  A Lean-free cycle:
no `lean-fast` tag, no `FgReflect.lean` edit, no ceremony-reserved path in the
diff, P5 untouched.

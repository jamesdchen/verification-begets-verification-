# Round 1 for `refusal-set-carrier` — a cold start, seeded from the cycle that produced the row

*(the same purchase-driver firing that consumed round 2 of the function-symbol
row and merged PR #160; consuming freed the single slot, so this round could be
authored into it)*

## The purchase that was not made

`python3 tools/lean_env_probe.py`, **run** in this container, never read off
disk:

    lean-absent:not-installed

Not `lean-local`, so PLAN_FRAGMENT §3.1 rule 3's YIELD clause fires and this
unattended session did not take a tower-class bill.

`python3 tools/purchase_frontier.py`, regenerated this session: **13 rows, 3
open, 0 ready**. Not one open row is additive-class —
`refusal-symbolic-exponent` iteration-class, `refusal-function-symbol`
definitional-extension, `refusal-set-carrier` tower-class — so the yield is
TOTAL rather than partial: there is no strictly-first Lean-free half to ship,
because no open row has one. Yielding the purchase is not yielding the
session, so the session took the authoring ride.

## Why this row, and why it is a COLD START rather than a dead end

The channel is single-slot, and after this session's consumption two of the
three open rows have **complete** authoring queues:

| row | class | queue |
|---|---|---|
| `refusal-symbolic-exponent` | iteration-class | closed at r5 (`results/reflect_round5_consumption.md`) |
| `refusal-function-symbol` | definitional-extension | closed at r2 (`results/reflect_p8_round2_consumption.md`, this session) |
| `refusal-set-carrier` | **tower-class** | **no authoring row at all** |

`results/hammer_verdicts.json` carries no authoring row for
`refusal-set-carrier`, which the seed rule names as a COLD START and
explicitly **not** a dead end. So this round is authored rather than reported
as an empty queue.

## The seed is DERIVED, and here is the derivation

This row has no `tests/test_*_class.py` of its own — the two that exist cover
the other two rows. What it has instead is the cycle that produced its refusal
rows, plus §4's narrative, and **both name the missing construct in writing**.
Quoting a committed measurement is derivation; the guess the rule forbids is
inventing a construct no measurement names.

From `results/c3_cycle_16.md` (bold rendered as capitals, otherwise verbatim):

> `set-membership`: **the subject needs the `∈` atom over a set OBJECT, and the
> fragment has no set objects.** P2 bought `setbuild` only as `card`'s
> argument — a bounded, filtered literal interval — so a set can be
> **counted** but never inhabited, named, or compared.

> Kept apart from the connective signals because it names a **different
> purchase**: `iff` and `not` are propositional primitives; this one needs a
> set carrier and its membership atom.

> The signal is for set objects that **survive** unfolding.

The gate verdict the four `refused:set-membership` rows actually carry is
`unknown atom/connective 'mem'`. And PLAN_FRAGMENT §4's P9 narrative supplies
the classification: *"it needs set objects as first-class carrier values
(tower-class)"*.

So the construct is named three ways over two committed artifacts: a set
**carrier** whose objects survive unfolding, and a **membership atom** over it.

## What round 1 takes, and what it deliberately leaves

The measurement lists exactly three capabilities `setbuild` lacks — a set can
be counted but never **inhabited**, **named**, or **compared**. This round
takes the first two and leaves the third:

| declaration | what it answers |
|---|---|
| `StS` | the set CARRIER — set objects as first-class values, which is the tower-class cost |
| `StS.svar` | **NAMED**: an opaque named set, and therefore exactly the set object that SURVIVES unfolding |
| `StS.sicc` | the literal interval re-offered as a first-class OBJECT rather than only as `card`'s argument — the whole difference this row prices |
| `StS.sinter` | intersection, because `09_Sets#definition-003` is one of the two subjects that reached the `mem` atom by probing past `iff` |
| `memS` | **INHABITED**: the membership atom, computable, arm for arm |
| `PdS.pmem` / `denoteS` | membership as a predicate with `Prop` semantics |
| `memS_svar` / `memS_sicc` / `memS_sinter` / `denoteS_pmem` | one `rfl` tooth per arm, so a silent arm cannot pass unnoticed |

**COMPARED is left unmet on purpose** — set equality and subset over set
objects (the shape `09_Sets#problem-005`, `#problem-014` and `#problem-017`
present) is round 2's single requirement, so a regression stays attributable to
one addition. The `Decidable`/checker soundness layer is left to a later round
the same way `refusal-function-symbol`'s r2 followed its r1 rather than riding
inside it. Start small: the smallest tower whose failure transcript is legible
beats a large one whose failure is not, because the transcript IS the next
round's seed.

Neither `sicc` nor `sinter` is a widening: both are named by the measurement.

## The splice constraint, again

A candidate is APPENDED text — the committed `tools/FgReflect.lean` verbatim,
then this text re-entering `namespace FgReflect` — so `Tm` and `Pd` cannot be
extended and a set constructor must live in a **new inductive of its own
naming**. `TmS` is a minimal term tower re-declared for that reason (nothing
the slice declares is reachable as a constructor of a new type), not because
the committed `Tm` is inadequate at what it does.

## What a pass would settle, and what it emphatically would not

A pass would settle that set objects can be first-class carrier values with a
computable membership atom over them — the construct the measurement says the
fragment has nowhere to put. It would **not** touch:

* **the class verdict.** Still tower-class, still OPEN, still attended-only
  under §3.1 rule 3.
* **the ceiling, which this row records against its own interest.** The
  derived queue is the number that counts, and it is not the one §4's prose
  carries — `results/purchase_frontier.json` computes
  `refused_group_memberships: 4`,
  `held_by_a_signal_this_row_does_not_meet: 4`, `returns_to_ready: 0`. All
  **four** `set-membership` subjects carry a refusal this row does not meet, so
  it returns **ZERO** subjects to ready on its own and lands material only
  behind P6 — the reading P9's narrative states against its own interest
  (*"A large purchase against a small measured demand is the reading this row
  should carry rather than bury."*), and it survives the correction below
  **stronger**, not weaker.

## A stale count measured on the way past, and left for an attended fix

PLAN_FRAGMENT §4's P9 line still reads *"refusal-priced: 2 subject-rows"*, and
that is now **stale prose, not a disagreement about the world**: it was true
when cycle 16 wrote it, and cycle 19 measured two more `set-membership`
subjects into the append-only ledger (`measured_by: C3 cycle-19 driver
measurement`). The ledger carries four rows with four distinct
`subject_sha256`, and the derived frontier agrees at 4. Recompute beats
recollection, so this receipt uses 4 throughout and the brief's own
`refusal-set-carrier` count (4) is the live reading. No prose was edited to
match — §4 is narrative, the artifact is the instrument, and rewriting a §4
line is not this session's act.
* **the slice.** `tools/FgReflect.lean` is untouched; the candidate queue has
  no write path to it. A passed candidate is a PROPOSAL, and adopting one is
  an attended purchase decision under the ordinary bill discipline.

"It elaborated in the batch ride" is a reason to keep authoring and never a
done-predicate; the CI lane verdict stays final.

## Bounds

No ceremony-reserved surface touched. P5 remains a trust root this session did
not promote. Batch reproduces at **24 goals** (`queued=114, unresolved=0`) with
`+1 authoring` candidate, and the readout is regenerated from the new batch so
its reproduction teeth stay green. Ride marker written unbracketed as
lean-hammer everywhere except the ride commit message itself.

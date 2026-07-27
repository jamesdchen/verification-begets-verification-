# `refusal-set-carrier`: the price is the SWEEP DOMAIN, not the tower

**No purchase priced.**  This firing took the one open row on the derived
queue, and measured a constraint that sits *underneath* every price the row
has carried so far.  Probe verdict **`lean-local`** (RUN here, never read off
disk), so §3.1 rule 3's yield clause did not fire and the tower-class attempt
was licensed.  `tools/FgReflect.lean` is **byte-unchanged** in this diff — a
half-threaded tower is never shipped into a certified slice.

The product is a re-pricing of the row plus the Lean round that proves it,
queued on the authoring channel.

## What the row has been billed at, and why each estimate was under

| source | the stated price |
|---|---|
| PLAN_FRAGMENT §4 | "an uninterpreted predicate in the SMT mirror and a `Pd` constructor plus its `Decidable` story" |
| `results/p10_bill_measurement.md` (PR #203) | + threading a set environment through the slice's ~50 explicit `env` signatures; the typeclass shortcut is fenced by the escape gate |

Both are true.  Neither is binding.  A third cost dominates them, and it is
not a cost in the slice at all.

## The finding

A free set variable is not only a PREDICATE-layer atom.  In the emitted
statement it is a **BINDER** — and every binder in this pipeline is decided
by **sweeping its box-relativized domain**.  For an Int variable that domain
is the box.  For a set variable it is the **powerset of the box**.

Proven, not asserted.  Queued authoring round `p9-parallel-tower-r3`
(`results/reflect_candidates.json`) carries r2's passed text forward verbatim
and adds exactly one layer: the statement type with both binder kinds
(`StmtS.ssallS` is the set binder), the box-relativized semantics, the sweep,
and two theorems.

```lean
theorem checkStmtBoxS_sound (box : List Int) (sbox : List (Int -> Bool)) : ...
theorem subsetsOfS_length : (b : List Int) -> (subsetsOfS b).length = 2 ^ b.length
```

**The soundness theorem GOES THROUGH.**  That is the load-bearing half of the
round: the tower is *not* blocked by proof obligations.  What the sweep is
sound *relative to* is `sbox` — and `subsetsOfS_length` prices exactly that.
Elaborated in this container, spliced after the committed slice: **green**.

### The arithmetic, against the repo's own constants

`tests/test_set_carrier_box_domain.py` derives every number below —
box widths from `math_eval._box_size`, the ceiling from
`math_eval.EXISTS_SHADOW_MAX_ASSIGNMENTS`, the bound from `run/anchor.py::BOUND`.
Nothing is a literal, so a re-bound of the gate re-prices the row automatically.

| shape | domain | vs ceiling (2,000,000) |
|---|---|---|
| one set binder, Int box (17 values) | 131,072 | under |
| one set + **one** ordinary Int object | 2,228,224 | **over** |
| lead subject: two sets + one Int | **292,057,776,128** | **146,028×** |
| one set + one Nat object (Nat box, 9) | 4,608 | comfortably under |

The lead subject is `09_Sets#definition-003` — the row's entire measured
inventory, one subject.  It defines **intersection over two sets** the source
gives no comprehension for, so it carries the set binder *twice*.  That shape
is the committed class measurement's, not this receipt's
(`tests/test_set_object_class.py::test_definition_003_needs_arbitrary_sets_and_stays_held`).

## Why the wall cannot be walked around

Two structural facts, both verified against the code and both pinned by teeth
that were **mutation-verified in both directions**.

**1. The bounded shadow is MANDATORY, so the SMT mirror cannot carry it.**
§4's "uninterpreted predicate in the SMT mirror" would be the way around a
powerset — z3 handles an uninterpreted predicate symbolically, with no
enumeration at all.  But SMT can never carry a reading here.
`run/formalize.py`'s stage 4 (the instances gate) has **no SMT variant**: both
arms, `_instances` and `_exists_instances`, are pure `math_eval`.  The SMT
mirror is reached only from `_nonvacuity`, and only over **hypotheses** — it
never sees the conclusion.  So the enumeration is not one evidence channel
among several; it is the one that decides.

**2. The ∀ path has NO combinatorial ceiling at all — so a paid-for tower
would not refuse honestly, it would simply not stop.**
`EXISTS_SHADOW_MAX_ASSIGNMENTS` is consulted at exactly one site, inside
`exists_shadow_shape`, which returns `forall-only` *before* the ceiling
arithmetic whenever the reading has no ∃ binder.  The ceiling guards the ∃
path only.  The lead subject is a **definition** — ∀-only — so it would never
reach the guard: there is no `exists-domain-too-large` skip waiting for it,
because that skip lives on the other branch.

That second fact is worth separating from this row, because it is a live
property of `main` today and not a purchase question: the ∀ path's
`boundary_probes` runs one unbroken pass over `enumerate_domain` with no
budget, and the ∃ ceiling's own comment names the "minutes-plus regime" it
exists to cut off.  The ∀ path has no equivalent.  Recorded here as a
reading; **not** driven as work by this firing.

## What this re-prices

The row's *status* is unchanged — **OPEN**.  What changes is its shape, and
the change is the P8/P9 finding a third time: **two rungs wearing one name.**

* **At the Int carrier the row is not expensive, it is outside the
  pipeline's decision procedure.**  Its first non-trivial shape already
  exceeds the only ceiling the gate has, and its lead subject exceeds it by
  five orders of magnitude.
* **At a Nat box the identical construct is small** — 512 per set binder,
  4,608 beside an ordinary object.  A set-carrier row scoped to Nat is an
  ordinary bill.

So the honest next move on this row is a **split by carrier**, priced apart,
exactly as P8 split `function-symbol` and P9 split `set-membership`.  Naming
that split is a §4 / maintainer call, not an unattended session's, so this
firing records the measurement and does not edit the queue's declarations.

Standing and unchanged: this row returns **zero** subjects to ready and
refills nothing on its own.

## Bounds

`tools/FgReflect.lean` byte-unchanged.  No ceremony-reserved surface in the
diff — `kernel/certs.py`, `TRUST.md`, `buildloop/growth_protocol.py`,
`buildloop/validate_lean.py`, `setup.sh`, `ci/`, `.claude/`, `.github/` all
untouched.  P5 not promoted.  No park recorded or lifted; no refusal recorded
(nothing here is a reading about a corpus subject — the wall is the
pipeline's, not a source's).  Ledgers append-only.  **No purchase priced, so
no flywheel slot spent and no re-census delta owed.**  Titled `C3 authoring:`
deliberately: an authoring ride buys no purchase and must stay invisible to
the in-flight guard.

The lane's commit-back carries zero check runs and is never merged; a later
session re-commits any verdict under its own credentials.

**Gate**: `CGB_LEAN=0 python3 -m pytest tests/ -q` (the per-commit gate in a
lean-local container, per CLAUDE.md's full-gate row).

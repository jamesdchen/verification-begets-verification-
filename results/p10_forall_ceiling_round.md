# The forall-side ceiling, authored as a parallel tower (round 5)

**No purchase priced.**  The one open row on the derived queue is
`refusal-set-carrier`.  Probe verdict **`lean-local`** (`tools/lean_env_probe.py`
RUN in this container, never read off disk), so PLAN_FRAGMENT §3.1 rule 3's
yield clause did **not** fire and the tower-class attempt was licensed.  This
firing spent that licence on the AUTHORING channel rather than on the bill, and
the reason is measured rather than cautious — see "Why not the bill" below.

Titled `C3 authoring ...` deliberately: an authoring ride buys nothing and
spends no flywheel slot, so it must stay invisible to the in-flight guard.
**Retitled before the ride push**, per the measured `bill-manifest` title-keying
hazard.

## First: the authoring channel was FREE, and this closes a round

The single-slot channel (`results/reflect_candidates.json`) carried
`p9-parallel-tower-r4`, whose committed lane verdict is **PASSED**
(`gate_ok=true elaborated=true replayed=true`, axioms `Quot.sound, lcProof,
propext`).  No `C3 authoring ...` PR was open, so there was nothing to consume
and nothing to defer to: the slot was free and this round fills it.

Per the seed rule's **PASSED** branch — the row's `detail` is null by design,
so there is nothing to drive from and the rule says EXTEND toward the next
requirement the class measurement still names as unmet.

## The requirement r4 left unmet

`tests/test_set_carrier_box_domain.py::test_the_forall_path_has_no_combinatorial_ceiling_at_all`
measures, against `generators/math_eval.py` itself, that
`EXISTS_SHADOW_MAX_ASSIGNMENTS` is consulted at exactly **one** site — inside
`exists_shadow_shape`, which returns `forall-only` **before** the ceiling
arithmetic.  So the pipeline's only combinatorial ceiling guards the ∃ path,
and the ∀ path has none.

r4 built the set-binder sweep, proved it **sound**, and priced its domain at
`(2 ^ |box|) ^ n`.  What r4's checker does with that price is sweep it anyway:
`checkStmtBoxS` folds `sbox` unconditionally.  On this row's lead subject —
`09_Sets#definition-003`, a **definition** (∀-only) with two set binders,
292,057,776,128 leaf checks at the committed Int box — it would not answer and
would not honest-skip.  It would run.

**A verdict that cannot be reached is worse than a verdict of "too large":
the second is a reading, the first is a hang.**

## What round 5 adds — exactly one layer

r4's text is carried forward **verbatim**, so any regression is attributable.
The new layer is a budgeted verdict and the two theorems that make it a reading
rather than a quiet weakening:

| declaration | what it establishes |
|---|---|
| `costStmtS` | the sweep's leaf count, structurally: object binder × box, set binder × `sbox` |
| `inBudgetS`, `checkStmtFuelS` | the budgeted sweep; `none` is the honest skip |
| `checkStmtFuelS_sound` | **soundness survives the budget** — `some true` still implies the box denotation, so the budget subtracts answers and never adds them |
| `checkStmtFuelS_none_of_over_budget` | **honest in the other direction** — over budget the verdict is `none` |
| `checkStmtFuelS_ne_pass_of_over_budget` | and therefore never `some true`: a skip can never impersonate a pass |
| `lead_subject_cost_is_the_squared_powerset` | the price tied back to r4's own `subsetsOfS_length`, not a fresh number |
| `lead_subject_is_over_any_budget_below_its_domain` | the lead subject's shape declines at **every** budget below its domain — stated over the budget, so it prices the shape and not a remembered constant |

So a gate **can** acquire a forall-side ceiling without weakening what it
certifies, and that is now a theorem rather than a plan.

## The channel's own bound, measured while authoring

The round was first authored with `inductive VerdictS | holds | failed |
tooLarge`.  It elaborates and kernel-replays cleanly and **still fails the
ride**: its compiled form carries `lcUnreachable`, outside the measured constant
whitelist.  Bisected here rather than guessed — three probes, one elaboration
each:

| probe | verdict |
|---|---|
| direct `Nat` recursion over `StmtS` (3 constructors, **with fields**) | clean |
| the parameterized `costStmtS`, pattern-matched | clean |
| the nullary `VerdictS` enum + one `cond` | **`lcUnreachable`** |

So the rule is sharper than "avoid new inductives": it is the **nullary-only
enum** specifically.  Lean unboxes an all-nullary inductive to a scalar tag and
its `casesOn` compiles to a jump table with an unreachable default; `StmtS`
escapes precisely because its constructors carry fields.  Routing around it
through `StmtS.rec` does not work either — `code generator does not support
recursor 'FgReflect.StmtS.rec'`, so the definition has no executable code and
every dependent fails the IR check.

`Option Bool` carries the same three readings with no new type at all: `none`
**is** the honest skip.

That is the third instance in this lineage of one rule — r4 already records
`List.contains` specializing into its own constant and `List.map` lifting a
closure.  **The whitelist is a trust root; the candidate is what moves.**

One more thing the escape gate caught, and it is worth stating because it costs
a whole elaboration to learn: `buildloop/validate_lean.py` scans the **composed
bytes including comments**, so a doc comment that merely uses the word for a
blocklisted token is refused (`blocklisted token 'axiom' present`).  The prose
had to be reworded, not the code.

## Why not the bill

The purchase was licensed and was still declined, for a reason that is
committed on `main` rather than argued here.  The row's whole measured
inventory is one subject, and
`test_the_lead_subject_is_outside_the_pipelines_decision_procedure` prices that
subject's domain five orders of magnitude past the only ceiling the gate has,
while `test_a_single_set_binder_plus_one_ordinary_object_already_exceeds_the_ceiling`
shows there is no cheap corner of it at Int.  Paying the tower-class bill in
full therefore buys a tower that cannot decide the demand it prices — and, per
the forall measurement above, would hang rather than skip on it.

**Attendance was never this row's binding constraint.**  A forall-side ceiling,
or a subject at a smaller carrier, is — and this round authors the first of
those two as a proved prototype.

This is the fourth consecutive firing to decline the row (#203, #212, #216, this
one).  #216 is open and unmerged and ships the instrument that would stop a
fifth from re-deriving it (`decision_domain` on the frontier row); nothing here
duplicates it, and this firing deliberately did not re-ship it.

## Verification

Local: composed exactly as the ride composes (committed `tools/FgReflect.lean`
verbatim, then the candidate re-entering `namespace FgReflect`) and run through
the **same** `run/reflect_ride.verify_candidate`:

```
gate_ok=true  elaborated=true  replayed=true  declared_missing=[]
axioms=[Quot.sound, lcProof, propext]   passed=true
```

**A local green is necessary and never sufficient** — the CI Lean lane remains
the done-predicate, and this ride is what asks it.

Batch reassembled from **both** inputs (`--queue` and `--candidates`):
`24 goals (queued=118, unresolved=0) +1 authoring`, and the readout regenerated
from the new batch so its reproduction teeth stay green.

## Bounds

`tools/FgReflect.lean` **byte-unchanged** — a candidate is a PROPOSAL and the
queue has no write path to the slice; adopting a passed round is an ordinary
authored edit in a later session, never this one's act.  `generators/math_eval.py`
untouched: whether the pipeline should adopt a forall-side ceiling is a decision
this round prices and does not take.  No ceremony-reserved surface in the diff —
`kernel/certs.py`, `TRUST.md`, `buildloop/growth_protocol.py`,
`buildloop/validate_lean.py`, `setup.sh`, `ci/`, `.claude/`, `.github/`
untouched; the constant whitelist and the escape-gate blocklist were **read**,
never widened.  P5 not promoted.  No refusal and no park recorded — nothing here
is a reading about a corpus subject.  Ledgers append-only.  No purchase priced,
so no flywheel slot spent and no re-census delta owed.

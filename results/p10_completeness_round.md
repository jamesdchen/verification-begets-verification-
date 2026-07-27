# P10 round 6 — a ceiling that declines everything is sound, and useless

Receipt for the purchase firing of 2026-07-27T08:04Z.  **No purchase priced.**
The one open row on the derived queue is `refusal-set-carrier`.  Probe verdict
**`lean-local`** (`tools/lean_env_probe.py` RUN in this container, never read
off disk), so PLAN_FRAGMENT §3.1 rule 3's yield clause did **not** fire and the
tower-class attempt was licensed.  It was declined anyway, on evidence
committed to `main`, and the licence was spent on the authoring channel.

## First: the channel was CONSUMED, not deferred to

`results/reflect_candidates.json` is single-slot, and an open `C3 authoring ...`
PR owns it.  **#222** was open and its lane had **finished** — its tip
`7eb3be9` was the lane's own commit-back (`[skip ci]`, pushed with
`GITHUB_TOKEN`), which is why the PR carried **zero check runs**.  A tip with
no checks is exactly what the self-merge rule's missing-check refusal exists to
stop, so it could not merge as it stood.

The measured failure mode here is not a wrong decision, it is a correct one
repeated: consecutive firings each deferring to an open ride while the channel
runs exactly once.  So this session consumed it — merged `main` (the lessons
ledger conflicted append-against-append and was union-resolved; 51 rows, 51
distinct), re-derived the readout, ran the gate, **re-committed under its own
credentials** (which is what re-arms the checks), pushed, and merged #222 at
**22 green checks including `trust-surface`**.

```
reflect_ride report: verdicts=complete lean_available=True
  candidates=1  passed=1  failed=0  not-run=0
  [PASSED] p9-parallel-tower-r5
```

So round 5's forall-side ceiling is now **the CI Lean lane's verdict** — this
loop's done-predicate — rather than one container's local green.

## The requirement r5 left unmet, and it is a vacuity gap

r5 proved the budgeted sweep honest in two directions: `some true` still
implies the box denotation (`checkStmtFuelS_sound`), and over budget the
verdict is `none` and never `some true`
(`checkStmtFuelS_none_of_over_budget`, `checkStmtFuelS_ne_pass_of_over_budget`).

Both of those are satisfied by a checker that returns `none` **always**.

That is the gap this round closes.  Soundness plus over-budget honesty does not
yet say the ceiling affords anything at all, and a ceiling that declines
everything would price the row's demand exactly as badly as no ceiling — it
would merely fail loudly instead of hanging.  The class measurement
(`tests/test_set_carrier_box_domain.py`) names the other side explicitly:
`test_the_same_construct_is_tractable_at_the_Nat_box` measures that at a
smaller carrier the identical construct is small, *"the reason this is a
re-pricing rather than a refusal"*.  Nothing in r5's Lean touches that half.

## Round 6 — one layer, r5 carried forward verbatim

| declaration | what it establishes |
|---|---|
| `checkStmtFuelS_some_of_in_budget` | **completeness**: a shape the budget can pay is never skipped, and the answer is exactly r4's unbudgeted verdict |
| `checkStmtFuelS_eq_none_iff` | the skip is **exactly** the over-budget case — the ceiling is a total function of the price, not a licence to refuse |
| `single_set_binder_cost` | the tractable rung's shape priced: `2 ^ |box| * |box|` |
| `the_second_set_binder_costs_a_whole_powerset_more` | the gap between the rung that answers and the rung that cannot is exactly one factor of `2 ^ |box|`, **whatever the carrier** |
| `single_set_binder_answers_in_budget` | the tractable rung **answering**, at any budget affording its price |
| `one_budget_separates_the_two_rungs` | a **single** ceiling answers one binder and declines two, at any non-empty box |

The last one is the class measurement's split proved rather than tabulated.
`test_the_same_construct_is_tractable_at_the_Nat_box` states it as two
arithmetic facts at two remembered box widths; here it is one theorem over the
box, so it prices the **shape** and cannot rot into a remembered constant —
the same discipline r5 applied to `lead_subject_is_over_any_budget_below_its_domain`.

## Verification

Composed exactly as the ride composes and run through the **same**
`run/reflect_ride.verify_candidate`:

```
gate_ok=true  elaborated=true  replayed=true  declared_missing=[]
axioms=[Quot.sound, lcProof, propext]   passed=true
```

**A local green is necessary and never sufficient** — the CI Lean lane remains
the done-predicate, and this ride is what asks it.

Two elaborations, not a search: the first failed on one step, where `simpa`
normalized `1 < 2 ^ box.length` into `¬box = []` and left the term at
`2 ≤ 2 ^ box.length`.  Replaced with an explicit `Nat.lt_of_lt_of_le`.  That
iteration is what the `lean-local` capability actually buys — the round was
authored against a real elaborator instead of being posted to the lane to find
out.

Batch reassembled from **both** inputs: `24 goals (queued=118, unresolved=0)
+1 authoring`; readout regenerated from the new batch so its reproduction teeth
stay green.

## Why not the bill

The purchase was licensed by the probe and was still declined, on evidence
already committed to `main`:
`test_the_lead_subject_is_outside_the_pipelines_decision_procedure` prices the
row's whole measured inventory — one subject, `09_Sets#definition-003` — at
292,057,776,128 leaf checks against a 2,000,000 ceiling, and
`test_a_single_set_binder_plus_one_ordinary_object_already_exceeds_the_ceiling`
shows there is no cheap corner of it at Int.  Paying the tower-class bill in
full buys a tower that cannot decide the demand it prices, and per r5's
forall measurement would **hang** rather than honest-skip on it.

**Attendance was never this row's binding constraint.**  A forall-side ceiling
is — and rounds 5 and 6 now carry it as far as a prototype can go without an
adoption decision.

Fifth consecutive firing to decline this row (#203, #212, #216, #222, this
one).  What distinguishes this one from a fifth re-derivation: it closed the
channel #222 opened (the lane verdict is new), and it authored the layer that
turns r5's honesty from vacuous into a split.

## Bounds

`tools/FgReflect.lean` **byte-unchanged** — a candidate is a PROPOSAL and the
queue has no write path to the slice; adopting a passed round is an attended
purchase decision under the ordinary bill discipline, never an unattended
session's act.  `generators/math_eval.py` untouched: whether the pipeline
should adopt a forall-side ceiling is a decision these rounds **price and do
not take**.  No ceremony-reserved surface in the diff — `kernel/certs.py`,
`TRUST.md`, `buildloop/growth_protocol.py`, `buildloop/validate_lean.py`,
`setup.sh`, `ci/`, `.claude/`, `.github/` untouched; the constant whitelist and
the escape-gate blocklist were **read**, never widened.  P5 not promoted.  No
refusal and no park recorded — nothing here is a reading about a corpus
subject.  Ledgers append-only.  No purchase priced, so no flywheel slot spent
and no re-census delta owed.

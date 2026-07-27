# Round 7: one fixed ceiling, and the rung a subject lands on is its carrier

Receipt for the C3 purchase firing of 2026-07-27T09:05Z (PR #226).  No purchase
priced; the licence the probe granted was spent on the authoring channel.

## The purchase decision, and why it is not attendance

`tools/lean_env_probe.py` RUN in this container (never read off disk) returned
**`lean-local`**, so PLAN_FRAGMENT §3.1 rule 3's yield clause did **not** fire
and the tower-class attempt was licensed.  The row was declined anyway, on
evidence committed to `main`:

| | box width | one set binder + one object | two set binders + one object |
|---|---|---|---|
| Int (`2*8+1`) | 17 | **2,228,224** | 292,057,776,128 |
| Nat (`8+1`) | 9 | 4,608 | 2,359,296 |
| ceiling (`EXISTS_SHADOW_MAX_ASSIGNMENTS`) | | **2,000,000** | 2,000,000 |

`refusal-set-carrier`'s whole measured inventory is one subject,
`09_Sets#definition-003` — Int, two set binders.  Paying the tower-class bill
in full buys a tower that cannot decide the demand it prices, and per r5's
forall measurement it would **hang** rather than honest-skip on it.  Attendance
was never this row's binding constraint, so a session with a local toolchain
declines it for exactly the same reason a session without one does.

That is now the sixth consecutive firing to decline this row (#203, #212, #216,
#222, #224, this one).  What keeps it from being a sixth re-derivation is
below: this firing **closed** the channel #224 opened, and authored the layer
that turns r6's split into the pipeline's split.

## First: the channel was CONSUMED, not deferred to

`results/reflect_candidates.json` is single-slot, so an open `C3 authoring ...`
PR owns it and no further round is possible until it lands.  #224 was that PR
and its lane had **finished** — tip `0a26352`, the lane's own `cgb-ci`
commit-back, `[skip ci]`, pushed with `GITHUB_TOKEN`, therefore **zero check
runs**.  Consumed here: readout re-derived, gate run, re-committed under this
session's credentials, merged at four green checks including `trust-surface`.

```
reflect_ride report: verdicts=complete lean_available=True
  candidates=1  passed=1  failed=0  not-run=0
  [PASSED] p9-parallel-tower-r6
```

Details and the empty-commit defect that consumption measured:
`results/p10_r6_consumption.md`.

## The requirement r6 left unmet

r6 separated the rungs by **binder count**, at the budget that exactly affords
the cheaper one (`one_budget_separates_the_two_rungs`, over any non-empty box).
That is a real split and it is **not the one the pipeline has**.

The pipeline carries a *single fixed number* that does not move with the box.
So what decides whether a shape is answered is the box **width** — and the
width is set by the **carrier**.  Under a fixed ceiling the split falls
somewhere r6's budget cannot see: at the Int box even **one** set binder is
already over, while at the Nat box one is under and two are over.

The class measurement names both halves — `test_a_single_set_binder_plus_one_
ordinary_object_already_exceeds_the_ceiling` and `test_the_same_construct_is_
tractable_at_the_Nat_box`, the latter called *"the reason this is a re-pricing
rather than a refusal"* — and no round of the lineage had touched either.

## Round 7 — one layer, r6 carried forward verbatim

| declaration | what it establishes |
|---|---|
| `committedCeiling`, `intBoxWidth`, `natBoxWidth` | the three committed numbers, as literals cited to their sources |
| `one_binder_cost_is_monotone_in_the_box_width` | the price never falls as the box grows — so a fixed ceiling partitions widths into a prefix it answers and a tail it declines |
| `single_set_binder_answers_at_the_Nat_box` | the tractable rung **answered by the committed ceiling**, not by a budget chosen to fit |
| `two_set_binders_decline_at_the_Nat_box` | at that carrier the committed ceiling *is* r6's separating budget |
| `one_binder_declines_at_any_box_at_least_as_wide_as_the_Int_box` | the **threshold**, stated over the width rather than at it |
| `the_committed_ceiling_splits_the_carriers` | the conjunction: one ceiling, one construct, opposite verdicts by carrier |

The threshold theorem is deliberately stated over the width, so a re-bound of
`run/anchor.py::BOUND` widens the declining tail instead of invalidating the
statement — the same discipline r5 applied to
`lead_subject_is_over_any_budget_below_its_domain`.

**What this says about the row.**  `refusal-set-carrier` is two rungs wearing
one name, and which rung a subject lands on is decided by its carrier and its
binder count — never by how well the tower is authored.  That is the reading
the row should carry, and it is now proved rather than tabulated at two
remembered widths.

## Verification

Composed exactly as the ride composes, through the same
`run/reflect_ride.verify_candidate`:

```
gate_ok=true  elaborated=true  replayed=true  declared_missing=[]
axioms=[Classical.choice, Quot.sound, lcProof, propext]   passed=true
```

The axiom set gains `Classical.choice` relative to r6 (`norm_num`'s
arithmetic).  It is inside `run/reflect_ride.py::AUTHORING_AXIOM_WHITELIST`,
which is Lean's benign core set plus `lcProof` — recorded rather than passed
over, because a widening axiom set is the kind of drift a pass can hide.

**A local green is necessary and never sufficient**: the CI Lean lane remains
the done-predicate, and this ride is what asks it.  One elaboration, no search
— which is what `lean-local` buys.

Batch reassembled from **both** inputs: `24 goals (queued=118, unresolved=0)
+1 authoring`; readout regenerated so its reproduction teeth stay green.

## Bounds

`tools/FgReflect.lean` **byte-unchanged** — a candidate is a PROPOSAL and the
queue has no write path to the slice.  `generators/math_eval.py` untouched:
whether the pipeline should adopt a forall-side ceiling is a decision these
rounds **price and do not take**, and adopting a passed prototype is an
attended purchase decision under the ordinary bill discipline.  No
ceremony-reserved surface in the diff — `kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `buildloop/validate_lean.py`, `setup.sh`,
`ci/`, `.claude/`, `.github/` untouched; the escape-gate blocklist and the
constant whitelist were **read**, never widened.  P5 not promoted.  No refusal
and no park recorded — nothing here is a reading about a corpus subject.
Ledgers append-only.  No purchase priced, so no flywheel slot spent and no
re-census delta owed.

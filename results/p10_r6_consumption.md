# Consuming round 6: the lane's verdict on the completeness dual

Receipt for the consumption half of the C3 purchase firing of 2026-07-27T09:05Z
(claim PR #226).  The authoring channel is single-slot -- there is exactly one
`results/reflect_candidates.json` -- so an open `C3 authoring ...` PR owns it and
no further round is possible until it lands.  #224 was that PR and its lane had
FINISHED, so this firing closed the slot rather than deferring to it.

## What the lane returned

```
reflect_ride report: verdicts=complete lean_available=True
  candidates=1  passed=1  failed=0  not-run=0
  [PASSED] p9-parallel-tower-r6
```

`gate_ok=true  elaborated=true  replayed=true  declared_missing=[]`, axioms
`Quot.sound, lcProof, propext` -- inside `run/reflect_ride.py::
AUTHORING_AXIOM_WHITELIST`.

So round 6's completeness dual is now **the CI Lean lane's verdict** -- this
loop's done-predicate -- rather than one container's local green.  What r5 left
vacuous is closed: soundness plus over-budget honesty are both satisfied by a
checker that returns `none` always, and `checkStmtFuelS_some_of_in_budget` plus
`checkStmtFuelS_eq_none_iff` rule that out -- the skip is exactly the
over-budget case, a total function of the price rather than a licence to refuse.

## Why the tip could not merge as it stood

#224's tip `0a26352` was the lane's OWN commit-back: author `cgb-ci`, message
`ci(lean-hammer): batched ride verdicts + readout [skip ci]`, pushed with
`GITHUB_TOKEN`, which fires no workflows.  That tip carried **zero check runs**,
and a tip with no checks is precisely what the self-merge rule's
missing-`trust-surface` refusal exists to stop.  Re-committing under session
credentials is what re-arms them.

## MEASURED HERE, and it is a defect in how that re-commit was done

The first re-commit attempt was `git commit --allow-empty` -- an empty
consumption commit, on the reasoning that the readout regenerated
byte-identically and there was nothing to add.  It pushed cleanly
(`0a26352..82d4825`) and produced **no workflow runs at all**: not
`trust-surface`, not `regression`, nothing.  25 minutes later the PR still read
`total_count: 0` check runs while `mergeable_state` read `clean`.

The re-commit had therefore failed at the one job it exists to do.  An empty
commit changes no paths, so every workflow with a path filter declines it and
the run list stays empty -- the tip is left in exactly the checkless state the
lane's own commit-back was in, wearing session credentials instead of
`GITHUB_TOKEN`.

The diagnosis matters more than the fix: this is NOT the cycle-24
missing-check shape.  `mergeable_state` was `clean`, so there was no merge
conflict and no altered CI config -- the third cause of a missing check is a
head commit that touches nothing.  Reading it as either of the other two would
have sent the next firing hunting a conflict that does not exist.

**So a consumption commit must carry content.**  This receipt is that content,
and the rule it records is: the act that re-arms the checks is a commit with a
diff, never merely a commit with credentials.

## Bounds

`tools/FgReflect.lean` byte-unchanged; `results/reflect_candidates.json`
unchanged by this commit (round 6 stands exactly as the lane verified it).  No
ceremony-reserved surface touched.  No purchase priced.  Gate:
`CGB_LEAN=0 python3 -m pytest tests/ -q` -> 2002 passed, 42 skipped.

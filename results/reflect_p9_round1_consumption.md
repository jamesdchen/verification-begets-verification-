# Consuming round 1 for `refusal-set-carrier` — the carrier and its membership atom PASSED

*(a purchase-driver firing that found the in-flight guard clear, YIELDED the
bill on a measured probe verdict, and spent itself closing the single-slot
authoring channel PR #162 was holding)*

## Why this commit exists

The channel is SINGLE-SLOT — there is exactly one
`results/reflect_candidates.json` — so an open `C3 authoring ...` PR OWNS it
and no further round is possible until that PR lands. Consuming means CLOSING
THE SLOT, not reading a file. Deferring to a FINISHED ride is the 2026-07-26
wedge that ran this route exactly once and then stalled for three firings,
each firing reasoning correctly and each stopping. This firing did not defer.

PR #162's lane had finished: the commit-back `3a772e7`
(`ci(lean-hammer): batched ride verdicts + readout [skip ci]`) landed, and
that authoring PR's own follow-up commits (`db53ad7`, `ab8f946`) had already
re-armed the checks the `GITHUB_TOKEN` tip could not fire — `get_check_runs`
on #162 reads `trust-surface: success`, `bill-manifest: skipped`,
`hammer: skipped`. This commit is the consumption that closes the slot and
frees it for round 2.

## The readout

`python3 run/reflect_ride.py --verdicts results/hammer_verdicts.json
--batch results/hammer_batch.json`, run this session:

    reflect_ride report: verdicts=complete lean_available=True
      candidates=1  passed=1  failed=0  not-run=0
      [PASSED] p9-parallel-tower-r1
        declares=TmS,evalTmS,StS,memS,PdS,denoteS,
                 memS_svar,memS_sicc,memS_sinter,denoteS_pmem

One candidate, one verdict. **No FAILED rows and no NOT-RUN rows.**
`p9-parallel-tower-r1` PASSED with `gate_ok: true`, `elaborated: true`,
kernel-`replayed: true`, `declared_missing: []`, and the audited axiom set
`{Quot.sound, lcProof, propext}` — **no `sorryAx`**, so this is a real
elaboration and not a well-formed hole. `detail` is `null` by design; a pass
carries no transcript, which is exactly why the PASSED branch of the seed rule
drives the next round from the measurement rather than from a transcript tail.

The proof-goal half of the same batch reproduces unchanged: **24 goals, 10
closed, 0 statement-cert demand, 14 tactic (H3) refusals, 0 not-run**
(`bench_hammer consume` re-derived the readout byte-for-byte against the
committed batch; the working tree came back clean).

## What round 1 established, and what the measurement still names as unmet

`results/c3_cycle_16.md` prices this row's gap as exactly three things a
`setbuild` cannot do — a set can be **counted** but never **inhabited**,
**named**, or **compared**. Round 1 took the first two by declaration and left
the third by declaration:

| capability the measurement names | round | verdict |
|---|---|---|
| **NAMED** — a set object that survives unfolding (`StS.svar`), plus `StS.sicc` / `StS.sinter` as first-class objects rather than `card` arguments | r1 | **PASSED** |
| **INHABITED** — a computable membership atom over set objects (`memS`, `PdS.pmem`, `denoteS`), with one `rfl` tooth per arm | r1 | **PASSED** |
| **COMPARED** — set equality and subset over set objects | r2 | **open; it is the next round's single requirement** |

So the terminal branch of the PASSED rule does **not** fire here. Both other
open rows closed their queues on their own measurement's terms —
`refusal-symbolic-exponent` at r5, `refusal-function-symbol` at r2 — but this
row's measurement names a third capability that no candidate has yet
prototyped. The measurement is the work queue, not a one-shot seed: the
prototype elaborated, so it is EXTENDED toward the requirement still unmet,
one addition per round so a regression stays attributable.

## What this consumption does NOT do

* **It does not adopt anything.** `tools/FgReflect.lean` is untouched. A
  passed candidate is a PROPOSAL; the candidate queue has no write path to the
  slice, and adopting one is an attended purchase decision under the ordinary
  bill discipline. "It elaborated in the batch ride" is a reason to keep
  authoring and never a done-predicate.
* **It does not buy anything.** `refusal-set-carrier` stays OPEN and
  tower-class. No flywheel slot was spent: an authoring ride is not a
  purchase, which is why its PR is titled `C3 authoring` and stays invisible
  to the one-per-cycle in-flight guard.
* **It does not move the ceiling this row records against its own interest.**
  `results/purchase_frontier.json`, regenerated this session, still computes
  all four `set-membership` subjects as
  `held_by_a_signal_this_row_does_not_meet: 4` and
  `returns_to_ready: 0` — the row lands material only beside P6. A passing
  prototype changes what the fragment COULD say, not what the ledger measures.

## Bounds

No ceremony-reserved surface touched. P5 remains a trust root this session did
not promote. The CI lane verdict stays final. Ride marker written unbracketed
as lean-hammer everywhere except a ride commit message itself.

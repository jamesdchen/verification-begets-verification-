# Consuming round 2 for `refusal-set-carrier` — COMPARED PASSED, and the channel is now terminal

*(a purchase-driver firing that found the in-flight guard clear, YIELDED the
bill on a measured probe verdict, and spent itself closing the single-slot
authoring channel PR #164 was holding)*

## Why this commit exists

The authoring channel is SINGLE-SLOT — there is exactly one
`results/reflect_candidates.json` — so an open `C3 authoring ...` PR OWNS it
and no further round is possible until that PR lands. Consuming means CLOSING
THE SLOT, not reading a file.

PR #164's lane had FINISHED: the commit-back `376727d`
(`ci(lean-hammer): batched ride verdicts + readout [skip ci]`) is the branch
tip. `get_check_runs` on #164 read **`total_count: 0`** — zero check runs, and
that is exactly the expected shape of a `GITHUB_TOKEN` commit-back, which
fires no workflows. A tip with no checks is precisely what the self-merge
rule's missing-`trust-surface` refusal exists to stop, so the lane tip is
**never** merged as it stands. This commit is the consumption: it re-commits
the lane's verdicts under session credentials, which re-arms the checks, and
only then may the PR merge.

Deferring to a FINISHED ride is the 2026-07-26 wedge that ran this route
exactly once and then stalled for three firings, each reasoning correctly and
each stopping. This firing did not defer.

## The readout

`python3 run/reflect_ride.py --verdicts results/hammer_verdicts.json
--batch results/hammer_batch.json`, run this session:

    reflect_ride report: verdicts=complete lean_available=True
      candidates=1  passed=1  failed=0  not-run=0
      [PASSED] p9-parallel-tower-r2
        declares=PdS,denoteS,denoteS_psub,denoteS_pseteq,
                 boolS_ext,pseteq_iff_mutual_psub,psub_sinter_left

One candidate, one verdict. **No FAILED rows and no NOT-RUN rows.**
`p9-parallel-tower-r2` PASSED with `gate_ok: true`, `elaborated: true`,
kernel-`replayed: true`, `declared_missing: []`, and the audited axiom set
`{Quot.sound, lcProof, propext}` — **no `sorryAx`**, so set equality as mutual
containment is a real elaboration and not a well-formed hole. `detail` is
`null` by design; a pass carries no transcript.

## And this consumption is TERMINAL for the channel

The PASSED rule has two branches, and which one fires is decided by the row's
committed class measurement, not by appetite. `results/c3_cycle_16.md` prices
this row's gap as exactly three things P2's `setbuild` cannot do — a set can be
**counted** but never *inhabited*, *named*, or *compared* (line 93, verbatim):

| capability the measurement names | round | verdict |
|---|---|---|
| **NAMED** — `StS.svar`, the opaque set that survives unfolding; `StS.sicc` / `StS.sinter` as first-class objects | r1 | PASSED |
| **INHABITED** — `memS`, `PdS.pmem`, `denoteS`, one `rfl` tooth per arm | r1 | PASSED |
| **COMPARED** — `PdS.psub` / `PdS.pseteq`, `boolS_ext`, `pseteq_iff_mutual_psub`, `psub_sinter_left` | r2 | **PASSED** |

The measurement now names **nothing further unmet**, so the terminal branch
fires and **authoring on `refusal-set-carrier` stops**. That is the honest
stop the rule asks for, not an admission of having run out of ideas: the row
was closed on its own measurement's terms.

With it, **all three open rows have complete authoring queues** —
`refusal-symbolic-exponent` at r5, `refusal-function-symbol` at r2,
`refusal-set-carrier` at r2 — so this firing authored **no round 3**, and the
honest reading is that the unattended authoring channel has no further round
to take on any currently open row. Extending it further would require either a
NEW class measurement naming a construct no prototype has taken, or a new open
row; neither is an unattended session's to manufacture.

## What this consumption does NOT do

* **It does not adopt anything.** `tools/FgReflect.lean` is untouched. A
  passed candidate is a PROPOSAL; the candidate queue has no write path to the
  slice, and ADOPTING one is an attended purchase decision under the ordinary
  bill discipline. "It elaborated in the batch ride" is a reason to keep
  authoring and never a done-predicate; the CI lane verdict stays final.
* **It does not buy anything.** `refusal-set-carrier` stays OPEN and
  tower-class. No flywheel slot was spent: an authoring ride is not a
  purchase, which is why its PR is titled `C3 authoring` and stays invisible
  to the one-per-cycle in-flight guard.
* **It does not move the ceiling.** `results/purchase_frontier.json`,
  regenerated this session, still reads **13 rows, 3 open, 0 ready**. All four
  `set-membership` subjects remain `held_by_a_signal_this_row_does_not_meet`,
  `returns_to_ready: 0` — the row lands material only beside P6. A passing
  prototype changes what the fragment COULD say, not what the ledger measures.

## The purchase that was not made, this firing

`python3 tools/lean_env_probe.py`, **run** in this container, never read off
disk:

    lean-absent:not-installed

Not `lean-local`, so PLAN_FRAGMENT §3.1 rule 3's YIELD clause fires and this
unattended session did not take a tower-class bill. `purchase_frontier`
regenerated: 13 rows, 3 open, 0 ready, and not one open row is additive-class,
so the yield is TOTAL rather than partial — there is no strictly-first
Lean-free half to ship, because no open row has one.

## Bounds

No ceremony-reserved surface touched. P5 remains a trust root this session did
not promote. `kernel/certs.py` pins, `TRUST.md` and the escape-gate blocklist
are untouched. Ride marker written unbracketed as lean-hammer everywhere
except a ride commit message itself.

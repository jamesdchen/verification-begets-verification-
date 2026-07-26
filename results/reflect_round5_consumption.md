# Consuming round 5 for `refusal-symbolic-exponent` — and closing the row's authoring queue

*(a purchase-driver firing that found the in-flight guard clear, YIELDED the
bill on a measured probe verdict, and spent itself closing the single-slot
authoring channel instead)*

## Why this commit exists

The lane's commit-back (`dc4b080`) is pushed with `GITHUB_TOKEN`, fires no
workflows, and carries **zero check runs** — this session read
`get_check_runs` on PR #153 and got `total_count: 0`, which is exactly the
tip the self-merge rule's missing-`trust-surface` refusal exists to stop.
The consuming session re-commits the verdicts under its OWN credentials,
which re-arms the checks. This is that commit.

The channel is SINGLE-SLOT — one `results/reflect_candidates.json` — so an
open `C3 authoring ...` PR owns it and no further round is possible until it
lands. Consuming means CLOSING THE SLOT, not reading a file. Deferring to a
finished ride is what stalled this route for three firings on 2026-07-26
(each session reasoning correctly and each stopping); this firing did not
defer.

## The readout

`python3 run/reflect_ride.py --verdicts results/hammer_verdicts.json
--batch results/hammer_batch.json`:

    reflect_ride report: verdicts=complete lean_available=True
      candidates=1  passed=1  failed=0  not-run=0
      [PASSED] p7-parallel-tower-r5
        declares=PdP,denoteP,decDenoteP,checkP,checkP_sound,checkP_sound_powp

One candidate, one verdict, no NOT-RUN rows. `p7-parallel-tower-r5` PASSED:
`gate_ok`, `elaborated`, kernel-`replayed`, `declared_missing == []`, and the
axiom set is `{Quot.sound, lcProof, propext}` — **no `sorryAx`**. `detail` is
null by design; a pass carries no transcript.

So the predicate layer over the parallel tower elaborates: `PdP` with both
connectives, `denoteP`, `decDenoteP`, `checkP`, `checkP_sound`, and the tooth
`checkP_sound_powp` — a `true` from the checker on an equation whose left
side carries `powp`, discharged by `checkP_sound` alone. The third additive
criterion's phrase "decidability INHERITED from `decDenote`" is now a
machine-checked claim about `powp` rather than an untested one.

## THE ROW'S AUTHORING QUEUE IS COMPLETE — and this session stopped

The PASSED rule says to extend the prototype toward the next requirement the
row's class measurement still names as unmet, and to STOP when it names none.
Read this session, `tests/test_symbolic_exponent_class.py` names the tower at
two granularities and **both are now met**:

| requirement | named at | round | verdict |
|---|---|---|---|
| new `evalTm` case | docstring + executable assertion | r1 | PASSED |
| new `substTm` case | docstring + executable assertion | r1 | PASSED |
| new `evalTmN` case | docstring + executable assertion | r2 | PASSED |
| `substTm_evalTm` / `evalTm_subst` | docstring + executable assertion | r3 | PASSED |
| `evalTmN_subst` | executable assertion | r4 | PASSED |
| new `check`/`decDenote` case | docstring | **r5** | **PASSED** |

The executable assertion `test_the_reflect_slice_has_no_term_level_exponent`
enumerates five walkers (`evalTm`, `evalTmN`, `substTm`, `evalTm_subst`,
`evalTmN_subst`); the module docstring enumerates six, adding the
`check`/`decDenote` case. r4 read the narrower list and called itself last;
r5 was authored precisely because that was one reading short. Nothing in
either enumeration is now unmet.

Therefore **no round 6 was authored**, and inventing a seventh requirement to
keep the channel busy would be the dishonest move the rule forbids. The row
this reading is about is `refusal-symbolic-exponent`; the measurement read is
`tests/test_symbolic_exponent_class.py` (module docstring lines 99-101 and
`test_the_reflect_slice_has_no_term_level_exponent`, lines ~735-757). The
next firing starts from that reading rather than re-deriving it.

## What this does NOT buy

* `tools/FgReflect.lean` is **untouched**. A candidate is a PROPOSAL; the
  queue has no write path to the slice. Adopting `TmP`/`PdP` into the slice
  is an attended purchase decision under the ordinary bill discipline, and
  no unattended session may take it.
* "It elaborated in the batch ride" is a reason to keep authoring and never a
  done-predicate. The CI lane verdict stays final.
* The `refusal-symbolic-exponent` row is still OPEN and still
  `iteration-class`. Its twelve refused subjects are still refused. What
  changed is that the tower the class measurement priced now exists as a
  machine-checked prototype, in full, with its soundness story attached.

## The purchase that was not made (this firing)

`python3 tools/lean_env_probe.py`, **run** in this container, not read off
disk:

    lean-absent:not-installed

Same verdict the round-5 session measured, and the same kind-change from the
`policy-denied` reading before it: the enumerated hosts are reachable, the
toolchain simply is not installed here. `lean-absent:not-installed` is not
`lean-local`, so PLAN_FRAGMENT §3.1 rule 3's YIELD clause fires and this
unattended session did not take a tower-class bill. `results/lean_env.json`
is left as the round-5 session committed it — the two readings agree, so
there is no delta to record.

The queue is unchanged from what the round-5 receipt priced: 13 rows, 3 open,
**0 ready**, and not one open row additive-class
(`refusal-symbolic-exponent` iteration-class, `refusal-function-symbol`
definitional-extension, `refusal-set-carrier` tower-class). The yield is
total rather than partial — there is no strictly-first Lean-free half to
ship, because no open row has one.

## Bounds

Full suite green before this commit. No ceremony-reserved surface touched:
`kernel/certs.py`, `TRUST.md`, `buildloop/growth_protocol.py` and the escape
gate are untouched, and P5 remains a trust root this session did not promote.

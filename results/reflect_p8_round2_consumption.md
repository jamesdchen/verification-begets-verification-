# Consuming round 2 for `refusal-function-symbol` — and the row's authoring queue closes

*(a purchase-driver firing that found the in-flight guard clear, YIELDED the
bill on a measured probe verdict, and spent itself closing the single-slot
authoring channel)*

## Why this commit exists

The lane's commit-back (`232da62`, `ci(lean-hammer): batched ride verdicts +
readout [skip ci]`) is pushed with `GITHUB_TOKEN`, fires no workflows, and
carries **zero check runs** — this session read `get_check_runs` on PR #160
and got `total_count: 0`, which is exactly the tip the self-merge rule's
missing-`trust-surface` refusal exists to stop. The consuming session
re-commits the verdicts under its OWN credentials, which re-arms the checks.
This is that commit.

The channel is SINGLE-SLOT — one `results/reflect_candidates.json` — so an
open `C3 authoring ...` PR owns it and no further round is possible until it
lands. Consuming means CLOSING THE SLOT, not reading a file; deferring to a
finished ride is the 2026-07-26 wedge that ran this route exactly once and
then stalled for three firings. This firing did not defer.

## The readout

`python3 run/reflect_ride.py --verdicts results/hammer_verdicts.json
--batch results/hammer_batch.json`:

    reflect_ride report: verdicts=complete lean_available=True
      candidates=1  passed=1  failed=0  not-run=0
      [PASSED] p8-parallel-tower-r2
        declares=PdF,denoteF,decDenoteF,checkF,checkF_sound,checkF_sound_app

One candidate, one verdict, **no FAILED rows and no NOT-RUN rows**.
`p8-parallel-tower-r2` PASSED: `gate_ok`, `elaborated`, kernel-`replayed`,
`declared_missing == []`, and the audited axiom set is
`{Quot.sound, lcProof, propext}` — **no `sorryAx`**, so this is an
elaboration and not a well-formed hole. `detail` is null by design; a pass
carries no transcript.

The proof-goal half of the same batch reproduces unchanged: **24 goals, 10
closed, 0 statement-cert demand, 14 tactic (H3) refusals, 0 not-run** — the
count that the one-flag `assemble` form silently dropped to zero on the
firing before last, and the reason `C3_PROMPTS.md` now quotes `--queue`
beside `--candidates`.

## What round 2 established

`tests/test_function_symbol_class.py`'s finding (4) —
`test_a_function_symbol_forces_a_constructor_and_a_decidable_story` — prices
this rung at **exactly two** costs, and it says so in its own docstring: an
application node is new structure, *"worse for the bill, `decDenote` decides
every `Pd` BY COMPUTATION over `evalTm`, and an uninterpreted symbol
constrained only by axioms has no computable value — so the rung would owe a
new `Decidable` story as well, not merely a new case."*

| cost | round | verdict |
|---|---|---|
| (i) an APPLICATION NODE — every `Tm` argument position is a bare `Int`/`Nat`/`Tm`, so an applied symbol and the environment it is read from have nowhere to live | r1 | **PASSED** |
| (ii) a new `Decidable` STORY — `decDenote` decides by computation, and an axiom-only symbol has no computable value | r2 | **PASSED** |

r2 carried r1's text forward verbatim (the splice appends after the committed
slice, so nothing r1 declared exists unless re-declared) and added exactly one
requirement on top: `PdF` with both connectives, `denoteF`, the `decDenoteF`
instance arm for arm, `checkF`/`checkF_sound`, and the tooth
`checkF_sound_app` — a `true` from the checker on an equation whose LEFT SIDE
IS AN APPLICATION, discharged by `checkF_sound` alone. An instance that never
met the new constructor would elaborate just as happily; the tooth is
decidability reaching **through** `TmF.app` rather than around it.

## So this row's authoring queue is COMPLETE, and that is a stopping rule

The measurement names two costs. Both are now machine-checked constructions
rather than argued ones, and **the measurement names nothing further unmet** —
so the PASSED rule's terminal branch fires: stop authoring this row and say
so. `refusal-symbolic-exponent` closed the same way at r5
(`results/reflect_round5_consumption.md`); this is the second row to close,
and the two closed for the same reason rather than by running out of ideas.

What that does NOT mean, stated because the distinction is the whole honesty
of the channel:

* **The row is not bought.** It stays OPEN in
  `results/purchase_frontier.json`, `definitional-extension`, capped at its
  measured **five** returnable subjects.
* **The prototype is not adopted.** `tools/FgReflect.lean` is untouched; a
  candidate is a PROPOSAL and the queue has no write path to the slice.
  ADOPTING a passed prototype is an attended purchase decision under the
  ordinary bill discipline — never an unattended session's act.
* **The measurement is not refuted.** r2 settles that an application node does
  not *by itself* destroy the computational `Decidable` story **provided the
  symbol is INTERPRETED** by a computable `fenv`. The *"no computable value"*
  claim is about the **axiom-only** route, which is the shape the row's real
  subjects present (the recurrences `a_n`/`d_n`/`F_n` at a *symbolic* index,
  where there is no computable `fenv` to supply). What the two rounds
  delimit is the **cost**, not the verdict.

## Bounds

No ceremony-reserved surface touched. P5 remains a trust root this session did
not promote. Full suite before this commit: **1767 passed, 41 skipped**.
Ride marker written unbracketed as lean-hammer throughout, per marker
discipline — the bracketed form appears only in a commit message that IS a
ride, and this commit is a consumption.

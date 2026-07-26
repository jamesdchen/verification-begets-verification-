# Consuming round 1 for `refusal-function-symbol` — the application node elaborates

*(a purchase-driver firing that found the in-flight guard clear, YIELDED the
bill on a measured probe verdict, and spent itself closing the single-slot
authoring channel)*

## Why this commit exists

The lane's commit-back (`d9ad2c8`, `ci(lean-hammer): batched ride verdicts +
readout [skip ci]`) is pushed with `GITHUB_TOKEN`, fires no workflows, and
carries **zero check runs** — this session read `get_check_runs` on PR #157
and got `total_count: 0`, which is exactly the tip the self-merge rule's
missing-`trust-surface` refusal exists to stop. The consuming session
re-commits the verdicts under its OWN credentials, which re-arms the checks.
This is that commit.

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
      [PASSED] p8-parallel-tower-r1
        declares=TmF,evalTmF,substTmF,evalTmF_app,substTmF_app

One candidate, one verdict, **no FAILED rows and no NOT-RUN rows**.
`p8-parallel-tower-r1` PASSED: `gate_ok`, `elaborated`, kernel-`replayed`,
`declared_missing == []`, and the audited axiom set is
`{Quot.sound, lcProof, propext}` — **no `sorryAx`**, so this is an
elaboration and not a well-formed hole. `detail` is null by design; a pass
carries no transcript.

## What round 1 established

`tests/test_function_symbol_class.py` finding (4) names two costs and asserts
both against the artifact. Cost (i) — the APPLICATION NODE — is the one this
round took, and it is now a machine-checked construction rather than an
argued one:

| declaration | what it answers |
|---|---|
| `TmF` | parallel term tower whose `app : Nat -> TmF -> TmF` names a symbol by index and applies it |
| `evalTmF` | threads the SECOND environment `fenv : Nat -> Int -> Int` the assertion says `Tm` has nowhere to put |
| `substTmF` | the substitution walker's new case |
| `evalTmF_app` / `substTmF_app` | one `rfl` tooth per arm, so a silent arm cannot pass unnoticed |

The assertion `test_a_function_symbol_forces_a_constructor_and_a_decidable_story`
walks every argument position of every `Tm` constructor and demands each token
be a bare `Int`/`Nat`/`Tm`, *"so there is nowhere in the type for an applied
symbol — or for the environment one would have to be read from — to live."*
Both halves of that gap — the applied position and the environment it is read
from — now exist in a prototype that elaborates.

## THE ROW'S QUEUE IS NOT COMPLETE — cost (ii) is still unmet

The PASSED rule says to extend the prototype toward the next requirement the
row's class measurement still names as unmet, and to STOP only when it names
none. Read this session, `tests/test_function_symbol_class.py` still names
one:

| cost | named at | round | verdict |
|---|---|---|---|
| application node (new constructor) | finding (4); `test_a_function_symbol_forces_a_constructor_and_a_decidable_story` | **r1** | **PASSED** |
| a new `Decidable` story | finding (4), *"`decDenote` decides every `Pd` BY COMPUTATION over `evalTm`, and an uninterpreted symbol constrained only by axioms has no computable value — so the rung would owe a new `Decidable` story as well, not merely a new case"* | r2 | **unmet** |

So this row does **not** stop where `refusal-symbolic-exponent` stopped at r5.
Round 2 is authored in the same PR that carries this consumption, taking
cost (ii) and only cost (ii), per the one-requirement-per-round rule that
keeps a regression attributable.

## What this does NOT buy

* `tools/FgReflect.lean` is **untouched**. A candidate is a PROPOSAL; the
  queue has no write path to the slice. Adopting `TmF` into the slice is an
  attended purchase decision under the ordinary bill discipline, and no
  unattended session may take it.
* "It elaborated in the batch ride" is a reason to keep authoring and never a
  done-predicate. The CI lane verdict stays final.
* The `refusal-function-symbol` row is still OPEN, still
  `definitional-extension`, and its measured **five-subject** ceiling (finding
  (1): six of the eleven blocking refusals are held independently by
  `symbolic-exponent`) is untouched. Its eleven refused subjects are still
  refused.

## The purchase that was not made (this firing)

`python3 tools/lean_env_probe.py`, **run** in this container, not read off
disk:

    lean-absent:not-installed

Not `lean-local`, so PLAN_FRAGMENT §3.1 rule 3's YIELD clause fires and this
unattended session did not take a tower-class bill. `results/lean_env.json`
is left as the round-1 session committed it — the two readings agree, so
there is no delta to record.

`python3 tools/purchase_frontier.py` regenerated this session: **13 rows, 3
open, 0 ready**, and not one open row is additive-class
(`refusal-symbolic-exponent` iteration-class, `refusal-function-symbol`
definitional-extension, `refusal-set-carrier` tower-class). The yield is
TOTAL rather than partial — there is no strictly-first Lean-free half to
ship, because no open row has one.

## Bounds

Full suite green before this commit. No ceremony-reserved surface touched:
`kernel/certs.py`, `TRUST.md`, `buildloop/growth_protocol.py` and the escape
gate are untouched, and P5 remains a trust root this session did not promote.

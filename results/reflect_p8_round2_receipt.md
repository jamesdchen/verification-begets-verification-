# Round 2 for `refusal-function-symbol` — the Decidable story, and exactly what it delimits

*(the same purchase-driver firing that consumed round 1 and merged PR #157;
consuming freed the single slot, so this round could be authored into it)*

## The purchase that was not made

`python3 tools/lean_env_probe.py`, **run** in this container, never read off
disk:

    lean-absent:not-installed

Not `lean-local`, so PLAN_FRAGMENT §3.1 rule 3's YIELD clause fires and this
unattended session did not take a tower-class bill.

`python3 tools/purchase_frontier.py`, regenerated this session: **13 rows, 3
open, 0 ready**. Not one open row is additive-class —
`refusal-symbolic-exponent` iteration-class, `refusal-function-symbol`
definitional-extension, `refusal-set-carrier` tower-class — so the yield is
TOTAL rather than partial: there is no strictly-first Lean-free half to ship,
because no open row has one. Yielding the purchase is not yielding the
session, so the session took the authoring ride.

## Why there was a slot to author into

`results/reflect_candidates.json` is a single file, so an open
`C3 authoring ...` PR owns the channel. PR #157 was open and its lane had
FINISHED (commit-back tip `d9ad2c8`, zero check runs). This firing consumed
it rather than deferring to it — receipt
`results/reflect_p8_round1_consumption.md`, merged as PR #157 — and only then
authored below.

## What round 1 established, and what it left

`tests/test_function_symbol_class.py` finding (4) prices the rung at **two**
costs and asserts both against the artifact:

| cost | round | status |
|---|---|---|
| (i) an APPLICATION NODE — `Tm`'s six constructors take bare `Int`/`Nat`/`Tm` in every argument position, *"so there is nowhere in the type for an applied symbol — or for the environment one would have to be read from — to live"* | r1 | **PASSED** |
| (ii) a new DECIDABLE STORY — *"`decDenote` decides every `Pd` BY COMPUTATION over `evalTm`, and an uninterpreted symbol constrained only by axioms has no computable value — so the rung would owe a new `Decidable` story as well, not merely a new case"* | **r2** | authored here |

A PASS carries a null `detail` by design, so there was no transcript to drive
from. The PASSED rule says to extend the prototype toward the next
requirement the measurement still names unmet, and this row named exactly
one.

## What r2 adds — one requirement, so a regression is attributable

r1's text is carried forward **verbatim** (the splice appends after the
committed slice, so nothing r1 declared exists unless re-declared), and
exactly one thing is added on top:

| new | what it answers |
|---|---|
| `PdF` | predicate layer over `TmF`, both connectives (`pand`, `pimp`) |
| `denoteF` | its `Prop` semantics through `evalTmF` |
| `decDenoteF` | the `Decidable` instance, by computation, arm for arm |
| `checkF` / `checkF_sound` | the Boolean checker and its soundness |
| `checkF_sound_app` | **the tooth** — a `true` from the checker on an equation whose LEFT SIDE IS AN APPLICATION, discharged by `checkF_sound` alone |

`checkF_sound_app` is the point of the round. An instance that never meets
the new constructor would elaborate just as happily; the tooth is
decidability reaching **through** `TmF.app` rather than around it.

## WHAT THIS SETTLES — and what it emphatically does not

It settles that an application node does not **by itself** destroy the
computational `Decidable` story, **provided the symbol is INTERPRETED** by a
computable `fenv : Nat -> Int -> Int`, which is the route this tower takes.

It does **not** refute the measurement, and must not be read as doing so.
The measurement's *"no computable value"* claim is about the **axiom-only**
route — a symbol constrained by hypotheses alone — and that is the shape the
row's actual subjects present: the recurrences `a_n`/`d_n`/`F_n` at a
**symbolic** index, where there is no computable `fenv` to supply. So what
r2 delimits is the **cost**, not the verdict: the Decidable story is owed,
here is what one looks like on the interpreted route, and the axiom-only
route still has none. That is precisely why `refusal-function-symbol` stays
`definitional-extension` and attended-only under §3.1 rule 3.

Nothing here revises the row's class verdict, its OPEN status, or its
measured **five-subject** ceiling (finding (1): six of the eleven blocking
refusals are held independently by `symbolic-exponent`, and a
function-symbol mechanism bought alone returns none of those six).

## A prompt defect this ride measured and fixed

The PURCHASE DRIVER prompt quoted the ride's assemble step as

    python3 bench/bench_hammer.py assemble --candidates results/reflect_candidates.json

`--queue` defaults to ABSENT, so that one-flag form assembles the honest
empty-bootstrap batch: this firing ran it verbatim and got
`0 goals (queued=0, unresolved=0)` where the committed batch carries **24**,
which reds three committed reproduction teeth
(`test_committed_batch_reproduces_byte_for_byte`,
`test_committed_batch_still_reproduces_byte_for_byte`,
`test_committed_readout_reproduces_from_committed_inputs`) that byte-compare
the artifact against a fresh derivation from BOTH inputs. The readout is
derived from the batch in the same way, so a new batch also leaves the
committed readout stale.

`C3_PROMPTS.md` now quotes both flags and the `consume` regen step, with the
measurement beside them. It is not a ceremony-reserved surface, and the
Architecture section's own rule is that prompt fixes ship by git merge alone.
The four teeth in `tests/test_authoring_route.py` that read this command
(`test_named_command_exists`, `test_bench_assemble_accepts_the_candidates_flag`,
`test_the_paths_the_prompt_quotes_are_the_paths_that_exist`,
`test_prompts_carry_the_marker_exactly_once`) stay green across the edit.

`results/supply_status.json` moves with it: that artifact pins
`C3_PROMPTS.md`'s SHA-256 in its `derived_from`, so the prompt edit — and
only the prompt edit, not the candidate change — restaled it. Regenerated
with `python3 tools/supply_status.py`; the **verdict text is unchanged**
(`supply-blocked: tower-class-only (3 open rows ...)`), so this is a re-pin
and not a supply reading that moved.

## Bounds

* `tools/FgReflect.lean` is **untouched**. A candidate is a PROPOSAL; the
  queue has no write path to the slice. Adopting `TmF`/`PdF` is an attended
  purchase decision under the ordinary bill discipline.
* "It elaborated in the batch ride" is a reason to keep authoring and never a
  done-predicate. The CI lane verdict stays final.
* Still a PARALLEL tower — the splice constraint means `Tm` and `Pd` cannot
  be extended from an append.
* No ceremony-reserved surface touched: `kernel/certs.py`, `TRUST.md`,
  `buildloop/growth_protocol.py` and the escape gate are untouched, and P5
  remains a trust root this session did not promote.

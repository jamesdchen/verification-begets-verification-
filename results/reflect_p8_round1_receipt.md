# Round 1 for `refusal-function-symbol` — the application node, and the slot moving rows

*(a purchase-driver firing that found the in-flight guard clear, YIELDED the
bill on a measured probe verdict, and spent itself opening a NEW row's
authoring queue rather than reporting an empty one)*

## The purchase that was not made (this firing)

`python3 tools/lean_env_probe.py`, **run** in this container, never read off
disk:

    lean-absent:not-installed

Same verdict the round-5 consumption session measured. `lean-absent:not-installed`
is not `lean-local`, so PLAN_FRAGMENT §3.1 rule 3's YIELD clause fires and this
unattended session did not take a tower-class bill.

`python3 tools/purchase_frontier.py` derives 13 rows (7 purchased, 1 trust-root,
2 parked, **3 open**), **0 ready**, 46 refused subjects over 68 group
memberships. Not one open row is additive-class:

| row | bill class | blocking refusals |
|---|---|---|
| `refusal-symbolic-exponent` | iteration-class | symbolic-exponent × 12 |
| `refusal-function-symbol` | definitional-extension | function-symbol × 11 |
| `refusal-set-carrier` | tower-class | set-membership × 4 |

The yield is **total** rather than partial: there is no strictly-first
Lean-free half to ship, because no open row has one. That is unchanged from the
round-5 reading and is recorded here as a re-measurement, not as news.

## Consume first: the slot was already free

`C3 authoring ...` open-PR query: **none**. The previous occupant landed as
PR #153 (`df0f06f`), whose consumption commit re-armed the checks under session
credentials and merged. `results/hammer_verdicts.json` carries exactly one
authoring row and it is already consumed:

    reflect_ride report: verdicts=complete lean_available=True
      candidates=1  passed=1  failed=0  not-run=0
      [PASSED] p7-parallel-tower-r5
        declares=PdP,denoteP,decDenoteP,checkP,checkP_sound,checkP_sound_powp

No NOT-RUN rows, no FAILED rows, nothing left to close. So this firing did not
consume; it authored.

## WHY THE SLOT MOVED ROWS — and why that is not a widening

`results/reflect_round5_consumption.md` recorded `refusal-symbolic-exponent`'s
authoring queue as **complete**: `tests/test_symbolic_exponent_class.py` names
the tower at two granularities (an executable assertion enumerating five
walkers, a module docstring enumerating six), and r1..r5 met every entry of
both. The PASSED rule says to STOP authoring when the measurement names nothing
further unmet, and inventing a seventh requirement to keep the channel busy is
the dishonest move that rule forbids.

Stopping on that row is not stopping on the channel. The next open row whose
committed class measurement DOES name an unmet construct is
`refusal-function-symbol`, and the seed rule names its measurement by file:
`tests/test_function_symbol_class.py`. Quoting a committed measurement is
DERIVATION; the guess the rule forbids is inventing a construct no measurement
names.

## The seed, read out of the measurement rather than recalled

`tests/test_function_symbol_class.py` finding (4) and its executable assertion
`test_a_function_symbol_forces_a_constructor_and_a_decidable_story`
(lines ~653-681) name **two** costs, and assert both against the artifact
rather than arguing them:

1. **An application node.** The test reads `tools/FgReflect.lean`'s
   `inductive Tm`, pins the constructor list to exactly
   `(lit, tvar, add, sub, mul, tmod)`, then walks every argument position of
   every constructor and asserts each token is a bare `Int`, `Nat` or `Tm` —
   *"so there is nowhere in the type for an applied symbol — or for the
   environment one would have to be read from — to live."* It is a
   constructor-shape check, not a name check.
2. **A new `Decidable` story.** `decDenote` decides every `Pd` BY COMPUTATION
   over `evalTm`, and an uninterpreted symbol constrained only by axioms has no
   computable value.

**This round takes (1) only, and takes it small** — the smallest parallel tower
whose failure transcript would be legible, because the transcript is the next
round's seed:

| declaration | what it answers |
|---|---|
| `TmF` | the parallel term tower; its fifth constructor `app : Nat -> TmF -> TmF` names a function symbol by index and applies it to a term |
| `evalTmF` | the evaluator, threading the SECOND environment `fenv : Nat -> Int -> Int` the assertion says `Tm` has nowhere to put |
| `substTmF` | the substitution walker's new case |
| `evalTmF_app` | `rfl` tooth on the eval arm |
| `substTmF_app` | `rfl` tooth on the subst arm |

The two walkers are the minimum a new constructor owes on the sibling row's
own accounting (an `evalTm` case and a `substTm` case, which were r1 there
too), plus one `rfl` tooth apiece so a silent arm cannot pass unnoticed.

## What this round deliberately does NOT claim

Stated here so a later round cannot be read as having been promised, and so the
row's own class verdict is not quietly revised by a prototype:

* Routing the symbol through an **interpreting** environment (`fenv`) is the
  route on which decidability could be inherited. The measurement's *"no
  computable value"* claim is about the **axiom-only** route — a symbol
  constrained by hypotheses alone — which is the shape the row's actual
  subjects present (the recurrences `a_n`/`d_n`/`F_n` at a *symbolic* index).
  Whether the interpreted route reaches those subjects is a question for later
  rounds and for the measurement; nothing this round elaborates settles it.
* The row stays **`definitional-extension`** and stays **open**. Its measured
  five-subject ceiling (finding (1): six of the eleven are independently held
  by `symbolic-exponent`) is untouched, as is finding (2)'s reading that two of
  its three named exemplars are already in the fragment.

## Bounds

* Still a **PARALLEL** tower. The splice constraint is structural: a candidate
  is text appended after the committed slice re-entering `namespace FgReflect`,
  so `Tm` cannot be extended from an append and an application constructor must
  live in a new inductive.
* Still a **PROPOSAL**. `tools/FgReflect.lean` is untouched and the candidate
  queue has no write path to it. "It elaborated in the batch ride" is a reason
  to keep authoring and never a done-predicate; the CI lane verdict stays final.
* Full suite green before the ride commit. No ceremony-reserved surface
  touched: `kernel/certs.py`, `TRUST.md`, `buildloop/growth_protocol.py` and
  the escape-gate blocklist are untouched, and P5 remains a trust root this
  session did not promote.

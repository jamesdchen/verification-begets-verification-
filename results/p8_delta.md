# P8 delta — named function symbols (a definitional extension)

*(P8 purchase receipt.)*

**Row**: `refusal-function-symbol` (PLAN_FRAGMENT §4 P8), refusal-priced,
11 subject-rows in `results/frontier_refusals.jsonl`.
**Class**: DECLARED `definitional-extension` (attended-only under §3.1
rule 3); **MEASURED `additive-desugaring`** — the P6 shape, and the class
this row actually landed in.
**Attendance**: taken by an unattended Routine firing under a MEASURED
`lean-local` probe verdict. The class finding below means the probe's
permission was not what this bill needed — see "Two readings a reviewer
should not conflate".

## What was bought

A `definition` statement — the source NAMES a function and gives it an
EXPLICIT body over its own parameters — plus the term `{"app": f, "args":
[...]}` that applies it.

```json
{"kind":"definition","name":"f","params":["k"],"body":<term over k>}
```

Before this, the only thing the fragment could do with a named function was
DECLARE ITS VALUES as objects at literal indices and constrain them by
hypotheses. `tests/test_function_symbol_class.py` measured that shape
precisely: it works at `b_5` and cannot reach `for all n, b_n`, because
dropping the index leaves the object unconstrained and the reading then
asserts something *weaker* than the source (test (8): nine counterexamples to
a statement the source makes). **What P8 buys is application at a SYMBOLIC
argument** — the thing no amount of literal-index unfolding reaches.

## The finding: both billed costs were priced against the wrong object

The row's own class measurement, finding (4), priced this rung at exactly two
costs — an APPLICATION NODE in `tools/FgReflect.lean`'s `Tm`, and a new
`Decidable` story, because "an uninterpreted symbol constrained only by
axioms has no computable interpretation".

**That is correct about an uninterpreted symbol, and it is why this row did
not buy one.** A symbol with an explicit, non-recursive body is *eliminable*:
every application rewrites, by capture-free substitution, to a term the
fragment already had. So the reading is desugared once, at the gate
(`generators.math_reading._unfold_term`), and:

| consumer | change |
|---|---|
| `generators/math_eval.py` | **none** |
| `generators/math_smt.py` | **none** |
| `generators/math_compile.py` | **none** |
| `tools/FgReflect.lean` | **none** — `Tm`/`Pd` byte-unchanged |

`decDenote` keeps deciding every `Pd` by computation, and §3.1 rule 3(a) is
not reached at all. This is P6's shape exactly — and P6 is the precedent the
class measurement's own preamble names for refusing to settle a declaration
by preference. The measurement's test
`test_a_function_symbol_forces_a_constructor_and_a_decidable_story` **still
passes unchanged**, because every word of it remains true of the slice.

Conservativity is not argued in prose either. It is the substitution, and
`tests/test_funcdef_battery.py` measures it: every reading that uses a
definition is compared against a HAND-UNFOLDED twin written longhand in the
pre-P8 fragment —

* **eval**: same verdict at every point of a box sweep;
* **SMT**: byte-identical rendering, and both z3 *and* cvc5 return `unsat` on
  the negated biconditional — equivalence for *all* n, not just on the box;
* **Lean**: byte-identical `lean_text` *and* `statement_hash`.

The reference is never a Python re-implementation of substitution. That is
what makes agreement evidence rather than a tautology.

## What was NOT bought, and it is the headline

**The recurrences.** `a_{k+1} = a_k + 2a_{k-1}` has no finite unfolding at a
symbolic index; discharging one needs well-founded recursion and a
termination argument, which is a different and much larger purchase. It is
refused BY NAME as first-class demand:

| refusal | what it holds | why it is a fence and not a gap |
|---|---|---|
| `funcdef:recursive-body` | a body applying itself, or a function defined later | no finite unfolding at a symbolic index; keeps the dependency graph a DAG |
| `funcdef:binder-body` | a bigop/set binder inside a body | makes use-site substitution capture-free BY CONSTRUCTION, not by a delicate argument |
| `funcdef:open-body` | a body mentioning a declared object | a body reading an ambient object is a hypothesis about one, with a different conservativity story |

So `definitional-extension` was **two rungs wearing one name**. The
non-recursive one is bought; the recursive one is what the new refusal
prices. Each freeze is pinned in BOTH directions in the battery.

## The refill, stated before anyone can be disappointed by it

`tests/test_function_symbol_class.py` had already measured this row's
ceiling at **five** subjects, not eleven (six of the eleven carry an
independent `symbolic-exponent` refusal). This bill buys the non-recursive
half, and of the eleven subjects: nine are `literal-index` recurrences, one
(`edge-disjoint`) needs a magma carrier filed here by accident of vocabulary,
and one is already expressible. **So this purchase is honestly expected to
return few or zero subjects immediately.**

§4 says so in advance — a refusal-priced purchase "may still measure zero,
because a subject blocked by two signals returns only when both are met" —
and the number of record is the NEXT corpus cycle's
`intake_from_frontier --unblocked refused:function-symbol`, not this receipt.
What this purchase bought is the RUNG.

## Re-census delta: ZERO, and structurally so

`results/census_portfolio.json` is **byte-identical**. This is the P4 shape
and it is predicted rather than excused: the portfolio census is LEXICAL, and
a definitional-extension *mechanism* adds no fragment word and no census
pattern row. Recorded as the no-delta reading it is, never widened until it
moves.

**Measured twice, against two different trees, because the tree moved under
this cycle.** C3 cycle 22 (#184) merged mid-session and took the portfolio
from 6 corpora / 1008 nodes to **7 / 1952**. The delta was re-measured after
merging `main` rather than carried over: byte-identical at 6 / 1008
(108 / 169 / 731) *and* byte-identical at **7 / 1952**
(135 attempt-candidate / 296 no-signal / 1521 out-of-fragment). The second
reading is the one of record, because it is the tree this purchase lands on.

The merge also changed what the window looks like, and the two facts must not
be conflated: `ready_now` is **27** (cycle 22's intake, not P8's), while
`total_returns_to_ready` stays **0** and `awaiting_unblock_run` stays **23**.
The 27 are cycle 23's to consume; the 23 are still awaiting an `--unblocked`
run.

## And it exposed an instrument defect — 23 subjects of paid-for supply

Landing this row turned `results/purchase_frontier.json`'s refill projection
to **`total_returns_to_ready: 0`** with the window still empty, and
`tests/test_purchase_frontier.py::test_when_ready_is_zero_the_artifact_says_what_would_refill_it`
fired — correctly. The projection totalled over **OPEN rows only**, so at the
moment a refusal-priced purchase LANDS, its subjects vanish from the
projection while still sitting demoted in the append-only ledger. The route
back is the next corpus cycle's `intake_from_frontier --unblocked`
(§3.2 path (d)), never the purchase itself, and between those two events the
artifact reported *"0 ready, and nothing would refill it"* over supply that
was fully paid for. Not merely silent — **wrong**.

Closed by a second reading, `awaiting_unblock_run` / `awaiting_unblock_subjects`:
subjects every one of whose blocking signals is met by a LANDED purchase.
It measures **23 subjects**, and two honesty notes travel with that number.
**They are not P8's** — they are the accumulated backlog of P6, P7 *and* P8,
sitting uncollected because no corpus cycle has run `--unblocked` since; P8
is only the firing that made the defect visible, by being the purchase that
emptied the open-row column. And **23 is an UPPER BOUND**, on exactly the
same terms as every other number in this projection: a returning subject
still has to clear the ready computation's other demotions (already intaken,
independently parked), which the projection does not model. The count is
reported separately from `total_returns_to_ready` rather than folded into it,
because folding it in would promise a refill no *purchase* delivers.

The tooth now fails only when BOTH numbers are zero — the true silent stall.
That is a nearer reading, not a weaker one: this supply needs no purchase at
all, only a corpus cycle. **It is the largest actionable thing on the board
and it belongs to the CORPUS loop, not this one.**

## Two readings a reviewer should not conflate

1. The probe read `lean-local` in this container, corroborated by direct
   measurement rather than trusted: the committed `tools/FgReflect.lean`
   (1405 lines) **elaborates locally, `ok=True`, in 72.9s**. PR #181 argues
   these containers cannot elaborate a Mathlib-importing file; **that reading
   did not reproduce here**, on `main` at `130f08b`, matching what
   `results/p7_delta.md` found. Recorded as a disagreement between two
   measurements rather than silently resolved in this purchase's favour.
2. **That permission was not what this bill needed.** `lean-local` licenses
   an unattended session to take tower-class work; the measurement then said
   this row is not tower-class. The two facts are independent, and the second
   would hold in a Lean-absent container too. A reader should not take this
   receipt as evidence that `lean-local` bought anything here.

## Bounds held

* No new carrier, no new node class, no new operator word, no new trust root.
* `Tm`/`Pd` byte-unchanged; no new `Decidable` instance; no import-pin change.
* P5 not promoted and not touched. `kernel/certs.py` pins, `TRUST.md` and the
  escape-gate blocklist untouched.
* The only ceremony-reserved path in this diff is
  `buildloop/growth_protocol.py`, whose diff is confined to the `GROWERS` and
  `SIGNATURE_PINS` assignment spans: one row added
  (`funcdef-definitional-extension`), two pins added, and three existing pins
  updated because P8 widened `_check_bigop`/`_check_setbuild`/`_check_card`
  by one OPTIONAL parameter (default `None`, so every existing call site is
  byte-identical).
* The prompt byte-pin `tests/golden/math_prompt_operator_seam.json` moved.
  The grammar block is GENERATED from `MATH_LF_KINDS`, so this drift is
  intended; regenerated with a line-by-line diff check, verified a PURE
  ADDITION (nothing removed), and the added lines are exactly the new
  `definition` clause and the `app` term form.
* No Lean-touching edit, so no lane tag.

## Per-commit gate

`CGB_LEAN=0 python3 -m pytest tests/ -q`, per `CLAUDE.md`: local Lean is for
authoring iteration, never the per-commit gate.

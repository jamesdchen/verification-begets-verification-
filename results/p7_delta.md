# P7 delta — the symbolic exponent (`^` at a non-literal power)

**Row**: `refusal-symbolic-exponent` (PLAN_FRAGMENT §4 P7), refusal-priced,
12 subject-rows in `results/frontier_refusals.jsonl`.
**Class**: iteration-class / tower-class — it grows the reflect slice's TERM
TYPE, which is §3.1 rule 3(a) verbatim.
**Attendance**: taken by an unattended Routine firing under a MEASURED
`lean-local` probe verdict. See "Why an unattended session took a tower-class
bill" below; that is the part of this receipt a reviewer should read first.

## What was bought

`Tm.pow : Tm -> Tm -> Tm` in the reflect slice, plus the admission rule that
makes it sound, plus the four consumers' answers to a non-literal exponent.
The row's own class measurement (`tests/test_symbolic_exponent_class.py`) had
already priced this exactly, and every item it billed is present:

| billed by the class measurement | paid |
|---|---|
| `Tm.pow : Tm -> Tm -> Tm` | `tools/FgReflect.lean` inductive block |
| new `evalTm` case | `(evalTm env a) ^ (evalTm env b).toNat` |
| new `evalTmN` case | `(evalTmN env a) ^ (evalTmN env b)` |
| new `substTm` case | structural, both arguments |
| new `evalTm_subst` case | substitution lemma stays UNCONDITIONAL |
| new `evalTmN_subst` case | same, at Nat |
| (not billed, still owed) `emitTm` | `(a ^ (b).toNat)` — the quoter |

Six walker sites, which is what the elaborator itself enumerated when the
constructor was added — the error list was exactly the class measurement's
list, which is the strongest evidence that the pre-purchase reading was right.

## The admission rule, and why it is carrier-Nat

A symbolic exponent is admitted **only at carrier `Nat`**
(`generators/math_reading._check_pow_exponent`). This is not conservatism, it
is the condition that makes every downstream layer type-correct at once:

* **Lean refuses the alternative outright.** `Monoid.npow` is `HPow _ Nat _`.
  Asking Lean to elaborate an Int-exponent power gives, measured in this
  container:

  ```
  error: failed to synthesize
    HPow ℤ ℤ ?m.15
  ```

  `zpow` would want a `DivisionRing` the integer carriers do not have. So an
  Int exponent has no Lean rendering at all — the gate is refusing something
  the emitter could not have emitted.
* **The evaluator stays inside the carrier.** `base ** e` at `e >= 0` is an
  integer; at `e < 0` Python produces a `Fraction`/float and leaves the
  carrier entirely. Non-negativity by TYPE means no consumer has to
  re-establish it.
* **It makes the reflect slice's totalisation unreachable.** `evalTm` computes
  `(evalTm env b).toNat`, which totalises a negative exponent to `x ^ 0 = 1`.
  That branch is *both* mirrored in Python (`base ** max(e, 0)`) *and*
  unreachable from any admitted reading. Mirrored-and-unreachable rather than
  either alone: the fence could widen later, and two evaluators that disagree
  the moment it does would be the fail-OPEN hazard `results/p3_delta.md`
  measured in this very tower.

The rule **fails CLOSED** (§3.1 rule 3(e)): refusal is the default and `Nat`
is the single admitted case, so a carrier nobody has written yet refuses
instead of falling through to a power whose meaning someone would then guess.

## The SMT bill item, paid as a REFUSAL — and why that is payment

**Every previous purchase could be corroborated by a dual-solver differential.
This one cannot, and that is recorded rather than worked around.** SMT-LIB has
no exponentiation, and the k-fold product unroll the fragment has used since
D10 needs a k. There is no honest rendering of `a ^ n`.

So `generators/math_smt.smt_representable` now routes such a reading to the
**enumeration channel** — and it is the first enum-only route keyed to a node
**shape** rather than to an operator **word**. `_ENUM_ONLY` (gcd, coprime) can
decide on the head alone because those have no rendering at any argument; `^`
renders perfectly well at a literal, so the predicate had to start looking at
the node. A rule that collapsed back to the head would have taken every
literal-exponent reading off the solver, which is why both directions are
toothed.

Enumeration is exhaustive over the box, which is a *stronger* claim about that
box than a solver's `sat`. **The b2-analogue symbolic battery is absent**, and
that is a real reduction in corroboration for this row alone.

## THE LIMIT — what P7 did NOT buy

**P7 buys the term constructor and the enumeration route. It does not buy the
discharge.** Enumeration over a box is not a proof of `for all n`. The class
measurement showed why the box cannot be escaped: `denoteStmt_of_box` /
`denoteStmtN_of_box` lift a box-relativized statement only under
`exOnly s = true` and meet a universal with `nomatch hex`, and **all twelve
ledger subjects are universal in their exponent.** The missing ingredient is
an **induction principle the slice still does not have**.

This is the headline, not a footnote, and it is toothed:
`test_the_unbounded_universal_is_still_not_discharged` reds if an induction
principle lands, so the limit is learned from a test rather than from a
paragraph a session might skim.

Residual demand, first-class: **`pow:symbolic-exponent@Int`**. The old guess
`pow:symbolic-exponent` meant "the fragment cannot express this at all", which
stopped being true; the carrier-suffixed name is the demand that is still real
(same idiom P3 used for `operator:/@{carrier}`). A row that kept its old price
after being partly paid would over-price the next purchase.

## The re-census delta: honestly ZERO, and the refill is a NEXT-cycle number

The §2 re-census delta on the portfolio is **zero**, recorded as zero. The
census is lexical; it prices vocabulary, and P7 grew a node shape.

The refill this buys is a **refusal retirement**, realized by a later corpus
cycle through `intake_from_frontier --unblocked refused:symbolic-exponent`.
The derived queue's projection, re-measured here from the ledger:

* 12 distinct subjects carry `symbolic-exponent`;
* **5** carry it as their ONLY blocker (these are the ones that could return);
* **7** are also held by a signal this row does not meet, so they stay held.

**That 5 is a projection and not a claim, and P7's rule makes it narrower than
the frontier's number suggests.** The admission rule is carrier-**Nat**; of the
twelve subjects, ten say "for all natural numbers n" (a Nat exponent, so the
rule reaches them), one says "for all sufficiently large n" (a threshold, not
a bound), and one is Fermat's little theorem at exponent `p - 1` for an
arbitrary prime `p`. Whether a given subject's reading actually declares its
exponent object as `Nat` is a **measurement the next corpus cycle makes**, not
something this receipt may assert. A subject returning to ready is a selection
fact and never a prediction that it will certify.

## Bill items and where each was paid

| item | where |
|---|---|
| validator + admission rule | `generators/math_reading._check_pow_exponent`, called from `_check_carrier_ops` |
| eval semantics | `generators/math_eval.py` `^` branch (mirrors `Int.toNat`) |
| SMT | `generators/math_smt.py`: shape-keyed enum route, named refusal in `render_term`, total `_term_nonlinear` |
| Lean rendering | `generators/math_compile.py` `^` branch (`Monoid.npow`, no coercion) |
| reflect slice | `tools/FgReflect.lean`: `Tm.pow` + six walker cases |
| growth-registry row | `buildloop/growth_protocol.py` `pow-symbolic-exponent` (+2 signature pins); conformance green, completeness canary green |
| prompt grammar | `buildloop/math_prompt.py` |
| batteries + teeth | `tests/test_pow_battery.py` (new), `tests/test_symbolic_exponent_class.py` and `tests/test_symbolic_exponent_demand.py` (converted to post-purchase duals) |
| re-census delta | this receipt; zero, recorded |

### The structural split the gate needed

`_check_term` is carrier-blind, so it now ADMITS a well-formed non-literal
exponent and decides nothing; `_check_carrier_ops` — the one walk that
resolves carriers — decides admissibility. Structure in one place, carrier in
the other. Deciding it in both would be two rules that can disagree; deciding
it in neither would be a hole.

### The measurement files were inverted, not deleted

`tests/test_symbolic_exponent_class.py` said, in writing, that a purchase
adding `Tm.pow` "reds the assertions below, which is the point: the class claim
must be falsifiable by the very edit that would change it." This is that edit.
Each refuted tooth was replaced by its post-purchase dual, and each
replacement is at least as strong:

* `test_the_gate_refuses_a_symbolic_exponent_with_the_quoted_rule` →
  `test_the_gate_admits_a_symbolic_exponent_only_at_carrier_Nat`
* `test_every_downstream_layer_reads_the_literal_by_subscript` →
  `test_no_downstream_layer_reads_the_literal_by_subscript_any_more`, plus a
  new `test_a_symbolic_exponent_routes_the_reading_to_enumeration`
* `test_the_reflect_slice_has_no_term_level_exponent` →
  `test_the_reflect_slice_now_has_a_term_level_exponent_and_every_walker_answers_it`

The pre-purchase reading is preserved *here*, in this receipt, which is where a
superseded measurement belongs.

### Pins moved in this commit, and why each was allowed to move

`tests/test_fg_reflect_shape.py::test_tm_constructors_match_the_pin` is the
attendance fence over the reflect slice: it reds on any added constructor and
its own failure advice says *"If the growth IS intended, update the pin in
tests/test_fg_reflect_shape.py in THIS commit and say so in the delta
receipt."* This is that sentence. The pin moved from six constructors to seven,
in this commit, and the attendance question it guards is answered above under
the `lean-local` probe.

Two other pins moved, both mechanically forced and neither a judgment:

* `tests/test_function_symbol_class.py`'s copy of the `Tm` constructor list.
  P8's verdict is untouched — it needs an APPLICATION node, which `Tm.pow` is
  not — but that file's *price* claim ("the ceiling is five, not eleven") rested
  on `^` refusing every variable exponent, which stopped being true. The claim
  is **amended in place with the reading, not the projection**: the ceiling of
  five stands as the last MEASURED number, and whether P7 lifts it is a
  next-corpus-cycle measurement through
  `intake_from_frontier --unblocked refused:symbolic-exponent`.
* `tests/golden/math_prompt_operator_seam.json`, the prompt byte-pin. It exists
  to catch unintended drift from the operator seam; this drift is intended (the
  grammar clause for `^`). Regenerated with a line-by-line diff check, and the
  diff is exactly the one clause — 2 lines — so nothing unrelated was absorbed.

`powTm : Tm -> Nat -> Tm` is deliberately **kept**. A literal-width power still
has a literal-width spelling, and deleting it would have re-verdicted every
existing bigop reading to buy nothing. The purchase is additive to the slice's
vocabulary, not a replacement of it — and the literal path's byte-invariance is
measured at all four consumers rather than asserted.

## Why an unattended session took a tower-class bill

§3.1 rule 3 makes tower-class work attended-only *unless* the container can
elaborate Lean locally, because local iteration is what attendance was buying.
`tools/lean_env_probe.py` was **RUN in this session** (never read off disk) and
returned:

```
verdict: lean-local
```

The probe's own honesty field says it measures **presence**, not capability, so
the verdict was corroborated by direct measurement rather than trusted:

* the full pinned `common.MATHLIB_IMPORTS` set (including
  `Mathlib.Tactic.NormNum`) elaborated with `ok=True` and a clean transcript;
* `tests/test_statement_cert.py` — Lean-gated, real elaboration — passed
  18/18 in 131s;
* the complete post-purchase `tools/FgReflect.lean` **elaborates locally**;
* the ill-typed Int-exponent probe **fails** to elaborate, so the tooth that
  justifies the carrier rule was mutation-verified rather than assumed.

This matters because PR #181 (open at the time of this purchase) reports
`unknown module prefix 'Plausible'` and argues these containers cannot
elaborate a Mathlib-importing file. **That reading did not reproduce here**,
on `main` at `b6509f6`. It is recorded as a disagreement between two
measurements rather than silently resolved in this purchase's favour.

**A local green is NECESSARY and never SUFFICIENT.** The CI Lean lane is the
done-predicate; all Lean-touching edits ride the final `lean-fast` commit.

## Per-commit gate

Run as `CGB_LEAN=0 python3 -m pytest tests/ -q`, per `CLAUDE.md` as amended by
PR #182 (merged mid-session): local Lean is for authoring iteration, never the
per-commit gate.

## Bounds held

P5 not promoted and not touched. `kernel/certs.py` pins, `TRUST.md` and the
escape-gate blocklist untouched — the blocklist in fact refused the token
`syntax` in a first draft of a source comment, and the comment was reworded
rather than the blocklist edited. The only ceremony-reserved path this diff
touches is `buildloop/growth_protocol.py`, and its diff is rows added to
`GROWERS` and `SIGNATURE_PINS` with nothing else moved.

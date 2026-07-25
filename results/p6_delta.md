# P6 purchase receipt — the propositional connectives `not` and `iff` (PLAN_FRAGMENT §2/§4 P6)

**The purchase.** `not` (unary) and `iff` (binary) landed through the full
admission bill.  `_CONNECTIVES` was exactly `{and, or, implies}`, so a source
that negated an atom or stated a biconditional had no faithful reading at all;
it is now `{and, or, implies, not, iff}`.

This is the first purchase on the CONNECTIVE axis, the first priced by MEASURED
REFUSALS rather than by census vocabulary, and the first anywhere here whose
bill came in **smaller than the queue declared**.  §4 P6 declared it
tower-class against the possibility that negation needs a `Pd` constructor, and
said in as many words that which bill it really is "is a fact about the slice
that only the purchase can measure".  The purchase measured it.  The answer is
that negation needs no constructor, and this receipt is where that stops being
a preference and starts being a table.

## The additive-class argument, and the table it rests on

Two claims, and neither is about what the new words *can* express — both are
about what they *cost*.

**`iff` is pure DESUGARING.**  `a <-> b` **is** `(a -> b) and (b -> a)`.  The
SMT mirror emits literally that conjunction; Lean's `↔` is notation for it; the
reflect slice will quote it as `pand` of two `pimp`.  No channel learns a new
idea, so no channel can get a new idea wrong.

**`not` is NEGATION-NORMAL FORM.**  It never has to be *carried*.  It pushes
through the connectives by De Morgan — and through an implication as
`not (a -> b) == a and not b`, the rewrite that returns the antecedent
**positive** — until it reaches an atom, where it becomes a *different atom the
fragment already has*:

| atom | its negation | swaps? |
|---|---|---|
| `a = b` | `a != b` | no |
| `a != b` | `a = b` | no |
| `a <= b` | `b < a` | **yes** |
| `a < b` | `b <= a` | **yes** |
| `even n` | `odd n` | no |
| `odd n` | `even n` | no |

The two order rows are the ones worth staring at: `<=` and `<` are duals only
*across the arguments*.  `not (a <= b)` is `b < a`, never `a < b`, and a
lowering that drops the swap is a silent lie about the reading — which is why
the swap has its own half of the divergence tooth below rather than a comment.

The table lives at `generators/math_reading._ATOM_DUALS`, is consumed through
the single accessor `_dual_atom`, and every row of it is witnessed
symbolically by both solvers and pointwise by the evaluator in
`tests/test_connective_battery.py::test_atom_dual_table_is_exhaustively_witnessed`.

**Therefore: no new `Tm` constructor, no new `Pd` constructor, no new
`Decidable` instance, and `tools/FgReflect.lean` is byte-untouched.**  §3.1
rule 3(a) — which puts any new `Tm`/`Pd` constructor outside the additive class
— is not *satisfied* here, it is *not reached*.  The purchase is
**additive-desugaring**, a bill class this cycle adds to
`tools/purchase_frontier.py::BILL_CLASSES` because the queue had no name for a
purchase that grows the vocabulary without growing anything that represents it.

`connective-node-class` is registered in `buildloop/growth_protocol.py` with
all seven roles; `ANTI_LIST` is byte-untouched.

## The named skip: the atoms with no dual

`dvd` and `coprime` carry **no dual in the fragment**.  "a does not divide b"
is not any other atom here, and non-coprimality is not the coprimality of
anything.  A negation that lands on either cannot be pushed to an atom, and the
fragment has no negation NODE to leave it at — that node is a constructor, i.e.
exactly the tower-class purchase this row declared and deliberately did not
make.

So it refuses, by name, as first-class demand data:

    not:dvd-no-dual        not:coprime-no-dual

Two findings are worth recording against the design as it was written down
before the work:

1. **`dvd` is not the only dual-less atom.**  It is the only one in the reflect
   slice's `Pd`, which is where the design note was looking; at the level the
   GATE freezes — the whole fragment — `coprime` has no dual either.  Naming
   only `dvd` would have hidden a second missing dual behind the first, so the
   refusal is a FAMILY (`not:<op>-no-dual`) emitted by one rule rather than a
   hand-listed string.  A split is non-destructive: neither signal is the
   other's excuse.
2. **The freeze is `Pd`'s polarity algebra, not classical NNF.**  `Pd` carries
   `pand`/`por`/`pimp` as CONSTRUCTORS, so a POSITIVE implication needs no push
   at all and both its arms stay positive.  Reading `a -> b` classically as
   `not a or b` would have put every antecedent in negative position and
   RETROACTIVELY REFUSED every committed reading whose hypothesis divides
   something.  A purchase that re-verdicts yesterday's readings is not additive,
   whatever else it is; `test_positive_dvd_under_implies_and_iff_still_parses`
   is the tooth that says so.

## The bill, item by item

- **validator / lexicon** (`generators/math_reading.py`): `_CONNECTIVES` grown
  by the two words; `_CONNECTIVE_ARITY` as the single source for both the gate's
  width check and `op_signature`'s arity field (so the recurrence miner's
  op-slot typing cannot drift from the grammar); `_ATOM_DUALS` + `_dual_atom` as
  the conserve argument in code; `_check_connective_nnf` as the freeze, walked
  once per hypothesis/conclusion beside the P3/P4 carrier walks, and descending
  into `setbuild` filters so a negation cannot hide under `card`.
- **eval semantics** (`generators/math_eval.py`): both words on the ordinary
  truth table, deliberately NOT through the NNF push.  Eval's job is to be the
  obvious reading of the AST; a rewrite here would put a transformation between
  the AST and the number the batteries trust.  NNF proves the SHAPE is
  representable; Python's `not` is what the shape MEANS; the battery pins the
  two against each other pointwise.
- **SMT mirror** (`generators/math_smt.py`): `not` as `(not …)`; `iff` as the
  DESUGARING `(and (=> a b) (=> b a))` rather than SMT-LIB's Bool-sorted
  `(= p q)`.  The reason is written at the site and pinned by a tooth: emitting
  `(= p q)` would make this the one channel carrying the biconditional as a
  PRIMITIVE, so a divergence between "iff as a primitive" and "iff as two
  implications" would have nowhere to show up.  The two renderings are proved
  to be the same formula, so the choice is shape and never meaning.  The three
  connective-transparent walkers (`_pred_uses_enum`, `_pred_has_ref`,
  `_pred_nonlinear`) already sourced `_CONNECTIVES`; the hand-written second
  copy of that set in this module is deleted and IMPORTED from the grammar,
  because a set that now changes may not have two homes.
- **Lean rendering** (`generators/math_compile.py`): `(¬ p)` and `(p ↔ q)`.
  `¬` and `↔` are **Sm-class math symbols, not word characters**, so T7's
  non-ASCII IDENTIFIER rule does not reach them — exactly as it does not reach
  `∧ ∨ → ≤ ≠ ∣`.  VERIFIED against `buildloop/validate_lean.py` rather than
  assumed; the prefix forms `Not` / `Iff` were the fallback and are not needed.
- **kernel vocabulary pin** (`kernel/rung.py`): `_CONNECTIVES` and `_ARITY`
  grown to match the grammar (SHAPE only — whether a negation can be pushed is
  the reading gate's call).  The anti-drift test now reconstructs the connective
  widths FROM `_CONNECTIVE_ARITY` instead of re-listing them, since a second
  hand-written copy is the drift that test exists to catch.
- **census surface** (`buildloop/census.py`): `_BUILTIN_ALIASES` rows `¬`/`Not`
  and `↔`/`Iff`.  Required — the derivation raises on a builtin with no alias
  row — and honest: `¬` and `↔` stop being foreign surface the moment the
  fragment can read them, and reporting them as foreign afterwards would be the
  census lying in our favour.
- **prompt grammar** (`buildloop/math_prompt.py`): `_PRED_AST_NOTE` states both
  words, the NNF reading, the dual table including the ARGUMENT SWAP, and the
  named miss; `tests/golden/math_prompt_operator_seam.json` regenerated.
- **growth-protocol registry** (`buildloop/growth_protocol.py`): the
  `connective-node-class` row, all seven roles, with `_check_connective_nnf`
  and `_dual_atom` signature-pinned; completeness canary green.
- **batteries + teeth** (`tests/test_connective_battery.py`, 40 collected
  teeth), below.
- **queue view** (`tools/purchase_frontier.py`): the `additive-desugaring` bill
  class; the P6 row carrying its grower key and this receipt; the
  `iff-connective` / `not-connective` reasons re-tensed, because they described
  a fragment that no longer exists.

## The §2 re-census delta: ZERO, and this row never owed one

`python3 tools/regen_downstream.py --from census_portfolio` over the six
committed corpora (1 008 nodes) returns every census artifact
**byte-identical**:

| verdict | before | after |
|---|---|---|
| `attempt-candidate` | 108 | **108** |
| `no-signal` | 169 | **169** |
| `out-of-fragment` | 731 | **731** |

The miss histogram is unchanged row for row.  The mathlib-side census
(`specs/mathsources/mathlib/census.json`) is unchanged too, even though the
resident identifier set genuinely grew by `¬`/`Not`/`↔`/`Iff` — the residency
widened, the classification did not move.

**This is not the P1/P2/P4 zero.**  Those were census-priced rows that hoped for
a delta and honestly did not get one.  P6 is **refusal-priced** (§4's own
distinction), and a refusal-priced row's price is not a census number at all —
it is the `refused:<signal>` group returning to the intake window.  A census
delta here would have been a *surprise*, not a success: `tools/blueprint_census.py`
prices lexical SUBJECT-MATTER vocabulary (operator words and carrier names), and
"not" and "iff" are not subject matter.  Recording the zero is recording that
the instrument measured what it measures.

**What this row actually bought**, from the derived queue
(`results/purchase_frontier.json`, `refill_projection`) rather than from prose:
the three groups it meets are `not-connective` **6**, `iff-connective` **8** and
`definition-biconditional` **7** — 21 group MEMBERSHIPS, the largest single
demand on the board — and the projection says **13 DISTINCT SUBJECTS** return to
ready when it lands.  The gap between 21 and 13 is not slippage; it is the
projection counting subjects while the groups count a subject once per signal it
carries, and 5 of those subjects are held by a second signal this row does not
meet.

Two honesty notes carried verbatim from the queue's own rules.  First, **the
refill is not realized by this commit**: it is realized by the NEXT corpus cycle,
through `python3 tools/intake_from_frontier.py --unblocked refused:not-connective`
(and the two sibling signals), and the number that cycle measures is the number
of record — this one is a projection.  Second, **a subject returning to ready is
a SELECTION fact and never a promise it will certify**; it passed selection once
and was demoted by a measured refusal, so retiring that refusal returns it to the
window where it is a candidate again, exactly as it was before.

`results/frontier_refusals.jsonl` is untouched, as it must be: the ledger is
append-only, and evidence is never re-measured to force a green.

## What this purchase does NOT buy

- **No negation constructor.**  A `Pd` negation node — and the `Decidable`
  instance and the walker cases that come with it — remains tower-class and
  unbought.  `not:dvd-no-dual` and `not:coprime-no-dual` are its demand, now
  measurable instead of hypothetical.
- **No reflect probe for the new words, yet.**  The reflect quoting rides a
  LATER commit; the additive claim is about what the slice would have to GROW
  (nothing), not about what it already quotes.  Until that commit, a reading
  using `not`/`iff` takes the EXISTING fail-closed
  `op-out-of-reflect-slice:not` / `:iff` skip — a named skip that predates this
  purchase and is already in the sweep's allowlist.  Nothing fails open, and
  nothing new was invented to describe it: introducing a `not:negated-dvd`
  reflect-skip name today would have been dead vocabulary, since the gate
  refuses that shape before a quoter could ever see it.
- **No definitions.**  `definition-biconditional`'s 7 rows are filed here
  because `iff` is their FIRST blocker, and they are kept named apart for the
  reason §4 gives: a DEFINITION may still need P8's definitional-extension
  mechanism underneath.  Whether those seven certify is measured next cycle,
  never claimed here.
- **No set objects, no symbolic exponents, no function symbols.**  P7/P8/P9 are
  untouched.  The two `refusal-set-carrier` subjects each carry a connective
  refusal as well, so P6 is the row that makes them *reachable* by P9 — it does
  not reach them itself.
- **No trust-root movement.**  `ANTI_LIST`, `kernel/certs.py`, `TRUST.md`, the
  escape-gate blocklist and the primitive ladder rungs are byte-untouched.

## Teeth

`tests/test_connective_battery.py` — 40 collected teeth on the
bigop/finset/rat/zmod battery template:

- a **differential truth-table battery** (17 planted ground rows: double
  negation, De Morgan both ways, both polarities of the negated implication,
  both biconditional polarities, every atom dual including the two that SWAP,
  and deliberately FALSE rows that must come back `unsat` — the battery can
  fail), each verdict corroborated three ways: an independent Python truth-table
  oracle, `math_eval.eval_pred`, and the ground SMT differential on **both**
  solvers; plus a free-object row swept over a grid;
- a **symbolic identity battery** — the additive-class argument itself, asserted
  rather than believed: involution, all three De Morgan laws, the
  `not (a -> b) == a and not b` rewrite, the `iff` desugaring, `not (a <-> b)`,
  and every `_ATOM_DUALS` row, each as a `iff`-wrapped identity whose NEGATION
  both solvers must call `unsat`, corroborated pointwise by the evaluator; and
  two deliberately false identities that must come back `sat`;
- **`test_lossy_demorgan_flip_gets_no_certificate`**, the planted-lossy tooth
  and the registry's divergence index.  A negation push that forgets to FLIP
  `and` into `or`, and a dual that forgets to SWAP the order atom's arguments,
  are each rendered honestly — they are preds this fragment ADMITS, which is
  what makes them dangerous, since nothing downstream would refuse them on
  shape.  Each is refused two ways (the identity flips `unsat → sat`; the
  divergence obligation comes back `sat`) with the evaluator naming the
  divergence point, so no solver verdict is an artefact of the encoding;
- **`test_iff_desugaring_is_the_same_claim_as_a_bool_equality`** — the
  desugared rendering and `(= p q)` proved to be the same formula, which is what
  licenses the comment at the rendering site;
- **`test_connectives_do_not_move_the_declared_logic`** — QF_LIA stays QF_LIA
  through `not` and `iff`, and a nonlinear atom is still SEEN through them.  A
  purchase that silently escalated the declared logic would be spending a budget
  nobody billed, and the declared logic is not advisory: CVC5's parser enforces
  it;
- the **gate refusal surface** (`not:<op>-no-dual` on both dual-less atoms,
  including when De Morgan carries the negation down to one through `and`/`or`/
  a negated implication/a negated biconditional; the arities as MALFORMATIONS
  and never as demand data), and **`test_every_pre_p6_refusal_still_refuses`** —
  P1's symbolic bound, P3's `/@Int`, P4's `<=@ZMod 5`, the variable exponent and
  an unknown atom, all re-run against the grown grammar so the purchase can be
  SEEN not to have widened anything on its way past;
- the residue row (`ZMod n` admits `=`/`!=`, which are each other's dual, so the
  connectives ride in without a single new refusal — the smallest possible
  statement of what "additive" means here), the Lean rendering + escape gate +
  hash byte-stability, and an end-to-end gate → eval → compile → escape row.

The GATE half of the registry's teeth index points at
`tests/test_math_reading.py::test_negated_dvd_is_a_fragment_miss`, where that
refusal is decided; the DIVERGENCE half points into the battery, where a
lowering is caught lying.  One tooth per half of the bill, the shape every row
above it uses.

**Full suite green.**  One purchase this cycle, its re-census delta committed in
the same session that measured it.

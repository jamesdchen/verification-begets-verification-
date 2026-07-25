"""P6 admission batteries: the propositional connectives `not` and `iff`.

The PLAN_FRAGMENT §4 bill, applied to the first purchase on the CONNECTIVE
axis -- and to the first one whose whole claim is that it adds NOTHING.  P1
bought a binding node, P2 a set node, P3 and P4 carriers; each of those had to
argue that a NEW thing behaves.  P6 has to argue the opposite: that neither new
word is a new thing at all.

  * `iff` is DESUGARING.  `a <-> b` IS `(a -> b) and (b -> a)` -- the SMT
    mirror emits exactly that conjunction, Lean's `↔` unfolds to it, and the
    reflect slice will quote it as `pand` of two `pimp`.  No representation
    learns a new idea.
  * `not` is NEGATION-NORMAL FORM.  It never has to be CARRIED: it pushes
    through the connectives by De Morgan (`not (a -> b)` == `a and not b`) to
    an atom, and there it becomes a DIFFERENT ATOM THE FRAGMENT ALREADY HAS
    (`=`/`!=`, `<=`/`<` with the arguments SWAPPED, `even`/`odd`).

That is the ADDITIVE-CLASS argument (§3.1 rule 3), and this file is where it
stops being prose.  LLM-free, Lean-free teeth, in the operator-growth battery
discipline:

  * (b-analogue) DIFFERENTIAL TRUTH-TABLE battery: over planted ground rows
    (double negation, De Morgan both ways, a negated implication, both
    biconditional polarities, each atom dual including the ORDER swap),
    ``math_eval.eval_pred``'s verdict is corroborated by an independent Python
    truth-table oracle AND by the ground SMT differential on z3 and cvc5
    (dual-solver agreement; absent cvc5 degrades honestly).  Both directions
    carry teeth: a true row must be ``sat``, a false row ``unsat``.
  * (b2-analogue) SYMBOLIC battery: the objects stay FREE and the IDENTITY's
    negation is asserted; a dual-solver ``unsat`` is agreement at every point.
    This is where the two claims above are actually checked -- involution, all
    three De Morgan laws, the `not (a -> b)` rewrite, the `iff` desugaring, and
    every row of the `_ATOM_DUALS` table.  A deliberately false identity (the
    order dual with the swap DROPPED) must come back ``sat`` -- the battery can
    fail.
  * LOSSY DE MORGAN FLIP GETS NO CERTIFICATE: the planted-lowering tooth.  A
    negation push that forgets to flip `and` into `or`, and one that forgets to
    swap the order atom's arguments, are each rendered honestly (they are
    preds the fragment admits -- that is what makes them dangerous) and the
    differential refuses them two ways, with the evaluator witnessing the
    divergence pointwise.
  * NO NEW SORT, NO NEW LOGIC: the declared SMT logic is a function of the
    ARITHMETIC, and connectives are transparent to it, so wrapping a pred in
    `not`/`iff` may not move QF_LIA.  Pinned, because a purchase that silently
    escalated the logic would be paying a cost nobody billed.
  * The gate's refusal surface (a negation landing on a dual-less atom; the
    arities) is pinned as demand data, and every PRE-P6 refusal is re-run
    against the grown grammar so the purchase can be seen not to have widened
    anything on its way past.
  * The Lean rendering rides the escape gate and the statement hash is
    byte-stable.

Named limits this file pins as limits, not as gaps: `dvd` and `coprime` carry
no dual in the fragment, so a negation reaching either is `not:<op>-no-dual` --
first-class demand data for the negation-CONSTRUCTOR purchase §4 P6 declared
tower-class and this one deliberately did not make.  And the reflect slice's
quoting of the two new words rides a later commit: until it lands, a reading
that uses them keeps the EXISTING fail-closed `op-out-of-reflect-slice:` skip
rather than a probe, which is the honest state and not a silent one.
"""
import json

import pytest

from generators.math_reading import (
    parse_math_reading, BadMathReading, FragmentMiss, _ATOM_DUALS, _dual_atom)
from generators.math_eval import eval_pred
from generators import math_smt
from generators.math_compile import compile_math_reading
from buildloop.validate_lean import validate_lean
from kernel.backends import SmtBackend


def _dual(smtlib, expect):
    """Run both solvers with the given expectation; return the raw SmtBackend
    verdicts ('pass' = answered as expected, 'fail' = answered the opposite)."""
    be = SmtBackend()
    z = be.run_z3(smtlib, expect=expect).get("result")
    c = be.run_cvc5(smtlib, expect=expect).get("result")
    return z, c


# ------------------------------------------------------------ AST shorthands
def _lit(k):
    return {"lit": k}


def _ref(n):
    return {"ref": n}


def _add(*a):
    return {"op": "+", "args": list(a)}


def _eq(a, b):
    return {"op": "=", "args": [a, b]}


def _ne(a, b):
    return {"op": "!=", "args": [a, b]}


def _le(a, b):
    return {"op": "<=", "args": [a, b]}


def _lt(a, b):
    return {"op": "<", "args": [a, b]}


def _even(a):
    return {"op": "even", "args": [a]}


def _odd(a):
    return {"op": "odd", "args": [a]}


def _dvd(a, b):
    return {"op": "dvd", "args": [a, b]}


def _and(*p):
    return {"op": "and", "args": list(p)}


def _or(*p):
    return {"op": "or", "args": list(p)}


def _imp(p, q):
    return {"op": "implies", "args": [p, q]}


def _not(p):
    return {"op": "not", "args": [p]}


def _iff(p, q):
    return {"op": "iff", "args": [p, q]}


# ------------------------------------------------------------ reading builder
def _doc(objects, concl, hyps=(), ambient=None):
    """A minimal gate-legal reading: one object per entry, a ∀ quantifier over
    them, the presupposed hypotheses and the demanded conclusion.  The SOURCE is
    synthesized from the quotes, so groundedness holds by construction (these
    teeth are about the connectives, not the quote gate)."""
    stmts = []
    if ambient is not None:
        stmts.append({"id": "amb", "force": "choice", "quote": "",
                      "lf": {"kind": "ambient", "carrier": ambient}})
    for name in sorted(objects):
        stmts.append({"id": f"obj_{name}", "force": "demand",
                      "quote": f"the number {name} of type {objects[name]}",
                      "lf": {"kind": "object", "name": name,
                             "type": objects[name]}})
    if objects:
        stmts.append({"id": "qf", "force": "demand",
                      "quote": "for every number named above",
                      "lf": {"kind": "quantifier", "binder": "forall",
                             "objects": sorted(objects)}})
    for i, h in enumerate(hyps):
        stmts.append({"id": f"hyp{i}", "force": "presupposition",
                      "quote": f"the side condition number {i}",
                      "lf": {"kind": "hypothesis", "pred": h}})
    stmts.append({"id": "concl", "force": "demand",
                  "quote": "the asserted claim",
                  "lf": {"kind": "conclusion", "pred": concl}})
    src = " ".join(s["quote"] for s in stmts if s["quote"])
    return json.dumps({"theorem": "connective_battery",
                       "statements": stmts}), src


def _parse(objects, concl, hyps=(), ambient=None):
    doc, src = _doc(objects, concl, hyps, ambient)
    return parse_math_reading(doc, src)


# ------------------------------------------------------- independent oracle
def _truth(pred, assignment):
    """The oracle verdict, in plain Python, independently of math_eval: the
    connectives on their ordinary truth table over atoms decided by direct
    integer arithmetic.  Deliberately NOT a re-import of eval_pred -- a mirror
    that shares its implementation with the thing it mirrors checks nothing."""
    op, args = pred["op"], pred["args"]
    if op == "and":
        return all(_truth(a, assignment) for a in args)
    if op == "or":
        return any(_truth(a, assignment) for a in args)
    if op == "implies":
        return (not _truth(args[0], assignment)) or _truth(args[1], assignment)
    if op == "not":
        return not _truth(args[0], assignment)
    if op == "iff":
        return _truth(args[0], assignment) is _truth(args[1], assignment)

    def v(t):
        if "lit" in t:
            return t["lit"]
        if "ref" in t:
            return assignment[t["ref"]]
        if t["op"] == "+":
            total = 0
            for a in t["args"]:
                total += v(a)
            return total
        raise AssertionError(f"oracle: unexpected term op {t.get('op')!r}")

    if op == "=":
        return v(args[0]) == v(args[1])
    if op == "!=":
        return v(args[0]) != v(args[1])
    if op == "<=":
        return v(args[0]) <= v(args[1])
    if op == "<":
        return v(args[0]) < v(args[1])
    if op == "even":
        return v(args[0]) % 2 == 0
    if op == "odd":
        return v(args[0]) % 2 != 0
    if op == "dvd":
        a, b = v(args[0]), v(args[1])
        return (b % a == 0) if a != 0 else (b == 0)
    raise AssertionError(f"oracle: unexpected atom {op!r}")


# ---------------------------------------------------------- SMT obligations
def _declare(name, ty):
    lines = [f"(declare-const {name} Int)"]
    if ty == "Nat":
        lines.append(f"(assert (>= {name} 0))")
    return lines


def _ground_pred(pred, objects, carrier, assignment):
    """Pin every object and assert the pred: ``sat`` iff the solvers' logic
    agrees the pred HOLDS there."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.extend(_declare(name, objects[name]))
        lines.append(
            f"(assert (= {name} {math_smt._render_lit(assignment[name])}))")
    lines.append(f"(assert {math_smt.render_pred(pred, objects, carrier)})")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _symbolic_valid(pred, objects, carrier):
    """Objects FREE, assert the pred's NEGATION: unsat = the pred holds at
    EVERY point (the b2 shape for a predicate)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.extend(_declare(name, objects[name]))
    lines.append(
        f"(assert (not {math_smt.render_pred(pred, objects, carrier)}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _distinct_preds(honest, lossy, objects, carrier):
    """The divergence obligation: the two renderings xor'd over a FREE domain.
    ``sat`` says a point exists where they disagree -- corroborated by eval,
    never load-bearing alone (the operator_growth._carrier_stability_obligation
    direction-split discipline)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.extend(_declare(name, objects[name]))
    lines.append("(assert (xor "
                 f"{math_smt.render_pred(honest, objects, carrier)} "
                 f"{math_smt.render_pred(lossy, objects, carrier)}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


# ============================================ (b) differential truth-table battery
# Planted GROUND rows: the shapes the two new words exist to get right.
# `expected` is stated by hand AND recomputed by the oracle, so a typo in
# either one is caught.
_PLANTED = [
    # (label, pred, expected)
    ("not_false_atom", _not(_eq(_lit(2), _lit(3))), True),
    ("not_true_atom", _not(_eq(_lit(2), _lit(2))), False),
    ("double_negation", _not(_not(_eq(_lit(2), _lit(2)))), True),
    # De Morgan, both directions, stated as ground rows.
    ("demorgan_and", _not(_and(_eq(_lit(1), _lit(1)), _eq(_lit(1), _lit(2)))),
     True),
    ("demorgan_or", _not(_or(_eq(_lit(1), _lit(2)), _eq(_lit(1), _lit(3)))),
     True),
    # `not (a -> b)` is `a and not b` -- the rewrite that keeps the antecedent
    # POSITIVE, which is the one everyone gets backwards.
    ("not_implies_true", _not(_imp(_eq(_lit(1), _lit(1)), _eq(_lit(1),
                                                              _lit(2)))), True),
    ("not_implies_false", _not(_imp(_eq(_lit(1), _lit(2)), _eq(_lit(1),
                                                               _lit(2)))),
     False),
    # both biconditional polarities, and the false row that gives it teeth.
    ("iff_both_true", _iff(_eq(_lit(1), _lit(1)), _le(_lit(1), _lit(2))), True),
    ("iff_both_false", _iff(_eq(_lit(1), _lit(2)), _lt(_lit(2), _lit(1))),
     True),
    ("iff_mismatched", _iff(_eq(_lit(1), _lit(1)), _eq(_lit(1), _lit(2))),
     False),
    # every atom dual, as a ground biconditional: the `_ATOM_DUALS` table,
    # asserted rather than believed.  The ORDER rows are the ones that swap.
    ("dual_eq", _iff(_not(_eq(_lit(2), _lit(3))), _ne(_lit(2), _lit(3))), True),
    ("dual_ne", _iff(_not(_ne(_lit(2), _lit(2))), _eq(_lit(2), _lit(2))), True),
    ("dual_le_swaps", _iff(_not(_le(_lit(3), _lit(2))), _lt(_lit(2), _lit(3))),
     True),
    ("dual_lt_swaps", _iff(_not(_lt(_lit(2), _lit(2))), _le(_lit(2), _lit(2))),
     True),
    ("dual_even", _iff(_not(_even(_lit(3))), _odd(_lit(3))), True),
    ("dual_odd", _iff(_not(_odd(_lit(4))), _even(_lit(4))), True),
    # the order dual WITHOUT the swap is a different claim, and false here --
    # the ground half of the swap tooth.
    ("le_dual_without_swap_is_false",
     _iff(_not(_le(_lit(3), _lit(2))), _lt(_lit(3), _lit(2))), False),
]


@pytest.mark.parametrize("label,pred,expected", _PLANTED,
                         ids=[p[0] for p in _PLANTED])
def test_truth_table_battery_eval_agrees_with_dual_solver(label, pred,
                                                          expected):
    assert _truth(pred, {}) is expected, f"{label}: oracle disagrees"
    v = eval_pred(pred, {}, {}, "Int")
    assert bool(v) is expected, f"{label}: evaluator says {v}"
    want = "sat" if expected else "unsat"
    z, c = _dual(_ground_pred(pred, {}, "Int", {}), want)
    assert z == "pass", f"{label}: z3 {z}"
    assert c in ("pass", "unknown", "error"), f"{label}: cvc5 {c}"


def test_truth_table_battery_over_free_objects():
    """The same differential with OBJECTS in the atoms, pinned at each point of
    a small grid: the negated implication, evaluated pointwise in all three
    channels."""
    objects = {"a": "Int", "b": "Int"}
    pred = _not(_imp(_le(_ref("a"), _ref("b")), _eq(_ref("a"), _ref("b"))))
    for av in range(-2, 3):
        for bv in range(-2, 3):
            asg = {"a": av, "b": bv}
            want = _truth(pred, asg)
            assert eval_pred(pred, asg, objects, None) is want, asg
            z, c = _dual(_ground_pred(pred, objects, "Int", asg),
                         "sat" if want else "unsat")
            assert z == "pass", f"{asg}: z3 {z}"
            assert c in ("pass", "unknown", "error"), f"{asg}: cvc5 {c}"


# =================================================== (b2) symbolic identity battery
# THE ADDITIVE-CLASS ARGUMENT ITSELF.  Each row is an identity between a shape
# that USES a new connective and a shape that does not; a dual-solver `unsat`
# on its negation says the two are the same claim at every point, i.e. that the
# new word introduced no new meaning for any channel to get wrong.
_A, _B = _ref("a"), _ref("b")
_P = _le(_A, _B)
_Q = _even(_A)
_IDENTITIES = [
    ("involution", _iff(_not(_not(_P)), _P), True),
    ("demorgan_and", _iff(_not(_and(_P, _Q)), _or(_not(_P), _not(_Q))), True),
    ("demorgan_or", _iff(_not(_or(_P, _Q)), _and(_not(_P), _not(_Q))), True),
    # the rewrite the freeze names explicitly: the antecedent comes back
    # POSITIVE.
    ("not_implies", _iff(_not(_imp(_P, _Q)), _and(_P, _not(_Q))), True),
    # `iff` IS the conjunction of two implications -- the desugaring, asserted.
    ("iff_desugars", _iff(_iff(_P, _Q), _and(_imp(_P, _Q), _imp(_Q, _P))),
     True),
    ("not_iff", _iff(_not(_iff(_P, _Q)),
                     _or(_and(_P, _not(_Q)), _and(_Q, _not(_P)))), True),
    # every `_ATOM_DUALS` row, symbolically.
    ("dual_eq", _iff(_not(_eq(_A, _B)), _ne(_A, _B)), True),
    ("dual_le", _iff(_not(_le(_A, _B)), _lt(_B, _A)), True),
    ("dual_lt", _iff(_not(_lt(_A, _B)), _le(_B, _A)), True),
    ("dual_even", _iff(_not(_even(_A)), _odd(_A)), True),
    # THE BATTERY CAN FAIL: the order dual with the swap dropped is NOT an
    # identity, and a `sat` is the only honest answer.
    ("le_dual_without_swap", _iff(_not(_le(_A, _B)), _lt(_A, _B)), False),
    # nor is the De Morgan law with the connective left unflipped.
    ("demorgan_unflipped", _iff(_not(_and(_P, _Q)), _and(_not(_P), _not(_Q))),
     False),
]


@pytest.mark.parametrize("label,identity,valid", _IDENTITIES,
                         ids=[i[0] for i in _IDENTITIES])
def test_symbolic_identity_battery(label, identity, valid):
    objects = {"a": "Int", "b": "Int"}
    # the reading has to be gate-legal before it is asked anything else.
    _parse(objects, identity)
    z, c = _dual(_symbolic_valid(identity, objects, "Int"),
                 "unsat" if valid else "sat")
    assert z == "pass", f"{label}: z3 {z}"
    assert c in ("pass", "unknown", "error"), f"{label}: cvc5 {c}"
    if valid:
        # corroborated pointwise by the evaluator, so the `unsat` is never
        # load-bearing on its own.
        for av in range(-3, 4):
            for bv in range(-3, 4):
                asg = {"a": av, "b": bv}
                assert eval_pred(identity, asg, objects, None) is True, \
                    f"{label}: evaluator disagrees at {asg}"
    else:
        # a counterexample the EVALUATOR can name, so the `sat` is corroborated
        # in the same currency.
        assert any(eval_pred(identity, {"a": av, "b": bv}, objects, None)
                   is False
                   for av in range(-3, 4) for bv in range(-3, 4)), \
            f"{label}: solver says sat but eval found no witness"


def test_atom_dual_table_is_exhaustively_witnessed():
    """The `_ATOM_DUALS` table, walked ROW BY ROW rather than sampled: for each
    row the dual really is the negation, checked over a grid in the evaluator
    and over the free domain by both solvers.  A row added to the table without
    a proof lands here, not in production."""
    objects = {"a": "Int", "b": "Int"}
    for op in sorted(_ATOM_DUALS):
        atom = ({"op": op, "args": [_A, _B]} if op in ("=", "!=", "<=", "<")
                else {"op": op, "args": [_A]})
        identity = _iff(_not(atom), _dual_atom(atom))
        for av in range(-3, 4):
            for bv in range(-3, 4):
                asg = {"a": av, "b": bv}
                assert eval_pred(identity, asg, objects, None) is True, \
                    f"{op}: dual fails at {asg}"
        z, c = _dual(_symbolic_valid(identity, objects, "Int"), "unsat")
        assert z == "pass", f"{op}: z3 {z}"
        assert c in ("pass", "unknown", "error"), f"{op}: cvc5 {c}"


# ==================================================== the planted-lossy tooth
def test_lossy_demorgan_flip_gets_no_certificate():
    """THE PLANTED-LOSSY TOOTH: a negation push that forgets to FLIP the
    connective, and one that forgets to SWAP the order atom's arguments.

    Both lossy forms are produced honestly -- they are preds this fragment
    admits, which is exactly what makes them dangerous: nothing downstream
    would refuse them on shape, so only a differential can catch them.  Each is
    refused two ways: the symbolic obligation that the honest and lossy forms
    are the same claim comes back `sat` (a divergence point exists) where the
    honest identity comes back `unsat`, and the EVALUATOR names the point, so
    neither verdict is an artefact of the encoding.  This is what makes the De
    Morgan flip and the argument swap load-bearing rather than decorative."""
    objects = {"a": "Int", "b": "Int"}

    # (1) the connective flip.  honest: not(P and Q) == (not P) or (not Q).
    honest = _or(_not(_P), _not(_Q))
    lossy = _and(_not(_P), _not(_Q))
    source = _not(_and(_P, _Q))
    z, _ = _dual(_symbolic_valid(_iff(source, honest), objects, "Int"), "unsat")
    assert z == "pass", f"the honest push must be valid, z3 said {z}"
    z, c = _dual(_symbolic_valid(_iff(source, lossy), objects, "Int"), "unsat")
    assert z == "fail", f"the unflipped push must be refused, z3 said {z}"
    assert c in ("fail", "error"), f"unflipped push, cvc5 said {c}"
    z, c = _dual(_distinct_preds(source, lossy, objects, "Int"), "sat")
    assert z == "pass", f"a divergence point must exist, z3 said {z}"
    assert c in ("pass", "unknown", "error"), f"divergence, cvc5 said {c}"
    witnesses = [(av, bv) for av in range(-3, 4) for bv in range(-3, 4)
                 if eval_pred(source, {"a": av, "b": bv}, objects, None)
                 is not eval_pred(lossy, {"a": av, "b": bv}, objects, None)]
    assert witnesses, "eval found no divergence point for the unflipped push"

    # (2) the argument swap.  honest: not(a <= b) == b < a.
    atom = _le(_A, _B)
    honest_dual = _lt(_B, _A)
    lossy_dual = _lt(_A, _B)
    z, _ = _dual(_symbolic_valid(_iff(_not(atom), honest_dual), objects, "Int"),
                 "unsat")
    assert z == "pass", f"the honest dual must be valid, z3 said {z}"
    z, c = _dual(_symbolic_valid(_iff(_not(atom), lossy_dual), objects, "Int"),
                 "unsat")
    assert z == "fail", f"the unswapped dual must be refused, z3 said {z}"
    assert c in ("fail", "error"), f"unswapped dual, cvc5 said {c}"
    swap_witnesses = [
        (av, bv) for av in range(-3, 4) for bv in range(-3, 4)
        if eval_pred(_not(atom), {"a": av, "b": bv}, objects, None)
        is not eval_pred(lossy_dual, {"a": av, "b": bv}, objects, None)]
    assert swap_witnesses, "eval found no divergence point for the unswapped dual"


def test_iff_desugaring_is_the_same_claim_as_a_bool_equality():
    """The SMT mirror renders `iff` as the DESUGARED conjunction rather than as
    SMT-LIB's Bool-sorted `(= p q)`.  That is a shape choice, and this pins it
    as ONLY a shape choice: the two renderings are the same formula.  Pinning
    it is what lets the comment at the rendering site claim what it claims."""
    objects = {"a": "Int", "b": "Int"}
    pred = _iff(_P, _Q)
    desugared = math_smt.render_pred(pred, objects, "Int")
    assert desugared.startswith("(and (=> "), desugared
    p = math_smt.render_pred(_P, objects, "Int")
    q = math_smt.render_pred(_Q, objects, "Int")
    lines = ["(set-logic QF_NIA)",
             "(declare-const a Int)", "(declare-const b Int)",
             f"(assert (xor {desugared} (= {p} {q})))",
             "(check-sat)"]
    z, c = _dual("\n".join(lines) + "\n", "unsat")
    assert z == "pass", f"the two iff renderings must agree, z3 said {z}"
    assert c in ("pass", "unknown", "error"), f"iff renderings, cvc5 said {c}"


# ============================================== no new sort, no new logic
def test_connectives_do_not_move_the_declared_logic():
    """The declared logic is a function of the ARITHMETIC; connectives are
    transparent to `_pred_nonlinear` and must stay so.  A purchase that
    silently escalated QF_LIA to QF_NIA would be spending a budget nobody
    billed -- and the declared logic is not advisory, CVC5's parser enforces
    it."""
    objects = {"a": "Int", "b": "Int"}
    linear = _le(_A, _B)
    nonlinear = _eq({"op": "*", "args": [_A, _B]}, _lit(6))
    concl = _eq(_A, _B)

    def logic(hyp):                 # the declared logic reads the HYPOTHESES
        return math_smt._logic(_parse(objects, concl, hyps=[hyp]))

    assert logic(linear) == "QF_LIA"
    assert logic(_not(linear)) == "QF_LIA"
    assert logic(_iff(linear, _not(linear))) == "QF_LIA"
    # and a nonlinear atom is still seen THROUGH the new connectives.
    assert logic(nonlinear) == "QF_NIA"
    assert logic(_not(nonlinear)) == "QF_NIA"
    assert logic(_iff(linear, nonlinear)) == "QF_NIA"


# ====================================================== the gate refusal surface
def test_negated_dual_less_atom_is_a_fragment_miss():
    """The battery-side statement of the gate's named limit (the gate-side
    tooth lives in tests/test_math_reading.py, where the refusal is decided).
    `dvd` and `coprime` have no dual, so a negation reaching one cannot be
    pushed to an atom and the fragment carries no node to leave it at."""
    objects = {"a": "Nat", "b": "Nat"}
    for pred, want in ((_not(_dvd(_A, _B)), "not:dvd-no-dual"),
                       (_not({"op": "coprime", "args": [_A, _B]}),
                        "not:coprime-no-dual")):
        with pytest.raises(FragmentMiss) as ei:
            _parse(objects, pred)
        assert ei.value.missing_kind_guess == want
    # a POSITIVE dvd under an implication or a biconditional is untouched --
    # `pimp` is a constructor, so nothing pushes through it.
    _parse(objects, _imp(_dvd(_A, _B), _le(_A, _B)))
    _parse(objects, _iff(_dvd(_A, _B), _le(_A, _B)))


def test_connective_arities_refuse_as_malformations():
    """A wrong width is a malformation, not demand data: `not` is unary and
    `iff` binary, and neither is a missing primitive at any other width."""
    objects = {"a": "Int", "b": "Int"}
    for pred in ({"op": "not", "args": [_P, _Q]},
                 {"op": "not", "args": []},
                 {"op": "iff", "args": [_P]},
                 {"op": "iff", "args": [_P, _Q, _P]}):
        with pytest.raises(BadMathReading) as ei:
            _parse(objects, pred)
        assert not isinstance(ei.value, FragmentMiss)


def test_every_pre_p6_refusal_still_refuses():
    """The purchase did not widen anything on its way past.  Each row is a
    refusal that predates P6, re-run against the grown grammar; the point is
    not that these shapes are interesting but that the connective purchase can
    be SEEN not to have touched them."""
    objects = {"a": "Int", "b": "Int"}
    # a symbolic big-operator bound (P1's freeze)
    with pytest.raises(FragmentMiss) as ei:
        _parse(objects, _eq({"op": "bigsum", "args": [
            {"var": "i"}, {"lit": 0}, _ref("b"), _ref("i")]}, _lit(0)))
    assert ei.value.missing_kind_guess == "bigop:symbolic-bound"
    # `/` outside Rat (P3's freeze)
    with pytest.raises(FragmentMiss) as ei:
        _parse(objects, _eq({"op": "/", "args": [_A, _lit(2)]}, _lit(1)))
    assert ei.value.missing_kind_guess == "operator:/@Int"
    # an order atom at a residue carrier (P4's freeze)
    with pytest.raises(FragmentMiss) as ei:
        _parse({"a": "ZMod 5"}, _le(_A, _lit(2)))
    assert ei.value.missing_kind_guess == "operator:<=@ZMod 5"
    # a variable exponent (D10) and an unknown atom stay malformations
    with pytest.raises(BadMathReading):
        _parse(objects, _eq({"op": "^", "args": [_A, _B]}, _lit(1)))
    with pytest.raises(BadMathReading):
        _parse(objects, {"op": "nand", "args": [_P, _Q]})


def test_the_new_words_are_admissible_at_a_residue_carrier():
    """`ZMod n` admits `=` and `!=` only, and they are each other's dual, so
    the connectives ride in without a single new refusal -- the smallest
    possible statement of what "additive" means here."""
    reading = _parse({"a": "ZMod 5"},
                     _iff(_not(_eq(_A, _lit(2))), _ne(_A, _lit(2))))
    assert reading.objects() == {"a": "ZMod 5"}
    for av in range(5):
        assert eval_pred(_not(_eq(_A, _lit(7))), {"a": av},
                         {"a": "ZMod 5"}, None) is (av != 2)


# ============================================ Lean rendering + escape gate + hash
def test_lean_rendering_rides_the_escape_gate():
    """`¬` and `↔` are Sm-class MATH SYMBOLS, not word characters, so T7's
    non-ASCII IDENTIFIER rule does not reach them -- exactly as it does not
    reach `∧ ∨ → ≤ ≠ ∣`.  VERIFIED here rather than assumed: the prefix forms
    `Not` / `Iff` were the fallback and are not needed."""
    objects = {"a": "Int", "b": "Int"}
    reading = _parse(objects, _iff(_not(_le(_A, _B)), _lt(_B, _A)))
    art = compile_math_reading(reading)
    text = art["lean_text"]
    assert "¬" in text and "↔" in text, text
    ok, why = validate_lean(text)
    assert ok, f"escape gate refused the connective rendering: {why}"
    # byte-stability: compiling twice is the same artifact, hash included.
    again = compile_math_reading(_parse(objects,
                                        _iff(_not(_le(_A, _B)), _lt(_B, _A))))
    assert again["lean_text"] == text
    assert again["statement_hash"] == art["statement_hash"]


def test_end_to_end_gate_eval_compile_escape():
    """One reading through the whole Lean-free pipeline: the gate admits it,
    the evaluator decides it pointwise in agreement with the oracle, the SMT
    mirror renders it, the compiler emits it and the escape gate passes it."""
    objects = {"a": "Nat", "b": "Nat"}
    concl = _iff(_not(_lt(_A, _B)), _le(_B, _A))
    reading = _parse(objects, concl, hyps=[_not(_eq(_A, _B))])
    for av in range(0, 5):
        for bv in range(0, 5):
            asg = {"a": av, "b": bv}
            assert eval_pred(concl, asg, objects, None) is _truth(concl, asg)
    assert math_smt.render_pred(concl, objects, "Nat").startswith("(and (=> ")
    ok, why = validate_lean(compile_math_reading(reading)["lean_text"])
    assert ok, why


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))

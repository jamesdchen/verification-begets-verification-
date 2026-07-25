"""P4 admission batteries: the concrete finite carrier ZMod n.

The PLAN_FRAGMENT §4 bill, applied to the first PARAMETRIC carrier: a ZMod n
reading is arithmetic over the integers read through its residue class, and the
whole admissibility argument is that n is a NON-ZERO LITERAL -- the same
literal-makes-it-exact move that carries P1's bounds and D10's exponent.
LLM-free, Lean-free teeth that would fail if the carrier's semantics regressed
in ANY of the four translations (gate / eval / SMT mirror / Lean text), in the
operator-growth battery discipline:

  * (b-analogue) DIFFERENTIAL VALUE battery: over planted residue equations
    (wrapping sums, products, a NEGATIVE difference, a literal above the
    modulus, a `^` unroll), ``math_eval.eval_pred``'s verdict is corroborated
    by an independent Python residue oracle AND by the ground SMT differential
    on z3 and cvc5 (dual-solver agreement; absent cvc5 degrades honestly).
    Both directions carry teeth: a true row must be ``sat``, a false row
    ``unsat``.
  * (b2-analogue) SYMBOLIC battery: the residue param stays FREE over
    0..n-1 (never pinned) and the atom's NEGATION is asserted; a dual-solver
    ``unsat`` is all-residues agreement.  A deliberately false identity must
    come back ``sat`` -- the battery can fail.
  * LOSSY MOD DROP GETS NO CERTIFICATE: render the same atom WITHOUT the mod
    wrap (the Int rendering) and both halves of the differential must refuse --
    the ground obligation flips sat to unsat on a planted wrapping case, the
    symbolic one flips unsat to sat on a planted identity -- with the evaluator
    witnessing each divergence pointwise.  The divergence tooth that proves the
    wrap is load-bearing rather than decorative.
  * D8-CLASS CARRIER DIVERGENCE: the ZMod and Int readings of one atom are
    xor'd over the SHARED residue domain (``sat`` = a divergence point
    exists), corroborated by an eval-witnessed point -- the direction-split
    discipline of ``operator_growth._carrier_stability_obligation``.
  * COMPLETE DECISION: the domain sweep of a pure-ZMod reading IS the whole
    carrier (range(0, n)), so the bounded shadow stops being bounded evidence
    and becomes a decision -- pinned as box size, box contents, and
    bound-independence.
  * The gate's refusal surface (symbolic modulus / zero modulus / order and
    mod-family operators / mixed moduli / a binder index inside a ZMod
    reading) is pinned as demand data, the SMT logic classification is pinned,
    the reflect congruence image and each of its NAMED edges are pinned, and
    the Lean rendering + escape gate + hash byte-stability are pinned.

The residue conventions agree three ways at a POSITIVE literal modulus and the
teeth lean on that: Python's `%`, Lean's `Int.emod` and SMT-LIB's Euclidean
`mod` all return the non-negative representative, so `2 - 4` reads as 3 over
ZMod 5 in every channel (the negative-difference row is exactly that check).

Named limits this file pins as limits, not as gaps (spec-p4's v1 freeze):
a LITERAL modulus only (`carrier:zmod-symbolic-modulus`) and n >= 1
(`carrier:zmod-zero-modulus`); no order and no divisibility family at a residue
carrier, by construction rather than by omission; no binder inside a residue
reading (`zmod:binder-index-carrier`, the index is pinned Nat); one modulus per
reading, never mixed; a non-canonical spelling of the type text keeps the
generic `carrier:<ty>` miss rather than being normalized into the family; the
reflect image's own edges (`zmod:negated-congruence`,
`zmod:atom-out-of-image:<op>`, and `carrier-out-of-reflect-slice:ZMod <n>` on
the box-sweep route, whose Int box is not a residue reading's honest box); and
`zmod:carrier-type` -- the Lean rendering is
TEXT-LEVEL, because ZMod is not reachable at the pinned import whitelist, the
same state P2's Finset.card rendering started in.  Widening that pin is cert
identity surgery, so it is future work with a name, not a line in this bill.
"""
import json

import pytest

from generators.math_reading import (
    parse_math_reading, BadMathReading, FragmentMiss, CARRIERS, _zmod_modulus)
from generators.math_eval import (
    eval_pred, conclusion_holds, enumerate_domain, _box_size)
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


def _mul(*a):
    return {"op": "*", "args": list(a)}


def _sub(a, b):
    return {"op": "-", "args": [a, b]}


def _pow(a, k):
    return {"op": "^", "args": [a, _lit(k)]}


def _eq(a, b):
    return {"op": "=", "args": [a, b]}


def _ne(a, b):
    return {"op": "!=", "args": [a, b]}


def _le(a, b):
    return {"op": "<=", "args": [a, b]}


def _dvd(a, b):
    return {"op": "dvd", "args": [a, b]}


def _mod(a, b):
    return {"op": "%", "args": [a, b]}


def _bigsum(var, lo, hi, body):
    return {"op": "bigsum",
            "args": [{"var": var}, _lit(lo), _lit(hi), body]}


# ------------------------------------------------------------ reading builder
def _doc(objects, ambient, concl, hyps=()):
    """A minimal gate-legal reading: the ambient choice, one object per entry, a
    ∀ quantifier over them, the presupposed hypotheses and the demanded
    conclusion.  The SOURCE is synthesized from the quotes, so groundedness
    holds by construction (these teeth are about the carrier, not the quote
    gate)."""
    stmts = []
    if ambient is not None:
        stmts.append({"id": "amb", "force": "choice", "quote": "",
                      "lf": {"kind": "ambient", "carrier": ambient}})
    for name in sorted(objects):
        stmts.append({"id": f"obj_{name}", "force": "demand",
                      "quote": f"the residue {name} of type {objects[name]}",
                      "lf": {"kind": "object", "name": name,
                             "type": objects[name]}})
    if objects:
        stmts.append({"id": "qf", "force": "demand",
                      "quote": "for every residue named above",
                      "lf": {"kind": "quantifier", "binder": "forall",
                             "objects": sorted(objects)}})
    for i, h in enumerate(hyps):
        stmts.append({"id": f"hyp{i}", "force": "presupposition",
                      "quote": f"the side condition number {i}",
                      "lf": {"kind": "hypothesis", "pred": h}})
    stmts.append({"id": "concl", "force": "demand",
                  "quote": "the asserted congruence",
                  "lf": {"kind": "conclusion", "pred": concl}})
    src = " ".join(s["quote"] for s in stmts if s["quote"])
    return json.dumps({"theorem": "zmod_battery", "statements": stmts}), src


def _parse(objects, ambient, concl, hyps=()):
    doc, src = _doc(objects, ambient, concl, hyps)
    return parse_math_reading(doc, src)


# ------------------------------------------------------- independent oracle
def _int_value(term, assignment):
    """Evaluate a term over the INTEGERS, in plain Python, independently of
    math_eval -- the residue reduction is applied by the caller, at the atom,
    exactly where the design freeze puts it."""
    if "lit" in term:
        return term["lit"]
    if "ref" in term:
        return assignment[term["ref"]]
    op, args = term["op"], term["args"]
    if op == "+":
        total = 0
        for a in args:
            total += _int_value(a, assignment)
        return total
    if op == "*":
        prod = 1
        for a in args:
            prod *= _int_value(a, assignment)
        return prod
    if op == "-":
        return _int_value(args[0], assignment) - _int_value(args[1], assignment)
    if op == "^":
        return _int_value(args[0], assignment) ** args[1]["lit"]
    raise AssertionError(f"oracle: unexpected term op {op!r}")


def _residue_truth(pred, n, assignment=None):
    """The oracle verdict for a =/!= atom over ZMod n: reduce both sides."""
    a = assignment or {}
    lhs = _int_value(pred["args"][0], a) % n
    rhs = _int_value(pred["args"][1], a) % n
    return lhs == rhs if pred["op"] == "=" else lhs != rhs


# ---------------------------------------------------------- SMT obligations
def _declare(name, ty):
    lines = [f"(declare-const {name} Int)"]
    n = _zmod_modulus(ty)
    if n is not None:                       # the residue domain, as a range
        lines.append(f"(assert (and (<= 0 {name}) (< {name} {n})))")
    elif ty == "Nat":
        lines.append(f"(assert (>= {name} 0))")
    return lines


def _ground_pred(pred, objects, carrier, assignment):
    """Pin every object inside its residue range and assert the atom: ``sat``
    iff the solvers' arithmetic agrees the atom HOLDS there (the
    _ground_term_smt discipline, lifted to a predicate so the mod wrap -- which
    lives at the atom -- is inside the obligation)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.extend(_declare(name, objects[name]))
        lines.append(
            f"(assert (= {name} {math_smt._render_lit(assignment[name])}))")
    lines.append(f"(assert {math_smt.render_pred(pred, objects, carrier)})")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _symbolic_valid(pred, objects, carrier):
    """Params FREE over their residue range, assert the atom's NEGATION: unsat
    = the atom holds at EVERY residue (the b2 shape for a predicate)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.extend(_declare(name, objects[name]))
    lines.append(f"(assert (not {math_smt.render_pred(pred, objects, carrier)}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _carrier_xor(pred, name, n):
    """The cross-carrier divergence obligation over the SHARED domain (the
    residues 0..n-1): the ZMod rendering xor the Int rendering of ONE atom.
    ``unsat`` would prove the mod wrap changes nothing; ``sat`` says a
    divergence point exists -- corroborated by eval, never load-bearing alone
    (operator_growth._carrier_stability_obligation's discipline)."""
    zmod, integer = f"ZMod {n}", "Int"
    lines = ["(set-logic QF_NIA)",
             f"(declare-const {name} Int)",
             f"(assert (and (<= 0 {name}) (< {name} {n})))",
             "(assert (xor "
             f"{math_smt.render_pred(pred, {name: zmod}, zmod)} "
             f"{math_smt.render_pred(pred, {name: integer}, integer)}))",
             "(check-sat)"]
    return "\n".join(lines) + "\n"


# ================================================= (b) differential value battery
# Planted residue equations, all ground: the wrapping cases the carrier exists
# to get right.  `expected` is stated by hand AND recomputed by the oracle, so a
# typo in either one is caught.
_PLANTED = [
    # (label, modulus, pred, expected)
    ("add_wraps", 5, _eq(_add(_lit(3), _lit(4)), _lit(2)), True),
    ("mul_wraps", 5, _eq(_mul(_lit(3), _lit(4)), _lit(2)), True),
    # the negative difference: `-` over ZMod is REAL subtraction (never Nat
    # truncation) and the atom's reduction brings it back into 0..n-1.
    ("sub_wraps_negative", 5, _eq(_sub(_lit(2), _lit(4)), _lit(3)), True),
    ("pow_wraps", 5, _eq(_pow(_lit(2), 3), _lit(3)), True),
    ("literal_above_modulus", 5, _eq(_lit(7), _lit(2)), True),
    ("chain_sub_add", 5, _eq(_add(_sub(_lit(1), _lit(3)), _lit(4)), _lit(2)),
     True),
    ("ne_holds", 5, _ne(_add(_lit(3), _lit(4)), _lit(1)), True),
    # both directions carry teeth: a FALSE row must come back unsat.
    ("eq_fails", 5, _eq(_add(_lit(3), _lit(4)), _lit(3)), False),
    # a second modulus, so nothing can hard-code 5.
    ("parity_zmod2", 2, _eq(_add(_lit(3), _lit(1)), _lit(0)), True),
    ("odd_residue_zmod2", 2, _eq(_mul(_lit(3), _lit(5)), _lit(1)), True),
]


@pytest.mark.parametrize("label,n,pred,expected", _PLANTED,
                         ids=[p[0] for p in _PLANTED])
def test_value_battery_eval_agrees_with_dual_solver(label, n, pred, expected):
    carrier = f"ZMod {n}"
    assert _residue_truth(pred, n) is expected, f"{label}: oracle disagrees"
    v = eval_pred(pred, {}, {}, carrier)
    assert bool(v) is expected, f"{label}: evaluator says {v}"
    want = "sat" if expected else "unsat"
    z, c = _dual(_ground_pred(pred, {}, carrier, {}), want)
    assert z == "pass", f"{label}: z3 {z}"
    assert c in ("pass", "unknown", "error"), f"{label}: cvc5 {c}"


def test_value_battery_over_a_free_residue_object():
    """The same differential with an OBJECT in the atom, pinned at each residue:
    x + 5 reads as x over ZMod 5, at every point of the (complete) domain."""
    carrier, objects = "ZMod 5", {"x": "ZMod 5"}
    pred = _eq(_add(_ref("x"), _lit(5)), _ref("x"))
    for xv in range(5):
        a = {"x": xv}
        assert _residue_truth(pred, 5, a) is True
        assert eval_pred(pred, a, objects, carrier)
        z, c = _dual(_ground_pred(pred, objects, carrier, a), "sat")
        assert z == "pass", f"x={xv}: z3 {z}"
        assert c in ("pass", "unknown", "error"), f"x={xv}: cvc5 {c}"


def test_lossy_mod_drop_gets_no_certificate():
    """THE PLANTED-LOSSY TOOTH: dropping the atom's mod wrap is not a
    simplification, it silently re-states the theorem over the integers.

    The lossy rendering is produced honestly -- the SAME AST rendered at an Int
    carrier, which is exactly what a wrap-less residue mirror would emit -- and
    the differential refuses it three ways: on a planted GROUND wrapping case
    the obligation flips from sat to unsat (no certificate is available for the
    residue claim); on the planted IDENTITY the symbolic obligation flips the
    other way, from unsat to sat (a counterexample exists); and the evaluator
    witnesses both divergences pointwise, so neither solver verdict is an
    artefact of the encoding.  This is what makes the wrap load-bearing rather
    than decorative."""
    ground = _eq(_sub(_lit(2), _lit(4)), _lit(3))   # 3 over ZMod 5, -2 over Int
    assert eval_pred(ground, {}, {}, "ZMod 5")
    assert not eval_pred(ground, {}, {}, "Int")
    z, c = _dual(_ground_pred(ground, {}, "ZMod 5", {}), "sat")
    assert z == "pass", f"the honest rendering must be sat, z3 said {z}"
    z, c = _dual(_ground_pred(ground, {}, "Int", {}), "sat")
    assert z == "fail", f"the un-wrapped rendering must be refused, z3 said {z}"
    assert c in ("fail", "error"), f"un-wrapped rendering, cvc5 said {c}"
    # the symbolic half of the same tooth: `x + 5 = x` is a residue identity at
    # every one of the five points, and false at every one of them over Z.
    identity = _eq(_add(_ref("x"), _lit(5)), _ref("x"))
    faithful = math_smt.render_pred(identity, {"x": "ZMod 5"}, "ZMod 5")
    lossy = math_smt.render_pred(identity, {"x": "Int"}, "Int")
    assert "mod" in faithful and "mod" not in lossy
    zf, cf = _dual(_symbolic_valid(identity, {"x": "ZMod 5"}, "ZMod 5"), "unsat")
    assert zf == "pass" and cf in ("pass", "unknown", "error")
    zl, cl = _dual(_symbolic_valid(identity, {"x": "Int"}, "Int"), "unsat")
    assert zl == "fail", f"the lossy identity must not certify, z3 said {zl}"
    assert cl in ("fail", "error"), f"lossy identity, cvc5 said {cl}"
    for v in range(5):
        assert eval_pred(identity, {"x": v}, {"x": "ZMod 5"}, "ZMod 5") is True
        assert eval_pred(identity, {"x": v}, {"x": "Int"}, "Int") is False


def test_mod_wrap_is_lexically_present_at_zmod_atoms():
    """The wrap is emitted at the ATOM (both sides), and only for ZMod: the Int
    rendering of the same atom carries no residue reduction at all."""
    pred = _eq(_add(_ref("x"), _lit(5)), _ref("x"))
    at_zmod = math_smt.render_pred(pred, {"x": "ZMod 5"}, "ZMod 5")
    at_int = math_smt.render_pred(pred, {"x": "Int"}, "Int")
    assert "(mod " in at_zmod
    assert "(mod " not in at_int
    assert at_zmod != at_int


# ================================================ D8-class carrier divergence
def test_zmod_and_int_readings_diverge_and_the_point_is_witnessed():
    """One atom, two carriers, the SHARED residue domain: the solver says a
    divergence point exists and the enumeration NAMES it.  A solver existence
    claim is never load-bearing on its own (the direction-split rule); the
    eval-witnessed point is what makes this evidence."""
    pred = _eq(_sub(_ref("x"), _lit(4)), _lit(3))
    witness = None
    for xv in range(5):
        at_zmod = bool(eval_pred(pred, {"x": xv}, {"x": "ZMod 5"}, "ZMod 5"))
        at_int = bool(eval_pred(pred, {"x": xv}, {"x": "Int"}, "Int"))
        if at_zmod != at_int:
            witness = {"x": xv, "zmod": at_zmod, "int": at_int}
            break
    # x = 2: 2 - 4 = -2 reads as 3 over ZMod 5, and is plainly not 3 over Int.
    assert witness == {"x": 2, "zmod": True, "int": False}, witness
    z, c = _dual(_carrier_xor(pred, "x", 5), "sat")
    assert z == "pass", f"the carriers must be able to disagree, z3 said {z}"
    assert c in ("pass", "unknown", "error"), f"cvc5 {c}"


# ======================================================== (b2) symbolic battery
def test_symbolic_battery_adding_the_modulus_changes_nothing():
    # x + 5 = x for ALL residues x (free param over 0..4, never pinned).
    pred = _eq(_add(_ref("x"), _lit(5)), _ref("x"))
    z, c = _dual(_symbolic_valid(pred, {"x": "ZMod 5"}, "ZMod 5"), "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


def test_symbolic_battery_pow_unroll_matches_the_product():
    # x^2 = x*x for ALL residues: the D10 unroll survives the residue wrap.
    pred = _eq(_pow(_ref("x"), 2), _mul(_ref("x"), _ref("x")))
    z, c = _dual(_symbolic_valid(pred, {"x": "ZMod 5"}, "ZMod 5"), "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


def test_symbolic_battery_refuses_a_false_identity():
    """The battery can fail: idempotence is NOT a residue identity (x = 2 is a
    counterexample over ZMod 5), so the negation must be satisfiable."""
    pred = _eq(_mul(_ref("x"), _ref("x")), _ref("x"))
    assert not eval_pred(pred, {"x": 2}, {"x": "ZMod 5"}, "ZMod 5")
    z, c = _dual(_symbolic_valid(pred, {"x": "ZMod 5"}, "ZMod 5"), "sat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


# ==================================================== gate refusals (demand data)
# The REGISTRY teeth for the modulus freeze live at the gate that decides them
# (`tests/test_math_reading.py::test_symbolic_modulus_is_a_fragment_miss` and
# its siblings).  The rows below are the battery's own, in the `rat-carrier`
# pattern: they carry what the gate teeth do not -- the resolution path with no
# ambient, the NON-CANONICAL modulus spellings, and the miner-facing
# consequence -- so deleting either half leaves the other visibly short.
def test_zmod_is_a_parametric_family_not_a_carriers_row():
    """The carrier whitelist stays a tuple of BARE strings; ZMod is admitted by
    a predicate over the literal modulus, so no CARRIERS row can drift."""
    assert "ZMod 5" not in CARRIERS
    assert _zmod_modulus("ZMod 5") == 5
    assert _zmod_modulus("ZMod 1") == 1
    assert _zmod_modulus("Int") is None
    assert _zmod_modulus("ZMod n") is None          # symbolic modulus
    assert _zmod_modulus("ZMod 0") is None          # the zero ring
    assert _zmod_modulus("ZMod  5") is None         # the exact Lean type text
    assert _zmod_modulus("ZMod 007") is None        # no leading zeros


def test_modulus_freeze_refuses_symbolic_zero_and_non_canonical():
    """The named demand this purchase does NOT buy: a modulus that is an object
    rather than a literal.  Symbolic bounds were P1's named future purchase and
    a symbolic modulus is the same shape -- refused in writing, ranked by F4.

    The third clause is this battery's own: a NON-CANONICAL spelling of a
    perfectly finite modulus ("ZMod 07", "ZMod -1", the two-space form) is NOT
    given the residue signals.  It falls to the generic `carrier:<ty>` miss, and
    deliberately: the carrier string is the exact Lean type TEXT that binders
    emit verbatim, so admitting a second spelling would put two strings on one
    carrier and hand the mirrors two names for one thing.  Naming the limit is
    the honest move; normalizing the text would be a silent widening."""
    concl = _eq(_ref("x"), _ref("x"))
    with pytest.raises(FragmentMiss) as e:
        _parse({"x": "ZMod n"}, None, concl)
    assert e.value.missing_kind_guess == "carrier:zmod-symbolic-modulus"
    # ...and as the ambient, where formalization freedom would hide it
    with pytest.raises(FragmentMiss) as e2:
        _parse({}, "ZMod n", _eq(_lit(1), _lit(1)))
    assert e2.value.missing_kind_guess == "carrier:zmod-symbolic-modulus"
    # the zero ring is its own refusal (n >= 1 by the design freeze)
    with pytest.raises(FragmentMiss) as e3:
        _parse({"x": "ZMod 0"}, None, concl)
    assert e3.value.missing_kind_guess == "carrier:zmod-zero-modulus"
    # everything else -- including a non-canonical modulus spelling -- stays the
    # generic carrier miss, so no reading is priced as residue demand it is not.
    for ty in ("Zmod 5", "ZMod 07", "ZMod -1", "ZMod  5", "ZMod"):
        with pytest.raises(FragmentMiss) as e4:
            _parse({"x": ty}, None, concl)
        assert e4.value.missing_kind_guess == f"carrier:{ty}", ty


def test_order_and_mod_family_operators_refuse_at_zmod():
    """There is no order on ZMod n and no remainder either: <= < % mod dvd gcd
    coprime even odd are refused BY CONSTRUCTION, not merely unimplemented.
    Admitting them would be an untruth the compiler would happily render."""
    for pred, op in ((_le(_ref("x"), _lit(2)), "<="),
                     ({"op": "<", "args": [_ref("x"), _lit(2)]}, "<"),
                     (_eq(_mod(_ref("x"), _lit(2)), _lit(0)), "%"),
                     (_dvd(_lit(2), _ref("x")), "dvd"),
                     ({"op": "even", "args": [_ref("x")]}, "even")):
        with pytest.raises(FragmentMiss) as e:
            _parse({"x": "ZMod 5"}, "ZMod 5", pred)
        assert e.value.missing_kind_guess == f"operator:{op}@ZMod 5", op


def test_mixed_moduli_and_integer_carriers_refuse():
    """Two moduli are two DIFFERENT carriers (the strings differ), so the walk
    refuses them in one reading exactly as it refuses a mixed-carrier `-`, and
    an ambient does not rescue the mix: there is no ambient that makes a residue
    class and an integer the same kind of thing.  The rule is READING-wide, not
    per-pred, because both mirrors resolve the modulus from the object map."""
    mix = _eq(_add(_ref("x"), _ref("y")), _lit(0))
    for other in ("ZMod 7", "Int", "Nat", "Rat"):
        with pytest.raises(BadMathReading):
            _parse({"x": "ZMod 5", "y": other}, None, mix)
        with pytest.raises(BadMathReading):
            _parse({"x": "ZMod 5", "y": other}, "ZMod 5", mix)
    # the single-carrier readings of the same shape are untouched
    _parse({"x": "ZMod 5", "y": "ZMod 5"}, "ZMod 5", mix)
    _parse({"x": "Nat", "y": "Int"}, "Int", mix)


def test_binder_index_carrier_refuses_inside_a_zmod_reading():
    """The index of a bounded fold or a set-builder is pinned at Nat; a ZMod
    reading has no Nat to pin it to, so the binding classes are refused here
    rather than silently read at the wrong carrier."""
    with pytest.raises(FragmentMiss) as e:
        _parse({"x": "ZMod 5"}, "ZMod 5",
               _eq(_bigsum("i", 1, 3, _ref("i")), _ref("x")))
    assert e.value.missing_kind_guess == "zmod:binder-index-carrier"


def test_admissible_operators_parse_at_zmod():
    """The positive control: + * - ^ = != are the whole admitted vocabulary,
    and all of them pass the gate at a literal modulus."""
    concl = _ne(_add(_mul(_ref("x"), _lit(2)),
                     _sub(_pow(_ref("x"), 2), _lit(1))), _lit(4))
    r = _parse({"x": "ZMod 5"}, "ZMod 5", concl)
    assert r.objects() == {"x": "ZMod 5"}
    assert r.ambient_carrier() == "ZMod 5"


# ==================================================== SMT logic classification
def test_logic_classification_rides_the_int_machinery():
    """The congruence image is an Int statement: the residue wrap is a `mod` by
    a LITERAL, which stays linear, so a linear ZMod reading classifies QF_LIA
    and only genuine nonlinearity (a product of two objects, a `^` of an
    object) pushes it to QF_NIA -- the same rule as every other carrier."""
    linear = _eq(_add(_ref("x"), _lit(5)), _ref("x"))
    nonlinear = _eq(_mul(_ref("x"), _ref("y")), _lit(1))
    assert not math_smt._pred_nonlinear(linear)
    assert math_smt._pred_nonlinear(nonlinear)
    lin_reading = _parse({"x": "ZMod 5"}, "ZMod 5",
                         _eq(_ref("x"), _ref("x")), hyps=[linear])
    assert math_smt._logic(lin_reading) == "QF_LIA"
    non_reading = _parse({"x": "ZMod 5", "y": "ZMod 5"}, "ZMod 5",
                         _eq(_ref("x"), _ref("x")), hyps=[nonlinear])
    assert math_smt._logic(non_reading) == "QF_NIA"


# ================================================ the complete-decision capability
def test_zmod_sweep_is_a_complete_decision_not_a_bounded_one():
    """What this purchase actually BUYS: the domain sweep of a pure-ZMod
    reading is the WHOLE carrier, so a green sweep is a decision, not bounded
    evidence.  Pinned three ways -- the box has exactly n points, they are the n
    residues in canonical order, and the sweep bound cannot change either."""
    concl = _eq(_pow(_ref("x"), 3), _ref("x"))     # true at every residue mod 3
    r = _parse({"x": "ZMod 3"}, "ZMod 3", concl)
    box = list(enumerate_domain(r))
    assert len(box) == 3
    assert [a["x"] for a in box] == [0, 1, 2]
    assert all(conclusion_holds(r, a) for a in box)
    # bound-independence: the range is the carrier, never the bound
    assert list(enumerate_domain(r, bound=2)) == box
    assert list(enumerate_domain(r, bound=64)) == box
    assert _box_size(["x"], {"x": "ZMod 3"}, 8) == 3
    assert _box_size(["x", "y"], {"x": "ZMod 3", "y": "ZMod 3"}, 8) == 9


# ==================================================== reflect slice (honest state)
def _exists_reading(carrier, concl=None, quote="n plus one is m"):
    """A forall-outer / exists-inner reading -- the ONE shape both reflect
    routes accept -- on a single carrier.  Built here rather than with `_doc`
    because the reflect routes need the exists binder `_doc` does not emit, and
    its conclusion is an `=` atom rather than the order atom the Rat sibling
    uses: there is no order on a residue class to write one with."""
    concl = concl if concl is not None else _eq(_add(_ref("n"), _lit(1)),
                                                _ref("m"))
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": carrier}},
        {"id": "on", "force": "demand", "quote": "the residue n",
         "lf": {"kind": "object", "name": "n", "type": carrier}},
        {"id": "om", "force": "demand", "quote": "the residue m",
         "lf": {"kind": "object", "name": "m", "type": carrier}},
        {"id": "qf", "force": "demand", "quote": "for every",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "qx", "force": "demand", "quote": "there exists",
         "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
        {"id": "c", "force": "demand", "quote": "n plus one is m",
         "lf": {"kind": "conclusion",
                "pred": _eq(_add(_ref("n"), _lit(1)), _ref("m"))}},
    ]
    src = " ".join(s["quote"] for s in stmts if s["quote"])
    return parse_math_reading(
        json.dumps({"theorem": "zmod_reflect", "statements": stmts}), src)


def test_zmod_reflect_rides_the_congruence_image_and_names_its_edges():
    """CURRENT honest state, and it is NOT a wholesale skip.

    The residue carrier gets no third FgReflect tower.  A residue `=` atom is
    quoted through its CONGRUENCE IMAGE over the PROVEN Int layer -- equality
    in `ZMod n` IS divisibility of the difference by the literal modulus
    (`FgReflect.zmodEq`) -- so the Int layer is used for exactly what it
    proves, and nothing is borrowed.  Every shape the image does not reach
    keeps a NAMED skip instead of a widening, and this row pins all three
    edges so none can quietly move:

      * `=` at a residue carrier quotes to `(zmodEq n ...)`;
      * `!=` has NO image (`Pd` carries no negation constructor, so a negated
        congruence has no shape here) and skips `zmod:negated-congruence`;
      * the LAYER CHOICE underneath is still P3's fail-close: asked the plain
        question, a residue carrier is no more one of the two proven layers
        than `Rat` is, and route 2's box sweep keeps that answer outright --
        its honest box is `range(0, n)`, not an Int box.

    The elaboration of the image is CI-lane evidence, as every Lean-side claim
    here is; what this tooth pins is the quoting decision, which is Python."""
    from run.reflect_shadow import (search_probe, quote_pred, _reflect_layer,
                                    _reflect_layer_is_nat, SliceMiss)
    # the image: an `=` atom over ZMod 5 quotes as a congruence, with the
    # modulus riding along (the image is meaningless without it)
    assert _reflect_layer({"ZMod 5"}) == (False, 5)
    quoted = quote_pred(_eq(_ref("n"), _ref("m")), {"n": 0, "m": 1}, "Int", 5)
    assert quoted == "(zmodEq 5 (Tm.tvar 0) (Tm.tvar 1))"
    # the named edge: `!=` is admissible at ZMod in the fragment and has no
    # image in `Pd`, so it skips by name rather than being encoded silently.
    with pytest.raises(SliceMiss) as e:
        quote_pred(_ne(_ref("n"), _ref("m")), {"n": 0, "m": 1}, "Int", 5)
    assert str(e.value) == "zmod:negated-congruence"
    # route 2 keeps the carrier fail-close outright
    assert search_probe(_exists_reading("ZMod 5")) == {
        "status": "skip", "reason": "carrier-out-of-reflect-slice:ZMod 5"}
    # ...and the fail-close underneath still answers by name, so the reason
    # string cannot drift while the image is being extended.
    with pytest.raises(SliceMiss) as e2:
        _reflect_layer_is_nat({"ZMod 5"})
    assert str(e2.value) == "carrier-out-of-reflect-slice:ZMod 5"
    # the integer layers are untouched: this purchase narrows nothing proven.
    assert _reflect_layer_is_nat({"Nat"}) is True
    assert _reflect_layer_is_nat({"Int"}) is False
    assert _reflect_layer({"Int"}) == (False, None)


# ============================================== end-to-end reading + Lean + hash
def test_end_to_end_gate_eval_compile_escape():
    """The binder carries the carrier string VERBATIM -- it is the Lean type
    text -- and the rendering survives the escape gate (ASCII identifiers, the
    modulus a literal).  Elaboration is deliberately NOT claimed here: ZMod
    lives behind the pinned import whitelist, a named limit
    (`zmod:carrier-type`), the same text-level state P2's Finset rendering
    started in."""
    concl = _eq(_add(_ref("x"), _lit(7)), _ref("x"))
    r = _parse({"x": "ZMod 7"}, "ZMod 7", concl)
    assert conclusion_holds(r, {"x": 3})
    art = compile_math_reading(r)
    assert "(x : ZMod 7)" in art["lean_text"]
    ok, reason = validate_lean(art["lean_text"])
    assert ok, reason
    # byte-stability: recompilation is hash-identical
    art2 = compile_math_reading(_parse({"x": "ZMod 7"}, "ZMod 7", concl))
    assert art["statement_hash"] == art2["statement_hash"]

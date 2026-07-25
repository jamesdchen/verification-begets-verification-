"""P3 admission batteries: the rational carrier Rat.

The PLAN_FRAGMENT §4 bill, applied to the first carrier whose values are not
integers: a Rat reading is exact fraction arithmetic, and the whole
admissibility argument is that division becomes TOTAL by convention (q/0 = 0,
Lean's own totalisation) rather than by a side condition nobody enforces.
LLM-free, Lean-free teeth that would fail if the carrier's semantics regressed
in ANY of the four translations (gate / eval / SMT mirror / Lean text), in the
operator-growth battery discipline:

  * (b-analogue) DIFFERENTIAL VALUE battery: over planted Rat terms (exact
    halves and thirds, a negative difference, the division totalisation at
    zero, a literal-exponent power of a fraction, a mixed `+ * - /`
    expression), ``math_eval.eval_term``'s value is corroborated by an
    independent Python `Fraction` oracle AND by the ground-equation SMT
    differential on z3 AND cvc5 (dual-solver agreement; absent cvc5 degrades
    honestly).  The order atoms carry their own rows in both directions: a true
    row must be ``sat``, a false row ``unsat``.
  * (b2-analogue) SYMBOLIC battery: the object params stay FREE over the whole
    Real line (never pinned), the term is asserted DISTINCT from an
    independently-derived closed form; a dual-solver ``unsat`` is the
    all-values agreement.  A deliberately false identity must come back
    ``sat`` -- the battery can fail.
  * LOSSY DIVISION GETS NO CERTIFICATE: drop the div-by-zero `ite` guard and
    the same obligation must flip verdict -- the divergence tooth that proves
    the totalisation is load-bearing rather than decorative.  This one is
    subtle and worth the sentence: SMT-LIB leaves `(/ x 0)` UNCONSTRAINED, so
    the guard-dropped rendering does not merely give a different answer, it
    lets a solver INVENT one.  A ground obligation would therefore still come
    back ``sat`` (measured); only the SYMBOLIC shape -- "is this term zero at
    every numerator?" -- separates the honest rendering (unsat, it is) from the
    lossy one (sat, a model exists where it is not).  The same D9 hazard the
    `%`-totalisation comment in math_smt names, in its division form.
  * D8-CLASS CARRIER STABILITY: one atom, two carriers, the SHARED domain --
    the Rat rendering XOR the Nat rendering, `sat` = a divergence point exists
    (``operator_growth._carrier_stability_obligation``'s discipline), always
    corroborated by an eval-witnessed point because a solver existence claim is
    never load-bearing alone.  An AGREEING control must come back ``unsat``, so
    the obligation is not trivially satisfiable.  Where the two carriers cannot
    even be compared -- `1/2` has no Int reading at all -- the GATE REFUSAL is
    the divergence handling, and that is pinned as its own row.
  * The gate's refusal surface (`/` outside Rat, the mod/dvd family at Rat, a
    mixed Rat/Int subtraction) is pinned as demand data, the SMT logic
    classification is pinned (and the integer classification pinned unchanged),
    the reflect-slice skip is pinned as the current honest state, and the Lean
    rendering + escape gate + hash byte-stability are pinned.

Named limits this file pins as limits, not as gaps (spec-p3's v1 freeze):
`rat:no-coercion` (a Rat/Int mix refuses, there is no coercion story this
cycle), no `%`/`mod`/`dvd`/`gcd`/`coprime`/`even`/`odd` at Rat, and the reflect
skip `carrier-out-of-reflect-slice:Rat` -- the Q tower is CI-lane future work.
"""
import json
from fractions import Fraction

import pytest

from generators.math_reading import (
    parse_math_reading, BadMathReading, FragmentMiss, CARRIERS, op_signature)
from generators.math_eval import eval_term, eval_pred, conclusion_holds
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


def _div(a, b):
    return {"op": "/", "args": [a, b]}


def _pow(a, k):
    return {"op": "^", "args": [a, _lit(k)]}


def _eq(a, b):
    return {"op": "=", "args": [a, b]}


def _ne(a, b):
    return {"op": "!=", "args": [a, b]}


def _le(a, b):
    return {"op": "<=", "args": [a, b]}


def _lt(a, b):
    return {"op": "<", "args": [a, b]}


def _mod(a, b):
    return {"op": "%", "args": [a, b]}


def _dvd(a, b):
    return {"op": "dvd", "args": [a, b]}


# A rational VALUE is a `/` of int lits -- spec-p3's v1 freeze adds no new leaf
# shape, so {"lit": k} stays integers-only and 1/2 is a term, not a literal.
def _frac(p, q):
    return _div(_lit(p), _lit(q))


# ------------------------------------------------------------ reading builder
def _doc(objects, ambient, concl, hyps=()):
    """A minimal gate-legal reading: the ambient choice, one object per entry, a
    forall quantifier over them, the presupposed hypotheses and the demanded
    conclusion.  The SOURCE is synthesized from the quotes, so groundedness
    holds by construction (these teeth are about the carrier, not the quote
    gate)."""
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
                  "quote": "the asserted relation",
                  "lf": {"kind": "conclusion", "pred": concl}})
    src = " ".join(s["quote"] for s in stmts if s["quote"])
    return json.dumps({"theorem": "rat_battery", "statements": stmts}), src


def _parse(objects, ambient, concl, hyps=()):
    doc, src = _doc(objects, ambient, concl, hyps)
    return parse_math_reading(doc, src)


# --------------------------------------------------------- independent oracle
def _rat_value(term, assignment):
    """Evaluate a term over the RATIONALS, in plain Python `Fraction`,
    independently of math_eval -- including the D9-class totalisation q/0 = 0,
    which is stated HERE as well so a regression has to break two hand-written
    statements of the convention, not one."""
    if "lit" in term:
        return Fraction(term["lit"])
    if "ref" in term:
        return Fraction(assignment[term["ref"]])
    op, args = term["op"], term["args"]
    if op == "+":
        total = Fraction(0)
        for a in args:
            total += _rat_value(a, assignment)
        return total
    if op == "*":
        prod = Fraction(1)
        for a in args:
            prod *= _rat_value(a, assignment)
        return prod
    if op == "-":                       # real subtraction: only Nat truncates
        return _rat_value(args[0], assignment) - _rat_value(args[1], assignment)
    if op == "/":
        num = _rat_value(args[0], assignment)
        den = _rat_value(args[1], assignment)
        return Fraction(0) if den == 0 else num / den
    if op == "^":
        return _rat_value(args[0], assignment) ** args[1]["lit"]
    raise AssertionError(f"oracle: unexpected term op {op!r}")


def _rat_truth(pred, assignment=None):
    """The oracle verdict for a comparison atom over Rat."""
    a = assignment or {}
    lhs = _rat_value(pred["args"][0], a)
    rhs = _rat_value(pred["args"][1], a)
    op = pred["op"]
    return {"=": lhs == rhs, "!=": lhs != rhs,
            "<=": lhs <= rhs, "<": lhs < rhs}[op]


# ----------------------------------------------------------- SMT obligations
def _real(v):
    """Render an exact rational as an SMT-LIB Real numeral, INDEPENDENTLY of
    the module under test (the differential must not be the mirror grading its
    own homework).  SMT-LIB2 has no negative numerals, so a negative value is
    `(- n)`; a non-integral value is the exact quotient `(/ p.0 q.0)` -- never a
    decimal expansion, which would silently round 1/3."""
    f = Fraction(v)
    num = f"{abs(f.numerator)}.0"
    body = num if f.denominator == 1 else f"(/ {num} {f.denominator}.0)"
    return body if f >= 0 else f"(- {body})"


def _declare(name, ty):
    """A Rat object is a Real const with NO range assertion: the carrier is the
    whole line (contrast Nat's `>= 0`), which is exactly why the symbolic
    battery below is an all-values claim."""
    if ty == "Rat":
        return [f"(declare-const {name} Real)"]
    lines = [f"(declare-const {name} Int)"]
    if ty == "Nat":
        lines.append(f"(assert (>= {name} 0))")
    return lines


def _ground_equation(term, objects, assignment, value, logic="QF_NRA"):
    """Pin every object, assert term = value: ``sat`` iff the solvers'
    arithmetic agrees with the evaluator (the _ground_term_smt discipline, over
    Real).  QF_NRA by default because a planted `/` by an object divisor is
    nonlinear and cvc5's parser enforces the declared logic strictly -- it
    errors on a variable divisor under QF_LRA (measured)."""
    lines = [f"(set-logic {logic})"]
    for name in sorted(objects):
        lines.extend(_declare(name, objects[name]))
        lines.append(f"(assert (= {name} {_real(assignment[name])}))")
    lines.append(f"(assert (= {math_smt.render_term(term, objects, 'Rat')} "
                 f"{_real(value)}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _ground_pred(pred, objects, assignment, logic="QF_NRA"):
    """The predicate sibling: pin every object and assert the ATOM.  ``sat``
    iff the solvers agree the atom holds there; a FALSE planted row asserts the
    same text and must come back ``unsat``, so both directions carry teeth."""
    lines = [f"(set-logic {logic})"]
    for name in sorted(objects):
        lines.extend(_declare(name, objects[name]))
        lines.append(f"(assert (= {name} {_real(assignment[name])}))")
    lines.append(f"(assert {math_smt.render_pred(pred, objects, 'Rat')})")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _symbolic_distinct(term, closed_smt, objects, logic="QF_LRA"):
    """Params FREE over the whole Real line (never pinned), assert term !=
    closed form: ``unsat`` = all-values agreement (the b2 shape).  QF_LRA where
    the term is linear -- declaring it is the point: cvc5 would refuse the
    obligation outright if the rendering smuggled in a variable divisor."""
    lines = [f"(set-logic {logic})"]
    for name in sorted(objects):
        lines.extend(_declare(name, objects[name]))
    lines.append(f"(assert (distinct "
                 f"{math_smt.render_term(term, objects, 'Rat')} {closed_smt}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _carrier_xor(pred):
    """The cross-carrier divergence obligation on a GROUND atom: the Rat
    rendering (Real sort) XOR the Nat rendering (Int sort) of ONE pred, both
    produced by the mirror itself.  ``unsat`` would prove the carriers mean the
    same thing here; ``sat`` says a divergence point exists -- corroborated by
    eval, never load-bearing alone (operator_growth._carrier_stability_
    obligation's discipline).

    QF_LIRA is a BATTERY-LOCAL choice, not a mirror behaviour: it exists only so
    two sorts can meet in one query.  The mirror never emits a mixed-sort
    obligation -- B1 refuses a mixed-carrier reading at the gate, which is the
    whole `rat:no-coercion` limit -- so nothing downstream inherits this logic.
    Both arms are ground, so no shared free variable has to be coerced."""
    lines = ["(set-logic QF_LIRA)",
             "(assert (xor "
             f"{math_smt.render_pred(pred, {}, 'Rat')} "
             f"{math_smt.render_pred(pred, {}, 'Nat')}))",
             "(check-sat)"]
    return "\n".join(lines) + "\n"


# ================================================= (b) differential value battery
# Planted Rat terms: `closed` is stated by hand AND recomputed by the structural
# oracle, so a typo in either one is caught.  The rows are the cases the carrier
# exists to get right -- exactness (thirds do not round), a negative difference
# (`-` is real subtraction here, never Nat truncation), the totalisation at zero
# in both its literal and its object-divisor form, a fraction raised to a
# literal power (the D10 unroll over a non-integer base), and one expression
# using all four of `+ * - /` at once.
_PLANTED = [
    # (label, term, closed(assignment) -> Fraction)
    ("exact_half", _frac(1, 2), lambda a: Fraction(1, 2)),
    ("thirds_sum_is_exact", _add(_frac(1, 3), _frac(1, 6)),
     lambda a: Fraction(1, 2)),
    ("negative_difference", _sub(_lit(3), _lit(5)), lambda a: Fraction(-2)),
    ("div_by_zero_totalises", _div(_lit(3), _lit(0)), lambda a: Fraction(0)),
    ("ref_div_by_zero_totalises", _div(_ref("x"), _lit(0)),
     lambda a: Fraction(0)),
    ("literal_power_of_a_fraction", _pow(_frac(2, 3), 3),
     lambda a: Fraction(8, 27)),
    ("scaled_ref", _div(_mul(_ref("x"), _lit(3)), _lit(4)),
     lambda a: a["x"] * 3 / Fraction(4)),
    ("mixed_expression",
     _sub(_add(_mul(_lit(2), _frac(3, 4)), _div(_ref("x"), _lit(2))), _lit(1)),
     lambda a: Fraction(2) * Fraction(3, 4) + a["x"] / Fraction(2) - 1),
    ("nested_quotient", _div(_frac(1, 2), _frac(1, 4)), lambda a: Fraction(2)),
]

# The sweep: zero, a proper fraction, a negative fraction, an integer-valued
# rational.  Small on purpose -- the point is exactness, not coverage.
_XS = [Fraction(0), Fraction(1, 2), Fraction(-3, 2), Fraction(2)]


@pytest.mark.parametrize("label,term,closed", _PLANTED,
                         ids=[p[0] for p in _PLANTED])
def test_value_battery_eval_agrees_with_dual_solver(label, term, closed):
    objects = {"x": "Rat"}
    for xv in _XS:
        a = {"x": xv}
        want = closed(a)
        assert _rat_value(term, a) == want, f"{label}@{a}: oracle disagrees"
        v = eval_term(term, a, objects, "Rat")
        # exactness is the purchase: a float here would pass `==` on 1/2 and
        # quietly lose 1/3, so the type is pinned alongside the value.
        assert not isinstance(v, float), f"{label}@{a}: eval returned a float"
        assert v == want, f"{label}@{a}: evaluator {v} != oracle {want}"
        z, c = _dual(_ground_equation(term, objects, a, v), "sat")
        assert z == "pass", f"{label}@{a}: z3 {z}"
        assert c in ("pass", "unknown", "error"), f"{label}@{a}: cvc5 {c}"


# Order on Q is decidable and the whole reason `<=` and `<` are admitted at Rat
# (QF_LRA); these rows carry BOTH directions, so the differential can fail.
_PLANTED_ATOMS = [
    # (label, pred, expected)
    ("half_lt_two_thirds", _lt(_frac(1, 2), _frac(2, 3)), True),
    ("le_is_reflexive_on_thirds", _le(_frac(1, 3), _frac(1, 3)), True),
    ("negative_difference_is_negative", _lt(_sub(_lit(3), _lit(5)), _lit(0)),
     True),
    ("distinct_fractions", _ne(_frac(1, 2), _frac(1, 3)), True),
    ("ref_order_row", _le(_div(_ref("x"), _lit(2)), _ref("x")), None),
    # a FALSE row: 2/3 is not below 1/2, and the obligation must come back unsat.
    ("false_order_row", _lt(_frac(2, 3), _frac(1, 2)), False),
    ("false_equality_row", _eq(_add(_frac(1, 3), _frac(1, 3)), _lit(1)), False),
]


@pytest.mark.parametrize("label,pred,expected", _PLANTED_ATOMS,
                         ids=[p[0] for p in _PLANTED_ATOMS])
def test_order_battery_eval_agrees_with_dual_solver(label, pred, expected):
    """`expected is None` means the row's truth VARIES with x -- the oracle
    supplies it per point, and the row is required to take both values across
    the sweep, so a row that quietly became constant stops being a row."""
    objects = {"x": "Rat"}
    seen = set()
    for xv in _XS:
        a = {"x": xv}
        want = _rat_truth(pred, a) if expected is None else expected
        assert _rat_truth(pred, a) is want, f"{label}@{a}: oracle disagrees"
        assert bool(eval_pred(pred, a, objects, "Rat")) is want, \
            f"{label}@{a}: evaluator disagrees"
        z, c = _dual(_ground_pred(pred, objects, a), "sat" if want else "unsat")
        assert z == "pass", f"{label}@{a}: z3 {z}"
        assert c in ("pass", "unknown", "error"), f"{label}@{a}: cvc5 {c}"
        seen.add(want)
    if expected is None:
        assert seen == {True, False}, f"{label}: the row no longer varies"


def test_lossy_division_gets_no_certificate():
    """The divergence tooth: DROP the div-by-zero `ite` guard from the emitted
    rendering and the obligation must flip verdict -- never a silent pass.

    Read the shape before changing it.  SMT-LIB leaves `(/ x 0)` UNCONSTRAINED,
    so the guard-dropped rendering does not merely compute something else: it
    lets the solver INVENT a value that happens to match.  A ground obligation
    is therefore useless here (measured: it still answers sat).  The claim that
    separates them has to be universal -- "is this term zero at EVERY
    numerator?" -- which the honest, totalised rendering satisfies (unsat, no
    counterexample) and the lossy one does not (sat, a model where q/0 != 0).
    The same D9 hazard math_smt's `%`-totalisation comment names, in its
    division form."""
    term = _div(_ref("x"), _lit(0))
    objects = {"x": "Rat"}
    assert eval_term(term, {"x": Fraction(7, 3)}, objects, "Rat") == 0

    honest = math_smt.render_term(term, objects, "Rat")
    # the lossy lowering: the same text with the totalisation guard removed.
    lossy = f"(/ {math_smt.render_term(_ref('x'), objects, 'Rat')} 0.0)"
    assert honest != lossy, ("the guard is not being emitted at all -- the "
                             "totalisation is missing, not merely lossy")

    def obligation(rendered):
        return ("(set-logic QF_NRA)\n(declare-const x Real)\n"
                f"(assert (distinct {rendered} 0.0))\n(check-sat)\n")

    z, c = _dual(obligation(honest), "unsat")
    assert z == "pass", f"the totalised rendering must be unsat, z3 said {z}"
    assert c in ("pass", "unknown", "error"), f"cvc5 {c}"
    z, c = _dual(obligation(lossy), "unsat")
    assert z == "fail", f"the un-totalised rendering must be refused, z3 {z}"
    assert c in ("fail", "error"), f"un-totalised rendering, cvc5 said {c}"


def test_rat_rendering_is_over_the_real_sort():
    """The only tooth that reads the emitted TEXT: a Rat term renders over Real
    (decimal numerals) with the totalisation guard at every `/`, and the Int
    rendering of a comparable term carries neither.  Retarget this one if the
    numeral shape changes; the solver-level teeth do not care."""
    at_rat = math_smt.render_term(_div(_ref("x"), _lit(2)), {"x": "Rat"}, "Rat")
    assert "(ite " in at_rat and "0.0" in at_rat
    at_int = math_smt.render_term(_sub(_ref("x"), _lit(2)), {"x": "Int"}, "Int")
    assert "0.0" not in at_int
    # and the Rat `-` is REAL subtraction: no Nat truncation ite ever appears.
    rat_sub = math_smt.render_term(_sub(_ref("x"), _lit(2)), {"x": "Rat"}, "Rat")
    assert "(ite " not in rat_sub


# ================================================ D8-class carrier stability
# One atom, two carriers, the shared ground point.  Rat reads `-` as real
# subtraction; Nat truncates at zero (D8) -- so these rows diverge, and the xor
# obligation is how we say "diverge" in a form a solver can refuse.
_DIVERGENCE = [
    # (label, pred, rat_truth, nat_truth)
    ("three_minus_five", _eq(_sub(_lit(3), _lit(5)), _lit(-2)), True, False),
    ("one_minus_four", _eq(_sub(_lit(1), _lit(4)), _lit(-3)), True, False),
    ("zero_minus_two_is_negative", _lt(_sub(_lit(0), _lit(2)), _lit(0)),
     True, False),
]


@pytest.mark.parametrize("label,pred,rat_truth,nat_truth", _DIVERGENCE,
                         ids=[p[0] for p in _DIVERGENCE])
def test_rat_and_nat_readings_diverge_and_the_point_is_witnessed(
        label, pred, rat_truth, nat_truth):
    """The solver says the two carriers CAN disagree here; eval NAMES the
    disagreement.  A solver existence claim is never load-bearing on its own
    (the direction-split rule) -- the eval-witnessed verdicts are the evidence,
    and the xor is the corroboration."""
    assert bool(eval_pred(pred, {}, {}, "Rat")) is rat_truth, label
    assert bool(eval_pred(pred, {}, {}, "Nat")) is nat_truth, label
    assert rat_truth != nat_truth, f"{label} is not a divergence row"
    z, c = _dual(_carrier_xor(pred), "sat")
    assert z == "pass", f"{label}: the carriers must be able to disagree, z3 {z}"
    assert c in ("pass", "unknown", "error"), f"{label}: cvc5 {c}"


@pytest.mark.parametrize("label,pred", [
    ("addition_agrees", _eq(_add(_lit(3), _lit(5)), _lit(8))),
    ("non_truncating_difference_agrees", _eq(_sub(_lit(5), _lit(3)), _lit(2))),
])
def test_carrier_xor_proves_agreement_where_there_is_no_divergence(label, pred):
    """The obligation is not trivially satisfiable: where the carriers really
    do mean the same thing, the SAME xor comes back ``unsat``.  Without this
    control the divergence rows above would prove nothing about the mirror."""
    assert bool(eval_pred(pred, {}, {}, "Rat")) is True
    assert bool(eval_pred(pred, {}, {}, "Nat")) is True
    z, c = _dual(_carrier_xor(pred), "unsat")
    assert z == "pass", f"{label}: z3 {z}"
    assert c in ("pass", "unknown", "error"), f"{label}: cvc5 {c}"


def test_the_gate_refusal_is_the_divergence_handling_for_division():
    """The other half of the D8 story, and the more important half: `1/2` has no
    integer reading to diverge FROM.  There is nothing to xor -- Lean's `/` at
    Nat and Int is floor division, a genuinely different function, and admitting
    it would let the compiler render a truth the evaluator never checked.  So
    the divergence is handled at the GATE, by refusal, and that refusal is the
    tooth (spec-p3's `/`-is-Rat-only freeze; it also keeps this class clear of
    buildloop/census.py's `operator:div` row for integer readings)."""
    half = _eq(_frac(1, 2), _frac(1, 2))
    r = _parse({}, "Rat", half)                       # admissible at Rat
    assert r.ambient_carrier() == "Rat"
    assert eval_term(_frac(1, 2), {}, {}, "Rat") == Fraction(1, 2)
    for carrier in ("Nat", "Int"):
        with pytest.raises(FragmentMiss) as e:
            _parse({}, carrier, half)
        assert e.value.missing_kind_guess == f"operator:/@{carrier}", carrier


# ======================================================== (b2) symbolic battery
def test_symbolic_battery_two_halves_make_a_whole():
    # (x/2) + (x/2) = x for ALL rationals x (free param over the whole line,
    # never pinned) -- the identity that is FALSE over every integer carrier and
    # is exactly what buying Q buys.
    term = _add(_div(_ref("x"), _lit(2)), _div(_ref("x"), _lit(2)))
    z, c = _dual(_symbolic_distinct(term, "x", {"x": "Rat"}), "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


def test_symbolic_battery_divide_then_multiply_is_the_identity():
    # ((x + y) / 2) * 2 = x + y for ALL rationals -- no rounding step survives.
    term = _mul(_div(_add(_ref("x"), _ref("y")), _lit(2)), _lit(2))
    z, c = _dual(_symbolic_distinct(term, "(+ x y)",
                                    {"x": "Rat", "y": "Rat"}), "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


def test_symbolic_battery_division_by_zero_is_zero_everywhere():
    # The D9-class convention as an ALL-VALUES claim: x/0 = 0 for every x, which
    # is what makes the fragment total.  QF_NRA: the guard's `/` is inside the
    # untaken branch and cvc5 classifies on the syntax, not the semantics.
    term = _div(_ref("x"), _lit(0))
    z, c = _dual(_symbolic_distinct(term, "0.0", {"x": "Rat"}, "QF_NRA"),
                 "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


def test_symbolic_battery_refuses_a_false_identity():
    """The battery can fail: halving is not the identity on Q (x = 1 is a
    counterexample), so the distinctness must be satisfiable."""
    term = _div(_ref("x"), _lit(2))
    assert eval_term(term, {"x": Fraction(1)}, {"x": "Rat"}, "Rat") \
        != Fraction(1)
    z, c = _dual(_symbolic_distinct(term, "x", {"x": "Rat"}), "sat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


# ==================================================== gate refusals (demand data)
def test_div_outside_rat_refuses_and_is_unmineable():
    """`/` is admissible ONLY at Rat.  At Nat and Int, Lean's `/` is FLOOR
    division -- a different function, whose divergence from exact division is
    precisely the bug class T4 exists to catch -- so the reading refuses at the
    gate rather than compiling a claim the evaluator cannot mirror.  Refusals
    are first-class demand data (F4): integer division is a named, ranked,
    unpurchased class, not an oversight.

    The REGISTRY tooth for this refusal is
    `tests/test_math_reading.py::test_div_outside_rat_is_a_fragment_miss`,
    which pins the refusal at the gate where it is decided.  This row is the
    battery's own sibling and carries what that one does not: the resolution
    path with no ambient, and the MINER-facing consequence -- `/` must be
    unmineable outside Rat, or the recurrence miner manufactures the very
    integer division the gate just refused."""
    concl = _eq(_div(_ref("x"), _lit(2)), _lit(1))
    for carrier in ("Nat", "Int"):
        with pytest.raises(FragmentMiss) as e:
            _parse({"x": carrier}, carrier, concl)
        assert e.value.missing_kind_guess == f"operator:/@{carrier}", carrier
    # ...and with no ambient, where the carrier is resolved from the object
    with pytest.raises(FragmentMiss) as e2:
        _parse({"x": "Int"}, None, concl)
    assert e2.value.missing_kind_guess == "operator:/@Int"
    # the positive control: the same shape at Rat is admitted
    r = _parse({"x": "Rat"}, "Rat", concl)
    assert r.objects() == {"x": "Rat"}
    # and the miner may never mine an integer `/` slot: the op's carrier support
    # is Rat ALONE, not the whole whitelist (COMPRESSION §11.3's mined-`-`
    # hazard, in its division form).
    assert op_signature("/") == ("term", 2, frozenset({"Rat"}))


def test_mod_family_refuses_at_rat():
    """There is no remainder on Q and no divisibility either: `%`, `mod`, `dvd`,
    `even`, `odd` are refused at Rat BY CONSTRUCTION, not merely unimplemented.
    `%` needs an explicit carrier check because the built-in term operators are
    carrier-blind (spec-p3 §B1.1); the lexicon words refuse through the
    carrier-indexed `lean` table, which has no Rat entry for any of them."""
    rows = (
        (_eq(_mod(_ref("x"), _lit(2)), _lit(0)), "%"),
        (_eq({"op": "mod", "args": [_ref("x"), _lit(2)]}, _lit(0)), "mod"),
        (_dvd(_lit(2), _ref("x")), "dvd"),
        ({"op": "even", "args": [_ref("x")]}, "even"),
        ({"op": "odd", "args": [_ref("x")]}, "odd"),
    )
    for pred, op in rows:
        with pytest.raises(FragmentMiss) as e:
            _parse({"x": "Rat"}, "Rat", pred)
        assert e.value.missing_kind_guess == f"operator:{op}@Rat", op
    # the integer carriers keep every one of them -- this purchase narrows
    # nothing that was already bought.
    _parse({"x": "Nat"}, "Nat", _eq(_mod(_ref("x"), _lit(2)), _lit(0)))
    _parse({"x": "Int"}, "Int", _dvd(_lit(2), _ref("x")))


def test_mixed_rat_and_integer_carriers_refuse():
    """`rat:no-coercion`, the named v1 limit: a `-` mixing Rat with an integer
    carrier refuses exactly as a Nat/Int mix does (B1).  There is no coercion
    story this cycle -- Lean's `Rat.cast` would have to be mirrored in eval and
    in SMT, and an unmirrored coercion is the two-translations-of-one-text bug
    class (TRUST 1.2e).  Refused in writing, ranked by F4, not silently widened."""
    mix = _eq(_sub(_ref("x"), _ref("y")), _lit(0))
    for other in ("Nat", "Int"):
        with pytest.raises(BadMathReading):
            _parse({"x": "Rat", "y": other}, None, mix)
        # ...and an ambient does NOT rescue it (the P3 extension to the B1 walk):
        # a declared ambient resolves an ambiguity between Nat and Int, but
        # there is no ambient that makes a Rat and an Int operand the same kind
        # of thing.
        with pytest.raises(BadMathReading):
            _parse({"x": "Rat", "y": other}, "Rat", mix)
    # single-carrier Rat is fine, and so is the untouched Nat/Int ambient rule
    _parse({"x": "Rat", "y": "Rat"}, "Rat", mix)
    _parse({"x": "Nat", "y": "Int"}, "Int", mix)


def test_rat_joins_the_carrier_whitelist_without_disturbing_it():
    """The whitelist grew by exactly one row, in place -- the integer carriers
    keep their positions so nothing that indexes CARRIERS shifts under them."""
    assert CARRIERS == ("Nat", "Int", "Rat")
    with pytest.raises(FragmentMiss) as e:
        _parse({"x": "Real"}, None, _eq(_ref("x"), _ref("x")))
    assert e.value.missing_kind_guess == "carrier:Real"


# ==================================================== SMT logic classification
def test_logic_classification_splits_lra_from_nra():
    """A Rat obligation is a REAL obligation: linear Rat hypotheses classify
    QF_LRA and only genuine nonlinearity -- a product of two objects, or
    division BY an object -- pushes it to QF_NRA.  This is required for
    correctness, not advisory: cvc5's parser refuses `(/ x y)` under QF_LRA
    outright ("a non-linear fact was asserted to arithmetic in a linear
    logic"), the same strictness that forces the QF_LIA/QF_NIA split."""
    linear = _eq(_add(_div(_ref("x"), _lit(2)), _ref("x")), _lit(1))
    by_object = _eq(_div(_lit(1), _ref("x")), _lit(1))
    product = _eq(_mul(_ref("x"), _ref("y")), _lit(1))
    # division by a CONSTANT is linear; division by an object is not (the
    # `%`-divisor rule, in its division form).
    assert not math_smt._term_nonlinear(_div(_ref("x"), _lit(2)))
    assert math_smt._term_nonlinear(_div(_lit(1), _ref("x")))
    assert not math_smt._pred_nonlinear(linear)
    assert math_smt._pred_nonlinear(by_object)
    assert math_smt._pred_nonlinear(product)

    triv = _eq(_ref("x"), _ref("x"))
    assert math_smt._logic(_parse({"x": "Rat"}, "Rat", triv,
                                  hyps=[linear])) == "QF_LRA"
    assert math_smt._logic(_parse({"x": "Rat"}, "Rat", triv,
                                  hyps=[by_object])) == "QF_NRA"
    assert math_smt._logic(_parse({"x": "Rat", "y": "Rat"}, "Rat", triv,
                                  hyps=[product])) == "QF_NRA"
    # the integer classification is untouched: this purchase adds a branch, it
    # does not re-route the one that was already paid for.
    int_lin = _eq(_add(_ref("x"), _lit(1)), _lit(2))
    assert math_smt._logic(_parse({"x": "Int"}, "Int", triv,
                                  hyps=[int_lin])) == "QF_LIA"
    assert math_smt._logic(_parse({"x": "Int", "y": "Int"}, "Int", triv,
                                  hyps=[product])) == "QF_NIA"


# ==================================================== reflect slice (honest state)
def _exists_reading(carrier):
    """A forall-outer / exists-inner reading -- the ONE shape both reflect
    routes accept -- on a single carrier.  Built here rather than with `_doc`
    because the reflect routes need the exists binder `_doc` does not emit."""
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": carrier}},
        {"id": "on", "force": "demand", "quote": "the number n",
         "lf": {"kind": "object", "name": "n", "type": carrier}},
        {"id": "om", "force": "demand", "quote": "the number m",
         "lf": {"kind": "object", "name": "m", "type": carrier}},
        {"id": "qf", "force": "demand", "quote": "for every",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "qx", "force": "demand", "quote": "there exists",
         "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
        {"id": "c", "force": "demand", "quote": "n below m",
         "lf": {"kind": "conclusion", "pred": _lt(_ref("n"), _ref("m"))}},
    ]
    src = " ".join(s["quote"] for s in stmts if s["quote"])
    return parse_math_reading(
        json.dumps({"theorem": "rat_reflect", "statements": stmts}), src)


def test_rat_reading_is_a_named_reflect_skip():
    """CURRENT honest state, and the point of P3's reflect half: the reflect
    slice is proven over Int and Nat ONLY, so a Rat reading must skip BY NAME
    on BOTH probe routes.  Those routes were fail-OPEN before this purchase --
    they decided the layer by asking whether the carrier set was exactly
    `{"Nat"}`, so ANY other single carrier fell through to the Int slice and
    would have been probed against a layer that says nothing about Q.  A named
    skip is never a failure; an unnamed one is a silent widening.  The Q tower
    is CI-lane future work (the addendum's own blocker list), and when it lands
    this tooth flips to assert the probe.

    The fail-close lives at the LAYER CHOICE (`_reflect_layer_is_nat`), not in
    the quoters: the quoters are told which layer to quote for, so they are
    downstream of exactly the decision that was unsound.  Pinned on the probes'
    reported reason, which is the thing the sweep records."""
    from run.reflect_shadow import (shadow_probe, search_probe,
                                    _reflect_layer_is_nat, SliceMiss)
    rat = _exists_reading("Rat")
    assert shadow_probe(rat) == {
        "status": "skip", "reason": "carrier-out-of-reflect-slice:Rat"}
    assert search_probe(rat) == {
        "status": "skip", "reason": "carrier-out-of-reflect-slice:Rat"}
    # the decision itself, so the reason string cannot drift silently
    with pytest.raises(SliceMiss) as e:
        _reflect_layer_is_nat({"Rat"})
    assert str(e.value) == "carrier-out-of-reflect-slice:Rat"
    # the integer layers keep PROBING: the fail-close narrows the Rat path only.
    assert _reflect_layer_is_nat({"Nat"}) is True
    assert _reflect_layer_is_nat({"Int"}) is False
    assert shadow_probe(_exists_reading("Int"))["status"] == "probe"


# ============================================== end-to-end reading + Lean + hash
def test_end_to_end_gate_eval_compile_escape():
    """The binder carries the carrier string VERBATIM -- `Rat` is the ASCII Lean
    type text, because the Q glyph is escape-gate refused (non-ASCII identifier
    character, T7) -- and the rendering survives the gate.  Elaboration is
    deliberately NOT claimed here: Lean-touching steps ride the CI lane, and the
    reflect slice names Rat as out of scope this cycle."""
    concl = _eq(_add(_div(_ref("x"), _lit(2)), _div(_ref("x"), _lit(2))),
                _ref("x"))
    r = _parse({"x": "Rat"}, "Rat", concl)
    assert conclusion_holds(r, {"x": Fraction(1, 3)})
    assert conclusion_holds(r, {"x": Fraction(-5, 2)})
    art = compile_math_reading(r)
    assert "(x : Rat)" in art["lean_text"]
    assert "/ 2" in art["lean_text"]              # `/` renders infix, Rat-only
    ok, reason = validate_lean(art["lean_text"])
    assert ok, reason
    # byte-stability: recompilation is hash-identical
    art2 = compile_math_reading(_parse({"x": "Rat"}, "Rat", concl))
    assert art["statement_hash"] == art2["statement_hash"]

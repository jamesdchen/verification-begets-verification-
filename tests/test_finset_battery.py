"""P2 admission batteries: the bounded Finset carrier + cardinality node class.

The PLAN_FRAGMENT §4 bill, applied to the second structural extension
(sets-cardinality), riding P1's binding machinery: a `setbuild` is a bounded,
filtered literal interval, and `card` is the term operator that counts it back
into the arithmetic fragment.  LLM-free, Lean-free teeth that would fail if the
class's semantics regressed in ANY of the four translations (gate / eval / SMT
mirror / Lean text), in the operator-growth battery discipline:

  * (b-analogue) DIFFERENTIAL VALUE battery: over planted card terms on both
    carriers and small-int instances, ``math_eval.eval_term``'s count is
    corroborated by the ground-equation SMT differential on z3 AND cvc5
    (dual-solver agreement; absent cvc5 degrades honestly).
  * (b2-analogue) SYMBOLIC battery: the filter's object params FREE (never
    pinned), the unrolled indicator sum is asserted DISTINCT from an
    independently-derived closed form; a dual-solver ``unsat`` is the
    all-values agreement.
  * LOSSY FILTER GETS NO CERTIFICATE: a planted filter-dropping lowering (the
    interval counted un-filtered) must produce a DEFINITE solver disagreement
    -- the divergence tooth that proves the differential has teeth.
  * The gate's refusal surface (symbolic bound / nesting / bare setbuild /
    non-set card arg / negative bound / shadowing) is pinned as demand data,
    the SMT logic classification is pinned, and the Lean rendering + escape
    gate + hash byte-stability are pinned.
"""
import json

import pytest

from generators.math_reading import (
    parse_math_reading, BadMathReading, FragmentMiss, _check_term, op_signature)
from generators.math_eval import eval_term, eval_pred
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


def _setbuild(var, lo, hi, filt):
    return {"op": "setbuild",
            "args": [{"var": var}, {"lit": lo}, {"lit": hi}, filt]}


def _card(var, lo, hi, filt):
    return {"op": "card", "args": [_setbuild(var, lo, hi, filt)]}


# atom / pred shorthands over the index `i`
def _even(t):
    return {"op": "even", "args": [t]}


def _odd(t):
    return {"op": "odd", "args": [t]}


def _le(a, b):
    return {"op": "<=", "args": [a, b]}


def _eq(a, b):
    return {"op": "=", "args": [a, b]}


def _dvd(a, b):
    return {"op": "dvd", "args": [a, b]}


def _mod(a, b):
    return {"op": "%", "args": [a, b]}


def _ref(n):
    return {"ref": n}


def _lit(k):
    return {"lit": k}


def _ground_equation(term, objects, carrier, assignment, value):
    """Pin every object, assert term = value: ``sat`` iff the solvers'
    arithmetic agrees with the evaluator (the _ground_term_smt discipline)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.append(f"(declare-const {name} Int)")
        if objects[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
        lines.append(
            f"(assert (= {name} {math_smt._render_lit(assignment[name])}))")
    lines.append(f"(assert (= {math_smt.render_term(term, objects, carrier)} "
                 f"{math_smt._render_lit(value)}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


# ================================================= (b) differential value battery
# Planted cards: independent Python oracles for the count; filters exercise the
# index directly (even/odd/mod), an object-dependent comparison, an object dvd
# divisor (nonlinear), a conjunction, and the empty set.
_PLANTED = [
    # (label, carrier, term, oracle(assignment) -> count)
    ("count_even", "Nat", _card("i", 1, 6, _even(_ref("i"))),
     lambda a: sum(1 for i in range(1, 7) if i % 2 == 0)),
    ("count_odd", "Int", _card("i", 0, 9, _odd(_ref("i"))),
     lambda a: sum(1 for i in range(0, 10) if i % 2 == 1)),
    ("count_mod3", "Nat", _card("i", 0, 11, _eq(_mod(_ref("i"), _lit(3)), _lit(0))),
     lambda a: sum(1 for i in range(0, 12) if i % 3 == 0)),
    ("count_le_x", "Nat", _card("i", 0, 5, _le(_ref("i"), _ref("x"))),
     lambda a: sum(1 for i in range(0, 6) if i <= a["x"])),
    ("count_mult_x", "Nat", _card("i", 1, 12, _dvd(_ref("x"), _ref("i"))),
     lambda a: sum(1 for i in range(1, 13)
                   if (a["x"] != 0 and i % a["x"] == 0) or (a["x"] == 0 and i == 0))),
    ("count_conj", "Nat",
     _card("i", 1, 10, {"op": "and", "args": [_even(_ref("i")),
                                              _le(_ref("i"), _ref("x"))]}),
     lambda a: sum(1 for i in range(1, 11) if i % 2 == 0 and i <= a["x"])),
    ("count_empty", "Nat", _card("i", 5, 4, _even(_ref("i"))),
     lambda a: 0),
]


@pytest.mark.parametrize("label,carrier,term,oracle", _PLANTED,
                         ids=[p[0] for p in _PLANTED])
def test_value_battery_eval_agrees_with_dual_solver(label, carrier, term, oracle):
    objects = {"x": carrier}
    for xv in ([0, 1, 3, 6] if carrier == "Nat" else [-3, 0, 2, 6]):
        a = {"x": xv}
        v = eval_term(term, a, objects, carrier)
        assert v == oracle(a), f"{label}@{a}: evaluator {v} != oracle {oracle(a)}"
        z, c = _dual(_ground_equation(term, objects, carrier, a, v), "sat")
        assert z == "pass", f"{label}@{a}: z3 {z}"
        assert c in ("pass", "unknown", "error"), f"{label}@{a}: cvc5 {c}"


def test_lossy_filter_gets_no_certificate():
    """The divergence tooth: DROP the filter (count the whole interval instead
    of only the even members) and the ground differential must refuse --
    definite unsat from both solvers, never a silent pass."""
    term = _card("i", 1, 6, _even(_ref("i")))          # counts 2,4,6 -> 3
    lossy = _card("i", 1, 6, _le(_lit(0), _ref("i")))  # 0<=i always true -> 6
    objects = {"x": "Nat"}
    a = {"x": 0}
    v = eval_term(term, a, objects, "Nat")
    assert v == 3 and eval_term(lossy, a, objects, "Nat") == 6
    z, c = _dual(_ground_equation(lossy, objects, "Nat", a, v), "sat")
    assert z == "fail", f"lossy filter must be refused, z3 said {z}"
    assert c in ("fail", "error"), f"lossy filter must be refused, cvc5 said {c}"


# ======================================================== (b2) symbolic battery
def _symbolic_distinct(term, closed_smt, objects):
    """Params FREE (Nat >= 0), assert term != closed form: unsat = all-values
    agreement (the b2 shape)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.append(f"(declare-const {name} Int)")
        if objects[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
    lines.append(f"(assert (distinct "
                 f"{math_smt.render_term(term, objects, None)} {closed_smt}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def test_symbolic_battery_count_of_equal():
    # |{i in 1..5 | i = x}| = (1 if 1<=x<=5 else 0), for ALL x >= 0 (free param).
    term = _card("i", 1, 5, _eq(_ref("i"), _ref("x")))
    closed = "(ite (and (<= 1 x) (<= x 5)) 1 0)"
    z, c = _dual(_symbolic_distinct(term, closed, {"x": "Nat"}), "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


def test_symbolic_battery_count_le_is_clamped_successor():
    # |{i in 0..3 | i <= x}| = min(x, 3) + 1 for ALL x >= 0 (a clamped count).
    term = _card("i", 0, 3, _le(_ref("i"), _ref("x")))
    closed = "(ite (<= 3 x) 4 (+ x 1))"
    z, c = _dual(_symbolic_distinct(term, closed, {"x": "Nat"}), "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


# ==================================================== gate refusals (demand data)
def test_symbolic_bound_is_a_fragment_miss():
    symbolic = {"op": "card", "args": [{"op": "setbuild", "args": [
        {"var": "i"}, {"lit": 1}, {"ref": "n"}, _even(_ref("i"))]}]}
    with pytest.raises(FragmentMiss) as e:
        _check_term(symbolic, {"n": "Nat"})
    assert e.value.missing_kind_guess == "set:symbolic-bound"


def test_nested_set_is_a_fragment_miss():
    inner = _card("j", 1, 2, _even(_ref("j")))
    # a card buried inside a setbuild filter (under a comparison) is set:nested
    with pytest.raises(FragmentMiss) as e:
        _check_term(_card("i", 1, 3, _eq(inner, _lit(1))), {})
    assert e.value.missing_kind_guess == "set:nested"
    # and a set inside a big-operator body is set:nested too
    bigsum = {"op": "bigsum", "args": [
        {"var": "i"}, {"lit": 1}, {"lit": 3}, inner]}
    with pytest.raises(FragmentMiss) as e2:
        _check_term(bigsum, {})
    assert e2.value.missing_kind_guess == "set:nested"


def test_bare_setbuild_and_non_set_card_arg_refuse():
    # a bare setbuild is not a value
    with pytest.raises(BadMathReading):
        _check_term(_setbuild("i", 1, 6, _even(_ref("i"))), {})
    # card's argument must be a setbuild, not any other term
    with pytest.raises(BadMathReading):
        _check_term({"op": "card", "args": [{"lit": 3}]}, {})
    with pytest.raises(BadMathReading):
        _check_term({"op": "card", "args": [_ref("x")]}, {"x": "Nat"})


def test_shadowing_and_negative_bounds_refuse():
    with pytest.raises(BadMathReading):
        _check_term(_card("n", 1, 3, _even(_ref("n"))), {"n": "Nat"})
    with pytest.raises(BadMathReading):
        _check_term(_card("i", -1, 3, _even(_ref("i"))), {})


def test_object_filter_is_in_fragment_but_reflect_skips_it():
    # An object-dependent filter IS in the gate/eval/SMT/compile fragment...
    t = _card("i", 0, 5, _le(_ref("i"), _ref("x")))
    _check_term(t, {"x": "Nat"})
    assert eval_term(t, {"x": 3}, {"x": "Nat"}, "Nat") == 4
    # ...but is a NAMED reflect skip (needs a term-level conditional -- a future
    # purchase), never a silent widening.
    from run.reflect_shadow import quote_term, SliceMiss
    with pytest.raises(SliceMiss) as e:
        quote_term(t, {"x": 0}, "Nat")
    assert str(e.value) == "card:object-filter"
    # an index-only filter reflects through cardTm
    q = quote_term(_card("i", 1, 6, _even(_ref("i"))), {}, "Nat")
    assert q.startswith("(cardTm [")


# ==================================================== SMT logic classification
def test_logic_classification_matches_filter_shape():
    """card unrolls to a sum of indicators: an ite over constant branches stays
    linear (QF_LIA); only a NONLINEAR filter condition (a mod/dvd by an object)
    pushes the obligation to QF_NIA -- mirroring the ^/bigprod discipline."""
    index_only = _card("i", 1, 6, _even(_ref("i")))
    obj_linear = _card("i", 0, 5, _le(_ref("i"), _ref("x")))
    obj_dvd = _card("i", 1, 6, _dvd(_ref("x"), _ref("i")))   # divisor is object
    assert not math_smt._term_nonlinear(index_only)
    assert not math_smt._term_nonlinear(obj_linear)
    assert math_smt._term_nonlinear(obj_dvd)
    # the count depends on a free object iff the filter does
    assert not math_smt._has_ref(index_only)
    assert math_smt._has_ref(obj_linear)
    # the binding class is never a mineable slot
    assert op_signature("card") is None
    assert op_signature("setbuild") is None


# ============================================== end-to-end reading + Lean + hash
_SRC = ("For every natural number n, the number of even i from 1 to 6 is at "
        "most n plus 3.")


def _reading():
    return {
        "theorem": "card_e2e",
        "statements": [
            {"id": "amb", "force": "choice", "quote": "",
             "lf": {"kind": "ambient", "carrier": "Nat"}},
            {"id": "on", "force": "demand", "quote": "natural number n",
             "lf": {"kind": "object", "name": "n", "type": "Nat"}},
            {"id": "qf", "force": "demand",
             "quote": "For every natural number n",
             "lf": {"kind": "quantifier", "binder": "forall",
                    "objects": ["n"]}},
            {"id": "c", "force": "demand",
             "quote": "the number of even i from 1 to 6 is at most n plus 3",
             "lf": {"kind": "conclusion",
                    "pred": _le(_card("i", 1, 6, _even(_ref("i"))),
                                {"op": "+", "args": [_ref("n"), _lit(3)]})}},
        ]}


def test_end_to_end_gate_eval_compile_escape():
    r = parse_math_reading(json.dumps(_reading()), _SRC)
    pred = [s for s in r.statements if s["lf"]["kind"] == "conclusion"][0]
    assert eval_pred(pred["lf"]["pred"], {"n": 0}, {"n": "Nat"}, "Nat")
    art = compile_math_reading(r)
    assert "Finset.card (Finset.filter (fun i =>" in art["lean_text"]
    assert "Finset.Icc 1 6" in art["lean_text"]
    ok, reason = validate_lean(art["lean_text"])
    assert ok, reason
    # byte-stability: recompilation is hash-identical
    art2 = compile_math_reading(parse_math_reading(json.dumps(_reading()), _SRC))
    assert art["statement_hash"] == art2["statement_hash"]

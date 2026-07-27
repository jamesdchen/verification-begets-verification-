"""P9 admission batteries: NAMED SETS BY COMPREHENSION + the membership atom.

The PLAN_FRAGMENT §4 bill for the row `refusal-set-carrier`, and the battery
half of paying it.  What P9 buys is a `setdef` statement -- the source NAMES a
set and gives it an EXPLICIT comprehension body over one parameter -- plus the
`{"op":"mem","args":[<term>,{"set":s}]}` atom that takes membership in it.

WHY THIS BATTERY LOOKS LIKE P8'S, AND WHY THAT IS THE POINT.  A membership is
ELIMINATED at the gate, exactly as an application is: `e in {x | phi(x)}` IS
`phi(e)`.  By the time any consumer sees the reading there is no membership
left in it, so the full dual-solver differential is available -- and the thing
it corroborates is precisely the conservativity claim, that a named set adds no
meaning the fragment did not already have.

THE HEADLINE IDENTITY, conservativity made executable.  For every reading R
that uses a comprehension, let U(R) be the HAND-UNFOLDED twin -- the same
reading with the body substituted by hand and no `setdef` statement at all.
Then at all four consumers:

    eval:    same verdict at every point of a box sweep
    SMT:     same verdict from z3 AND from cvc5
    Lean:    byte-identical `lean_text` AND byte-identical `statement_hash`
    reflect: nothing to compare, because `Tm`/`Pd` are byte-unchanged

The reference is never a Python re-implementation of substitution: it is a
reading written out longhand in the fragment the purchase did not touch.  That
is what makes agreement evidence rather than a tautology -- if `_unfold_mem`
substituted the wrong comprehension, the hand-written twin would not move with
it, and `test_unfolding_a_wrong_comprehension_gets_no_certificate` plants
exactly that.

WHAT THE ROW DOES NOT BUY, measured here rather than promised in prose: a set
the source gives NO comprehension for.  `set:free-set-variable` (an arbitrary
`U`, the 09_Sets#definition-003 shape) and `set:set-valued-param` (a
comprehension binding a set, the powerset shape) are the refusals, and they are
the tower-class residue this row prices and deliberately leaves on the board --
membership in either SURVIVES unfolding, which is the one thing an
eliminability argument cannot reach.  The other three freezes --
`setdef:recursive-body`, `setdef:binder-body`, `setdef:open-body` -- are what
keep the elimination total, and all are pinned in both directions below.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from generators import math_compile as MC  # noqa: E402
from generators import math_eval as ME  # noqa: E402
from generators import math_reading as MR  # noqa: E402
from generators import math_smt as MS  # noqa: E402
from kernel.backends import SmtBackend  # noqa: E402


# --------------------------------------------------------------------------- #
# Helpers and the two readings every differential below compares.
# --------------------------------------------------------------------------- #
def _lit(k):
    return {"lit": k}


def _ref(n):
    return {"ref": n}


def _t(op, *args):
    return {"op": op, "args": list(args)}


def _in(elem, sname):
    return {"op": "mem", "args": [elem, {"set": sname}]}


#: The source both readings are grounded in.  One sentence, so the quotes are
#: identical in the two readings and groundedness cannot be what makes them
#: differ.
SRC = ("Let a be the set of even natural numbers. Show that for all natural "
       "numbers n, n is in a if and only if n is even.")


def _reading(statements, source=SRC, theorem="setdef_thm"):
    return MR.parse_math_reading(
        json.dumps({"theorem": theorem, "statements": statements}), source)


def _preamble():
    return [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "obn", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Nat"}},
        {"id": "opev", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "even", "carrier": "Nat"}},
        {"id": "opod", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "odd", "carrier": "Nat"}},
        {"id": "q", "force": "demand", "quote": "for all natural numbers n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
    ]


def _with_setdef(body=None, concl=None):
    """The P9 reading: one `setdef` statement and a MEMBERSHIP."""
    return _reading(_preamble() + [
        {"id": "sd", "force": "presupposition",
         "quote": "the set of even natural numbers",
         "lf": {"kind": "setdef", "name": "a", "param": "k",
                "body": _t("even", _ref("k")) if body is None else body}},
        {"id": "c", "force": "demand",
         "quote": "n is in a if and only if n is even",
         "lf": {"kind": "conclusion",
                "pred": concl if concl is not None else
                _t("iff", _in(_ref("n"), "a"), _t("even", _ref("n")))}},
    ])


def _hand_unfolded():
    """The reference reading: NO setdef, NO membership -- the comprehension
    body written out at the use site, in the fragment as it stood before P9."""
    return _reading(_preamble() + [
        {"id": "c", "force": "demand",
         "quote": "n is in a if and only if n is even",
         "lf": {"kind": "conclusion",
                "pred": _t("iff", _t("even", _ref("n")),
                           _t("even", _ref("n")))}},
    ])


def _concl(reading):
    return [s for s in reading.statements
            if s["lf"]["kind"] == "conclusion"][0]["lf"]["pred"]


def _dual(smtlib, expect):
    """Both solvers, same obligation, same expectation.  `SmtBackend` reports
    `pass`/`fail` AGAINST the expectation rather than the raw sat/unsat, so
    `pass` here means "the solver returned exactly `expect`"."""
    be = SmtBackend()
    z = be.run_z3(smtlib, expect=expect).get("result")
    c = be.run_cvc5(smtlib, expect=expect).get("result")
    return z, c


# --------------------------------------------------------------------------- #
# (a) THE ELIMINATION ITSELF: no membership survives the gate.
# --------------------------------------------------------------------------- #
def test_the_gate_leaves_no_membership_in_the_reading():
    """The structural fact the whole bill rests on, asserted before anything is
    compared: after `parse_math_reading`, every pred is membership-free and
    carries no `{"set": ...}` leaf.  This is why the evaluator, the SMT mirror
    and the Lean emitter needed no new code -- and a purchase that claimed that
    without checking it would be claiming the cheapest thing in the bill on
    trust."""
    def walk(node):
        if not isinstance(node, dict):
            return
        assert node.get("op") != "mem", f"a membership survived the gate: {node}"
        assert "set" not in node, f"a set leaf survived the gate: {node}"
        for a in node.get("args", []):
            walk(a)

    reading = _with_setdef()
    for s in reading.statements:
        if s["lf"]["kind"] in ("hypothesis", "conclusion"):
            walk(s["lf"]["pred"])
    # ... and the RECORD of what the source said is still there, because the
    # comprehension is a thing the text did, not a thing we invented.
    assert set(reading.setdefs()) == {"a"}
    assert reading.setdefs()["a"]["param"] == "k"


def test_the_desugared_pred_is_the_hand_unfolded_pred():
    """The elimination lands on exactly the pred a human writes longhand --
    structural equality against a reference nothing in P9 produced."""
    assert _concl(_with_setdef()) == _concl(_hand_unfolded())


# --------------------------------------------------------------------------- #
# (b) DIFFERENTIAL battery: the evaluator, swept over a box.
# --------------------------------------------------------------------------- #
def test_the_two_readings_agree_at_every_point_of_the_box():
    """The (b) half of the bill.  Same verdict, point for point -- and the
    sweep is over the DECLARED carrier, so every point is one the reading
    actually admits."""
    setd, hand = _concl(_with_setdef()), _concl(_hand_unfolded())
    seen = set()
    for n in range(0, 40):
        a = ME.eval_pred(setd, {"n": n}, {"n": "Nat"}, "Nat")
        b = ME.eval_pred(hand, {"n": n}, {"n": "Nat"}, "Nat")
        assert a == b, (n, a, b)
        seen.add(a)
    # the sweep must be INFORMATIVE: `n in {k | k even} iff n even` is true by
    # construction, so a constant True here is correct -- and the wrong-body
    # plant below is what shows the comparison can separate two readings at all.
    assert seen == {True}


@pytest.mark.parametrize("param,body,elem,point,expect", [
    # the element is a COMPOUND term: substitution puts the whole term in
    ("k", {"op": "even", "args": [{"ref": "k"}]},
     {"op": "+", "args": [{"ref": "m"}, {"lit": 1}]}, {"m": 3}, True),
    ("k", {"op": "even", "args": [{"ref": "k"}]},
     {"op": "+", "args": [{"ref": "m"}, {"lit": 1}]}, {"m": 4}, False),
    # the parameter is used TWICE: substitution must COPY, not alias
    ("k", {"op": "=", "args": [{"op": "*", "args": [{"ref": "k"}, {"ref": "k"}]},
                               {"lit": 9}]},
     {"ref": "m"}, {"m": 3}, True),
    ("k", {"op": "=", "args": [{"op": "*", "args": [{"ref": "k"}, {"ref": "k"}]},
                               {"lit": 9}]},
     {"ref": "m"}, {"m": 4}, False),
    # the parameter is used ZERO times: a constant comprehension is still one
    ("k", {"op": "=", "args": [{"lit": 1}, {"lit": 1}]},
     {"ref": "m"}, {"m": 7}, True),
])
def test_substitution_is_positional_and_copying(param, body, elem, point,
                                                expect):
    """Element MULTIPLICITY and element STRUCTURE, both measured.  A
    substitution that shared one element subtree where the body used the
    parameter twice, or that dropped a compound element down to its head,
    would pass the simple case above and fail here."""
    src = ("Let s be the set given by its body and let m be given. Then the "
           "claim holds.")
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "om", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "m", "type": "Nat"}},
        {"id": "opev", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "even", "carrier": "Nat"}},
        {"id": "sd", "force": "choice", "quote": "",
         "lf": {"kind": "setdef", "name": "s", "param": param, "body": body}},
        {"id": "c", "force": "demand", "quote": "the claim holds",
         "lf": {"kind": "conclusion", "pred": _in(elem, "s")}},
    ]
    pred = _concl(_reading(stmts, src, "s_thm"))
    assert ME.eval_pred(pred, point, {"m": "Nat"}, "Nat") is expect


# --------------------------------------------------------------------------- #
# (b2) SYMBOLIC battery: the dual-solver differential.
# --------------------------------------------------------------------------- #
def test_both_solvers_agree_the_two_readings_are_equivalent():
    """The (b2) half of the bill, and the strongest statement in this file: the
    comprehension reading and the hand-unfolded reading are equivalent for ALL
    n, not merely on the box -- and BOTH solvers say so independently.  The
    obligation is the negation of the biconditional, so `unsat` IS the
    equivalence."""
    setd = MS.render_pred(_concl(_with_setdef()), {"n": "Nat"}, "Nat")
    hand = MS.render_pred(_concl(_hand_unfolded()), {"n": "Nat"}, "Nat")
    smtlib = (
        "(set-logic QF_NIA)\n"
        "(declare-fun n () Int)\n"
        "(assert (>= n 0))\n"
        f"(assert (not (= {setd} {hand})))\n"
        "(check-sat)\n")
    z, c = _dual(smtlib, "unsat")
    assert z == "pass", z          # z3 returned unsat: equivalent for ALL n
    assert c == "pass", c          # ... and cvc5 agrees, independently


def test_the_smt_rendering_is_byte_identical():
    """Stronger than agreement, and cheap: the two readings render to the SAME
    SMT-LIB bytes, because the elimination happened before the mirror ever saw
    them.  A row that had taught the mirror about membership would fail this
    and have to argue instead."""
    assert (MS.render_pred(_concl(_with_setdef()), {"n": "Nat"}, "Nat")
            == MS.render_pred(_concl(_hand_unfolded()), {"n": "Nat"}, "Nat"))


def test_a_setdef_reading_is_smt_representable():
    """The routing half: this row does NOT fall back to enumeration -- there is
    nothing left in the reading that the mirror cannot render."""
    assert MS.smt_representable(_with_setdef()) is True


# --------------------------------------------------------------------------- #
# (c) THE LEAN CONSUMER: byte-identical text and hash.
# --------------------------------------------------------------------------- #
def test_the_compiled_lean_is_byte_identical_to_the_hand_unfolded_reading():
    """The emitter is the one consumer where "same meaning" is not enough to
    check cheaply -- so this checks the stronger thing.  Same `lean_text`, same
    `statement_hash`: the comprehension costs the compiler no rendering rule,
    no `Set`/`Membership` name lookup and no new import pin."""
    a = MC.compile_math_reading(_with_setdef())
    b = MC.compile_math_reading(_hand_unfolded())
    assert a["lean_text"] == b["lean_text"], (a["lean_text"], b["lean_text"])
    assert a["statement_hash"] == b["statement_hash"]
    # and the emitted statement is the one a reader would expect: no set, no
    # membership sign, nothing but the body the comprehension named.
    assert "∀ (n : Nat)" in a["lean_text"]
    assert "∈" not in a["lean_text"], a["lean_text"]
    assert "Set" not in a["lean_text"], a["lean_text"]


# --------------------------------------------------------------------------- #
# (d) THE DIVERGENCE TOOTH: a planted wrong comprehension gets no certificate.
# --------------------------------------------------------------------------- #
def test_unfolding_a_wrong_comprehension_gets_no_certificate():
    """THE tooth for this row (registered in
    buildloop.growth_protocol GROWERS['setdef-comprehension-membership']).

    If `_unfold_mem` substituted a comprehension OTHER than the one the source
    declared, the reading would still parse, evaluate, render and compile --
    every consumer internally consistent, and nothing anywhere raising an
    error.  What it would NOT do is still MEAN what the source said.  So the
    plant is a comprehension whose body is the DUAL of the declared one against
    a conclusion the source asserts, and all three channels witness the
    divergence: the evaluator refutes it pointwise, both solvers refute it
    symbolically, and the emitted Lean bytes differ.

    This is the test that makes every agreement above evidence: without it, the
    comparisons would pass equally well against a broken substitution applied
    consistently on both sides."""
    good = _with_setdef()                              # {k | k even}
    wrong = _with_setdef(body=_t("odd", _ref("k")))    # {k | k odd}
    good_pred, wrong_pred = _concl(good), _concl(wrong)
    assert good_pred != wrong_pred

    # 1. the evaluator refutes the planted reading at every point ...
    for n in range(0, 20):
        assert ME.eval_pred(good_pred, {"n": n}, {"n": "Nat"}, "Nat") is True
        assert ME.eval_pred(wrong_pred, {"n": n}, {"n": "Nat"}, "Nat") is False

    # 2. ... both solvers agree the planted claim is FALSIFIABLE (a model of
    #    its negation exists) while the honest one is not ...
    def obligation(pred):
        return ("(set-logic QF_NIA)\n(declare-fun n () Int)\n"
                "(assert (>= n 0))\n"
                f"(assert (not {MS.render_pred(pred, {'n': 'Nat'}, 'Nat')}))\n"
                "(check-sat)\n")

    z, c = _dual(obligation(good_pred), "unsat")
    assert (z, c) == ("pass", "pass"), (z, c)      # the honest reading holds
    z, c = _dual(obligation(wrong_pred), "sat")
    assert (z, c) == ("pass", "pass"), (z, c)      # the planted one does not

    # 3. ... and the emitted Lean is not the same statement either.
    assert (MC.compile_math_reading(good)["statement_hash"]
            != MC.compile_math_reading(wrong)["statement_hash"])


def test_a_membership_in_an_undeclared_set_cannot_even_be_stated():
    """The cheaper half of the same protection: a membership naming a set no
    `setdef` introduced is refused at the gate rather than silently treated as
    an empty or universal set."""
    with pytest.raises(MR.FragmentMiss) as e:
        _with_setdef(concl=_t("iff", _in(_ref("n"), "b"),
                              _t("even", _ref("n"))))
    assert e.value.missing_kind_guess == "setdef:recursive-body"
    assert "undefined set" in str(e.value)


def test_the_battery_can_fail():
    """The battery's own falsifiability check (the shape every row above uses):
    the comparison machinery separates two readings that really differ, so a
    green above is not the machinery being unable to say no."""
    a = _concl(_with_setdef())
    b = _concl(_with_setdef(body=_t("odd", _ref("k"))))
    assert a != b
    diff = [n for n in range(20)
            if ME.eval_pred(a, {"n": n}, {"n": "Nat"}, "Nat")
            != ME.eval_pred(b, {"n": n}, {"n": "Nat"}, "Nat")]
    assert len(diff) == 20, diff


# --------------------------------------------------------------------------- #
# (e) THE FREEZES, both directions.
# --------------------------------------------------------------------------- #
def _setdef_miss(param, body, concl=None, extra=()):
    src = ("Let s be a set given by its body and let n be given. Then the "
           "claim holds.")
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "on", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Nat"}},
        {"id": "opev", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "even", "carrier": "Nat"}},
    ] + list(extra) + [
        {"id": "sd", "force": "choice", "quote": "",
         "lf": {"kind": "setdef", "name": "s", "param": param, "body": body}},
        {"id": "c", "force": "demand", "quote": "the claim holds",
         "lf": {"kind": "conclusion",
                "pred": concl if concl is not None else _in(_ref("n"), "s")}},
    ]
    with pytest.raises(MR.FragmentMiss) as e:
        _reading(stmts, src, "s_thm")
    return e.value.missing_kind_guess


def test_a_recursive_comprehension_is_first_class_demand():
    """`setdef:recursive-body` -- a comprehension whose body takes membership
    in the set being defined has no finite unfolding, so it is refused as
    DEMAND (it reaches the fragment-miss sink and can raise a future row's
    price) rather than as a malformed reading."""
    assert _setdef_miss("k", _in(_ref("k"), "s")) == "setdef:recursive-body"


def test_a_forward_reference_is_recursion_wearing_a_different_hat():
    """Mutual recursion, refused by the same rule: a body may use only the
    setdefs declared BEFORE it, which is what makes the dependency graph a DAG
    and `_unfold_mem` terminate without an occurs-check."""
    assert _setdef_miss("k", _in(_ref("k"), "later")) == "setdef:recursive-body"


def test_an_open_comprehension_body_is_first_class_demand():
    """`setdef:open-body` -- a body reading an ambient object is not a set, it
    is a hypothesis about one, and the two have different conservativity
    stories."""
    assert _setdef_miss("k", _t("=", _ref("k"), _ref("n"))) == "setdef:open-body"


def test_a_binder_in_a_comprehension_body_is_first_class_demand():
    """`setdef:binder-body` -- what makes the membership substitution
    capture-free BY CONSTRUCTION rather than by a delicate argument."""
    body = _t("=", _t("card",
                      _t("setbuild", {"var": "i"}, _lit(0), _lit(3),
                         _t("even", {"ref": "i"}))),
              _ref("k"))
    assert _setdef_miss("k", body) == "setdef:binder-body"


def test_a_free_set_variable_is_the_tower_class_residue():
    """`set:free-set-variable` -- the thing this row PRICES and does not buy.
    An arbitrary set has no comprehension to substitute, so membership in it
    SURVIVES unfolding: it needs an uninterpreted predicate in the mirror and a
    `Pd` constructor in the reflect slice, which is a different purchase."""
    src = "Let u be a set and let n be given. Then n is in u."
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "on", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Nat"}},
        {"id": "ou", "force": "presupposition", "quote": "u be a set",
         "lf": {"kind": "object", "name": "u", "type": "Nat"}},
        {"id": "c", "force": "demand", "quote": "n is in u",
         "lf": {"kind": "conclusion", "pred": _in(_ref("n"), "u")}},
    ]
    with pytest.raises(MR.FragmentMiss) as e:
        _reading(stmts, src, "u_thm")
    assert e.value.missing_kind_guess == "set:free-set-variable"

    # ... and the same demand however the source SPELLS it: declaring the
    # object at a set TYPE refuses under the identical signal, so the frontier
    # never splits one demand into a row per element type.
    stmts[2]["lf"]["type"] = "Set Nat"
    with pytest.raises(MR.FragmentMiss) as e2:
        _reading(stmts, src, "u_thm")
    assert e2.value.missing_kind_guess == "set:free-set-variable"


def test_a_set_valued_parameter_is_the_powerset_shape():
    """`set:set-valued-param` -- the same wall reached from the other side.  A
    comprehension whose parameter ranges over SETS (`{s | 3 in s}`, the
    09_Sets#problem-017 shape) applies membership to something the reading has
    no body for."""
    assert _setdef_miss("k", _in(_lit(3), "k")) == "set:set-valued-param"


def test_a_set_leaf_is_not_a_value():
    """The sort discipline P2 gave `setbuild` and P8 gave `app`, held here too:
    a set is not a value, so a `{"set": ...}` leaf may appear ONLY as mem's
    second argument and nowhere a term is expected."""
    with pytest.raises(MR.BadMathReading) as e:
        _with_setdef(concl=_t("=", {"set": "a"}, _lit(1)))
    assert "not a value" in str(e.value)


def test_a_wrong_mem_shape_cannot_even_be_stated():
    """mem's second argument must be a set REFERENCE.  A membership whose
    right-hand side is an ordinary term is a malformed reading, refused rather
    than coerced into naming a set."""
    with pytest.raises(MR.BadMathReading) as e:
        _with_setdef(concl=_t("iff",
                              {"op": "mem", "args": [_ref("n"), _ref("n")]},
                              _t("even", _ref("n"))))
    assert "set reference" in str(e.value)


# --------------------------------------------------------------------------- #
# (f) THE PRE-P9 FRAGMENT IS BYTE-UNCHANGED.
# --------------------------------------------------------------------------- #
def test_a_reading_without_a_setdef_is_untouched():
    """The additive half: a reading that names no set parses exactly as it did
    before this purchase, and the P9 machinery is inert on it.  This is what
    makes the row additive rather than a rewrite of the gate."""
    hand = _hand_unfolded()
    assert hand.setdefs() == {}
    assert _concl(hand) == _t("iff", _t("even", _ref("n")),
                              _t("even", _ref("n")))

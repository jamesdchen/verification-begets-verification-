"""Teeth for the F1.1/F-G math-reading gate (`generators/math_reading.py`).

Fast, LLM-free, deterministic.  Drives the ONE owned fixture home
(`tests/fixtures_math_readings.py`, X16) through `parse_math_reading` and pins:

  * every "parse" fixture parses; every ("refuse", stage) fixture is refused at
    the math-reading-gate (a FragmentMiss, carrying `.missing_kind_guess`, for
    the fragment-miss entries);
  * byte-stability: parsing a fixture twice yields structurally-equal
    statements (the gate is a pure function of reading+source);
  * the force trichotomy is enforced per kind (F1.1 force column);
  * the single-source discipline of the LF kind sets (the reading.py pattern);
  * fragment-miss carries the F4 demand data (`missing_kind_guess`).
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import common
from generators.math_reading import (
    parse_math_reading,
    BadMathReading,
    FragmentMiss,
    MathReading,
    MATH_LF_KINDS,
    _MLF_FIELDS,
    _MLF_FORCES,
)
from tests.fixtures_math_readings import (
    FIXTURES,
    FRAGMENT_MISS,
    reading_text,
    source,
)

_PARSE = sorted(n for n, e in FIXTURES.items() if e["expect"] == "parse")
_REFUSE = sorted(n for n, e in FIXTURES.items() if e["expect"] != "parse")


# --- the fixture home itself ------------------------------------------------
def test_fixture_counts():
    """F1 done-when: ten hand-written MathReadings that parse (we ship >= 10),
    plus the refusal fixtures."""
    assert len(FIXTURES) >= 10
    assert len(_PARSE) >= 10
    # the mandated refusals are all present.
    for required in ("bad_fabricated_quote", "bad_choice_quote",
                     "bad_undeclared_ref"):
        assert required in _REFUSE
    assert FRAGMENT_MISS <= set(_REFUSE)


# --- parse / refuse behaviour ----------------------------------------------
@pytest.mark.parametrize("name", _PARSE)
def test_parse_fixture_parses(name):
    mr = parse_math_reading(reading_text(name), source(name))
    assert isinstance(mr, MathReading)
    # F1.1: the asserted content is present as a demanded conclusion.
    assert any(s["lf"]["kind"] == "conclusion" and s["force"] == "demand"
               for s in mr.statements)


@pytest.mark.parametrize("name", _REFUSE)
def test_refuse_fixture_is_refused_at_gate(name):
    stage = FIXTURES[name]["expect"][1]
    assert stage == "math-reading-gate"
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(reading_text(name), source(name))
    if name in FRAGMENT_MISS:
        assert isinstance(ei.value, FragmentMiss)
        assert ei.value.missing_kind_guess is not None


def test_every_parse_quote_occurs_verbatim_in_source():
    """The gate's groundedness contract, stated over the fixture home: every
    demand/presupposition quotes a span literally present in the source, and
    every choice quotes nothing."""
    def _norm(t):
        return " ".join(t.lower().split())
    for name in _PARSE:
        src = _norm(source(name))
        for s in FIXTURES[name]["reading"]["statements"]:
            q = s.get("quote", "")
            if s["force"] in ("demand", "presupposition"):
                assert q.strip(), f"{name}/{s['id']}: non-empty quote required"
                assert _norm(q) in src, f"{name}/{s['id']}: {q!r} not in source"
            else:
                assert not q.strip(), f"{name}/{s['id']}: choice must be empty"


# --- byte-stability: the gate is a pure function ----------------------------
@pytest.mark.parametrize("name", _PARSE)
def test_parse_is_byte_stable(name):
    a = parse_math_reading(reading_text(name), source(name))
    b = parse_math_reading(reading_text(name), source(name))
    # structural equality via canonical re-serialisation of the statements.
    assert common.canonical_json(a.statements) == common.canonical_json(
        b.statements)
    # and the parse did not mutate the fixture's meaning between calls.
    assert a.theorem == b.theorem


# --- force-rule enforcement (F1.1 force column), by mutating a valid fixture -
# even_add carries exactly one of every kind we need to poke: object, operator,
# ambient, quantifier, hypothesis, conclusion.
_FORCE_BASE = "even_add"


def _mutate(base_name, kind, **overrides):
    """Deep-copy `base_name`'s reading, apply `overrides` to the first statement
    of the given lf kind, and return (reading_json, source)."""
    entry = FIXTURES[base_name]
    reading = copy.deepcopy(entry["reading"])
    for st in reading["statements"]:
        if st["lf"]["kind"] == kind:
            for k, v in overrides.items():
                st[k] = v
            break
    else:  # pragma: no cover - guards the base fixture's shape
        raise AssertionError(f"no {kind!r} statement in {base_name!r}")
    return json.dumps(reading), entry["source"]


def test_conclusion_tagged_non_demand_is_refused():
    # conclusion is demand-only; a presupposition conclusion is refused.
    txt, src = _mutate(_FORCE_BASE, "conclusion", force="presupposition")
    with pytest.raises(BadMathReading):
        parse_math_reading(txt, src)


def test_ambient_tagged_non_choice_is_refused():
    # ambient is choice-only; give it a non-empty in-source quote so the refusal
    # is the FORCE rule, not the empty-quote rule.
    txt, src = _mutate(_FORCE_BASE, "ambient",
                       force="presupposition", quote="even")
    with pytest.raises(BadMathReading):
        parse_math_reading(txt, src)


def test_hypothesis_tagged_choice_is_refused():
    # hypothesis is demand-or-presupposition, never choice; empty quote so the
    # refusal is the FORCE rule, not the choice-must-be-empty rule.
    txt, src = _mutate(_FORCE_BASE, "hypothesis", force="choice", quote="")
    with pytest.raises(BadMathReading):
        parse_math_reading(txt, src)


def test_operator_tagged_demand_is_refused():
    # operator is presupposition-or-choice; demand is refused (quote kept, and
    # it is in-source, so the refusal is the FORCE rule).
    txt, src = _mutate(_FORCE_BASE, "operator", force="demand")
    with pytest.raises(BadMathReading):
        parse_math_reading(txt, src)


# --- single-source discipline (the reading.py pattern) ----------------------
def test_lf_kind_sets_are_single_sourced():
    assert set(_MLF_FIELDS) == set(MATH_LF_KINDS) == set(_MLF_FORCES)


def _math_grammar_block():
    """Render the per-kind LF grammar block from MATH_LF_KINDS, mirroring
    buildloop/service_loop.py:_reading_grammar_block (F1.3)."""
    out = []
    for kind, (sig, force) in MATH_LF_KINDS.items():
        out.append(f"  {sig}")
        out.append(f"      (force: {force})")
    return "\n".join(out)


def test_grammar_render_names_every_kind():
    block = _math_grammar_block()
    for kind in MATH_LF_KINDS:
        assert kind in block, f"grammar render omits kind {kind!r}"


# --- fragment-miss is F4 demand data ----------------------------------------
@pytest.mark.parametrize("name", sorted(FRAGMENT_MISS))
def test_fragment_miss_carries_missing_kind_guess(name):
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(reading_text(name), source(name))
    assert ei.value.missing_kind_guess is not None
    assert isinstance(ei.value.missing_kind_guess, str)


# --- B1: mixed-carrier `-` without ambient is refused at the gate ------------
# The eval mirror resolves a `-` node's carrier by its FIRST ref (order-
# sensitive) while the SMT mirror truncates on any Nat operand (order-
# insensitive); on a mixed-carrier `-` with no ambient the two channels
# disagree, so the gate refuses it (§11.0 B1 / §11.5).
def _obj(name, ty):
    return {"id": "o_" + name, "force": "choice", "quote": "",
            "lf": {"kind": "object", "name": name, "type": ty}}


def _concl(sid, pred, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def _minus_reading(a_ty, b_ty, ambient=None):
    stmts = [_obj("a", a_ty), _obj("b", b_ty),
             _concl("c1", {"op": "=", "args": [
                 {"op": "-", "args": [{"ref": "a"}, {"ref": "b"}]}, {"lit": 0}]},
                 "a minus b is zero")]
    if ambient is not None:
        stmts.insert(0, {"id": "amb", "force": "choice", "quote": "",
                         "lf": {"kind": "ambient", "carrier": ambient}})
    doc = {"theorem": "thm", "statements": stmts}
    return json.dumps(doc), "let a and b be given, a minus b is zero"


def test_mixed_carrier_minus_without_ambient_is_refused():
    txt, src = _minus_reading("Nat", "Int")
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(txt, src)
    assert "carrier" in str(ei.value).lower()


def test_mixed_carrier_minus_with_ambient_is_allowed():
    # the fix is scoped to the no-ambient case (§11.0); a declared ambient parses.
    txt, src = _minus_reading("Nat", "Int", ambient="Int")
    parse_math_reading(txt, src)


def test_shared_carrier_minus_without_ambient_is_allowed():
    # a `-` whose operands share one carrier has no divergence, so it parses.
    txt, src = _minus_reading("Int", "Int")
    parse_math_reading(txt, src)


def test_refused_minus_shape_is_exactly_a_mirror_divergence():
    # the refused shape is not arbitrary: bypassing the gate, the eval and SMT
    # carrier rules genuinely disagree on the SAME `-` node.  Reordering the sum
    # in `(n + b) - 5` flips the eval carrier (first ref) while the SMT carrier
    # (any-Nat-operand) is unchanged -- a relational witness that the gate is
    # closing a real divergence, not a phantom one.
    from generators import math_smt, math_eval
    minus = {"op": "-", "args": [{"op": "+", "args": [{"ref": "n"}, {"ref": "b"}]},
                                 {"lit": 5}]}
    reordered = {"op": "-", "args": [{"op": "+", "args": [{"ref": "b"},
                                     {"ref": "n"}]}, {"lit": 5}]}
    objects = {"n": "Int", "b": "Nat"}          # mixed carriers, no ambient
    # eval carrier = first ref in pre-order -> order-sensitive
    assert math_eval._term_carrier(minus, objects, None) == "Int"
    assert math_eval._term_carrier(reordered, objects, None) == "Nat"
    # SMT carrier = any Nat operand -> order-insensitive (Nat both ways)
    assert math_smt._minus_carrier(minus["args"], objects, None) == "Nat"
    assert math_smt._minus_carrier(reordered["args"], objects, None) == "Nat"
    # so eval(minus)=Int disagrees with smt(minus)=Nat: exactly what the gate bars


# --- P3: the Rat carrier's admissibility teeth ------------------------------
# The two planted-violation teeth the `rat-carrier` grower registers
# (buildloop/growth_protocol.GROWERS).  They live here, on the GATE, because
# that is where the two refusals are decided; the differential/lossy batteries
# ride the battery half of the P3 bill.
def _div_reading(ty, ambient=None):
    stmts = [_obj("a", ty),
             _concl("c1", {"op": "=", "args": [
                 {"op": "/", "args": [{"ref": "a"}, {"lit": 2}]}, {"lit": 1}]},
                 "a over two is one")]
    if ambient is not None:
        stmts.insert(0, {"id": "amb", "force": "choice", "quote": "",
                         "lf": {"kind": "ambient", "carrier": ambient}})
    return json.dumps({"theorem": "thm", "statements": stmts}), \
        "let a be given, a over two is one"


def test_div_outside_rat_is_a_fragment_miss():
    """`/` is admissible ONLY at Rat.  At Nat/Int Lean's division FLOORS, and
    modelling a lossy operator is exactly the divergence the fragment refuses
    to buy -- so the reading is a FIRST-CLASS miss (demand data), never a
    silently-floored admission.  At Rat the same shape parses."""
    for ty in ("Nat", "Int"):
        txt, src = _div_reading(ty)
        with pytest.raises(FragmentMiss) as ei:
            parse_math_reading(txt, src)
        assert ei.value.missing_kind_guess == f"operator:/@{ty}"
    parse_math_reading(*_div_reading("Rat"))
    # the divisibility family is the mirror image: refused OVER Rat, by name.
    for word, pred in (("%", {"op": "=", "args": [
                            {"op": "%", "args": [{"ref": "a"}, {"lit": 2}]},
                            {"lit": 1}]}),
                       ("dvd", {"op": "dvd", "args": [{"ref": "a"}, {"lit": 4}]}),
                       ("even", {"op": "even", "args": [{"ref": "a"}]})):
        txt = json.dumps({"theorem": "thm", "statements": [
            _obj("a", "Rat"), _concl("c1", pred, "a over two is one")]})
        with pytest.raises(FragmentMiss) as ei:
            parse_math_reading(txt, "let a be given, a over two is one")
        assert ei.value.missing_kind_guess == f"operator:{word}@Rat"


def test_rat_carrier_mixing_is_refused():
    """rat:no-coercion.  A Rat object may not share a reading with an integer
    one, and an ambient does NOT rescue the mix the way it rescues Nat/Int:
    there is no coercion story in v1, and every mirror renders a reading over
    ONE carrier (the SMT mirror declares one sort; the compiler leans on one
    binder type).  A binder is refused inside a Rat reading for the same
    reason -- its index is pinned Nat."""
    for ambient in (None, "Int", "Rat"):
        txt, src = _minus_reading("Rat", "Int", ambient=ambient)
        with pytest.raises(BadMathReading) as ei:
            parse_math_reading(txt, src)
        assert "rat:no-coercion" in str(ei.value) or "mixes the Rat" in str(ei.value)
    # ... while a single-carrier Rat reading of the same shape parses.
    parse_math_reading(*_minus_reading("Rat", "Rat"))
    # a bigop's Nat index cannot ride into a Rat reading either.
    txt = json.dumps({"theorem": "thm", "statements": [
        _obj("a", "Rat"),
        _concl("c1", {"op": "=", "args": [
            {"op": "bigsum", "args": [{"var": "i"}, {"lit": 0}, {"lit": 3},
                                      {"ref": "i"}]},
            {"ref": "a"}]}, "a minus b is zero")]})
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(txt, "let a and b be given, a minus b is zero")
    assert ei.value.missing_kind_guess == "operator:bigsum@Rat"


# --- P4: the parametric residue carrier `ZMod n` ----------------------------
_ZMOD_SOURCE = "over the integers mod five, three plus four is two"


def _zmod_reading(pred, types=("ZMod 5",), ambient=None,
                  quote="three plus four is two", extra=()):
    """A one-conclusion reading whose objects carry the given types, in order
    (a, b, ...).  Every refusal below differs from the parsing case in exactly
    one place, so each test names one rule."""
    names = "abc"
    stmts = [_obj(names[i], ty) for i, ty in enumerate(types)]
    stmts.extend(extra)
    stmts.append(_concl("c1", pred, quote))
    if ambient is not None:
        stmts.insert(0, {"id": "amb", "force": "choice", "quote": "",
                         "lf": {"kind": "ambient", "carrier": ambient}})
    return json.dumps({"theorem": "thm", "statements": stmts}), _ZMOD_SOURCE


def test_zmod_literal_modulus_parses():
    # the admitted shape: one literal modulus, `+ * - ^` and `= !=` only.
    txt, src = _zmod_reading(
        {"op": "=", "args": [
            {"op": "+", "args": [{"ref": "a"}, {"lit": 4}]}, {"lit": 2}]})
    r = parse_math_reading(txt, src)
    assert r.objects() == {"a": "ZMod 5"}
    # the ambient may carry the same residue carrier (a choice, quoting nothing)
    txt2, src2 = _zmod_reading(
        {"op": "!=", "args": [
            {"op": "-", "args": [{"ref": "a"}, {"lit": 4}]}, {"lit": 0}]},
        ambient="ZMod 5")
    assert parse_math_reading(txt2, src2).ambient_carrier() == "ZMod 5"


def test_symbolic_modulus_is_a_fragment_miss():
    """The v1 modulus freeze, and the SPLIT that keeps its two demands apart.

    A symbolic modulus (`ZMod n`) and the degenerate `ZMod 0` (which Lean reads
    as the integers, not a finite quotient) are DIFFERENT demands, so they carry
    different signals -- collapsing them into one `carrier:ZMod ...` bin would
    let either one masquerade as evidence for the other."""
    for ty, guess in (("ZMod n", "carrier:zmod-symbolic-modulus"),
                      ("ZMod k", "carrier:zmod-symbolic-modulus"),
                      ("ZMod 0", "carrier:zmod-zero-modulus"),
                      ("ZMod 00", "carrier:zmod-zero-modulus")):
        txt, src = _zmod_reading(
            {"op": "=", "args": [{"ref": "a"}, {"lit": 0}]}, types=(ty,))
        with pytest.raises(FragmentMiss) as ei:
            parse_math_reading(txt, src)
        assert ei.value.missing_kind_guess == guess, ty
    # the same split holds at the ambient slot (a carrier claim either way)
    txt, src = _zmod_reading({"op": "=", "args": [{"ref": "a"}, {"lit": 0}]},
                             types=("ZMod 5",), ambient="ZMod n")
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(txt, src)
    assert ei.value.missing_kind_guess == "carrier:zmod-symbolic-modulus"
    # a carrier that is not ZMod-shaped keeps the generic signal it always had
    txt, src = _zmod_reading({"op": "=", "args": [{"ref": "a"}, {"lit": 0}]},
                             types=("Real",))
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(txt, src)
    assert ei.value.missing_kind_guess == "carrier:Real"


def test_order_and_mod_family_at_zmod_are_fragment_misses():
    # a congruence class carries no order and no division: each refused op is
    # its own priced signal, never a malformation.
    for op in ("<=", "<"):
        txt, src = _zmod_reading({"op": op, "args": [{"ref": "a"}, {"lit": 2}]})
        with pytest.raises(FragmentMiss) as ei:
            parse_math_reading(txt, src)
        assert ei.value.missing_kind_guess == f"operator:{op}@ZMod 5"
    txt, src = _zmod_reading(
        {"op": "=", "args": [
            {"op": "%", "args": [{"ref": "a"}, {"lit": 2}]}, {"lit": 0}]})
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(txt, src)
    assert ei.value.missing_kind_guess == "operator:%@ZMod 5"
    # lexicon words refuse through the SAME channel that has always refused an
    # unsupported (word, carrier) pair -- no new mechanism needed.
    binding = {"id": "op1", "force": "choice", "quote": "",
               "lf": {"kind": "operator", "word": "dvd", "carrier": "ZMod 5"}}
    txt, src = _zmod_reading(
        {"op": "dvd", "args": [{"ref": "a"}, {"lit": 2}]}, extra=(binding,))
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(txt, src)
    assert ei.value.missing_kind_guess == "operator:dvd@ZMod 5"


def test_binder_inside_a_zmod_reading_is_a_fragment_miss():
    # P1 pins a bound index to carrier Nat, so a fold inside a residue reading
    # would mix carriers behind every walker's back.
    txt, src = _zmod_reading(
        {"op": "=", "args": [
            {"op": "bigsum", "args": [{"var": "i"}, {"lit": 0}, {"lit": 3},
                                      {"ref": "a"}]},
            {"lit": 2}]})
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(txt, src)
    assert ei.value.missing_kind_guess == "zmod:binder-index-carrier"


def test_mixed_moduli_and_mixed_carriers_refuse():
    # two moduli are two unrelated carriers ...
    txt, src = _zmod_reading(
        {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]},
        types=("ZMod 5", "ZMod 7"))
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(txt, src)
    assert "residue carriers" in str(ei.value)
    # ... and a residue class is not an integer, with or without an ambient
    # (the fragment has no coercion, so an ambient cannot rescue the mix).
    for ambient in (None, "Int"):
        txt, src = _zmod_reading(
            {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]},
            types=("ZMod 5", "Int"), ambient=ambient)
        with pytest.raises(BadMathReading):
            parse_math_reading(txt, src)


def test_zmod_carrier_rule_is_reading_wide_not_per_pred():
    """The subtle shape the per-pred reading of the rule would let through: no
    single pred mixes carriers, but the reading declares two.

    Both mirrors resolve the residue modulus from the reading's OBJECT MAP
    (`math_eval._zmod_carrier_of` / `math_smt._zmod_carrier`) -- they must, or
    an all-literal term inside a residue reading would fall to the Int rule --
    so a reading like this one would have its INT conclusion silently reduced
    mod 5.  The gate refuses the shape rather than let that divergence run."""
    hyp = {"id": "h1", "force": "presupposition", "quote": "three plus four",
           "lf": {"kind": "hypothesis",
                  "pred": {"op": "=", "args": [{"ref": "a"}, {"lit": 1}]}}}
    stmts = [_obj("a", "ZMod 5"), _obj("b", "Int"), hyp,
             _concl("c1", {"op": "=", "args": [{"ref": "b"}, {"lit": 1}]},
                    "three plus four is two")]
    src = "three plus four is two"
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(
            json.dumps({"theorem": "thm", "statements": stmts}), src)
    assert "residue carrier" in str(ei.value)


# --- P6: the connectives' NNF admissibility teeth ---------------------------
# The GATE half of the `connective-node-class` bill
# (buildloop/growth_protocol.GROWERS).  P6 admits `not` and `iff` precisely
# because neither has to be REPRESENTED -- `iff` desugars into two `implies`
# and `not` pushes to an atom's dual -- so the one thing the gate owes is a
# refusal for the negations that cannot be pushed.  The differential /
# planted-lossy batteries ride the battery half (tests/test_connective_battery).
def _conn_reading(pred, ty="Int", quote="the asserted claim"):
    stmts = [_obj("a", ty), _obj("b", ty), _concl("c1", pred, quote)]
    return json.dumps({"theorem": "thm", "statements": stmts}), quote


def test_connectives_admit_not_and_iff():
    """The positive half: both new words parse, at every arity the grammar
    gives them, and nested inside the pre-existing connectives."""
    eq = {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]}
    le = {"op": "<=", "args": [{"ref": "a"}, {"ref": "b"}]}
    for pred in ({"op": "not", "args": [eq]},
                 {"op": "iff", "args": [eq, le]},
                 {"op": "not", "args": [{"op": "not", "args": [le]}]},
                 {"op": "and", "args": [{"op": "not", "args": [eq]},
                                        {"op": "iff", "args": [le, eq]}]},
                 {"op": "implies", "args": [eq, {"op": "not", "args": [le]}]}):
        parse_math_reading(*_conn_reading(pred))


def test_connective_arity_is_enforced():
    """`not` is unary and `iff` binary -- a malformation, not demand data, so
    these are plain BadMathReadings and never FragmentMisses (a width the
    fragment has no meaning for is not a missing primitive)."""
    eq = {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]}
    le = {"op": "<=", "args": [{"ref": "a"}, {"ref": "b"}]}
    for pred in ({"op": "not", "args": [eq, le]},
                 {"op": "iff", "args": [eq]},
                 {"op": "iff", "args": [eq, le, eq]}):
        with pytest.raises(BadMathReading) as ei:
            parse_math_reading(*_conn_reading(pred))
        assert not isinstance(ei.value, FragmentMiss)


def test_negated_dvd_is_a_fragment_miss():
    """THE NAMED LIMIT OF THE NNF ARGUMENT, and the reason it is a limit rather
    than a gap.  Every comparison/parity atom has a dual IN the fragment, so a
    negation reaching one becomes another atom the fragment already carries.
    `dvd` has none -- "a does not divide b" is not any other atom here -- and
    leaving the negation where it stands would need a negation NODE, i.e. a
    constructor, i.e. the tower-class purchase §4 P6 declared and this one
    deliberately did not make.  So it refuses BY NAME, carrying the demand.

    `coprime` is the same shape and the reason the signal is a FAMILY rather
    than one string: non-coprimality is not coprimality of anything either, and
    naming only `dvd` would have hidden a second missing dual behind the first.
    """
    dvd = {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}
    cop = {"op": "coprime", "args": [{"ref": "a"}, {"ref": "b"}]}
    for pred, want in ((dvd, "not:dvd-no-dual"), (cop, "not:coprime-no-dual")):
        with pytest.raises(FragmentMiss) as ei:
            parse_math_reading(*_conn_reading({"op": "not", "args": [pred]},
                                              ty="Nat"))
        assert ei.value.missing_kind_guess == want
    # the negation does not have to be ADJACENT: De Morgan carries it down
    # through and/or, and through the consequent of a negated implication.
    eq = {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]}
    for pred in ({"op": "not", "args": [{"op": "and", "args": [eq, dvd]}]},
                 {"op": "not", "args": [{"op": "or", "args": [dvd, eq]}]},
                 {"op": "not", "args": [
                     {"op": "implies", "args": [eq, dvd]}]},
                 {"op": "not", "args": [{"op": "iff", "args": [eq, dvd]}]}):
        with pytest.raises(FragmentMiss) as ei:
            parse_math_reading(*_conn_reading(pred, ty="Nat"))
        assert ei.value.missing_kind_guess == "not:dvd-no-dual"


def test_positive_dvd_under_implies_and_iff_still_parses():
    """THE BYTE-UNCHANGED TOOTH, and the one that decides whether this purchase
    is additive at all.  `Pd` carries `pand`/`por`/`pimp` as CONSTRUCTORS, so a
    POSITIVE implication needs no push and its antecedent is not in negative
    position for this freeze -- a classical-NNF reading (`a -> b` == `not a or
    b`) would have retroactively refused every committed reading whose
    hypothesis divides something.  A purchase that re-verdicts yesterday's
    readings is not additive, whatever else it is."""
    dvd = {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}
    eq = {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]}
    for pred in ({"op": "implies", "args": [dvd, eq]},
                 {"op": "implies", "args": [eq, dvd]},
                 {"op": "iff", "args": [dvd, eq]},
                 {"op": "not", "args": [
                     {"op": "implies", "args": [dvd, eq]}]},
                 {"op": "and", "args": [dvd, {"op": "not", "args": [eq]}]}):
        parse_math_reading(*_conn_reading(pred, ty="Nat"))


def test_atom_duals_are_the_fragments_own_atoms():
    """The `conserve` role, checked as arithmetic rather than believed as
    prose: every dual named is an atom the fragment already admits, and the
    ORDER atoms swap their arguments (`not (a <= b)` is `b < a`, never
    `a < b`).  Getting that swap backwards is a silent lie about the reading,
    so it is pinned pointwise against the evaluator further down the bill."""
    from generators.math_reading import _ATOM_DUALS, _dual_atom, _ATOM_OPS
    assert set(_ATOM_DUALS) <= _ATOM_OPS
    for op, (dual, swap) in _ATOM_DUALS.items():
        assert dual in _ATOM_OPS, op
        assert _ATOM_DUALS[dual][0] == op, f"{op}/{dual} are not a dual PAIR"
        assert _ATOM_DUALS[dual][1] is swap
    # the atoms with no dual are exactly the two the receipt names
    assert _ATOM_OPS - set(_ATOM_DUALS) == {"dvd", "coprime"}
    a, b = {"ref": "a"}, {"ref": "b"}
    assert _dual_atom({"op": "<=", "args": [a, b]}) == \
        {"op": "<", "args": [b, a]}
    assert _dual_atom({"op": "=", "args": [a, b]}) == \
        {"op": "!=", "args": [a, b]}
    assert _dual_atom({"op": "dvd", "args": [a, b]}) is None


def test_negation_inside_a_setbuild_filter_is_checked():
    """P2 lets a pred hide a whole second pred under `card`'s set argument, so
    a walk that only followed connectives would never reach it.  A negated
    `dvd` in a filter is the same miss it is anywhere else -- the freeze is a
    property of the fragment, not of where in the tree it is written."""
    filt = {"op": "not", "args": [
        {"op": "dvd", "args": [{"lit": 3}, {"ref": "i"}]}]}
    card = {"op": "card", "args": [
        {"op": "setbuild", "args": [{"var": "i"}, {"lit": 1}, {"lit": 9},
                                    filt]}]}
    pred = {"op": "=", "args": [card, {"lit": 6}]}
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(*_conn_reading(pred, ty="Nat"))
    assert ei.value.missing_kind_guess == "not:dvd-no-dual"
    # the same filter with a dualisable atom parses (six of 1..9 are not 3-ish)
    ok = {"op": "not", "args": [
        {"op": "even", "args": [{"ref": "i"}]}]}
    card_ok = {"op": "card", "args": [
        {"op": "setbuild", "args": [{"var": "i"}, {"lit": 1}, {"lit": 9}, ok]}]}
    parse_math_reading(
        *_conn_reading({"op": "=", "args": [card_ok, {"lit": 5}]}, ty="Nat"))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))

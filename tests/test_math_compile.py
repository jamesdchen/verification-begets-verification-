"""Tests for the F1.2 compiler (generators/math_compile.py).

MathReadings are built INLINE via parse_math_reading (no shared fixture import;
the fixture home may not exist during this run).  We assert the F-B contract:
byte-stability, canonical structure, provenance coverage, carrier resolution.
"""
import json

import pytest

from generators.math_reading import parse_math_reading
from generators.math_compile import compile_math_reading


def _mk(theorem, statements, source):
    return parse_math_reading(json.dumps({"theorem": theorem,
                                          "statements": statements}), source)


# --- inline readings --------------------------------------------------------
def _dvd_nat():
    """∀ (a b : Nat), a ∣ b → a ∣ (b * b)   -- divisibility over Nat."""
    src = "for all natural numbers a and b if a divides b then a divides b times b"
    return _mk("dvd_example", [
        {"id": "o1", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "a", "type": "Nat"}},
        {"id": "o2", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "b", "type": "Nat"}},
        {"id": "q1", "force": "demand", "quote": "for all natural numbers a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h1", "force": "presupposition", "quote": "a divides b",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}},
        {"id": "c1", "force": "demand", "quote": "a divides b times b",
         "lf": {"kind": "conclusion",
                "pred": {"op": "dvd", "args": [
                    {"ref": "a"},
                    {"op": "*", "args": [{"ref": "b"}, {"ref": "b"}]}]}}},
    ], src)


def _even_int():
    """∀ (n : Int), Even ((n ^ 2) - n)  -- Int subtraction + ^ + parity."""
    src = "for every integer n the number n squared minus n is even"
    return _mk("even_int", [
        {"id": "on", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "qn", "force": "demand", "quote": "for every integer n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "cc", "force": "demand", "quote": "n squared minus n is even",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [
                    {"op": "-", "args": [
                        {"op": "^", "args": [{"ref": "n"}, {"lit": 2}]},
                        {"ref": "n"}]}]}}},
    ], src)


def _gcd_coprime():
    """∀ (a b : Nat), Nat.Coprime a b → Nat.gcd a b = 1  -- carrier-indexed names."""
    src = ("for all natural numbers a and b if a is coprime to b then the gcd "
           "of a and b equals one")
    return _mk("gcd_coprime", [
        {"id": "o1", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "a", "type": "Nat"}},
        {"id": "o2", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "b", "type": "Nat"}},
        {"id": "q1", "force": "demand", "quote": "for all natural numbers a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h1", "force": "presupposition", "quote": "a is coprime to b",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "coprime", "args": [{"ref": "a"}, {"ref": "b"}]}}},
        {"id": "c1", "force": "demand", "quote": "the gcd of a and b equals one",
         "lf": {"kind": "conclusion",
                "pred": {"op": "=", "args": [
                    {"op": "gcd", "args": [{"ref": "a"}, {"ref": "b"}]},
                    {"lit": 1}]}}},
    ], src)


def _odd_leading():
    """No quantifier statement: the referenced object is bound by a LEADING ∀."""
    src = "m plus one is odd"
    return _mk("odd_leading", [
        {"id": "om", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "m", "type": "Nat"}},
        {"id": "c1", "force": "demand", "quote": "m plus one is odd",
         "lf": {"kind": "conclusion",
                "pred": {"op": "odd", "args": [
                    {"op": "+", "args": [{"ref": "m"}, {"lit": 1}]}]}}},
    ], src)


_ALL = [_dvd_nat, _even_int, _gcd_coprime, _odd_leading]


# --- byte-stability ---------------------------------------------------------
@pytest.mark.parametrize("mk", _ALL)
def test_byte_stable(mk):
    r = mk()
    a = compile_math_reading(r)
    b = compile_math_reading(r)
    assert a["lean_text"] == b["lean_text"]
    assert a["statement_hash"] == b["statement_hash"]
    # a fresh, independently-parsed but identical reading hashes identically.
    c = compile_math_reading(mk())
    assert c["statement_hash"] == a["statement_hash"]


def test_hash_is_over_lean_text_bytes_only():
    import hashlib
    art = compile_math_reading(_dvd_nat())
    assert art["statement_hash"] == hashlib.sha256(
        art["lean_text"].encode("utf-8")).hexdigest()


# --- structural shape -------------------------------------------------------
@pytest.mark.parametrize("mk", _ALL)
def test_theorem_envelope(mk):
    t = compile_math_reading(mk())["lean_text"]
    assert t.startswith("theorem ")
    assert t.endswith(":= sorry")
    assert "∀" in t


def test_divisibility_symbol():
    assert "∣" in compile_math_reading(_dvd_nat())["lean_text"]


def test_parity_symbol():
    t = compile_math_reading(_even_int())["lean_text"]
    assert ("Even" in t) or ("Odd" in t)
    assert "Even" in t
    assert "Odd" in compile_math_reading(_odd_leading())["lean_text"]


def test_int_subtraction_and_power():
    t = compile_math_reading(_even_int())["lean_text"]
    assert "-" in t            # Int subtraction, D8
    assert "^" in t            # literal-exponent power, D10


def test_carrier_indexed_names():
    t = compile_math_reading(_gcd_coprime())["lean_text"]
    assert "Nat.gcd" in t
    assert "Nat.Coprime" in t


def test_hypothesis_chain_and_arrow():
    t = compile_math_reading(_dvd_nat())["lean_text"]
    assert "→" in t            # hypothesis chained into conclusion


# --- carrier resolution -----------------------------------------------------
def test_nat_binder():
    assert ": Nat" in compile_math_reading(_dvd_nat())["lean_text"]
    assert ": Int" not in compile_math_reading(_dvd_nat())["lean_text"]


def test_int_binder():
    assert ": Int" in compile_math_reading(_even_int())["lean_text"]
    assert ": Nat" not in compile_math_reading(_even_int())["lean_text"]


# --- provenance -------------------------------------------------------------
@pytest.mark.parametrize("mk", _ALL)
def test_provenance_covers_contributors(mk):
    r = mk()
    prov = compile_math_reading(r)["provenance"]
    all_ids = set()
    for v in prov.values():
        all_ids.update(v)

    # every hypothesis and conclusion id appears in some provenance value
    for s in r.statements:
        if s["lf"]["kind"] in ("hypothesis", "conclusion"):
            assert s["id"] in all_ids, s["id"]

    # every referenced object has a binder key
    referenced = set()
    for s in r.statements:
        if s["lf"]["kind"] in ("hypothesis", "conclusion"):
            from generators.math_compile import _pred_refs
            referenced.update(_pred_refs(s["lf"]["pred"]))
    for name in referenced:
        assert f"binder.{name}" in prov, name

    # keyed hyp/conclusion/quantifier provenance points back at itself
    for s in r.statements:
        k = s["lf"]["kind"]
        if k == "hypothesis":
            assert prov[f"hyp.{s['id']}"] == [s["id"]]
        elif k == "conclusion":
            assert prov[f"conclusion.{s['id']}"] == [s["id"]]
        elif k == "quantifier":
            assert prov[f"quantifier.{s['id']}"] == [s["id"]]


def test_leading_forall_binds_unquantified_object():
    # _odd_leading has NO quantifier statement; m must still be bound by ∀.
    art = compile_math_reading(_odd_leading())
    assert art["lean_text"].startswith("theorem odd_leading : ∀ (m : Nat),")
    assert art["provenance"]["binder.m"] == ["om"]


# --- exact-text goldens (guards the canonical pretty-printer) ---------------
def test_exact_texts():
    assert (compile_math_reading(_dvd_nat())["lean_text"] ==
            "theorem dvd_example : ∀ (a : Nat) (b : Nat), "
            "(a ∣ b) → (a ∣ (b * b)) := sorry")
    assert (compile_math_reading(_even_int())["lean_text"] ==
            "theorem even_int : ∀ (n : Int), (Even ((n ^ 2) - n)) := sorry")
    assert (compile_math_reading(_gcd_coprime())["lean_text"] ==
            "theorem gcd_coprime : ∀ (a : Nat) (b : Nat), "
            "(Nat.Coprime a b) → ((Nat.gcd a b) = 1) := sorry")
    assert (compile_math_reading(_odd_leading())["lean_text"] ==
            "theorem odd_leading : ∀ (m : Nat), (Odd (m + 1)) := sorry")

"""WP-F teeth for planner/math_choices.py (F-INT-6, closes G6).

Every assertion is RELATIONAL (ordering / membership / equality of structure),
never an absolute-constant DL value (E5/H52).  Fixtures are hand-authored HERE
(the X16 discipline: each WP authors bespoke fixtures in its own test file); no
Lean and no LLM is touched -- the whole search is decidable arithmetic over the
F-G fragment, and cvc5 may be absent (honest degradation to the enumeration
channel).
"""
import copy
import json

import pytest

from planner.math_choices import (
    search_carrier, searchable_slots, apply_carrier_assignment,
    NonChoiceForceError)


# --------------------------------------------------------------- fixtures
def _envelope(source, theorem, statements):
    return json.dumps({"source": source,
                       "reading": {"theorem": theorem, "statements": statements}})


def _nat_vs_int_reading():
    """The planted N-vs-Z case built on OBJECT-TYPE substitution (⚠FI-6):
    objects a, b are CHOICE-force (searchable); hypothesis ``a < b``; conclusion
    ``(a - b) + b = a``.  Over Int subtraction is real so the conclusion always
    holds; over Nat it truncates (``a - b = 0`` when ``a < b``) so the conclusion
    is FALSE on every hypothesis-satisfying instance -- the wrong carrier is
    refuted by the instance gate."""
    source = ("If a is less than b then subtracting b from a and adding b "
              "back gives a.")
    statements = [
        {"id": "oa", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "subtracting b from a",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h", "force": "presupposition", "quote": "a is less than b",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "<", "args": [{"ref": "a"}, {"ref": "b"}]}}},
        {"id": "c", "force": "demand",
         "quote": "subtracting b from a and adding b back gives a",
         "lf": {"kind": "conclusion",
                "pred": {"op": "=", "args": [
                    {"op": "+", "args": [
                        {"op": "-", "args": [{"ref": "a"}, {"ref": "b"}]},
                        {"ref": "b"}]},
                    {"ref": "a"}]}}},
    ]
    return source, "sub_add_restores", statements


def _coprime_reading():
    """``coprime`` is Nat-only in MATH_OPERATORS; a CHOICE-force operator bound to
    it, searched to Int, is an out-of-table (word, carrier) -- a fragment-miss,
    not a crash.  Objects are presupposition-force so the operator is the lone
    searchable slot."""
    source = "If a and b are coprime then a and b are coprime."
    statements = [
        {"id": "oa", "force": "presupposition", "quote": "a and b",
         "lf": {"kind": "object", "name": "a", "type": "Nat"}},
        {"id": "ob", "force": "presupposition", "quote": "a and b",
         "lf": {"kind": "object", "name": "b", "type": "Nat"}},
        {"id": "op", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "coprime", "carrier": "Nat"}},
        {"id": "q", "force": "presupposition", "quote": "a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h", "force": "presupposition", "quote": "a and b are coprime",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "coprime", "args": [{"ref": "a"}, {"ref": "b"}]}}},
        {"id": "c", "force": "demand", "quote": "a and b are coprime",
         "lf": {"kind": "conclusion",
                "pred": {"op": "coprime", "args": [{"ref": "a"}, {"ref": "b"}]}}},
    ]
    return source, "coprime_refl", statements


def _no_choice_reading():
    """Every carrier is presupposition/demand-force: no formalization freedom, so
    the search yields exactly one candidate (the reading itself)."""
    source = "Every even integer n is even."
    statements = [
        {"id": "oa", "force": "presupposition", "quote": "even integer n",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "q", "force": "presupposition", "quote": "Every even integer n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "h", "force": "presupposition", "quote": "even integer n",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "even", "args": [{"ref": "n"}]}}},
        {"id": "c", "force": "demand", "quote": "n is even",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "n"}]}}},
    ]
    return source, "even_is_even", statements


_FROZEN_KEYS = {"assignment", "certifies", "witness", "boundary_behavior",
                "statement_hash"}


def _find(results, assignment):
    for i, r in enumerate(results):
        if r["assignment"] == assignment:
            return i, r
    raise AssertionError(f"no entry for assignment {assignment}")


# ------------------------------------------------------------- F2 tooth 1
def test_wrong_carrier_refuted_and_ranked_below_certifying():
    """The wrong (Nat) object-type assignment is refuted by the instance gate
    and ranked BELOW the certifying (Int) one -- the whole point of the search."""
    source, thm, stmts = _nat_vs_int_reading()
    results = search_carrier(_envelope(source, thm, stmts), bound=8)

    # the top-ranked candidate certifies.
    assert results[0]["certifies"] is True

    i_int, int_int = _find(results, {"oa": "Int", "ob": "Int"})
    i_nat, nat_nat = _find(results, {"oa": "Nat", "ob": "Nat"})

    # the all-Int reading certifies; the all-Nat reading is refused ...
    assert int_int["certifies"] is True
    assert nat_nat["certifies"] is False
    # ... by a concrete refuting witness (an instance the hypotheses admit but
    # the truncated conclusion rejects) ...
    assert nat_nat["witness"] is not None
    assert isinstance(nat_nat["witness"], dict) and set(nat_nat["witness"]) == {"a", "b"}
    assert nat_nat["witness"]["a"] < nat_nat["witness"]["b"]     # hypothesis a<b holds
    # ... and it is ranked strictly below the certifying assignment.
    assert i_int < i_nat
    # every non-certifying candidate sorts after every certifying one.
    ranks = [r["certifies"] for r in results if "certifies" in r]
    assert ranks == sorted(ranks, key=lambda c: 0 if c else 1)


# ------------------------------------------------------------- F2 tooth 2
def test_searching_a_non_choice_force_carrier_raises():
    """A demand- or presupposition-force type/carrier is NEVER overridden -- the
    trichotomy is load-bearing."""
    source, thm, stmts = _nat_vs_int_reading()
    doc = {"theorem": thm, "statements": stmts}

    # 'h' is a presupposition-force hypothesis: not a searchable carrier slot.
    with pytest.raises(NonChoiceForceError):
        apply_carrier_assignment(doc, {"h": "Nat"})

    # a presupposition-force OBJECT (fixture with presupposition objects) also
    # refuses -- force, not kind, gates searchability.
    _s2, _t2, stmts2 = _coprime_reading()
    doc2 = {"theorem": _t2, "statements": stmts2}
    with pytest.raises(NonChoiceForceError):
        apply_carrier_assignment(doc2, {"oa": "Int"})

    # an unknown id also refuses (never a silent no-op).
    with pytest.raises(NonChoiceForceError):
        apply_carrier_assignment(doc, {"nope": "Int"})


# ------------------------------------------------------------- F2 tooth 3
def test_out_of_table_word_carrier_yields_fragment_miss():
    """A (word, carrier) outside MATH_OPERATORS (coprime@Int) is DEMAND DATA:
    a fragment-miss entry, not a crash."""
    source, thm, stmts = _coprime_reading()
    results = search_carrier(_envelope(source, thm, stmts), bound=8)

    _i, miss = _find(results, {"op": "Int"})
    assert set(miss) == {"assignment", "fragment_miss"}     # distinct entry shape
    assert "coprime" in miss["fragment_miss"]
    assert "certifies" not in miss                          # never a gated verdict

    _j, nat = _find(results, {"op": "Nat"})
    assert nat["certifies"] is True
    # the in-fragment (certifying) candidate ranks before the fragment-miss.
    assert results.index(nat) < results.index(miss)


# ------------------------------------------------------------- F2 tooth 4
def test_original_reading_object_is_never_mutated():
    """Every candidate is a fresh json deep copy; the caller's inputs are
    untouched after the search."""
    source, thm, stmts = _nat_vs_int_reading()
    env = _envelope(source, thm, stmts)
    env_before = env
    stmts_before = copy.deepcopy(stmts)

    search_carrier(env, bound=8)

    assert env == env_before                    # the json string is immutable data
    assert stmts == stmts_before                # no aliasing into the fixture

    # apply_carrier_assignment returns a copy and leaves its input alone.
    doc = {"theorem": thm, "statements": stmts}
    doc_before = copy.deepcopy(doc)
    out = apply_carrier_assignment(doc, {"oa": "Nat"})
    assert doc == doc_before
    assert out["statements"][0]["lf"]["type"] == "Nat"
    assert doc["statements"][0]["lf"]["type"] == "Int"


# ------------------------------------------------------------- ranking / shape
def test_entries_carry_the_frozen_keys_and_are_evidence_only():
    source, thm, stmts = _nat_vs_int_reading()
    results = search_carrier(_envelope(source, thm, stmts), bound=8)
    assert results, "the search enumerates at least one candidate"
    for r in results:
        if "fragment_miss" in r:
            assert set(r) == {"assignment", "fragment_miss"}
        else:
            assert set(r) == _FROZEN_KEYS
            assert isinstance(r["certifies"], bool)
            assert isinstance(r["boundary_behavior"], list)
            # evidence-only (L3): a plain dict ranking, never a Certificate.
            assert not hasattr(r, "channels")


def test_certifying_candidates_sorted_by_compiled_statement_dl():
    """Within the certifying block, entries are ordered by ascending
    compiled-statement DL (relational: the recomputed DL is nondecreasing)."""
    from generators.math_reading import parse_math_reading, split_envelope
    from generators.math_compile import compile_math_reading

    source, thm, stmts = _nat_vs_int_reading()
    env = _envelope(source, thm, stmts)
    _inner, src = split_envelope(env)
    results = search_carrier(env, bound=8)

    def dl_of(entry):
        doc = {"theorem": thm, "statements": copy.deepcopy(stmts)}
        for s in doc["statements"]:
            if s["id"] in entry["assignment"]:
                field = "type" if s["lf"]["kind"] == "object" else "carrier"
                s["lf"][field] = entry["assignment"][s["id"]]
        reading = parse_math_reading(json.dumps(doc), src)
        return len(compile_math_reading(reading)["lean_text"])

    certifying = [r for r in results if r.get("certifies")]
    dls = [dl_of(r) for r in certifying]
    assert dls == sorted(dls)


def test_no_choice_freedom_yields_single_candidate():
    source, thm, stmts = _no_choice_reading()
    results = search_carrier(_envelope(source, thm, stmts), bound=8)
    assert searchable_slots({"theorem": thm, "statements": stmts}) == []
    assert len(results) == 1
    assert results[0]["assignment"] == {}
    assert results[0]["certifies"] is True


def test_search_is_deterministic():
    source, thm, stmts = _nat_vs_int_reading()
    env = _envelope(source, thm, stmts)
    a = search_carrier(env, bound=8)
    b = search_carrier(env, bound=8)
    assert a == b


def test_searchable_slots_selects_only_choice_force_carriers():
    source, thm, stmts = _nat_vs_int_reading()
    slots = searchable_slots({"theorem": thm, "statements": stmts})
    ids = [sid for sid, _f, _c in slots]
    assert ids == ["oa", "ob"]                 # the two choice-force objects only
    # the presupposition hypothesis and demand conclusion are not slots.
    assert "h" not in ids and "c" not in ids

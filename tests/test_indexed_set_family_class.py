"""INDEXED SET FAMILIES over the CURRENT fragment: why `indexed-set-family`
is filed apart from `free-set-variable`, measured rather than argued.

THE QUESTION THIS FILE ANSWERS MECHANICALLY.  C3 cycle 32 took the first
carleson batch and two of its five subjects -- `disjoint-row-support` ("The
sets \\(E_j\\), \\(1 \\le j \\le 2^n\\) are pairwise disjoint.") and
`pairwise-disjoint` (tiles whose supports meet coincide) -- refused at a set
the source gives no comprehension for.  The cheap filing was
`free-set-variable`, the signal P9 already carries for "an arbitrary `U`",
and `refusal-set-carrier` already prices it.  The cycle-27/29 lesson says a
word coarser than its cause PROMISES A RETURN IT CANNOT MAKE, so the
separation is settled here against the repo's own machinery instead of by
preference.

THE FINDING, in the order the tests below establish it.

  (1) THE FAMILY READING IS REFUSED STRUCTURALLY, NOT FOR MISSING
      VOCABULARY.  P9's `setdef` body is CLOSED OVER ITS PARAMETER by
      construction -- the gate says so in its own words, and gives the
      reason: a membership site must be eliminable by substitution alone.
      A set that varies with a free index needs a body mentioning that
      index, so NO set-carrier purchase expresses it: the wall is the
      elimination discipline, not the carrier whitelist.

  (2) THE NON-INDEXED READING IS REFUTED BY THE BOX.  Read with sets that
      do NOT vary with their index -- exactly the shape a
      free-set-variable / set-valued-param retirement would supply -- both
      subjects GATE CLEANLY and are then FALSE, because two sets that do
      not vary may meet without their indices agreeing.  So the coarse
      filing would return these subjects to `ready` for a re-measurement
      that comes back refuted.

  (3) THEREFORE the signal resolves to NO purchase on the board, and
      `tools/purchase_frontier.py::SIGNAL_UNBLOCKED_BY` must keep saying so.
      What it prices is a set-valued FUNCTION, which is the
      definitional-extension axis one level up from `function-symbol`; a
      row is never authored from a corpus cycle, so the map says `None`
      and names the reason.

WHAT COUNTS AS A PROOF HERE.  Every claim is asserted against the gate
(`generators.math_reading.parse_math_reading`) and the evaluator
(`generators.math_eval`), never against a re-implementation of the
fragment's semantics.  The subject prose is read out of the primary corpus
artifact by content hash, so a re-census that moves a subject moves this
file's answer with it.  Offline, deterministic, Lean-free.
"""
import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from generators.math_reading import (BadMathReading, FragmentMiss,   # noqa: E402
                                     parse_math_reading)
from generators import math_eval                                     # noqa: E402

CORPUS = os.path.join(ROOT, "specs", "mathsources", "carleson", "nodes.jsonl")

#: The two subjects, by the text hash the refusal ledger files them under --
#: never by label, so a re-extraction that renames a node reds here loudly
#: instead of silently measuring a different sentence.
SUBJECTS = {
    "disjoint-row-support":
        "c1cb51f45e41623e04655f7931e1af9fb7fc0044c0695055112d386a09e534b9",
    "pairwise-disjoint":
        "cda14d2ef0927d4766247a469f35604c22ab497b45419f3043e023220a38a639",
}


def _prose(label):
    """The subject's VERBATIM prose, re-derived from the primary artifact and
    checked against the hash the ledger files it under."""
    with open(CORPUS) as fh:
        for line in fh:
            node = json.loads(line)
            if node.get("label") == label:
                text = node["prose"]
                got = hashlib.sha256(text.encode("utf-8")).hexdigest()
                assert got == SUBJECTS[label], (
                    f"{label}: prose hash moved ({got}); the ledger rows "
                    f"file the OLD text, so this measurement would be about "
                    f"a different sentence")
                return text
    pytest.fail(f"{label} is not in {CORPUS}")


# --- reading builders (the same helpers every wp_c*_readings.py uses) -------
def _amb(c):
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": c}}


def _obj(i, name, quote):
    return {"id": i, "force": "presupposition", "quote": quote,
            "lf": {"kind": "object", "name": name, "type": "Nat"}}


def _setdef(i, name, param, body, quote):
    return {"id": i, "force": "presupposition", "quote": quote,
            "lf": {"kind": "setdef", "name": name, "param": param,
                   "body": body}}


def _hyp(i, pred, quote):
    return {"id": i, "force": "demand", "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _con(pred, quote):
    return {"id": "c", "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def _r(n):
    return {"ref": n}


def _lit(n):
    return {"lit": n}


def _op(o, *a):
    return {"op": o, "args": list(a)}


def _mem(t, s):
    return {"op": "mem", "args": [t, {"set": s}]}


def _readings(label):
    """(family_reading, non_indexed_reading) for one subject.

    The two differ in EXACTLY ONE thing -- whether each comprehension body
    mentions the index -- so the divergence below is attributable to
    indexing and to nothing else."""
    if label == "pairwise-disjoint":
        q_hyp = (r"{E_1}({\mathfrak p})\cap {E_1}({\mathfrak p}')"
                 r"\neq \emptyset")
        q_obj = r"{\mathfrak p}, {\mathfrak p}' \in {\mathfrak {M}}(k,n)"
        q_con = r"then \({\mathfrak p}={\mathfrak p}'\)"
        common = [_amb("Nat"), _obj("p", "p", q_obj), _obj("pp", "pp", q_obj),
                  _obj("x", "x", q_hyp)]
        tail = [_hyp("h", _op("and", _mem(_r("x"), "s1"), _mem(_r("x"), "s2")),
                     q_hyp),
                _con(_op("=", _r("p"), _r("pp")), q_con)]
        indexed = [_setdef("d1", "s1", "y", _op("=", _r("y"), _r("p")), q_hyp),
                   _setdef("d2", "s2", "y", _op("=", _r("y"), _r("pp")), q_hyp)]
        flat = [_setdef("d1", "s1", "y", _op("<=", _lit(0), _r("y")), q_hyp),
                _setdef("d2", "s2", "y", _op("<=", _lit(0), _r("y")), q_hyp)]
        name = "tiles"
    else:
        q_set = r"The sets \(E_j\)"
        q_idx = r"1 \le j \le 2^n"
        q_dis = r"are pairwise disjoint"
        common = [_amb("Nat"), _obj("j", "j", q_idx), _obj("jp", "jp", q_idx),
                  _obj("x", "x", q_set)]
        # "pairwise disjoint" stated element-wise: distinct indices share no
        # element, i.e. the shared-element hypothesis is contradictory.
        tail = [_hyp("h", _op("and", _op("!=", _r("j"), _r("jp")),
                              _op("and", _mem(_r("x"), "s1"),
                                  _mem(_r("x"), "s2"))), q_dis),
                _con(_op("!=", _lit(0), _lit(0)), q_dis)]
        indexed = [_setdef("d1", "s1", "y", _op("=", _r("y"), _r("j")), q_set),
                   _setdef("d2", "s2", "y", _op("=", _r("y"), _r("jp")), q_set)]
        flat = [_setdef("d1", "s1", "y", _op("<=", _lit(0), _r("y")), q_set),
                _setdef("d2", "s2", "y", _op("<=", _lit(0), _r("y")), q_set)]
        name = "rows"
    return ({"theorem": f"{name}_family_reading",
             "statements": common + indexed + tail},
            {"theorem": f"{name}_non_indexed_reading",
             "statements": common + flat + tail})


@pytest.mark.parametrize("label", sorted(SUBJECTS))
def test_the_family_reading_is_refused_by_the_closure_rule_not_the_carrier(label):
    """(1) The wall is P9's elimination discipline, not the carrier
    whitelist -- so no set-carrier purchase reaches this subject."""
    source = _prose(label)
    family, _ = _readings(label)
    with pytest.raises((BadMathReading, FragmentMiss)) as exc:
        parse_math_reading(json.dumps(family), source)
    msg = str(exc.value)
    assert "is not its parameter" in msg, msg
    assert "closed over its parameter" in msg, msg
    # And the reason is the ELIMINATION discipline, which is exactly why a
    # carrier purchase cannot lift it.
    assert "substitution" in msg, msg


@pytest.mark.parametrize("label", sorted(SUBJECTS))
def test_the_non_indexed_reading_gates_and_is_then_refuted(label):
    """(2) The shape a free-set-variable retirement WOULD supply is not
    merely weaker -- it is FALSE, so the coarse filing would promise a
    return that comes back refuted."""
    source = _prose(label)
    _, flat = _readings(label)
    reading = parse_math_reading(json.dumps(flat), source)   # gates cleanly
    assert math_eval.bounded_nonvacuous(reading, bound=8), \
        f"{label}: a vacuous box would make the refutation below meaningless"
    counterexamples = [a for a in math_eval.enumerate_domain(reading, bound=8)
                       if math_eval.hypotheses_hold(reading, a)
                       and not math_eval.conclusion_holds(reading, a)]
    assert counterexamples, (
        f"{label}: the non-indexed reading is TRUE on the box -- if that ever "
        f"becomes the measurement, `indexed-set-family` loses its reason to "
        f"be filed apart and this file should say so")


@pytest.mark.parametrize("label", sorted(SUBJECTS))
def test_both_subjects_are_filed_under_indexed_set_family(label):
    """The ledger and this measurement name the same subjects."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import frontier_refusals as fr
    refused = fr.refused_by_subject()
    assert "indexed-set-family" in refused.get(SUBJECTS[label], []), \
        f"{label} is measured here but not filed under indexed-set-family"


def test_the_signal_resolves_to_no_purchase_and_says_why():
    """(3) The separation must survive in the SHIPPED map, not just here."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from purchase_frontier import SIGNAL_UNBLOCKED_BY
    key, reason = SIGNAL_UNBLOCKED_BY["indexed-set-family"]
    assert key is None, (
        "filing indexed-set-family under a purchase publishes a return the "
        "measurement above says that purchase cannot make")
    assert "index" in reason.lower() and len(reason.split()) >= 8, reason

"""Teeth for run/reflect_shadow.py (S4a: reflection as a paired shadow
channel).  Cert-shape invariance is the load-bearing property: nothing here
may touch the pinned channels/discharge vocabulary."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from generators.math_reading import parse_math_reading
from run import reflect_shadow
from kernel.certs import ANCHOR_CERT_CHANNELS, ANCHOR_DISCHARGE_RUNGS


def _exists_reading():
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "on", "force": "demand", "quote": "integer n",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "om", "force": "demand", "quote": "integer m",
         "lf": {"kind": "object", "name": "m", "type": "Int"}},
        {"id": "qf", "force": "demand", "quote": "for every",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "qx", "force": "demand", "quote": "there exists",
         "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
        {"id": "c", "force": "demand", "quote": "n less than m",
         "lf": {"kind": "conclusion",
                "pred": {"op": "<", "args": [{"ref": "n"}, {"ref": "m"}]}}},
    ]
    src = ("integer n integer m for every there exists n less than m")
    return parse_math_reading(
        json.dumps({"theorem": "t", "statements": stmts}), src)


def test_pinned_vocabulary_untouched():
    # the whole point of the shadow route: the frozen cert surfaces do not
    # know reflection exists.
    assert ANCHOR_CERT_CHANNELS == ("lean-elaborate+lean4checker",
                                    "template-eval-replay")
    assert ANCHOR_DISCHARGE_RUNGS == ("decide", "omega", "norm_num", "simp")
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "run", "reflect_shadow.py")).read()
    assert "ANCHOR_CERT_CHANNELS" not in src.replace(
        "``ANCHOR_CERT_CHANNELS``", "")   # named only in the docstring


def test_probe_builds_gate_clean_and_deterministic():
    r = _exists_reading()
    a = reflect_shadow.shadow_probe(r)
    b = reflect_shadow.shadow_probe(r)
    assert a["status"] == "probe", a
    assert a == b                          # byte-stable
    assert a["n_envs"] >= 1
    assert "checkAll_witness" in a["probe"]
    assert "rfl" in a["probe"]
    # the ∃ var m sits after n in sorted order -> index 0 is m? sorted(m,n)
    # gives m=0, n=1; k must be m's index.
    assert a["k"] == 0
    assert a["template"] == "(Tm.add (Tm.tvar 1) (Tm.lit 1))"


def test_quote_slice_misses_are_named_skips():
    r = _exists_reading()
    # patch the conclusion to an out-of-slice op via a fresh reading.
    import copy
    with pytest.raises(reflect_shadow.SliceMiss):
        reflect_shadow.quote_pred({"op": "coprime",
                                   "args": [{"ref": "n"}, {"ref": "m"}]},
                                  {"n": 0, "m": 1})


def test_corpus_sweep_rows_named():
    rep = reflect_shadow.run_shadow()
    assert rep["rows"], "committed corpus produced no rows"
    for r in rep["rows"]:
        assert r["status"] in ("probe", "skip")
        if r["status"] == "skip":
            assert any(r["reason"].startswith(p) for p in
                       ("not-emitted:", "multi-exists-out-of-scope-v0",
                        "op-out-of-reflect-slice:",
                        "nat-sub-out-of-reflect-slice"))
    if not common.lean_available():
        assert rep["verdicts"] == "deferred: lean toolchain absent"


@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent (Lean-lane test)")
def test_shadow_probe_elaborates_and_agrees():
    from kernel.backends import LeanBackend
    r = _exists_reading()
    p = reflect_shadow.shadow_probe(r)
    assert p["status"] == "probe"
    res = LeanBackend().elaborate(p["probe"], expect_sorry=False)
    assert not res.get("unavailable"), res
    assert res.get("ok"), res              # reflection agrees with the ladder

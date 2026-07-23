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


def test_out_of_slice_ops_all_named_skips():
    # S6 shape 6: `^` / gcd / coprime stay honest NAMED skips until the
    # reflect slice grows those constructors -- pinned per op so a silent
    # mis-quote can never slip in as a probe.
    idx = {"n": 0, "m": 1}
    for op in ("gcd", "^"):
        with pytest.raises(reflect_shadow.SliceMiss):
            reflect_shadow.quote_term(
                {"op": op, "args": [{"ref": "n"}, {"lit": 2}]}, idx)
    with pytest.raises(reflect_shadow.SliceMiss):
        reflect_shadow.quote_pred(
            {"op": "coprime", "args": [{"ref": "n"}, {"ref": "m"}]}, idx)


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


def test_corpus_emits_probes_from_committed_readings():
    # S4a'(ii) done-predicate: >=5 probe rows, all sourced from the COMMITTED
    # corpus (run_shadow only reads specs/mathsources/readings/, so a fixture
    # can never produce a row), including >=2 multi-outer-variable and >=2
    # hypothesis-bearing readings -- the S4b entrance predicate's mix.
    rep = reflect_shadow.run_shadow()
    probes = [r for r in rep["rows"] if r["status"] == "probe"]
    assert len(probes) >= 5, [r.get("reason", r["status"]) for r in rep["rows"]]
    readings_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "specs", "mathsources", "readings")
    multi_outer = hyp_bearing = 0
    for r in probes:
        stmts = json.load(open(os.path.join(
            readings_dir, r["source"])))["reading"]["statements"]
        n_outer = sum(len(s["lf"]["objects"]) for s in stmts
                      if s["lf"].get("kind") == "quantifier"
                      and s["lf"]["binder"] == "forall")
        if n_outer >= 2:
            multi_outer += 1
        if any(s["lf"].get("kind") == "hypothesis" for s in stmts):
            hyp_bearing += 1
    assert multi_outer >= 2 and hyp_bearing >= 2, (multi_outer, hyp_bearing)


def test_ledger_append_only(tmp_path):
    # S4a'(i) tooth: the byte-prefix discipline (the _Ledger convention) --
    # appending never rewrites what a prior run recorded.
    fake = {"rows": [
        {"status": "probe", "elaborated": True, "module_sha": "m0",
         "source": "x.json", "statement_hash": "h0"},
        {"status": "skip", "reason": "not-emitted:no-exists-binder"},
        {"status": "probe", "elaborated": False, "module_sha": "m0",
         "source": "y.json", "statement_hash": "h1"},
    ]}
    path = str(tmp_path / "ledger.jsonl")
    first_rows = reflect_shadow.append_ledger(fake, path, "run-1")
    first = open(path, "rb").read()
    second_rows = reflect_shadow.append_ledger(fake, path, "run-2")
    second = open(path, "rb").read()
    assert len(first_rows) == len(second_rows) == 2   # skips never ledger
    assert second.startswith(first)                   # append-only, by bytes
    rows = [json.loads(line) for line in open(path)]
    assert [r["lane_run_id"] for r in rows] == ["run-1"] * 2 + ["run-2"] * 2
    assert {r["verdict"] for r in rows} == {"agree", "disagree"}
    # a disagreement row carries its root cause (unexplained when unknown);
    # an agreement row carries none.
    for r in rows:
        if r["verdict"] == "disagree":
            assert r["reason"] == "unexplained"
        else:
            assert "reason" not in r
    # rows are canonical JSON lines (byte-stable across appends of same data).
    for line, row in zip(open(path), rows):
        assert line == common.canonical_json(row) + "\n"


def test_committed_ledger_wellformed_if_present():
    # The committed evidence store: every row carries the S4a' schema.  Skips
    # (named) until the first lane run's rows are committed back.
    path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results", "reflect_agreement.jsonl")
    if not os.path.exists(path):
        pytest.skip("agreement ledger not yet seeded (first lane run pending)")
    rows = [json.loads(line) for line in open(path)]
    assert rows, "committed ledger exists but is empty"
    base = {"lane_run_id", "module_sha", "source", "statement_hash", "verdict"}
    for row in rows:
        # `reason` (disagreement root-cause) arrived with the second lane
        # iteration; earlier committed rows predate it -- append-only history
        # is never rewritten, so the older schema stays valid.
        assert base <= set(row) <= base | {"reason"}
        assert row["verdict"] in ("agree", "disagree")
        if "reason" in row:
            assert row["verdict"] == "disagree"


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

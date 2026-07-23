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
            # nat-sub-out-of-reflect-slice is RETIRED (S6-carrier proved the
            # truncation semantics); its reappearance would be a regression.
            assert any(r["reason"].startswith(p) for p in
                       ("not-emitted:", "multi-exists-out-of-scope-v0",
                        "op-out-of-reflect-slice:",
                        "mixed-carriers-out-of-reflect-slice",
                        "route-not-applicable:", "no-inbox-witness-envs",
                        "no-true-box-points"))
    if not common.lean_available():
        assert rep["verdicts"] == "deferred: lean toolchain absent"


def test_nat_reading_probes_through_nat_layer():
    # S6-carrier retirement made observable: the committed Nat ∃-reading
    # (truncated-sub template) emits a probe through the Nat mirror, not a
    # nat-sub skip.
    readings_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "specs", "mathsources", "readings")
    d = json.load(open(os.path.join(readings_dir, "67_nat_pred_witness.json")))
    r = parse_math_reading(json.dumps(d["reading"]), d["source"])
    p = reflect_shadow.shadow_probe(r)
    assert p["status"] == "probe", p
    assert "checkAllN_witness" in p["probe"]
    assert "(0 : Nat)" in p["probe"]
    assert "Tm.sub" in p["template"]       # the truncated-sub template


def test_all_three_routes_probe_from_committed_corpus():
    # S4b's route-qualified vocabulary needs PER-ROUTE evidence: the sweep
    # must exercise every route it would promote, from the committed corpus.
    rep = reflect_shadow.run_shadow()
    by_route = {}
    for r in rep["rows"]:
        if r["status"] == "probe":
            by_route.setdefault(r["route"], []).append(r)
    assert len(by_route.get("checkAll_witness", [])) >= 5
    assert len(by_route.get("checkStmtBox_sound_exOnly", [])) >= 5
    assert len(by_route.get("sall_guard_of_check", [])) >= 2
    for r in by_route["checkStmtBox_sound_exOnly"]:
        assert "checkStmtBox_sound_exOnly" in r["probe"]
    for r in by_route["sall_guard_of_check"]:
        assert "sall_guard_of_check" in r["probe"]
        assert "Pd.pimp (Pd.peq (Tm.tvar 0)" in r["probe"]   # the guard shape


def test_corpus_emits_probes_from_committed_readings():
    # S4a'(ii) done-predicate: >=5 probe rows, all sourced from the COMMITTED
    # corpus (run_shadow only reads specs/mathsources/readings/, so a fixture
    # can never produce a row), including >=2 multi-outer-variable and >=2
    # hypothesis-bearing readings -- the S4b entrance predicate's mix.
    rep = reflect_shadow.run_shadow()
    probes = [r for r in rep["rows"] if r["status"] == "probe"
              and r["route"] == "checkAll_witness"]
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
         "source": "x.json", "statement_hash": "h0",
         "route": "checkAll_witness"},
        {"status": "skip", "reason": "not-emitted:no-exists-binder"},
        {"status": "probe", "elaborated": False, "module_sha": "m0",
         "source": "y.json", "statement_hash": "h1",
         "route": "sall_guard_of_check"},
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
    assert [r["route"] for r in rows] == ["checkAll_witness",
                                          "sall_guard_of_check"] * 2
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
    # `route` arrived with the per-route sweep; rows before it are implicitly
    # checkAll_witness (the only route the sweep then exercised).
    base = {"lane_run_id", "module_sha", "source", "statement_hash", "verdict"}
    ann = {"kind", "annotates_lane_run_id", "source", "statement_hash",
           "reason"}
    for row in rows:
        if row.get("kind") == "root-cause-annotation":
            # append-only root-cause for rows that predate the `reason`
            # field: history is never rewritten, so the explanation is a
            # NEW row pointing at the old one.
            assert set(row) == ann
            continue
        # `reason` (disagreement root-cause) arrived with the second lane
        # iteration; earlier committed rows predate it -- append-only history
        # is never rewritten, so the older schema stays valid.
        assert base <= set(row) <= base | {"reason", "route"}
        assert row["verdict"] in ("agree", "disagree")
        if "reason" in row:
            assert row["verdict"] == "disagree"


def test_no_unexplained_disagreements_ledger_measured():
    # THE S4b entrance axis, measured from the ledger ALONE (never prose):
    # every disagreement row either carries its own `reason` or is pointed
    # at by a root-cause-annotation row.
    path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results", "reflect_agreement.jsonl")
    if not os.path.exists(path):
        pytest.skip("agreement ledger not yet seeded (first lane run pending)")
    rows = [json.loads(line) for line in open(path)]
    annotated = {(r["annotates_lane_run_id"], r["statement_hash"])
                 for r in rows if r.get("kind") == "root-cause-annotation"}
    unexplained = [
        r for r in rows
        if r.get("kind") is None and r["verdict"] == "disagree"
        and "reason" not in r
        and (r["lane_run_id"], r["statement_hash"]) not in annotated]
    assert unexplained == [], unexplained


def _corpus_reading(name):
    readings_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "specs", "mathsources", "readings")
    d = json.load(open(os.path.join(readings_dir, name)))
    return parse_math_reading(json.dumps(d["reading"]), d["source"])


class _StubBackend:
    """Refuses every probe with a fixed detail -- exercises the RECORDING
    path (verdict, reason classification, ledger rows) without Lean."""
    def __init__(self, detail):
        self._detail = detail

    def elaborate(self, text, *, expect_sorry):
        return {"ok": False, "unavailable": False, "detail": self._detail}


def _stubbed_sweep(monkeypatch, detail):
    import kernel.backends as kb
    monkeypatch.setattr(common, "lean_available", lambda: True)
    monkeypatch.setattr(kb, "LeanBackend", lambda: _StubBackend(detail))
    return reflect_shadow.run_shadow()


def test_planted_failure_is_recorded_not_laundered(monkeypatch, tmp_path):
    # Every refusal must surface as a disagree row with a reason -- the
    # plumbing can neither crash on failure nor launder it into agreement.
    rep = _stubbed_sweep(monkeypatch, "boom: something else entirely")
    probes = [r for r in rep["rows"] if r["status"] == "probe"]
    assert probes and rep["verdicts"]["agree"] == 0
    assert rep["verdicts"]["disagree"] == len(probes)
    for r in probes:
        assert r["elaborated"] is False
        assert r["disagreement"]["reason"] == "unexplained"
    ledger = str(tmp_path / "led.jsonl")
    rows = reflect_shadow.append_ledger(rep, ledger, "planted-run")
    assert len(rows) == len(probes)
    assert all(r["verdict"] == "disagree" and r["reason"] == "unexplained"
               for r in rows)


def test_planted_budget_failure_classified(monkeypatch):
    # the one known-benign refusal class is classified from the transcript,
    # never guessed.
    rep = _stubbed_sweep(
        monkeypatch, "(deterministic) timeout at whnf, maximum number of "
                     "heartbeats (400000) has been reached")
    probes = [r for r in rep["rows"] if r["status"] == "probe"]
    assert probes
    for r in probes:
        assert (r["disagreement"]["reason"]
                == "deterministic-timeout-at-heartbeat-cap")


def test_shadow_discharge_deterministic_and_replays():
    reading = _corpus_reading("43_larger_integer_exists.json")
    a = reflect_shadow.discharge_reflection(reading, "checkAll_witness")
    b = reflect_shadow.discharge_reflection(reading, "checkAll_witness")
    assert a == b, "discharge record is not byte-stable"
    assert a["status"] == "proposed"
    assert a["route"] == "reflection/checkAll_witness"
    assert reflect_shadow.replay_reflection(reading, a)["ok"]
    # a tampered record must fail replay -- probe bytes are the gate.
    tampered = dict(a, probe_sha="0" * 64)
    assert not reflect_shadow.replay_reflection(reading, tampered)["ok"]
    # a route that cannot reach this reading declines with a named skip and
    # still carries the route-qualified name.
    forall_only = _corpus_reading("01_dvd_reflexive.json")
    rec = reflect_shadow.discharge_reflection(forall_only, "checkAll_witness")
    assert rec["status"] == "skip"
    assert rec["route"] == "reflection/checkAll_witness"


def test_shadow_discharge_all_routes_route_qualified():
    reading = _corpus_reading("68_between_witness.json")
    for route, _ in reflect_shadow.ROUTES:
        rec = reflect_shadow.discharge_reflection(reading, route)
        assert rec["route"] == f"reflection/{route}"
        assert rec["status"] in ("proposed", "skip")


@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent (Lean-lane test)")
def test_planted_false_probe_refused_under_lean():
    # end-to-end negative control: a probe asserting a FALSE claim (3 < 2)
    # must fail elaboration -- the kernel is the arbiter, and this pins that
    # the probe construction cannot accidentally prove around it.
    from kernel.backends import LeanBackend
    module = open(reflect_shadow._REFLECT_SRC).read()
    probe = (module + "\n\nnamespace FgReflect\n\n"
             "-- PLANTED negative control: the checker computes false, so\n"
             "-- rfl cannot close and elaboration must refuse.\n"
             "example : denote (fun _ => 0)"
             " (Pd.plt (Tm.lit 3) (Tm.lit 2)) :=\n"
             "  check_sound _ _ rfl\n\n"
             "end FgReflect\n")
    res = LeanBackend().elaborate(probe, expect_sorry=False)
    assert not res.get("unavailable"), res
    assert res.get("ok") is False, "a false claim elaborated -- soundness leak"


@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent (Lean-lane test)")
def test_shadow_discharge_elaborates_axiom_clean():
    # the record the ceremony's runner would mint: elaborates, and the
    # run-2 audit shows an EMPTY axiom set (no sorryAx, nothing smuggled).
    from kernel.backends import LeanBackend
    reading = _corpus_reading("43_larger_integer_exists.json")
    rec = reflect_shadow.discharge_reflection(reading, "checkAll_witness")
    assert rec["status"] == "proposed"
    be = LeanBackend()
    res = be.elaborate(rec["probe"], expect_sorry=False)
    assert res.get("ok"), res
    rc = be.recheck(res["olean_path"])
    assert rc.get("ok"), rc
    assert rc.get("axioms") == [], rc


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

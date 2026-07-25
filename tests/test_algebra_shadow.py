"""Teeth for run/algebra_shadow.py (S4a: the abstract-algebra discharge
route as a paired shadow channel, PLAN_FRAGMENT §4 P5).

Cert-shape invariance is the load-bearing property: P5 is a TRUST ROOT, not
a purchase, so nothing here -- and nothing in the module under test -- may
touch the pinned channels or the discharge vocabulary.  Everything below is
Lean-free and deterministic; the ledger-measured axes skip honestly until a
lane run seeds the evidence store.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from run import algebra_shadow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_SRC = os.path.join(ROOT, "run", "algebra_shadow.py")


def _queue_goals():
    return algebra_shadow.load_queue(ROOT)["goals"]


def _first_probe_goal():
    readings = algebra_shadow.bench_readings(ROOT)
    for g in _queue_goals():
        if algebra_shadow.algebra_probe(
                g, readings=readings, root=ROOT)["status"] == "probe":
            return g
    raise AssertionError("committed queue produced no probeable goal")


def _first_skip_goal():
    readings = algebra_shadow.bench_readings(ROOT)
    for g in _queue_goals():
        if algebra_shadow.algebra_probe(
                g, readings=readings, root=ROOT)["status"] == "skip":
            return g
    raise AssertionError("committed queue produced no skip")


# --------------------------------------------------------------- 1. the pins
def test_pinned_vocabulary_untouched():
    # P5's whole point: a new rung may not arrive by growth or economics.
    # The pins are asserted here so a shadow-channel commit that drifted them
    # would be loud, and the module is grepped so it can only NAME them.
    from kernel.certs import (ANCHOR_CERT_CHANNELS, ANCHOR_DISCHARGE_RUNGS,
                              ANCHOR_LIVE_DISCHARGES)
    assert ANCHOR_CERT_CHANNELS == ("lean-elaborate+lean4checker",
                                    "template-eval-replay")
    assert ANCHOR_DISCHARGE_RUNGS == ("decide", "omega", "norm_num", "simp")
    assert ANCHOR_LIVE_DISCHARGES == ANCHOR_DISCHARGE_RUNGS + (
        "reflection/checkAll_witness",)
    src = open(MODULE_SRC).read()
    for name in ("ANCHOR_CERT_CHANNELS", "ANCHOR_DISCHARGE_RUNGS",
                 "ANCHOR_LIVE_DISCHARGES"):
        # named only in the docstring (double-backtick prose form).
        assert name not in src.replace(f"``{name}``", ""), name
    # the dependency points one way: the shadow never imports cert surfaces.
    assert "kernel.certs" not in src
    assert "certs" not in src.replace("kernel/certs.py", "")


# ------------------------------------------------------- 2. the probe itself
def test_probe_builds_gate_clean_and_deterministic():
    from buildloop.validate_lean import validate_lean
    g = _first_probe_goal()
    a = algebra_shadow.algebra_probe(g, root=ROOT)
    b = algebra_shadow.algebra_probe(g, root=ROOT)
    assert a["status"] == "probe", a
    assert a == b                                  # byte-stable
    assert a["route"] == algebra_shadow.ROUTE == "algebra/ring_nf"
    assert f"by {algebra_shadow.TACTIC}" in a["lean"]
    assert "sorry" not in a["lean"]
    # the probe asserts the goal the QUEUE names, verified by hash.
    assert a["statement_hash"] == g["subject"]["sha256"]
    ok, why = validate_lean(a["lean"])
    assert ok, why
    assert a["probe_sha"] == common.sha256_bytes(a["lean"].encode())


def test_probe_carries_a_capped_budget():
    # the whitelisted set_option cap rides every probe (the gate enforces the
    # numeric range; `maxHeartbeats 0` is refused outright).
    a = algebra_shadow.algebra_probe(_first_probe_goal(), root=ROOT)
    assert f"set_option maxHeartbeats {common.LEAN_MAXHEARTBEATS} in" in a["lean"]


# ---------------------------------------------------------- 3. named skips
def test_skips_are_named():
    # FROZEN vocabulary, pinned as a tuple: a skip is never a failure, but it
    # is also never anonymous -- a new skip class must be declared, not
    # invented at runtime.
    assert algebra_shadow.SKIP_PREFIXES == (
        "family-not-algebra:", "no-lean-prop", "route-not-applicable:")
    rep = algebra_shadow.run_shadow(ROOT)
    skips = [r for r in rep["rows"] if r["status"] == "skip"]
    assert skips, "committed queue produced no skips at all"
    for r in skips:
        assert any(r["reason"].startswith(p)
                   for p in algebra_shadow.SKIP_PREFIXES), r["reason"]
        assert r["route"] == algebra_shadow.ROUTE
    # every declared prefix is documented in the module's frozen-vocabulary
    # block -- prose and code cannot drift apart.
    doc = algebra_shadow.__doc__
    for p in algebra_shadow.SKIP_PREFIXES:
        assert p in doc, p


def test_non_ring_families_are_skipped_never_probed():
    # the honesty rule the census taught: measure the class the route can
    # actually reach; everything else is a NAMED miss, not a widened claim.
    rep = algebra_shadow.run_shadow(ROOT)
    families = {r["family"] for r in rep["rows"] if r["status"] == "probe"}
    assert families == set(algebra_shadow.ALGEBRA_FAMILIES) == {"linear"}
    reasons = {r["reason"] for r in rep["rows"] if r["status"] == "skip"}
    assert any(x.startswith("family-not-algebra:") for x in reasons)


# ------------------------------------------------------- 4. the corpus sweep
def test_sweep_from_committed_queue():
    # S4a'(ii): rows come from the COMMITTED queue alone (run_shadow reads
    # results/proof_queue.json and the bench state, so a fixture can never
    # produce a row) and every row is one of the two honest statuses.
    rep = algebra_shadow.run_shadow(ROOT)
    assert rep["rows"], "committed queue produced no rows"
    assert rep["tool"] == "algebra_shadow"
    assert rep["channel"] == "shadow (paired, non-cert)"
    refs = {g["subject"]["ref"] for g in _queue_goals()}
    for r in rep["rows"]:
        assert r["status"] in ("probe", "skip")
        assert r["source"] in refs          # zero fixture-sourced rows
    probes = [r for r in rep["rows"] if r["status"] == "probe"]
    assert len(probes) >= 8, len(probes)
    assert len({r["statement_hash"] for r in probes}) == len(probes)
    if not common.lean_available():
        assert rep["verdicts"] == "deferred: lean toolchain absent"


def test_sweep_pins_its_own_inputs_and_builder():
    # a report that cannot say WHICH queue and WHICH builder produced it is
    # not evidence; both pins ride the report.
    rep = algebra_shadow.run_shadow(ROOT)
    assert rep["module_sha"] == algebra_shadow.builder_sha()
    assert set(rep["queue_derived_from"]) == set(
        algebra_shadow.load_queue(ROOT)["derived_from"])


def test_queue_is_read_only():
    # the tap point is READ-ONLY: a sweep may not perturb a committed byte.
    path = os.path.join(ROOT, *algebra_shadow.QUEUE.split("/"))
    before = open(path, "rb").read()
    algebra_shadow.run_shadow(ROOT)
    assert open(path, "rb").read() == before
    assert not os.path.exists(os.path.join(ROOT, *algebra_shadow.LEDGER.split("/"))) \
        or True                              # ledger presence is a lane fact


# ------------------------------------------------------------- 5. the ledger
def test_ledger_append_only(tmp_path):
    # S4a'(i) tooth: the byte-prefix discipline (the _Ledger convention) --
    # appending never rewrites what a prior run recorded.
    rows = [
        {"status": "probe", "elaborated": True, "probe_sha": "p0",
         "source": "x", "statement_hash": "h0", "route": algebra_shadow.ROUTE},
        {"status": "skip", "reason": "family-not-algebra:gcd",
         "route": algebra_shadow.ROUTE, "source": "y"},
        {"status": "probe", "elaborated": False, "probe_sha": "p1",
         "source": "z", "statement_hash": "h1", "route": algebra_shadow.ROUTE},
    ]
    path = str(tmp_path / "ledger.jsonl")
    first_rows = algebra_shadow.append_ledger(path, rows, "run-1", "m0")
    first = open(path, "rb").read()
    second_rows = algebra_shadow.append_ledger(path, rows, "run-2", "m0")
    second = open(path, "rb").read()
    assert len(first_rows) == len(second_rows) == 2   # skips never ledger
    assert second.startswith(first)                   # append-only, by bytes
    out = [json.loads(line) for line in open(path)]
    assert [r["lane_run_id"] for r in out] == ["run-1"] * 2 + ["run-2"] * 2
    assert {r["verdict"] for r in out} == {"agree", "disagree"}
    assert {r["module_sha"] for r in out} == {"m0"}
    for r in out:
        if r["verdict"] == "disagree":
            assert r["reason"] == "unexplained"
        else:
            assert "reason" not in r
    # canonical JSON lines, byte-stable across appends of the same data.
    for line, row in zip(open(path), out):
        assert line == common.canonical_json(row) + "\n"


def test_ledger_defaults_to_the_live_builder_sha(tmp_path):
    path = str(tmp_path / "l.jsonl")
    rows = algebra_shadow.append_ledger(
        path, [{"status": "probe", "elaborated": True, "probe_sha": "p",
                "source": "s", "statement_hash": "h",
                "route": algebra_shadow.ROUTE}], "run-x")
    assert rows[0]["module_sha"] == algebra_shadow.builder_sha()


def test_deferred_sweep_writes_no_ledger(tmp_path):
    # the :542 convention: a sweep with no real verdicts contributes nothing
    # to the evidence store -- deferred is not agreement.
    rep = algebra_shadow.run_shadow(ROOT)
    if isinstance(rep.get("verdicts"), dict):
        pytest.skip("lean present: this tooth pins the deferred path")
    path = str(tmp_path / "never.jsonl")
    assert algebra_shadow.append_ledger(path, rep["rows"], "run-0") == []
    assert not os.path.exists(path)


# -------------------------------------------------- 6/7/8. ledger-measured
def _ledger_path():
    return os.path.join(ROOT, *algebra_shadow.LEDGER.split("/"))


def _ledger_rows():
    if not os.path.exists(_ledger_path()):
        pytest.skip("algebra agreement ledger not yet seeded (needs a lane run)")
    return [json.loads(line) for line in open(_ledger_path())]


def test_committed_ledger_wellformed_if_present():
    rows = _ledger_rows()
    assert rows, "committed ledger exists but is empty"
    base = {"lane_run_id", "module_sha", "probe_sha", "route", "run_attempt",
            "source", "statement_hash", "verdict"}
    ann = {"kind", "annotates_lane_run_id", "source", "statement_hash",
           "reason"}
    for row in rows:
        if row.get("kind") == "root-cause-annotation":
            # append-only root cause for rows that predate the `reason`
            # field: history is never rewritten, so the explanation is a NEW
            # row pointing at the old one.
            assert set(row) == ann
            continue
        assert base <= set(row) <= base | {"reason"}
        assert row["verdict"] in ("agree", "disagree")
        assert row["route"] == algebra_shadow.ROUTE
        if "reason" in row:
            assert row["verdict"] == "disagree"


def test_no_unexplained_disagreements_ledger_measured():
    # THE S4b entrance axis, measured from the ledger ALONE (never prose):
    # every disagreement row either carries its own `reason` or is pointed at
    # by a root-cause-annotation row.
    rows = _ledger_rows()
    annotated = {(r["annotates_lane_run_id"], r["statement_hash"])
                 for r in rows if r.get("kind") == "root-cause-annotation"}
    unexplained = [
        r for r in rows
        if r.get("kind") is None and r["verdict"] == "disagree"
        and "reason" not in r
        and (r["lane_run_id"], r["statement_hash"]) not in annotated]
    assert unexplained == [], unexplained


def test_entrance_predicate_ledger_measured():
    # The entrance predicate, every axis, computed from the committed ledger
    # ALONE -- the house rule is that no done-condition may live only as
    # prose, so the numbers the reflection channel's ceremony was gated on
    # are mirrored here as EXECUTABLE thresholds from day one, before any row
    # exists.  Meeting them is necessary, never sufficient: S4b additionally
    # requires explicit maintainer sign-off (PLAN_FRAGMENT §4 P5).
    rows = _ledger_rows()
    data = [r for r in rows if "kind" not in r]
    agree = [r for r in data if r["verdict"] == "agree"]
    assert len(agree) >= 25, len(agree)
    assert len({r["lane_run_id"] for r in agree}) >= 3
    assert len({r["statement_hash"] for r in agree}) >= 8
    annotated = {(r["annotates_lane_run_id"], r["statement_hash"])
                 for r in rows if r.get("kind") == "root-cause-annotation"}
    unexplained = [
        r for r in data if r["verdict"] == "disagree" and "reason" not in r
        and (r["lane_run_id"], r["statement_hash"]) not in annotated]
    assert unexplained == [], unexplained


# --------------------------------------------------- 9. the planted failure
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
    return algebra_shadow.run_shadow(ROOT)


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
    rows = algebra_shadow.append_ledger(ledger, rep["rows"], "planted-run")
    assert len(rows) == len(probes)
    assert all(r["verdict"] == "disagree" and r["reason"] == "unexplained"
               for r in rows)


def test_planted_budget_failure_classified(monkeypatch):
    rep = _stubbed_sweep(
        monkeypatch, "(deterministic) timeout at whnf, maximum number of "
                     "heartbeats (400000) has been reached")
    probes = [r for r in rep["rows"] if r["status"] == "probe"]
    assert probes
    for r in probes:
        assert (r["disagreement"]["reason"]
                == "deterministic-timeout-at-heartbeat-cap")


def test_planted_missing_tactic_classified(monkeypatch):
    # the refusal class this cycle EXPECTS to see first: the candidate route
    # is not reachable under the pinned narrow import set.  It is classified
    # and recorded -- the repair is an import decision for a later cycle, not
    # a silent widening of common.MATHLIB_IMPORTS here.
    rep = _stubbed_sweep(monkeypatch, "unknown tactic 'ring_nf'")
    probes = [r for r in rep["rows"] if r["status"] == "probe"]
    assert probes
    for r in probes:
        assert (r["disagreement"]["reason"]
                == "tactic-unavailable-under-pinned-imports")


# ------------------------------------------- 10. discharge record + replay
def test_shadow_discharge_deterministic():
    g = _first_probe_goal()
    a = algebra_shadow.discharge_algebra(g, root=ROOT)
    b = algebra_shadow.discharge_algebra(g, root=ROOT)
    assert a == b, "discharge record is not byte-stable"
    assert a["status"] == "proposed"
    assert a["route"] == "algebra/ring_nf"     # route-qualified, always
    assert algebra_shadow.replay_algebra(g, a, root=ROOT)["ok"]
    # a tampered record must fail replay -- probe bytes are the gate.
    for field in ("probe_sha", "module_sha", "statement_hash"):
        tampered = dict(a, **{field: "0" * 64})
        assert not algebra_shadow.replay_algebra(
            g, tampered, root=ROOT)["ok"], field
    # a goal the route cannot reach declines with a NAMED skip and still
    # carries the route-qualified name.
    rec = algebra_shadow.discharge_algebra(_first_skip_goal(), root=ROOT)
    assert rec["status"] == "skip"
    assert rec["route"] == "algebra/ring_nf"
    assert any(rec["reason"].startswith(p)
               for p in algebra_shadow.SKIP_PREFIXES)


def test_subject_hash_mismatch_is_a_named_skip_not_a_reaimed_probe():
    # planted staleness: the queue pins the subject by hash, so a goal whose
    # subject hash no longer matches its reading must DECLINE, never quietly
    # probe a different proposition.
    g = _first_probe_goal()
    stale = json.loads(json.dumps(g))
    stale["subject"]["sha256"] = "0" * 64
    r = algebra_shadow.algebra_probe(stale, root=ROOT)
    assert r["status"] == "skip"
    assert r["reason"] == "no-lean-prop:subject-hash-mismatch"

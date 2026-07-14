"""Unit teeth for the Combined-Loop W3 miss-typed scheduler.

Deterministic and LLM-free: every fixture is seeded through the registry on an
isolated temp DB, and moves are dispatched with no-op stubs so nothing calls an
LLM or the kernel.  Mirrors demo_scheduler.py's five teeth plus the internal
invariants they rely on (tie-break, terminal state, evidence-hash suppression).
"""
import tempfile

import common
import planner
from buildloop import dl, loop, recurrence
from buildloop.mdl_macros import corpus_dl, dl_macro
from library import Registry


def _reg():
    tmp = tempfile.mkdtemp()
    return Registry(db_path=f"{tmp}/reg.sqlite")


def _bound(action, left, cmp_, right):
    return {"kind": "bound", "action": action, "left": left,
            "cmp": cmp_, "right": right}


def _stmt(sid, lf, force="demand", quote="span"):
    return {"id": sid, "force": force, "quote": quote, "lf": lf}


def _two_bound_reading(r1, r2):
    return common.canonical_json({"service": "shop", "statements": [
        _stmt("s1", _bound("sell", "n", "<=", r1)),
        _stmt("s2", _bound("buy", "m", ">=", r2))]})


def _spec(did, atoms):
    return {"demand_id": did, "kind": "spec-file", "origin": "exogenous",
            "status": "open", "language": "ksy", "features": sorted(atoms),
            "payload_ref": did, "size_bytes": 64, "covered_via": None}


def _incumbent(did):
    return {"demand_id": did, "kind": "caged-incumbent", "origin": "exogenous",
            "status": "open", "language": None, "features": None,
            "payload_ref": did, "size_bytes": 500, "covered_via": None}


def _stub_dispatch(status="stub"):
    def mk(k):
        return lambda move, snap, reg, bl, pol, uc, m: {"status": f"{k}-{status}"}
    return {k: mk(k) for k in loop.KIND_ORDER}


def _seed_readings(reg, n=3):
    for i in range(n):
        reg.reading_add(f"req-{i}", _two_bound_reading(5, 1), f"cert-{i}")


def _last_decision(reg):
    return reg.events("scheduler-decision")[-1]["payload"]


def _picked(decision):
    return next((m for m in decision["moves"] if m["picked"]), None)


# ---------------------------------------------------------------- tooth (a)
def test_coverage_picked_before_recurrence():
    reg = _reg()
    _seed_readings(reg)
    reg.demand_upsert(_spec("spec-a", ["uint:1", "uint:2"]))
    reg.demand_upsert(_spec("spec-b", ["uint:1", "uint:2"]))
    loop.run_iteration(reg, [], dispatch=_stub_dispatch())
    d = _last_decision(reg)
    p = _picked(d)
    assert p["kind"] == "coverage"
    # 2 specs x UNCOVERED_PENALTY, minus the minimal covering-grammar cost (the
    # optimistic-upper-bound deduction): close to -100 but reduced by ~1.
    est = dl.generator_dl({"spec_grammar": {"atoms": ["uint:1", "uint:2"]},
                           "emit_entrypoint": {}})
    assert abs(p["expected_dl_delta"] + (2 * dl.UNCOVERED_PENALTY - est)) < 0.01
    assert any(m["kind"] == "recurrence" for m in d["moves"])


def test_no_false_convergence_with_bloated_generators():
    """Regression (adversarial-review MAJOR): a coverable spec must NOT be
    declared converged just because the LIVE generators are bloated.  Deducting
    the median existing generator_dl (which exceeds UNCOVERED_PENALTY once a
    generator carries a 20 KB grammar) drove a servable single-spec group
    negative and the loop stopped with the spec still uncovered."""
    reg = _reg()
    # three bloated, IRRELEVANT generators (wrong atoms) -> big median cost.
    for i in range(3):
        reg.register(name=f"bloat{i}", tier="emit-check", spec_language="ksy",
                     output_language="python-codec",
                     spec_grammar={"atoms": [f"junk{i}:{j}" for j in range(300)]},
                     emit_entrypoint={"kind": "e", "authored_bytes": 8000},
                     contract={}, provenance={})
    reg.demand_upsert(_spec("spec-a", ["uint:1"]))   # coverable, uncovered
    res = loop.run_iteration(reg, [], dispatch=_stub_dispatch())
    d = _last_decision(reg)
    cov = next((m for m in d["moves"] if m["kind"] == "coverage"), None)
    # expected_dl_delta == -score; a servable move reduces ledger_dl (negative).
    assert cov is not None and cov["expected_dl_delta"] < 0, \
        "a coverable single spec must be servable (DL-reducing), not hidden"
    assert res["status"] != "converged", \
        "must not converge while a ledger-reducing coverage miss remains"


def test_recurrence_picked_after_coverage_lands():
    reg = _reg()
    _seed_readings(reg)
    reg.demand_upsert(_spec("spec-a", ["uint:1", "uint:2"]))
    reg.demand_upsert(_spec("spec-b", ["uint:1", "uint:2"]))
    reg.register(name="codec", tier="emit-check", spec_language="ksy",
                 output_language="python-codec",
                 spec_grammar={"atoms": ["uint:1", "uint:2", "uint:4"]},
                 emit_entrypoint={"kind": "ksc-python-rw"},
                 contract={"type": "codec-roundtrip"},
                 provenance={"author": "t"})
    loop.run_iteration(reg, [], dispatch=_stub_dispatch())
    d = _last_decision(reg)
    p = _picked(d)
    assert p["kind"] == "recurrence"
    assert all(m["kind"] != "coverage" for m in d["moves"])


# ---------------------------------------------------------------- tooth (b)
def test_refused_conversion_suppressed_next_round():
    reg = _reg()
    row = _incumbent("world-machine")
    reg.demand_upsert(row)
    ih = dl.incumbent_hash_of(row)
    reg.counter_add(f"toll:{ih}:calls", 5000.0)

    r1 = loop.run_iteration(reg, [])          # default toll stub refuses
    assert _picked(_last_decision(reg))["kind"] == "toll"
    assert r1["status"] == "refused"
    assert reg.events("conversion-suppressed")

    loop.run_iteration(reg, [])
    d2 = _last_decision(reg)
    assert _picked(d2) is None                # nothing eligible -> converged
    toll = next(m for m in d2["moves"] if m["kind"] == "toll")
    assert "suppressed_by" in toll


def test_toll_reappears_when_evidence_changes():
    reg = _reg()
    row = _incumbent("world-machine")
    reg.demand_upsert(row)
    ih = dl.incumbent_hash_of(row)
    reg.counter_add(f"toll:{ih}:calls", 5000.0)
    loop.run_iteration(reg, [])               # refused + suppressed
    # a larger lift bound n changes the evidence hash -> no longer suppressed.
    reg.counter_add(f"lift_n:{ih}", 1.0)
    loop.run_iteration(reg, [])
    assert _picked(_last_decision(reg))["kind"] == "toll"


# ---------------------------------------------------------------- tooth (c)
def test_two_runs_byte_identical():
    reg = _reg()
    _seed_readings(reg)
    reg.demand_upsert(_spec("spec-a", ["uint:1", "uint:2"]))
    reg.demand_upsert(_spec("spec-b", ["uint:1", "uint:2"]))
    row = _incumbent("m")
    reg.demand_upsert(row)
    reg.counter_add(f"toll:{dl.incumbent_hash_of(row)}:calls", 800.0)
    snap = dl.snapshot(reg)
    _, log1, _ = loop.score_moves(snap, reg)
    _, log2, _ = loop.score_moves(snap, reg)
    assert common.canonical_json(log1) == common.canonical_json(log2)


# ---------------------------------------------------------------- tooth (d)
def test_macro_gc_retires_stranded_macro():
    reg = _reg()
    s1 = _bound("a", "x", "<=", 1)
    s2 = _bound("b", "y", "<=", 2)
    s3 = _bound("c", "z", "<=", 3)
    stmts = [_stmt("s1", s1), _stmt("s2", s2), _stmt("s3", s3)]
    readings = [{"service": "svc", "statements": stmts},
                {"service": "svc2", "statements": stmts}]
    for i, r in enumerate(readings):
        reg.reading_add(f"r{i}", common.canonical_json(r), f"c{i}")
    macro_a = {"name": "A", "params": [], "body": [s1, s2]}
    macro_b = {"name": "B", "params": [], "body": [s1, s2, s3]}
    reg.macro_add("A", common.canonical_json(macro_a))
    assert corpus_dl(readings, reg.macro_table())["reading_uses"]["A"] == 2
    reg.macro_add("B", common.canonical_json(macro_b))

    before = corpus_dl(readings, reg.macro_table())["total"]
    retired = recurrence.gc_macros(reg, readings)
    after = corpus_dl(readings, reg.macro_table())["total"]
    assert retired == ["A"]
    assert "A" not in reg.macro_table() and "B" in reg.macro_table()
    assert abs((before - after) - dl_macro(macro_a)) < 1e-6
    assert reg.events("macro-retired")


# ---------------------------------------------------------------- tooth (e)
def test_one_off_never_a_candidate():
    reg = _reg()
    reg.reading_add("only", _two_bound_reading(5, 1), "c0")
    reg.reading_add("other", common.canonical_json({"service": "x",
        "statements": [_stmt("q", {"kind": "action", "name": "go"},
                             force="choice", quote="")]}), "c1")
    cands = recurrence.mine(list(dl.snapshot(reg).readings.values()),
                            reg.macro_table())
    assert cands == []


def test_within_reading_repeat_is_uses_one():
    # the same 2-window twice inside ONE reading is still one witness reading.
    reg = _reg()
    p = _bound("a", "x", "<=", 1)
    q = _bound("b", "y", "<=", 2)
    reading = {"service": "svc", "statements": [
        _stmt("s1", p), _stmt("s2", q), _stmt("s3", p), _stmt("s4", q)]}
    reg.reading_add("solo", common.canonical_json(reading), "c0")
    reg.reading_add("n't", common.canonical_json(
        {"service": "z", "statements": [
            _stmt("a", {"kind": "action", "name": "noop"}, "choice", "")]}), "c1")
    cands = recurrence.mine(list(dl.snapshot(reg).readings.values()),
                            reg.macro_table())
    assert cands == []


# ---------------------------------------------- scheduler-level invariants
def test_terminal_state_converged():
    reg = _reg()
    out = loop.run_iteration(reg, [])
    assert out["status"] == "converged"
    assert out["picked"] is None


def test_tie_break_kind_order_then_key():
    # two moves with equal score: kind order (coverage < request < recurrence
    # < toll), then lexicographic candidate_key.
    a = {"kind": "recurrence", "candidate_key": "z", "score": 5.0}
    b = {"kind": "coverage", "candidate_key": "y", "score": 5.0}
    c = {"kind": "coverage", "candidate_key": "x", "score": 5.0}
    ordered = sorted([a, b, c], key=lambda m: (-m["score"],
                     loop.KIND_ORDER[m["kind"]], m["candidate_key"]))
    assert [m["candidate_key"] for m in ordered] == ["x", "y", "z"]


def test_miss_records_logged():
    reg = _reg()
    _seed_readings(reg)
    reg.demand_upsert(_spec("spec-a", ["uint:1", "uint:2"]))
    reg.demand_upsert(_spec("spec-b", ["uint:1", "uint:2"]))
    row = _incumbent("mm")
    reg.demand_upsert(row)
    reg.counter_add(f"toll:{dl.incumbent_hash_of(row)}:calls", 100.0)
    loop.run_iteration(reg, [], dispatch=_stub_dispatch())
    assert reg.events("coverage-miss")
    assert reg.events("recurrence-miss")
    assert reg.events("toll-miss")

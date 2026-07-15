#!/usr/bin/env python3
"""Combined-Loop W3 -- the miss-typed scheduler (one loop, four signals).

LLM-free, deterministic teeth for the scheduler that scores four typed misses
(coverage / request / recurrence / toll) over ONE frozen snapshot, picks the
argmax with a deterministic tie-break, and logs every considered move (§4.10).

Teeth (exit 0 iff all pass):

  (a) Ordering: 3 clustered readings AND an uncovered 2-spec codec group on one
      snapshot -> coverage (2x50 upper bound) is picked first; after it lands,
      recurrence is picked -- both asserted from the decision log.
  (b) Refusal memory: a refused trapdoor conversion does NOT win the next round.
  (c) Determinism: two runs over one snapshot yield byte-identical ranked-move
      logs.
  (d) Macro GC: admit macro A (2 uses), then a subsuming macro B -> A is retired
      and corpus_dl drops by exactly dl_macro(A).
  (e) One-off: a pattern used by a single reading never becomes a candidate.

Everything is seeded through the registry (reading_add / macro_add /
demand_upsert / counter_add) on an ISOLATED temp Registry, so the demo never
touches the default DB and never calls an LLM or the kernel check pipeline.

REQUIRES_LLM = False
"""
from __future__ import annotations

import sys
import tempfile

import common
import planner
from buildloop import dl, loop, recurrence
from buildloop.mdl_macros import corpus_dl, dl_macro
from library import Registry

REQUIRES_LLM = False


# --------------------------------------------------------------- builders
def _reg():
    tmp = tempfile.mkdtemp()
    return Registry(db_path=f"{tmp}/reg.sqlite")


def _bound(action, left, cmp_, right):
    return {"kind": "bound", "action": action, "left": left,
            "cmp": cmp_, "right": right}


def _stmt(sid, lf, force="demand", quote="span"):
    return {"id": sid, "force": force, "quote": quote, "lf": lf}


def _reading_json(statements, service="shop"):
    return common.canonical_json({"service": service, "statements": statements})


def _spec(did, atoms, size=64):
    return {"demand_id": did, "kind": "spec-file", "origin": "exogenous",
            "status": "open", "language": "ksy", "features": sorted(atoms),
            "payload_ref": did, "size_bytes": size, "covered_via": None}


def _incumbent(did, size=500):
    return {"demand_id": did, "kind": "caged-incumbent", "origin": "exogenous",
            "status": "open", "language": None, "features": None,
            "payload_ref": did, "size_bytes": size, "covered_via": None}


def _register_codec(reg, atoms):
    reg.register(name="codec-gen", tier="emit-check", spec_language="ksy",
                 output_language="python-codec",
                 spec_grammar={"atoms": sorted(atoms)},
                 emit_entrypoint={"kind": "ksc-python-rw"},
                 contract={"type": "codec-roundtrip"},
                 provenance={"author": "demo-seed"})


def _stub(status):
    def _run(move, snap, registry, backlog, policy, use_corpus, model):
        return {"status": status}
    return _run


def _stub_dispatch(status="stub"):
    return {k: _stub("%s-%s" % (k, status)) for k in loop.KIND_ORDER}


def _last_decision(reg):
    evs = reg.events("scheduler-decision")
    return evs[-1]["payload"]


def _picked(decision):
    for m in decision["moves"]:
        if m["picked"]:
            return m
    return None


def _two_bound_reading(right1, right2):
    return _reading_json([
        _stmt("s1", _bound("sell", "n", "<=", right1)),
        _stmt("s2", _bound("buy", "m", ">=", right2))])


# ============================================================= tooth (a)
def tooth_a() -> bool:
    reg = _reg()
    # 3 readings sharing one contiguous 2-statement demand cluster.
    for i, did in enumerate(("req-1", "req-2", "req-3")):
        reg.reading_add(did, _two_bound_reading(5, 1), f"cert-{i}")
    # an uncovered 2-spec codec group (same missing atoms -> one group).
    reg.demand_upsert(_spec("spec-a", ["uint:1", "uint:2"]))
    reg.demand_upsert(_spec("spec-b", ["uint:1", "uint:2"]))

    disp = _stub_dispatch()
    loop.run_iteration(reg, [], dispatch=disp)
    d1 = _last_decision(reg)
    p1 = _picked(d1)
    kinds1 = {m["kind"] for m in d1["moves"]}
    # 2 specs x UNCOVERED_PENALTY minus the minimal covering-grammar cost (the
    # optimistic-upper-bound deduction, ~1) -> a strong DL reduction, picked
    # over recurrence.
    ok_cov = (p1 is not None and p1["kind"] == "coverage"
              and p1["expected_dl_delta"] < -90.0
              and "recurrence" in kinds1)
    print(f"(a) round 1 picked={p1 and p1['kind']} "
          f"expected_dl_delta={p1 and p1['expected_dl_delta']} "
          f"recurrence-considered={'recurrence' in kinds1} -> "
          f"{'PASS' if ok_cov else 'FAIL'}")

    # land coverage: register a generator covering both specs' atoms.
    _register_codec(reg, ["uint:1", "uint:2", "uint:4"])
    loop.run_iteration(reg, [], dispatch=disp)
    d2 = _last_decision(reg)
    p2 = _picked(d2)
    ok_rec = (p2 is not None and p2["kind"] == "recurrence"
              and "coverage" not in {m["kind"] for m in d2["moves"]})
    print(f"(a) round 2 picked={p2 and p2['kind']} "
          f"(coverage landed) -> {'PASS' if ok_rec else 'FAIL'}")
    return ok_cov and ok_rec


# ============================================================= tooth (b)
def tooth_b() -> bool:
    reg = _reg()
    row = _incumbent("world-machine")
    reg.demand_upsert(row)
    ih = dl.incumbent_hash_of(row)
    reg.counter_add(f"toll:{ih}:calls", 5000.0)     # monotone, high standing toll

    # round 1: toll is argmax and dispatched; the W3 conversion stub REFUSES,
    # so the scheduler records the refusal (the real conversion lands in W4.2).
    r1 = loop.run_iteration(reg, [])
    d1 = _last_decision(reg)
    p1 = _picked(d1)
    round1_ok = (p1 is not None and p1["kind"] == "toll"
                 and r1["status"] == "refused")

    # round 2: SAME snapshot (toll grew, evidence unchanged) -> suppressed,
    # so the doomed conversion does NOT win again.
    loop.run_iteration(reg, [])
    d2 = _last_decision(reg)
    p2 = _picked(d2)
    toll_move = next((m for m in d2["moves"] if m["kind"] == "toll"), None)
    round2_ok = (p2 is None and toll_move is not None
                 and "suppressed_by" in toll_move)
    ok = round1_ok and round2_ok
    print(f"(b) round1 picked=toll & refused={round1_ok}; "
          f"round2 toll suppressed & not picked={round2_ok} -> "
          f"{'PASS' if ok else 'FAIL'}")
    return ok


# ============================================================= tooth (c)
def tooth_c() -> bool:
    reg = _reg()
    for i, did in enumerate(("req-1", "req-2", "req-3")):
        reg.reading_add(did, _two_bound_reading(5, 1), f"cert-{i}")
    reg.demand_upsert(_spec("spec-a", ["uint:1", "uint:2"]))
    reg.demand_upsert(_spec("spec-b", ["uint:1", "uint:2"]))
    row = _incumbent("machine")
    reg.demand_upsert(row)
    reg.counter_add(f"toll:{dl.incumbent_hash_of(row)}:calls", 800.0)

    snap = dl.snapshot(reg)
    _, log1, _ = loop.score_moves(snap, reg)
    _, log2, _ = loop.score_moves(snap, reg)
    ok = common.canonical_json(log1) == common.canonical_json(log2)
    print(f"(c) two rankings over one snapshot byte-identical "
          f"({len(log1)} moves) -> {'PASS' if ok else 'FAIL'}")
    return ok


# ============================================================= tooth (d)
def tooth_d() -> bool:
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
    # A alone: used by both readings.
    uses_a = corpus_dl(readings, reg.macro_table())["reading_uses"].get("A", 0)
    reg.macro_add("B", common.canonical_json(macro_b))   # subsumes A

    before = corpus_dl(readings, reg.macro_table())["total"]
    retired = recurrence.gc_macros(reg, readings)
    after = corpus_dl(readings, reg.macro_table())["total"]

    ok = (uses_a == 2 and "A" in retired
          and "B" in reg.macro_table() and "A" not in reg.macro_table()
          and abs((before - after) - dl_macro(macro_a)) < 1e-6)
    print(f"(d) A uses={uses_a}, retired={retired}, "
          f"corpus_dl drop={round(before - after, 3)} == dl_macro(A)="
          f"{round(dl_macro(macro_a), 3)} -> {'PASS' if ok else 'FAIL'}")
    return ok


# ============================================================= tooth (e)
def tooth_e() -> bool:
    reg = _reg()
    # the 2-'bound' cluster appears in EXACTLY ONE reading (uses=1); a second,
    # structurally different reading shares no cluster.
    reg.reading_add("only", _two_bound_reading(5, 1), "c0")
    reg.reading_add("other", _reading_json(
        [_stmt("q1", {"kind": "quantity", "name": "n", "min": 0, "max": 9},
               force="choice", quote=""),
         _stmt("q2", {"kind": "action", "name": "go"}, force="choice",
               quote="")]), "c1")
    cands = recurrence.mine(list(dl.snapshot(reg).readings.values()),
                            reg.macro_table())
    ok = cands == []
    print(f"(e) one-off pattern -> candidates={len(cands)} -> "
          f"{'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    print("== Combined-Loop W3: miss-typed scheduler teeth ==")
    results = {"(a) coverage-then-recurrence ordering": tooth_a(),
               "(b) refusal memory suppression": tooth_b(),
               "(c) byte-identical ranked-move log": tooth_c(),
               "(d) macro GC": tooth_d(),
               "(e) one-off never a candidate": tooth_e()}
    print("-" * 60)
    for name, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    all_ok = all(results.values())
    print("== %s ==" % ("ALL TEETH PASS" if all_ok else "TEETH FAILED"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

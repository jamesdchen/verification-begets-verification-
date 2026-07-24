"""WS-R teeth -- the UNBOUNDED-statement hammer bench + in-lane ride, Lean-FREE.

Pinned here without a toolchain (the import_rt / anchor fake-backend pattern):

  * ASSEMBLE determinism (byte-compare on a SYNTHETIC queue fixture), the
    ``queued``-status filter, the deterministic cap, and ∀/∃ script routing;
  * every rendered proof byte survives the F0.4 escape gate (defense in depth);
  * RUNGS is single-sourced from ``math_witness`` and equals
    ``kernel.certs.ANCHOR_DISCHARGE_RUNGS`` (the import_rt RUNGS precedent);
  * the RIDE's honest Lean-absent DEFERRAL (the only path local tests cover),
    plus fake-backend closed / statement-cert-demand / tactic-refusal /
    fail-closed-on-audit-silence / deadline-partial verdicts, and verdicts
    byte-stability (no per-row wall time);
  * CONSUME on a synthetic verdicts fixture: the readout schema, the H3
    statement-cert vs tactic-refusal split, per-rung & per-family tables, and
    zero token columns.
"""
from __future__ import annotations

import json
import pathlib

import pytest

import common
from generators import math_witness
from kernel import certs
from buildloop.validate_lean import validate_lean
from tests.fixtures_math_readings import FIXTURES

from bench import bench_hammer as B
from run import hammer_ride as H

import wp_auth_readings


# --------------------------------------------------------------- resolver / queue
def _resolver(goal):
    ref = goal["subject"]["ref"]
    if ref in FIXTURES:
        return B._reading_from_doc(FIXTURES[ref]["reading"])
    return B._reading_from_doc(wp_auth_readings.READINGS[ref])


def _synthetic_queue():
    """A tiny proof queue (the SCHEMA CONTRACT shape): one ∀ goal, one ∃ goal,
    one non-queued row that must be filtered out."""
    return {"derived_from": {}, "goals": [
        {"goal_id": "g_even_add", "source": "bench-certified",
         "subject": {"ref": "even_add", "sha256": "s-even"},
         "status": "queued", "family": "parity", "rung_hint": "decide"},
        {"goal_id": "g_43", "source": "anchor-exists",
         "subject": {"ref": "43_larger_integer_exists", "sha256": "s-43"},
         "status": "queued", "family": "exists", "rung_hint": "decide"},
        {"goal_id": "g_infra", "source": "rt-failed",
         "subject": {"ref": "nope", "sha256": "s-x"},
         "status": "infra-refused", "family": "other"},
    ], "honesty": "..."}


def _write_queue(tmp_path, queue=None):
    qp = tmp_path / "proof_queue.json"
    qp.write_text(json.dumps(queue or _synthetic_queue()))
    return qp


# ===========================================================================
# 1. RUNGS single-source equality (the import_rt precedent).
# ===========================================================================
def test_rungs_single_sourced_and_equal_anchor_discharge():
    assert B.RUNGS is math_witness.RUNGS                 # imported, never redeclared
    assert tuple(B.RUNGS) == tuple(certs.ANCHOR_DISCHARGE_RUNGS)
    assert not any("native_decide" in r for r in B.RUNGS)


# ===========================================================================
# 2. ASSEMBLE: determinism, queued-filter, cap, routing.
# ===========================================================================
def test_assemble_filters_queued_and_routes_shapes(tmp_path):
    qp = _write_queue(tmp_path)
    batch = B.assemble(qp, resolver=_resolver)
    assert batch["schema"] == B.BATCH_SCHEMA
    assert batch["n_queued"] == 2                        # the infra-refused row gone
    ids = {g["goal_id"]: g for g in batch["goals"]}
    assert set(ids) == {"g_even_add", "g_43"}
    assert ids["g_even_add"]["shape"] == "forall"
    assert ids["g_43"]["shape"] == "exists"
    # ∀ goal has one script per rung, in ladder order.
    assert [s["discharge"] for s in ids["g_even_add"]["scripts"]] == list(B.RUNGS)
    # ∃ goal routes via the anchor kernel-leg emitter (43 emits a witness proof).
    assert ids["g_43"]["scripts"], "source 43 must emit a witness ladder"
    assert "refine" in ids["g_43"]["scripts"][0]["lean_text"]   # template machinery
    # statements are the `:= sorry` compiled form.
    assert ids["g_even_add"]["statement_lean_text"].endswith(" := sorry")


def test_assemble_byte_deterministic(tmp_path):
    qp = _write_queue(tmp_path)
    a = B.render_batch_json(B.assemble(qp, resolver=_resolver))
    b = B.render_batch_json(B.assemble(qp, resolver=_resolver))
    assert a == b                                        # byte-identical re-emit


def test_assemble_cap_is_deterministic_prefix(tmp_path):
    qp = _write_queue(tmp_path)
    batch = B.assemble(qp, resolver=_resolver, cap=1)
    assert len(batch["goals"]) == 1
    assert batch["goals"][0]["goal_id"] == "g_even_add"  # queue order, first cap
    assert batch["cap"] == 1


def test_assemble_missing_queue_is_empty_bootstrap():
    batch = B.assemble(None)
    assert batch["goals"] == [] and batch["n_queued"] == 0
    assert batch["queue_sha256"] is None                 # honest, no crash


def test_assemble_unresolved_ref_recorded_not_crashed(tmp_path):
    q = _synthetic_queue()
    q["goals"].append({"goal_id": "g_ghost", "source": "anchor-exists",
                       "subject": {"ref": "ghost_source", "sha256": "s-g"},
                       "status": "queued", "family": "other"})
    qp = _write_queue(tmp_path, q)
    batch = B.assemble(qp, resolver=B.default_resolver)   # real corpus resolver
    assert "g_ghost" in batch["unresolved"]              # honest, never conflated


def test_assemble_queue_sha_pins_the_input(tmp_path):
    qp = _write_queue(tmp_path)
    batch = B.assemble(qp, resolver=_resolver)
    assert batch["queue_sha256"] == common.sha256_bytes(qp.read_bytes())


def test_rendered_bytes_pass_escape_gate(tmp_path):
    qp = _write_queue(tmp_path)
    batch = B.assemble(qp, resolver=_resolver)
    for g in batch["goals"]:
        ok, why = validate_lean(g["statement_lean_text"])
        assert ok, (g["goal_id"], why)
        for s in g["scripts"]:
            ok, why = validate_lean(s["lean_text"])
            assert ok, (g["goal_id"], s["discharge"], why)


def test_forall_prelude_is_intro_and_rung_only(tmp_path):
    # 48_db_sum: ∀ (a b g), g|a -> g|b -> g|(a+b).  Only intro + the rung.
    r = B._reading_from_doc(wp_auth_readings.READINGS["48_db_sum"])
    from generators.math_compile import compile_math_reading
    scripts = B._forall_scripts(r, compile_math_reading(r)["lean_text"])
    for s in scripts:
        body = s["lean_text"].split(":= by", 1)[1]
        # no tactic outside the closed vocabulary {intro} + the rungs.
        for line in body.strip().splitlines():
            tok = line.strip()
            assert tok.startswith("intro ") or tok == s["discharge"], tok
        assert "native_decide" not in s["lean_text"]


# ===========================================================================
# 3. the RIDE: fake-backend verdict mapping + honest deferral.
# ===========================================================================
class _FakeBackend:
    """Deterministic injected backend (no lean, no sandbox) with the frozen
    ``elaborate``/``recheck`` signature.  ``close_rung`` names the rung whose
    proof script elaborates and kernel-replays; ``stmt_ok`` gates the statement
    stage; ``audited`` toggles the run-2 axiom audit (auditor-silence)."""

    def __init__(self, *, unavailable=False, stmt_ok=True, close_rung=None,
                 recheck_ok=True, audited=True, axioms=("sorryAx",)):
        self.unavailable = unavailable
        self.stmt_ok = stmt_ok
        self.close_rung = close_rung
        self.recheck_ok = recheck_ok
        self.audited = audited
        self.axioms = list(axioms)
        self.calls = []

    def elaborate(self, text, *, expect_sorry):
        self.calls.append(("elaborate", expect_sorry))
        if self.unavailable:
            return {"ok": False, "unavailable": True, "olean_path": None}
        if text.rstrip().endswith(":= sorry"):
            return {"ok": self.stmt_ok, "unavailable": False,
                    "olean_path": "/olean/stmt"}
        last = text.rstrip().splitlines()[-1].strip()
        ok = self.close_rung is not None and last == self.close_rung
        return {"ok": ok, "unavailable": False, "olean_path": "/olean/" + last}

    def recheck(self, olean_path):
        self.calls.append(("recheck", olean_path))
        if self.unavailable:
            return {"ok": False, "unavailable": True, "audited": False,
                    "axioms": []}
        return {"ok": self.recheck_ok, "unavailable": False,
                "audited": self.audited, "axioms": list(self.axioms)}


def _batch(tmp_path):
    return B.assemble(_write_queue(tmp_path), resolver=_resolver)


def test_ride_defers_when_lean_absent(tmp_path):
    # The definition-of-done local path (import_rt precedent): unavailable backend
    # -> an all-not-run `deferred` artifact, no exception.
    batch = _batch(tmp_path)
    v = H.run_ride(batch, backend=_FakeBackend(unavailable=True))
    assert v["status"] == "deferred"
    assert v["schema"] == B.VERDICTS_SCHEMA
    assert len(v["rows"]) == len(batch["goals"])
    for row in v["rows"]:
        assert row["elaborated"] is None                # not-run, honestly null
        assert row["replayed"] is None and row["axioms"] is None
    assert "certificates" in v["evidence_note"].lower()


def test_ride_real_default_backend_defers_here():
    # This container is Lean-absent: the default LeanBackend honest-degrades.
    assert common.lean_available() is False
    batch = {"schema": B.BATCH_SCHEMA, "goals": [
        {"goal_id": "g", "statement_lean_text": "theorem t : True := sorry",
         "scripts": [{"discharge": "decide",
                      "lean_text": "theorem t : True := by decide"}]}]}
    v = H.run_ride(batch)                               # no injected backend
    assert v["status"] == "deferred"
    assert v["rows"][0]["elaborated"] is None


def test_ride_closes_goal_first_success(tmp_path):
    batch = _batch(tmp_path)
    v = H.run_ride(batch, backend=_FakeBackend(close_rung="decide"))
    assert v["status"] == "complete"
    for row in v["rows"]:
        assert row["elaborated"] is True and row["replayed"] is True
        assert row["axioms"] == ["sorryAx"]
        assert row["script"].rstrip().endswith("decide")   # the winning rung
    assert set(v["rows"][0]) == {"goal_id", "script", "elaborated",
                                 "replayed", "axioms"}       # frozen 5-key schema


def test_ride_statement_cert_demand_when_statement_fails(tmp_path):
    batch = _batch(tmp_path)
    v = H.run_ride(batch, backend=_FakeBackend(stmt_ok=False))
    for row in v["rows"]:
        assert row["elaborated"] is False               # statement stage failed
        assert row["replayed"] is False and row["script"] is None


def test_ride_tactic_refusal_when_no_rung_closes(tmp_path):
    batch = _batch(tmp_path)
    v = H.run_ride(batch, backend=_FakeBackend(close_rung=None))
    for row in v["rows"]:
        assert row["elaborated"] is True and row["replayed"] is False


def test_ride_fail_closed_on_audit_silence(tmp_path):
    # A rung that elaborates + rechecks OK but reports NO audit is NOT a close.
    batch = _batch(tmp_path)
    v = H.run_ride(batch, backend=_FakeBackend(close_rung="decide", audited=False))
    for row in v["rows"]:
        assert row["replayed"] is False                 # auditor silence -> no verdict


def test_ride_deadline_writes_partial_not_run(tmp_path):
    batch = _batch(tmp_path)
    ticks = iter([0.0, 0.0, 100.0, 100.0, 100.0])       # 2nd goal is past budget
    v = H.run_ride(batch, backend=_FakeBackend(close_rung="decide"),
                   deadline_seconds=10.0, clock=lambda: next(ticks))
    assert v["status"] == "partial"
    assert v["rows"][0]["elaborated"] is True            # first goal ran
    assert v["rows"][1]["elaborated"] is None            # remaining -> not-run


def test_ride_verdicts_byte_stable_no_wall_time(tmp_path):
    batch = _batch(tmp_path)
    a = H.render_verdicts_json(H.run_ride(batch, backend=_FakeBackend(close_rung="decide")))
    b = H.render_verdicts_json(H.run_ride(batch, backend=_FakeBackend(close_rung="decide")))
    assert a == b
    # no per-row timing: rows carry EXACTLY the frozen 5 keys, nothing time-like.
    for row in H.run_ride(batch, backend=_FakeBackend(close_rung="decide"))["rows"]:
        assert set(row) == {"goal_id", "script", "elaborated", "replayed", "axioms"}


# ===========================================================================
# 4. CONSUME: synthetic verdicts fixture -> readout schema + H3 split.
# ===========================================================================
def _batch_and_verdicts(tmp_path):
    batch = _batch(tmp_path)
    gids = [g["goal_id"] for g in batch["goals"]]
    # goal 0: closed by 'decide'; goal 1: statement-cert demand.
    closing = batch["goals"][0]["scripts"][0]["lean_text"]
    verdicts = {"schema": B.VERDICTS_SCHEMA, "status": "complete",
                "lean_available": False, "rows": [
                    {"goal_id": gids[0], "script": closing,
                     "elaborated": True, "replayed": True, "axioms": ["sorryAx"]},
                    {"goal_id": gids[1], "script": None,
                     "elaborated": False, "replayed": False, "axioms": []}]}
    return batch, verdicts


def test_consume_readout_schema_and_h3_split(tmp_path):
    batch, verdicts = _batch_and_verdicts(tmp_path)
    ro = B.build_readout(verdicts, batch)
    assert ro["schema"] == B.READOUT_SCHEMA
    assert ro["totals"]["n_closed"] == 1
    assert ro["totals"]["n_statement_cert_demand"] == 1  # elaborated=False, separate
    assert ro["totals"]["n_tactic_refused"] == 0
    # per-rung closure names the closing rung.
    assert ro["per_rung"]["decide"]["closed"] == 1
    # per-family tables carry the family from the batch.
    assert ro["per_family"]["parity"]["closed"] == 1
    assert ro["per_family"]["exists"]["statement_cert_demand"] == 1
    # token columns present AND zero (LLM off).
    assert ro["tokens"] == {"prompt": 0, "completion": 0, "total": 0}
    # the demand lists are first-class.
    assert ro["statement_cert_demand"] == [verdicts["rows"][1]["goal_id"]]


def test_consume_tactic_refusal_distinct_from_stmt_demand(tmp_path):
    batch = _batch(tmp_path)
    gid = batch["goals"][0]["goal_id"]
    verdicts = {"schema": B.VERDICTS_SCHEMA, "status": "complete",
                "lean_available": False, "rows": [
                    {"goal_id": gid, "script": None, "elaborated": True,
                     "replayed": False, "axioms": []}]}
    ro = B.build_readout(verdicts, batch)
    assert ro["totals"]["n_tactic_refused"] == 1
    assert ro["totals"]["n_statement_cert_demand"] == 0
    assert ro["tactic_refusals"] == [gid]


def test_consume_missing_verdicts_is_not_yet_run_bootstrap(tmp_path):
    ro = B.consume(verdicts_path=tmp_path / "nope.json",
                   batch_path=tmp_path / "nobatch.json")
    assert ro["verdicts_status"] == "not-run"
    assert ro["totals"] == {"n_goals": 0, "n_closed": 0,
                            "n_statement_cert_demand": 0,
                            "n_tactic_refused": 0, "n_not_run": 0}


def test_readout_md_renders_both_tables(tmp_path):
    batch, verdicts = _batch_and_verdicts(tmp_path)
    md = B.render_readout_md(B.build_readout(verdicts, batch))
    assert "Per-rung closure" in md and "Per-family closure" in md
    assert "Statement-cert demand" in md and "Tokens (LLM off)" in md


def test_consume_readout_byte_stable(tmp_path):
    batch, verdicts = _batch_and_verdicts(tmp_path)
    a = common.canonical_json(B.build_readout(verdicts, batch))
    b = common.canonical_json(B.build_readout(verdicts, batch))
    assert a == b


# ===========================================================================
# 5. end-to-end (Lean-free): assemble -> ride(defer) -> consume(bootstrap).
# ===========================================================================
def test_end_to_end_lean_absent_bootstrap(tmp_path):
    batch = _batch(tmp_path)
    verdicts = H.run_ride(batch, backend=_FakeBackend(unavailable=True))
    ro = B.build_readout(verdicts, batch)
    assert ro["verdicts_status"] == "deferred"
    assert ro["totals"]["n_not_run"] == len(batch["goals"])
    assert ro["totals"]["n_closed"] == 0                # honest not-yet-run


# ===========================================================================
# 6. the COMMITTED bootstrap artifacts are byte-reproducible (the frontier /
#    anchor committed-artifact tooth) and honestly not-yet-run.
# ===========================================================================
_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_committed_bootstrap_batch_reproduces_byte_for_byte():
    committed = (_ROOT / "results" / "hammer_batch.json").read_text()
    assert B.render_batch_json(B.assemble(None)) == committed   # empty bootstrap


def test_committed_bootstrap_is_honest_not_yet_run():
    v = json.loads((_ROOT / "results" / "hammer_verdicts.json").read_text())
    ro = json.loads((_ROOT / "results" / "hammer_readout.json").read_text())
    assert v["status"] == "not-run" and v["rows"] == []
    assert ro["totals"]["n_closed"] == 0
    assert ro["tokens"] == {"prompt": 0, "completion": 0, "total": 0}


def test_committed_readout_reproduces_from_committed_inputs():
    batch = json.loads((_ROOT / "results" / "hammer_batch.json").read_text())
    verdicts = json.loads((_ROOT / "results" / "hammer_verdicts.json").read_text())
    committed = (_ROOT / "results" / "hammer_readout.json").read_text()
    assert common.canonical_json(B.build_readout(verdicts, batch)) + "\n" == committed

"""WP-LI2 teeth -- the RT differential oracle (run/import_rt.py), Lean-FREE.

What is pinned here, without a toolchain (the fake-backend pattern of
tests/test_lean_backend.py / test_anchor_runner.py -- a tiny injected runner,
never real lean):

  * probe-file text generation is correct AND deterministic (golden strings
    for a fixture reading; the frozen IFF_LADDER, whose witness rungs are the
    generators/math_witness.py RUNGS precedent verbatim);
  * the verdict mapping: defeq-pass -> defeq; defeq-fail + iff-pass -> proved
    (first closing rung recorded); both-fail -> failed WITH the first-class
    ``rt-differential-failure`` event present; runner-unavailable / lean
    absent -> deferred (honest, never a failure);
  * batch resumability (settled verdicts are never re-probed; deferred rows
    re-run) and report byte-stability (write twice, compare bytes);
  * the Lean-absent lane: ``rt_batch`` with no injected runner produces an
    all-deferred report without error (the statement-cert deferral
    discipline).

The single real-Lean smoke test is gated with the repo's skip-with-reason
convention (``skipif(not common.lean_available())`` -- ⚠X7): it never fails on
a toolchain-less container, and on a Lean host it exercises the true
``LeanBackend.elaborate`` probe path end to end.
"""
from __future__ import annotations

import json
import pathlib

import pytest

import common
from generators import math_witness
from run import import_rt
from tests.fixtures_math_readings import FIXTURES

# ---------------------------------------------------------------------------
# Fixture material: the hand-written `even_add` reading (the X16 single fixture
# home) posing as the authored reading of a fictional original declaration.
# ---------------------------------------------------------------------------
DECL = "Nat.even_add_orig"
READING = FIXTURES["even_add"]["reading"]
# The "original" pretty-printed statement (the WP-LI0 queue's statement_pp):
# deliberately NOT byte-equal to the compiled form (bare ∧/→, no full parens),
# so defeq/iff probes are a genuine differential, not a string echo.
PP = "∀ (m : Nat) (n : Nat), Even m ∧ Even n → Even (m + n)"

# The compiled prop of `even_add` under the canonical F1.2 emission rules.
C_PROP = "∀ (m : Nat) (n : Nat), ((Even m) ∧ (Even n)) → (Even (m + n))"

_HB = common.LEAN_MAXHEARTBEATS


# ------------------------------------------------------------ fake runners
def make_runner(*, defeq_ok=False, pass_rungs=(), unavailable=False):
    """A deterministic injected fake with the runner signature
    ``runner(probe_text) -> {"ok", "unavailable", "detail"}`` -- the repo's
    fake-backend test pattern; no lean, no sandbox, no subprocess."""
    calls = []

    def runner(text):
        calls.append(text)
        if unavailable:
            return {"ok": False, "unavailable": True, "detail": ""}
        if ":= @" in text:
            return {"ok": bool(defeq_ok), "unavailable": False,
                    "detail": "fake-defeq"}
        for rung in import_rt.IFF_LADDER:
            if text.rstrip("\n").endswith(":= " + rung):
                return {"ok": rung in pass_rungs, "unavailable": False,
                        "detail": "fake-iff:" + rung}
        return {"ok": False, "unavailable": False, "detail": "fake-unknown"}

    runner.calls = calls
    return runner


# ===========================================================================
# 1. probe-file text generation: golden strings + determinism.
# ===========================================================================
def test_compiled_prop_extraction():
    assert import_rt.compiled_prop(
        f"theorem even_add : {C_PROP} := sorry") == C_PROP
    with pytest.raises(ValueError):
        import_rt.compiled_prop("def foo := 3")
    with pytest.raises(ValueError):
        import_rt.compiled_prop("theorem t : p := rfl")   # no := sorry suffix


def test_defeq_probe_golden():
    got = import_rt.defeq_probe_text(DECL, C_PROP)
    assert got == (
        f"set_option maxHeartbeats {_HB} in\n"
        "example : ∀ (m : Nat) (n : Nat), ((Even m) ∧ (Even n)) → "
        "(Even (m + n)) := @Nat.even_add_orig\n")


def test_iff_probe_golden_first_rung():
    got = import_rt.iff_probe_text(C_PROP, PP, "Iff.rfl")
    assert got == (
        f"set_option maxHeartbeats {_HB} in\n"
        "example : (∀ (m : Nat) (n : Nat), ((Even m) ∧ (Even n)) → "
        "(Even (m + n))) ↔ (∀ (m : Nat) (n : Nat), Even m ∧ Even n → "
        "Even (m + n)) := Iff.rfl\n")


def test_probe_text_deterministic_and_distinct():
    a = [import_rt.iff_probe_text(C_PROP, PP, r) for r in import_rt.IFF_LADDER]
    b = [import_rt.iff_probe_text(C_PROP, PP, r) for r in import_rt.IFF_LADDER]
    assert a == b                                # identical bytes on re-emit
    assert len(set(a)) == len(a)                 # one distinct probe per rung
    assert (import_rt.defeq_probe_text(DECL, C_PROP)
            == import_rt.defeq_probe_text(DECL, C_PROP))


def test_iff_probe_refuses_unknown_rung():
    # The ladder is FROZEN: an off-ladder rung (open-ended search like exact?)
    # can never be emitted.
    with pytest.raises(ValueError):
        import_rt.iff_probe_text(C_PROP, PP, "by exact?")


def test_ladder_frozen_and_witness_rung_precedent():
    # Pinned verbatim (WP-LI2: "the ladder is frozen, not open-ended").
    assert import_rt.IFF_LADDER == (
        "Iff.rfl",
        "by constructor <;> intro h <;> exact h",
        "by decide", "by omega", "by norm_num", "by simp")
    # The witness rungs ARE the math_witness RUNGS precedent, in pinned order.
    assert import_rt.IFF_LADDER[2:] == tuple(
        "by " + r for r in math_witness.RUNGS)
    # native_decide is escape-gate-forbidden and must never appear.
    assert not any("native_decide" in r for r in import_rt.IFF_LADDER)


def test_probes_pass_the_escape_gate():
    # Our OWN probe emission must survive F0.4 (defense in depth is real).
    from buildloop.validate_lean import validate_lean
    ok, reason = validate_lean(import_rt.defeq_probe_text(DECL, C_PROP))
    assert ok, reason
    for rung in import_rt.IFF_LADDER:
        ok, reason = validate_lean(import_rt.iff_probe_text(C_PROP, PP, rung))
        assert ok, reason


# ===========================================================================
# 2. verdict mapping via the injected fake runner.
# ===========================================================================
def test_verdict_defeq_fast_path():
    r = make_runner(defeq_ok=True)
    res = import_rt.rt_check(DECL, PP, READING, runner=r)
    assert res.verdict == "defeq"
    assert res.closed_by == "defeq"
    assert len(res.probe_transcripts) == 1          # fast path stops here
    assert res.probe_transcripts[0]["probe"] == "defeq"
    assert res.probe_transcripts[0]["ok"] is True
    assert res.statement_hash_compiled
    assert res.lean_toolchain_hash == common.lean_toolchain_hash()
    assert len(r.calls) == 1


def test_verdict_proved_first_rung():
    r = make_runner(defeq_ok=False, pass_rungs=("Iff.rfl",))
    res = import_rt.rt_check(DECL, PP, READING, runner=r)
    assert res.verdict == "proved"
    assert res.closed_by == "Iff.rfl"
    assert [t["ok"] for t in res.probe_transcripts] == [False, True]


def test_verdict_proved_late_rung_records_ladder_walk():
    r = make_runner(defeq_ok=False, pass_rungs=("by omega",))
    res = import_rt.rt_check(DECL, PP, READING, runner=r)
    assert res.verdict == "proved"
    assert res.closed_by == "by omega"
    # defeq + Iff.rfl + constructor-rung + decide + omega, in ladder order.
    assert [t["rung"] for t in res.probe_transcripts] == [
        None, "Iff.rfl", "by constructor <;> intro h <;> exact h",
        "by decide", "by omega"]
    assert [t["ok"] for t in res.probe_transcripts] == [
        False, False, False, False, True]


def test_verdict_failed_emits_first_class_event():
    events = []
    r = make_runner()                               # everything fails
    res = import_rt.rt_check(DECL, PP, READING, runner=r,
                             event_sink=lambda k, p: events.append((k, p)))
    assert res.verdict == "failed"
    assert res.closed_by is None
    # FULL transcript: 1 defeq + every ladder rung; nothing dropped.
    assert len(res.probe_transcripts) == 1 + len(import_rt.IFF_LADDER)
    # The measured-mistranslation event is present, first-class, and carries
    # the full transcript (the disagreement-logging discipline).
    assert [k for k, _ in events] == [import_rt.EVENT_KIND]
    payload = events[0][1]
    assert payload["decl_name"] == DECL
    assert payload["verdict"] == "failed"
    assert payload["probe_transcripts"] == res.probe_transcripts
    assert "mistranslation" in payload["note"]


def test_verdict_deferred_on_unavailable_runner():
    events = []
    r = make_runner(unavailable=True)
    res = import_rt.rt_check(DECL, PP, READING, runner=r,
                             event_sink=lambda k, p: events.append((k, p)))
    assert res.verdict == "deferred"
    assert res.lean_toolchain_hash is None          # no probe actually ran
    assert events == []                             # a deferral is NOT a failure
    assert res.probe_transcripts[0]["ok"] is None


@pytest.mark.skipif(common.lean_available(),
                    reason="lean toolchain PRESENT -- absent-path test")
def test_verdict_deferred_lean_absent_default_runner():
    res = import_rt.rt_check(DECL, PP, READING)     # runner=None, no toolchain
    assert res.verdict == "deferred"
    assert res.lean_toolchain_hash is None
    assert all(t["ok"] is None for t in res.probe_transcripts)
    assert all("deferred" in t["detail"] for t in res.probe_transcripts)


def test_uncompilable_reading_is_failed_with_event():
    events = []
    res = import_rt.rt_check("Nat.broken", "n = n", {"theorem": "broken"},
                             runner=make_runner(defeq_ok=True),
                             event_sink=lambda k, p: events.append((k, p)))
    assert res.verdict == "failed"
    assert res.probe_transcripts[0]["probe"] == "compile"
    assert [k for k, _ in events] == [import_rt.EVENT_KIND]


def test_rt_check_deterministic():
    a = import_rt.rt_check(DECL, PP, READING, runner=make_runner())
    b = import_rt.rt_check(DECL, PP, READING, runner=make_runner())
    assert a == b


# ===========================================================================
# 3. batch: report writing, resumability, byte-stability, Lean-absent lane.
# ===========================================================================
def _write_fixture_batch(tmp_path):
    """A tiny queue + readings dir: two authored decls sharing the even_add
    reading, one still-pending decl (must be ignored), one authored decl with
    a MISSING reading artifact (must be recorded, not conflated)."""
    queue = tmp_path / "queue.jsonl"
    readings = tmp_path / "readings"
    readings.mkdir()
    rows = [
        {"decl_name": "Nat.even_add_b", "module": "M", "statement_pp": PP,
         "statement_hash": "sh-b", "status": "authored"},
        {"decl_name": "Nat.even_add_a", "module": "M", "statement_pp": PP,
         "statement_hash": "sh-a", "status": "authored"},
        {"decl_name": "Nat.still_pending", "module": "M", "statement_pp": PP,
         "statement_hash": "sh-p", "status": "pending"},
        {"decl_name": "Nat.reading_lost", "module": "M", "statement_pp": PP,
         "statement_hash": "sh-lost", "status": "authored"},
    ]
    queue.write_text("".join(common.canonical_json(r) + "\n" for r in rows))
    for decl in ("Nat.even_add_a", "Nat.even_add_b"):
        # the WP-LI1 persist_reading artifact shape; only "reading" is load-
        # bearing for RT.
        doc = {"decl_name": decl, "statement_hash": "sh",
               "gloss": None, "reading": READING, "model_id": "fake",
               "encoding_version": 1}
        (readings / (decl + ".json")).write_text(common.canonical_json(doc))
    return queue, readings


def test_batch_report_verdicts_and_ordering(tmp_path):
    queue, readings = _write_fixture_batch(tmp_path)
    out = tmp_path / "rt_report.json"
    summary = import_rt.rt_batch(queue, readings, out,
                                 runner=make_runner(defeq_ok=True))
    assert summary["status"] == "completed"
    assert summary["by_verdict"] == {"defeq": 2, "proved": 0, "failed": 0,
                                     "deferred": 0}
    assert summary["missing_readings"] == ["Nat.reading_lost"]
    report = json.loads(out.read_text())
    assert report["schema"] == import_rt.SCHEMA
    assert report["channel"] == "rt-differential"
    # deterministic decl-name ordering (b was listed first in the queue).
    assert [r["decl_name"] for r in report["rows"]] == [
        "Nat.even_add_a", "Nat.even_add_b"]
    # the R1 anchor hash is carried from the queue row, never recomputed.
    assert [r["statement_hash_original"] for r in report["rows"]] == [
        "sh-a", "sh-b"]


def test_batch_byte_stability_write_twice(tmp_path):
    queue, readings = _write_fixture_batch(tmp_path)
    out = tmp_path / "rt_report.json"
    import_rt.rt_batch(queue, readings, out, runner=make_runner(defeq_ok=True))
    first = out.read_bytes()
    # Second invocation over the same inputs: byte-identical report.
    import_rt.rt_batch(queue, readings, out, runner=make_runner(defeq_ok=True))
    assert out.read_bytes() == first
    # And a from-scratch rebuild at a different path is byte-identical too.
    out2 = tmp_path / "rt_report_2.json"
    import_rt.rt_batch(queue, readings, out2,
                       runner=make_runner(defeq_ok=True))
    assert out2.read_bytes() == first


def test_batch_resumability_settled_rows_never_reprobed(tmp_path):
    queue, readings = _write_fixture_batch(tmp_path)
    out = tmp_path / "rt_report.json"
    import_rt.rt_batch(queue, readings, out, runner=make_runner(defeq_ok=True))
    first = out.read_bytes()
    # A second run with a runner that would FAIL everything: settled (non-
    # deferred) rows are skipped -- the runner is never called, the report is
    # unchanged.
    r2 = make_runner()
    summary = import_rt.rt_batch(queue, readings, out, runner=r2)
    assert r2.calls == []
    assert summary["n_resumed"] == 2
    assert summary["n_checked"] == 0
    assert out.read_bytes() == first


def test_batch_deferred_rows_rerun(tmp_path):
    queue, readings = _write_fixture_batch(tmp_path)
    out = tmp_path / "rt_report.json"
    # wave 1: toolchain "absent" (unavailable runner) -> all deferred.
    s1 = import_rt.rt_batch(queue, readings, out,
                            runner=make_runner(unavailable=True))
    assert s1["by_verdict"]["deferred"] == 2
    # wave 2: toolchain "up" -> deferred rows re-run and settle.
    s2 = import_rt.rt_batch(queue, readings, out,
                            runner=make_runner(defeq_ok=True))
    assert s2["n_resumed"] == 0                      # deferred is never settled
    assert s2["by_verdict"] == {"defeq": 2, "proved": 0, "failed": 0,
                                "deferred": 0}


def test_batch_failed_flips_queue_only_when_asked(tmp_path):
    queue, readings = _write_fixture_batch(tmp_path)
    out = tmp_path / "rt_report.json"
    events = []
    summary = import_rt.rt_batch(queue, readings, out, runner=make_runner(),
                                 event_sink=lambda k, p: events.append(k),
                                 update_queue=True)
    assert summary["by_verdict"]["failed"] == 2
    assert summary["failed_decls"] == ["Nat.even_add_a", "Nat.even_add_b"]
    # one first-class event per failed row -- never silently dropped.
    assert events == [import_rt.EVENT_KIND, import_rt.EVENT_KIND]
    # the failed rows flipped to refused; pending/missing rows untouched.
    status = {r["decl_name"]: r["status"]
              for r in map(json.loads, queue.read_text().splitlines())}
    assert status == {"Nat.even_add_a": "refused",
                      "Nat.even_add_b": "refused",
                      "Nat.still_pending": "pending",
                      "Nat.reading_lost": "authored"}


@pytest.mark.skipif(common.lean_available(),
                    reason="lean toolchain PRESENT -- absent-path test")
def test_batch_lean_absent_all_deferred_without_error(tmp_path):
    # The definition-of-done lane: a fixture queue, NO injected runner, lean
    # absent -> an all-deferred report, no exception, honest bookkeeping.
    queue, readings = _write_fixture_batch(tmp_path)
    out = tmp_path / "rt_report.json"
    summary = import_rt.rt_batch(queue, readings, out)
    assert summary["by_verdict"] == {"defeq": 0, "proved": 0, "failed": 0,
                                     "deferred": 2}
    report = json.loads(out.read_text())
    assert report["lean_available"] is False
    assert all(r["verdict"] == "deferred" for r in report["rows"])
    assert all(r["lean_toolchain_hash"] is None for r in report["rows"])


# ===========================================================================
# 4. real-Lean smoke (skip-with-reason on a toolchain-less container, ⚠X7).
# ===========================================================================
@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent")
def test_rt_smoke_real_lean_nat_dvd_refl():
    """End-to-end RT against a REAL pinned-surface declaration: a hand-written
    reading of ``Nat.dvd_refl`` must come back defeq or proved through the
    genuine sandboxed ``LeanBackend.elaborate`` probe path."""
    reading = {"theorem": "nat_dvd_refl", "statements": [
        {"id": "o_n", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Nat"}},
        {"id": "op_dvd", "force": "presupposition", "quote": "∣",
         "lf": {"kind": "operator", "word": "dvd", "carrier": "Nat"}},
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "q", "force": "presupposition", "quote": "∀ (n : Nat)",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "c", "force": "demand", "quote": "n ∣ n",
         "lf": {"kind": "conclusion",
                "pred": {"op": "dvd", "args": [{"ref": "n"}, {"ref": "n"}]}}},
    ]}
    res = import_rt.rt_check("Nat.dvd_refl", "∀ (n : Nat), n ∣ n", reading)
    assert res.verdict in ("defeq", "proved"), res.probe_transcripts
    assert res.lean_toolchain_hash == common.lean_toolchain_hash()

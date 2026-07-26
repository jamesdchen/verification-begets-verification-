"""Teeth for the AUTHORING kind of the `[lean-hammer]` ride (PLAN_HAMMER H1.3).

Pinned WITHOUT a toolchain (the `tests/test_algebra_shadow.py` stub-backend and
`tests/test_hammer_bench.py` fake-backend patterns), because the whole point of
the kind is that it works in a container that cannot get Lean:

  * the authoring kind ROUND-TRIPS -- candidate queue -> batch -> ride ->
    verdicts -> session-side report;
  * BYTE COMPATIBILITY, which is the load-bearing property: with no authoring
    entries the batch, the verdicts and the readout md are byte-for-byte what
    they were before the kind existed (the committed-artifact reproduction teeth
    of `tests/test_hammer_bench.py` depend on exactly this);
  * a candidate that fails the F0.4 ESCAPE GATE is refused BEFORE elaboration
    and the backend is never touched -- asserted on the stub's own call log,
    not inferred from the verdict;
  * the two things elaboration alone does NOT establish: a `sorry`-bearing
    candidate is never reported proved (`sorryAx` in the audited set), and a
    candidate whose claimed declarations are absent from its OWN text FAILS --
    a proof that renames its own theorem must not pass;
  * fail-CLOSED on audit silence, honest NOT-RUN on a Lean-absent backend,
    determinism, and no clock anywhere in the emitted bytes.

The one genuinely Lean-requiring node carries the repo's skipif idiom
(`skipif(not common.lean_available())`, ⚠X7): it never fails on a Lean-absent
container, and it never silently passes there either.
"""
from __future__ import annotations

import json
import pathlib

import pytest

import common
from bench import bench_hammer as B
from run import hammer_ride as H
from run import reflect_ride as R

_ROOT = pathlib.Path(__file__).resolve().parent.parent


# --------------------------------------------------------------- fixtures
_GOOD_TEXT = ("def tmTwice (t : Tm) : Tm := Tm.add t t\n"
              "\n"
              "theorem evalTm_tmTwice (env : Nat -> Int) (t : Tm) :\n"
              "    evalTm env (tmTwice t) = evalTm env t + evalTm env t := rfl\n")

_SORRY_TEXT = ("theorem evalTm_bogus (env : Nat -> Int) (t : Tm) :\n"
               "    evalTm env t = evalTm env t + 1 := by sorry\n")

# Claims `evalTm_tmTwice`, introduces `evalTm_renamed` -- the rename control.
_RENAMED_TEXT = ("def tmTwice (t : Tm) : Tm := Tm.add t t\n"
                 "\n"
                 "theorem evalTm_renamed (env : Nat -> Int) (t : Tm) :\n"
                 "    evalTm env (tmTwice t) = evalTm env t + evalTm env t"
                 " := rfl\n")

# `macro_rules` is a blocklisted token: the gate refuses this before any backend.
_ESCAPE_TEXT = ("macro_rules | `(tactic| trivial) => `(tactic| rfl)\n"
                "theorem t_escape : True := trivial\n")


def _cand(cid, text, declares, origin="test"):
    return {"candidate_id": cid, "declares": list(declares),
            "module_text": text, "origin": origin}


def _write_candidates(tmp_path, candidates):
    p = tmp_path / "reflect_candidates.json"
    p.write_text(json.dumps({"schema": B.CANDIDATES_SCHEMA,
                             "candidates": candidates}))
    return p


class _StubBackend:
    """Deterministic injected backend with the frozen ``elaborate``/``recheck``
    signature and NO Lean (the algebra-shadow stub pattern).  ``calls`` is the
    tooth that proves the escape gate short-circuits before the backend."""

    def __init__(self, *, unavailable=False, elaborate_ok=True,
                 recheck_ok=True, audited=True, axioms=("propext",),
                 detail="stub transcript tail"):
        self.unavailable = unavailable
        self.elaborate_ok = elaborate_ok
        self.recheck_ok = recheck_ok
        self.audited = audited
        self.axioms = list(axioms)
        self.detail = detail
        self.calls = []

    def elaborate(self, text, *, expect_sorry):
        self.calls.append(("elaborate", expect_sorry, len(text)))
        if self.unavailable:
            return {"ok": False, "unavailable": True, "olean_path": None}
        return {"ok": self.elaborate_ok, "unavailable": False,
                "olean_path": "/olean/candidate", "detail": self.detail}

    def recheck(self, olean_path):
        self.calls.append(("recheck", olean_path))
        if self.unavailable:
            return {"ok": False, "unavailable": True, "audited": False,
                    "axioms": []}
        return {"ok": self.recheck_ok, "unavailable": False,
                "audited": self.audited, "axioms": list(self.axioms),
                "transcript": self.detail}


def _authoring_batch(cands):
    return {"schema": B.BATCH_SCHEMA, "goals": [], "authoring": cands}


# ===========================================================================
# 1. BYTE COMPATIBILITY -- the empty case must be a no-op end to end.
# ===========================================================================
def test_committed_candidate_queue_is_well_formed():
    """The bootstrap-era form of this tooth asserted `candidates == []`, and it
    held only until the first candidate was queued (the
    test_committed_verdicts_are_honest precedent, one kind over).  Post-seed
    the invariant is SHAPE, which is strictly stronger than emptiness: every
    candidate must be rideable, and a `declares` name absent from the
    candidate's own text is the borrowed-evidence failure the ride refuses."""
    doc = json.loads((_ROOT / "results" / "reflect_candidates.json")
                     .read_text(encoding="utf-8"))
    assert doc["schema"] == B.CANDIDATES_SCHEMA
    assert "sorryAx" in doc["honesty"]            # the negative control, in writing
    seen = set()
    for c in doc["candidates"]:
        assert set(c) >= {"candidate_id", "module_text", "declares", "origin"}, c
        assert c["candidate_id"] not in seen, f"duplicate id {c['candidate_id']}"
        seen.add(c["candidate_id"])
        assert c["module_text"].strip(), c["candidate_id"]
        for name in c["declares"]:
            assert name in c["module_text"], (
                f"{c['candidate_id']} claims {name}, which is absent from its "
                f"own text -- the ride would fail it for borrowed evidence")


def test_assemble_omits_the_authoring_key_when_there_are_no_candidates(tmp_path):
    qp = tmp_path / "q.json"
    qp.write_text(json.dumps({"goals": []}))
    batch = B.assemble(qp, candidates_path=tmp_path / "absent.json")
    assert "authoring" not in batch               # ⚠ key ABSENT, not empty list
    assert "authoring_cap" not in batch
    # An EMPTY queue file behaves identically to an absent one.  This used to
    # read the committed queue, which was empty until the first candidate was
    # seeded; the property under test is about emptiness, not about which file
    # happens to be empty today.
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"schema": B.CANDIDATES_SCHEMA,
                                 "candidates": []}))
    same = B.assemble(qp, candidates_path=empty)
    assert B.render_batch_json(same) == B.render_batch_json(batch)


def test_committed_batch_still_reproduces_byte_for_byte():
    """The H1.1 reproduction tooth, restated against the authoring-aware
    assemble: adding a kind that nothing uses yet must move ZERO bytes."""
    committed = (_ROOT / "results" / "hammer_batch.json").read_text()
    assert B.render_batch_json(
        B.assemble(_ROOT / "results" / "proof_queue.json",
                   candidates_path=_ROOT / "results" / "reflect_candidates.json")
    ) == committed


def test_ride_omits_authoring_rows_for_a_goal_only_batch():
    batch = {"schema": B.BATCH_SCHEMA, "goals": []}
    v = H.run_ride(batch, backend=_StubBackend())
    assert "authoring_rows" not in v
    assert v["status"] == "complete" and v["rows"] == []


def test_readout_md_and_json_unchanged_without_authoring():
    """The md renderer grew an authoring section; with no authoring rows it must
    emit the SAME bytes it emitted before, and the readout json must not grow a
    key.  Measured against verdicts with the authoring rows STRIPPED rather than
    against the committed pair: the committed verdicts carried no authoring rows
    only until the first ride landed one, and the property under test is
    'no rows => no section', not 'today's file happens to have none'.  The
    committed pair's reproduction is owned by
    test_committed_readout_reproduces_from_committed_inputs."""
    batch = json.loads((_ROOT / "results" / "hammer_batch.json").read_text())
    verdicts = json.loads((_ROOT / "results" / "hammer_verdicts.json").read_text())
    bare = {k: v for k, v in verdicts.items() if k != "authoring_rows"}
    ro = B.build_readout(bare, batch)
    assert "authoring" not in ro                  # ⚠ key ABSENT, not empty
    md = B.render_readout_md(ro)
    assert "Authoring candidates" not in md
    assert md.endswith(f"> {ro['note']}\n")       # the trailing shape is intact
    # ...and with the rows present, the section MUST appear -- otherwise the
    # assertion above would pass on a renderer that emitted nothing at all.
    full = B.build_readout(verdicts, batch)
    assert "authoring" in full, "the renderer drops authoring rows entirely"


# ===========================================================================
# 2. the authoring kind ROUND-TRIPS (queue -> batch -> ride -> report).
# ===========================================================================
def test_authoring_kind_round_trips(tmp_path):
    cp = _write_candidates(tmp_path, [
        _cand("c_twice", _GOOD_TEXT, ["tmTwice", "evalTm_tmTwice"])])
    qp = tmp_path / "q.json"
    qp.write_text(json.dumps({"goals": []}))
    batch = B.assemble(qp, candidates_path=cp)
    assert [e["candidate_id"] for e in batch["authoring"]] == ["c_twice"]
    assert set(batch["authoring"][0]) == {"candidate_id", "declares",
                                          "module_text", "origin"}
    assert batch["authoring_cap"] == B.DEFAULT_AUTHORING_CAP

    v = H.run_ride(batch, backend=_StubBackend())
    assert v["status"] == "complete"
    row = v["authoring_rows"][0]
    assert row["passed"] is True and row["candidate_id"] == "c_twice"

    rep = R.report(v, batch)
    assert rep["totals"] == {"n_candidates": 1, "n_passed": 1, "n_failed": 0,
                             "n_not_run": 0}
    assert rep["candidates"][0]["status"] == R.PASSED
    assert rep["candidates"][0]["declares"] == ["tmTwice", "evalTm_tmTwice"]
    # the readout carries the authoring block once the ride produced rows.
    ro = B.build_readout(v, batch)
    assert ro["authoring"]["totals"]["n_passed"] == 1
    assert "Authoring candidates" in B.render_readout_md(ro)


def test_candidates_are_ordered_by_id_and_capped(tmp_path):
    cp = _write_candidates(tmp_path, [
        _cand("c_z", _GOOD_TEXT, ["tmTwice"]),
        _cand("c_a", _GOOD_TEXT, ["tmTwice"]),
        _cand("c_m", _GOOD_TEXT, ["tmTwice"])])
    assert [e["candidate_id"] for e in B.load_candidates(cp)] == \
        ["c_a", "c_m", "c_z"]                     # id order, not file order
    assert [e["candidate_id"] for e in B.load_candidates(cp, cap=2)] == \
        ["c_a", "c_m"]                            # deterministic prefix


def test_load_candidates_is_total_on_junk(tmp_path):
    assert B.load_candidates(tmp_path / "nope.json") == []
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert B.load_candidates(bad) == []           # honest empty, never a crash


# ===========================================================================
# 3. the ESCAPE GATE runs BEFORE the backend (asserted on the call log).
# ===========================================================================
def test_escape_gate_refusal_never_reaches_the_backend():
    be = _StubBackend()
    row, deferred = R.verify_candidate(
        _cand("c_escape", _ESCAPE_TEXT, ["t_escape"]), be)
    assert deferred is False
    assert row["gate_ok"] is False and row["passed"] is False
    assert "escape-gate refusal" in row["detail"]
    assert be.calls == []                         # ⚠ the backend was NEVER touched
    # and the verdict-bearing fields stay null rather than a fabricated false.
    assert row["elaborated"] is None and row["replayed"] is None


def test_gate_refusal_is_per_candidate_not_per_ride():
    be = _StubBackend()
    batch = _authoring_batch([_cand("c_bad", _ESCAPE_TEXT, ["t_escape"]),
                              _cand("c_ok", _GOOD_TEXT, ["tmTwice"])])
    v = H.run_ride(batch, backend=be)
    ids = {r["candidate_id"]: r for r in v["authoring_rows"]}
    assert ids["c_bad"]["passed"] is False and ids["c_ok"]["passed"] is True
    assert v["status"] == "complete"              # a refusal is not a ride failure


def test_candidate_claiming_nothing_is_refused_preflight():
    be = _StubBackend()
    row, _ = R.verify_candidate(_cand("c_mute", _GOOD_TEXT, []), be)
    assert row["passed"] is False and row["gate_ok"] is True
    assert be.calls == []                         # no lane elaboration spent
    assert "declares no names" in row["detail"]


# ===========================================================================
# 4. the negative controls: sorry, renames, audit silence, stray axioms.
# ===========================================================================
def test_sorry_bearing_candidate_is_never_reported_proved():
    """The failure mode that would poison every downstream reading: a candidate
    that ELABORATES with a hole in it.  The audited run-2 axiom set is what
    catches it (`sorryAx`), never a lexical guess."""
    be = _StubBackend(axioms=("propext", "sorryAx"))
    row, _ = R.verify_candidate(
        _cand("c_sorry", _SORRY_TEXT, ["evalTm_bogus"]), be)
    assert row["elaborated"] is True and row["replayed"] is True
    assert row["passed"] is False                 # elaborated, NOT proved
    assert "sorryAx" in row["detail"]
    assert R.classify(row) == R.FAILED


def test_renamed_declaration_fails_rather_than_passes():
    be = _StubBackend()
    row, _ = R.verify_candidate(
        _cand("c_rename", _RENAMED_TEXT, ["tmTwice", "evalTm_tmTwice"]), be)
    assert row["declared_missing"] == ["evalTm_tmTwice"]
    assert row["passed"] is False
    assert "claimed declarations absent" in row["detail"]


def test_declaration_search_is_over_the_candidate_not_the_slice():
    """`checkAll_witness` lives in the committed slice.  Claiming it must NOT
    pass: the candidate introduced nothing."""
    be = _StubBackend()
    row, _ = R.verify_candidate(
        _cand("c_borrow", _GOOD_TEXT, ["checkAll_witness"]), be)
    assert row["declared_missing"] == ["checkAll_witness"]
    assert row["passed"] is False


def test_declares_missing_accepts_every_declaration_head():
    for head in R._DECL_HEADS:
        assert R.declares_missing(f"{head} foo := bar", ["foo"]) == []
    # `example` introduces no name, so it can never satisfy a claim.
    assert R.declares_missing("example : True := trivial", ["foo"]) == ["foo"]
    # a prefix match is not a declaration.
    assert R.declares_missing("theorem foobar := x", ["foo"]) == ["foo"]


def test_audit_silence_fails_closed():
    be = _StubBackend(audited=False)
    row, _ = R.verify_candidate(_cand("c_mute", _GOOD_TEXT, ["tmTwice"]), be)
    assert row["elaborated"] is True
    assert row["replayed"] is False and row["passed"] is False
    assert "fail closed" in row["detail"]


def test_axiom_outside_the_whitelist_is_not_a_pass():
    be = _StubBackend(axioms=("propext", "Bogus.axiom_of_choice"))
    row, _ = R.verify_candidate(_cand("c_ax", _GOOD_TEXT, ["tmTwice"]), be)
    assert row["passed"] is False
    assert "outside the measured whitelist" in row["detail"]


def test_elaboration_failure_carries_the_transcript():
    be = _StubBackend(elaborate_ok=False, detail="unknown identifier 'tmTwice'")
    row, _ = R.verify_candidate(_cand("c_fail", _GOOD_TEXT, ["tmTwice"]), be)
    assert row["elaborated"] is False and row["passed"] is False
    assert "unknown identifier" in row["detail"]
    assert R.classify(row) == R.FAILED            # FAILED-WITH-TRANSCRIPT


def test_kernel_replay_refusal_is_not_a_pass():
    be = _StubBackend(recheck_ok=False)
    row, _ = R.verify_candidate(_cand("c_replay", _GOOD_TEXT, ["tmTwice"]), be)
    assert row["elaborated"] is True and row["replayed"] is False
    assert row["passed"] is False


def test_whitelist_is_single_sourced_from_the_kernel_standard_axioms():
    import kernel
    assert (set(R.AUTHORING_AXIOM_WHITELIST)
            == set(kernel._STANDARD_AXIOMS) | {"lcProof"})
    assert "sorryAx" not in R.AUTHORING_AXIOM_WHITELIST


# ===========================================================================
# 5. Lean-absent deferral, determinism, no clock.
# ===========================================================================
def test_lean_absent_defers_every_candidate_as_not_run():
    batch = _authoring_batch([_cand("c_a", _GOOD_TEXT, ["tmTwice"]),
                              _cand("c_b", _GOOD_TEXT, ["tmTwice"])])
    v = H.run_ride(batch, backend=_StubBackend(unavailable=True))
    assert v["status"] == "deferred"
    for row in v["authoring_rows"]:
        assert row["passed"] is None              # honestly null, never false
        assert row["elaborated"] is None and row["axioms"] is None
        assert R.classify(row) == R.NOT_RUN


@pytest.mark.skipif(
    common.lean_available(),
    reason="⚠X7 mirrored: this tooth describes the DEFERRAL a Lean-absent "
           "container produces; where a toolchain is present the ride really "
           "runs, which is what test_good_candidate_elaborates_and_audits_"
           "clean covers (results/lean_gate.md)")
def test_real_default_backend_defers_here():
    # This container is Lean-absent (policy denial); the default LeanBackend
    # honest-degrades and the ride writes NOT-RUN, never a false green.
    assert common.lean_available() is False
    batch = _authoring_batch([_cand("c_a", _GOOD_TEXT, ["tmTwice"])])
    v = H.run_ride(batch)                         # no injected backend
    assert v["status"] == "deferred"
    assert v["authoring_rows"][0]["passed"] is None


def test_deadline_marks_remaining_candidates_not_run():
    batch = _authoring_batch([_cand("c_a", _GOOD_TEXT, ["tmTwice"]),
                              _cand("c_b", _GOOD_TEXT, ["tmTwice"])])
    ticks = iter([0.0, 0.0, 100.0])               # 2nd candidate is past budget
    v = H.run_ride(batch, backend=_StubBackend(), deadline_seconds=10.0,
                   clock=lambda: next(ticks))
    assert v["status"] == "partial"
    assert v["authoring_rows"][0]["passed"] is True
    assert v["authoring_rows"][1]["passed"] is None


def test_authoring_rows_are_deterministic_and_carry_no_clock():
    batch = _authoring_batch([_cand("c_a", _GOOD_TEXT, ["tmTwice"])])
    a = H.render_verdicts_json(H.run_ride(batch, backend=_StubBackend()))
    b = H.render_verdicts_json(H.run_ride(batch, backend=_StubBackend()))
    assert a == b                                 # byte-identical re-ride
    for row in json.loads(a)["authoring_rows"]:
        assert set(row) == {"candidate_id", "gate_ok", "elaborated", "replayed",
                            "declared_missing", "axioms", "passed", "detail"}
        assert not any(k in row for k in ("seconds", "wall", "started_at"))


def test_compose_is_deterministic_and_leaves_the_slice_untouched():
    src = (_ROOT / "tools" / "FgReflect.lean").read_text(encoding="utf-8")
    before = common.sha256_bytes(src.encode())
    a = R.compose_candidate_module(_GOOD_TEXT, candidate_id="c_a")
    b = R.compose_candidate_module(_GOOD_TEXT, candidate_id="c_a")
    assert a == b
    # spliced INSIDE the namespace, after the whole committed source (the
    # reflect_shadow probe idiom -- unqualified slice names must resolve).
    assert a.startswith(src)
    assert a.index("namespace FgReflect\n\n-- authoring candidate") > len(src) - 1
    assert a.index(_GOOD_TEXT.rstrip()) > a.rindex("namespace FgReflect")
    assert a.rstrip().endswith("end FgReflect")
    assert common.sha256_bytes(
        (_ROOT / "tools" / "FgReflect.lean").read_bytes()) == before


def test_composed_module_survives_the_escape_gate():
    from buildloop.validate_lean import validate_lean
    ok, why = validate_lean(R.compose_candidate_module(_GOOD_TEXT,
                                                       candidate_id="c_a"))
    assert ok, why


# ===========================================================================
# 6. the session-side report (the consumption side of the protocol).
# ===========================================================================
def test_report_classifies_all_three_ways():
    verdicts = {"status": "partial", "lean_available": True, "authoring_rows": [
        R._row("c_pass", gate_ok=True, elaborated=True, replayed=True,
               declared_missing=[], axioms=["propext"], passed=True),
        R._row("c_fail", gate_ok=True, elaborated=False, replayed=False,
               declared_missing=[], axioms=[], passed=False,
               detail="error: unknown identifier"),
        R.not_run_row("c_later")]}
    batch = _authoring_batch([_cand("c_pass", _GOOD_TEXT, ["tmTwice"])])
    rep = R.report(verdicts, batch)
    assert [c["status"] for c in rep["candidates"]] == [R.PASSED, R.FAILED,
                                                        R.NOT_RUN]
    assert rep["totals"] == {"n_candidates": 3, "n_passed": 1, "n_failed": 1,
                             "n_not_run": 1}
    text = R.render_report_text(rep)
    assert "unknown identifier" in text           # the transcript is the handle
    assert "certificate" in rep["note"]           # evidence, never a certificate


def test_report_on_a_goal_only_ride_is_honestly_empty():
    rep = R.report({"status": "complete", "lean_available": False, "rows": []},
                   {"goals": []})
    assert rep["candidates"] == []
    assert rep["totals"]["n_candidates"] == 0
    assert "no authoring entries" in R.render_report_text(rep)


def test_report_cli_reads_the_committed_pair(capsys):
    assert R.main([]) == 0
    out = capsys.readouterr().out
    assert "reflect_ride report:" in out


# ===========================================================================
# 7. the one genuinely Lean-requiring node (⚠X7 skipif idiom).
# ===========================================================================
@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent (Lean-lane test)")
def test_good_candidate_elaborates_and_audits_clean():
    from kernel.backends import LeanBackend
    row, deferred = R.verify_candidate(
        _cand("c_twice", _GOOD_TEXT, ["tmTwice", "evalTm_tmTwice"]),
        LeanBackend())
    assert deferred is False, row
    assert row["passed"] is True, row
    assert "sorryAx" not in (row["axioms"] or [])
    assert set(row["axioms"] or []) <= set(R.AUTHORING_AXIOM_WHITELIST)


@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent (Lean-lane test)")
def test_sorry_candidate_elaborates_but_never_passes():
    from kernel.backends import LeanBackend
    row, _ = R.verify_candidate(
        _cand("c_sorry", _SORRY_TEXT, ["evalTm_bogus"]), LeanBackend())
    assert row["passed"] is False, row

"""Teeth for tools/smt_proof_probe.py + proof_mine.certify_rewrite
(certifying-algorithms sweep, items 1 and 3).

LLM-free, Lean-free.  z3 is a hard dependency (subprocess leg); cvc5 absence
degrades honestly and these asserts tolerate it."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import smt_proof_probe, proof_mine


def _cvc5_present():
    try:
        import cvc5  # noqa: F401
        return True
    except ImportError:
        return False


def test_probe_produces_z3_proof_artifacts():
    rep = smt_proof_probe.probe(smt_proof_probe.DEMO_OBLIGATIONS)
    assert len(rep["rows"]) == 2
    for r in rep["rows"]:
        assert r["tier"] in ("proof-produced-unchecked", "proof-checked")
        assert r["z3"]["verdict"] == "unsat", r
        assert r["z3"]["proof_bytes"] > 0          # the artifact exists
        assert r["artifacts"]["z3_proof_sexpr"].startswith("(")
        # TIGHTENED after the QF bug: tolerance for 'error' when the binding
        # is PRESENT masked a malformed obligation (an `exists` inside a QF_
        # logic that only z3's lenient parser accepted).  With cvc5 installed
        # the verdict must be a real unsat; 'absent' remains honest only when
        # the binding is genuinely missing.
        if _cvc5_present():
            assert r["cvc5"]["verdict"] == "unsat", r
        else:
            assert r["cvc5"]["verdict"] == "absent"
    assert "not checked" in rep["honesty"]


def test_carcara_wiring_flips_tier(tmp_path, monkeypatch):
    # Planted-checker tooth (the operator planted-verdict pattern): a stub
    # binary standing in for carcara proves the WIRING -- artifact routed to
    # the checker, exit 0 flips the tier -- without claiming any real proof
    # was checked.  The stub is labeled; nothing real is upgraded.
    stub = tmp_path / "carcara"
    stub.write_text("#!/bin/sh\nexit 0\n")
    stub.chmod(0o755)
    monkeypatch.setenv("CGB_CARCARA", str(stub))
    out = smt_proof_probe.carcara_check("(dummy proof)", "(dummy problem)")
    assert out == {"ran": True, "checked": True, "detail": out["detail"]}
    failing = tmp_path / "carcara_fail"
    failing.write_text("#!/bin/sh\nexit 1\n")
    failing.chmod(0o755)
    monkeypatch.setenv("CGB_CARCARA", str(failing))
    out2 = smt_proof_probe.carcara_check("(dummy)", "(dummy)")
    assert out2["ran"] is True and out2["checked"] is False


def test_carcara_absent_is_honest(monkeypatch):
    monkeypatch.delenv("CGB_CARCARA", raising=False)
    monkeypatch.setenv("PATH", "/nonexistent")
    out = smt_proof_probe.carcara_check("(p)", "(s)")
    assert out == {"ran": False, "reason": "carcara absent"}


def test_probe_obligation_hash_is_content_bound():
    a = smt_proof_probe.probe(smt_proof_probe.DEMO_OBLIGATIONS)
    b = smt_proof_probe.probe(smt_proof_probe.DEMO_OBLIGATIONS)
    assert [r["obligation_sha"] for r in a["rows"]] == \
        [r["obligation_sha"] for r in b["rows"]]
    assert a["rows"][0]["obligation_sha"] != a["rows"][1]["obligation_sha"]


def test_certify_rewrite_roundtrip_and_collision():
    programs = [
        {"source": "s1", "sexpr": "(+ (ref n) (lit 1))"},
        {"source": "s2", "sexpr": "(< (+ (ref n) (lit 1)) (ref m))"},
    ]
    cert = proof_mine.certify_rewrite(programs, "(+ (ref n) (lit 1))")
    assert cert["ok"] is True
    assert cert["total_uses"] == 2
    # marker collision is detected, never silently rewritten through.
    collided = [{"source": "s3", "sexpr": "(A0)"}]
    cert2 = proof_mine.certify_rewrite(collided, "(A0)")
    assert cert2["ok"] is False or cert2["rows"][0]["marker_collision"]


def test_certify_rewrite_unused_candidate_refuses():
    programs = [{"source": "s1", "sexpr": "(ref n)"}]
    cert = proof_mine.certify_rewrite(programs, "(+ (ref x) (lit 9))")
    assert cert["ok"] is False and cert["total_uses"] == 0

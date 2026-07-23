"""Teeth for tools/smt_proof_probe.py + proof_mine.certify_rewrite
(certifying-algorithms sweep, items 1 and 3).

LLM-free, Lean-free.  z3 is a hard dependency (subprocess leg); cvc5 absence
degrades honestly and these asserts tolerate it."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import smt_proof_probe, proof_mine


def test_probe_produces_z3_proof_artifacts():
    rep = smt_proof_probe.probe(smt_proof_probe.DEMO_OBLIGATIONS)
    assert len(rep["rows"]) == 2
    for r in rep["rows"]:
        assert r["tier"] == "proof-produced-unchecked"
        assert r["z3"]["verdict"] == "unsat", r
        assert r["z3"]["proof_bytes"] > 0          # the artifact exists
        assert r["artifacts"]["z3_proof_sexpr"].startswith("(")
        # cvc5: unsat-with-proof when present, honest absence otherwise.
        assert r["cvc5"]["verdict"] in ("unsat", "absent", "error")
    assert "not checked" in rep["honesty"]


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

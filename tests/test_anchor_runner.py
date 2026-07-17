"""WP-KA B6 -- the ∃-anchor runner (``run/anchor.py``): the serial integrator that
wires FI-KA-1..4 (emitter -> lattice -> divergence guard -> v12 kernel.check ->
``results/anchor_report.json``).

These teeth exercise the runner in the LEAN-ABSENT lane (this container's honest
reality: ``common.lean_available()`` is False).  The runner still produces a
report, mapping every ∃ reading to its shadow column via the lattice; NO cert can
mint (no false green without the kernel), and NO divergence fires (T-a/T-b need a
kernel-proved leg).  Everything here is Lean-free, deterministic, and byte-stable.
"""
from __future__ import annotations

import json
import pathlib

import pytest

import common
from kernel import verdict_lattice
from kernel.certs import Certificate
from generators.math_compile import compile_math_reading
from generators import math_witness
from run import anchor as A
from buildloop import anchor_divergence


def test_container_is_lean_absent():
    # The premise of every tooth below: the kernel leg honestly degrades.
    assert common.lean_available() is False


# ---------------------------------------------------------- corpus discovery
def test_exists_corpus_is_the_41_44_class():
    sids = [s for s, _ in A.exists_readings()]
    # 41/42/44 shadow-certify; 43 is the honest box-edge refusal.  All are ∃-shaped.
    assert sids == sorted(sids)                     # deterministic order
    for want in ("41_division_algorithm", "42_bezout_identity",
                 "43_larger_integer_exists", "44_divides_witness"):
        assert want in sids
    # every returned reading really is ∃-shaped (supported shape).
    from generators.math_eval import exists_shadow_shape
    for _sid, reading in A.exists_readings():
        assert exists_shadow_shape(reading, bound=None)["mode"] == "supported"


# ------------------------------------------------------ fresh shadow recompute
def test_shadow_recomputed_fresh_not_parsed():
    # Source 43 refutes at the box edge (n = B = 8, no in-box m > 8): the fresh
    # recompute returns `refuted` with the canonically-first refuting outer.
    r43 = dict(A.exists_readings())["43_larger_integer_exists"]
    shadow = A.recompute_shadow(r43, bound=8)
    assert shadow["verdict"] == "refuted"
    assert shadow["refuting_outer"] == {"n": 8}
    assert shadow["bound"] == 8
    # 41/42/44 certify (every admitted outer has an in-box witness).
    readings = dict(A.exists_readings())
    for sid in ("41_division_algorithm", "42_bezout_identity", "44_divides_witness"):
        assert A.recompute_shadow(readings[sid], bound=8)["verdict"] == "pass"


# ------------------------------------------------------------- the report shape
def test_report_is_lean_absent_shadow_column():
    rep = A.build_report()
    assert rep["schema"] == "anchor-report/v1"
    assert rep["lean_available"] is False
    by_sid = {r["source_id"]: r for r in rep["readings"]}

    # 43: shadow refuted + kernel unavailable -> shadow-edge-refused (NOT
    # divergent -- the §7.2 permanent differential, the package's whole tooth).
    r43 = by_sid["43_larger_integer_exists"]
    assert r43["lattice_point"] == "shadow-edge-refused"
    assert r43["shadow"]["verdict"] == "refuted"
    assert r43["kernel"]["verdict"] == "unavailable"
    assert r43["kernel"]["cert_id"] is None
    # the emitted template rides as provenance (optional `template?` field).
    assert r43["template"] == {"m": {"op": "+",
                                     "args": [{"ref": "n"}, {"lit": 1}]}}

    # 41/42/44: shadow pass; the emitter honestly skips (division witnesses are
    # outside the v1 template family) -> kernel not-attempted -> shadow-certified.
    for sid in ("41_division_algorithm", "42_bezout_identity", "44_divides_witness"):
        assert by_sid[sid]["lattice_point"] == "shadow-certified"
        assert by_sid[sid]["shadow"]["verdict"] == "pass"
        assert "template" not in by_sid[sid]     # nothing emitted -> no template

    # every reported lattice_point is one of the five (no boolean-ization).
    for r in rep["readings"]:
        assert r["lattice_point"] in verdict_lattice.LATTICE_POINTS


def test_summary_counts_consistent():
    rep = A.build_report()
    s = rep["summary"]
    assert s["n_exists_readings"] == s["n_anchor_rows"] + s["n_honest_absence"]
    assert s["n_anchor_rows"] == len(rep["readings"])
    assert sum(s["by_lattice_point"].values()) == s["n_anchor_rows"]
    assert s["by_lattice_point"]["shadow-certified"] == 3
    assert s["by_lattice_point"]["shadow-edge-refused"] == 1
    assert s["by_lattice_point"]["kernel-proved"] == 0     # no mint w/o Lean
    assert s["by_lattice_point"]["divergent"] == 0         # no trigger fired
    assert s["n_unresolved_divergences"] == 0


# ------------------------------------------------- no mint without the kernel
def test_no_certificate_minted_in_lean_absent_lane():
    # FI-KA-1 tooth 2 / FI-KA-4: with Lean absent the runner can NEVER produce a
    # Certificate -- no false green without the kernel run.  Every row's kernel
    # verdict is unavailable/not-attempted and carries no cert_id.
    rep = A.build_report()
    for r in rep["readings"]:
        assert r["kernel"]["verdict"] in ("unavailable", "not-attempted")
        assert r["kernel"]["cert_id"] is None


# --------------------------------------------------------- determinism / bytes
def test_report_byte_stable_across_two_builds():
    a = A.render_json(A.build_report())
    b = A.render_json(A.build_report())
    assert a == b, "anchor_report is not byte-stable across two builds"


def test_report_body_has_no_wall_clock():
    text = A.render_json(A.build_report())
    for forbidden in ("created_at", "timestamp", "wall_ms", "wall_clock",
                      "now_iso", "generated_at"):
        assert forbidden not in text


def test_committed_artifact_matches_a_fresh_build():
    committed = A.REPORT_PATH.read_text()
    fresh = A.render_json(A.build_report())
    assert committed == fresh, \
        "results/anchor_report.json is stale vs a fresh runner build"


def test_subject_hash_is_the_raw_statement_join_key():
    # The report subject is the RAW `:= sorry` statement's sha -- identical to what
    # a statement-cert keys on, so anchor verdicts join on ONE key (v11 rule).
    rep = A.build_report()
    readings = dict(A.exists_readings())
    for r in rep["readings"]:
        want = compile_math_reading(readings[r["source_id"]])["statement_hash"]
        assert r["subject_hash"] == want


# ------------------------------------------------- 43 edge-refusal is NOT T-a
def test_source_43_is_not_a_divergence():
    # The accepted `m := n + 1` witness at the refuting point n=8 is m=9 -- OUTSIDE
    # the box -- so T-a does NOT fire: shadow refutes the BOUNDED claim only, never
    # contradicting the unbounded theorem.  (FI-KA-2 failure-mode 1.)
    r43 = dict(A.exists_readings())["43_larger_integer_exists"]
    template = {"m": {"op": "+", "args": [{"ref": "n"}, {"lit": 1}]}}
    shadow = A.recompute_shadow(r43, bound=8)
    ev = A._in_bound_witness_contradiction(r43, template, shadow, bound=8)
    assert ev is None, "43's out-of-box witness must NOT trigger T-a"


# ------------------------------------------- divergence stickiness / mint-guard
def test_unresolved_divergence_forces_divergent_and_blocks_mint(tmp_path):
    # An unresolved committed divergence for a subject makes the lattice return
    # `divergent` for it (regardless of fresh inputs) and the mint-guard raises --
    # order-independently (FI-KA-3 teeth 2/3).
    r43 = dict(A.exists_readings())["43_larger_integer_exists"]
    subject = compile_math_reading(r43)["statement_hash"]
    div_dir = tmp_path / "anchor_divergences"

    # No artifact yet -> the guard is silent, the lattice maps normally.
    anchor_divergence.assert_no_unresolved(subject, out_dir=div_dir)
    row = A.evaluate_reading("43_larger_integer_exists", r43,
                             divergence_dir=div_dir)
    assert row["lattice_point"] == "shadow-edge-refused"

    # Record an (unresolved) divergence, then the guard raises and the lattice
    # returns divergent -- even though no fresh trigger fired this run.
    anchor_divergence.record_divergence({
        "subject_hash": subject, "source_id": "43_larger_integer_exists",
        "trigger": anchor_divergence.TRIGGERS[0],
        "shadow": {"verdict": "refuted", "bound": 8, "refuting_outer": {"n": 8},
                   "n_outer_admitted": 17},
        "kernel": {"verdict": "proved", "cert_id": "x", "discharge": "omega",
                   "transcript_tail": ""},
        "template": {"m": {"op": "+", "args": [{"ref": "n"}, {"lit": 1}]}},
        "witness_eval": {"outer": {"n": 8}, "template_values": {"m": 9},
                         "in_bound": False, "conclusion_holds_eval": True},
        "identity": {"certs_version": 12, "rung": "exists-anchor/v1"},
    }, out_dir=div_dir)

    with pytest.raises(anchor_divergence.UnresolvedDivergenceError):
        anchor_divergence.assert_no_unresolved(subject, out_dir=div_dir)
    row2 = A.evaluate_reading("43_larger_integer_exists", r43,
                              divergence_dir=div_dir)
    assert row2["lattice_point"] == "divergent"


def test_lean_absent_run_records_no_divergence(tmp_path):
    # The committed run fires NO trigger (no kernel-proved leg), so the append-only
    # divergence dir stays empty -- the runner never fabricates a divergence.
    div_dir = tmp_path / "anchor_divergences"
    A.build_report(divergence_dir=div_dir)
    assert not div_dir.exists() or not list(div_dir.glob("*.json"))


# ---------------------------------------------- honest-absence None -> no row
def test_none_lattice_point_emits_no_row(monkeypatch, tmp_path):
    # The (skip, unavailable) honest-absence cell returns None from the lattice;
    # the runner emits NO anchor row for it (FI-KA-2's honest absence).  Force a
    # `skip` shadow via a stubbed recompute and assert the row is dropped.
    r43 = dict(A.exists_readings())["43_larger_integer_exists"]
    monkeypatch.setattr(A, "recompute_shadow", lambda reading, *, bound=A.BOUND: {
        "verdict": "skip", "bound": bound, "refuting_outer": None,
        "n_outer_admitted": 0})
    # emitter skip -> kernel not-attempted; (skip, not-attempted) -> None.
    monkeypatch.setattr(A.math_witness, "emit_witness_proofs",
                        lambda reading, *, bound: {"status": "skip",
                                                   "reason": "no-template-found"})
    row = A.evaluate_reading("43_larger_integer_exists", r43,
                             divergence_dir=tmp_path)
    assert row is None

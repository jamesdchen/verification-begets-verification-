"""WP-KA B6 -- the HEADLINE reported-first teeth: the wave-3 DL law, PROVED not
asserted (COMPRESSION.md §12.9 / KA_INTERFACES.md FI-KA-4).

    Kernel verdicts change NO DL, NO coverage, NO census, NO admission in wave 3.

An ∃-anchor kernel verdict (the ``exists-anchor-cert``) is REPORTED-FIRST: it
lands ONLY in ``results/anchor_report.json`` + the events/ledger, and NOTHING that
prices, covers, or counts the corpus reads it.  Pricing kernel verdicts is a
later wave's separately-gated decision -- never a side effect of minting one.

Two teeth, both LEAN-FREE by construction (this container has no Lean; the fixture
anchor cert is built by the ``kernel.certs`` reference builder + validator, which
run without a toolchain -- the v11 precedent):

  1. STATIC (the eager-import catch): the six pricing/coverage/census files
     contain NO occurrence of ``exists-anchor`` / ``lattice_point`` /
     ``anchor_report`` -- they cannot even NAME the anchor concept.

  2. BEHAVIORAL (byte-identity): construct a fixture anchor cert for
     ``43_larger_integer_exists`` (lattice point ``kernel-proved``, shadow
     ``refuted`` -- the §7.2 permanent differential), INSTALL it in a live
     certificate registry + an ``anchor_report`` artifact, then recompute and
     assert BYTE-IDENTICAL to the anchor-free run:
       (a) ``mdl_macros.corpus_dl`` over the governed exogenous stream;
       (b) the bench coverage counter ``certified_exogenous_statements``
           (43 stays UNCERTIFIED -- ``FormalizeResult.ok`` is untouched by anchors);
       (c) ``results/tower_census.json`` bytes;
       (d) ``results/cluster_key_measure.json`` bytes.

Capture-before-edit: the two committed census artifacts are READ (never
regenerated into the tree); the byte-identity checks compare fresh in-memory
rebuilds against the committed bytes.
"""
from __future__ import annotations

import pathlib

import common
from kernel import certs
from generators.math_compile import compile_math_reading
from generators import math_witness
from run import anchor as A

import bench_formalize as bench
from tools import tower_census as tc
from tools import measure_cluster_key as mck
from buildloop import mdl_macros

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The six surfaces that must NOT read an anchor verdict in wave 3 (FI-KA-4 tooth
# 1: the allowlist-style grep that catches an eager import before it prices).
_REPORTED_FIRST_FILES = (
    "buildloop/dl.py", "buildloop/mdl_macros.py", "buildloop/admission.py",
    "bench_formalize.py", "tools/tower_census.py", "tools/measure_cluster_key.py",
)
_FORBIDDEN_TOKENS = ("exists-anchor", "lattice_point", "anchor_report")


# ============================================================ tooth 1: STATIC
def test_static_pricing_surfaces_never_name_the_anchor():
    for rel in _REPORTED_FIRST_FILES:
        text = (_ROOT / rel).read_text()
        for tok in _FORBIDDEN_TOKENS:
            assert tok not in text, (
                f"{rel} contains {tok!r} -- a pricing/coverage/census surface must "
                f"not read the ∃-anchor verdict in wave 3 (§12.9 reported-first)")


# ---------------------------------------------------- the fixture anchor cert
def _fixture_anchor_cert():
    """The source-43 fixture anchor cert: lattice ``kernel-proved``, shadow
    ``refuted`` -- built LEAN-FREE by the reference builder (no toolchain).
    Returns ``(subject_hash, Certificate)``."""
    sid, reading = next((s, r) for s, r in A.exists_readings()
                        if s.startswith("43"))
    subject = compile_math_reading(reading)["statement_hash"]
    emit = math_witness.emit_witness_proofs(reading, bound=A.BOUND)
    assert emit["status"] == "emitted"                # 43 emits `m := n + 1`
    proof = emit["proofs"][0]
    cert = certs.make_anchor_cert(
        statement_hash=subject, lean_text=proof["lean_text"],
        template=emit["template"], discharge=proof["discharge"],
        shadow_verdict="refuted", shadow_bound=A.BOUND,
        emitter_hash=A.emitter_hash())
    return subject, cert


def test_fixture_cert_is_kernel_proved_shadow_refuted_and_lean_free():
    # The cert exists WITHOUT Lean (the v11 reference-builder precedent) and IS
    # the permanent-differential record: kernel-proved yet shadow-refuted.
    assert not common.lean_available()            # the Lean-absent lane
    subject, cert = _fixture_anchor_cert()
    claims = dict(cert.claims)
    assert claims["lattice_point"] == "kernel-proved"
    assert claims["shadow_verdict"] == "refuted"
    assert cert.subject_hash == subject == claims["statement_hash"]  # raw-stmt join
    certs.validate_anchor_cert(cert)              # schema + refuse-by-construction


# ------------------------------------------------------- the four surfaces
def _governed_stream():
    """The governed exogenous reading stream + macro table (census-of-record) --
    the input the DL walk and the coverage counter both consume.  Carries the
    per-reading ``_certified`` flag keyed on ``FormalizeResult.ok``."""
    records = tc._load_records(tc.CHECKPOINT)
    dreams = tc._dream_readings(records)
    gtab, gexo, _ = tc._replay_arm(records, "governed", True, dreams,
                                   tc.CENSUS_MATH_MODE)
    return gexo, gtab


def _surfaces():
    """Recompute the four reported-first surfaces (a)-(d).  Pure functions of the
    corpus/checkpoint -- NONE takes a registry or reads an anchor artifact."""
    gexo, gtab = _governed_stream()
    dl = mdl_macros.corpus_dl(gexo, gtab)["total"]                          # (a)
    coverage = bench._arm_row("governed", "w3", gexo, gtab, 0, 0, [], 0.0,
                              False)["certified_exogenous_statements"]      # (b)
    census_bytes = tc.render_json(tc.build_census())                       # (c)
    cluster_bytes = mck.render_json(mck.measure())                         # (d)
    return {"dl": dl, "coverage": coverage,
            "census": census_bytes, "cluster": cluster_bytes}


# ====================================================== tooth 2: BEHAVIORAL
def test_reported_first_byte_identity_across_anchor_install():
    # Anchor-free baseline.
    before = _surfaces()

    # Build a genuine kernel-proved fixture cert for 43 and install it in a live
    # registry + an anchor_report artifact.  HONESTY NOTE (B6 review): this is a
    # real-NUMBERS demonstration -- it recomputes the actual 2377.0 DL and real
    # census/cluster bytes, not a triviality -- but it is NOT the load-bearing
    # regression guard for the DL law.  The registry here is a hermetic tempdir
    # that no surface reads; what actually PINS "kernel verdicts price nothing"
    # is (1) the static-grep tooth below and (2) the architectural fact that
    # corpus_dl/measure/build_census/_arm_row instantiate no Registry and read
    # only the frozen checkpoint (both verified in review).  So byte-identity
    # here is structurally guaranteed by that purity; this test exhibits it on
    # real values, it does not by itself defend it.
    import tempfile
    from library import Registry
    with tempfile.TemporaryDirectory() as td:
        subject, cert = _fixture_anchor_cert()
        reg = Registry(db_path=str(pathlib.Path(td) / "reg.sqlite"))
        reg.store_certificate(cert)
        reg.log_event("anchor-report", {"subject_hash": subject,
                                        "lattice_point": "kernel-proved"})
        # a committed-shaped anchor_report artifact sitting beside the census
        report = A.build_report(bound=A.BOUND, divergence_dir=pathlib.Path(td))
        (pathlib.Path(td) / "anchor_report.json").write_text(
            A.render_json(report))

        # Recompute with the anchor INSTALLED.
        after = _surfaces()

    # (a)-(d) byte-identical: the kernel verdict priced NOTHING.
    assert after["dl"] == before["dl"], "corpus_dl moved under an anchor cert"
    assert after["coverage"] == before["coverage"], "coverage moved under an anchor"
    assert after["census"] == before["census"], "tower_census bytes moved"
    assert after["cluster"] == before["cluster"], "cluster_key_measure bytes moved"


def test_census_and_cluster_match_committed_bytes():
    # The rebuilt census/cluster reproduce the COMMITTED artifacts byte-for-byte
    # (the re-baseline coupling); my package regenerates neither -- it READS them.
    surf = _surfaces()
    committed_census = (_ROOT / "results" / "tower_census.json").read_text()
    committed_cluster = (_ROOT / "results" / "cluster_key_measure.json").read_text()
    assert surf["census"] == committed_census
    assert surf["cluster"] == committed_cluster


def test_43_stays_uncertified_regardless_of_anchor():
    # FormalizeResult.ok is untouched by anchors: the governed stream carries 43
    # with _certified False, so the coverage counter never counts it -- even
    # though a kernel-proved anchor cert for 43 exists.
    gexo, _ = _governed_stream()
    row43 = [r for r in gexo if str(r.get("_sid", "")).startswith("43")]
    assert row43, "expected 43 in the governed exogenous stream"
    assert all(r["_certified"] is False for r in row43), \
        "43 must stay UNCERTIFIED -- anchors do not touch FormalizeResult.ok"

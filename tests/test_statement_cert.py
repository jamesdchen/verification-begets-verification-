"""WP-G teeth: the two Lean proof-assistant contracts (FORMALIZATION F0.2/F0.3).

Runs HERE with NO Lean toolchain.  The Lean-absent assertions prove the honest
degradation (no false green without the kernel) and the L2 cache identity; the
TIERS/CERTS_VERSION assertions pin the interface-freeze amendment (F-C, ⚠A9/T5).
The L5 forgery teeth and the positive "a true statement certifies" path need a
real toolchain and self-skip with reason (⚠X7) -- never fail.

statement-cert / proof-cert are NON-POOLED, direct-path contracts (the
monitor-cert / tier-classification pattern): not in POOL_SUPPORTED, no
channel_specs/run_channel, so the channel-parity tripwire is untouched.
"""
import pytest

import common
import kernel
from kernel.certs import Certificate, ErrorTranscript, TIERS, CERTS_VERSION

# A clean `:= sorry` statement over the fragment (ASCII, a pinned import, no
# metaprogramming) -- this MUST survive the escape gate.
_PIN = common.MATHLIB_IMPORTS[0]
_CLEAN_SORRY = (
    f"import {_PIN}\n"
    "theorem cgb_stmt (n : Nat) (h : 2 < n) : n * 1 = n := sorry\n"
)
# A clean statement WITH a real proof (for proof-cert fixtures).
_CLEAN_PROOF = (
    f"import {_PIN}\n"
    "theorem cgb_stmt (n : Nat) (h : 2 < n) : n * 1 = n := by simp\n"
)


def _artifact():
    # A statement-cert / proof-cert subject carries no emitted files: the subject
    # identity is the statement_hash (folded in _subject_and_cdesc).
    return {"kind": "lean-statement", "files": {}}


def _fidelity_all_pass():
    """The tool-independent F2.1/F2.2 fidelity channels (computed by WP-H), all
    passing -- the disjoint evidence that meets the dual-checker rule (⚠T3)."""
    return [
        {"backend": "nonvacuity-z3^cvc5+decide", "result": "pass",
         "role": "cross-impl-differential",
         "detail": "hypotheses sat (Z3 ^ CVC5) + Lean decide witness"},
        {"backend": "entailed-instances", "result": "pass",
         "role": "behavioral-witness",
         "detail": "k smallest hypothesis-satisfying instances all hold"},
    ]


def _statement_contract(lean_text=_CLEAN_SORRY, import_set=None,
                        fidelity=None, **extra):
    c = {"type": "statement-cert",
         "lean_text": lean_text,
         "statement_hash": common.sha256_bytes(lean_text.encode()),
         "fidelity_channels": _fidelity_all_pass() if fidelity is None
         else fidelity,
         "mathlib_commit": common.MATHLIB_COMMIT,
         "toolchain": common.LEAN_TOOLCHAIN,
         "import_set": list(common.MATHLIB_IMPORTS) if import_set is None
         else list(import_set)}
    c.update(extra)
    return c


def _proof_contract(lean_text=_CLEAN_PROOF, fidelity=None, **extra):
    c = {"type": "proof-cert",
         "lean_text": lean_text,
         "proof_hash": common.sha256_bytes(lean_text.encode()),
         "statement_hash": common.sha256_bytes(_CLEAN_SORRY.encode()),
         "fidelity_channels": _fidelity_all_pass() if fidelity is None
         else fidelity,
         "mathlib_commit": common.MATHLIB_COMMIT,
         "toolchain": common.LEAN_TOOLCHAIN,
         "import_set": list(common.MATHLIB_IMPORTS)}
    c.update(extra)
    return c


# ============================================================ pinning / vocabulary
def test_both_types_implemented_and_non_pooled():
    impl = kernel.IMPLEMENTED_CONTRACT_TYPES
    assert "statement-cert" in impl
    assert "proof-cert" in impl
    # NON-POOLED: never in POOL_SUPPORTED (no channel_specs/run_channel path).
    assert "statement-cert" not in kernel.POOL_SUPPORTED
    assert "proof-cert" not in kernel.POOL_SUPPORTED


def test_channel_specs_refuses_the_non_pool_types():
    # The direct-path contracts are refused by the pooled decomposition (they
    # only ever run through check()), like smt-obligation.
    for c in (_statement_contract(), _proof_contract()):
        with pytest.raises(ValueError):
            kernel.channel_specs(_artifact(), c)


# =============================================================== TIERS / freeze
def test_kernel_checked_tier_and_certs_version():
    assert "kernel-checked" in TIERS
    assert CERTS_VERSION == 10


def test_kernel_checked_certificate_round_trips():
    cert = Certificate.make(
        "proof-cert-admission", "subj", "chash",
        [{"backend": "lean-elaborate+lean4checker", "result": "pass"}],
        tier="kernel-checked",
        claims=(("proof_hash", "abc"), ("axioms", ("Classical.choice",))),
        non_claims=(("novelty", "not judged"),))
    d = cert.to_dict()
    cert2 = Certificate.from_dict(d)
    assert cert2 == cert
    assert cert2.tier == "kernel-checked"
    # claims/non_claims round-trip as tuples (JSON->lists rehydrated), so
    # dataclass __eq__ is stable across DB/cache/fresh.
    assert cert2.claims == cert.claims
    assert isinstance(cert2.claims, tuple)


def test_old_emit_check_certificate_still_loads():
    # Load-compatibility: a pre-existing statement-cert dict (tier emit-check).
    old = {"cert_id": "x", "kind": "statement-cert-admission",
           "subject_hash": "s", "contract_hash": "c", "channels": [],
           "created_at": "t", "tier": "emit-check",
           "claims": [["statement_hash", "abc"], ["independence",
                                                   "kernel-family"]],
           "non_claims": []}
    c = Certificate.from_dict(old)
    assert c.tier == "emit-check"
    assert c.claims == (("statement_hash", "abc"),
                        ("independence", "kernel-family"))
    # And a REALLY old dict predating the honest-tier fields loads with the
    # frozen defaults (plain immutable defaults, never default_factory).
    ancient = {"cert_id": "y", "kind": "emission-check", "subject_hash": "s",
               "contract_hash": "c", "channels": [], "created_at": "t"}
    c2 = Certificate.from_dict(ancient)
    assert c2.tier == "" and c2.claims == () and c2.non_claims == ()


# =========================================================== L2 cache identity
def test_cache_key_deterministic():
    a, c = _artifact(), _statement_contract()
    assert kernel.cache_key(a, c) == kernel.cache_key(a, c)
    assert kernel.cache_key(a, c).startswith(f"v{CERTS_VERSION}:")


def test_cache_key_changes_on_import_set():
    a = _artifact()
    k_full = kernel.cache_key(a, _statement_contract())
    k_narrow = kernel.cache_key(
        a, _statement_contract(import_set=common.MATHLIB_IMPORTS[:-1]))
    assert k_full != k_narrow, "import set is an L2 dimension; must re-key"


def test_cache_key_changes_on_statement_bytes():
    a = _artifact()
    k1 = kernel.cache_key(a, _statement_contract())
    k2 = kernel.cache_key(
        a, _statement_contract(
            lean_text=_CLEAN_SORRY.replace("n * 1 = n", "n + 0 = n")))
    assert k1 != k2, "statement bytes are an L2 dimension; must re-key"


def test_cache_key_changes_on_validate_lean_hash(monkeypatch):
    # A changed escape gate is a clean cache miss, never a stale false-green (L2).
    a, c = _artifact(), _statement_contract()
    base = kernel.cache_key(a, c)
    monkeypatch.setattr(common, "validate_lean_hash",
                        lambda: "de" + "ad" * 31)
    assert kernel.cache_key(a, c) != base, \
        "validate_lean_hash (escape-gate source) must fold into the key"


def test_cache_key_changes_on_toolchain_hash(monkeypatch):
    a, c = _artifact(), _statement_contract()
    base = kernel.cache_key(a, c)
    monkeypatch.setattr(common, "lean_toolchain_hash",
                        lambda: "be" + "ef" * 31)
    assert kernel.cache_key(a, c) != base, \
        "the joint toolchain+Mathlib pin must fold into the key"


def test_proof_cert_cache_key_deterministic_and_distinct():
    a = _artifact()
    kp = kernel.cache_key(a, _proof_contract())
    assert kp == kernel.cache_key(a, _proof_contract())
    # a statement-cert and a proof-cert over the same text never collide (the
    # contract type is part of cdesc).
    ks = kernel.cache_key(a, _statement_contract(lean_text=_CLEAN_PROOF))
    assert kp != ks


# ============================================ Lean absent -> NO false green (L5)
def test_statement_cert_lean_absent_is_non_certificate():
    assert common.lean_available() is False, "this test asserts the absent path"
    v = kernel.check(_artifact(), _statement_contract())
    # channel 1 (the kernel audit) is unavailable -> honest non-Certificate,
    # EVEN with every fidelity channel passing.  No false green without the
    # kernel.
    assert not isinstance(v, Certificate), "false green with Lean absent!"
    assert isinstance(v, ErrorTranscript)


def test_statement_cert_all_fidelity_pass_still_no_cert():
    # Belt-and-braces on the headline invariant: fidelity green is NOT enough.
    c = _statement_contract(fidelity=[
        {"backend": "nonvacuity-z3^cvc5+decide", "result": "pass",
         "role": "cross-impl-differential", "detail": "sat + decide witness"},
        {"backend": "entailed-instances", "result": "pass",
         "role": "behavioral-witness", "detail": "instances hold"},
        {"backend": "examiner-convergence", "result": "pass",
         "role": "behavioral-witness", "detail": "expectations converge"}])
    v = kernel.check(_artifact(), c)
    assert not isinstance(v, Certificate)
    # the kernel channel is present in the recorded evidence and is not a pass.
    ch1 = [ch for ch in v.channels
           if ch["backend"] == "lean-elaborate+lean4checker"]
    assert ch1 and ch1[0]["result"] != "pass"
    assert ch1[0]["independence"] == "kernel-family"


def test_proof_cert_lean_absent_is_non_certificate():
    v = kernel.check(_artifact(), _proof_contract())
    assert not isinstance(v, Certificate)
    assert isinstance(v, ErrorTranscript)


def test_escape_gate_fires_through_check_without_lean():
    # Defense in depth (F0.4) is pure-Python and fires BEFORE elaboration, so a
    # metaprogramming escape is refused at channel 1 even with Lean absent.
    bad = (f"import {_PIN}\n"
           "theorem t (n : Nat) : n = n := by native_decide\n")
    v = kernel.check(_artifact(), _statement_contract(lean_text=bad))
    assert not isinstance(v, Certificate)
    ch1 = [ch for ch in v.channels
           if ch["backend"] == "lean-elaborate+lean4checker"][0]
    assert ch1["result"] == "fail"
    assert "escape-gate" in ch1["detail"]


def test_macro_escape_refused_through_proof_check_without_lean():
    forged = (f"import {_PIN}\n"
              "macro_rules | `(tactic| cheat) => `(tactic| sorry)\n"
              "theorem t : True := by cheat\n")
    v = kernel.check(_artifact(), _proof_contract(lean_text=forged))
    assert not isinstance(v, Certificate)


# ---------- toolchain-requiring L5 teeth: skip-with-reason, never fail (⚠X7) ----
# These need a real toolchain (WP-H runs them after `./setup.sh --with-lean`).
_SKIP = pytest.mark.skipif(not common.lean_available(),
                           reason="lean toolchain absent")


@_SKIP
def test_true_statement_certifies():
    # The positive path: a clean `:= sorry` statement whose run-2 audit shows
    # sorryAx alone, pp.all round-trips def-eq, and the fidelity gates pass ->
    # a Certificate at tier emit-check (⚠A9/T5), independence kernel-family.
    c = _statement_contract(axioms=["sorryAx"], pp_roundtrip={"ok": True})
    v = kernel.check(_artifact(), c)
    assert isinstance(v, Certificate), "a true statement failed to certify"
    assert v.tier == "emit-check"
    assert dict(v.claims)["independence"] == "kernel-family"


@_SKIP
def test_forged_driver_file_refused():
    # L5 tooth (i)/⚠T1: a proof script that writes a forged driver-result file at
    # elaboration time (run 1) and exits 0 must NOT certify -- the trusted run-2
    # pass in a fresh sandbox never reads run-1's forged file.
    forged = (f"import {_PIN}\n"
              "theorem t (n : Nat) (h : 2 < n) : n * 1 = n := sorry\n")
    c = _statement_contract(lean_text=forged, forge="driver-result-file")
    v = kernel.check(_artifact(), c)
    assert not isinstance(v, Certificate)


@_SKIP
def test_addDecl_smuggled_axiom_caught_by_run2_audit():
    # L5 tooth (ii)/⚠T2: an axiom smuggled via Lean.addDecl metaprogramming (no
    # `axiom` token) is caught by the run-2 ENVIRONMENT audit, not the escape
    # gate -- axioms outside the standard three -> proof-cert refuses.
    c = _proof_contract(smuggle="addDecl-axiom")
    v = kernel.check(_artifact(), c)
    assert not isinstance(v, Certificate)


@_SKIP
def test_smuggled_sorry_proof_refused():
    # L5 tooth (iii): a proof-cert whose proof secretly reduces to `sorry` shows
    # sorryAx in the run-2 audit -> proof-cert (forbid_sorry) refuses.
    smuggled = (f"import {_PIN}\n"
                "theorem t (n : Nat) (h : 2 < n) : n * 1 = n := by exact sorry\n")
    v = kernel.check(_artifact(), _proof_contract(lean_text=smuggled))
    assert not isinstance(v, Certificate)


if __name__ == "__main__":
    import sys
    raise SystemExit(pytest.main([__file__, "-q", *sys.argv[1:]]))

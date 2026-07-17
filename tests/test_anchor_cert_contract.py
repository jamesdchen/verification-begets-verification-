"""Wave-3 FI-KA-4 -- the exists-anchor-cert contract SCHEMA (COMPRESSION.md §12.2).

The v12 CERTS bump lands the ∃-anchor kernel verdict: this stanza + validator +
reference builder in kernel.certs, PLUS the _subject_and_cdesc / _dispatch /
IMPLEMENTED_CONTRACT_TYPES entries in kernel/__init__.py, all in one commit before
any producer code (the v11 order).  Every tooth here is LEAN-FREE (schema +
refuse-by-construction + subject-join, the v11 precedent): they run without a
toolchain.  The failure-mode teeth of FI-KA-4 are pinned by name below.

Note on the source-43 fixture: `∀ n:Int, ∃ m:Int, n < m` is the committed honest
box-edge refusal -- at n = B = 8 no in-box witness exists, so the bounded shadow
REFUTES, yet the unbounded theorem is true and the emitted `m := n + 1` proof is
kernel-provable.  The FI-KA-4 tooth is that this cert MINTS with the shadow
refuted: the §7.2 permanent differential, realized.
"""
import pytest

import common
import kernel
from kernel import certs
from kernel.certs import Certificate, CERTS_VERSION, TIERS

# --- the source-43 fixture (raw sorry'd statement + emitted witness proof) ----
S43 = ("theorem s43_larger_integer_exists : "
       "∀ (n : Int), ∃ (m : Int), n < m := sorry")
P43 = ("theorem s43_larger_integer_exists : "
       "∀ (n : Int), ∃ (m : Int), n < m := by\n"
       "  intro n\n"
       "  refine ⟨n + 1, ?_⟩\n"
       "  omega")
T43 = {"m": {"op": "+", "args": [{"ref": "n"}, {"lit": 1}]}}
H43 = common.sha256_bytes(S43.encode())


def _well_formed_anchor(**over):
    kw = dict(statement_hash=H43, lean_text=P43, template=T43, discharge="omega",
              shadow_verdict="refuted", shadow_bound=8, emitter_hash="emit-sha-0",
              axioms=("Classical.choice", "propext"))
    kw.update(over)
    return certs.make_anchor_cert(**kw)


def _anchor_contract(statement_text=S43, proof_text=P43, template=None,
                     discharge="omega", shadow_verdict="refuted", shadow_bound=8,
                     emitter_hash="emit-sha-0", axioms=("Classical.choice", "propext"),
                     template_eval_result="pass", **extra):
    template = T43 if template is None else template
    c = {"type": "exists-anchor-cert",
         "statement_hash": common.sha256_bytes(statement_text.encode()),
         "lean_text": proof_text,
         "template": template,
         "discharge": discharge,
         "shadow": {"verdict": shadow_verdict, "bound": shadow_bound},
         "emitter_hash": emitter_hash,
         "axioms": axioms,
         "template_eval_channel": {
             "backend": "template-eval-replay", "role": "cross-impl-differential",
             "result": template_eval_result,
             "detail": "exhaustive template-eval replay (every admitted outer "
                       "point, never sampled)"},
         "mathlib_commit": common.MATHLIB_COMMIT,
         "toolchain": common.LEAN_TOOLCHAIN,
         "import_set": list(common.MATHLIB_IMPORTS)}
    c.update(extra)
    return c


# ===================================================== pinning / version / freeze
def test_certs_version_is_12_and_type_pinned():
    # FI-KA-4 tooth 3: producer-before-schema / version bump.  The schema test
    # asserts CERTS_VERSION == 12 (same-commit rule at the review gate); the
    # allowlist pin is the sibling tooth in test_contract_allowlist.
    assert CERTS_VERSION == 12
    assert certs.ANCHOR_CERT_TYPE == "exists-anchor-cert"
    assert certs.ANCHOR_TIER == "kernel-checked"
    assert certs.ANCHOR_TIER in TIERS
    # lands WITH its dispatch branch (unlike norm-cert), NON-POOLED.
    assert "exists-anchor-cert" in kernel.IMPLEMENTED_CONTRACT_TYPES
    assert "exists-anchor-cert" not in kernel.POOL_SUPPORTED


def test_lattice_point_strings_are_the_five_frozen_fi_ka_2_points():
    # B1 CONSUMES the frozen lattice strings (it does NOT import B2's module).
    assert certs.ANCHOR_LATTICE_POINTS == (
        "kernel-proved", "shadow-certified", "shadow-edge-refused",
        "kernel-failed", "divergent")
    assert certs.ANCHOR_MINTABLE_LATTICE_POINT == "kernel-proved"
    assert certs.ANCHOR_CERT_CHANNELS == (
        "lean-elaborate+lean4checker", "template-eval-replay")


# =============================================================== well-formed shape
def test_well_formed_anchor_validates_and_round_trips():
    cert = _well_formed_anchor()
    certs.validate_anchor_cert(cert)                   # builder already validated
    assert cert.subject_hash == H43
    assert cert.tier == "kernel-checked"
    assert cert.kind == "exists-anchor-admission"
    rehydrated = Certificate.from_dict(cert.to_dict())
    certs.validate_anchor_cert(rehydrated)
    assert rehydrated == cert


def test_claims_tuple_is_exactly_the_frozen_order():
    cert = _well_formed_anchor()
    keys = [c[0] for c in cert.claims]
    assert keys == ["statement_hash", "lattice_point", "witness_template",
                    "discharge", "shadow_verdict", "shadow_bound", "axioms",
                    "kernel_checked"]
    d = dict(cert.claims)
    assert d["statement_hash"] == cert.subject_hash == H43
    assert d["lattice_point"] == "kernel-proved"
    assert d["witness_template"] == common.sha256_json(T43)
    assert d["discharge"] == "omega"
    assert d["shadow_verdict"] == "refuted"
    assert d["shadow_bound"] == 8
    assert d["axioms"] == ("Classical.choice", "propext")   # sorted
    assert d["kernel_checked"] is True


def test_non_claims_are_the_frozen_five_including_reported_first_dl_pricing():
    cert = _well_formed_anchor()
    nc = dict(cert.non_claims)
    assert list(nc) == ["fidelity_to_text", "shadow_agreement", "dl_pricing",
                        "novelty", "kernel_independence"]
    # the REPORTED-FIRST dl-pricing non-claim, verbatim intent (FI-KA-4 tooth 4).
    assert nc["dl_pricing"] == (
        "REPORTED-FIRST: this verdict prices nothing; no DL, coverage, census or"
        " admission surface reads it in wave 3 (§12.9)")
    # the permanent-differential shadow non-claim, verbatim.
    assert nc["shadow_agreement"] == (
        "the bounded shadow's refutation at the box edge is recorded, not"
        " overruled; it remains the permanent differential channel")
    assert "kernel-family" in nc["kernel_independence"]


# =========================================== FI-KA-4 tooth 1: raw-statement subject
def test_subject_is_the_raw_statement_hash():
    cert = _well_formed_anchor()
    assert cert.subject_hash == common.sha256_bytes(S43.encode())


def test_subject_must_equal_the_statement_hash_claim():
    cert = _well_formed_anchor()
    cert.subject_hash = "a-different-hash"
    with pytest.raises(ValueError, match="statement_hash claim"):
        certs.validate_anchor_cert(cert)


def test_subject_joins_the_statement_cert_for_the_same_reading():
    # The whole point of keeping subject = RAW statement sha: the anchor verdict
    # joins the statement-cert (and the store/ledger/audit chain) on ONE key.
    anchor = _well_formed_anchor()
    stmt_contract = {"type": "statement-cert", "lean_text": S43,
                     "statement_hash": H43, "fidelity_channels": []}
    stmt_subject, _ = kernel._subject_and_cdesc({}, stmt_contract)
    assert anchor.subject_hash == stmt_subject == H43


# ================================= FI-KA-4 tooth 5: refuse-by-construction (E/F/D)
@pytest.mark.parametrize("bad", ["shadow-certified", "shadow-edge-refused",
                                 "kernel-failed", "divergent"])
def test_non_kernel_proved_point_is_refused(bad):
    # Certificates are POSITIVE assertions; E/F/D points are reported, never
    # certified.  make_anchor_cert refuses to acquire an id for them.
    with pytest.raises(ValueError, match="kernel-proved"):
        _well_formed_anchor(lattice_point=bad)


def test_unknown_lattice_point_is_refused():
    with pytest.raises(ValueError, match="unknown lattice_point"):
        _well_formed_anchor(lattice_point="made-up")


# =========================== FI-KA-4 tooth 2: shadow verdict is NOT a channel result
def test_source43_mints_with_shadow_refuted_via_adjudicate():
    # The headline tooth: a kernel-proved run with the shadow REFUTED must MINT.
    # Two passing channels (kernel leg + exhaustive template-eval replay); the
    # shadow verdict rides in CLAIMS, never as a channel -- so adjudicate() sees
    # zero fail-class channels and issues the Certificate.
    contract = _anchor_contract(shadow_verdict="refuted")
    subject, cdesc = kernel._subject_and_cdesc({}, contract)
    chash = common.sha256_json(cdesc)
    ch1 = {"backend": "lean-elaborate+lean4checker", "role": "behavioral-witness",
           "result": "pass", "detail": "kernel-proved (L5) -- stub for the schema test"}
    ch2 = contract["template_eval_channel"]
    out = kernel.adjudicate("exists-anchor-admission", subject, chash, cdesc,
                            [ch1, ch2])
    assert isinstance(out, Certificate), \
        "the source-43 cert MUST mint with the shadow refuted (permanent differential)"
    certs.validate_anchor_cert(out)
    d = dict(out.claims)
    assert d["shadow_verdict"] == "refuted"
    assert d["lattice_point"] == "kernel-proved"
    # the channel list carries NO shadow verdict.
    assert [c["backend"] for c in out.channels] == list(certs.ANCHOR_CERT_CHANNELS)


def test_shadow_refutation_smuggled_as_a_channel_forbids_the_mint():
    # The failure mode the tooth guards: had a builder ridden the shadow verdict as
    # a fail-class channel, adjudicate() would count the fail and the 43 cert could
    # NEVER mint.  Prove it, so the channel list stays pinned to exactly two.
    contract = _anchor_contract(shadow_verdict="refuted")
    subject, cdesc = kernel._subject_and_cdesc({}, contract)
    chash = common.sha256_json(cdesc)
    ch1 = {"backend": "lean-elaborate+lean4checker", "role": "behavioral-witness",
           "result": "pass", "detail": "kernel-proved"}
    ch2 = contract["template_eval_channel"]
    shadow = {"backend": "bounded-shadow", "role": "cross-impl-differential",
              "result": "fail", "detail": "refuted at n=8 (box edge)"}
    out = kernel.adjudicate("exists-anchor-admission", subject, chash, cdesc,
                            [ch1, ch2, shadow])
    assert not isinstance(out, Certificate)          # a fail-class channel -> no cert


def test_channel_list_is_pinned_to_exactly_two():
    cert = _well_formed_anchor()
    assert [c["backend"] for c in cert.channels] == list(certs.ANCHOR_CERT_CHANNELS)
    cert.channels = list(cert.channels) + [
        {"backend": "bounded-shadow", "result": "refuted"}]
    with pytest.raises(ValueError, match="channels must be"):
        certs.validate_anchor_cert(cert)


# ==================== FI-KA-4 tooth 6: cache identity folds emitter/rung/shadow/bound
def test_cache_identity_folds_emitter_bound_and_shadow_verdict():
    _, c0 = kernel._subject_and_cdesc({}, _anchor_contract())
    h0 = common.sha256_json(c0)
    # the v12 additions are present.
    assert c0["rung"] == "exists-anchor/v1"
    assert c0["shadow"] == {"verdict": "refuted", "bound": 8}
    assert c0["emitter_hash"] == "emit-sha-0"
    # the raw-statement L2 fields are folded too.
    assert c0["lean_text_hash"] == H43                # == subject (statement bytes)
    assert c0["proof_sha"] == common.sha256_bytes(P43.encode())
    for field in ("import_set", "toolchain_hash", "mathlib_commit", "gate_hash",
                  "driver_hash"):
        assert field in c0
    # a changed EMITTER is a clean miss.
    _, ce = kernel._subject_and_cdesc({}, _anchor_contract(emitter_hash="emit-sha-1"))
    assert common.sha256_json(ce) != h0
    # a changed BOUND is a clean miss (the bound in the KEY, never the proof bytes).
    _, cb = kernel._subject_and_cdesc({}, _anchor_contract(shadow_bound=12))
    assert common.sha256_json(cb) != h0
    # a changed SHADOW VERDICT is a clean miss.
    _, cv = kernel._subject_and_cdesc({}, _anchor_contract(shadow_verdict="pass"))
    assert common.sha256_json(cv) != h0


def test_builder_and_kernel_cache_key_agree_byte_for_byte():
    # Single source of truth: make_anchor_cert and _subject_and_cdesc BOTH call
    # certs.anchor_cert_cdesc, so a minted cert's contract_hash and kernel.cache_key
    # can never drift (FI-KA-4 tooth 6, the norm-cert pattern).
    cert = _well_formed_anchor()
    contract = _anchor_contract()
    subject, cdesc = kernel._subject_and_cdesc({}, contract)
    assert subject == cert.subject_hash == H43
    assert common.sha256_json(cdesc) == cert.contract_hash
    assert kernel.cache_key({}, contract) == f"v12:{subject}:{cert.contract_hash}"


def test_cache_key_is_deterministic():
    assert kernel.cache_key({}, _anchor_contract()) == \
        kernel.cache_key({}, _anchor_contract())


# ====================================== schema refusals (missing / malformed fields)
def test_missing_claim_is_refused():
    cert = _well_formed_anchor()
    cert.claims = tuple(c for c in cert.claims if c[0] != "witness_template")
    with pytest.raises(ValueError, match="witness_template"):
        certs.validate_anchor_cert(cert)


def test_empty_subject_is_refused():
    cert = _well_formed_anchor()
    cert.subject_hash = ""
    with pytest.raises(ValueError, match="empty subject_hash"):
        certs.validate_anchor_cert(cert)


def test_kernel_checked_claim_must_be_true():
    cert = _well_formed_anchor()
    cert.claims = tuple((k, (False if k == "kernel_checked" else v))
                        for k, v in cert.claims)
    with pytest.raises(ValueError, match="kernel_checked"):
        certs.validate_anchor_cert(cert)


def test_unknown_shadow_verdict_is_refused():
    with pytest.raises(ValueError, match="shadow_verdict"):
        _well_formed_anchor(shadow_verdict="maybe")


def test_wrong_tier_is_refused():
    cert = _well_formed_anchor()
    cert.tier = "emit-check"
    with pytest.raises(ValueError, match="tier must be"):
        certs.validate_anchor_cert(cert)


# ============ FI-KA-1 tooth 2 mirror on B1's dispatch: no false green without Lean
def test_lean_absent_dispatch_yields_no_certificate():
    # "Trusting the fit": minting on the template-eval pass alone, without the
    # kernel run.  With Lean absent channel 1 is `unknown`, so adjudicate issues NO
    # certificate even though channel 2 passes -- the existing _lean_kernel_channel
    # honesty, reused byte-for-byte.
    if common.lean_available():
        pytest.skip("Lean toolchain present -- this tooth exercises the absent path")
    contract = _anchor_contract()
    kind, channels = kernel._dispatch({}, contract, None)
    assert kind == "exists-anchor-admission"
    assert channels[0]["backend"] == "lean-elaborate+lean4checker"
    assert channels[0]["result"] == "unknown"        # honest degrade, no verdict
    assert channels[1] is contract["template_eval_channel"]
    subject, cdesc = kernel._subject_and_cdesc({}, contract)
    out = kernel.adjudicate(kind, subject, common.sha256_json(cdesc), cdesc,
                            channels)
    assert not isinstance(out, Certificate)          # no false green without kernel

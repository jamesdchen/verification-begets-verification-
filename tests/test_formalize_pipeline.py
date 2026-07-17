"""WP-H: the statement-fidelity pipeline (run/formalize.py), Lean-free stages.

Every fidelity gate is decidable arithmetic over the F-G fragment, so the five
teeth are exercised WITHOUT a Lean toolchain.  The F0 kernel statement-cert is
the deferred, stronger layer -- assertions that need it are skipif-gated on
``common.lean_available()``.
"""
import json

import pytest

import common
import kernel
from kernel.certs import Certificate, ErrorTranscript
from run import formalize
from run.formalize import certify_statement


def _mk(theorem, statements):
    return json.dumps({"theorem": theorem, "statements": statements})


# The stage at which an instance/bounded-shadow refutation surfaces depends on
# the toolchain lane (first lean shakeout finding, §12.8.1): the failing
# fidelity channel rides INSIDE the statement-cert contract, so with Lean
# PRESENT the kernel adjudicates it there and refuses at "statement-cert"
# before stage 4 is ever reached; with Lean ABSENT statement-cert defers
# honestly and stage 4 issues the same refusal as "instances".  Both lanes
# REFUSE -- only the catching stage differs, and each lane is pinned strictly.
_INSTANCE_REFUSAL_STAGE = (
    "statement-cert" if common.lean_available() else "instances")


# A valid formalization: for every positive n and every k, n | n*k.
_VALID_SRC = "for every positive n and every k, n divides the product n times k"
_VALID = [
    {"id": "amb", "force": "choice", "quote": "",
     "lf": {"kind": "ambient", "carrier": "Int"}},
    {"id": "on", "force": "demand", "quote": "every positive n",
     "lf": {"kind": "object", "name": "n", "type": "Int"}},
    {"id": "ok", "force": "demand", "quote": "every k",
     "lf": {"kind": "object", "name": "k", "type": "Int"}},
    {"id": "q", "force": "demand", "quote": "for every positive n and every k",
     "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n", "k"]}},
    {"id": "h", "force": "presupposition", "quote": "positive n",
     "lf": {"kind": "hypothesis",
            "pred": {"op": "<", "args": [{"lit": 0}, {"ref": "n"}]}}},
    {"id": "c", "force": "demand", "quote": "n divides the product n times k",
     "lf": {"kind": "conclusion", "pred": {"op": "dvd", "args": [
         {"ref": "n"}, {"op": "*", "args": [{"ref": "n"}, {"ref": "k"}]}]}}},
]


def test_valid_passes_all_fidelity_gates():
    r = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    assert r.ok, r.error
    stages = [L[0] for L in r.layers]
    assert stages[:3] == ["math-reading-gate", "nonvacuity", "compile"]
    assert "instances" in stages
    assert r.lean_text.startswith("theorem ") and r.lean_text.rstrip().endswith(
        ":= sorry")
    # provenance covers the demanded conclusion and binds every object.
    covered = {sid for sids in r.provenance.values() for sid in sids}
    assert "c" in covered


def test_statement_cert_deferred_not_failed_when_lean_absent():
    r = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    if not common.lean_available():
        # honest deferral, not a pipeline failure and not a false green.
        assert r.ok
        assert r.statement_cert is None
        sc = next(L for L in r.layers if L[0] == "statement-cert")
        assert sc[1] is None            # deferred marker


# --- WP-KA false-deferral fix: statement-cert honesty (design-review finding) --
# The bug (pre-existing, predates WP-KA, run/formalize.py:636-642): the stage-3.5
# recorder labelled ANY non-Certificate kernel verdict "deferred: lean toolchain
# absent", conflating (i) Lean genuinely absent (honest deferral) with (ii) Lean
# PRESENT + a kernel-channel refutation (a false deferral hiding a real failure).
# The fix branches on common.lean_available(): the absent path is byte-identical;
# the Lean-present ErrorTranscript path REFUSES with the transcript's reason.
def _error_transcript_fail():
    """A synthetic kernel refutation: channel-1 (the kernel audit) FAILS on the
    real statement -- the pp.all-roundtrip / wrong-instance class F0 catches."""
    return ErrorTranscript(
        verdict="fail", subject_hash="subj", contract_hash="chash",
        channels=[
            {"backend": "lean-elaborate+lean4checker", "result": "fail",
             "detail": "pp.all round-trip not def-eq (D6): wrong-instance"},
            {"backend": "nonvacuity", "result": "pass", "detail": "sat"},
            {"backend": "entailed-instances", "result": "pass", "detail": "hold"}],
        failing_input="", observed="not-def-eq", expected="def-eq",
        llm_feedback="pp.all round-trip is not definitionally equal (D6)")


def test_ka_lean_present_error_transcript_refuses_never_absent(monkeypatch):
    # Tooth (a): Lean PRESENT + a failing kernel channel (monkeypatched verdict)
    # -> the pipeline REFUSES at stage 'statement-cert', the layer carries the
    # transcript's failure, and the word "absent" appears NOWHERE (the honest
    # record, not the absent-toolchain fiction).
    monkeypatch.setattr(common, "lean_available", lambda: True)
    et = _error_transcript_fail()
    monkeypatch.setattr(kernel, "check", lambda *a, **k: et)
    r = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    assert not r.ok and r.stage == "statement-cert"
    assert r.statement_cert is None
    sc = next(L for L in r.layers if L[0] == "statement-cert")
    assert sc[1] is False                                  # refused, not deferred
    flat = json.dumps(sc) + " " + r.error
    assert "absent" not in flat, "false-deferral fiction leaked with Lean present"
    assert "verdict" in dict(sc[2]) or any(k == "verdict" for k, _ in sc[2])
    assert dict(sc[2]).get("lean-elaborate+lean4checker") == "fail"
    assert "pp.all round-trip" in r.error                  # transcript reason


def test_ka_lean_absent_statement_cert_layer_byte_identical():
    # Tooth (b): the committed-corpus PIN.  With Lean absent the recorder must be
    # byte-identical to the pre-edit capture -- statement_cert None, ok True, and
    # the exact "deferred: lean toolchain absent" layer.  (Guard: only meaningful
    # when Lean is genuinely absent, the committed-corpus condition.)
    if common.lean_available():
        pytest.skip("committed-corpus pin is the Lean-absent recording")
    r = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    assert r.ok is True
    assert r.statement_cert is None
    sc = next(L for L in r.layers if L[0] == "statement-cert")
    assert sc == ("statement-cert", None,
                  [("lean-elaborate+lean4checker",
                    "deferred: lean toolchain absent")])


def test_ka_certificate_path_untouched(monkeypatch):
    # Tooth (c): when the kernel ISSUES a Certificate the recorder is unchanged --
    # statement_cert is the cert, the layer is ('statement-cert', True, channels).
    cert = Certificate.make(
        "statement-cert-admission", "subj", "chash",
        [{"backend": "lean-elaborate+lean4checker", "result": "pass"},
         {"backend": "nonvacuity", "result": "pass"},
         {"backend": "entailed-instances", "result": "pass"}],
        tier="emit-check")
    monkeypatch.setattr(kernel, "check", lambda *a, **k: cert)
    r = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    assert r.ok
    assert r.statement_cert is cert
    sc = next(L for L in r.layers if L[0] == "statement-cert")
    assert sc[0] == "statement-cert" and sc[1] is True
    assert ("lean-elaborate+lean4checker", "pass") in sc[2]


def test_t1_fabricated_conclusion_refused_at_gate():
    doc = [dict(s) for s in _VALID]
    doc[-1] = {**doc[-1], "quote": "n is prime"}   # not in the source
    r = certify_statement(_VALID_SRC, _mk("t1", doc))
    assert not r.ok and r.stage == "math-reading-gate"


def test_t2_contradictory_hypotheses_refused_at_nonvacuity():
    src = "for every n greater than five and less than three, n is even"
    t2 = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "o", "force": "demand", "quote": "every n",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "for every n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "h1", "force": "presupposition", "quote": "greater than five",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "<", "args": [{"lit": 5}, {"ref": "n"}]}}},
        {"id": "h2", "force": "presupposition", "quote": "less than three",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "<", "args": [{"ref": "n"}, {"lit": 3}]}}},
        {"id": "c", "force": "demand", "quote": "n is even",
         "lf": {"kind": "conclusion", "pred": {"op": "even",
                                               "args": [{"ref": "n"}]}}},
    ]
    r = certify_statement(src, _mk("t2", t2))
    assert not r.ok and r.stage == "nonvacuity"


def test_t3_wrong_operator_binding_refused_at_instances():
    src = "for all a and b, if a divides b then a divides b"
    t3 = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "demand", "quote": "all a",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "demand", "quote": "b",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "for all a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h", "force": "presupposition", "quote": "a divides b",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}},
        {"id": "c", "force": "demand", "quote": "a divides b",
         "lf": {"kind": "conclusion",              # bound the WRONG way: b | a
                "pred": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}},
    ]
    r = certify_statement(src, _mk("t3", t3))
    assert not r.ok and r.stage == _INSTANCE_REFUSAL_STAGE


def test_t4_narrowed_carrier_refused_at_instances():
    src = "for all integers a and b, a minus b plus b equals a"
    t4 = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},          # narrowed
        {"id": "oa", "force": "demand", "quote": "integers a",
         "lf": {"kind": "object", "name": "a", "type": "Nat"}},
        {"id": "ob", "force": "demand", "quote": "b",
         "lf": {"kind": "object", "name": "b", "type": "Nat"}},
        {"id": "q", "force": "demand", "quote": "for all integers a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "c", "force": "demand", "quote": "a minus b plus b equals a",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [
                 {"op": "-", "args": [{"ref": "a"}, {"ref": "b"}]}, {"ref": "b"}]},
             {"ref": "a"}]}}},
    ]
    r = certify_statement(src, _mk("t4", t4))
    assert not r.ok and r.stage == _INSTANCE_REFUSAL_STAGE


def test_t5_omitted_presupposition_certifies_but_examiner_diverges():
    # Drop the "0 < n" presupposition: `n | n*k` is true for every n (0 | 0),
    # so every fidelity gate passes -- only the examiner's meaning-expectation
    # catches the gap.  This is the plan's reason to exist (L3: evidence, not a
    # refusal).
    doc = [s for s in _VALID if s["id"] != "h"]
    expectations = json.dumps({"expectations": [
        {"kind": "positive", "assignment": {"n": 3, "k": 2}, "expect": "holds",
         "why": "3 | 6"},
        {"kind": "boundary", "assignment": {"n": 0, "k": 5}, "expect": "outside",
         "why": "n=0 not positive"},
    ]})
    r = certify_statement(_VALID_SRC, _mk("t5", doc),
                          expectations_json=expectations)
    assert r.ok                                   # fidelity certifies
    assert r.examiner.get("converged") is False   # examiner catches the meaning
    diverged = r.examiner.get("diverged", [])
    assert any(d["assignment"] == {"n": 0, "k": 5} and d["conclusion_holds"]
               for d in diverged)


def test_examiner_is_evidence_never_a_refusal():
    # Even a maximally-divergent examiner cannot flip the pipeline's ok verdict
    # (L3): the examiner neither issues nor blocks the certificate.
    doc = [s for s in _VALID if s["id"] != "h"]
    expectations = json.dumps({"expectations": [
        {"kind": "positive", "assignment": {"n": 1, "k": 1}, "expect": "holds",
         "why": "1 | 1"},
        {"kind": "boundary", "assignment": {"n": 0, "k": 0}, "expect": "outside",
         "why": "boundary"},
    ]})
    r = certify_statement(_VALID_SRC, _mk("t5b", doc),
                          expectations_json=expectations)
    assert r.ok                                   # divergence never refuses


def test_determinism_statement_hash_stable():
    r1 = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    r2 = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    assert r1.statement_hash == r2.statement_hash and r1.statement_hash


# --- B3 -> T6b: the bounded-shadow ∃ mode (COMPRESSION.md §11.6) ---------------
# WHY these teeth changed shape: pre-T6b, ANY exists binder honest-skipped at the
# `quantifier-support` stage (the eval/SMT mirrors had no quantifier handling).
# §11.6 re-specs the rung as an EVAL-CHANNEL finitization: a SUPPORTED ∀-outer/
# ∃-inner reading now runs the ∃-aware gate and certifies with a BOUNDED-SHADOW
# fidelity channel (the compiled ∃ stays real in lean_text); shapes BEYOND the
# mode still honest-skip.  The bounded-shadow semantics are pinned here and
# documented in generators/math_eval.py's module docstring.
def _with_binder(binder):
    doc = [dict(s) for s in _VALID]
    for i, s in enumerate(doc):
        if s["lf"]["kind"] == "quantifier":
            doc[i] = {**s, "lf": {**s["lf"], "binder": binder}}
    return doc


# A supported ∀-outer/∃-inner reading: ∀ n:Int, ∃ m:Int, m + n = 0 (additive
# inverse).  TRUE under the bounded shadow with NO edge issue -- for every
# n∈[-B,B] the witness m = -n is itself in [-B,B] (the additive-inverse map is a
# bijection on the box), which is exactly why it certifies where the edge-y
# `∀n ∃m, n<m` (below) does not.
_ADDINV_SRC = ("for every integer n there exists an integer m with m plus n "
               "equal to zero")
_ADDINV = [
    {"id": "amb", "force": "choice", "quote": "",
     "lf": {"kind": "ambient", "carrier": "Int"}},
    {"id": "on", "force": "demand", "quote": "every integer n",
     "lf": {"kind": "object", "name": "n", "type": "Int"}},
    {"id": "om", "force": "demand", "quote": "there exists an integer m",
     "lf": {"kind": "object", "name": "m", "type": "Int"}},
    {"id": "q1", "force": "demand", "quote": "for every integer n",
     "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
    {"id": "q2", "force": "demand", "quote": "there exists an integer m",
     "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
    {"id": "c", "force": "demand", "quote": "m plus n equal to zero",
     "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
         {"op": "+", "args": [{"ref": "m"}, {"ref": "n"}]}, {"lit": 0}]}}},
]


def test_t6b_true_forall_exists_certifies_bounded_shadow():
    # (a) a TRUE ∀∃ reading no longer honest-skips: it runs the ∃-aware gate and
    # certifies with the bounded-shadow evidence, and lean_text keeps the real ∃.
    r = certify_statement(_ADDINV_SRC, _mk("addinv", _ADDINV))
    assert r.ok, r.error
    # the compiled statement carries the REAL ∃ (the eval channel is finitized,
    # the compiler is untouched -- the workaround this dissolves).
    assert "∃" in r.lean_text
    # the bounded-shadow evidence is observable in the instances layer (with Lean
    # absent no Certificate issues, so this layer is where the channel surfaces).
    inst = dict((L[0], (L[1], L[2])) for L in r.layers)["instances"]
    assert inst[0] is True
    detail = dict(inst[1])
    assert detail["bounded-shadow"] == "pass"
    assert detail["backend"] == "exists-finitized-enum"
    # SMT is recorded ABSENT (enum-only) for ∃ readings -- a declared limitation.
    nv = dict((L[0], L[2]) for L in r.layers)["nonvacuity"]
    assert ["enum-only", "True"] in [list(c) for c in nv]
    # honest tier discipline: no false green from a kernel channel that never ran.
    if not common.lean_available():
        assert r.statement_cert is None


def test_t6b_bound_is_not_baked_into_bytes():
    # B is the runtime bound, never part of the compiled statement identity: two
    # runs at different bounds compile to the SAME statement_hash (bytes keep the
    # unbounded ∃), while the bounded-shadow evidence records the bound as data.
    r8 = certify_statement(_ADDINV_SRC, _mk("addinv", _ADDINV), bound=8)
    r5 = certify_statement(_ADDINV_SRC, _mk("addinv", _ADDINV), bound=5)
    assert r8.ok and r5.ok
    assert r8.statement_hash == r5.statement_hash    # bound not in the bytes
    d8 = dict(dict((L[0], L[2]) for L in r8.layers)["instances"])
    d5 = dict(dict((L[0], L[2]) for L in r5.layers)["instances"])
    assert d8["bound"] == "8" and d5["bound"] == "5"


def test_t6b_bound_edge_refutation_is_conservative():
    # (a', the edge policy) ∀ n:Int, ∃ m:Int, n < m is TRUE unbounded, but the
    # bounded shadow claims only "∃ m within [-B,B]": at n = B no in-bound m
    # exceeds B, so the shadow REFUTES with the OUTER witness n = B.  This is the
    # deliberate bound-edge honesty (conservative: never a false green).
    src = ("for every integer n there exists an integer m with n less than m")
    succ = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "on", "force": "demand", "quote": "every integer n",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "om", "force": "demand", "quote": "there exists an integer m",
         "lf": {"kind": "object", "name": "m", "type": "Int"}},
        {"id": "q1", "force": "demand", "quote": "for every integer n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "q2", "force": "demand", "quote": "there exists an integer m",
         "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
        {"id": "c", "force": "demand", "quote": "n less than m",
         "lf": {"kind": "conclusion",
                "pred": {"op": "<", "args": [{"ref": "n"}, {"ref": "m"}]}}},
    ]
    r = certify_statement(src, _mk("succ", succ), bound=8)
    assert not r.ok and r.stage == _INSTANCE_REFUSAL_STAGE
    assert "witness={'n': 8}" in r.error          # the outer bound-edge assignment


def test_t6b_false_exists_refutes_with_witness():
    # (b) a FALSE bounded existential: ∀ n:Nat, ∃ m:Nat, m + 1 = n -- the Nat
    # predecessor, which does NOT exist at n = 0 (m would be -1, out of Nat).  The
    # bounded shadow refutes with the outer witness n = 0 (the 28_predecessor
    # story: no false green from a k-smallest mask; the FULL bounded disjunction
    # is genuinely empty here).
    src = ("for every natural number n there exists a natural number m with m "
           "plus one equal to n")
    pred = [
        {"id": "on", "force": "demand", "quote": "every natural number n",
         "lf": {"kind": "object", "name": "n", "type": "Nat"}},
        {"id": "om", "force": "demand", "quote": "there exists a natural number m",
         "lf": {"kind": "object", "name": "m", "type": "Nat"}},
        {"id": "q1", "force": "demand", "quote": "for every natural number n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "q2", "force": "demand", "quote": "there exists a natural number m",
         "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
        {"id": "c", "force": "demand", "quote": "m plus one equal to n",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [{"ref": "m"}, {"lit": 1}]}, {"ref": "n"}]}}},
    ]
    r = certify_statement(src, _mk("pred", pred))
    assert not r.ok and r.stage == _INSTANCE_REFUSAL_STAGE
    assert "witness={'n': 0}" in r.error


def test_t6b_exists_only_still_honest_skips():
    # (c) a shape BEYOND the mode still honest-skips (never universalised): an
    # exists-only reading has no outer scope, so it is out of the ∀-outer/∃-inner
    # bounded shadow.  This keeps the pre-T6b B3 discipline for unsupported shapes.
    r = certify_statement(_VALID_SRC, _mk("ex", _with_binder("exists")))
    assert not r.ok                                   # never a green cert
    assert r.stage == "quantifier-support"
    assert "exists-unsupported-by-eval-mirrors" in r.error
    assert "exists-only" in r.error
    assert r.statement_cert is None
    # the mirror gates never ran -- no universalisation.
    stages = [L[0] for L in r.layers]
    assert "nonvacuity" not in stages and "instances" not in stages


def test_t6b_exists_before_forall_still_honest_skips():
    # (c') an ∃-before-∀ interleaving compiles to ∃...∀... (∃-outer/∀-inner),
    # NOT the ∀*∃* prefix the shadow models -- honest-skip with the named reason.
    src = ("there exists an integer m such that for every integer n we have m "
           "plus n equal to n plus m")
    inter = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "on", "force": "demand", "quote": "every integer n",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "om", "force": "demand", "quote": "there exists an integer m",
         "lf": {"kind": "object", "name": "m", "type": "Int"}},
        {"id": "q1", "force": "demand", "quote": "there exists an integer m",
         "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
        {"id": "q2", "force": "demand", "quote": "for every integer n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "c", "force": "demand", "quote": "m plus n equal to n plus m",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [{"ref": "m"}, {"ref": "n"}]},
             {"op": "+", "args": [{"ref": "n"}, {"ref": "m"}]}]}}},
    ]
    r = certify_statement(src, _mk("inter", inter))
    assert not r.ok and r.stage == "quantifier-support"
    assert "exists-before-forall" in r.error


def test_forall_reading_byte_unaffected_by_t6b():
    # the exists routing fires only when an ∃ binder is present, so the forall
    # path is byte-identical to the pre-T6b result: same verdict, hash,
    # provenance, layers.
    base = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    same = certify_statement(_VALID_SRC, _mk("valid", _with_binder("forall")))
    assert same.ok and base.ok
    assert same.statement_hash == base.statement_hash
    assert same.provenance == base.provenance
    assert [L[0] for L in same.layers] == [L[0] for L in base.layers]
    assert "quantifier-support" not in [L[0] for L in base.layers]

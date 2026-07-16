"""WP-H: the statement-fidelity pipeline (run/formalize.py), Lean-free stages.

Every fidelity gate is decidable arithmetic over the F-G fragment, so the five
teeth are exercised WITHOUT a Lean toolchain.  The F0 kernel statement-cert is
the deferred, stronger layer -- assertions that need it are skipif-gated on
``common.lean_available()``.
"""
import json

import pytest

import common
from run.formalize import certify_statement


def _mk(theorem, statements):
    return json.dumps({"theorem": theorem, "statements": statements})


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
    assert not r.ok and r.stage == "instances"


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
    assert not r.ok and r.stage == "instances"


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


# --- B3: an exists binder is honest-skipped, never universalised silently -----
def _with_binder(binder):
    doc = [dict(s) for s in _VALID]
    for i, s in enumerate(doc):
        if s["lf"]["kind"] == "quantifier":
            doc[i] = {**s, "lf": {**s["lf"], "binder": binder}}
    return doc


def test_exists_binder_honest_skip_never_green():
    # The eval/SMT mirrors have no quantifier handling, so an exists-bound object
    # is enumerated universally; a green cert would claim the wrong statement.
    r = certify_statement(_VALID_SRC, _mk("ex", _with_binder("exists")))
    assert not r.ok                                   # never a green cert
    assert r.stage == "quantifier-support"
    assert "exists-unsupported-by-eval-mirrors" in r.error
    assert r.statement_cert is None
    # the mirror gates (nonvacuity / instances) never ran -- no universalisation.
    stages = [L[0] for L in r.layers]
    assert "nonvacuity" not in stages and "instances" not in stages


def test_forall_reading_byte_unaffected_by_b3():
    # the tripwire fires only on non-forall binders, so the forall path is
    # byte-identical to the pre-B3 result: same verdict, hash, provenance, layers.
    base = certify_statement(_VALID_SRC, _mk("valid", _VALID))
    same = certify_statement(_VALID_SRC, _mk("valid", _with_binder("forall")))
    assert same.ok and base.ok
    assert same.statement_hash == base.statement_hash
    assert same.provenance == base.provenance
    assert [L[0] for L in same.layers] == [L[0] for L in base.layers]
    assert "quantifier-support" not in [L[0] for L in base.layers]

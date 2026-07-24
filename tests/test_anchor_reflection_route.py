"""S4b ceremony teeth: the reflection discharge routes on exists-anchor-cert.

Lean-free (the reference-builder pattern of test_anchor_cert_contract): the
route vocabulary, the shape-pending refusals, the unknown-discharge refusal,
and the ladder/reflection PARITY join -- two certs for the same statement,
one per discharge family, must share the subject key and differ exactly in
the route-qualified discharge claim.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from kernel import certs

S43 = ("theorem s43_larger_integer_exists : "
       "∀ (n : Int), ∃ (m : Int), n < m := sorry")
H43 = common.sha256_bytes(S43.encode())
T43 = {"m": {"op": "+", "args": [{"ref": "n"}, {"lit": 1}]}}
P_LADDER = S43.replace(" := sorry", " := by\n  intro n\n  exact ⟨n + 1, by omega⟩")
P_REFLECT = "-- FgReflect module + checkAll_witness examples (probe bytes)"


def _mint(discharge, lean_text):
    return certs.make_anchor_cert(
        statement_hash=H43, lean_text=lean_text, template=T43,
        discharge=discharge, shadow_verdict="refuted", shadow_bound=8,
        emitter_hash="emit-sha-0", axioms=("Classical.choice", "propext"))


def test_reflection_route_mints():
    cert = _mint("reflection/checkAll_witness", P_REFLECT)
    certs.validate_anchor_cert(cert)
    claims = dict(cert.claims)
    assert claims["discharge"] == "reflection/checkAll_witness"
    assert claims["lattice_point"] == "kernel-proved"


def test_ladder_rungs_still_mint():
    for rung in certs.ANCHOR_DISCHARGE_RUNGS:
        certs.validate_anchor_cert(_mint(rung, P_LADDER))


def test_reserved_routes_refused_shape_pending():
    # routes 2-3 are IN the vocabulary (maintainer-signed) but their shapes
    # (template-free search, forall-guard) do not fit this cert kind; the
    # validator must refuse with the shape-pending message, never mint.
    for route in certs.ANCHOR_REFLECTION_ROUTES[1:]:
        with pytest.raises(ValueError, match="SHAPE-PENDING"):
            _mint(route, P_REFLECT)


def test_unknown_discharge_refused():
    for bad in ("native_decide", "reflection/witness_of_check", "sorry", ""):
        with pytest.raises(ValueError, match="discharge"):
            _mint(bad, P_LADDER)


def test_ladder_reflection_parity_join():
    # the cert-level parity the ceremony promises: same statement, two
    # discharge families -> identical subject join key (statement_hash is the
    # raw-statement sha both ways), identical lattice point, and the ONLY
    # intended claims difference is the discharge itself.
    a = _mint("omega", P_LADDER)
    b = _mint("reflection/checkAll_witness", P_REFLECT)
    assert a.subject_hash == b.subject_hash == H43
    ca, cb = dict(a.claims), dict(b.claims)
    assert ca.pop("discharge") == "omega"
    assert cb.pop("discharge") == "reflection/checkAll_witness"
    assert ca == cb
    # evidence differs (different proof bytes), identity does not: the proof
    # rides the contract hash, never the subject.
    assert a.contract_hash != b.contract_hash

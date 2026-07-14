#!/usr/bin/env python3
"""CF1/CF2 regression guard: the cage certificate has REAL teeth on every layer
it claims -- egress AND per-call constraint -- proved by NEGATIVE tests.

An earlier adversarial review found two false-greens in the `cage-conformance`
(tier "monitored") contract: the certificate CLAIMS egress and per-call
constraint as boundary layers, but no certification channel exercised them, so a
cage that NEUTERED egress or DROPPED the constraint check still certified GREEN.

This test builds the demo store cage (which declares an output_schema on every
tool AND a per-call constraint qty>=1 on `reserve`) three ways and asserts the
teeth bite:

  * INTACT       -> certifies (kernel.check returns a Certificate, tier
                    "monitored").
  * EGRESS NEUTERED (output validators replaced by a pass-through `decode`)
                 -> FAILS: the containment channel's egress-teeth probe drives the
                    FULL caged pipeline with a schema-violating incumbent output
                    and observes the neutered cage admit it (no `egress` refusal).
  * CONSTRAINT DROPPED (the dispatcher's `for c in CONSTRAINTS.get(...)` check
                    made inert) -> FAILS: containment feeds a solver-generated
                    input that satisfies schema + guard but violates the
                    constraint; the independent reference rejects it, so the
                    constraint-dropping dispatcher ADMITS a call the oracle
                    rejects (a containment breach).

Both neutered cages must yield an ErrorTranscript, not a Certificate.  Runnable
under pytest AND as `python3 tests/test_cage_teeth.py` (prints PASS/<case>).
"""
from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from kernel.certs import Certificate, ErrorTranscript
from generators import service_model
from run import guarded
from demo_guarded import STORE, HONEST_SRC

# a pass-through output validator: `decode` accepts ANY value -> egress neutered
_PASS_THROUGH = b"def decode(x):\n    return x\n"


def _model():
    return service_model.parse_service_spec(json.dumps(STORE))


def _intact_cage(m):
    """The demo store cage, fully intact."""
    return guarded.Cage(m, HONEST_SRC)


def _egress_neutered_cage(m):
    """(a) egress validators replaced with a pass-through -- egress has no teeth."""
    cage = guarded.Cage(m, HONEST_SRC)
    assert cage._egress_files, "fixture must declare >=1 output_schema tool"
    cage._egress_files = {n: _PASS_THROUGH for n in cage._egress_files}
    return cage


def _constraint_dropped_cage(m):
    """(b) the emitted dispatcher's per-call constraint check made inert (the loop
    iterates over [] instead of CONSTRAINTS.get(tool, []))."""
    cage = guarded.Cage(m, HONEST_SRC)
    svc = cage._dispatcher_files["service.py"].decode()
    dropped = svc.replace("CONSTRAINTS.get(tool, [])", "[]")
    assert dropped != svc, "constraint-drop patch did not match the emitted dispatcher"
    cage._dispatcher_files = dict(cage._dispatcher_files,
                                  **{"service.py": dropped.encode()})
    return cage


def _containment_channel(v):
    """The cage-containment channel dict from a Certificate or ErrorTranscript
    (both carry the full channel list)."""
    return next((c for c in v.channels
                 if c["backend"] == "cage-containment"), None)


# --- the three assertions ----------------------------------------------------
def test_intact_cage_certifies():
    """The intact demo cage certifies at tier 'monitored' (both teeth pass)."""
    m = _model()
    v = guarded.certify_cage(_intact_cage(m), m)
    assert isinstance(v, Certificate), (
        "intact cage must certify, got %r" % (getattr(v, "llm_feedback", v),))
    assert v.tier == "monitored", ("tier", v.tier)


def test_egress_neutered_cage_fails():
    """A cage whose egress validators are pass-through FAILS cage-conformance:
    the containment egress-teeth probe (CF1) catches the admitted bad output."""
    m = _model()
    v = guarded.certify_cage(_egress_neutered_cage(m), m)
    assert isinstance(v, ErrorTranscript), (
        "egress-neutered cage must NOT certify, got a Certificate")
    ch = _containment_channel(v)
    assert ch is not None and ch["result"] != "pass", (
        "expected the containment channel to fail", ch)
    assert "egress" in ch["detail"].lower(), (
        "containment must fail on egress teeth", ch["detail"])


def test_constraint_dropped_cage_fails():
    """A dispatcher with the per-call constraint check dropped FAILS
    cage-conformance: containment (CF2) feeds a schema+guard-legal but
    constraint-violating input the reference rejects and the cage admits."""
    m = _model()
    v = guarded.certify_cage(_constraint_dropped_cage(m), m)
    assert isinstance(v, ErrorTranscript), (
        "constraint-dropped cage must NOT certify, got a Certificate")
    ch = _containment_channel(v)
    assert ch is not None and ch["result"] != "pass", (
        "expected the containment channel to fail", ch)
    assert "reject" in ch["detail"].lower() or "admit" in ch["detail"].lower(), (
        "containment must fail on an admitted reference-rejected call", ch["detail"])


if __name__ == "__main__":
    m = _model()

    v = guarded.certify_cage(_intact_cage(m), m)
    assert isinstance(v, Certificate), "intact cage failed to certify"
    print("PASS intact-cage-certifies  tier=%r  #claims=%d  #non_claims=%d"
          % (v.tier, len(v.claims), len(v.non_claims)))

    v = guarded.certify_cage(_egress_neutered_cage(m), m)
    assert isinstance(v, ErrorTranscript), "egress-neutered cage wrongly certified"
    print("PASS egress-neutered-fails  containment: %s"
          % _containment_channel(v)["detail"][:100])

    v = guarded.certify_cage(_constraint_dropped_cage(m), m)
    assert isinstance(v, ErrorTranscript), "constraint-dropped cage wrongly certified"
    print("PASS constraint-dropped-fails  containment: %s"
          % _containment_channel(v)["detail"][:100])

    print("\ncage teeth hold: neutered egress and dropped constraint both FAIL "
          "certification; the intact cage certifies")

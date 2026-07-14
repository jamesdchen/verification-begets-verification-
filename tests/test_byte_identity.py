#!/usr/bin/env python3
"""P1.6 byte-identity rule (house rule 8): adding the temporal/terminal machinery
must NOT change the emitted bytes for specs that do not use it.

Certificates are content-addressed, so an unconditional new key in an emitted
template would invalidate every existing certificate and cache entry.  Phase 1
adds the monitor dispatcher wiring, the reference monitor wiring, the LTLf
obligation and the idle discipline -- all behind CONDITIONAL emission.  This test
pins the four affected emitters on every pre-Phase-1 demo spec:

  * generators.service_gen.emit_service       (orders, tickets)
  * generators.service_gen.ref_service_source (orders, tickets)
  * generators.protocol_gen.bmc_smtlib        (orders/tickets projections, order)
       -- the NEW post-P1.3-idle-discipline output IS the pinned baseline; the
          point is that ADDING temporal features to a spec that doesn't use them
          changes nothing, NOT that idle discipline changed nothing (it did, once
          and globally, which is why CERTS_VERSION was bumped 2 -> 3).
  * generators.protocol_gen.emit_validator / constraint_gen.emit_validator

Two properties:
  (a) golden hashes: every function/spec pair matches tests/golden/byte_identity.
  (b) conditional-emission no-op: emitting a plain spec is byte-identical to
      emitting the SAME spec with an empty `obligations: []` (and no terminal
      flags) declared -- proving the temporal branches are truly conditional.

The emitters embed Python `set(...)` reprs, whose order is PYTHONHASHSEED-
dependent; the golden was captured under seed 0, so this test re-execs itself
under PYTHONHASHSEED=0 for a deterministic comparison.  Runnable under pytest and
as `python3 tests/test_byte_identity.py`.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _reexec_seeded():
    """Ensure a deterministic hash seed for stable set-repr in emitted code."""
    if os.environ.get("PYTHONHASHSEED") != "0":
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = "0"
        os.execve(sys.executable, [sys.executable, __file__], env)


# under pytest the module is imported (not __main__); seed via the collected
# environment if possible, else skip the seed-sensitive golden check gracefully.
sys.path.insert(0, str(_ROOT))

from generators import (service_model, service_gen, protocol_model,
                        protocol_gen, constraint_model, constraint_gen)

GOLDEN = json.loads((_ROOT / "tests" / "golden" / "byte_identity.json").read_text())
SERVICE_SPECS = {"orders": "specs/services/orders.json",
                 "tickets": "specs/services/tickets.json"}


def _h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _current_hashes() -> dict:
    now = {}
    for name, rel in SERVICE_SPECS.items():
        m = service_model.parse_service_spec((_ROOT / rel).read_text())
        now[f"{name}:emit_service"] = _h(service_gen.emit_service(m)["service.py"])
        now[f"{name}:ref_service_source"] = _h(
            service_gen.ref_service_source(m).encode())
        pm = protocol_model.parse_protocol_spec(m.protocol_spec_text())
        K, _ = pm.acyclic_bound()
        now[f"{name}:bmc_smtlib"] = _h(protocol_gen.bmc_smtlib(pm, K).encode())
        now[f"{name}:emit_validator"] = _h(
            protocol_gen.emit_validator(pm)["validator.py"])
    pm = protocol_model.parse_protocol_spec(
        (_ROOT / "specs/protocols/order.json").read_text())
    K, _ = pm.acyclic_bound()
    now["order:bmc_smtlib"] = _h(protocol_gen.bmc_smtlib(pm, K).encode())
    now["order:emit_validator"] = _h(protocol_gen.emit_validator(pm)["validator.py"])
    cm = constraint_model.parse_constraint_spec(
        (_ROOT / "specs/constraints/book_meeting.json").read_text())
    now["book_meeting:emit_validator"] = _h(
        constraint_gen.emit_validator(cm)["validator.py"])
    return now


def test_golden_byte_identity():
    """Every pinned emitter/spec pair is byte-identical to the committed golden
    (deterministic under PYTHONHASHSEED=0)."""
    if os.environ.get("PYTHONHASHSEED") != "0":
        # seed-sensitive: verified as a bare script; the conditional-emission
        # test below is seed-robust and always runs.
        import pytest
        pytest.skip("golden hashes are pinned under PYTHONHASHSEED=0; "
                    "run `python3 tests/test_byte_identity.py`")
    now = _current_hashes()
    mismatch = {k: (GOLDEN[k], now.get(k)) for k in GOLDEN if GOLDEN[k] != now.get(k)}
    assert not mismatch, f"byte-identity drift: {sorted(mismatch)}"


def test_conditional_emission_is_a_noop():
    """Emitting a plain spec == emitting it with an empty `obligations: []`
    declared: the temporal branches are truly conditional (seed-robust: both
    sides are hashed in THIS process, so set-repr order cancels out)."""
    for name, rel in SERVICE_SPECS.items():
        doc = json.loads((_ROOT / rel).read_text())
        assert not doc.get("obligations"), f"{name} unexpectedly has obligations"
        doc_empty = dict(doc, obligations=[])
        m0 = service_model.parse_service_spec(json.dumps(doc))
        m1 = service_model.parse_service_spec(json.dumps(doc_empty))
        assert service_gen.emit_service(m0)["service.py"] == \
            service_gen.emit_service(m1)["service.py"], f"{name}: emit_service drift"
        assert service_gen.ref_service_source(m0) == \
            service_gen.ref_service_source(m1), f"{name}: ref_service drift"
        # and no temporal machinery leaked into a plain dispatcher
        src = service_gen.emit_service(m0)["service.py"]
        for marker in (b"MON_TABLES", b"TERMINAL_TOOLS", b'"obligation"',
                       b"self.mon"):
            assert marker not in src, f"{name}: temporal marker {marker!r} leaked"


if __name__ == "__main__":
    _reexec_seeded()
    now = _current_hashes()
    mismatch = {k: (GOLDEN[k], now.get(k))
                for k in GOLDEN if GOLDEN[k] != now.get(k)}
    if mismatch:
        for k in sorted(mismatch):
            print("DRIFT", k, mismatch[k])
        print("byte-identity FAILED")
        sys.exit(1)
    print(f"PASS golden byte-identity ({len(GOLDEN)} emitter/spec pairs)")
    test_conditional_emission_is_a_noop()
    print("PASS conditional-emission no-op (plain specs emit no temporal code)")
    print("byte-identity holds: temporal features do not perturb plain specs")

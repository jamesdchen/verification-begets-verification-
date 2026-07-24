#!/usr/bin/env python3
"""P1 temporal TEETH -- the stranding query and the pending predicate must be
sound and honest.  Runnable under pytest AND as a bare script
(`python3 tests/test_temporal_teeth.py` -> PASS lines, exit 0).

Three teeth pin the adversarial-review fixes:

  (a) TF1 -- the GAMED stranding service (an unguarded `abandon: active->closed`
      PLUS an inert `noop: closed->closed` self-loop) must FAIL certification.
      The self-loop makes `closed` a non-sink, so the OLD "last real action is a
      completing (terminal/to-sink) action" query went vacuously unsat and the
      genuinely-stranding service CERTIFIED.  The product DEAD-END reachability
      query refutes it (both solvers) with the shortest strand [hold, abandon],
      and kernel.check(protocol-cert) returns a non-Certificate.
  (b) a genuinely-safe `eventually` service (the terminal `close` is refused
      while the monitor pends, so the demand is always dischargeable before the
      session ends) still CERTIFIES: the query is unsat on both solvers and
      kernel.check(protocol-cert) issues a Certificate.
  (c) PF2 -- a `within` monitor's MISSED-DEADLINE state reports pending()==False
      (permanently decided, not open), so a consumer waiting for `not pending()`
      does not deadlock after the deadline lapses.
"""
from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

import kernel
from kernel.certs import Certificate
from kernel.backends import SmtBackend
from generators import (service_model, protocol_model, protocol_gen, monitor_gen,
                        ltlf_smt)
from demos import demo_temporal as dt

_EMPTY_SCH = {"type": "object", "properties": {}, "required": [],
              "additionalProperties": False}


def _gamed_service() -> dict:
    """demo_temporal's STRANDS (unguarded `abandon` exit) plus an INERT
    `noop: closed->closed` self-loop -- the loop makes `closed` a non-sink so the
    old completing-action query could no longer see the strand."""
    g = json.loads(json.dumps(dt.STRANDS))
    g["name"] = "gamed"
    g["tools"].append(
        {"name": "noop", "from": "closed", "to": "closed", "input_schema": _EMPTY_SCH})
    return g


def _protocol_of(service_dict: dict):
    m = service_model.parse_service_spec(json.dumps(service_dict))
    return protocol_model.parse_protocol_spec(m.protocol_spec_text())


def _dual_verdict(pm, obligation, K):
    """(z3_result, cvc5_result) for the stranding obligation.  'fail' == sat ==
    a strand exists (refuted); 'pass' == unsat == certified."""
    obl = ltlf_smt.protocol_temporal_smtlib(pm, obligation, K)
    smt = SmtBackend()
    return smt.run_z3(obl)["result"], smt.run_cvc5(obl)["result"]


# ---------------------------------------------------------------------------
def test_gamed_noop_stranding_service_is_refuted():
    """(a) TF1 PRIMARY: the gamed noop-self-loop strander FAILS certification."""
    pm = _protocol_of(_gamed_service())
    o = pm.obligations[0]
    K = protocol_gen.temporal_bound(pm, pm.acyclic_bound()[0])

    # The defeated OLD heuristic: because `closed` is no longer a structural
    # sink, the session-ending `abandon` is NOT a "completing action" -- the old
    # query keyed on exactly this list and so went vacuously unsat.
    assert "closed" not in pm.sink_states(), "noop should make closed a non-sink"
    assert "abandon" not in pm.completing_actions(), \
        "the gamed noop defeats the old completing-action notion"

    # The product DEAD-END query refutes the strand on BOTH solvers.
    z, c = _dual_verdict(pm, o, K)
    assert z == "fail" and c == "fail", \
        f"gamed strander must be REFUTED by both solvers, got z3={z} cvc5={c}"

    # ... with the shortest strand [hold, abandon] (held item, pending, reaches
    # the dead-end control state `closed` via the unguarded exit).
    ce = protocol_gen.temporal_counterexample(pm, o, K)
    trace = [step[0] for step in ce["trace"]] if ce else None
    assert trace == ["hold", "abandon"], f"unexpected strand witness: {trace}"

    # And the real adjudication path agrees: NOT a Certificate.
    v = kernel.check(
        {"kind": "protocol-validator", "files": protocol_gen.emit_validator(pm)},
        {"type": "protocol-cert", "spec_text": pm.source})
    assert not isinstance(v, Certificate), \
        "gamed strander must NOT certify via kernel.check"
    # the temporal channel is the one that fails (safety/conformance still pass)
    failing = [ch["backend"] for ch in v.channels if ch["result"] != "pass"]
    assert any("temporal" in b for b in failing), \
        f"a temporal channel must be the refuting one; failing={failing}"


def test_safe_eventually_service_still_certifies():
    """(b) the obligation-blocked-terminal `holds` service certifies (unsat)."""
    pm = _protocol_of(dt.HOLDS)
    o = pm.obligations[0]
    K = protocol_gen.temporal_bound(pm, pm.acyclic_bound()[0])

    z, c = _dual_verdict(pm, o, K)
    assert z == "pass" and c == "pass", \
        f"safe service must CERTIFY on both solvers, got z3={z} cvc5={c}"
    assert protocol_gen.temporal_counterexample(pm, o, K) is None, \
        "safe service must have no strand witness"

    v = kernel.check(
        {"kind": "protocol-validator", "files": protocol_gen.emit_validator(pm)},
        {"type": "protocol-cert", "spec_text": pm.source})
    assert isinstance(v, Certificate), "safe `holds` service must certify"


def test_within_missed_deadline_is_not_pending():
    """(c) PF2: a `within` monitor's missed-deadline state -> pending()==False."""
    ns: dict = {}
    r = monitor_gen.build_monitor("within", {"action": "ship", "steps": 2},
                                  ["pay", "ship", "close"])
    exec(compile(r["monitor.py"], "<emitted>", "exec"), ns)
    step, accepting, pending = ns["step"], ns["accepting"], ns["pending"]

    st = ns["INITIAL"]
    for sym in ("close", "close"):      # two non-ship steps exhaust the deadline
        st = step(st, sym)
    assert accepting(st) is False, "missed deadline must be non-accepting"
    assert pending(st) is False, \
        "PF2: a missed `within` deadline is permanently DECIDED, so NOT pending"

    # ... and it stays decided (a further `ship` cannot revive the obligation).
    st2 = step(st, "ship")
    assert accepting(st2) is False and pending(st2) is False, \
        "late ship cannot revive a lapsed deadline"

    # sanity: BEFORE the deadline lapses the obligation IS still open (pending).
    assert pending(step(ns["INITIAL"], "pay")) is True, \
        "one step in, ship still possible -> still pending"


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_"):
            _fn()
            print("PASS", _name)
    print("temporal teeth hold "
          "(TF1 product dead-end refutes the gamed strander; safe certifies; "
          "PF2 missed-deadline not pending)")

"""W6.2 teeth (a) -- per-pass certification of the service compiler passes.

Each byte-affecting pass is checked by its DESIGNATED EXISTING kernel contract
(tool-differential / constraint-cert / protocol-cert / monitor-cert /
service-conformance -- all Dafny-free).  Asserts:

  (a) every contract-bearing pass certifies for a clean service, and pass 5 is a
      GENUINE no-op (certified None, no monitor subjects) when there are no
      obligations but a real monitor-cert when there are;
  (b) a defect planted in ONE pass's bundle output makes THAT pass's certificate
      FAIL while every other contract-bearing pass still certifies, and the
      failing contract is the one OWNING the mutated bundle key (pass-level
      attribution).
"""
import json
import os
import pathlib
import tempfile

# Fresh, isolated registry/artifacts dirs BEFORE anything imports the kernel
# (service_passes imports kernel lazily inside certify_passes).  Dafny-free path.
os.environ.setdefault("CGB_KSC_CLASSPATH", "/opt/ksc/lib/*")
for _var in ("CGB_DB", "CGB_ARTIFACTS"):
    if not os.environ.get(_var):
        os.environ[_var] = tempfile.mkdtemp(prefix="pass_certs_")

import pytest

from generators import service_model, service_passes

SPEC_DIR = pathlib.Path(__file__).resolve().parent.parent / "specs" / "services"
ORDERS = (SPEC_DIR / "orders.json").read_text()

# A temporal service so pass 5's monitor-cert fires (specs/services/*.json
# declare no obligations).
HOLDS = json.dumps({
    "name": "holds",
    "context": {"held": {"init_min": 0, "init_max": 0}},
    "states": ["shop", "active", "closed"],
    "initial": "shop",
    "tools": [
        {"name": "hold", "from": "shop", "to": "active",
         "input_schema": {"type": "object", "properties": {}, "required": [],
                          "additionalProperties": False},
         "update": {"held": {"op": "+", "left": {"var": "held"}, "right": 1}}},
        {"name": "settle", "from": "active", "to": "active",
         "input_schema": {"type": "object", "properties": {}, "required": [],
                          "additionalProperties": False},
         "guard": {"op": ">=", "left": "held", "right": 1},
         "update": {"held": {"op": "-", "left": {"var": "held"}, "right": 1}}},
        {"name": "close", "from": "active", "to": "closed", "terminal": True,
         "input_schema": {"type": "object", "properties": {}, "required": [],
                          "additionalProperties": False}},
    ],
    "safety": {"when": "*", "invariant": {"op": ">=", "left": "held",
                                          "right": 0}},
    "obligations": [{"id": "o1", "kind": "eventually", "action": "settle"}],
})


def _model(spec):
    return service_model.parse_service_spec(spec)


def _by_pass(records):
    return {r["pass"]: r for r in records}


def _contracted(records):
    """Contract-bearing passes with a real verdict (not a no-op None)."""
    return [r for r in records if r["contract"] and r["certified"] is not None]


# --------------------------------------------------------------------------- (a)
def test_orders_every_contract_pass_certifies():
    recs = service_passes.certify_passes(_model(ORDERS))
    contracted = _contracted(recs)
    # pass 2 (tool-differential), 3 (constraint-cert), 4 (protocol-cert),
    # 7 (service-conformance) all have real verdicts and all certify.
    kinds = {r["contract"] for r in contracted}
    assert kinds == {"tool-differential", "constraint-cert", "protocol-cert",
                     "service-conformance"}
    assert all(r["certified"] for r in contracted), \
        [(r["pass"], r["certified"]) for r in contracted]


def test_holds_monitor_cert_certifies():
    recs = service_passes.certify_passes(_model(HOLDS))
    by = _by_pass(recs)
    mon = by["obligation_monitor"]
    assert mon["contract"] == "monitor-cert"
    assert mon["certified"] is True
    assert [s["subject"] for s in mon["subjects"]] == ["monitor:o1"]
    # and every contract-bearing pass certifies
    assert all(r["certified"] for r in _contracted(recs))


def test_pass5_genuine_noop_without_obligations():
    """orders declares no obligations: pass 5 is a genuine no-op (certified
    None, zero monitor subjects) -- it never builds a monitor."""
    recs = service_passes.certify_passes(_model(ORDERS))
    mon = _by_pass(recs)["obligation_monitor"]
    assert mon["contract"] == "monitor-cert"
    assert mon["certified"] is None
    assert mon["subjects"] == []


def test_structural_passes_reported_without_contract():
    recs = service_passes.certify_passes(_model(ORDERS))
    by = _by_pass(recs)
    for p in ("parse_normalize", "adversary_golden"):
        assert by[p]["contract"] is None
        assert by[p]["certified"] is True          # structural self-check passes


# --------------------------------------------------------------------------- (b)
def _drop_transition(bundle):
    bundle["transitions"] = bundle["transitions"][1:]   # drop `login`
    return bundle


def _weaken_constraint(bundle):
    bundle["constraints_table"]["pay"] = [              # amount>=0  ->  amount>=-5
        {"op": ">=", "left": "amount", "right": -5}]
    return bundle


def test_dropped_transition_fails_only_protocol_cert():
    recs = service_passes.certify_passes(_model(ORDERS), mutate=_drop_transition)
    failed = [r for r in _contracted(recs) if not r["certified"]]
    # exactly the protocol_stack pass fails; its contract owns `transitions`.
    assert [r["pass"] for r in failed] == ["protocol_stack"]
    assert failed[0]["contract"] == "protocol-cert"
    # every other contract-bearing pass still certifies (attribution).
    assert all(r["certified"] for r in _contracted(recs)
               if r["pass"] != "protocol_stack")


def test_weakened_constraint_fails_only_constraint_cert():
    recs = service_passes.certify_passes(_model(ORDERS), mutate=_weaken_constraint)
    failed = [r for r in _contracted(recs) if not r["certified"]]
    assert [r["pass"] for r in failed] == ["constraint"]
    assert failed[0]["contract"] == "constraint-cert"
    assert all(r["certified"] for r in _contracted(recs)
               if r["pass"] != "constraint")


def test_defect_attribution_is_disjoint():
    """The two defects fail DISJOINT passes -- attribution is per-pass, not a
    blanket end-to-end failure."""
    p = service_passes.certify_passes(_model(ORDERS), mutate=_drop_transition)
    c = service_passes.certify_passes(_model(ORDERS), mutate=_weaken_constraint)
    pf = {r["pass"] for r in _contracted(p) if not r["certified"]}
    cf = {r["pass"] for r in _contracted(c) if not r["certified"]}
    assert pf == {"protocol_stack"}
    assert cf == {"constraint"}
    assert pf.isdisjoint(cf)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

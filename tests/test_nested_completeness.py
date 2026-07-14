"""Guard for the P4a-review NF1 fix: `complete-to-depth(D)` must NOT be claimed
when a context-mutating action lies on a call/return cycle (such a cycle can
drift a context variable unboundedly at bounded stack depth, so BMC at the
structural K would issue a FALSE "complete").  Pure-function test over
ProtocolModel.acyclic_bound -- no kernel/sandbox needed.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import protocol_model as pm


def _bound(spec):
    return pm.parse_protocol_spec(json.dumps(spec)).acyclic_bound()


DRIFT = {  # begin(call a->a) / step(a->b, escrow-=1) / ret(return b) -- a cycle
    "name": "drift", "states": ["a", "b", "done"], "initial": "a",
    "context": {"escrow": {"init_min": 0, "init_max": 0}},
    "actions": [
        {"name": "call", "from": "a", "to": "a", "kind": "call", "return_to": "a"},
        {"name": "step", "from": "a", "to": "b", "kind": "internal",
         "update": {"escrow": {"op": "-", "left": {"var": "escrow"}, "right": 1}}},
        {"name": "ret", "from": "b", "to": "a", "kind": "return"},
        {"name": "fin", "from": "a", "to": "done", "kind": "internal"}],
    "safety": {"when": "*", "invariant": {"op": ">=", "left": "escrow", "right": -8}}}

CFLOW = {  # same shape but NO context mutation -> genuinely complete
    "name": "cflow", "states": ["a", "b", "done"], "initial": "a",
    "context": {"x": {"init_min": 0, "init_max": 0}},
    "actions": [
        {"name": "call", "from": "a", "to": "a", "kind": "call", "return_to": "a"},
        {"name": "work", "from": "a", "to": "b", "kind": "internal"},
        {"name": "ret", "from": "b", "to": "a", "kind": "return"},
        {"name": "fin", "from": "a", "to": "done", "kind": "internal"}],
    "safety": {"when": "*", "invariant": {"op": ">=", "left": "x", "right": 0}}}


def test_context_drift_on_cycle_is_not_complete():
    K, complete, D = _bound(DRIFT)
    assert complete is False, \
        "FALSE-CERT: a context-mutating call/return cycle claims complete-to-depth(D)"
    assert D == pm.STACK_DEPTH


def test_control_flow_only_nesting_stays_complete():
    K, complete, D = _bound(CFLOW)
    assert complete is True, \
        "over-conservative: context-free nesting should stay complete-to-depth(D)"
    assert D == pm.STACK_DEPTH


def test_non_nested_unchanged():
    nn = {"name": "nn", "states": ["a", "b"], "initial": "a",
          "context": {"x": {"init_min": 0, "init_max": 0}},
          "actions": [{"name": "go", "from": "a", "to": "b",
                       "update": {"x": {"op": "+", "left": {"var": "x"}, "right": 1}}}],
          "safety": {"when": "*", "invariant": {"op": ">=", "left": "x", "right": 0}}}
    K, complete, D = _bound(nn)
    assert complete is True and D == 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
    print("nested-completeness guard holds: context-drift -> bounded-K (no false complete)")

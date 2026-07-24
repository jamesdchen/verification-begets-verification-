#!/usr/bin/env python3
"""P4a nested sessions (visible stack) -- call/return sub-transactions certified
by bounded-stack BMC and conformance-checked against an INDEPENDENTLY-stacked
reference.

The `nested_txn` service opens sub-transactions with a `call` tool (`begin`),
does guarded work inside them (`charge`), and closes them with a `return` tool
(`settle`) whose target is STACK-DETERMINED (the popped continuation, never a
static `to`).  A top-level `close` ends the session.  Safety (`escrow >= 0`) is
proved by bounded model checking over a visible stack -- per step a pointer
`sp[i]` plus fixed slots `stk[d][i]` for d < D, a symbolic-index case split, pure
QF_LIA (no arrays).  Exploration is COMPLETE only for stack depth <= D, so the
soundness condition is that the dispatcher AND the reference enforce the same
bound; both do, and the certificate names (K, D).

Part A -- certify the whole nested service: four tool schemas, the sequencing
safety (dual BMC over the bounded stack; the emitted session validator vs. an
independently-stacked reference simulator), and the composition (dispatcher vs.
an independent reference service + a liveness witness whose golden run round-
trips a sub-transaction and empties the stack).  The protocol certificate names
(K, D).  This service is tier `bounded-K` -- HONESTLY, not complete-to-depth(D):
`charge` mutates `escrow` on the begin/charge/settle call/return cycle, so the
context could in principle drift unboundedly at bounded stack depth, and the
depth-aware bound refuses to claim completeness when a context-mutating action
lies on such a cycle (a genuinely context-free nested protocol certifies
`complete-to-depth(D)`; a drifting one is honestly bounded-K -- safe within K,
completeness not claimed).

Part B1 -- a DANGLING transaction is refused.  `close` (a terminal) is refused
while a sub-transaction is still open (the stack is non-empty): you cannot end
the outer session with an unbalanced call.  The independent reference refuses the
identical trace.

Part B2 -- an OVER-POP is caught.  A `settle` (return) once the stack is empty --
a return that matches no open call -- is refused at the sequencing layer, after a
fully legal nested prefix.  Again the independent reference agrees.

REQUIRES_LLM = False -- the meta-spec and both implementations are fixed; nothing
here calls an LLM.
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib
import json
import pathlib
import sys
import tempfile

import kernel
from kernel.certs import Certificate
from generators import service_model, service_gen
from run import service as svc

REQUIRES_LLM = False

SPEC = pathlib.Path("specs/services/nested_txn.json").read_text()
INIT = {"escrow": 0}


def _load():
    """Materialize the emitted dispatcher (needs its per-tool validator modules)
    and the INDEPENDENT reference service; return (Service, run_reference)."""
    m = service_model.parse_service_spec(SPEC)
    d = tempfile.mkdtemp()
    for name, data in service_gen.emit_service(m).items():
        (pathlib.Path(d) / name).write_bytes(data)
    if d not in sys.path:
        sys.path.insert(0, d)
    Service = importlib.import_module("service").Service
    ns: dict = {}
    exec(service_gen.ref_service_source(m), ns)
    return Service, ns["run_reference"]


def _dispatch(Service, seq):
    s = Service(dict(INIT))
    return [s.call(t, a) for t, a in seq]


def part_a():
    print("== Part A: certify the whole nested `nested_txn` service ==")
    r = svc.certify_service(SPEC, write_output=True)
    for L in r.layers:
        print(f"  {'OK' if L['certified'] else 'XX'} {L['layer']:<30} "
              f"{L['channels']}")
    proto = next((L for L in r.layers if L["layer"].startswith("protocol")), None)
    if proto and proto["certified"]:
        c = proto["cert"]
        print(f"  protocol tier: {c['tier']}   claims: {c['claims']}")
    print(f"  service certified: {r.ok}  ({len(r.layers)} layers) -> {r.out_dir}")
    return r.ok


def part_b1(Service, run_reference):
    print("\n== Part B1: a DANGLING transaction is refused (close while a "
          "sub-txn is open) ==")
    seq = [["begin", {}], ["close", {}]]      # open a sub-txn, then try to close
    got = _dispatch(Service, seq)
    oks = [r["ok"] for r in got]
    ref = run_reference(dict(INIT), seq)
    refused = got[-1]
    dangling_refused = (oks == [True, False]
                        and refused["layer"] == "sequencing"
                        and oks == ref)
    print(f"  trace: {[s[0] for s in seq]}")
    print(f"  dispatcher: {oks}   refused layer: {refused['layer']!r}")
    print(f"  independent reference agrees: {oks == ref}")
    print(f"  dangling transaction refused: {dangling_refused}")
    return dangling_refused


def part_b2(Service, run_reference):
    print("\n== Part B2: an OVER-POP is caught (a return with an empty stack) ==")
    # a fully legal nested round-trip, then one settle too many -> over-pop
    seq = [["begin", {}], ["charge", {"amt": 1}], ["settle", {}],
           ["charge", {"amt": 1}], ["settle", {}]]
    got = _dispatch(Service, seq)
    oks = [r["ok"] for r in got]
    ref = run_reference(dict(INIT), seq)
    refused = got[-1]
    overpop_caught = (oks == [True, True, True, True, False]
                      and refused["layer"] == "sequencing"
                      and oks == ref)
    print(f"  trace: {[s[0] for s in seq]}")
    print(f"  dispatcher: {oks}   refused layer: {refused['layer']!r}")
    print(f"  independent reference agrees: {oks == ref}")
    # bonus: the soundness bound itself -- a call at depth D is refused too
    depth = _dispatch(Service, [["begin", {}]] * 5)
    depth_refused = [r["ok"] for r in depth] == [True, True, True, True, False]
    print(f"  (depth bound: 5th begin at depth D refused: {depth_refused})")
    print(f"  over-pop caught: {overpop_caught}")
    return overpop_caught and depth_refused


if __name__ == "__main__":
    a = part_a()
    Service, run_reference = _load()
    b1 = part_b1(Service, run_reference)
    b2 = part_b2(Service, run_reference)
    print("\nsummary:", json.dumps({
        "part_a_nested_certified": a,
        "part_b1_dangling_txn_refused": b1,
        "part_b2_overpop_caught": b2}))
    sys.exit(0 if all([a, b1, b2]) else 1)

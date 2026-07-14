#!/usr/bin/env python3
"""W6 -- the service monolith is now a pipeline of certified compiler passes.

This LLM-free demo shows the BYTE-PRESERVING core of W6: `emit_service` is a
linear composition of seven pure passes over a canonical-JSON bundle, and the
pass boundaries are REAL -- a defect planted in one pass is attributable to
that pass by comparing its bundle output to the reference pass, and a new
fragment is added by INSERTING a pass, never by editing the monolith.

Tooth (a) -- pass-boundary attribution: a protocol_stack pass that drops one
transition produces a bundle whose `transitions` key differs from the
reference pass's output at exactly that pass, and the emitted service.py
changes -- so the defect is localized to pass 4, not just to the end-to-end
differential.

Tooth (d) -- fragment-insertion payoff: a toy pass inserted between passes 4
and 5 that adds a bundle key but touches nothing else leaves every downstream
pass's output (and the final emitted bytes) IDENTICAL -- a fragment is a pass
insertion, never a monolith edit.

DEFERRED (byte-changing / cert-dependent, later serialized window):
  Tooth (b) -- pass-order mutation refused by the assemble pass's ORDER
    CONTRACT certificate: the order_contract is a data record here; its
    certificate obligation is not yet wired.
  Tooth (c) full form -- the per-pass conditional-emission CERTIFICATE: the
    parity itself is demonstrated (empty monitor keys, no flloat) and asserted
    in tests/test_passes.py, but the certificate is deferred.
"""
from __future__ import annotations

import json
import pathlib
import sys

from generators import service_model, service_gen, service_passes

REQUIRES_LLM = False

SPEC = pathlib.Path("specs/services/nested_txn.json").read_text()


def tooth_a_pass_boundary_attribution() -> bool:
    print("== Tooth (a): a planted defect is attributable to ONE pass ==")
    m = service_model.parse_service_spec(SPEC)

    # reference: the real protocol_stack pass output.
    ref = service_passes.run_passes(m, service_passes.EMIT_PASSES)

    def defective_protocol_stack(bundle):
        """protocol_stack with a dropped transition -- the classic pass 4 bug."""
        bundle = service_passes.protocol_stack(bundle)
        bundle["transitions"] = bundle["transitions"][1:]   # drop first transition
        return bundle

    passes = list(service_passes.EMIT_PASSES)
    passes[3] = defective_protocol_stack          # swap in the defective pass 4
    bad = service_passes.run_passes(m, passes)

    # ATTRIBUTION: compare each pass's bundle key to the reference.  The defect
    # shows up at pass 4's key (`transitions`) and nowhere upstream.
    upstream_same = (bad["init_ctx"] == ref["init_ctx"]
                     and bad["validators"] == ref["validators"]
                     and bad["constraints_table"] == ref["constraints_table"])
    pass4_differs = bad["transitions"] != ref["transitions"]
    emitted_differs = bad["files"]["service.py"] != ref["files"]["service.py"]

    print(f"  upstream passes (1-3) outputs unchanged: {upstream_same}")
    print(f"  pass 4 (protocol_stack) `transitions` differs: {pass4_differs}")
    print(f"  emitted service.py changed as a result:   {emitted_differs}")
    caught = upstream_same and pass4_differs and emitted_differs
    print(f"  defect localized to pass 4: {caught}")
    return caught


def tooth_d_fragment_insertion_payoff() -> bool:
    print("\n== Tooth (d): a fragment is added by INSERTING a pass ==")
    m = service_model.parse_service_spec(SPEC)
    ref = service_passes.run_passes(m, service_passes.EMIT_PASSES)

    inserted = {"ran": False}

    def toy_pass(bundle):
        """A toy pass inserted between protocol_stack (4) and
        obligation_monitor (5): adds its own bundle key, touches nothing else."""
        inserted["ran"] = True
        bundle["toy_fragment"] = {"note": "inserted between passes 4 and 5"}
        return bundle

    passes = list(service_passes.EMIT_PASSES)
    passes.insert(4, toy_pass)                    # between protocol_stack & monitor
    out = service_passes.run_passes(m, passes)

    # No other pass's output changed; the emitted bytes are IDENTICAL.
    downstream_same = (out["monitor"] == ref["monitor"]
                       and out["files"] == ref["files"])
    added_only = "toy_fragment" in out and "toy_fragment" not in ref
    print(f"  toy pass ran:                              {inserted['ran']}")
    print(f"  it added a new bundle key (toy_fragment):  {added_only}")
    print(f"  all other passes' outputs + bytes IDENTICAL: {downstream_same}")
    payoff = inserted["ran"] and downstream_same and added_only
    print(f"  fragment-insertion payoff (no monolith edit): {payoff}")
    return payoff


if __name__ == "__main__":
    a = tooth_a_pass_boundary_attribution()
    d = tooth_d_fragment_insertion_payoff()
    print("\n  (deferred: tooth (b) order-contract cert; tooth (c) per-pass"
          " conditional-emission certificate -- need byte changes / cert wiring)")
    print("\nsummary:", json.dumps({
        "tooth_a_pass_boundary_attribution": a,
        "tooth_d_fragment_insertion_payoff": d}))
    sys.exit(0 if all([a, d]) else 1)

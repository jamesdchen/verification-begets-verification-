#!/usr/bin/env python3
"""P5.1 tier-classification -- classify a protocol's CONTROL SKELETON (control
states + action-labelled transitions, IGNORING guards / integer context / stack)
as star-free or not, via the DUAL, genuinely-independent channels of
generators.monoid: channel 1 = transition-monoid aperiodicity (m^k == m^(k+1)),
channel 2 = a counter-free r-cycle search on the minimal DFA (a different
algorithm for the same property, the z3-vs-cvc5 independence grade).  Both run
in-process (pure / z3-free); the kernel issues a certificate only when they
AGREE, and the tier-tag rides on the certificate's machine-readable `claims`.

Part A -- the P5.1 done-when: certify `specs/protocols/order.json`, LOAD the
issued certificate (persist to a store, rehydrate), and assert a tier-tag claim
`("control_skeleton", "star-free")` is present on the loaded certificate.  order
is a linear DAG, so its legal-action-sequence language is star-free; both
channels concur.

Part B1 -- teeth: a NOT-star-free control skeleton certifies honestly.  A toggle
action `x` (even<->odd) plus a `ping` legal only in `even` makes the two phases
distinguishable, so the 2-cycle survives minimization and is a genuine counter.
Both independent channels find it; the certificate claims `not-star-free`.

Part B2 -- honesty (what it declines to classify): a NESTED / pushdown protocol
(a call/return stack) has no plain DFA control skeleton, so the classifier emits
an honest tier-unclassified NON-certificate -- never a crash, never a false
star-free claim.  The star-free method is for REGULAR control only.

REQUIRES_LLM = False -- every spec here is fixed; nothing calls an LLM.
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pathlib
import sys

import kernel
from kernel.certs import Certificate

REQUIRES_LLM = False

ORDER = pathlib.Path("specs/protocols/order.json").read_text()

# A genuinely NOT-star-free control skeleton: the toggle 'x' alternates even<->odd
# while 'ping' (legal only in even) distinguishes the phases, so the 2-cycle is
# observable in the legal-sequence language and survives minimization.
PHASED = json.dumps({
    "name": "phased", "states": ["even", "odd"], "initial": "even",
    "actions": [{"name": "x", "from": "even", "to": "odd"},
                {"name": "x", "from": "odd", "to": "even"},
                {"name": "ping", "from": "even", "to": "even"}],
    "safety": {"when": "*", "invariant": {"op": ">=", "left": 0, "right": 0}}})

# A nested (pushdown) protocol: call/return -> no plain DFA control skeleton.
NESTED = json.dumps({
    "name": "nested", "states": ["top", "inside", "done"], "initial": "top",
    "actions": [{"name": "begin", "kind": "call", "from": "top", "to": "inside",
                 "return_to": "done"},
                {"name": "end", "kind": "return", "from": "inside", "to": "inside"}],
    "safety": {"when": "*", "invariant": {"op": ">=", "left": 0, "right": 0}}})

ART = {"kind": "protocol", "files": {}}


def _classify(spec_text, **kw):
    return kernel.check(ART, {"type": "tier-classification", "spec_text": spec_text},
                        **kw)


def part_a():
    print("== Part A: certify order's control skeleton, LOAD the cert, assert "
          "tier-tag claim ==")
    # A JSON-serializing store: prove the tier-tag survives a persist + reload.
    store: dict = {}
    con = {"type": "tier-classification", "spec_text": ORDER}
    issued = kernel.check(ART, con,
                          cache_put=lambda k, v: store.__setitem__(k, json.dumps(v.to_dict())))
    ok = isinstance(issued, Certificate)
    loaded = kernel.check(  # LOAD from the store (rehydrate from JSON)
        ART, con, cache_get=lambda k: (Certificate.from_dict(json.loads(store[k]))
                                       if k in store else None))
    tag = ("control_skeleton", "star-free")
    claim_present = isinstance(loaded, Certificate) and tag in loaded.claims
    print(f"  {'OK' if ok else 'XX'} tier-classification    "
          f"channels={[(c['backend'], c['result']) for c in (issued.channels if ok else [])]}")
    if isinstance(loaded, Certificate):
        print(f"  loaded cert tier: {loaded.tier}")
        print(f"  loaded cert claims: {loaded.claims}")
        print(f"  tier-tag claim {tag} present: {claim_present}")
    return ok and claim_present


def part_b1():
    print("\n== Part B1: a NOT-star-free control skeleton certifies honestly ==")
    v = _classify(PHASED)
    ok = isinstance(v, Certificate)
    tag = ("control_skeleton", "not-star-free")
    claim_present = ok and tag in v.claims
    ch = [(c["backend"], c["result"]) for c in (v.channels if ok else [])]
    print(f"  {'OK' if ok else 'XX'} not-star-free cert     channels={ch}")
    if ok:
        print(f"  tier: {v.tier}   claims: {v.claims}")
    # both INDEPENDENT channels must have found the counter (agreement, not one)
    both_agree = ok and len({c["result"] for c in v.channels}) == 1
    print(f"  both independent channels agree not-star-free: {both_agree}")
    return claim_present and both_agree


def part_b2():
    print("\n== Part B2: a NESTED/pushdown protocol -> honest tier-unclassified "
          "(no false star-free claim) ==")
    events: list = []
    v = _classify(NESTED, event_sink=lambda k, p: events.append(k))
    non_cert = not isinstance(v, Certificate)
    d = v.to_dict() if non_cert else {}
    unclassified = non_cert and "tier-unclassified" in json.dumps(d["channels"])
    # honesty: NO certificate exists, so no star-free claim was ever made, and no
    # disagreement was logged (this is out-of-scope, not a checker conflict).
    no_disagreement = "dual-checker-disagreement" not in events
    print(f"  issued a certificate: {not non_cert}  (want False)")
    if non_cert:
        print(f"  verdict={d['verdict']}  channels="
              f"{[(c['backend'], c['result']) for c in d['channels']]}")
    print(f"  honest tier-unclassified, no false star-free claim: {unclassified}")
    return non_cert and unclassified and no_disagreement


if __name__ == "__main__":
    a = part_a()
    b1 = part_b1()
    b2 = part_b2()
    print("\nsummary:", json.dumps({
        "part_a_order_star_free_claim_present": a,
        "part_b1_not_star_free_certified": b1,
        "part_b2_nested_tier_unclassified_honest": b2}))
    sys.exit(0 if all([a, b1, b2]) else 1)

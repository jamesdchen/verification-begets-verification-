#!/usr/bin/env python3
"""Phase 2 -- the CAGE: arbitrary incumbent code behind a certified boundary.

A third-party (never LLM-authored) incumbent runs inside an OS sandbox with a
certified dispatcher in front (ingress: sequencing / schema / constraint / guard)
and emitted output-contracts behind (egress: output_schema).  The certificate
proves the CAGE (containment + transparency) and machine-readably DECLINES to
praise the cargo (tier "monitored", non-empty non_claims).

Part A -- HONEST incumbent, TRANSPARENT + CERTIFIED.  An honest incumbent that
does its job and returns well-formed output runs through the cage exactly as it
runs bare: the transparency channel confirms caged results are byte-identical to
the bare incumbent (common.canonical_json).  The cage certifies end to end --
CONTAINMENT (on solver-generated violating inputs the cage rejects the exact call
the bare incumbent would act on) AND TRANSPARENCY -- yielding a `cage-conformance`
certificate at tier "monitored".  A script assertion reloads that certificate and
checks tier=="monitored" and non_claims != ().

Part B -- MALICIOUS incumbent, CONTAINED at the exact layer.  A malicious
incumbent (i) OVERSELLS: it would honour a reservation exceeding stock, but the
dispatcher's guard refuses it at INGRESS before it is ever called; (ii) emits
MALFORMED OUTPUT on a perfectly legal call, refused at EGRESS by the output
contract.  In both cases the BARE incumbent acts and the cage stops it -- at the
guard layer and the egress layer respectively.  (Failure classes: a policy the
incumbent does not enforce; a result contract the incumbent violates.)
"""
from __future__ import annotations

import json
import pathlib
import sys

from kernel.certs import Certificate
from generators import service_model
from run import guarded

REQUIRES_LLM = False


# --- the service: a tiny store with a stock guard and egress output contracts
def _sch(props=None, req=None):
    return {"type": "object", "properties": props or {},
            "required": req or [], "additionalProperties": False}


STORE = {
    "name": "store",
    "context": {"stock": {"init_min": 1, "init_max": 3}},
    "states": ["shop", "held", "done"],
    "initial": "shop",
    "tools": [
        {"name": "reserve", "from": "shop", "to": "held", "arg": "qty",
         "input_schema": _sch({"qty": {"type": "integer"}}, ["qty"]),
         "guard": {"op": "<=", "left": "qty", "right": "stock"},
         "constraints": {"name": "reserve_c",
                         "fields": {"qty": {"type": "integer"}},
                         "constraints": [{"op": ">=", "left": "qty", "right": 1}],
                         "invariant": {"op": ">=", "left": "qty", "right": 1}},
         "update": {"stock": {"op": "-", "left": {"var": "stock"},
                              "right": {"var": "qty"}}},
         # EGRESS contract on the reservation result
         "output_schema": _sch({"ticket": {"type": "integer"},
                                "left": {"type": "integer"}}, ["ticket", "left"])},
        {"name": "checkout", "from": "held", "to": "done", "terminal": True,
         "input_schema": _sch(),
         "output_schema": _sch({"status": {"type": "string"}}, ["status"])},
    ],
    "safety": {"when": "*", "invariant": {"op": ">=", "left": "stock", "right": 0}},
}

# An HONEST incumbent: does its job, returns well-formed output.  It does NOT
# re-enforce the cage's stock policy (that is the cage's job) -- so bare it would
# happily honour an over-reservation, which is exactly what the cage contains.
HONEST_SRC = '''
class Incumbent:
    def __init__(self):
        self.n = 0                       # all state in instance attrs; no globals
    def call(self, tool, args):
        args = args or {}
        if tool == "reserve":
            self.n += 1
            qty = args.get("qty", 0)
            left = 100 - qty if isinstance(qty, int) else 0
            return {"ticket": self.n, "left": left}
        if tool == "checkout":
            return {"status": "shipped"}
        return "__error__"
'''

# A MALICIOUS incumbent: oversells (acts on any reservation) AND emits malformed
# output (ticket is not an int and `left` is missing; status is not a string).
MALICIOUS_SRC = '''
class Incumbent:
    def __init__(self):
        self.n = 0
    def call(self, tool, args):
        args = args or {}
        if tool == "reserve":
            self.n += 1
            return {"ticket": "OVERSOLD"}     # malformed: ticket not int, left missing
        if tool == "checkout":
            return {"status": 0}              # malformed: status not a string
        return "__error__"
'''

CERT_PATH = pathlib.Path("results/cage_certificate.json")


def part_a():
    print("== Part A: honest incumbent -- transparent + the cage certifies ==")
    m = service_model.parse_service_spec(json.dumps(STORE))
    cage = guarded.Cage(m, HONEST_SRC)

    # (1) transparency, observed directly: caged legal run == bare incumbent
    legal = guarded.legal_sessions(m)
    transparent = bool(legal)
    for s in legal:
        caged = cage.run(s["init"], s["seq"])
        bare = cage.run_bare(s["init"], s["seq"])
        for i, (t, _a) in enumerate(s["seq"]):
            import common
            ok = caged[i].get("ok") and (common.canonical_json(caged[i].get("result"))
                                         == common.canonical_json(bare[i].get("result")))
            transparent = transparent and ok
            print(f"  {'OK' if ok else 'XX'} legal step {t:<9} caged={caged[i]}  "
                  f"bare={bare[i].get('result')}")

    # (2) certify the cage (containment + transparency channels)
    v = guarded.certify_cage(cage, m)
    cert = isinstance(v, Certificate)
    for c in (v.channels if cert else v.to_dict()["channels"]):
        print(f"  {'OK' if c['result'] == 'pass' else 'XX'} channel "
              f"{c['backend']:<18} {c['result']} -- {str(c.get('detail'))[:88]}")
    tier = getattr(v, "tier", "")
    non_claims = getattr(v, "non_claims", ())
    print(f"  -> cage certified: {cert}  tier={tier!r}  "
          f"#claims={len(getattr(v, 'claims', ()))}  #non_claims={len(non_claims)}")

    # (3) the script assertion: reload the emitted certificate off disk and check
    #     tier=="monitored" and non_claims != ()
    ok_cert = False
    if cert:
        CERT_PATH.parent.mkdir(parents=True, exist_ok=True)
        CERT_PATH.write_text(json.dumps(v.to_dict(), indent=2))
        loaded = Certificate.from_dict(json.loads(CERT_PATH.read_text()))
        assert loaded.tier == "monitored", ("tier", loaded.tier)
        assert loaded.non_claims != (), "non_claims must be non-empty (cage does not praise the cargo)"
        print(f"  -> reloaded cert: tier=={loaded.tier!r}, non_claims (first) = "
              f"{loaded.non_claims[0][0]!r}: {loaded.non_claims[0][1][:60]!r}...")
        ok_cert = True

    result = bool(transparent and cert and ok_cert)
    print(f"  => part A (honest transparent + certified): {result}")
    return result


def part_b():
    print("\n== Part B: malicious incumbent -- contained at the exact layer ==")
    m = service_model.parse_service_spec(json.dumps(STORE))
    cage = guarded.Cage(m, MALICIOUS_SRC)
    init = {"stock": 1}

    # (i) OVERSELL -> refused at INGRESS (guard); the incumbent is never called
    oversell = [["reserve", {"qty": 2}]]        # qty(2) > stock(1)
    caged_o = cage.run(init, oversell)
    bare_o = cage.run_bare(init, oversell)
    oversell_contained = (not caged_o[-1]["ok"]
                          and caged_o[-1].get("layer") == "guard"
                          and bare_o[-1].get("acted"))
    print(f"  {'OK' if oversell_contained else 'XX'} oversell reserve(qty=2, stock=1): "
          f"caged={caged_o[-1]}  bare_acted={bare_o[-1].get('acted')}")

    # (ii) MALFORMED OUTPUT on a LEGAL call -> refused at EGRESS
    legal = [["reserve", {"qty": 1}]]           # qty(1) <= stock(1): ingress accepts
    caged_m = cage.run(init, legal)
    bare_m = cage.run_bare(init, legal)
    malformed_contained = (not caged_m[-1]["ok"]
                           and caged_m[-1].get("layer") == "egress"
                           and bare_m[-1].get("acted"))
    print(f"  {'OK' if malformed_contained else 'XX'} malformed output reserve(qty=1): "
          f"caged={caged_m[-1]}  bare_result={bare_m[-1].get('result')}")

    result = bool(oversell_contained and malformed_contained)
    print(f"  => part B (malicious contained at guard + egress): {result}")
    return result


if __name__ == "__main__":
    a = part_a()
    b = part_b()
    summary = {"part_a_honest_incumbent_transparent": a,
               "part_b_malicious_incumbent_contained": b}
    print("\nsummary:", json.dumps(summary))
    sys.exit(0 if all(summary.values()) else 1)

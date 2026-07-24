#!/usr/bin/env python3
"""S4 speculative pre-gate + divergence ledger -- teeth, LLM-free, hand-planted.

The speculative executor fans candidate Readings out against CHEAP pre-gates and
RANKS them; it never certifies (Z1).  This demo plants readings by hand and
shows, without any LLM:

  * a GOOD grounded reading clears the three rejecting pre-gates and reaches the
    rank-only entailed-replay stage;
  * the INVERTED-verb-effect plant (selling INCREASES stock) SLIPS PAST every
    pre-gate -- the ⚠H42 check: demands_smt ignores effects and compile is
    structural, so only the full pipeline's protocol BMC can catch it.  That is
    exactly why the caught plant is a contradictory demand set instead;
  * a CONTRADICTORY demand set (count<=8 AND count>=10) is caught at the
    'consistency' pre-gate;
  * an UNGROUNDED quote is caught at the 'reading-gate' pre-gate;
  * a divergence event is logged for the loser (Z-D payload);
  * Z1: NO composed certificate (and no persisted reading) exists for the loser.

Exit 0 on success, non-zero on any failure.
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import sys
import tempfile

from buildloop import speculate
from library import Registry

REQUIRES_LLM = False

REQUEST = ("I run a small venue. Help me not oversell tickets. "
           "Nobody may take more than 8 tickets in one order.")

READING = {
    "service": "tickets",
    "statements": [
        {"id": "s1", "force": "presupposition", "quote": "tickets",
         "lf": {"kind": "quantity", "name": "tickets_left",
                "min": 0, "max": 100}},
        {"id": "s2", "force": "presupposition", "quote": "oversell",
         "lf": {"kind": "action", "name": "sell", "arg": "count"}},
        {"id": "s3", "force": "presupposition", "quote": "oversell",
         "lf": {"kind": "effect", "action": "sell", "quantity": "tickets_left",
                "op": "dec", "amount": {"arg": "count"}}},
        {"id": "s4", "force": "demand", "quote": "not oversell tickets",
         "lf": {"kind": "always",
                "pred": {"op": ">=", "left": "tickets_left", "right": 0}}},
        {"id": "s5", "force": "demand", "quote": "not oversell tickets",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": "<=", "right": "tickets_left"}},
        {"id": "s6", "force": "demand",
         "quote": "more than 8 tickets in one order",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": "<=", "right": 8}},
        {"id": "s7", "force": "presupposition", "quote": "take",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": ">=", "right": 1}},
        {"id": "s8", "force": "choice", "quote": "",
         "lf": {"kind": "action", "name": "close_sales"}},
        {"id": "s9", "force": "choice", "quote": "",
         "lf": {"kind": "lifecycle", "states": ["open", "closed"],
                "initial": "open"}},
        {"id": "s10", "force": "choice", "quote": "",
         "lf": {"kind": "transition", "action": "sell", "from": "open",
                "to": "open"}},
        {"id": "s11", "force": "choice", "quote": "",
         "lf": {"kind": "transition", "action": "close_sales", "from": "open",
                "to": "closed"}},
    ]
}


def _clone():
    return json.loads(json.dumps(READING))


def _text(doc):
    return json.dumps(doc)


def main() -> int:
    ok = []
    print("== S4 speculative pre-gate: cheapest-first, rank-only stage 4 ==")

    # ---- the GOOD reading reaches the rank-only entailed-replay stage --------
    good = speculate.pre_gate(REQUEST, _text(READING))
    print(f"  GOOD reading         reached={good['stage_reached']:<15} "
          f"ok={good['ok']} scenarios={good['scenarios']}")
    ok.append(good["ok"] is True and good["stage_reached"] == "entailed-replay")

    # ---- ⚠H42: the inverted-effect plant SLIPS PAST the pre-gates ------------
    inv = _clone()
    inv["statements"][2]["lf"]["op"] = "inc"     # selling INCREASES stock
    res_inv = speculate.pre_gate(REQUEST, _text(inv))
    slips = (res_inv["stage_reached"] == "entailed-replay" and res_inv["ok"])
    print(f"  INVERTED-effect plant reached={res_inv['stage_reached']:<15} "
          f"ok={res_inv['ok']}  (H42: pre-gates cannot see it -> switch plant)")
    ok.append(slips)

    # ---- the CAUGHT plant: a contradictory demand set at 'consistency' -------
    contra = _clone()
    contra["statements"].append(
        {"id": "sX", "force": "demand", "quote": "more than 8",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": ">=", "right": 10}})
    res_contra = speculate.pre_gate(REQUEST, _text(contra))
    print(f"  CONTRADICTORY plant   caught={not res_contra['ok']} "
          f"stage={res_contra['stage_reached']!r}")
    print(f"     {res_contra['detail'][:100]}")
    ok.append(not res_contra["ok"] and
              res_contra["stage_reached"] == "consistency")

    # ---- an UNGROUNDED quote is caught at 'reading-gate' ---------------------
    bad_q = _clone()
    bad_q["statements"][3]["quote"] = "guarantee same-day refunds"
    res_bad = speculate.pre_gate(REQUEST, _text(bad_q))
    print(f"  UNGROUNDED-quote plant caught={not res_bad['ok']} "
          f"stage={res_bad['stage_reached']!r}")
    ok.append(not res_bad["ok"] and
              res_bad["stage_reached"] == "reading-gate")

    # ---- log a divergence for the loser, then assert Z1 (no cert, no reading)-
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    candidate_sha = __import__("common").sha256_json(contra)
    request_sha = __import__("common").sha256_bytes(REQUEST.encode())
    payload = speculate.log_divergence(
        reg, stage=res_contra["stage_reached"],
        direction="predicted-fail-actual-pass",
        candidate_sha=candidate_sha, request_sha=request_sha)
    events = reg.events("speculation-divergence")
    print(f"  divergence logged     rows={len(events)} keys="
          f"{sorted(payload)}")
    ok.append(len(events) == 1 and
              set(events[0]["payload"]) ==
              {"stage", "direction", "candidate_sha", "request_sha"})

    # Z1: the loser has NO composed certificate and NO persisted reading.
    cert_rows = reg.db.execute("SELECT COUNT(*) FROM certificates").fetchone()[0]
    reading_rows = reg.readings_all()
    no_cert = (cert_rows == 0
               and not (set(res_contra) & {"cert", "cert_id", "certificate"}))
    print(f"  Z1 loser has no cert  certificates={cert_rows} "
          f"readings={len(reading_rows)} (no composed certificate minted)")
    ok.append(no_cert and reading_rows == [])

    if all(ok):
        print("\nALL TEETH PASS")
        return 0
    print("\nTEETH FAILED:", ok)
    return 1


if __name__ == "__main__":
    sys.exit(main())

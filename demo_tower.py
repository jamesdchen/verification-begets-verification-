#!/usr/bin/env python3
"""Climbing the spec-to-code tower -- one domain, three rungs of vagueness.

The bottom of the tower (spec -> code) is kernel-certified: schemas, proved
constraints, proved sequencing safety, checked composition.  The top
(language -> spec) gets the same dual-checker discipline lifted a rung: the LLM
derives, INDEPENDENTLY from the same request, (a) the service meta-spec and
(b) concrete accept/reject scenario expectations (shown only the tool
interface, never the guards/updates/constraints/safety).  The kernel then
replays the scenarios through the certified dispatcher AND the independent
reference interpreter.  Agreement = two independent linguistic readings of the
request converge on the same behaviour; divergence is fed back and the spec is
re-authored.

Each rung says the same thing more vaguely.  Rung 3 names no states, no tools,
no fields, no numbers -- the machinery must DESIGN the service and then survive
the independent cross-examination of its own reading.
"""
from __future__ import annotations

import json
import sys
import tempfile

from library import Registry
from buildloop import service_loop

MODEL = "claude-fable-5"

RUNGS = [
    ("rung1-precise", """
A prepaid ticketing service named tickets for one show with limited seats.
Context: integer seats_left, initially between 0 and 100.
Lifecycle states: browse -> held -> purchased -> closed, starting at browse.
Tools: hold(count) moves browse->held, guarded by count <= seats_left, updates
seats_left := seats_left - count, with cross-field constraints 1 <= count <= 8
(invariant: count >= 1); purchase() moves held->purchased; close() moves
purchased->closed.
Safety: when purchased, seats_left >= 0 (never oversell).
"""),
    ("rung2-partial", """
Sell tickets for a single show with a limited number of seats. Customers first
reserve some seats, then confirm the purchase, then the order is closed. Never
let more seats be reserved than remain, and nobody may take more than 8 seats
in one order. Track how many seats are left.
"""),
    ("rung3-vague", """
I run a small venue. Help me not oversell tickets.
"""),
]


def main():
    summary = []
    for name, request in RUNGS:
        print(f"== {name} ==")
        print("request:", " ".join(request.split())[:120], "...")
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tf:
            reg = Registry(db_path=tf.name)
            res = service_loop.synthesize_service(
                request, model=MODEL, event_sink=reg.log_event,
                cache_get=reg.cache_get, cache_put=reg.cache_put,
                write_output=False)
        ok = res["status"] == "certified"
        print(f"  status={res['status']} rounds={res['rounds']} "
              f"tokens={res['tokens']}")
        if ok:
            for layer, cert, ch in res["layers"]:
                print(f"  {'OK' if cert else 'XX'} {layer:<28} {ch}")
            spec = res["spec"]
            print(f"  designed: states={spec['states']} "
                  f"tools={[t['name'] for t in spec['tools']]} "
                  f"safety={json.dumps(spec['safety'])}")
        else:
            for t in res.get("last", []):
                print("  last transcript:", t[:400])
        summary.append({"rung": name, "status": res["status"],
                        "rounds": res["rounds"], "tokens": res["tokens"],
                        "layers": len(res.get("layers", []))})
        print()
    print("summary:", json.dumps(summary))
    return all(s["status"] == "certified" for s in summary)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

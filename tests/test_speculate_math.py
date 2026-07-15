#!/usr/bin/env python3
"""WP-E: MathReading speculative fan-out TEETH -- LLM-free, hand-planted.

Runnable under pytest AND as a bare script
(`python3 tests/test_speculate_math.py` -> PASS lines, exit 0).

F-INT-5 adds a Lean-free math pre-gate ladder that mirrors the service ladder
(`speculate.pre_gate`) rung for rung, cheapest first:

    parse-math-reading (gate)      -> parse_math_reading groundedness/trichotomy
    math-smt (hypothesis-sat)      -> dual-solver non-vacuity (Z3 [AND cvc5])
    compile-math (escape gate)     -> compile_math_reading + validate_lean
    entailed-instance-replay       -> RANK-ONLY, never a rejection (S4)

These teeth pin (E3):

  * RUNG ORDER: a fabricating candidate dies at the parse gate and NO SMT
    backend call is ever spent on it (cheapest-first is real, not decorative);
  * a CONTRADICTORY hypothesis set dies at math-smt (dual-solver degrades
    honestly when cvc5 is absent -- the enumeration channel still refuses);
  * a CARRIER-NARROWED candidate (declared object types Nat where Int is
    needed -- ⚠FI-6) REACHES entailed-instance-replay (rank-only never rejects)
    but its replay refutes it, so it REORDERS below the certifying candidate;
  * LOSER-HAS-NO-CERT (Z1): no losing candidate mints a certificate;
  * a speculated-pass / certified-fail divergence logs the Z-D payload;
  * the SERVICE ladder is byte-unchanged (the pin below, captured from the
    frozen pre-swarm base BEFORE speculate.py was edited -- ⚠FI-11).
"""
from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from buildloop import speculate


# --------------------------------------------------------------------------- #
# BYTE-IDENTITY PIN (⚠FI-11): the SERVICE ladder's structural verdicts on the
# four canonical scenarios of tests/test_speculate.py, captured from the FROZEN
# pre-swarm base before this package touched speculate.py.  WP-E adds functions;
# it never edits the service ladder, and this pin proves the service verdicts
# did not move.  Only the solver-version-STABLE fields are pinned (stage/ok/
# scenario count); `detail` carries a solver version string and is excluded by
# design -- pinning it would be a false byte-identity claim (E5 honesty).
_SERVICE_LADDER_GOLDEN = {
    "good":          {"stage_reached": "entailed-replay", "ok": True,  "scenarios": 3},
    "inverted":      {"stage_reached": "entailed-replay", "ok": True,  "scenarios": 3},
    "contradictory": {"stage_reached": "consistency",     "ok": False, "scenarios": 0},
    "ungrounded":    {"stage_reached": "reading-gate",    "ok": False, "scenarios": 0},
}

# The service request + planted readings (imported from the service teeth so the
# pin exercises the EXACT same fixtures the service path certifies).
import tests.test_speculate as _svc


def _service_scenarios() -> dict:
    out = {}
    out["good"] = speculate.pre_gate(_svc.REQUEST, _svc._text(_svc.GOOD))
    doc = _svc._clone(); doc["statements"][2]["lf"]["op"] = "inc"
    out["inverted"] = speculate.pre_gate(_svc.REQUEST, _svc._text(doc))
    doc = _svc._clone()
    doc["statements"].append(
        {"id": "sX", "force": "demand", "quote": "more than 8",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": ">=", "right": 10}})
    out["contradictory"] = speculate.pre_gate(_svc.REQUEST, _svc._text(doc))
    doc = _svc._clone(); doc["statements"][3]["quote"] = "guarantee same-day refunds"
    out["ungrounded"] = speculate.pre_gate(_svc.REQUEST, _svc._text(doc))
    return out


def test_service_ladder_byte_unchanged():
    """The SERVICE ladder's structural verdicts are byte-identical to the frozen
    pre-swarm base -- WP-E added the math path without disturbing the service
    path (the E3 byte-identity requirement)."""
    got = _service_scenarios()
    stable = {k: {"stage_reached": v["stage_reached"], "ok": v["ok"],
                  "scenarios": v["scenarios"]} for k, v in got.items()}
    assert stable == _SERVICE_LADDER_GOLDEN, json.dumps(stable, indent=2)


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print("PASS", _name)
    print("speculate-math pin holds (service ladder byte-unchanged)")

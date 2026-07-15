#!/usr/bin/env python3
"""S4 speculative pre-gate + divergence ledger TEETH -- LLM-free, hand-planted.

Runnable under pytest AND as a bare script
(`python3 tests/test_speculate.py` -> PASS lines, exit 0).

The pre-gate is a RANK, never a certificate (Z1), and stage 4 is rank-only.
These teeth pin exactly that:

  * a GOOD grounded reading clears the three rejecting pre-gates and reaches
    entailed-replay;
  * an INVERTED-effect plant SLIPS PAST every pre-gate (the ⚠H42 check: the
    speculative pre-gate cannot see it -- only the full pipeline's protocol BMC
    can), which is WHY the caught plant below is a contradictory demand set, not
    the inverted effect;
  * a CONTRADICTORY demand set is provably caught at "consistency";
  * an UNGROUNDED quote is provably caught at "reading-gate";
  * a divergence event carries exactly the Z-D payload keys;
  * Z1: a rejected candidate mints NO certificate and persists NO reading.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from buildloop import speculate
from library import Registry

# --------------------------------------------------------------------------- #
# A synthetic request with the exact spans the hand-planted readings quote.
REQUEST = ("I run a small venue. Help me not oversell tickets. "
           "Nobody may take more than 8 tickets in one order.")

# A GOOD, grounded reading: a quantity (tickets_left), an action (sell) with an
# integer argument (count), the depleting effect, and a demanded `always` bound
# (never oversell) plus per-call bounds.  Structure mirrors the certified
# reading in demo_reading.py.
GOOD = {
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
    return json.loads(json.dumps(GOOD))


def _text(doc):
    return json.dumps(doc)


# --------------------------------------------------------------------------- #
def test_good_reading_reaches_entailed_replay():
    """A grounded reading clears reading-gate, consistency and compile and
    reaches the rank-only entailed-replay stage (ok True)."""
    res = speculate.pre_gate(REQUEST, _text(GOOD))
    # passes at least through compile: ok True OR reached entailed-replay.
    assert res["ok"] is True or res["stage_reached"] == "entailed-replay", res
    assert res["stage_reached"] == "entailed-replay", res
    assert res["ok"] is True, res
    assert res["scenarios"] >= 1, res   # solver-entailed scenarios were derived
    # Z1: a pre-gate is a RANK, not a certificate -- no cert of any name.
    assert not (set(res) & {"cert", "cert_id", "certificate"}), res


def test_inverted_effect_slips_past_pregates():
    """⚠H42: the inverted-verb-effect plant (selling INCREASES stock) is NOT
    catchable by the pre-gates -- demands_smt ignores effects and compile is
    purely structural -- so it reaches entailed-replay.  This is the verification
    that mandates using a contradictory demand set as the caught plant."""
    doc = _clone()
    doc["statements"][2]["lf"]["op"] = "inc"   # dec -> inc: wrong verb semantics
    res = speculate.pre_gate(REQUEST, _text(doc))
    assert res["stage_reached"] == "entailed-replay", res
    assert res["ok"] is True, ("the inverted-effect plant is invisible to the "
                               "pre-gates; only the full pipeline catches it: "
                               + repr(res))


def test_contradictory_demand_caught_at_consistency():
    """The caught plant: two demanded bounds count<=8 and count>=10 make the
    demand set UNSAT, caught at the 'consistency' pre-gate with ok False."""
    doc = _clone()
    doc["statements"].append(
        {"id": "sX", "force": "demand", "quote": "more than 8",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": ">=", "right": 10}})
    res = speculate.pre_gate(REQUEST, _text(doc))
    assert res["stage_reached"] == "consistency", res
    assert res["ok"] is False, res
    assert res["scenarios"] == 0, res
    # Z1: even a rejected candidate never carries a certificate.
    assert not (set(res) & {"cert", "cert_id", "certificate"}), res


def test_ungrounded_quote_caught_at_reading_gate():
    """A fabricated demand (quote absent from the request) is caught earliest,
    at the 'reading-gate' pre-gate."""
    doc = _clone()
    doc["statements"][3]["quote"] = "guarantee same-day refunds"
    res = speculate.pre_gate(REQUEST, _text(doc))
    assert res["stage_reached"] == "reading-gate", res
    assert res["ok"] is False, res


def test_log_divergence_writes_zd_payload():
    """A divergence event lands in the events table with exactly the Z-D keys."""
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    payload = speculate.log_divergence(
        reg, stage="consistency",
        direction="predicted-pass-actual-fail",
        candidate_sha="cand-abc", request_sha="req-def")
    rows = reg.events("speculation-divergence")
    assert len(rows) == 1, rows
    got = rows[0]["payload"]
    assert set(got) == {"stage", "direction", "candidate_sha", "request_sha"}, got
    assert got["stage"] == "consistency"
    assert got["direction"] == "predicted-pass-actual-fail"
    assert got["candidate_sha"] == "cand-abc"
    assert got["request_sha"] == "req-def"
    assert got == payload


def test_log_divergence_rejects_bad_direction():
    """`direction` must be a real prediction-miss direction (Z-D vocabulary)."""
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    try:
        speculate.log_divergence(reg, stage="compile", direction="whatever",
                                 candidate_sha="a", request_sha="b")
    except ValueError:
        pass
    else:
        raise AssertionError("bad divergence direction must raise ValueError")
    assert reg.events("speculation-divergence") == []


def test_z1_loser_gets_no_certificate_and_no_reading():
    """Z1: a rejected candidate mints NO certificate and persists NO reading.
    The pre-gate returns a rank record with no cert id, and nothing in this
    module ever calls `reading_add`, so a fresh registry stays empty."""
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    # a contradictory (losing) candidate
    doc = _clone()
    doc["statements"].append(
        {"id": "sX", "force": "demand", "quote": "more than 8",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": ">=", "right": 10}})
    res = speculate.pre_gate(REQUEST, _text(doc))
    assert res["ok"] is False and res["stage_reached"] == "consistency", res
    # no certificate id of any kind is in the loser's rank record
    assert not (set(res) & {"cert", "cert_id", "certificate"}), res
    # and the pre-gate persisted nothing: no readings row was minted for it
    assert reg.readings_all() == [], reg.readings_all()
    assert reg.reading_get("any-demand-id") is None


def test_fan_out_llm_free_returns_empty():
    """With model=None (every LLM-free / CI caller), fan_out makes no LLM call
    and returns [] -- the deterministic path never touches the LLM."""
    assert speculate.fan_out(REQUEST, 3, model=None) == []
    assert speculate.fan_out(REQUEST, 1, model=None, spend=1000) == []


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print("PASS", _name)
    print("speculate teeth hold "
          "(good reaches entailed-replay; inverted effect slips past pre-gates; "
          "contradiction caught at consistency; ungrounded caught at "
          "reading-gate; Z-D payload logged; Z1 losers get no cert/reading)")

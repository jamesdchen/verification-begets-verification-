#!/usr/bin/env python3
"""S3 part_a / WP-M demo -- the structural CHOICE-force tail macro (the H2 win).

Deterministic, LLM-free.  ``buildloop.recurrence._demand_windows`` now mines
UNIFORM-(force, quote) windows, not demand-force-only (read recurrence.py).  That
makes a CHOICE-force tail -- a run of statements all ``force="choice"``,
``quote=""`` -- mineable, which it was NOT pre-H2.  This demo shows it end to end:

  1. a two-reading corpus sharing a contiguous choice-force transition tail mines
     a macro whose body IS that tail (and the statements it abstracts are CHOICE);
  2. NEGATIVE CONTROL -- give the tail's two statements DIFFERENT quotes and the
     H2 uniform-quote rule drops the window: nothing is mined;
  3. flat vs macro-aware design DL differ against the LIVE macro table -- the
     mined choice-tail macro makes ``planner.choices.score_reading`` strictly
     cheaper than the flat, empty-table score.

Prints the mined macro, the flat/macro-aware scores, per-check PASS/FAIL, ends
"ALL TEETH PASS", and exits non-zero on any failure.
"""
from __future__ import annotations

import json
import sys

from buildloop import recurrence, mdl_macros
import planner.choices as ch

REQUIRES_LLM = False

# The choice-force tail idiom (the S3 example): two adjacent transition
# statements, both force="choice", quote="".
TAIL = [
    {"kind": "transition", "action": "a", "from": "open", "to": "open"},
    {"kind": "transition", "action": "close_out", "from": "open", "to": "closed"},
]
TAIL_CLUSTER_KEY = ["transition", "transition"]


def _choice(sid, lf, quote=""):
    return {"id": sid, "force": "choice", "quote": quote, "lf": dict(lf)}


def _demand_prefix(sid, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}}


def _reading(name, prefix_quote, tail_quotes=("", "")):
    return {"service": name, "statements": [
        _demand_prefix(name + "_d", prefix_quote),
        _choice(name + "_t0", TAIL[0], tail_quotes[0]),
        _choice(name + "_t1", TAIL[1], tail_quotes[1])]}


def _good_corpus():
    return [_reading("svc1", "keep the quantity non negative here"),
            _reading("svc2", "an entirely different demand quote string")]


def _mismatched_corpus():
    return [_reading("svc1", "keep the quantity non negative here",
                     tail_quotes=("alpha", "beta")),
            _reading("svc2", "an entirely different demand quote string",
                     tail_quotes=("alpha", "beta"))]


def _choice_tail_candidate(candidates):
    hits = [c for c in candidates if c["cluster_key"] == TAIL_CLUSTER_KEY]
    return hits[0] if hits else None


def main() -> int:
    results = []

    def check(label, ok):
        results.append(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")

    good = _good_corpus()
    reading = good[0]

    print("== 1. mine a CHOICE-force tail (the H2 win) ==")
    print("  corpus: 2 readings sharing this force=choice, quote=\"\" tail:")
    for s in reading["statements"][-2:]:
        print(f"    force={s['force']:<7} quote={s['quote']!r:<4} lf={json.dumps(s['lf'])}")
    tail_is_choice = all(s["force"] == "choice" and s["quote"] == ""
                         for s in reading["statements"][-2:])
    check("the shared tail is CHOICE-force (force=choice, quote='')", tail_is_choice)

    cands = recurrence.mine(good, {})
    macro = _choice_tail_candidate(cands)
    check("mine() returns a choice-tail macro", macro is not None)
    if macro is None:
        print("\nsummary:", json.dumps({"mined": False}))
        print("SOME TEETH FAILED")
        return 1

    cand = macro["candidate"]
    print("\n  MINED CHOICE MACRO:")
    print("   ", json.dumps(cand))
    print(f"    cluster_key={macro['cluster_key']}  uses={macro['uses']}  "
          f"dl_saving={macro['dl_saving']}")
    check("mined body IS the choice-tail cluster", cand["body"] == TAIL)
    check("used by >= 2 readings and dl_saving > 0",
          macro["uses"] >= 2 and macro["dl_saving"] > 0)

    print("\n== 2. NEGATIVE CONTROL -- mismatched quotes drop the window ==")
    bad = _mismatched_corpus()
    for s in bad[0]["statements"][-2:]:
        print(f"    force={s['force']:<7} quote={s['quote']!r:<7} lf={json.dumps(s['lf'])}")
    bad_win = [w for w in recurrence._demand_windows(bad[0],
                                                     recurrence.DEFAULT_MAX_LEN)
               if [x["lf"]["kind"] for x in w] == TAIL_CLUSTER_KEY]
    check("_demand_windows drops the mismatched-quote tail window", bad_win == [])
    bad_cands = recurrence.mine(bad, {})
    check("mine() yields no choice-tail macro on the mismatched corpus",
          _choice_tail_candidate(bad_cands) is None and bad_cands == [])

    print("\n== 3. flat vs macro-aware design DL (live macro table) ==")
    table = {cand["name"]: cand}
    flat = ch.score_reading(reading, {})
    macroed = ch.score_reading(reading, table)
    print(f"    flat score  (empty table) = {flat}")
    print(f"    macro-aware (choice tail) = {macroed}")
    print(f"    statements: flat={mdl_macros.statement_count(reading, {})}  "
          f"macroed={mdl_macros.statement_count(reading, table)}")
    check("score_reading(reading, {}) is the flat reading DL",
          flat == mdl_macros.dl_reading(reading, {}))
    check("macro-aware score < flat score (the choice-tail macro compresses)",
          macroed < flat)

    ok = all(results)
    print("\nsummary:", json.dumps({
        "choice_force_tail_mined": macro is not None,
        "mined_macro": cand,
        "cluster_key": macro["cluster_key"],
        "dl_saving": macro["dl_saving"],
        "flat_score": flat,
        "macro_aware_score": macroed,
        "negative_control_drops_window": bool(bad_win == [] and bad_cands == []),
    }))
    if ok:
        print("ALL TEETH PASS")
        return 0
    print("SOME TEETH FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())

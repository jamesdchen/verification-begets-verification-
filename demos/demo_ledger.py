#!/usr/bin/env python3
"""Combined-Loop W0 -- one demand ledger, one currency (ledger_dl), one gate.

Every demand kind (spec-file, nl-request, caged-incumbent) is a row in ONE
ledger, priced in ONE unit, admitted through ONE gate.  This demo exercises the
gate's four teeth end to end, LLM-free:

Part 0 -- integration.  `ledger sync` ingests the committed static demand
  (backlog + requests + incumbents) as exogenous rows; a ledger_dl snapshot is
  recorded.  Re-sync is idempotent and never re-tags a row (house rule 12).

Tooth (a) -- a synthetic generator that covers one exogenous spec with a HUGE
  spec_grammar is REFUSED when a cheaper covering candidate exists, and only
  admitted-as-EXPANSION (dl_after > dl_before, i.e. NOT a DL win) when nothing
  cheaper covers the same rows.

Tooth (b) -- a candidate with tiny atoms but a 20 KB grammar_js is refused; the
  payload is now priced (fact 6: the legacy series popped it before pricing).

Tooth (c) -- a SYSTEM-origin rewrite row can never trigger the expansion
  exception (exogeneity rule, house rule 12).

Tooth (d) -- a fake incumbent with zero ingested calls contributes ZERO toll
  pressure (the capped-toll fix: caging is never worse than leaving demand
  uncovered).

REQUIRES_LLM = False -- pure, deterministic ledger accounting; no LLM, no codec
emission, no solver on this path.
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
import tempfile

import planner
from buildloop import dl
from library import Registry
from metrics import ledger_snapshot

REQUIRES_LLM = False


# --------------------------------------------------------------- builders
def _gen(name, atoms, *, tier="emit-check", grammar_js=""):
    g = {"name": name, "spec_language": "ksy", "output_language": "python-codec",
         "spec_grammar": {"atoms": sorted(atoms)},
         "emit_entrypoint": {"kind": "ksc-python-rw"},
         "contract": {"type": "codec-roundtrip"}, "tier": tier}
    if grammar_js:
        # the LLM-authored payload as it rides a real candidate: a top-level
        # `_grammar_js` the legacy series pops before pricing (fact 6).
        g["_grammar_js"] = grammar_js
    g["generator_hash"] = planner._hash_entry(g)
    return g


def _spec(did, atoms, size=64, *, origin="exogenous", status="open"):
    return {"demand_id": did, "kind": "spec-file", "origin": origin,
            "status": status, "language": "ksy", "features": sorted(atoms),
            "payload_ref": did, "size_bytes": size, "covered_via": None}


def _incumbent(did, *, status="open"):
    return {"demand_id": did, "kind": "caged-incumbent", "origin": "exogenous",
            "status": status, "language": None, "features": None,
            "payload_ref": did, "size_bytes": 500, "covered_via": None}


def _snap(generators, demand, *, toll_calls=None, readings=None):
    return dl.LedgerSnapshot(generators=list(generators), demand=list(demand),
                             macro_table={}, toll_calls=toll_calls or {},
                             readings=readings or {})


# ------------------------------------------------------------------- part 0
def part_0() -> bool:
    tmp = tempfile.mkdtemp()
    reg = Registry(db_path=f"{tmp}/reg.sqlite")
    import cgb
    n1 = cgb._ledger_sync(reg)
    n2 = cgb._ledger_sync(reg)          # idempotent
    total = dl.ledger_dl(reg)
    row = ledger_snapshot(reg, epoch=0, event="w0-baseline")
    # F3.1: the math-source kind joins the one ledger -- every top-level
    # exogenous corpus statement plus 8 dream paraphrases (origin=system).
    # The exogenous count is derived from the same glob _ledger_sync bills,
    # so the demo tracks the LIVE corpus across promotions (frozen bench
    # artifacts pin the historical 40-source run elsewhere).
    n_exo = len(list((pathlib.Path("specs") / "mathsources").glob("*.txt")))
    ok = (n1["added"] > 0 and n2["added"] == 0
          and total["total_spec"] == 200 and total["total_request"] == 20
          and total["total_incumbent"] == 2
          and n_exo >= 40
          and total["total_math"] == n_exo + 8 and total["dream_rows"] == 8
          # nothing registered yet -> every EXOGENOUS demand uncovered, priced
          # at 50; the 8 dreams bill 0.0 (E3: dreams propose, they never bill).
          and abs(total["ledger_dl"] - 50.0 * (200 + 20 + n_exo)) < 1e-6
          and row["ledger_dl"] == round(total["ledger_dl"], 3))
    print(f"  synced {n1['added']} rows (re-sync added {n2['added']}); "
          f"ledger_dl={round(total['ledger_dl'],3)} "
          f"(spec {total['covered_spec']}/{total['total_spec']}, "
          f"request {total['covered_request']}/{total['total_request']}, "
          f"math {total['covered_math']}/{total['total_math']} "
          f"[{total['dream_rows']} dreams bill 0], "
          f"incumbents {total['total_incumbent']})")
    print(f"  ledger_snapshot recorded: kernel_loc={row['kernel_loc']}, "
          f"tier_mix={row['tier_mix']}")
    print(f"  part_0 integration: {ok}")
    return ok


# ------------------------------------------------------------------- tooth a
def part_a() -> bool:
    d1 = _spec("D1", {"uint:1"})
    base = _snap([], [d1])
    # a huge grammar: covers uint:1 but 400 junk atoms make its generator_dl
    # dwarf the coverage saving -> DL-inflating.
    huge = _gen("huge", ["uint:1"] + [f"junk:{i}" for i in range(400)])
    small = _gen("small", ["uint:1"])

    with_alt = dl.admission_decision(base, huge, alternatives=[small])
    no_alt = dl.admission_decision(base, huge, alternatives=[])

    refused = (not with_alt["admit"]
               and with_alt["blocked_by_cheaper_alternative"] is not None
               and with_alt["exogenous_newly_covered"] == ["D1"])
    expanded = (no_alt["admit"] and no_alt["expansion"]
                and no_alt["dl_after"] > no_alt["dl_before"])   # NOT a DL win
    # and the cheaper alternative is itself a real DL win (admitted normally)
    small_dec = dl.admission_decision(base, small)
    cheaper_wins = small_dec["admit"] and not small_dec["expansion"]

    print(f"  huge vs cheaper-alt: refused={refused} "
          f"(blocked_by={with_alt['blocked_by_cheaper_alternative'][:8]}...)")
    print(f"  huge alone: admitted-as-expansion={expanded} "
          f"(dl {no_alt['dl_before']} -> {no_alt['dl_after']}, not a win)")
    print(f"  small covering candidate is a real DL win: {cheaper_wins}")
    ok = refused and expanded and cheaper_wins
    print(f"  part_a: {ok}")
    return ok


# ------------------------------------------------------------------- tooth b
def part_b() -> bool:
    d1 = _spec("D1", {"uint:1"})
    small = _gen("small", ["uint:1"])
    base = _snap([small], [d1])          # D1 already covered by `small`
    payload = "x" * 20000
    bloated = _gen("bloated", ["uint:1"], grammar_js=payload)  # covers nothing new

    dec = dl.admission_decision(base, bloated)
    # the payload is priced: generator_dl is dominated by the 20 KB grammar_js
    gdl = dl.generator_dl(bloated)
    from buildloop import mdl as legacy
    legacy_dl = legacy.generator_dl(bloated)   # legacy ignores grammar_js
    payload_priced = gdl > 300 and legacy_dl < 5
    refused = (not dec["admit"] and not dec["expansion"]
               and dec["newly_covered"] == [])

    print(f"  generator_dl(bloated)={round(gdl,2)}  "
          f"legacy generator_dl={round(legacy_dl,2)}  "
          f"payload_priced={payload_priced}")
    print(f"  gate refuses the bloated candidate: {refused}")
    ok = payload_priced and refused
    print(f"  part_b: {ok}")
    return ok


# ------------------------------------------------------------------- tooth c
def part_c() -> bool:
    d_sys = _spec("Dsys", {"uint:1"}, origin="system")
    base = _snap([], [d_sys])
    huge = _gen("huge", ["uint:1"] + [f"junk:{i}" for i in range(400)])
    dec = dl.admission_decision(base, huge, alternatives=[])
    # it newly covers a SYSTEM row, so expansion must NOT fire.
    ok = (not dec["admit"] and not dec["expansion"]
          and dec["system_newly_covered"] == ["Dsys"]
          and dec["exogenous_newly_covered"] == [])
    print(f"  system-origin newly-covered={dec['system_newly_covered']}, "
          f"expansion={dec['expansion']}, admit={dec['admit']}")
    print(f"  part_c: {ok}")
    return ok


# ------------------------------------------------------------------- tooth d
def part_d() -> bool:
    inc = _incumbent("INC")
    ih = dl.incumbent_hash_of(inc)
    zero = _snap([], [inc], toll_calls={})                 # no ingested calls
    busy = _snap([], [inc], toll_calls={ih: 100.0})        # 100 ingested calls
    cost_zero = dl._demand_cost(inc, zero)
    cost_busy = dl._demand_cost(inc, busy)
    # zero calls -> zero toll pressure; capped stock is positive but bounded.
    ok = (cost_zero == 0.0 and cost_busy == dl.toll_stock(100.0)
          and 0 < cost_busy <= dl.UNCOVERED_PENALTY)
    print(f"  toll pressure: 0 calls -> {cost_zero}, "
          f"100 calls -> {round(cost_busy,3)} (capped at {dl.UNCOVERED_PENALTY})")
    print(f"  part_d: {ok}")
    return ok


if __name__ == "__main__":
    p0 = part_0()
    a = part_a()
    b = part_b()
    c = part_c()
    d = part_d()
    print("\nsummary:", json.dumps({
        "part_0_ledger_sync_and_currency": p0,
        "tooth_a_expansion_refused_when_cheaper_exists": a,
        "tooth_b_payload_priced_and_refused": b,
        "tooth_c_system_row_cannot_expand": c,
        "tooth_d_zero_calls_zero_toll": d}))
    sys.exit(0 if all([p0, a, b, c, d]) else 1)

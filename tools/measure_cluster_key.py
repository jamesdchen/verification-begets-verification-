#!/usr/bin/env python3
"""WP-T3-CK: the cluster-key harvester's rerunnable before/after measurement.

This tool REPORTS numbers; it decides nothing.  It replays the committed
checkpoint's authored readings (the parsed LFs -- fixed DATA, independent of the
miner) through the greedy grow the bench uses, ONCE in "legacy" mode (byte-
identical to the committed run: the 2139 baseline) and ONCE in "refined" mode
(WP-T3-CK: force-only MATH windows behind the op-signature-skeleton cluster key),
then prints the before/after table and the acceptance verdicts (a)-(e).

Why a script and not a committed number: the frozen 37-reading corpus is being
grown by a parallel authoring run, so this package is RE-MEASURED at merge time.
Everything here is deterministic and reruns against whatever `bench._corpus_
sources()` and the checkpoint contain -- the relational verdicts (refined <
baseline, congruence macro reached, even/odd covered, <= 8 macros, service
byte-identical) are what must hold, not the exact 1820.

Note on the census (tools/tower_census.py): its committed pass-2/pass-3 numbers
measure the DEFAULT ("legacy") miner and stay correct -- the refined window rule
is gated behind `math_mode="refined"` and changes NO default behavior.  The
refined counterpart of the pass-3 window measurement (the congruence cluster's
demand-window count goes 0 -> N once force-only math windows are enabled) is
reported HERE, so the committed census golden is left untouched.

Determinism: no timestamps, no randomness; same checkpoint + same corpus ->
byte-identical JSON.  Reuses bench / tower_census functions READ-ONLY.

Usage:
    tools/measure_cluster_key.py            # writes results/cluster_key_measure.json
    tools/measure_cluster_key.py --print    # also echo the human before/after table
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import common                                       # noqa: E402
import bench_formalize as bench                     # noqa: E402
from buildloop import mdl_macros, recurrence        # noqa: E402
from tools import tower_census as tc                # noqa: E402

OUT_JSON = os.path.join(_ROOT, "results", "cluster_key_measure.json")

# The committed baseline -- re-registered at the WP-AUTH corpus growth
# (frozen 37-certified corpus: 2139.0; grown 46-certified corpus: 2920.0).
# Bar semantics preserved across the re-registration: ACCEPT_MAX_DL is
# baseline minus 29 (the magnitude of the T3 window-rule regression the
# original bar guarded against, §11.10); MAX_MACROS scales with certified
# readings by the original per-reading proportion (8 at 37 -> 10 at 46),
# and the over-fragmentation judgment is weighed explicitly by the flip
# decision (WP-FLIP), not silently by this bar.
BASELINE_GOVERNED_DL = 2920.0
ACCEPT_MAX_DL = 2891.0        # acceptance (a): >= this is "noise, not a harvest"
MAX_MACROS = 10              # acceptance (c): more signals over-fragmentation


# --------------------------------------------------------------- greedy replay
def _greedy_grow(table, corpus, wfilter, math_mode):
    """The bench's greedy grow (bench._greedy_grow) with the WP-T3-CK `math_mode`
    threaded through -- mine+admit the best candidate that clears the explicit
    admission gate, to a fixpoint."""
    while True:
        cands = recurrence.mine(corpus, table, witness_filter=wfilter,
                                math_mode=math_mode)
        chosen = None
        for c in cands:
            cand = c["candidate"]
            if cand["name"] in table:
                continue
            if mdl_macros.macro_admission_decision(
                    corpus, cand, table, witness_filter=wfilter)["admit"]:
                chosen = cand
                break
        if chosen is None:
            return
        table[chosen["name"]] = chosen


def _replay(records, arm, governed, dream_readings, math_mode):
    """Reconstruct one arm's final macro table by replaying its recorded waves'
    AUTHORED readings through the greedy grow in `math_mode`.  Mirrors
    tower_census._replay_arm's wave tiling (restricted to the checkpoint's
    recorded sources, per the frozen-vs-live note there) but swaps the miner mode
    and drops the table-hash verification (the recorded hashes pin the LEGACY
    miner; a different miner legitimately yields a different table)."""
    sources = bench._corpus_sources()
    recorded_sids = {r["source_id"] for r in records}
    sources = [(sid, txt) for sid, txt in sources if sid in recorded_sids]
    wfilter = bench._EXO if governed else None
    waves = [sources[i:i + bench.WAVE_SIZE]
             for i in range(0, len(sources), bench.WAVE_SIZE)]
    arm_recs = {r["source_id"]: r for r in records if r["arm"] == arm}
    table: dict = {}
    exo: list = []
    for wave in waves:
        for sid, txt in wave:
            rec = arm_recs.get(sid)
            if rec is None:
                continue
            doc = bench._reading_doc(rec, txt, origin="exogenous")
            if doc is not None:
                doc["_sid"] = sid
                exo.append(doc)
        corpus = exo + (dream_readings if not governed else [])
        _greedy_grow(table, corpus, wfilter, math_mode)
    return table, exo


# ------------------------------------------------------------------- inventory
def _inventory(table, readings):
    stats = mdl_macros.corpus_dl(readings, table)
    macros = []
    for name in sorted(table):
        m = table[name]
        kinds = [t.get("kind") if isinstance(t, dict) else t for t in m["body"]]
        macros.append({
            "name": name,
            "params": list(m.get("params", [])),
            "body_len": len(m["body"]),
            "kinds": kinds,
            "op_slots": {k: v for k, v in
                         sorted(recurrence._op_slot_params(m["body"]).items())},
            "uses": stats["reading_uses"].get(name, 0),
            "dl_macro": round(mdl_macros.dl_macro(m), 3),
        })
    return {"corpus_dl": round(stats["total"], 3),
            "count": len(table), "macros": macros}


def _covered_by(reading, macro, table):
    """True iff the greedy rewrite of `reading` with just {macro} uses it."""
    _, _, used = mdl_macros._reading_stats(reading, {macro["name"]: macro})
    return macro["name"] in used


def _congruence_reference_name(gexo):
    """The macro name of the census's hand-picked congruence body: anti-unify the
    CONG_TRIPLE [h1, h2, c] window (the -179 counterfactual) and name it.  If the
    greedy refined table CONTAINS this name, the greedy path REACHED the exact
    body the census could only reach counterfactually."""
    triple = [r for sid in tc.CONG_TRIPLE for r in gexo if r.get("_sid") == sid]
    if len(triple) != len(tc.CONG_TRIPLE):
        return None
    occ = [tc._pick_window(r, tc.CONG_WINDOW_IDS) for r in triple]
    body, _ = recurrence._antiunify_windows(occ)
    return recurrence._macro_name(body)


def _cong_window_count(gexo, math_mode):
    """The pass-3 window measurement, refined counterpart: how many demand
    windows over the congruence [h1,h2,c] cluster the miner proposes in
    `math_mode` (0 under legacy strict-quote windows; > 0 under force-only)."""
    total = 0
    for r in gexo:
        if r.get("_sid") not in tc.CONG_TRIPLE:
            continue
        ids = set(tc.CONG_WINDOW_IDS)
        for w in recurrence._demand_windows(r, recurrence.DEFAULT_MAX_LEN,
                                            math_mode=math_mode):
            wids = {s.get("id") for s in w}
            if ids <= wids:
                total += 1
    return total


# ------------------------------------------------------------------- the measure
def measure(checkpoint=tc.CHECKPOINT):
    records = tc._load_records()
    dream = tc._dream_readings(records)

    gov = {}
    for mode in ("legacy", "refined"):
        table, gexo = _replay(records, "governed", True, dream, mode)
        gov[mode] = {"table": table, "exo": gexo,
                     "inventory": _inventory(table, gexo)}
    ung = {}
    for mode in ("legacy", "refined"):
        table, uexo = _replay(records, "ungoverned", False, dream, mode)
        ung[mode] = {"inventory": _inventory(table, uexo)}

    gexo = gov["refined"]["exo"]
    ref_table = gov["refined"]["table"]
    base_dl = gov["legacy"]["inventory"]["corpus_dl"]
    ref_dl = gov["refined"]["inventory"]["corpus_dl"]

    # --- congruence macro: did the greedy path reach the census's -179 body? ---
    cong_name = _congruence_reference_name(gexo)
    cong_in_table = cong_name in ref_table
    cong_uses = gov["refined"]["inventory"]["macros"]
    cong_uses = next((m["uses"] for m in cong_uses if m["name"] == cong_name), 0)
    # its realized marginal delta: ablate it from the refined table.
    cong_delta = None
    if cong_in_table:
        trial = {k: v for k, v in ref_table.items() if k != cong_name}
        cong_delta = round(mdl_macros.corpus_dl(gexo, ref_table)["total"]
                           - mdl_macros.corpus_dl(gexo, trial)["total"], 3)

    # --- even/odd survival: an arity-1 op-slot macro (=> ranges over {even,odd}
    #     ONLY, the whole pred/1 lexicon) used by >= 2 readings, covering the
    #     even_plus_even / odd_plus_odd theorems. ---
    EVENODD_READINGS = ("04_even_plus_even", "05_odd_plus_odd")
    evenodd_macro = None
    for name in sorted(ref_table):
        m = ref_table[name]
        arities = set(recurrence._op_slot_params(m["body"]).values())
        if 1 in arities:                        # a pred/1 (even|odd) op-slot
            evenodd_macro = m
            break
    evenodd_uses = 0
    evenodd_covered = []
    if evenodd_macro is not None:
        inv = gov["refined"]["inventory"]["macros"]
        evenodd_uses = next(mm["uses"] for mm in inv
                            if mm["name"] == evenodd_macro["name"])
        for sid in EVENODD_READINGS:
            r = next((x for x in gexo if x.get("_sid") == sid), None)
            if r is not None and _covered_by(r, evenodd_macro, ref_table):
                evenodd_covered.append(sid)

    # --- service byte-identity: the pinned digest (test_service_mining pins it
    #     too) is unchanged in BOTH modes. ---
    from tests import fixtures_macro_corpora as fx
    svc = [fx._reading("r1", "ABCD"), fx._reading("r2", "ABCD")]
    svc_legacy = common.sha256_json(recurrence.mine(svc, {},
                                                    math_mode="legacy"))[:16]
    svc_refined = common.sha256_json(recurrence.mine(svc, {},
                                                     math_mode="refined"))[:16]
    service_identical = (svc_legacy == svc_refined == "b9f1f0b9bb198732")

    # --- acceptance verdicts (all relational) ---
    verdicts = {
        "a_beats_baseline": bool(ref_dl < BASELINE_GOVERNED_DL
                                 and ref_dl <= ACCEPT_MAX_DL),
        "b_evenodd_survives": bool(evenodd_macro is not None
                                   and evenodd_uses >= 2
                                   and set(evenodd_covered) == set(EVENODD_READINGS)),
        "c_no_macro_explosion": bool(gov["refined"]["inventory"]["count"] <= MAX_MACROS),
        "d_service_byte_identical": bool(service_identical),
        "e_ungoverned_reported": True,   # both arms are in this artifact
    }

    return {
        "baseline_governed_dl": BASELINE_GOVERNED_DL,
        "acceptance_bars": {"max_dl": ACCEPT_MAX_DL,
                            "counterfactual_target": 1989.0,
                            "max_macros": MAX_MACROS},
        "governed": {
            "legacy": gov["legacy"]["inventory"],
            "refined": gov["refined"]["inventory"],
            "delta_dl": round(ref_dl - base_dl, 3),
        },
        "ungoverned": {
            "legacy": ung["legacy"]["inventory"],
            "refined": ung["refined"]["inventory"],
        },
        "congruence_macro": {
            "reference_name": cong_name,
            "reached_by_greedy": bool(cong_in_table),
            "uses": cong_uses,
            "realized_marginal_delta": cong_delta,
        },
        "evenodd_macro": {
            "name": evenodd_macro["name"] if evenodd_macro else None,
            "op_slot_arities": sorted(set(
                recurrence._op_slot_params(evenodd_macro["body"]).values()))
            if evenodd_macro else [],
            "uses": evenodd_uses,
            "covers": sorted(evenodd_covered),
        },
        "congruence_windows": {
            "legacy": _cong_window_count(gexo, "legacy"),
            "refined": _cong_window_count(gexo, "refined"),
            "note": "pass-3 counterpart: force-only math windows unblock the "
                    "congruence cluster (0 -> N); the committed census still "
                    "reports the legacy 0.",
        },
        "service_digest": {"legacy": svc_legacy, "refined": svc_refined,
                           "pinned": "b9f1f0b9bb198732"},
        "verdicts": verdicts,
        "all_pass": all(verdicts.values()),
    }


def render_json(m):
    return json.dumps(m, indent=2, sort_keys=True) + "\n"


def _print_table(m):
    g = m["governed"]
    print("== WP-T3-CK before/after (governed, frozen corpus) ==")
    print(f"  baseline (legacy)  corpus_dl={g['legacy']['corpus_dl']:>8}  "
          f"macros={g['legacy']['count']}")
    print(f"  refined            corpus_dl={g['refined']['corpus_dl']:>8}  "
          f"macros={g['refined']['count']}   delta={g['delta_dl']}")
    print(f"  ungoverned legacy  corpus_dl={m['ungoverned']['legacy']['corpus_dl']:>8}  "
          f"macros={m['ungoverned']['legacy']['count']}")
    print(f"  ungoverned refined corpus_dl={m['ungoverned']['refined']['corpus_dl']:>8}  "
          f"macros={m['ungoverned']['refined']['count']}")
    print("  refined macro inventory:")
    for mm in g["refined"]["macros"]:
        slot = f" op_slots={mm['op_slots']}" if mm["op_slots"] else ""
        print(f"    {mm['name']}  params={mm['params']}  kinds={mm['kinds']}  "
              f"uses={mm['uses']}{slot}")
    c = m["congruence_macro"]
    print(f"  congruence macro {c['reference_name']}: reached={c['reached_by_greedy']} "
          f"uses={c['uses']} realized_delta={c['realized_marginal_delta']}")
    e = m["evenodd_macro"]
    print(f"  even/odd macro {e['name']}: op_slot_arities={e['op_slot_arities']} "
          f"uses={e['uses']} covers={e['covers']}")
    w = m["congruence_windows"]
    print(f"  congruence demand-windows: legacy={w['legacy']} refined={w['refined']}")
    print(f"  service digest legacy/refined/pinned: {m['service_digest']['legacy']} / "
          f"{m['service_digest']['refined']} / {m['service_digest']['pinned']}")
    print("  acceptance verdicts:")
    for k in sorted(m["verdicts"]):
        print(f"    {k}: {'PASS' if m['verdicts'][k] else 'FAIL'}")
    print(f"  ALL PASS: {m['all_pass']}")


def main(argv):
    m = measure()
    with open(OUT_JSON, "w") as fh:
        fh.write(render_json(m))
    if "--print" in argv:
        _print_table(m)
    print(f"wrote {os.path.relpath(OUT_JSON, _ROOT)}  "
          f"(governed {m['governed']['legacy']['corpus_dl']} -> "
          f"{m['governed']['refined']['corpus_dl']}, all_pass={m['all_pass']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

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
baseline, congruence macro reached, even/odd covered, <= MAX_MACROS, service
byte-identical) are what must hold, not the exact 1820.

WP-FLIP (§12.1): `math_mode="refined"` is now the CENSUS-OF-RECORD.  This harness
reports THREE governed tables, in ascending trust: the frozen LEGACY replay
(2920.0, the pre-flip census-of-record, carried as lineage); the refined GREEDY
table (the raw force-only-window + skeleton-key harvest, before GC); and the
refined+GC CENSUS-OF-RECORD (`recurrence.gc_table` retires every macro whose
final-table realized marginal is >= 0 -- the §12.1 adjudication of the +7
congruence drift).  The GC effect is measured explicitly (greedy vs census-of-
record corpus_dl).  The sibling census (tools/tower_census.py) mines in the same
refined census mode and keeps its LEGACY reconstruction only as the frozen
checkpoint's hash-lineage tooth.

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

# The committed baseline -- re-registered across two events, lineage preserved:
#   * WP-AUTH corpus growth: frozen 37-certified corpus 2139.0 -> grown
#     46-certified corpus 2920.0 (baseline reproduced from the LEGACY replay,
#     not assumed).
#   * WP-FLIP (§12.1): `math_mode="refined"` becomes the census-of-record.  The
#     baseline STAYS 2920.0 -- the FROZEN PRE-FLIP census-of-record (the legacy
#     miner over the grown corpus), carried here as LINEAGE.  Post-flip "legacy"
#     is no longer the census-of-record, so the acceptance shape is deliberate:
#     (a) the post-flip refined+GC census-of-record REPRODUCES its committed
#     value (CENSUS_OF_RECORD_DL, pinned below and reproduced live, never
#     assumed) AND clears the frozen legacy bar -- the harness compares refined
#     against the FROZEN LEGACY lineage, never refined against itself.
# Bar semantics preserved across BOTH re-registrations: ACCEPT_MAX_DL is
# baseline minus 29 (the magnitude of the T3 window-rule regression the original
# bar guarded against, §11.10); MAX_MACROS scales with certified readings by the
# original per-reading proportion (8 at 37 -> 10 at 46), and the
# over-fragmentation judgment is now ENFORCED by the re-mine-time GC pass
# (recurrence.gc_table), not merely weighed by this bar.
BASELINE_GOVERNED_DL = 2920.0   # frozen PRE-flip census-of-record (legacy), lineage
CENSUS_OF_RECORD_DL = 2377.0    # POST-flip census-of-record (refined + gc_table)
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

    # Governed arm: LEGACY lineage, refined GREEDY (pre-GC), refined+GC
    # CENSUS-OF-RECORD (WP-FLIP §12.1).  gc_table retires every macro whose
    # final-table realized marginal is >= 0 (the +7 congruence-drift adjudication).
    leg_table, gexo = _replay(records, "governed", True, dream, "legacy")
    ref_greedy, gexo = _replay(records, "governed", True, dream, "refined")
    ref_table = dict(ref_greedy)                         # the census-of-record
    gc_retired = recurrence.gc_table(ref_table, gexo)
    gov = {
        "legacy": _inventory(leg_table, gexo),
        "refined_greedy": _inventory(ref_greedy, gexo),
        "refined": _inventory(ref_table, gexo),
    }
    # Ungoverned arm (comparison, same shape): legacy + refined+GC census.
    uleg, uexo = _replay(records, "ungoverned", False, dream, "legacy")
    uref_greedy, uexo = _replay(records, "ungoverned", False, dream, "refined")
    uref_table = dict(uref_greedy)
    recurrence.gc_table(uref_table, uexo)
    ung = {"legacy": _inventory(uleg, uexo),
           "refined": _inventory(uref_table, uexo)}

    base_dl = gov["legacy"]["corpus_dl"]
    greedy_dl = gov["refined_greedy"]["corpus_dl"]
    ref_dl = gov["refined"]["corpus_dl"]

    # --- congruence macro: the greedy path reaches the census's -179 body; the
    #     final-table GC then adjudicates its realized marginal.  reached_by_greedy
    #     and realized_marginal are measured on the GREEDY table (pre-GC); the GC
    #     verdict (retired iff realized marginal >= 0) is reported alongside. ---
    cong_name = _congruence_reference_name(gexo)
    cong_reached = cong_name in ref_greedy
    cong_uses = next((m["uses"] for m in gov["refined_greedy"]["macros"]
                      if m["name"] == cong_name), 0)
    cong_delta = None
    if cong_reached:
        trial = {k: v for k, v in ref_greedy.items() if k != cong_name}
        cong_delta = round(mdl_macros.corpus_dl(gexo, ref_greedy)["total"]
                           - mdl_macros.corpus_dl(gexo, trial)["total"], 3)
    cong_retired = cong_name in gc_retired

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
        inv = gov["refined"]["macros"]
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

    # --- acceptance verdicts ---
    #   (a) is TWO honest checks: the post-flip refined+GC census-of-record
    #   REPRODUCES its committed value (never compared against itself), AND it
    #   clears the FROZEN LEGACY lineage bar (baseline and baseline-29).
    verdicts = {
        "a_reproduces_census_of_record": bool(ref_dl == CENSUS_OF_RECORD_DL),
        "a_beats_baseline": bool(ref_dl < BASELINE_GOVERNED_DL
                                 and ref_dl <= ACCEPT_MAX_DL),
        "b_evenodd_survives": bool(evenodd_macro is not None
                                   and evenodd_uses >= 2
                                   and set(evenodd_covered) == set(EVENODD_READINGS)),
        "c_no_macro_explosion": bool(gov["refined"]["count"] <= MAX_MACROS),
        "d_service_byte_identical": bool(service_identical),
        "e_ungoverned_reported": True,   # both arms are in this artifact
    }

    return {
        "baseline_governed_dl": BASELINE_GOVERNED_DL,
        "census_of_record_dl": CENSUS_OF_RECORD_DL,
        "acceptance_bars": {"max_dl": ACCEPT_MAX_DL,
                            "counterfactual_target": 1989.0,
                            "max_macros": MAX_MACROS},
        "governed": {
            "legacy": gov["legacy"],
            "refined_greedy": gov["refined_greedy"],
            "refined": gov["refined"],
            "delta_dl": round(ref_dl - base_dl, 3),
        },
        "gc_pass": {
            "law": "retire iff realized_marginal_delta >= 0 (threshold 0, a law)",
            "retired": sorted(gc_retired),
            "governed_dl_before_gc": greedy_dl,
            "governed_dl_after_gc": ref_dl,
            "gc_delta": round(ref_dl - greedy_dl, 3),
        },
        "ungoverned": {
            "legacy": ung["legacy"],
            "refined": ung["refined"],
        },
        "congruence_macro": {
            "reference_name": cong_name,
            "reached_by_greedy": bool(cong_reached),
            "uses": cong_uses,
            "realized_marginal_delta": cong_delta,
            "retired_by_gc": bool(cong_retired),
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
                    "congruence cluster (0 -> N); post-WP-FLIP the census-of-"
                    "record IS refined, so tower_census now reports the >0 count.",
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
    print(f"  refined greedy     corpus_dl={g['refined_greedy']['corpus_dl']:>8}  "
          f"macros={g['refined_greedy']['count']}")
    gc = m["gc_pass"]
    print(f"  refined+GC census  corpus_dl={g['refined']['corpus_dl']:>8}  "
          f"macros={g['refined']['count']}   delta={g['delta_dl']}  "
          f"(gc {gc['gc_delta']}, retired {gc['retired']})")
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
          f"uses={c['uses']} realized_delta={c['realized_marginal_delta']} "
          f"retired_by_gc={c['retired_by_gc']}")
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

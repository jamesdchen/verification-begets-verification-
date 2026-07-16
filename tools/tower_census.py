#!/usr/bin/env python3
"""WP-CENSUS: the measurement that gates WP-T1 and re-scopes WP-T4.

This tool REPORTS numbers; it decides nothing.  It reconstructs each arm's
final macro table from the committed checkpoint by replaying the recorded
waves through TODAY'S miner (the same greedy grow the bench uses), then runs
four census/measurement passes whose raw outputs the plan's pre-registered
gates (COMPRESSION.md §11.2/§11.3/§11.4) read against their bars.

Passes:
  1. Table reconstruction + wave-hash verification (loud on any mismatch).
  2. Tower census (gates T1, §11.2): rewrite the governed corpus with the
     final flat table, then census ADJACENT INVOCATION-PAIR recurrences in the
     rewritten stream -- for every adjacent (macro|statement) pair, the count
     of distinct exogenous readings witnessing it.  Context for readers, not a
     decision: §11.2 says a level-2 macro needs roughly >=7 witnesses to pay
     under the current currency.
  3. Slot measurement (§11.3): the congruence-triple [h1,h2,c] statements
     anti-unified via recurrence._antiunify, priced via
     mdl_macros.macro_admission_decision against the final governed table --
     the -179 number, plus per-op flat variants, plus _demand_windows output
     (the zero-window blocker) made into committed numbers.
  4. Subtree census (§11.4): recurring `pred` subtrees across certified
     governed readings at three abstraction levels (exact bytes / refs
     abstracted / refs+lits abstracted), with witness counts and a
     single-kernel-atom-alias flag; how many non-alias candidates clear >=2.

Determinism: no timestamps, no randomness; same checkpoint -> byte-identical
JSON and Markdown.  Everything is sorted; witnesses are identified by stable
source_id.  Reuses bench/miner functions READ-ONLY -- this file adds nothing
to the currency and changes no existing behaviour.

Usage:
    tools/tower_census.py                     # writes results/tower_census.{json,md}
    tools/tower_census.py --print             # also echo the human summary
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import common                                   # noqa: E402
import bench_formalize as bench                 # noqa: E402
from buildloop import recurrence, mdl_macros    # noqa: E402

CHECKPOINT = os.path.join(_ROOT, "results", "formalize_bench_state.jsonl")
OUT_JSON = os.path.join(_ROOT, "results", "tower_census.json")
OUT_MD = os.path.join(_ROOT, "results", "tower_census.md")

# The kernel's atom + term operator vocabulary (generators/math_eval.py): a
# subtree that is one of these applied directly to bare leaves (ref/lit) is a
# trivial alias of a kernel operator -- §11.4 Critical 1's `divides_alias`
# hazard -- and is flagged, not counted as a non-trivial T4 candidate.
KERNEL_OPS = frozenset({
    "=", "!=", "<=", "<", "dvd", "even", "odd", "coprime", "and", "or",
    "implies", "+", "*", "-", "%", "mod", "^", "gcd",
})

# The congruence triple whose [h1,h2,c] window carries the -179 (§11.3 / §7).
CONG_TRIPLE = ("33_cong_add", "34_cong_mul", "35_cong_sub")
CONG_WINDOW_IDS = ("h1", "h2", "c")

# §11.2 pre-registered context: level-2 macro pays at roughly this many
# witnesses under the current currency.  REPORTED beside the measurement --
# the tool does not apply it.
LEVEL2_WITNESS_BAR = 7


# ============================================================ checkpoint load
def _load_records(path=CHECKPOINT):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _dream_readings(records):
    """The system-origin dream readings, in author order (they join ONLY the
    ungoverned arm's mining corpus -- bench._run_arm)."""
    by_sid = {r["source_id"]: r for r in records if r["arm"] == "dream"}
    out = []
    for sid, txt in bench._dream_sources():
        rec = by_sid.get(sid)
        if rec is None:
            continue
        doc = bench._reading_doc(rec, txt, origin="system")
        if doc is not None:
            doc["_sid"] = sid
            out.append(doc)
    return out


def _replay_arm(records, arm, governed, dream_readings):
    """Reconstruct one arm's final macro table by replaying its waves through
    today's miner, exactly as bench._run_arm does: freeze the pre-wave table,
    accumulate the wave's authored readings, greedy-grow.  Returns
    (final_table, exo_readings, hash_report).

    hash_report verifies each wave's RECORDED table_hash against the hash of
    the table we reconstructed at the START of that wave -- the replay's proof
    it matches the committed run."""
    sources = bench._corpus_sources()
    wfilter = bench._EXO if governed else None
    waves = [sources[i:i + bench.WAVE_SIZE]
             for i in range(0, len(sources), bench.WAVE_SIZE)]
    arm_recs = {r["source_id"]: r for r in records if r["arm"] == arm}

    table: dict = {}
    exo: list = []
    hash_report = []
    for wi, wave in enumerate(waves):
        computed = bench._table_hash(dict(table))            # pre-wave snapshot
        recorded = sorted({r["table_hash"] for r in records
                           if r["arm"] == arm and r["wave"] == wi})
        match = (len(recorded) == 1 and recorded[0] == computed)
        hash_report.append({
            "wave": wi,
            "computed_table_hash": computed,
            "recorded_table_hash": recorded[0] if len(recorded) == 1 else None,
            "recorded_distinct": recorded,
            "match": bool(match),
        })
        for sid, txt in wave:
            rec = arm_recs.get(sid)
            if rec is None:
                continue
            doc = bench._reading_doc(rec, txt, origin="exogenous")
            if doc is not None:
                doc["_sid"] = sid
                exo.append(doc)
        corpus = exo + (dream_readings if not governed else [])
        bench._greedy_grow(table, corpus, wfilter)
    return table, exo, hash_report


def _table_summary(table):
    return {
        "count": len(table),
        "macros": [
            {"name": m["name"], "params": list(m.get("params", [])),
             "body_len": len(m["body"]),
             "dl_macro": round(mdl_macros.dl_macro(m), 3)}
            for m in sorted(table.values(), key=lambda m: m["name"])
        ],
    }


# =============================================================== tower census
def _token_stream(reading, table):
    """Greedily rewrite a reading's statement stream with the final flat table
    (longest body first, then name -- MIRRORING mdl_macros._reading_stats) and
    return the resulting token stream: 'M:<name>' for a macro invocation,
    'S:<lf-kind>' for an unmatched concrete statement.  The invoked NAME is
    folded into the macro token (§11.2 binding: the cluster key carries the
    callee)."""
    stmts = reading["statements"]
    macros = sorted(table.values(), key=lambda m: (-len(m["body"]), m["name"]))
    toks, i = [], 0
    while i < len(stmts):
        hit = next((m for m in macros
                    if mdl_macros._match_at(stmts, i, m) is not None), None)
        if hit is not None:
            toks.append("M:" + hit["name"])
            i += len(hit["body"])
        else:
            lf = mdl_macros._lf_of(stmts[i])
            kind = lf.get("kind") if isinstance(lf, dict) else "?"
            toks.append("S:" + str(kind))
            i += 1
    return toks


def _pair_category(a, b):
    am, bm = a.startswith("M:"), b.startswith("M:")
    if am and bm:
        return "MM"          # macro-macro: the level-2 (tower) target
    if am or bm:
        return "MS"          # macro+statement
    return "SS"              # statement-statement (level-1 territory)


def _tower_census(exo_readings, table):
    """Census adjacent invocation-pair recurrences in the flat-table-rewritten
    stream over the CERTIFIED readings.  Witnesses are distinct source_ids."""
    pair_wit = defaultdict(set)
    for r in exo_readings:
        if not r.get("_certified"):
            continue
        toks = _token_stream(r, table)
        for a, b in zip(toks, toks[1:]):
            pair_wit[(a, b)].add(r["_sid"])

    pairs = []
    for (a, b), wits in pair_wit.items():
        pairs.append({
            "a": a, "b": b,
            "category": _pair_category(a, b),
            "witnesses": len(wits),
            "witness_sids": sorted(wits),
        })
    pairs.sort(key=lambda p: (-p["witnesses"], p["a"], p["b"]))

    def _max_over(cats):
        vals = [p["witnesses"] for p in pairs if p["category"] in cats]
        return max(vals) if vals else 0

    dist = defaultdict(int)
    for p in pairs:
        dist[p["witnesses"]] += 1

    return {
        "n_certified_readings": sum(1 for r in exo_readings
                                    if r.get("_certified")),
        "level2_witness_bar": LEVEL2_WITNESS_BAR,
        "distinct_adjacent_pairs": len(pairs),
        "max_witness_macro_macro_pair": _max_over({"MM"}),
        "max_witness_any_macro_pair": _max_over({"MM", "MS"}),
        "macro_macro_pairs_at_or_above_bar": sum(
            1 for p in pairs
            if p["category"] == "MM" and p["witnesses"] >= LEVEL2_WITNESS_BAR),
        "any_macro_pairs_at_or_above_bar": sum(
            1 for p in pairs
            if p["category"] in ("MM", "MS")
            and p["witnesses"] >= LEVEL2_WITNESS_BAR),
        "witness_distribution": {str(k): dist[k] for k in sorted(dist)},
        "pairs": pairs,
    }


# =========================================================== slot measurement
def _pick_window(reading, ids):
    smap = {s["id"]: s for s in reading["statements"]}
    if not all(i in smap for i in ids):
        return None
    return [smap[i]["lf"] for i in ids]


def _slot_measurement(exo_readings, table):
    """Reproduce the -179: the congruence-triple [h1,h2,c] statements
    anti-unified into a slotted body, priced against the final governed
    table; plus the per-op flat variants; plus _demand_windows for the three
    readings (the zero-window blocker)."""
    by_sid = {r["_sid"]: r for r in exo_readings}
    triple = [by_sid[sid] for sid in CONG_TRIPLE if sid in by_sid]

    result = {
        "cong_triple": list(CONG_TRIPLE),
        "window_ids": list(CONG_WINDOW_IDS),
        "readings_present": [r["_sid"] for r in triple],
    }
    if len(triple) != len(CONG_TRIPLE):
        result["error"] = "congruence triple not fully present in checkpoint"
        return result

    occ = [_pick_window(r, CONG_WINDOW_IDS) for r in triple]
    body, params = recurrence._antiunify_windows(occ)
    cand = {"name": recurrence._macro_name(body), "params": params,
            "body": body}
    decision = mdl_macros.macro_admission_decision(exo_readings, cand, table)
    result["slot_candidate"] = {"name": cand["name"], "params": params,
                                "body": body}
    result["slot_admission"] = decision

    flats = []
    for r in triple:
        fbody = _pick_window(r, CONG_WINDOW_IDS)
        fcand = {"name": recurrence._macro_name(fbody), "params": [],
                 "body": fbody}
        fdec = mdl_macros.macro_admission_decision(exo_readings, fcand, table)
        flats.append({"sid": r["_sid"], "name": fcand["name"],
                      "admission": fdec})
    result["flat_variants"] = flats

    windows = []
    for r in triple:
        ws = recurrence._demand_windows(r, recurrence.DEFAULT_MAX_LEN)
        spans = [[s["id"] for s in w] for w in ws]
        covering = [sp for sp in spans
                    if set(CONG_WINDOW_IDS).issubset(set(sp))]
        windows.append({"sid": r["_sid"], "n_windows": len(ws),
                        "spans": spans,
                        "spans_covering_window": len(covering)})
    result["demand_windows"] = windows
    result["total_windows_covering_cong_cluster"] = sum(
        w["spans_covering_window"] for w in windows)
    return result


# ============================================================ subtree census
def _is_leaf(node):
    return isinstance(node, dict) and ("ref" in node or "lit" in node)


def _is_single_kernel_atom_alias(node):
    """A subtree that is one kernel operator applied to bare leaves -- a
    trivial alias of that operator (§11.4 Critical 1)."""
    return (isinstance(node, dict) and "op" in node
            and node["op"] in KERNEL_OPS
            and bool(node.get("args"))
            and all(_is_leaf(a) for a in node["args"]))


def _abstract(node, level):
    """level 0: exact; level 1: refs -> {"ref":"*"}; level 2: refs+lits."""
    if isinstance(node, dict):
        if "ref" in node and level >= 1:
            return {"ref": "*"}
        if "lit" in node and level >= 2:
            return {"lit": "*"}
        return {k: _abstract(v, level) for k, v in node.items()}
    if isinstance(node, list):
        return [_abstract(x, level) for x in node]
    return node


def _op_subtrees(node):
    """Every op-rooted subtree within a pred (the top predicate and every
    nested term operator)."""
    if isinstance(node, dict):
        if "op" in node:
            yield node
        for v in node.values():
            yield from _op_subtrees(v)
    elif isinstance(node, list):
        for v in node:
            yield from _op_subtrees(v)


def _subtree_census(exo_readings):
    certified = [r for r in exo_readings if r.get("_certified")]
    levels = {}
    for level in (0, 1, 2):
        wit = defaultdict(set)
        alias = {}
        for r in certified:
            for s in r["statements"]:
                pred = s["lf"].get("pred")
                if pred is None:
                    continue
                for st in _op_subtrees(pred):
                    key = common.canonical_json(_abstract(st, level))
                    wit[key].add(r["_sid"])
                    alias[key] = _is_single_kernel_atom_alias(st)
        cands = []
        for key, sids in wit.items():
            if len(sids) < 2:
                continue
            cands.append({"subtree": key, "witnesses": len(sids),
                          "witness_sids": sorted(sids),
                          "single_kernel_atom_alias": alias[key]})
        cands.sort(key=lambda c: (-c["witnesses"],
                                  c["single_kernel_atom_alias"], c["subtree"]))
        nonalias = [c for c in cands if not c["single_kernel_atom_alias"]]
        levels[str(level)] = {
            "distinct_subtrees": len(wit),
            "at_least_2_witnesses": len(cands),
            "alias_at_least_2": len(cands) - len(nonalias),
            "nonalias_at_least_2": len(nonalias),
            "candidates": cands,
        }
    return {
        "n_certified_readings": len(certified),
        "abstraction_levels": {"0": "exact-bytes", "1": "refs-abstracted",
                               "2": "refs+lits-abstracted"},
        "levels": levels,
    }


# =================================================================== assembly
def build_census(checkpoint=CHECKPOINT):
    records = _load_records(checkpoint)
    dreams = _dream_readings(records)

    gtab, gexo, ghash = _replay_arm(records, "governed", True, dreams)
    utab, uexo, uhash = _replay_arm(records, "ungoverned", False, dreams)

    all_hash_ok = all(h["match"] for h in ghash) and \
        all(h["match"] for h in uhash)

    census = {
        "artifact": "tower_census",
        "checkpoint": os.path.relpath(checkpoint, _ROOT),
        "records": {
            "total": len(records),
            "by_arm": {arm: sum(1 for r in records if r["arm"] == arm)
                       for arm in sorted({r["arm"] for r in records})},
            "waves": sorted({r["wave"] for r in records}),
        },
        "hash_verification": {
            "all_waves_match": bool(all_hash_ok),
            "governed": ghash,
            "ungoverned": uhash,
        },
        "final_tables": {
            "governed": {**_table_summary(gtab),
                         "corpus_dl": round(
                             mdl_macros.corpus_dl(gexo, gtab)["total"], 3)},
            "ungoverned": {**_table_summary(utab),
                           "corpus_dl": round(
                               mdl_macros.corpus_dl(uexo, utab)["total"], 3)},
        },
        # gates T1 (§11.2) -- the governed corpus is the gate corpus
        "tower_census": {
            "gate": "WP-T1 (COMPRESSION.md §11.2)",
            "governed": _tower_census(gexo, gtab),
            "ungoverned": _tower_census(uexo, utab),
        },
        # re-scopes / measures T3 (§11.3)
        "slot_measurement": {
            "gate": "WP-T3 (COMPRESSION.md §11.3)",
            "governed": _slot_measurement(gexo, gtab),
        },
        # re-scopes T4 (§11.4)
        "subtree_census": {
            "gate": "WP-T4 (COMPRESSION.md §11.4)",
            "governed": _subtree_census(gexo),
        },
    }
    return census


# ============================================================= serialization
def render_json(census):
    return json.dumps(census, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def _fmt_pairs(pairs, cats, limit=None):
    rows = [p for p in pairs if p["category"] in cats]
    if limit is not None:
        rows = rows[:limit]
    out = []
    for p in rows:
        out.append(f"  {p['category']}  {p['a']} + {p['b']}  "
                   f"->  {p['witnesses']} witnesses")
    return "\n".join(out) if out else "  (none)"


def render_md(census):
    g = census["final_tables"]["governed"]
    u = census["final_tables"]["ungoverned"]
    tw = census["tower_census"]["governed"]
    slot = census["slot_measurement"]["governed"]
    sub = census["subtree_census"]["governed"]
    hv = census["hash_verification"]

    lines = []
    W = lines.append
    W("# Tower census (WP-CENSUS)")
    W("")
    W("Measurement artifact for the §11 pre-registered gates. This file "
      "REPORTS numbers; the plan's predicates and humans decide. Reconstructed "
      "by replaying the committed checkpoint's waves through today's miner "
      "(greedy grow, same code path as the bench).")
    W("")
    W(f"- checkpoint: `{census['checkpoint']}` "
      f"({census['records']['total']} records, "
      f"waves {census['records']['waves']})")
    W(f"- wave table-hash verification: "
      f"**{'ALL MATCH' if hv['all_waves_match'] else 'MISMATCH -- SEE JSON'}**")
    W(f"- governed final table: {g['count']} macros, corpus_dl "
      f"{g['corpus_dl']}")
    W(f"- ungoverned final table: {u['count']} macros, corpus_dl "
      f"{u['corpus_dl']}")
    W("")

    W("## 1. Tower census -- gates WP-T1 (§11.2)")
    W("")
    W(f"Adjacent invocation-pair recurrences in the governed corpus rewritten "
      f"with the final flat table, over "
      f"{tw['n_certified_readings']} certified readings. Witnesses = distinct "
      f"exogenous readings.")
    W("")
    W(f"Pre-registered context (§11.2, reported not applied): a level-2 macro "
      f"needs roughly **>= {tw['level2_witness_bar']} witnesses** to pay under "
      f"the current currency.")
    W("")
    W(f"- distinct adjacent pairs: {tw['distinct_adjacent_pairs']}")
    W(f"- **max witnesses, macro-macro (MM) pair: "
      f"{tw['max_witness_macro_macro_pair']}**  (bar: "
      f"{tw['level2_witness_bar']})")
    W(f"- max witnesses, any macro-involving pair (MM or MS): "
      f"{tw['max_witness_any_macro_pair']}")
    W(f"- MM pairs at/above the bar: {tw['macro_macro_pairs_at_or_above_bar']}"
      f"; any-macro pairs at/above the bar: "
      f"{tw['any_macro_pairs_at_or_above_bar']}")
    W("")
    W("Witness distribution (witnesses: #pairs): "
      + ", ".join(f"{k}:{v}" for k, v in tw["witness_distribution"].items()))
    W("")
    W("Macro-macro (MM) pairs -- the level-2 target:")
    W("")
    W("```")
    W(_fmt_pairs(tw["pairs"], {"MM"}))
    W("```")
    W("")
    W("Macro+statement (MS) pairs:")
    W("")
    W("```")
    W(_fmt_pairs(tw["pairs"], {"MS"}))
    W("```")
    W("")

    W("## 2. Slot measurement -- WP-T3 (§11.3)")
    W("")
    adm = slot.get("slot_admission", {})
    W(f"Congruence triple {slot['cong_triple']}, window "
      f"{slot['window_ids']}, anti-unified via recurrence and priced against "
      f"the final governed table:")
    W("")
    W(f"- **delta: {adm.get('delta')}** (dl_before {adm.get('dl_before')} -> "
      f"dl_after {adm.get('dl_after')}); admit: **{adm.get('admit')}**; "
      f"uses: {adm.get('uses')}")
    W(f"- slot params: {slot.get('slot_candidate', {}).get('params')} "
      f"(one operator slot at the conclusion op position)")
    W("")
    W("Per-op flat variants (no slot):")
    W("")
    for fv in slot.get("flat_variants", []):
        fa = fv["admission"]
        W(f"- {fv['sid']}: admit {fa['admit']}, delta {fa['delta']}, "
          f"uses {fa['uses']}")
    W("")
    W(f"`_demand_windows` on the triple (the blocker as a committed number): "
      f"total windows covering the [h1,h2,c] cluster = "
      f"**{slot.get('total_windows_covering_cong_cluster')}** "
      f"(quotes are non-uniform, so no window is proposed):")
    W("")
    for dw in slot.get("demand_windows", []):
        W(f"- {dw['sid']}: {dw['n_windows']} demand windows, "
          f"{dw['spans_covering_window']} covering the cluster")
    W("")

    W("## 3. Subtree census -- WP-T4 (§11.4)")
    W("")
    W(f"Recurring `pred` subtrees across {sub['n_certified_readings']} "
      f"certified governed readings, three abstraction levels. "
      f"Single-kernel-atom-alias = one kernel operator over bare leaves "
      f"(a trivial alias, §11.4 Critical 1).")
    W("")
    W("| level | abstraction | distinct | >=2 wit | alias >=2 | "
      "**non-alias >=2** |")
    W("|---|---|---|---|---|---|")
    for lv in ("0", "1", "2"):
        L = sub["levels"][lv]
        name = sub["abstraction_levels"][lv]
        W(f"| {lv} | {name} | {L['distinct_subtrees']} | "
          f"{L['at_least_2_witnesses']} | {L['alias_at_least_2']} | "
          f"**{L['nonalias_at_least_2']}** |")
    W("")
    W("Non-alias candidates at >= 2 witnesses (exact-bytes level):")
    W("")
    W("```")
    exact = [c for c in sub["levels"]["0"]["candidates"]
             if not c["single_kernel_atom_alias"]]
    if exact:
        for c in exact:
            W(f"  {c['witnesses']}w  {c['subtree']}")
    else:
        W("  (none)")
    W("```")
    W("")
    W("---")
    W("")
    W("Generated by `tools/tower_census.py` from the committed checkpoint; "
      "deterministic (no timestamps, no randomness).")
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    census = build_census()
    js = render_json(census)
    md = render_md(census)
    with open(OUT_JSON, "w") as fh:
        fh.write(js)
    with open(OUT_MD, "w") as fh:
        fh.write(md)

    tw = census["tower_census"]["governed"]
    slot = census["slot_measurement"]["governed"]["slot_admission"]
    sub = census["subtree_census"]["governed"]["levels"]
    hv = census["hash_verification"]["all_waves_match"]
    print(f"tower_census: hash_verify={'OK' if hv else 'MISMATCH'} | "
          f"max MM witnesses={tw['max_witness_macro_macro_pair']} "
          f"(bar {tw['level2_witness_bar']}) | "
          f"slot delta={slot.get('delta')} admit={slot.get('admit')} | "
          f"non-alias subtrees >=2: "
          f"L0={sub['0']['nonalias_at_least_2']} "
          f"L1={sub['1']['nonalias_at_least_2']} "
          f"L2={sub['2']['nonalias_at_least_2']}")
    print(f"wrote {os.path.relpath(OUT_JSON, _ROOT)} and "
          f"{os.path.relpath(OUT_MD, _ROOT)}")
    if "--print" in argv:
        print()
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

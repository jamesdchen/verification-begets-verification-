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
     of distinct exogenous readings witnessing it.  The GATE METRIC is the
     REALIZABLE witness count: a pair counts only where the union of the raw
     statements both invocations cover is uniform in (force, quote) -- the same
     H2 constraint buildloop/recurrence._demand_windows enforces (a macro
     invocation expands with ONE inherited force+quote, so a level-2 body
     spanning a force/quote boundary is unrealizable).  Pass 3 already honors
     this; pass 2 now matches it.  The pre-gate raw adjacency count is kept as
     a clearly-labeled secondary ("raw_adjacent_witnesses"), NOT the gate
     metric.  Context for readers, not a decision: §11.2 says a level-2 macro
     needs roughly >=7 witnesses to pay under the current currency.
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
    tools/tower_census.py --math-mode refined --gapped   # WP-T2E census-of-record
        # ^ engages the NON-GATE gapped-idiom instrument (§12.4) + math_mode
        #   provenance; DEFAULT (no flags) is byte-identical to the committed run.
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


def _greedy_grow(table, corpus, witness_filter, math_mode="legacy"):
    """bench._greedy_grow with the WP-T3-CK `math_mode` threaded through (mirrors
    tools/measure_cluster_key._greedy_grow).  In the DEFAULT "legacy" mode this
    delegates VERBATIM to bench._greedy_grow -- the byte-identity pin, so the
    reconstruction is unchanged and the default census stays byte-for-byte the
    committed artifact.  "refined" swaps in the force-only math windows + the
    op-signature cluster key as ONE unit (recurrence.mine's math_mode)."""
    if math_mode == "legacy":
        bench._greedy_grow(table, corpus, witness_filter)
        return
    while True:
        cands = recurrence.mine(corpus, table, witness_filter=witness_filter,
                                math_mode=math_mode)
        chosen = None
        for c in cands:
            cand = c["candidate"]
            if cand["name"] in table:
                continue
            if mdl_macros.macro_admission_decision(
                    corpus, cand, table, witness_filter=witness_filter)["admit"]:
                chosen = cand
                break
        if chosen is None:
            return
        table[chosen["name"]] = chosen


def _replay_arm(records, arm, governed, dream_readings, math_mode="legacy"):
    """Reconstruct one arm's final macro table by replaying its waves through
    today's miner, exactly as bench._run_arm does: freeze the pre-wave table,
    accumulate the wave's authored readings, greedy-grow.  Returns
    (final_table, exo_readings, hash_report).

    `math_mode` (WP-T2E, COMPRESSION.md §12.4) is threaded to every recurrence
    call the reconstruction makes (via `_greedy_grow`); it DEFAULTS to "legacy",
    which is byte-identical to the committed run (and reuses bench._greedy_grow
    directly).  The recorded wave table_hashes pin the LEGACY miner, so in a
    refined replay the hash_report legitimately reports mismatches (a different
    miner yields a different table) -- the instrument reads the table, not the
    hashes.

    hash_report verifies each wave's RECORDED table_hash against the hash of
    the table we reconstructed at the START of that wave -- the replay's proof
    it matches the committed run."""
    sources = bench._corpus_sources()
    # FROZEN-vs-LIVE (WP-SRC promotion): this census reprocesses the COMMITTED
    # checkpoint, a FROZEN 40-source run.  The live corpus has since grown to 51
    # (11 staged exogenous sources promoted), so bench._corpus_sources() now
    # returns 51 -- but the 11 promoted sources are UNAUTHORED and were never in
    # the checkpoint.  Replaying the live 51 would append phantom waves (sources
    # with no records) whose recorded table_hash is absent, breaking hash
    # verification and shifting the wave tiling away from the committed run.
    # Restrict the replay to exactly the sources the checkpoint recorded, so the
    # census stays a faithful reconstruction of the frozen 40-source run (and its
    # output stays byte-identical to the committed results/tower_census.*).
    recorded_sids = {r["source_id"] for r in records}
    sources = [(sid, txt) for sid, txt in sources if sid in recorded_sids]
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
        _greedy_grow(table, corpus, wfilter, math_mode)
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
def _fq(stmt):
    """The (force, quote) pair a raw statement carries -- the H2 realizability
    coordinates (recurrence._demand_windows uses exactly these)."""
    return (stmt.get("force"), stmt.get("quote", ""))


def _token_stream(reading, table):
    """Greedily rewrite a reading's statement stream with the final flat table
    (longest body first, then name -- MIRRORING mdl_macros._reading_stats) and
    return the resulting token stream.  Each element is a (token, covered) pair:
    token is 'M:<name>' for a macro invocation (which consumes len(body) raw
    statements) or 'S:<lf-kind>' for an unmatched concrete statement (one raw
    statement); covered is the frozenset of (force, quote) pairs of the raw
    statements that token spans.  The invoked NAME is folded into the macro
    token (§11.2 binding: the cluster key carries the callee).  Threading the
    covered (force, quote) set is what lets the pair census apply the H2
    realizability gate (recurrence._demand_windows)."""
    stmts = reading["statements"]
    macros = sorted(table.values(), key=lambda m: (-len(m["body"]), m["name"]))
    toks, i = [], 0
    while i < len(stmts):
        hit = next((m for m in macros
                    if mdl_macros._match_at(stmts, i, m) is not None), None)
        if hit is not None:
            span = stmts[i:i + len(hit["body"])]
            toks.append(("M:" + hit["name"],
                         frozenset(_fq(s) for s in span)))
            i += len(hit["body"])
        else:
            lf = mdl_macros._lf_of(stmts[i])
            kind = lf.get("kind") if isinstance(lf, dict) else "?"
            toks.append(("S:" + str(kind), frozenset({_fq(stmts[i])})))
            i += 1
    return toks


def _pair_category(a, b):
    am, bm = a.startswith("M:"), b.startswith("M:")
    if am and bm:
        return "MM"          # macro-macro: the level-2 (tower) target
    if am or bm:
        return "MS"          # macro+statement
    return "SS"              # statement-statement (level-1 territory)


def _realizable(fq_a, fq_b):
    """H2 realizability (recurrence._demand_windows, verbatim rule): a level-2
    body spanning both invocations is realizable ONLY if the UNION of the raw
    statements both invocations cover is uniform in (force, quote) -- a macro
    invocation expands with ONE inherited force+quote, so a body straddling a
    force/quote boundary is unrealizable as a legal invocation.  Pass 3 of this
    tool honors the same rule; pass 2 must match."""
    return len(fq_a | fq_b) == 1


def _tower_census(exo_readings, table):
    """Census adjacent invocation-pair recurrences in the flat-table-rewritten
    stream over the CERTIFIED readings.  Witnesses are distinct source_ids.

    THE GATE METRIC is the REALIZABLE witness count: a pair witnesses a reading
    only when that adjacency's covered statements are uniform in (force, quote)
    across the union of both invocations (the H2 constraint
    recurrence._demand_windows enforces -- see _realizable).  The raw adjacency
    count is kept as a clearly-labeled secondary ('raw_adjacent_witnesses'),
    which is NOT the gate metric: it double-counts adjacencies whose level-2
    body no single invocation could ever expand to."""
    raw_wit = defaultdict(set)
    real_wit = defaultdict(set)
    for r in exo_readings:
        if not r.get("_certified"):
            continue
        toks = _token_stream(r, table)
        for (ta, fqa), (tb, fqb) in zip(toks, toks[1:]):
            key = (ta, tb)
            raw_wit[key].add(r["_sid"])
            if _realizable(fqa, fqb):
                real_wit[key].add(r["_sid"])

    pairs = []
    for key in set(raw_wit) | set(real_wit):
        a, b = key
        real = real_wit.get(key, set())
        raw = raw_wit.get(key, set())
        pairs.append({
            "a": a, "b": b,
            "category": _pair_category(a, b),
            # THE GATE METRIC -- realizable adjacent witnesses (H2-gated):
            "witnesses": len(real),
            "witness_sids": sorted(real),
            # SECONDARY, NOT THE GATE METRIC -- raw adjacency (ignores H2):
            "raw_adjacent_witnesses": len(raw),
            "raw_adjacent_witness_sids": sorted(raw),
        })
    pairs.sort(key=lambda p: (-p["witnesses"], -p["raw_adjacent_witnesses"],
                              p["a"], p["b"]))

    def _max_over(cats, field="witnesses"):
        vals = [p[field] for p in pairs if p["category"] in cats]
        return max(vals) if vals else 0

    dist = defaultdict(int)          # over the GATE metric (realizable)
    raw_dist = defaultdict(int)      # secondary, over raw adjacency
    for p in pairs:
        dist[p["witnesses"]] += 1
        raw_dist[p["raw_adjacent_witnesses"]] += 1

    return {
        "n_certified_readings": sum(1 for r in exo_readings
                                    if r.get("_certified")),
        "level2_witness_bar": LEVEL2_WITNESS_BAR,
        "gate_metric": "realizable_adjacent_witnesses",
        "gate_metric_note": (
            "witnesses = distinct readings where the adjacency is REALIZABLE "
            "-- its covered statements uniform in (force, quote) across the "
            "union of both invocations (H2, recurrence._demand_windows). "
            "raw_adjacent_* fields are the pre-gate counts, NOT the gate "
            "metric."),
        "distinct_adjacent_pairs": len(pairs),
        # ---- gate metric (realizable) ----
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
        # ---- secondary: raw adjacency (NOT the gate metric) ----
        "raw_adjacent_note": "NOT the gate metric -- pre-H2 raw adjacency.",
        "max_raw_adjacent_witness_macro_macro_pair": _max_over(
            {"MM"}, "raw_adjacent_witnesses"),
        "max_raw_adjacent_witness_any_macro_pair": _max_over(
            {"MM", "MS"}, "raw_adjacent_witnesses"),
        "raw_adjacent_macro_macro_pairs_at_or_above_bar": sum(
            1 for p in pairs
            if p["category"] == "MM"
            and p["raw_adjacent_witnesses"] >= LEVEL2_WITNESS_BAR),
        "raw_adjacent_witness_distribution": {
            str(k): raw_dist[k] for k in sorted(raw_dist)},
        "pairs": pairs,
    }


# ================================================ gapped-idiom instrument (T2E)
# The gapped-idiom gap budget G, FIXED at 1 by registration (COMPRESSION.md
# §12.4 REGISTERED stanza: "G = one statement" -- §11.8's own words, taken from
# the record, never tuned).  `_gapped_idiom_occurrences` carries a `max_gap`
# parameter for honesty of form; the census only ever reports the G=1 count.
GAPPED_IDIOM_G = 1


def _forms_window(kept_stmts, math_mode):
    """True iff `kept_stmts` (in order) satisfy the SAME window-admissibility rule
    the miner enforces -- i.e. `recurrence._demand_windows` proposes a window
    spanning ALL of them.  Reuses that predicate VERBATIM (no parallel force/quote
    logic): a synthetic reading over exactly these statements yields a full-length
    window iff they are uniform in (force, quote) [legacy / service] or force-only
    [refined math].  The math-domain classification carries correctly because a
    non-empty subset of a math reading's statements is still all-math-kind, and a
    subset of a service reading still carries its service kinds."""
    w = len(kept_stmts)
    if w < 2:
        return False
    fake = {"statements": list(kept_stmts)}
    wins = recurrence._demand_windows(fake, w, math_mode=math_mode)
    return any(len(win) == w for win in wins)


def _gapped_idiom_occurrences(reading, max_len, max_gap, math_mode):
    """Every gapped-idiom occurrence in one reading (definition in
    `_gapped_idiom_census`).  Yields idiom KEYS -- a reading witnessing the same
    key more than once still counts once (the census de-dups per reading)."""
    stmts = recurrence._statements(reading)
    n = len(stmts)
    out = []
    for i in range(n):
        for width in range(2, max_len + 1):           # flanking (kept) width
            for left in range(1, width):              # >=1 kept stmt each side
                right = width - left
                for gap in range(1, max_gap + 1):     # interposed count (G)
                    end = i + left + gap + right
                    if end > n:
                        continue
                    kept = (list(stmts[i:i + left])
                            + list(stmts[i + left + gap:end]))
                    if not _forms_window(kept, math_mode):
                        continue
                    lfs = [mdl_macros._lf_of(s) for s in kept]
                    if any(not isinstance(lf, dict) for lf in lfs):
                        continue
                    ckey = recurrence._cluster_key(kept, lfs, math_mode)
                    out.append((common.canonical_json(ckey), gap, left))
    return out


def _contiguous_admissible_remaining(readings, table, witness_filter, math_mode):
    """NON-GATE column: how many CONTIGUOUS mine-candidates still clear the
    admission gate (`macro_admission_decision`) against the CURRENT macro `table`
    -- the reconstruction's greedy grow ran to a fixpoint, so this is normally 0,
    and 0 is exactly the first T2 clause ("zero admissible contiguous candidates
    remaining").  Mirrors `_greedy_grow`'s per-candidate check."""
    cands = recurrence.mine(readings, table, witness_filter=witness_filter,
                            math_mode=math_mode)
    n = 0
    for c in cands:
        cand = c["candidate"]
        if cand["name"] in table:
            continue
        if mdl_macros.macro_admission_decision(
                readings, cand, table, witness_filter=witness_filter)["admit"]:
            n += 1
    return n


def _gapped_idiom_census(readings, table, witness_filter, math_mode,
                         *, max_gap=GAPPED_IDIOM_G,
                         max_len=recurrence.DEFAULT_MAX_LEN):
    """NON-GATE measurement instrument for WP-T2E (COMPRESSION.md §12.4).

    A GAPPED IDIOM (G = `max_gap`, registered = 1) is a demand-window pair
    separated by exactly one interposed statement: a span of `flank-width + gap`
    consecutive statements in which a single contiguous block of `gap` statements
    (gap in 1..max_gap) is the interruption and the >=2 FLANKING statements (>=1 on
    each side of the gap) satisfy the SAME window-admissibility rule the miner
    already enforces -- uniform in (force, quote) [legacy / service] or force-only
    [refined math].  That rule is checked by REUSING `recurrence._demand_windows`
    (via `_forms_window`); no parallel force/quote predicate is invented.  A gap
    straddling a force boundary makes the flanks non-uniform, so it never forms an
    idiom.  An idiom is keyed by the miner's OWN cluster key over its flanking
    statements (`recurrence._cluster_key`) plus the gap size and left-flank length,
    so "the same idiom" is the same flanking shape interrupted the same way.

    Witness discipline (E3): a reading witnesses an idiom iff it is an EXOGENOUS,
    certified reading containing >=1 occurrence; DREAM (system-origin) readings
    never witness.  Count per idiom = distinct witnessing source_ids.  This is a
    MEASUREMENT column only -- the T2 predicate is evaluated once, elsewhere."""
    witnesses = defaultdict(set)
    for r in readings:
        if r.get("origin") != "exogenous" or not r.get("_certified"):
            continue                                   # E3: dreams never witness
        for key in set(_gapped_idiom_occurrences(r, max_len, max_gap, math_mode)):
            witnesses[key].add(r["_sid"])

    idioms = []
    for (ckey, gap, left), sids in witnesses.items():
        idioms.append({
            "flank_cluster_key": ckey,
            "gap": gap,
            "left_flank_len": left,
            "witnesses": len(sids),
            "witness_sids": sorted(sids),
        })
    idioms.sort(key=lambda d: (-d["witnesses"], d["gap"], d["left_flank_len"],
                               d["flank_cluster_key"]))
    at_least_2 = sum(1 for d in idioms if d["witnesses"] >= 2)
    return {
        "measurement": "NON-GATE -- WP-T2E gapped-idiom instrument (§12.4)",
        "g": max_gap,
        "max_len": max_len,
        # NON-GATE column: contiguous candidates still admissible vs this table.
        "contiguous_admissible_remaining": _contiguous_admissible_remaining(
            readings, table, witness_filter, math_mode),
        # NON-GATE column: the gapped idioms (list + witness counts).
        "gapped_idioms_g1": idioms,
        "n_distinct_gapped_idioms": len(idioms),
        "gapped_idioms_g1_at_least_2_witnesses": at_least_2,
    }


# =========================================================== slot measurement
def _pick_window(reading, ids):
    smap = {s["id"]: s for s in reading["statements"]}
    if not all(i in smap for i in ids):
        return None
    return [smap[i]["lf"] for i in ids]


def _slot_measurement(exo_readings, table, *, math_mode="legacy"):
    """Reproduce the -179: the congruence-triple [h1,h2,c] statements
    anti-unified into a slotted body, priced against the final governed
    table; plus the per-op flat variants; plus _demand_windows for the three
    readings (the zero-window blocker).

    `math_mode` (WP-T2E, §12.4) is threaded to the `_demand_windows` call;
    "legacy" (default) is byte-identical to the committed run."""
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
        ws = recurrence._demand_windows(r, recurrence.DEFAULT_MAX_LEN,
                                        math_mode=math_mode)
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
def build_census(checkpoint=CHECKPOINT, *, math_mode="legacy",
                 gapped_instrument=False):
    """Build the census dict.

    `math_mode` (WP-T2E, §12.4) is threaded to every recurrence call the census
    makes (reconstruction + slot measurement + the gapped instrument); it
    DEFAULTS to "legacy", which -- together with `gapped_instrument=False` -- makes
    this call BYTE-IDENTICAL to the committed `results/tower_census.json` (the pin).

    `gapped_instrument` (default False) adds the NON-GATE WP-T2E measurement block
    (`gapped_idiom_census`) and a `provenance` field recording the producing
    `math_mode` (so the census-of-record is self-describing).  It is kept OFF by
    default precisely so the default artifact does not change; the orchestrator
    engages it (with math_mode="refined") to produce the post-flip census-of-record
    the T2 predicate is evaluated against -- once, elsewhere."""
    records = _load_records(checkpoint)
    dreams = _dream_readings(records)

    gtab, gexo, ghash = _replay_arm(records, "governed", True, dreams, math_mode)
    utab, uexo, uhash = _replay_arm(records, "ungoverned", False, dreams,
                                    math_mode)

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
            "governed": _slot_measurement(gexo, gtab, math_mode=math_mode),
        },
        # re-scopes T4 (§11.4)
        "subtree_census": {
            "gate": "WP-T4 (COMPRESSION.md §11.4)",
            "governed": _subtree_census(gexo),
        },
    }
    if gapped_instrument:
        # WP-T2E retrofit (COMPRESSION.md §12.4), MEASUREMENT-ONLY.  Added only
        # under the explicit flag so the default census stays byte-identical to
        # the committed artifact; provenance records the producing math_mode so the
        # census-of-record is self-describing.  Neither field gates anything -- the
        # T2 predicate reads them once, elsewhere (the orchestrator, post-flip).
        census["provenance"] = {
            "math_mode": math_mode,
            "gapped_idiom_g": GAPPED_IDIOM_G,
        }
        census["gapped_idiom_census"] = {
            "measurement": "NON-GATE -- WP-T2E (COMPRESSION.md §12.4)",
            "governed": _gapped_idiom_census(gexo, gtab, bench._EXO, math_mode),
            "ungoverned": _gapped_idiom_census(uexo, utab, None, math_mode),
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
                   f"->  {p['witnesses']} realizable witnesses "
                   f"(raw {p['raw_adjacent_witnesses']})")
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
    W(f"**Gate metric = REALIZABLE adjacent witnesses.** A pair witnesses a "
      f"reading only where its covered statements are uniform in (force, quote) "
      f"across the union of both invocations -- the H2 constraint "
      f"`buildloop/recurrence.py:_demand_windows` enforces (a macro invocation "
      f"expands with ONE inherited force+quote, so a level-2 body spanning a "
      f"force/quote boundary is unrealizable). Pass 3 already honors this rule; "
      f"pass 2 now matches it. The pre-gate `raw_adjacent_witnesses` count is "
      f"reported as a secondary column and is **NOT the gate metric**.")
    W("")
    W(f"Pre-registered context (§11.2, reported not applied): a level-2 macro "
      f"needs roughly **>= {tw['level2_witness_bar']} witnesses** to pay under "
      f"the current currency.")
    W("")
    W(f"- distinct adjacent pairs: {tw['distinct_adjacent_pairs']}")
    W(f"- **[GATE] max REALIZABLE witnesses, macro-macro (MM) pair: "
      f"{tw['max_witness_macro_macro_pair']}**  (bar: "
      f"{tw['level2_witness_bar']})")
    W(f"- **[GATE] MM pairs at/above the bar (realizable): "
      f"{tw['macro_macro_pairs_at_or_above_bar']}**; any-macro pairs "
      f"at/above the bar: {tw['any_macro_pairs_at_or_above_bar']}")
    W(f"- max realizable witnesses, any macro-involving pair (MM or MS): "
      f"{tw['max_witness_any_macro_pair']}")
    W("")
    W("Realizable-witness distribution (witnesses: #pairs): "
      + ", ".join(f"{k}:{v}" for k, v in tw["witness_distribution"].items()))
    W("")
    W(f"Secondary (NOT the gate metric) -- pre-H2 raw adjacency: max raw MM = "
      f"{tw['max_raw_adjacent_witness_macro_macro_pair']}, raw MM pairs "
      f">= bar = {tw['raw_adjacent_macro_macro_pairs_at_or_above_bar']}; "
      f"raw distribution: "
      + ", ".join(f"{k}:{v}"
                  for k, v in tw["raw_adjacent_witness_distribution"].items()))
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
    # WP-T2E (§12.4): both flags OFF by default -> byte-identical committed output.
    math_mode = argv[argv.index("--math-mode") + 1] if "--math-mode" in argv \
        else "legacy"
    gapped = "--gapped" in argv
    census = build_census(math_mode=math_mode, gapped_instrument=gapped)
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
          f"max REALIZABLE MM witnesses={tw['max_witness_macro_macro_pair']} "
          f"(bar {tw['level2_witness_bar']}, raw "
          f"{tw['max_raw_adjacent_witness_macro_macro_pair']}) | "
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

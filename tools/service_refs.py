#!/usr/bin/env python3
"""C3 reference stack for the SECOND domain — the committed SERVICE readings.

The math-domain reference stack (`tools/entropy_refs.py` + `tools/ppm_ref.py`)
measured the compression story for the number-theory readings. This is the
same story, told for the OTHER domain the shared miner/macro-table serves:
the hand-authored service readings under `specs/readings/`. Its point is the
profile comparison headline — does the service domain show the same
order-1-sequential-structure surplus the math domain did (the honest adaptive
KT-1 coder coming in WELL under the macro coder's corpus_dl), or a different
profile? Either answer shapes wave-3.

CORPUS (justified). The representative committed service corpus is the 11
top-level `specs/readings/*.json` readings — the hand-authored, already-grounded
service Readings that `cgb._seed_readings` classifies as REAL (exogenous:
each one's `request` byte-matches a committed `specs/requests/*.txt`). This is
the service analogue of the math stack's "governed / certified / EXOGENOUS"
filter: real, exogenous readings only. The `specs/readings/dream/` anchors are
SYSTEM-origin (dreams propose, they do not witness — S5) and are excluded, just
as the math stack excludes the dream arm. They are loaded read-only through the
one committed bridge, `buildloop.reading_corpus.load_readings` (sorted filename
order, pure JSON — deterministic).

TOKEN STREAM (stated; it need not match the math one). `tools/entropy_refs.py`
walks `bench_formalize._structure_tokens`, which is TUNED TO MATH LF shapes: it
reads `carrier`/`type`/`binder` and a math pred AST of the `{op, args:[...]}` /
`{ref} / {lit}` shape. Service LFs are a DISJOINT fragment (kinds
quantity/action/effect/bound/always/order/…; preds of the `{op, left, right}`
shape; structural fields states/transition/input) — so that extractor would
silently drop most service structure. We therefore define our OWN service
structure-token stream, `service_structure_tokens`, and state it in full:

    For each statement, in reading/statement order, emit
        ("kind",  lf.kind)          — the LF kind
        ("force", statement.force)  — the speech-act force
    then walk the rest of the lf (every key except "kind") as a tree, in
    SORTED-key order for determinism, emitting one token per scalar leaf tagged
    by the field key that reaches it: a dict recurses over sorted(keys); a list
    emits each element under the SAME field tag; a scalar leaf `v` reached under
    key `k` emits ("k", v). Tokens are rendered to stable strings "tag=<json>".

This is the faithful service adaptation of `_structure_tokens`' PHILOSOPHY
("statement kinds/forces, pred operators, refs, literals … walked
deterministically") — kinds, forces, effect/cmp/pred operators, referent names,
lifecycle states, and integer literals all become tokens, exactly the structure
the counting DL implicitly uniform-codes — but over the service LF tree rather
than the math one. Deterministic: sorted keys, no clock, no randomness.

SCALING CONVENTION (identical to entropy_refs / ppm_ref / the committed order-0
estimate — units reconciled by RATIO, never by mixing):

    DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|)

with naive_counting_dl = corpus_dl(readings, {}) and log2|A| the uniform
(counting-DL) per-token cost. Order-k plug-in uses bits_per_token = H_k; the
adaptive coders reuse ppm_ref's exact estimators (KT add-1/2, Laplace add-1)
with bits_per_token = total_adaptive_bits / N; the LZ77 proxy uses the standard
z*(log2 N + log2|A|)/N phrase cost. No tuned constants.

corpus_dl for the service domain. No committed artifact carries a LIVE service
macro table (`artifacts/registry.sqlite` has zero macros; the only persisted
macros anywhere are the m9 planted-teeth fixtures). So the reported service
corpus_dl is under a FRESH mine — `recurrence.searched_macro_sequence` (the
beam-searched admission sequence, the same deterministic gate the loop uses),
stated as such. It is not a frozen checkpoint value; it is recomputed here.

CAVEATS (same discipline as the math stack, kept in force in the md): the
plug-in H_k lines are IN-SAMPLE maximum-likelihood entropies that pay no
learning cost and are downward-biased (optimistic) — read against the
context-count statistics, never as floors. The adaptive KT/Laplace coders are
STANDARD but not optimal (no PPM escape, no cross-order mixing, no CTW). All
outputs are hindsight, in-sample, on an 11-reading corpus with zero
generalization power (§11.7); references, never floors (§10.2).

Deterministic: no timestamps, no randomness, byte-stable output (the test
asserts committed == fresh).
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from buildloop import mdl_macros, recurrence  # noqa: E402
from buildloop.reading_corpus import load_readings  # noqa: E402

READINGS_DIR = _REPO / "specs" / "readings"
ENTROPY_REFS_JSON = _REPO / "results" / "entropy_refs.json"
PPM_REF_JSON = _REPO / "results" / "ppm_ref.json"
JSON_OUT = _REPO / "results" / "service_refs.json"
MD_OUT = _REPO / "results" / "service_refs.md"

# The two named add-alpha estimators, reproduced verbatim from ppm_ref.py so the
# two domains' adaptive coders cannot drift. No other smoothing constant.
ESTIMATORS = {"kt": 0.5, "laplace": 1.0}
ORDERS = (0, 1, 2)


def load_service_readings(readings_dir: Path = READINGS_DIR) -> list:
    """The committed REAL service readings: the top-level `specs/readings/*.json`
    files (exogenous, request-byte-matched), as mining/pricing docs.

    Excludes the `dream/` subdirectory (system-origin anchors, S5), matching the
    math stack's exogenous-only filter. Sorted filename order (the loader's
    determinism)."""
    docs = []
    for entry in load_readings(readings_dir):
        obj = json.loads(entry.source)
        docs.append({"service": obj["reading"]["service"],
                     "statements": entry.statements})
    return docs


def _token(tag: str, value) -> str:
    """Render one structure token to a stable string. json.dumps with sorted
    keys is deterministic across runs and platforms and orders cleanly for the
    alphabet sort (no str-vs-int comparison hazard)."""
    return tag + "=" + json.dumps(value, sort_keys=True)


def service_structure_tokens(reading: dict) -> list:
    """The service structure-token stream (defined in the module docstring).

    Per statement: ("kind", lf.kind), ("force", force), then a sorted-key tree
    walk of the rest of the lf emitting one token per scalar leaf tagged by its
    reaching field key. Deterministic (sorted keys); returns rendered strings."""
    toks: list = []

    def walk(node, tag: str):
        if isinstance(node, dict):
            for k in sorted(node):
                walk(node[k], k)
        elif isinstance(node, list):
            for v in node:
                walk(v, tag)
        else:
            toks.append(_token(tag, node))

    for s in reading.get("statements", []):
        lf = s.get("lf", {})
        toks.append(_token("kind", lf.get("kind")))
        toks.append(_token("force", s.get("force")))
        for k in sorted(lf):
            if k == "kind":
                continue
            walk(lf[k], k)
    return toks


def token_stream(docs: list) -> list:
    toks: list = []
    for d in docs:
        toks.extend(service_structure_tokens(d))
    return toks


def reading_token_lists(docs: list) -> list:
    return [service_structure_tokens(d) for d in docs]


# ------------------------------------------------------------- order-k plug-in
def order_k_entropy(toks: list, k: int) -> float:
    """Empirical order-k entropy in bits/token (entropy_refs.order_k_entropy,
    reproduced so both domains use the identical estimator)."""
    if not toks:
        return 0.0
    if k == 0:
        n = len(toks)
        freq = Counter(toks)
        return -sum((c / n) * math.log2(c / n) for c in freq.values())
    ctx = Counter()
    joint = Counter()
    for i in range(k, len(toks)):
        c = tuple(toks[i - k:i])
        ctx[c] += 1
        joint[(c, toks[i])] += 1
    total = sum(joint.values())
    if total == 0:
        return 0.0
    h = 0.0
    for (c, s), cnt in joint.items():
        p_joint = cnt / total
        p_cond = cnt / ctx[c]
        h -= p_joint * math.log2(p_cond)
    return h


def context_stats(toks: list, k: int) -> dict:
    """Order-k context-count statistics (entropy_refs.context_stats): a context
    seen once predicts its successor with probability 1 (0 bits), so a high
    singleton fraction makes the plug-in H_k optimistically low."""
    if k < 1 or len(toks) <= k:
        return {"distinct_contexts": 0, "singleton_contexts": 0,
                "singleton_fraction": 0.0, "predictions": 0,
                "predictions_from_singletons": 0,
                "prediction_singleton_fraction": 0.0}
    ctx = Counter()
    for i in range(k, len(toks)):
        ctx[tuple(toks[i - k:i])] += 1
    distinct = len(ctx)
    singletons = sum(1 for v in ctx.values() if v == 1)
    predictions = sum(ctx.values())
    return {
        "distinct_contexts": distinct,
        "singleton_contexts": singletons,
        "singleton_fraction": round(singletons / distinct, 4) if distinct else 0.0,
        "predictions": predictions,
        "predictions_from_singletons": singletons,
        "prediction_singleton_fraction": round(
            singletons / predictions, 4) if predictions else 0.0,
    }


# ----------------------------------------------------------------- adaptive KT
def adaptive_code(toks: list, k: int, alpha: float, alphabet_size: int):
    """Sequential adaptive order-k code (ppm_ref.adaptive_code, verbatim): charge
    x_i = -log2 p(x_i | c), p the add-`alpha` estimate from counts so far in the
    order-k context, denominator over the FULL alphabet. All N tokens charged."""
    counts: dict = {}
    ctx_total: dict = {}
    denom_const = alpha * alphabet_size
    total_bits = 0.0
    for i, s in enumerate(toks):
        ctx = tuple(toks[max(0, i - k):i])
        sub = counts.get(ctx)
        n_s = sub.get(s, 0) if sub is not None else 0
        n_c = ctx_total.get(ctx, 0)
        p = (n_s + alpha) / (n_c + denom_const)
        total_bits += -math.log2(p)
        if sub is None:
            counts[ctx] = {s: 1}
        else:
            sub[s] = n_s + 1
        ctx_total[ctx] = n_c + 1
    return total_bits


# ---------------------------------------------------------------- LZ77 proxy
def lz77_phrase_count(toks: list) -> int:
    """Greedy longest-match self-referential LZ77 factorization
    (entropy_refs.lz77_phrase_count, verbatim)."""
    n = len(toks)
    i = 0
    z = 0
    while i < n:
        best = 0
        for j in range(0, i):
            l = 0
            while i + l < n and toks[j + l] == toks[i + l]:
                l += 1
            if l > best:
                best = l
        step = best if best >= 1 else 1
        z += 1
        i += step
    return z


def _load_math_side_by_side() -> dict:
    """Read the committed math reference artifacts (never recompute) for the
    side-by-side. Absent artifacts => the side-by-side is omitted, not faked."""
    out = {}
    if ENTROPY_REFS_JSON.exists():
        e = json.loads(ENTROPY_REFS_JSON.read_text())
        out["entropy_refs"] = {
            "n_readings": e["n_readings"], "stream_length": e["stream_length"],
            "alphabet_size": e["alphabet_size"],
            "naive_counting_dl": e["naive_counting_dl"],
            "corpus_dl": e["corpus_dl"],
            "DL0": e["order_k"]["DL0"], "DL1": e["order_k"]["DL1"],
            "DL2": e["order_k"]["DL2"],
            "lz77_proxy_DL": e["lz77_proxy"]["DL_lz77_proxy"]}
    if PPM_REF_JSON.exists():
        p = json.loads(PPM_REF_JSON.read_text())
        out["ppm_ref"] = {
            "kt": {k: p["results"]["kt"][k]["adaptive_DL"] for k in ("0", "1", "2")},
            "laplace": {k: p["results"]["laplace"][k]["adaptive_DL"]
                        for k in ("0", "1", "2")},
            "best_adaptive": p["headline"]["best_adaptive"]}
    return out


def compute() -> dict:
    docs = load_service_readings()
    reading_lists = reading_token_lists(docs)
    reading_lens = [len(t) for t in reading_lists]
    toks = [t for rt in reading_lists for t in rt]
    n = len(toks)
    alphabet = sorted(set(toks))
    a = len(alphabet)
    log2_a = math.log2(a) if a > 1 else 1.0

    naive = mdl_macros.corpus_dl(docs, {})["total"]

    # Fresh mine (no committed live service macro table) — stated as such.
    macro_table = recurrence.searched_macro_sequence(docs, {})
    corpus_stats = mdl_macros.corpus_dl(docs, macro_table)
    corpus_dl = corpus_stats["total"]

    def scaled_dl(bits_per_token: float) -> float:
        return naive * (bits_per_token / log2_a) if log2_a else 0.0

    h = {k: order_k_entropy(toks, k) for k in ORDERS}
    plugin_dl = {k: scaled_dl(h[k]) for k in ORDERS}

    ctx1 = context_stats(toks, 1)
    ctx2 = context_stats(toks, 2)

    z = lz77_phrase_count(toks)
    lz_bits = z * (math.log2(n) + log2_a) if n > 0 else 0.0
    lz_bpt = (lz_bits / n) if n > 0 else 0.0
    dl_lz = scaled_dl(lz_bpt)

    # Adaptive coders (KT headline, Laplace sensitivity).
    adaptive: dict = {}
    for est, alpha in ESTIMATORS.items():
        adaptive[est] = {}
        for k in ORDERS:
            total_bits = adaptive_code(toks, k, alpha, a)
            bpt = total_bits / n if n else 0.0
            dl = scaled_dl(bpt)
            adaptive[est][str(k)] = {
                "total_bits": round(total_bits, 6),
                "bits_per_token": round(bpt, 6),
                "adaptive_DL": round(dl, 3),
                "plugin_DL": round(plugin_dl[k], 3),
                "plugin_H_bits_per_token": round(h[k], 6),
                "adaptive_minus_corpus_dl": round(dl - corpus_dl, 3),
                "beats_corpus_dl": bool(dl < corpus_dl),
            }

    # Best honest adaptive coder, and whether ANY beats the macro coder.
    best_est = best_k = None
    best_dl = None
    any_beat = False
    for est in ESTIMATORS:
        for k in ORDERS:
            row = adaptive[est][str(k)]
            if row["beats_corpus_dl"]:
                any_beat = True
            if best_dl is None or row["adaptive_DL"] < best_dl:
                best_dl = row["adaptive_DL"]
                best_est, best_k = est, k

    math_side = _load_math_side_by_side()
    math_best = (math_side.get("ppm_ref", {}) or {}).get("best_adaptive")

    # Profile comparison headline: the order-1 surplus, service vs math, as the
    # fraction by which the best adaptive order-1 coder undercuts corpus_dl.
    svc_kt1 = adaptive["kt"]["1"]["adaptive_DL"]
    svc_surplus_pct = round(100.0 * (corpus_dl - svc_kt1) / corpus_dl, 3) \
        if corpus_dl else 0.0
    math_surplus_pct = None
    if math_best and math_best.get("order_k") == 1:
        m_corpus = math_best["corpus_dl"]
        math_surplus_pct = round(
            100.0 * (m_corpus - math_best["adaptive_DL"]) / m_corpus, 3) \
            if m_corpus else 0.0

    same_profile = (math_surplus_pct is not None
                    and svc_surplus_pct >= 0.5 * math_surplus_pct)

    return {
        "corpus": "service / real / exogenous (committed specs/readings/*.json)",
        "corpus_choice_rationale": (
            "The 11 top-level specs/readings/*.json readings are the REAL, "
            "exogenous (request-byte-matched) service Readings cgb._seed_readings "
            "certifies — the service analogue of the math stack's "
            "governed/certified/exogenous filter. dream/ anchors are SYSTEM-origin "
            "(S5) and excluded, as the math stack excludes the dream arm."
        ),
        "token_stream_definition": (
            "Per statement: ('kind', lf.kind), ('force', force), then a "
            "sorted-key tree walk of the rest of the lf emitting one token per "
            "scalar leaf tagged by its reaching field key (dict recurses over "
            "sorted keys; list emits each element under the same tag). The "
            "faithful service adaptation of bench_formalize._structure_tokens' "
            "philosophy over the DISJOINT service LF fragment (which that "
            "math-tuned extractor would silently drop). Deterministic."
        ),
        "macro_table_provenance": (
            "FRESH mine via recurrence.searched_macro_sequence (no committed "
            "artifact carries a live service macro table; registry.sqlite has "
            "zero macros). The reported corpus_dl is recomputed here, not a "
            "frozen checkpoint value."
        ),
        "n_readings": len(docs),
        "stream_length": n,
        "alphabet_size": a,
        "reading_token_lengths": reading_lens,
        "uniform_bits_per_token_log2_A": round(log2_a, 6),
        "naive_counting_dl": round(naive, 3),
        "corpus_dl": round(corpus_dl, 3),
        "macros_admitted": sorted(macro_table),
        "n_macros_admitted": len(macro_table),
        "scaling_convention": (
            "DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|); "
            "order-k uses H_k, adaptive uses total_adaptive_bits/N, LZ77 uses "
            "z*(log2 N + log2|A|)/N. Ratio-reconciled, no tuned constants "
            "(identical to entropy_refs / ppm_ref / _order0_entropy_dl_est)."
        ),
        "estimators": {
            "kt": "p(s|c) = (n_c(s) + 1/2) / (N_c + |A|/2)",
            "laplace": "p(s|c) = (n_c(s) + 1) / (N_c + |A|)",
        },
        "order_k_plugin": {
            "H0_bits_per_token": round(h[0], 6),
            "H1_bits_per_token": round(h[1], 6),
            "H2_bits_per_token": round(h[2], 6),
            "DL0": round(plugin_dl[0], 3),
            "DL1": round(plugin_dl[1], 3),
            "DL2": round(plugin_dl[2], 3),
        },
        "context_stats": {"order1": ctx1, "order2": ctx2},
        "lz77_proxy": {
            "z_phrases": z,
            "bits_per_token": round(lz_bpt, 6),
            "DL_lz77_proxy": round(dl_lz, 3),
        },
        "adaptive": adaptive,
        "stack": {
            "naive_counting_dl": round(naive, 3),
            "corpus_dl": round(corpus_dl, 3),
            "plugin_DL0": round(plugin_dl[0], 3),
            "plugin_DL1": round(plugin_dl[1], 3),
            "plugin_DL2": round(plugin_dl[2], 3),
            "kt_DL0": adaptive["kt"]["0"]["adaptive_DL"],
            "kt_DL1": adaptive["kt"]["1"]["adaptive_DL"],
            "kt_DL2": adaptive["kt"]["2"]["adaptive_DL"],
            "lz77_proxy_DL": round(dl_lz, 3),
        },
        "headline": {
            "any_adaptive_order_k_beats_corpus_dl": any_beat,
            "best_adaptive": {
                "estimator": best_est, "order_k": best_k,
                "adaptive_DL": best_dl, "corpus_dl": round(corpus_dl, 3),
                "gap_best_adaptive_minus_corpus_dl": round(best_dl - corpus_dl, 3),
            },
            "service_order1_surplus_pct_of_corpus_dl": svc_surplus_pct,
            "math_order1_surplus_pct_of_corpus_dl": math_surplus_pct,
            "same_profile_as_math": same_profile,
            "profile_verdict": (
                "Service shows the SAME profile as math: a large order-1 surplus "
                f"({svc_surplus_pct}% of corpus_dl)."
                if same_profile else
                "Service shows a DIFFERENT profile: the best honest adaptive "
                "order-1 coder undercuts the macro coder's corpus_dl by only "
                f"{svc_surplus_pct}%"
                + (f" vs the math domain's {math_surplus_pct}%"
                   if math_surplus_pct is not None else "")
                + " — no large order-1 sequential-structure surplus. The service "
                "stream's large, sparse alphabet (many per-service referent "
                "names/literals) leaves order-1 contexts mostly singleton, so "
                "the adaptive context model pays heavy learning cost and barely "
                "improves on the macro/grammar coder."
            ),
        },
        "math_side_by_side": math_side,
        "caveats": {
            "in_sample": (
                "IN-SAMPLE, single 11-reading corpus, hindsight; zero "
                "generalization power (§11.7)."
            ),
            "plugin_optimistic": (
                "The plug-in H_k lines are maximum-likelihood entropies that "
                "pay NO learning cost and are downward-biased. Here "
                f"{ctx1['singleton_contexts']}/{ctx1['distinct_contexts']} "
                f"({round(100 * ctx1['singleton_fraction'], 1)}%) order-1 and "
                f"{ctx2['singleton_contexts']}/{ctx2['distinct_contexts']} "
                f"({round(100 * ctx2['singleton_fraction'], 1)}%) order-2 "
                "contexts are singletons (predict their successor at 0 bits), so "
                "DL1/DL2 are OPTIMISTIC orientation lines, NOT floors."
            ),
            "reference_only": (
                "KT / Laplace are STANDARD estimators, not the best possible "
                "context model (no PPM escape, no cross-order mixing, no CTW). "
                "References, never floors (§10.2)."
            ),
        },
    }


def to_markdown(r: dict) -> str:
    hl = r["headline"]
    ms = r.get("math_side_by_side", {})
    e = ms.get("entropy_refs")
    p = ms.get("ppm_ref")
    ok = r["order_k_plugin"]
    ad = r["adaptive"]
    L = []
    L.append("# Service-domain reference stack (C3) — committed service readings")
    L.append("")
    L.append(
        "The measured compression story for the SECOND domain the shared "
        "miner/macro-table serves: the hand-authored **service** readings under "
        "`specs/readings/`. The math-domain stack lives in `entropy_refs` / "
        "`ppm_ref`; this is its service twin. Orientation references, **not "
        "floors** (§10.2)."
    )
    L.append("")
    L.append("## Corpus & token stream")
    L.append("")
    L.append(f"> **Corpus.** {r['corpus_choice_rationale']}")
    L.append("")
    L.append(f"> **Tokens.** {r['token_stream_definition']}")
    L.append("")
    L.append(f"> **Macro table.** {r['macro_table_provenance']}")
    L.append("")
    L.append("| quantity | value |")
    L.append("| --- | --- |")
    L.append(f"| real exogenous service readings | {r['n_readings']} |")
    L.append(f"| stream length N | {r['stream_length']} |")
    L.append(f"| alphabet size \\|A\\| | {r['alphabet_size']} |")
    L.append(f"| uniform bits/token log2\\|A\\| | "
             f"{r['uniform_bits_per_token_log2_A']} |")
    L.append(f"| naive counting DL (empty table) | {r['naive_counting_dl']} |")
    L.append(f"| corpus_dl (fresh mine, {r['n_macros_admitted']} macro"
             f"{'s' if r['n_macros_admitted'] != 1 else ''}) | {r['corpus_dl']} |")
    L.append("")
    L.append("## Scaling convention")
    L.append("")
    L.append(f"> {r['scaling_convention']}")
    L.append("")
    L.append("## The measured service stack")
    L.append("")
    L.append("| reference | bits/token | DL (counting units) |")
    L.append("| --- | --- | --- |")
    L.append(f"| corpus_dl (fresh macro table) | — | {r['stack']['corpus_dl']} |")
    L.append(f"| order-0 plug-in (memoryless) | {ok['H0_bits_per_token']} | "
             f"{ok['DL0']} |")
    L.append(f"| order-1 plug-in | {ok['H1_bits_per_token']} | {ok['DL1']} |")
    L.append(f"| order-2 plug-in | {ok['H2_bits_per_token']} | {ok['DL2']} |")
    L.append(f"| **adaptive KT order-0** | {ad['kt']['0']['bits_per_token']} | "
             f"**{ad['kt']['0']['adaptive_DL']}** |")
    L.append(f"| **adaptive KT order-1** | {ad['kt']['1']['bits_per_token']} | "
             f"**{ad['kt']['1']['adaptive_DL']}** |")
    L.append(f"| **adaptive KT order-2** | {ad['kt']['2']['bits_per_token']} | "
             f"**{ad['kt']['2']['adaptive_DL']}** |")
    L.append(f"| adaptive Laplace order-1 | "
             f"{ad['laplace']['1']['bits_per_token']} | "
             f"{ad['laplace']['1']['adaptive_DL']} |")
    L.append(f"| LZ77 parse proxy (z = {r['lz77_proxy']['z_phrases']}) | "
             f"{r['lz77_proxy']['bits_per_token']} | "
             f"{r['stack']['lz77_proxy_DL']} |")
    L.append("")
    L.append("(Adaptive DL > plug-in DL_k at each k is expected — the plug-in "
             "line does not pay the learning cost the adaptive coder does.)")
    L.append("")
    L.append("## Context-count statistics (small-sample hazard)")
    L.append("")
    L.append("| order k | distinct contexts | singleton contexts | singleton "
             "fraction |")
    L.append("| --- | --- | --- | --- |")
    for k, key in ((1, "order1"), (2, "order2")):
        cs = r["context_stats"][key]
        L.append(f"| {k} | {cs['distinct_contexts']} | "
                 f"{cs['singleton_contexts']} | {cs['singleton_fraction']} |")
    L.append("")
    L.append("## Math ↔ service, side by side (DL in counting units)")
    L.append("")
    if e and p:
        L.append("| line | MATH (number theory) | SERVICE |")
        L.append("| --- | --- | --- |")
        L.append(f"| readings / N / \\|A\\| | {e['n_readings']} / "
                 f"{e['stream_length']} / {e['alphabet_size']} | "
                 f"{r['n_readings']} / {r['stream_length']} / "
                 f"{r['alphabet_size']} |")
        L.append(f"| naive counting DL | {e['naive_counting_dl']} | "
                 f"{r['naive_counting_dl']} |")
        L.append(f"| corpus_dl (macro coder) | {e['corpus_dl']} | "
                 f"{r['corpus_dl']} |")
        L.append(f"| plug-in DL0 / DL1 / DL2 | {e['DL0']} / {e['DL1']} / "
                 f"{e['DL2']} | {ok['DL0']} / {ok['DL1']} / {ok['DL2']} |")
        L.append(f"| adaptive KT DL0 / DL1 / DL2 | {p['kt']['0']} / "
                 f"{p['kt']['1']} / {p['kt']['2']} | "
                 f"{ad['kt']['0']['adaptive_DL']} / "
                 f"{ad['kt']['1']['adaptive_DL']} / "
                 f"{ad['kt']['2']['adaptive_DL']} |")
        L.append(f"| LZ77 proxy DL | {e['lz77_proxy_DL']} | "
                 f"{r['stack']['lz77_proxy_DL']} |")
    else:
        L.append("_(committed math artifacts entropy_refs.json / ppm_ref.json "
                 "not found; side-by-side omitted rather than faked.)_")
    L.append("")
    L.append("## Headline — the profile question")
    L.append("")
    beats = hl["any_adaptive_order_k_beats_corpus_dl"]
    ba = hl["best_adaptive"]
    L.append(
        "**Does the service domain show the same order-1-sequential-structure "
        "surplus math did?**")
    L.append("")
    L.append(
        f"Best honest adaptive coder: **{ba['estimator'].upper()} order-"
        f"{ba['order_k']}** at DL = **{ba['adaptive_DL']}** "
        f"({ba['gap_best_adaptive_minus_corpus_dl']:+} vs corpus_dl "
        f"{ba['corpus_dl']}). Any adaptive order-k beats corpus_dl: "
        f"**{'YES' if beats else 'NO'}**.")
    L.append("")
    L.append(
        f"Order-1 surplus (how far the best adaptive order-1 coder undercuts "
        f"corpus_dl): **service {hl['service_order1_surplus_pct_of_corpus_dl']}%**"
        + (f" vs **math {hl['math_order1_surplus_pct_of_corpus_dl']}%**."
           if hl['math_order1_surplus_pct_of_corpus_dl'] is not None else "."))
    L.append("")
    L.append(f"> {hl['profile_verdict']}")
    L.append("")
    L.append("## Caveats")
    L.append("")
    for key in ("in_sample", "plugin_optimistic", "reference_only"):
        L.append(f"> {r['caveats'][key]}")
        L.append("")
    return "\n".join(L)


def _dump_json(r: dict) -> str:
    return json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    r = compute()
    JSON_OUT.write_text(_dump_json(r))
    MD_OUT.write_text(to_markdown(r))
    sys.stdout.write(f"wrote {JSON_OUT}\nwrote {MD_OUT}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

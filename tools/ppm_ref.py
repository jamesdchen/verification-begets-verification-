#!/usr/bin/env python3
"""C3 honest adaptive context-model reference for the governed corpus.

Answers §10.7's still-open empirical question -- "dictionary vs context
models on repetitive symbolic streams, empirically" -- on OUR corpus, with
an *adaptive* (prequential) order-k coder. This is the honest complement to
the plug-in H_k lines in tools/entropy_refs.py: the plug-in DL_k values are
in-sample maximum-likelihood entropies that get the whole corpus for free
(no learning cost); an adaptive coder charges the FULL stream, including
every context's first occurrences, so it *pays for learning* exactly as
§10.7's greedy-MDL amendment says a prequential code must.

WHAT THIS IS. For k in {0, 1, 2} we code the committed structure-token
stream sequentially. Token x_i in its order-k context c = x_{i-k..i-1} is
charged -log2 p(x_i | c) where p is estimated from the counts accumulated
SO FAR in context c (a prequential / adaptive plug-in code). Two standard,
tuned-constant-free estimators over the fixed |A|-symbol alphabet:

    KT  (Krichevsky-Trofimov, add-1/2):
        p(s | c) = (n_c(s) + 1/2) / (N_c + |A|/2)
    Laplace (add-1):
        p(s | c) = (n_c(s) + 1)   / (N_c + |A|)

where n_c(s) is the number of times symbol s has already followed context
c, N_c = sum_s n_c(s) is the number of times c has already been seen, and
|A| is the FULL alphabet size (41, fixed and known -- not the running count
of distinct symbols). No smoothing constants beyond these two named
standards; no free parameters. KT is the headline (it is the estimator with
the minimax pointwise-regret pedigree, cited in §10.3 via Grunwald & Roos);
Laplace is reported as a sensitivity row.

BEGINNING-OF-STREAM CONTEXTS. The whole point is to charge all N tokens, so
we never skip the first k. For i < k the full-length context does not yet
exist; we use the available prefix c = x_{max(0,i-k)..i-1}. Thus for
order-2 the stream opens with an empty context (i=0), a length-1 context
(i=1), then length-2 contexts thereafter -- each a distinct entry in the
count tables. Order-0 has the single empty context always.

SAME STREAM, SAME CONVENTIONS AS entropy_refs (mirrored, not modified):

  * Token stream: EXACTLY `bench_formalize._structure_tokens` walked over
    the governed exogenous readings the bench PRICES (`exo_readings`) in
    author order -- the SAME stream entropy_refs uses (all AUTHORED governed
    readings, not just certified; N, |A| read at runtime, never hardcoded).
    We import that extractor read-only and reproduce entropy_refs' reading
    filter verbatim so the two streams cannot drift (the drift guard in main()
    cross-checks N/|A|/n_readings against entropy_refs.json).
  * Counting-DL equivalent: the SAME ratio convention entropy_refs and the
    committed order-0 estimate use --

        DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|)

    with bits_per_token_ref = total_adaptive_bits / N. We READ
    `naive_counting_dl` and `uniform_bits_per_token_log2_A` (= log2|A|)
    FROM results/entropy_refs.json -- no recomputation, no hardcoding -- and
    read the plug-in DL_k and corpus_dl from the same json for the
    side-by-side. Units reconciled by ratio, never mixed.
  * Determinism: no timestamps, no randomness; float ops in a fixed order;
    rounded, sorted-key JSON. Byte-stable across runs (the test asserts it).

CAVEATS (kept in force, see the md): in-sample, single small corpus,
zero generalization power (§11.7). KT / Laplace are STANDARD but NOT the
best possible context model -- there is no PPM escape mechanism, no
back-off/mixing across orders, no CTW. This is a REFERENCE; the numbers say
nothing about optimal context modeling. And the §10.2 REFUTED claims stay
refuted: "early-stopped RePair reaches |S|H_k" (1-2) and "too many
nonterminals provably grows bit-size" (0-3) are NOT relied on here.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Read-only imports -- the same extractor entropy_refs.py imports, so the
# token stream is defined in exactly one place and cannot drift.
from bench.bench_formalize import _structure_tokens, _reading_doc  # noqa: E402

STATE_PATH = _REPO / "results" / "formalize_bench_state.jsonl"
ENTROPY_REFS_JSON = _REPO / "results" / "entropy_refs.json"
JSON_OUT = _REPO / "results" / "ppm_ref.json"
MD_OUT = _REPO / "results" / "ppm_ref.md"

# The two named estimators (add-alpha), keyed by name -> alpha. No other
# smoothing constant is admitted anywhere in this module.
ESTIMATORS = {"kt": 0.5, "laplace": 1.0}
ORDERS = (0, 1, 2)


def load_governed_exo_docs(state_path: Path = STATE_PATH) -> list:
    """The governed EXOGENOUS readings the bench prices, in author order.

    Reproduces `tools.entropy_refs.load_governed_exo_docs` verbatim (governed
    arm, PERSISTED reading -- NOT filtered by `certified`) so both tools walk
    the identical corpus the bench prices (`exo_readings`).  On the frozen
    40-source run authored == certified; on the 51-source continuation they
    differ by the one honest bounded-shadow ∃ refusal (43_larger_integer_
    exists), priced in the corpus DL but not counted as certified coverage."""
    docs = []
    with state_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("arm") != "governed":
                continue
            if not rec.get("reading_json"):
                continue
            doc = _reading_doc(rec, "", origin="exogenous")
            if doc:
                docs.append(doc)
    return docs


def reading_token_lists(docs: list) -> list:
    """`_structure_tokens` per reading, in author order (preserves the
    per-reading boundaries used for the prequential trajectory)."""
    return [_structure_tokens(d) for d in docs]


def adaptive_code(toks: list, k: int, alpha: float, alphabet_size: int):
    """Sequential adaptive order-k code over `toks`.

    Charges token x_i = -log2 p(x_i | c) with p the add-`alpha` estimate
    from the counts accumulated so far in the order-k context
    c = x_{max(0,i-k)..i-1}, denominator over the FULL alphabet of size
    `alphabet_size`. Returns (total_bits, per_token_bits) with ALL len(toks)
    tokens charged (first occurrences included)."""
    counts: dict = {}          # context -> {symbol: count so far}
    ctx_total: dict = {}       # context -> total seen so far
    denom_const = alpha * alphabet_size
    total_bits = 0.0
    per_token_bits = []
    for i, s in enumerate(toks):
        ctx = tuple(toks[max(0, i - k):i])
        sub = counts.get(ctx)
        n_s = sub.get(s, 0) if sub is not None else 0
        n_c = ctx_total.get(ctx, 0)
        p = (n_s + alpha) / (n_c + denom_const)
        bits = -math.log2(p)
        total_bits += bits
        per_token_bits.append(bits)
        if sub is None:
            counts[ctx] = {s: 1}
        else:
            sub[s] = n_s + 1
        ctx_total[ctx] = n_c + 1
    return total_bits, per_token_bits


def prequential_boundaries(per_token_bits: list, reading_lens: list) -> list:
    """Cumulative bits at each of the 37 reading boundaries (in reading
    order): the prequential trajectory shape, one point per reading."""
    out = []
    idx = 0
    cum = 0.0
    for m in reading_lens:
        for _ in range(m):
            cum += per_token_bits[idx]
            idx += 1
        out.append(round(cum, 3))
    return out


def _load_entropy_refs() -> dict:
    """Read the committed entropy_refs artifact (the source of truth for the
    scaling convention and the plug-in / corpus comparators)."""
    return json.loads(ENTROPY_REFS_JSON.read_text())


def compute() -> dict:
    docs = load_governed_exo_docs()
    reading_lists = reading_token_lists(docs)
    reading_lens = [len(t) for t in reading_lists]
    toks = [t for rt in reading_lists for t in rt]
    n = len(toks)
    alphabet = sorted(set(toks))
    a = len(alphabet)

    refs = _load_entropy_refs()
    # READ (never recompute) the scaling inputs and comparators from the
    # committed entropy_refs artifact.
    log2_a = refs["uniform_bits_per_token_log2_A"]
    naive = refs["naive_counting_dl"]
    corpus_dl = refs["corpus_dl"]
    plugin_dl = {0: refs["order_k"]["DL0"],
                 1: refs["order_k"]["DL1"],
                 2: refs["order_k"]["DL2"]}
    plugin_h = {0: refs["order_k"]["H0_bits_per_token"],
                1: refs["order_k"]["H1_bits_per_token"],
                2: refs["order_k"]["H2_bits_per_token"]}

    def scaled_dl(bits_per_token: float) -> float:
        return naive * (bits_per_token / log2_a) if log2_a else 0.0

    results = {}          # estimator -> k -> row
    prequential = {}      # estimator -> k -> [37 cumulative bits]
    for est, alpha in ESTIMATORS.items():
        results[est] = {}
        prequential[est] = {}
        for k in ORDERS:
            total_bits, per_tok = adaptive_code(toks, k, alpha, a)
            bpt = total_bits / n if n else 0.0
            dl = scaled_dl(bpt)
            results[est][str(k)] = {
                "total_bits": round(total_bits, 6),
                "bits_per_token": round(bpt, 6),
                "adaptive_DL": round(dl, 3),
                "plugin_DL": plugin_dl[k],
                "plugin_H_bits_per_token": plugin_h[k],
                "adaptive_minus_plugin_DL": round(dl - plugin_dl[k], 3),
                "adaptive_minus_corpus_dl": round(dl - corpus_dl, 3),
                "beats_corpus_dl": bool(dl < corpus_dl),
            }
            prequential[est][str(k)] = prequential_boundaries(per_tok, reading_lens)

    # The headline: does ANY honest adaptive order-k coder (either estimator)
    # beat the macro coder's corpus_dl?
    best_est = best_k = None
    best_dl = None
    any_beat = False
    for est in ESTIMATORS:
        for k in ORDERS:
            dl = results[est][str(k)]["adaptive_DL"]
            if results[est][str(k)]["beats_corpus_dl"]:
                any_beat = True
            if best_dl is None or dl < best_dl:
                best_dl = dl
                best_est, best_k = est, k

    return {
        "corpus": "governed / certified / exogenous (committed checkpoint)",
        "question": (
            "§10.7 open question, on THIS corpus: does any honest adaptive "
            "(prequential) order-k context coder beat the macro coder's "
            "corpus_dl? Adaptive = charges the full stream including each "
            "context's first occurrences (pays for learning), unlike the "
            "plug-in H_k lines."
        ),
        "n_readings": len(docs),
        "stream_length": n,
        "alphabet_size": a,
        "reading_token_lengths": reading_lens,
        "estimators": {
            "kt": "p(s|c) = (n_c(s) + 1/2) / (N_c + |A|/2)",
            "laplace": "p(s|c) = (n_c(s) + 1) / (N_c + |A|)",
        },
        "scaling_convention": (
            "DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|), "
            "bits_per_token_ref = total_adaptive_bits / N. naive_counting_dl "
            "and log2|A| are READ from results/entropy_refs.json (no "
            "recomputation); identical ratio convention to entropy_refs and "
            "bench_formalize._order0_entropy_dl_est. No tuned constants."
        ),
        "scaling_inputs_from_entropy_refs": {
            "naive_counting_dl": naive,
            "uniform_bits_per_token_log2_A": log2_a,
            "corpus_dl": corpus_dl,
            "plugin_DL0": plugin_dl[0],
            "plugin_DL1": plugin_dl[1],
            "plugin_DL2": plugin_dl[2],
        },
        "results": results,
        "headline": {
            "any_adaptive_order_k_beats_corpus_dl": any_beat,
            "best_adaptive": {
                "estimator": best_est,
                "order_k": best_k,
                "adaptive_DL": best_dl,
                "corpus_dl": corpus_dl,
                "gap_best_adaptive_minus_corpus_dl": round(best_dl - corpus_dl, 3),
            },
        },
        "prequential": prequential,
        "caveats": {
            "in_sample": (
                "IN-SAMPLE, single 37-reading corpus, hindsight; zero "
                "generalization power (§11.7)."
            ),
            "reference_only": (
                "KT / Laplace are STANDARD estimators but NOT the best "
                "possible context model: no PPM escape, no cross-order "
                "back-off/mixing, no CTW. This is a REFERENCE -- the numbers "
                "say nothing about optimal context modeling."
            ),
            "interpretation": (
                "§10.2-consistent: adaptive order-0 pays a pure learning cost "
                "with no context and loses (DL ~2511 > corpus_dl 2139); "
                "order-1 hits the sweet spot -- only 41 contexts, each seen "
                "often enough to converge, so it captures the corpus's "
                "sequential structure and comes in WELL under corpus_dl "
                "despite paying full learning cost (KT DL ~1515); order-2 "
                "splits N over ~164 mostly-rare contexts, so its learning "
                "cost rises again and it regresses relative to order-1 (still "
                "under corpus_dl). So on THIS repetitive small-N corpus an "
                "honest adaptive context model does beat the macro coder at "
                "orders 1-2 -- but note the plug-in H_k lines remain far "
                "below the adaptive DLs (the learning cost the plug-in never "
                "pays is exactly the §10.7 point), and this says nothing "
                "about generalization (§11.7) or about optimal context "
                "models (no PPM/CTW here)."
            ),
            "refuted_claims": (
                "The §10.2 REFUTED claims stay refuted and are NOT relied on: "
                "'early-stopped RePair reaches |S|H_k' (1-2) and 'too many "
                "nonterminals provably grows bit-size' (0-3)."
            ),
        },
    }


def to_markdown(r: dict) -> str:
    si = r["scaling_inputs_from_entropy_refs"]
    corpus_dl = si["corpus_dl"]
    hl = r["headline"]
    L = []
    L.append("# Adaptive context-model reference (C3) — committed governed corpus")
    L.append("")
    L.append(
        "The **honest (adaptive) context-model** complement to the plug-in "
        "H_k lines in `entropy_refs`. Answers §10.7's open empirical question "
        "— dictionary vs context models on a repetitive symbolic stream — on "
        "**this** corpus. Orientation reference, **not a floor** (§10.2)."
    )
    L.append("")
    L.append("## What is charged")
    L.append("")
    L.append(
        "Sequential order-k coding of the committed structure-token stream. "
        "Token x_i in its order-k context c = x_{i-k..i-1} is charged "
        "−log2 p(x_i | c), with p estimated from the counts accumulated **so "
        "far** in context c (a prequential / adaptive plug-in code). The "
        "**full stream is charged — including every context's first "
        "occurrences** — which is the whole point: adaptive coding pays for "
        "learning, unlike the plug-in H_k lines that get the corpus for free. "
        "For i < k the available prefix is used as the context (order-2 opens "
        "with an empty then a length-1 context)."
    )
    L.append("")
    L.append("Two standard, tuned-constant-free estimators over the fixed "
             "|A|-symbol alphabet:")
    L.append("")
    L.append("| estimator | formula |")
    L.append("| --- | --- |")
    L.append(f"| KT (Krichevsky–Trofimov, add-1/2) | {r['estimators']['kt']} |")
    L.append(f"| Laplace (add-1) | {r['estimators']['laplace']} |")
    L.append("")
    L.append(
        "n_c(s) = times s has already followed c; N_c = times c already "
        "seen; |A| = fixed alphabet size (not the running distinct count)."
    )
    L.append("")
    L.append("## Stream")
    L.append("")
    L.append("| quantity | value |")
    L.append("| --- | --- |")
    L.append(f"| certified governed exogenous readings | {r['n_readings']} |")
    L.append(f"| stream length N | {r['stream_length']} |")
    L.append(f"| alphabet size \\|A\\| | {r['alphabet_size']} |")
    L.append("")
    L.append("## Scaling convention")
    L.append("")
    L.append(f"> {r['scaling_convention']}")
    L.append("")
    L.append(
        f"Read from `entropy_refs.json`: naive_counting_dl = "
        f"{si['naive_counting_dl']}, log2\\|A\\| = "
        f"{si['uniform_bits_per_token_log2_A']}, corpus_dl = {corpus_dl}."
    )
    L.append("")
    L.append("## Plug-in vs adaptive, per order k (DL in counting units)")
    L.append("")
    L.append(
        "| k | plug-in H_k (b/tok) | plug-in DL_k | KT b/tok | **KT DL** | "
        "Laplace b/tok | **Laplace DL** | corpus_dl |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for k in (0, 1, 2):
        kt = r["results"]["kt"][str(k)]
        lp = r["results"]["laplace"][str(k)]
        L.append(
            f"| {k} | {kt['plugin_H_bits_per_token']} | {kt['plugin_DL']} | "
            f"{kt['bits_per_token']} | **{kt['adaptive_DL']}** | "
            f"{lp['bits_per_token']} | **{lp['adaptive_DL']}** | "
            f"{corpus_dl} |")
    L.append("")
    L.append(
        "(Adaptive DL > plug-in DL_k at every k is expected and correct — "
        "the plug-in line does not pay the learning cost the adaptive coder "
        "does.)"
    )
    L.append("")
    L.append("## Headline — the §10.7 question, answered on this corpus")
    L.append("")
    beats = hl["any_adaptive_order_k_beats_corpus_dl"]
    ba = hl["best_adaptive"]
    verdict = "YES" if beats else "NO"
    L.append(
        f"**Does ANY honest adaptive order-k coder (either estimator) beat "
        f"corpus_dl = {corpus_dl}? {verdict}.**"
    )
    L.append("")
    L.append(
        f"The best adaptive coder is **{ba['estimator'].upper()} order-"
        f"{ba['order_k']}** at DL = **{ba['adaptive_DL']}** — that is "
        f"{ba['gap_best_adaptive_minus_corpus_dl']:+} vs corpus_dl "
        f"({corpus_dl}). "
        + (
            "So on this corpus an honest adaptive context model does NOT beat "
            "the macro/grammar coder."
            if not beats else
            "So on this corpus an honest adaptive context model DOES beat the "
            "macro/grammar coder."
        )
    )
    L.append("")
    L.append(f"> {r['caveats']['interpretation']}")
    L.append("")
    L.append("## Prequential trajectory")
    L.append("")
    L.append(
        "Cumulative adaptive bits at each of the 37 reading boundaries (in "
        "author order) are emitted in `ppm_ref.json` under `prequential` for "
        "every (estimator, k), so the bench's prequential column gains a "
        "context-model comparator. Endpoints (KT):"
    )
    L.append("")
    L.append("| k | cumulative bits at final reading |")
    L.append("| --- | --- |")
    for k in (0, 1, 2):
        traj = r["prequential"]["kt"][str(k)]
        L.append(f"| {k} | {traj[-1]} |")
    L.append("")
    L.append("## Caveats")
    L.append("")
    L.append(f"> {r['caveats']['in_sample']}")
    L.append("")
    L.append(f"> {r['caveats']['reference_only']}")
    L.append("")
    L.append(f"> {r['caveats']['refuted_claims']}")
    L.append("")
    return "\n".join(L)


def _dump_json(r: dict) -> str:
    return json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    r = compute()
    # DRIFT GUARD (re-baselines automatically): the two tools MUST walk the
    # identical stream, so cross-check our (N, |A|, n_readings) against the
    # committed entropy_refs.json -- the shared source of truth -- instead of a
    # hardcoded frozen-run triple.  A genuine drift (the tools disagreeing on
    # the corpus) still STOPS loudly; a legitimate re-baseline (rerun the bench
    # + entropy_refs, then this tool) passes without a literal to hand-edit.
    refs = _load_entropy_refs()
    expect = (refs["stream_length"], refs["alphabet_size"], refs["n_readings"])
    got = (r["stream_length"], r["alphabet_size"], r["n_readings"])
    if got != expect:
        sys.stderr.write(
            "STOP: stream drift vs entropy_refs.json "
            f"(this tool N/|A|/readings={got}, entropy_refs={expect}); the two "
            "reference tools must walk the identical governed exogenous "
            "stream -- rerun tools/entropy_refs.py first.\n")
        return 1
    JSON_OUT.write_text(_dump_json(r))
    MD_OUT.write_text(to_markdown(r))
    sys.stdout.write(f"wrote {JSON_OUT}\nwrote {MD_OUT}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

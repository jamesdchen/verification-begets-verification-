#!/usr/bin/env python3
"""C3 reference floors for the committed governed corpus.

Reports the *computable* reference lines that make §11.8's T2 predicate
evaluable and §5's "visible headroom" a number: order-k empirical entropy
DLs (k = 0, 1, 2) and a self-referential LZ77-parse proxy, over the exact
structure-token stream the counting DL implicitly uniform-codes.

These are ORIENTATION REFERENCES, not floors for the macro coder. Per
§10.2 (verbatim-ish): "on highly repetitive corpora (plausibly ours)
grammar coders can encode far *below* nH_k -- which is exactly what the
bench measured (2139 < 2450 order-0)." A reported corpus_dl below an
order-k line is EXPECTED, not a bug.

Token stream: EXACTLY `bench_formalize._structure_tokens`, walked over the
37 certified governed exogenous readings in author order -- the same tokens
in the same order that `bench_formalize._order0_entropy_dl_est` uses. We
IMPORT that extractor read-only so the two streams cannot drift; the test
asserts our order-0 line reproduces the committed CSV value to the digit.

SCALING CONVENTION (documented prominently, mirrored from the committed
order-0 estimate -- bench_formalize._order0_entropy_dl_est):

    Every reference DL is the macro-free counting cost `naive` (=
    corpus_dl(readings, {})) scaled by the fraction of the uniform
    per-token code that the reference code actually spends:

        DL_ref = naive * (bits_per_token_ref / log2|A|)

    where log2|A| is the uniform (counting-DL) per-token cost. For the
    order-k lines bits_per_token_ref = H_k (empirical order-k conditional
    entropy). For the LZ77 proxy bits_per_token_ref = LZ_bits / N with
    LZ_bits = z * (log2 N + log2|A|), the standard phrase cost (a phrase
    names a source position, log2 N bits, plus an extending symbol,
    log2|A| bits). No tuned constants: the only inputs are N, |A|, the
    empirical frequencies, and the greedy parse length z.

Units are reconciled by RATIO, never by mixing -- the same discipline the
order-0 estimate documents. All outputs are hindsight, in-sample, and
on a 37-reading corpus carry zero generalization power (§11.7); they are
plotted for orientation and never asserted (E5).

Deterministic: no timestamps, no randomness, byte-stable output.
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

# Read-only imports. `_structure_tokens` is THE token-stream definition we
# must be consistent with (same function the order-0 estimate walks);
# `_reading_doc` builds the mining/pricing doc exactly as the bench does.
from bench_formalize import _structure_tokens, _reading_doc  # noqa: E402
from buildloop import mdl_macros  # noqa: E402

STATE_PATH = _REPO / "results" / "formalize_bench_state.jsonl"
CSV_PATH = _REPO / "results" / "formalize_governed.csv"
JSON_OUT = _REPO / "results" / "entropy_refs.json"
MD_OUT = _REPO / "results" / "entropy_refs.md"


def load_governed_certified_docs(state_path: Path = STATE_PATH) -> list:
    """The 37 certified governed exogenous readings, in author order.

    Mirrors the bench filter: governed arm, certified, with a persisted
    reading (author-failed records carry no reading_json and never enter
    `exo_readings`)."""
    docs = []
    with state_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("arm") != "governed":
                continue
            if not rec.get("certified"):
                continue
            if not rec.get("reading_json"):
                continue
            doc = _reading_doc(rec, "", origin="exogenous")
            if doc:
                docs.append(doc)
    return docs


def token_stream(docs: list) -> list:
    """Concatenate `_structure_tokens` over the readings in author order."""
    toks = []
    for d in docs:
        toks.extend(_structure_tokens(d))
    return toks


def order_k_entropy(toks: list, k: int) -> float:
    """Empirical order-k entropy in bits/token.

    k == 0 is the memoryless entropy -sum p log2 p. For k >= 1 it is the
    empirical conditional entropy H(X_i | X_{i-k..i-1}) = -sum_{c,s}
    p(c,s) log2 p(s|c), frequencies from the corpus itself (hindsight)."""
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


def lz77_phrase_count(toks: list) -> int:
    """Greedy longest-match self-referential LZ77 factorization; window =
    whole prefix; source may overlap the current position (classic LZ77).
    Returns the standard z77 phrase count.

    Each factor is either the longest substring starting at the current
    position that has an earlier occurrence (start j < i, match may extend
    past i-1 as the decoder produces those symbols in order), or -- when the
    current symbol is fresh -- a single-symbol literal phrase."""
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


def _last_governed_csv_row(csv_path: Path = CSV_PATH) -> dict:
    """The final governed row of the committed CSV (the full 37-reading
    corpus): carries the reported corpus_dl and the committed order-0
    estimate we consistency-check against."""
    lines = [ln.rstrip("\n") for ln in csv_path.read_text().splitlines() if ln.strip()]
    header = lines[0].split(",")
    last = None
    for ln in lines[1:]:
        cells = ln.split(",")
        row = dict(zip(header, cells))
        if row.get("arm") == "governed":
            last = row
    if last is None:
        raise RuntimeError("no governed row in committed CSV")
    return last


def compute() -> dict:
    """The full reference stack as a byte-stable dict."""
    docs = load_governed_certified_docs()
    toks = token_stream(docs)
    n = len(toks)
    alphabet = sorted(set(toks))
    a = len(alphabet)
    log2_a = math.log2(a) if a > 1 else 1.0

    naive = mdl_macros.corpus_dl(docs, {})["total"]

    csv_row = _last_governed_csv_row()
    corpus_dl = float(csv_row["reported_exogenous_dl"])
    committed_order0 = float(csv_row["order0_entropy_dl_est"])

    def scaled_dl(bits_per_token: float) -> float:
        # DL_ref = naive * (bits_per_token / log2|A|)  -- the ratio
        # convention, identical to the committed order-0 estimate.
        return naive * (bits_per_token / log2_a) if log2_a else 0.0

    h0 = order_k_entropy(toks, 0)
    h1 = order_k_entropy(toks, 1)
    h2 = order_k_entropy(toks, 2)
    dl0 = scaled_dl(h0)
    dl1 = scaled_dl(h1)
    dl2 = scaled_dl(h2)

    z = lz77_phrase_count(toks)
    lz_bits = z * (math.log2(n) + log2_a) if n > 0 else 0.0
    lz_bits_per_token = (lz_bits / n) if n > 0 else 0.0
    dl_lz = scaled_dl(lz_bits_per_token)

    residual_gap = corpus_dl - dl_lz

    return {
        "corpus": "governed / certified / exogenous (committed checkpoint)",
        "n_readings": len(docs),
        "stream_length": n,
        "alphabet_size": a,
        "uniform_bits_per_token_log2_A": round(log2_a, 6),
        "naive_counting_dl": round(naive, 3),
        "corpus_dl": round(corpus_dl, 3),
        "scaling_convention": (
            "DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|); "
            "order-k uses bits_per_token = H_k, LZ77 uses "
            "bits_per_token = z*(log2 N + log2|A|)/N. Ratio-reconciled, "
            "no tuned constants (mirrors bench_formalize._order0_entropy_dl_est)."
        ),
        "order_k": {
            "H0_bits_per_token": round(h0, 6),
            "H1_bits_per_token": round(h1, 6),
            "H2_bits_per_token": round(h2, 6),
            "DL0": round(dl0, 3),
            "DL1": round(dl1, 3),
            "DL2": round(dl2, 3),
        },
        "lz77_proxy": {
            "z_phrases": z,
            "phrase_cost_bits_log2N_plus_log2A": round(math.log2(n) + log2_a, 6),
            "total_bits": round(lz_bits, 3),
            "bits_per_token": round(lz_bits_per_token, 6),
            "DL_lz77_proxy": round(dl_lz, 3),
        },
        "stack": {
            "corpus_dl": round(corpus_dl, 3),
            "order0_DL": round(dl0, 3),
            "order1_DL": round(dl1, 3),
            "order2_DL": round(dl2, 3),
            "lz77_proxy_DL": round(dl_lz, 3),
        },
        "residual_gap_corpus_dl_minus_lz77": round(residual_gap, 3),
        "residual_gap_pct_of_corpus_dl": round(
            100.0 * residual_gap / corpus_dl, 3) if corpus_dl else 0.0,
        "order0_consistency": {
            "committed_csv_order0": round(committed_order0, 3),
            "recomputed_order0": round(dl0, 3),
            "matches": round(dl0, 3) == round(committed_order0, 3),
        },
        "caveat_order_k": (
            "References, not floors. Per COMPRESSION.md §10.2: on highly "
            "repetitive corpora (plausibly ours) grammar coders can encode "
            "far *below* nH_k -- which is exactly what the bench measured "
            "(2139 < 2450 order-0). A corpus_dl below an order-k line is "
            "expected. In-sample, hindsight, zero generalization power on a "
            "37-reading corpus (§11.7)."
        ),
    }


def to_markdown(r: dict) -> str:
    ok = r["order0_consistency"]
    lines = []
    lines.append("# Entropy reference floors (C3) — committed governed corpus")
    lines.append("")
    lines.append(
        "Computable reference lines for the structure-token stream the "
        "counting DL implicitly uniform-codes. Orientation references, **not "
        "floors** for the macro coder (§10.2)."
    )
    lines.append("")
    lines.append("## Stream")
    lines.append("")
    lines.append("| quantity | value |")
    lines.append("| --- | --- |")
    lines.append(f"| certified governed exogenous readings | {r['n_readings']} |")
    lines.append(f"| stream length N | {r['stream_length']} |")
    lines.append(f"| alphabet size \\|A\\| | {r['alphabet_size']} |")
    lines.append(
        f"| uniform bits/token log2\\|A\\| | "
        f"{r['uniform_bits_per_token_log2_A']} |")
    lines.append(f"| naive counting DL (empty table) | {r['naive_counting_dl']} |")
    lines.append("")
    lines.append("## Scaling convention")
    lines.append("")
    lines.append(f"> {r['scaling_convention']}")
    lines.append("")
    lines.append("## The measured stack")
    lines.append("")
    lines.append("| reference | bits/token | DL (counting units) |")
    lines.append("| --- | --- | --- |")
    lines.append(
        f"| corpus_dl (reported, learned macro table) | — | "
        f"{r['stack']['corpus_dl']} |")
    lines.append(
        f"| order-0 (memoryless) | {r['order_k']['H0_bits_per_token']} | "
        f"{r['stack']['order0_DL']} |")
    lines.append(
        f"| order-1 | {r['order_k']['H1_bits_per_token']} | "
        f"{r['stack']['order1_DL']} |")
    lines.append(
        f"| order-2 | {r['order_k']['H2_bits_per_token']} | "
        f"{r['stack']['order2_DL']} |")
    lines.append(
        f"| LZ77 parse proxy (z = {r['lz77_proxy']['z_phrases']}) | "
        f"{r['lz77_proxy']['bits_per_token']} | "
        f"{r['stack']['lz77_proxy_DL']} |")
    lines.append("")
    lines.append(
        f"**Residual gap (T2, §11.8):** corpus_dl − LZ77_proxy = "
        f"{r['stack']['corpus_dl']} − {r['stack']['lz77_proxy_DL']} = "
        f"**{r['residual_gap_corpus_dl_minus_lz77']}** "
        f"({r['residual_gap_pct_of_corpus_dl']}% of corpus_dl).")
    lines.append("")
    lines.append("## Order-0 consistency check")
    lines.append("")
    lines.append(
        f"Committed CSV order0_entropy_dl_est = {ok['committed_csv_order0']}; "
        f"recomputed = {ok['recomputed_order0']}; "
        f"match = **{ok['matches']}**.")
    lines.append("")
    lines.append("## Caveat")
    lines.append("")
    lines.append(f"> {r['caveat_order_k']}")
    lines.append("")
    return "\n".join(lines)


def _dump_json(r: dict) -> str:
    return json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    r = compute()
    if not r["order0_consistency"]["matches"]:
        sys.stderr.write(
            "STOP: order-0 line does not reproduce the committed CSV value "
            f"({r['order0_consistency']['recomputed_order0']} != "
            f"{r['order0_consistency']['committed_csv_order0']}).\n")
        return 1
    JSON_OUT.write_text(_dump_json(r))
    MD_OUT.write_text(to_markdown(r))
    sys.stdout.write(f"wrote {JSON_OUT}\nwrote {MD_OUT}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

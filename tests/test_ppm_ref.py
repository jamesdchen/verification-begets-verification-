#!/usr/bin/env python3
"""Tests for tools/ppm_ref.py -- the honest adaptive context-model reference.

Guards:
  * correctness: KT and Laplace codelengths on a tiny hand-computable stream
    ('abab' over a 2-symbol alphabet) match exact hand arithmetic;
  * token-stream fidelity: ppm_ref walks the identical governed exogenous
    stream as bench_formalize._structure_tokens (catches drift);
  * scaling discipline: DL is the entropy_refs ratio convention applied to
    the adaptive bits/token, using the values READ from entropy_refs.json;
  * the §10.7 headline is internally consistent with the per-k rows;
  * determinism / byte-stability: two compute() + serialize passes are
    byte-identical, and the committed artifacts equal a fresh recompute.
"""
import json
import math
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools import ppm_ref as pr  # noqa: E402
from bench_formalize import _structure_tokens  # noqa: E402


def _reg_stream():
    """Shared stream pins from the corpus-era registration (the one
    re-baseline point, specs/mathsources/registration.json)."""
    return json.loads((_REPO / "specs" / "mathsources" /
                       "registration.json").read_text())["governed_exogenous"]



# ---- correctness on a hand-computable stream --------------------------------

def test_kt_codelength_abab_hand_arithmetic():
    # 'abab' over alphabet {a, b} (|A| = 2), order-0 KT (add-1/2):
    #   p0(a) = 0.5/1 = 1/2 ; p1(b) = 0.5/2 = 1/4 ;
    #   p2(a) = 1.5/3 = 1/2 ; p3(b) = 1.5/4 = 3/8
    #   product = 1/2 * 1/4 * 1/2 * 3/8 = 3/128
    #   codelength = -log2(3/128) = log2(128/3)
    toks = ["a", "b", "a", "b"]
    total, per = pr.adaptive_code(toks, k=0, alpha=0.5, alphabet_size=2)
    # tolerance: summing -log2(p_i) differs from log2(prod) by <=1 ULP
    assert math.isclose(total, math.log2(128.0 / 3.0), abs_tol=1e-9)
    assert len(per) == 4
    assert abs(sum(per) - total) < 1e-12


def test_laplace_codelength_abab_hand_arithmetic():
    # order-0 Laplace (add-1), |A| = 2:
    #   p = 1/2, 1/3, 1/2, 2/5 ; product = 1/30 ; codelength = log2(30)
    toks = ["a", "b", "a", "b"]
    total, _ = pr.adaptive_code(toks, k=0, alpha=1.0, alphabet_size=2)
    assert math.isclose(total, math.log2(30.0), abs_tol=1e-9)


def test_kt_order1_abab_hand_arithmetic():
    # order-1 KT on 'abab', |A| = 2. Contexts (prefix for i < k):
    #   i0 ctx()  -> a : 0.5/1
    #   i1 ctx(a) -> b : 0.5/1   (ctx 'a' never seen before)
    #   i2 ctx(b) -> a : 0.5/1   (ctx 'b' never seen before)
    #   i3 ctx(a) -> b : ctx 'a' has [b:1], n_b=1,N=1 -> 1.5/2 = 0.75
    #   product = 1/2 * 1/2 * 1/2 * 3/4 -> codelength = 3 - log2(0.75)
    toks = ["a", "b", "a", "b"]
    total, _ = pr.adaptive_code(toks, k=1, alpha=0.5, alphabet_size=2)
    assert math.isclose(total, 3.0 - math.log2(0.75), abs_tol=1e-9)


def test_full_stream_charged_length():
    # Every token is charged -- per_token_bits has exactly N entries for all k.
    docs = pr.load_governed_exo_docs()
    toks = [t for rt in pr.reading_token_lists(docs) for t in rt]
    for k in (0, 1, 2):
        _, per = pr.adaptive_code(toks, k, 0.5, len(set(toks)))
        assert len(per) == len(toks) == _reg_stream()["stream_length"]


# ---- stream fidelity --------------------------------------------------------

def test_token_extraction_matches_bench_byte_for_byte():
    docs = pr.load_governed_exo_docs()
    reading_lists = pr.reading_token_lists(docs)
    tool_stream = [t for rt in reading_lists for t in rt]
    bench_stream = []
    for d in docs:
        bench_stream.extend(_structure_tokens(d))
    assert tool_stream == bench_stream
    assert len(tool_stream) == _reg_stream()["stream_length"]


def test_stream_shape():
    r = pr.compute()
    g = _reg_stream()
    assert r["n_readings"] == g["n_readings"]
    assert r["stream_length"] == g["stream_length"]
    assert r["alphabet_size"] == g["alphabet_size"]
    assert sum(r["reading_token_lengths"]) == g["stream_length"]
    assert len(r["reading_token_lengths"]) == g["n_readings"]


# ---- scaling discipline (read from entropy_refs.json, not recomputed) --------

def test_scaling_inputs_read_from_entropy_refs():
    refs = json.loads((_REPO / "results" / "entropy_refs.json").read_text())
    r = pr.compute()
    si = r["scaling_inputs_from_entropy_refs"]
    assert si["naive_counting_dl"] == refs["naive_counting_dl"]
    assert si["uniform_bits_per_token_log2_A"] == refs["uniform_bits_per_token_log2_A"]
    assert si["corpus_dl"] == refs["corpus_dl"]
    assert si["plugin_DL0"] == refs["order_k"]["DL0"]
    assert si["plugin_DL1"] == refs["order_k"]["DL1"]
    assert si["plugin_DL2"] == refs["order_k"]["DL2"]


def test_dl_is_ratio_of_bits_per_token():
    r = pr.compute()
    naive = r["scaling_inputs_from_entropy_refs"]["naive_counting_dl"]
    log2a = r["scaling_inputs_from_entropy_refs"]["uniform_bits_per_token_log2_A"]
    for est in ("kt", "laplace"):
        for k in ("0", "1", "2"):
            row = r["results"][est][k]
            # the tool scales the UNROUNDED bits-per-token; the stored
            # bits_per_token is rounded to 6 dp, so recomputing from it can
            # land one 3-dp ULP away at a rounding boundary (first hit at the
            # 59-source corpus).  Half-ULP slack, not a weakened relation.
            expect = round(naive * (row["bits_per_token"] / log2a), 3)
            assert abs(row["adaptive_DL"] - expect) <= 0.0011


def test_adaptive_pays_learning_cost_above_plugin():
    # The whole point: the adaptive DL exceeds the plug-in DL_k at every k
    # (the plug-in line never pays for learning). Sanity, not a floor claim.
    r = pr.compute()
    for est in ("kt", "laplace"):
        for k in ("0", "1", "2"):
            row = r["results"][est][k]
            assert row["adaptive_DL"] > row["plugin_DL"]
            assert row["adaptive_minus_plugin_DL"] > 0


# ---- headline consistency ---------------------------------------------------

def test_headline_matches_rows():
    r = pr.compute()
    hl = r["headline"]
    any_beat = any(
        r["results"][est][str(k)]["beats_corpus_dl"]
        for est in ("kt", "laplace") for k in (0, 1, 2)
    )
    assert hl["any_adaptive_order_k_beats_corpus_dl"] == any_beat
    # best_adaptive is the global minimum adaptive DL
    all_dls = [
        r["results"][est][str(k)]["adaptive_DL"]
        for est in ("kt", "laplace") for k in (0, 1, 2)
    ]
    assert hl["best_adaptive"]["adaptive_DL"] == min(all_dls)
    # on THIS corpus the best adaptive coder is KT order-1 and it beats corpus_dl
    assert hl["best_adaptive"]["estimator"] == "kt"
    assert hl["best_adaptive"]["order_k"] == 1
    assert hl["any_adaptive_order_k_beats_corpus_dl"] is True
    assert hl["best_adaptive"]["adaptive_DL"] < r["scaling_inputs_from_entropy_refs"]["corpus_dl"]


def test_prequential_trajectory_shape():
    r = pr.compute()
    for est in ("kt", "laplace"):
        for k in ("0", "1", "2"):
            traj = r["prequential"][est][k]
            assert len(traj) == _reg_stream()["n_readings"]  # one per reading
            assert all(traj[i] <= traj[i + 1] for i in range(54))  # non-decreasing
            # final cumulative bits == total_bits (to the rounding)
            assert abs(traj[-1] - r["results"][est][k]["total_bits"]) < 0.5


# ---- determinism ------------------------------------------------------------

def test_byte_stability_json_and_md():
    r1 = pr.compute()
    r2 = pr.compute()
    assert pr._dump_json(r1) == pr._dump_json(r2)
    assert pr.to_markdown(r1) == pr.to_markdown(r2)


def test_committed_artifacts_match_recompute():
    r = pr.compute()
    assert (_REPO / "results" / "ppm_ref.json").read_text() == pr._dump_json(r)
    assert (_REPO / "results" / "ppm_ref.md").read_text() == pr.to_markdown(r)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)

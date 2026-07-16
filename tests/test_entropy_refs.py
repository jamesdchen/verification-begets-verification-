#!/usr/bin/env python3
"""Tests for tools/entropy_refs.py -- the C3 reference floors.

Guards:
  * order-0 consistency: the recomputed order-0 line reproduces the
    committed CSV order0_entropy_dl_est to the digit (the hard STOP gate);
  * determinism / byte-stability: two independent compute() + serialize
    passes yield byte-identical JSON and Markdown;
  * token-stream fidelity: the tool's structure-token extraction is
    byte-identical to bench_formalize._structure_tokens over the committed
    corpus (catches drift if the import ever has to be vendored);
  * the reported stack invariants (stream length, alphabet, z >= 1,
    residual gap arithmetic).
"""
import csv
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools import entropy_refs as er  # noqa: E402
from bench_formalize import _structure_tokens  # noqa: E402


def _committed_csv_order0():
    with (_REPO / "results" / "formalize_governed.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    gov = [r for r in rows if r["arm"] == "governed"]
    return round(float(gov[-1]["order0_entropy_dl_est"]), 3)


def test_order0_consistency_against_committed_csv():
    r = er.compute()
    committed = _committed_csv_order0()
    assert committed == 2449.587, committed  # pin the committed value itself
    assert r["order_k"]["DL0"] == committed
    assert r["order0_consistency"]["matches"] is True
    assert r["order0_consistency"]["recomputed_order0"] == committed


def test_stream_shape():
    r = er.compute()
    assert r["n_readings"] == 37
    # The token STREAM is untouched by WP-T3-REAL (it is walked over the readings,
    # not the macro table), so stream length / alphabet / naive counting DL are
    # all byte-stable across the re-baseline.
    assert r["stream_length"] == 1067
    assert r["alphabet_size"] == 41
    assert r["naive_counting_dl"] == 2840.0
    # corpus_dl is read from the committed CSV's final governed reported DL, which
    # the WP-T3-REAL re-baseline moved 2139 -> 2168 (+29: the governed arm lost
    # the even/odd op-slot macro to cluster over-generalization -- see the census
    # test).  The order-k / LZ77 REFERENCE lines below do NOT move (same stream).
    assert r["corpus_dl"] == 2168.0


def test_token_extraction_matches_bench_byte_for_byte():
    # The tool must be CONSISTENT with the bench's token stream definition.
    docs = er.load_governed_certified_docs()
    tool_stream = er.token_stream(docs)
    bench_stream = []
    for d in docs:
        bench_stream.extend(_structure_tokens(d))
    assert tool_stream == bench_stream
    assert len(tool_stream) == 1067


def test_lz77_and_residual_gap():
    r = er.compute()
    z = r["lz77_proxy"]["z_phrases"]
    assert z >= 1
    assert z == 242
    expected_gap = round(r["stack"]["corpus_dl"] - r["stack"]["lz77_proxy_DL"], 3)
    assert r["residual_gap_corpus_dl_minus_lz77"] == expected_gap


def test_order_k_monotone_reference_lines():
    r = er.compute()
    h = r["order_k"]
    # Empirical order-k entropy is non-increasing in k.
    assert h["H0_bits_per_token"] >= h["H1_bits_per_token"] >= h["H2_bits_per_token"]
    assert h["DL0"] >= h["DL1"] >= h["DL2"]


def test_context_stats_small_sample_columns():
    # The small-sample hazard must be quantified in the artifact, not just
    # asserted in prose: distinct/singleton context counts per order.
    r = er.compute()
    cs = r["context_stats"]
    o1, o2 = cs["order1"], cs["order2"]
    assert o1["distinct_contexts"] == 41
    assert o1["singleton_contexts"] == 3
    assert o1["predictions"] == 1066
    assert o2["distinct_contexts"] == 164
    assert o2["singleton_contexts"] == 52
    assert o2["predictions"] == 1065
    assert o2["singleton_fraction"] == 0.3171
    # singleton contexts each contribute exactly one 0-bit prediction
    assert o2["predictions_from_singletons"] == o2["singleton_contexts"]
    # the optimism warning must reference the plug-in / LZ77-gate discipline
    warn = r["caveat_small_sample"]
    assert "PLUG-IN" in warn and "LZ77" in warn and "OPTIMISTIC" in warn


def test_byte_stability_json_and_md():
    r1 = er.compute()
    r2 = er.compute()
    assert er._dump_json(r1) == er._dump_json(r2)
    assert er.to_markdown(r1) == er.to_markdown(r2)


def test_committed_artifacts_match_recompute():
    # The committed artifacts must equal a fresh recompute (no drift).
    r = er.compute()
    assert (_REPO / "results" / "entropy_refs.json").read_text() == er._dump_json(r)
    assert (_REPO / "results" / "entropy_refs.md").read_text() == er.to_markdown(r)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)

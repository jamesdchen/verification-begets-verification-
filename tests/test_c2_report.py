#!/usr/bin/env python3
"""Tests for tools/c2_report.py -- WP-C2, the two-part entropy-coded currency
as a REPORTED experiment (COMPRESSION.md §3 C2 / §11.8).

Guards:
  * the ppm_ref CONSISTENCY ANCHOR: c2_dl(readings, {}) (empty table => 0 model
    bits + KT order-1 over the raw stream) reproduces ppm_ref.json's KT order-1
    adaptive_DL to the rounding digit -- the no-vocabulary variant IS ppm_ref;
  * a HAND-COMPUTABLE tiny case: exact rewritten-stream token mapping, exact
    leaf-counted model bits (== mdl_macros.dl_macro), exact KT bits, and the
    exact scaled data bits;
  * model bits are the mdl_macros leaf count (one source of truth), not a
    reimplementation;
  * the empty-table rewritten stream is byte-identical to the raw structure
    stream ppm_ref codes;
  * the committed headline numbers and the vocabulary-pays verdict are pinned
    (both mappings: the vocabulary does NOT pay under C2);
  * determinism / byte-stability of the serialized artifact.
"""
import json
import math
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _regj():
    """The corpus-era registration -- the one re-baseline point for shared
    corpus-growth pins (specs/mathsources/registration.json)."""
    return json.loads((_REPO / "specs" / "mathsources" /
                       "registration.json").read_text())

from tools import c2_report as c2          # noqa: E402
from tools import ppm_ref as ppm           # noqa: E402
from buildloop import mdl_macros           # noqa: E402
from bench_formalize import _structure_tokens  # noqa: E402


# --- a tiny hand-built corpus + macro ---------------------------------------
_MACRO = {"name": "mtest", "params": ["p0"],
          "body": [{"kind": "hypothesis",
                    "pred": {"op": "$p0", "args": [{"ref": "a"}]}}]}
_READING = {"statements": [{"force": "assert",
                            "lf": {"kind": "hypothesis",
                                   "pred": {"op": "even",
                                            "args": [{"ref": "a"}]}}}]}
_TABLE = {"mtest": _MACRO}


def _scale():
    refs = json.loads(c2.ENTROPY_REFS_JSON.read_text())
    return refs["naive_counting_dl"], refs["uniform_bits_per_token_log2_A"]


# ---- token mapping, hand-computable ----------------------------------------

def test_rewritten_stream_empty_is_raw_structure_stream():
    # Empty table: nothing matches, so the rewritten stream is exactly the raw
    # per-statement _structure_tokens walk.
    raw = c2.rewritten_stream([_READING], {}, mapping="canonical")
    assert raw == [("kind", "hypothesis"), ("force", "assert"),
                   ("op", "even"), ("ref", "a")]


def test_rewritten_stream_macro_mapping_is_name_plus_one_arg_token():
    # canonical mapping: invocation = 1 ('macro', name) + 1 ('argval', json) per
    # bound arg -- mirrors dl_invocation(k) = base + name + k.
    rew = c2.rewritten_stream([_READING], _TABLE, mapping="canonical")
    assert rew == [("macro", "mtest"), ("argval", json.dumps("even"))]


def test_rewritten_stream_structural_mapping_walks_arg_into_token_space():
    # structural mapping: the scalar op binding "even" becomes a ref-like leaf
    # in the raw token space, not a fresh argval symbol.
    rew = c2.rewritten_stream([_READING], _TABLE, mapping="structural")
    assert rew == [("macro", "mtest"), ("ref", "even")]


def test_empty_table_rewritten_matches_bench_structure_tokens_on_real_corpus():
    # On the committed corpus the empty-table rewritten stream equals the exact
    # concatenation of bench_formalize._structure_tokens per reading (the stream
    # ppm_ref codes) -- no drift.
    docs = c2.load_corpus()
    got = c2.rewritten_stream(docs, {}, mapping="canonical")
    expected = [t for d in docs for t in _structure_tokens(d)]
    assert got == expected
    assert len(got) == _regj()["governed_exogenous"]["stream_length"]


# ---- model bits are the mdl_macros leaf count (one source of truth) ---------

def test_model_bits_equal_mdl_macros_dl_macro():
    assert c2.macro_model_bits(_TABLE) == mdl_macros.dl_macro(_MACRO)
    # hand value: 1(base) + 1(param) + 10(dl_statement of the body) = 12
    assert c2.macro_model_bits(_TABLE) == 12.0


def test_model_bits_equal_corpus_dl_macro_cost_on_committed_table():
    docs = c2.load_corpus()
    tables = c2.load_final_tables()
    for arm in ("governed", "ungoverned"):
        table = tables[arm]["table"]
        cost = mdl_macros.corpus_dl(docs, table, canon=False)["macro_cost"]
        assert c2.macro_model_bits(table) == cost


# ---- the C2 currency on the hand case --------------------------------------

def test_c2_dl_tiny_case_exact_arithmetic():
    naive, log2_a = _scale()
    # raw (empty) stream has 4 distinct tokens over 4 positions; order-1 KT with
    # |A| = 4: every context is fresh, p = 0.5 / (0.5*4) = 0.25 => 2 bits each
    # => 8 bits.  n_raw = 4.
    res0 = c2.c2_dl([_READING], {}, mapping="canonical")
    assert res0["kt_bits"] == 8.0
    assert res0["stream_length"] == 4
    assert res0["model_bits"] == 0.0
    assert math.isclose(res0["data_bits"], round(naive * (8.0 / 4) / log2_a, 3),
                        abs_tol=1e-6)

    # with the macro: stream = [macro, argval], |A| = 2, both contexts fresh,
    # p = 0.5/(0.5*2) = 0.5 => 1 bit each => 2 bits.  n_raw still 4 (raw stream).
    res = c2.c2_dl([_READING], _TABLE, mapping="canonical")
    assert res["kt_bits"] == 2.0
    assert res["stream_length"] == 2
    assert res["model_bits"] == 12.0
    assert math.isclose(res["data_bits"], round(naive * (2.0 / 4) / log2_a, 3),
                        abs_tol=1e-6)
    assert math.isclose(res["total"], round(12.0 + naive * (2.0 / 4) / log2_a, 3),
                        abs_tol=1e-6)


# ---- the ppm_ref consistency anchor ----------------------------------------

def test_empty_table_c2_reconciles_with_ppm_ref_kt_order1():
    docs = c2.load_corpus()
    res = c2.c2_dl(docs, {}, mapping="canonical")
    ppm_json = json.loads(c2.PPM_REF_JSON.read_text())
    kt1 = ppm_json["results"]["kt"]["1"]["adaptive_DL"]
    # empty table => 0 model bits, data bits == ppm_ref KT order-1 exactly.
    assert res["model_bits"] == 0.0
    assert math.isclose(res["data_bits"], kt1, abs_tol=0.01)
    assert math.isclose(res["total"], kt1, abs_tol=0.01)


def test_empty_table_data_bits_match_independent_ppm_coder():
    # Independent recompute: the empty-table data bits equal the scaled KT
    # order-1 codelength of the raw stream via ppm_ref.adaptive_code directly.
    docs = c2.load_corpus()
    naive, log2_a = _scale()
    raw = c2.rewritten_stream(docs, {}, mapping="canonical")
    tb, _ = ppm.adaptive_code(raw, 1, 0.5, len(set(raw)))
    expected = round(naive * (tb / len(raw)) / log2_a, 3)
    assert c2.c2_dl(docs, {}, mapping="canonical")["data_bits"] == expected


# ---- committed report: anchors, decomposition, verdict ---------------------

def test_report_consistency_anchor_reconciles():
    r = c2.compute()
    assert r["consistency_anchor"]["reconciles"] is True


def test_committed_counting_corpus_dl_anchors():
    # The counting-currency anchors the tool reports must be the committed
    # numbers (governed 3417, ungoverned 3715 at the C2 census-sourced
    # 59-source corpus) -- ties the table derivation to the checkpoint.
    r = c2.compute()
    cnt = _regj()["counting"]
    assert r["arms"]["governed"]["canonical"]["counting_corpus_dl"] == \
        cnt["governed_corpus_dl"]
    assert r["arms"]["ungoverned"]["canonical"]["counting_corpus_dl"] == \
        cnt["ungoverned_corpus_dl"]
    assert r["committed_tables"]["governed"]["reported_dl"] == \
        cnt["governed_corpus_dl"]
    assert r["committed_tables"]["ungoverned"]["reported_dl"] == \
        cnt["ungoverned_corpus_dl"]


def test_committed_headline_numbers_pinned():
    r = c2.compute()
    h = r["headline"]
    assert h["governed_c2"] == 2737.614
    assert h["empty_c2_no_vocabulary"] == 2337.917
    assert h["ungoverned_c2"] == 2642.253
    assert h["kt1_advantage_over_counting"] == 1267.083
    assert h["c2_recovered_of_kt1_advantage"] == 867.386


def test_vocabulary_does_not_pay_under_c2_both_mappings():
    # The headline honest finding, pinned under BOTH mappings so it is not a
    # mapping artifact: governed C2 > empty-table C2 (the vocabulary costs bits).
    r = c2.compute()
    for mapping in c2.MAPPINGS:
        v = r["verdict"][mapping]
        assert v["vocabulary_pays_under_c2"] is False
        assert v["governed_c2"] > v["empty_c2_no_vocabulary"]
        assert v["vocabulary_cost_under_c2"] > 0


def test_decomposition_total_is_model_plus_data():
    r = c2.compute()
    for arm in ("empty", "governed", "ungoverned"):
        for mapping in c2.MAPPINGS:
            a = r["arms"][arm][mapping]
            assert math.isclose(a["total"], a["model_bits"] + a["data_bits"],
                                abs_tol=1e-6)


# ---- determinism -----------------------------------------------------------

def test_serialized_report_is_byte_stable():
    a = c2._dump_json(c2.compute())
    b = c2._dump_json(c2.compute())
    assert a == b


def test_markdown_renders():
    md = c2.to_markdown(c2.compute())
    assert "two-part entropy-coded DL" in md
    assert "does NOT pay" in md          # the committed verdict
    assert "Pre-registered future predicate" in md

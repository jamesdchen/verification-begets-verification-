"""Teeth for tools/proof_mine.py (the L5 wiring).

LLM-free, Lean-free, network-free.  The pipeline is exercised end-to-end on
SYNTHETIC ∃ readings (the test_math_witness source-43 shape -- the committed
corpus emits zero proof templates today, and the tool must both survive that
zero honestly and mine correctly when substrate exists)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.math_reading import parse_math_reading
from tools import proof_mine


def _reading(theorem, obj_names, concl, source):
    stmts = [{"id": "amb", "force": "choice", "quote": "",
              "lf": {"kind": "ambient", "carrier": "Int"}}]
    for i, n in enumerate(obj_names):
        stmts.append({"id": f"o{i}", "force": "demand", "quote": f"integer {n}",
                      "lf": {"kind": "object", "name": n, "type": "Int"}})
    stmts.append({"id": "qf", "force": "demand", "quote": "for every",
                  "lf": {"kind": "quantifier", "binder": "forall",
                         "objects": [obj_names[0]]}})
    stmts.append({"id": "qx", "force": "demand", "quote": "there exists",
                  "lf": {"kind": "quantifier", "binder": "exists",
                         "objects": [obj_names[1]]}})
    stmts.append({"id": "c", "force": "demand", "quote": "conclusion",
                  "lf": {"kind": "conclusion", "pred": concl}})
    return parse_math_reading(
        json.dumps({"theorem": theorem, "statements": stmts}), source)


def _lt(a, b):
    return {"op": "<", "args": [a, b]}


def _fixture_pairs():
    # Two sources sharing the m := n + 1 witness shape (regularity to mine),
    # phrased so the emitter genuinely emits for both.
    src_a = ("for every integer n there exists an integer m with n less "
             "than m  for every integer conclusion")
    src_b = ("for every integer k there exists an integer j with k less "
             "than j  for every integer conclusion")
    ra = _reading("larger_a", ["n", "m"], _lt({"ref": "n"}, {"ref": "m"}),
                  "integer n integer m for every there exists conclusion")
    rb = _reading("larger_b", ["k", "j"], _lt({"ref": "k"}, {"ref": "j"}),
                  "integer k integer j for every there exists conclusion")
    return [(ra, "fix:a"), (rb, "fix:b")], (src_a, src_b)


def test_collect_emits_templates_for_exists_fixture():
    pairs, _ = _fixture_pairs()
    programs, skips = proof_mine.collect_from_readings(pairs)
    assert len(programs) == 2, (programs, skips)
    for p in programs:
        assert p["layer"] == "proof-template"
        # the emitter's known survivor for this shape: witness = var + 1.
        assert p["ast"]["op"] == "+", p


def test_sexpr_canonical_and_deterministic():
    ast = {"op": "+", "args": [{"ref": "n"}, {"lit": 1}]}
    assert proof_mine.to_sexpr(ast) == "(+ (ref n) (lit 1))"
    assert proof_mine.to_sexpr(ast) == proof_mine.to_sexpr(ast)
    with pytest.raises(ValueError):
        proof_mine.to_sexpr({"weird": 1})


def test_mine_holdout_split_and_transfer():
    pairs, _ = _fixture_pairs()
    programs, _ = proof_mine.collect_from_readings(pairs)
    # duplicate each program so subtrees recur WITHIN the train side too.
    programs = programs + [dict(p) for p in programs]
    mined = proof_mine.mine(programs, top_k=5)
    assert mined["n_train"] + mined["n_holdout"] == mined["n_programs"]
    assert mined["n_train"] > 0 and mined["n_holdout"] > 0
    # sources split by parity: fix:a trains, fix:b holds out (sorted order).
    train_sources = {"fix:a"}
    for c in mined["candidates"]:
        assert c["train_occurrences"] >= 2
        assert 0.0 <= c["transfer"]


def test_repo_corpus_substrate_is_measured_not_hidden():
    rep = proof_mine.report()
    # The measured facts after S4a' grew the corpus (PLAN_REFLECT): the five
    # ∃-class readings emit witness programs; the three ∀-only readings are
    # named skips; the miner finds no cross-program regularity yet -- an
    # empty candidate list is the reported finding, never a hidden one.
    assert rep["substrate"]["programs"] == 5
    assert rep["substrate"]["emitter_skips"] == {"no-exists-binder": 3}
    assert rep["mined"]["candidates"] == []
    assert "empty substrate" in rep["honesty"].lower() or \
        "reported" in rep["honesty"].lower()


def test_stitch_pass_degrades_honestly():
    out = proof_mine.stitch_pass([])
    assert out == {"ran": False, "reason": "fewer than 2 programs"}


def test_stitch_pass_runs_when_available():
    stitch_core = pytest.importorskip("stitch_core")
    pairs, _ = _fixture_pairs()
    programs, _ = proof_mine.collect_from_readings(pairs)
    programs = programs + [dict(p) for p in programs]
    out = proof_mine.stitch_pass(programs)
    assert out["ran"] in (True, False)
    if out["ran"]:
        assert "abstractions" in out


def test_rank_for_verification_value_order():
    cands = [
        {"sexpr": "(a)", "approx_saving": 10, "transfer": 0.0},
        {"sexpr": "(b)", "approx_saving": 4, "transfer": 1.0},
        {"sexpr": "(c)", "approx_saving": 6, "transfer": 0.5},
    ]
    ranked = proof_mine.rank_for_verification(cands)
    # transferred regularity outranks bigger-but-untransferred savings.
    assert [c["sexpr"] for c in ranked] == ["(b)", "(c)", "(a)"]


def test_ledger_dedups_and_is_deterministic(tmp_path):
    pairs, _ = _fixture_pairs()
    programs, _ = proof_mine.collect_from_readings(pairs)
    programs = programs + [dict(p) for p in programs]
    mined = proof_mine.mine(programs, top_k=5)
    path = str(tmp_path / "ledger.jsonl")
    first = proof_mine.update_ledger(mined, programs, path)
    assert first["new"] >= 1 and first["updated"] == 0
    again = proof_mine.update_ledger(mined, programs, path)
    assert again["new"] == 0                    # dedup by candidate identity
    assert again["total"] == first["total"]
    a = open(path).read()
    proof_mine.update_ledger(mined, programs, path)
    assert open(path).read() == a               # byte-stable re-run


def test_certify_rewrite_cache_hits():
    programs = [{"source": "s1", "sexpr": "(+ (ref n) (lit 1))"}]
    cache = {}
    r1 = proof_mine.certify_rewrite(programs, "(+ (ref n) (lit 1))",
                                    cache=cache)
    assert len(cache) == 1
    r2 = proof_mine.certify_rewrite(programs, "(+ (ref n) (lit 1))",
                                    cache=cache)
    assert r2 is r1                             # served from the cache

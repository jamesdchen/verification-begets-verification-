"""WP-CENSUS: the tower_census tool's own determinism + reproduction test.

This is a NEW test for a NEW tool (house rule: new files only).  It runs the
tool on the COMMITTED checkpoint and asserts the emitted JSON is byte-identical
across two runs -- the pin the plan requires because this artifact is committed
and referenced.  It also re-derives the headline numbers so a drift in the
miner would fail here loudly.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools import tower_census as tc  # noqa: E402
from buildloop import mdl_macros  # noqa: E402


def test_json_byte_stable_across_two_runs():
    # SCOPE: this pins byte-identity across two builds in the SAME PROCESS on
    # this interpreter -- it proves the tool has no timestamp/hash-seed/set-
    # ordering nondeterminism within a run.  It does NOT prove cross-platform
    # or cross-interpreter byte stability (float formatting, hash randomization
    # across processes, etc. are out of its reach); the determinism the plan
    # relies on is same-checkpoint -> same-output on a fixed toolchain.
    a = tc.render_json(tc.build_census())
    b = tc.render_json(tc.build_census())
    assert a == b, "tower_census JSON is not byte-stable across runs"


def test_markdown_byte_stable_across_two_runs():
    a = tc.render_md(tc.build_census())
    b = tc.render_md(tc.build_census())
    assert a == b, "tower_census Markdown is not byte-stable across runs"


def test_wave_hashes_rebaselined_by_t3():
    # WP-T3-REAL re-baseline RECEIPT.  The checkpoint's recorded per-wave
    # `table_hash` is the PRE-T3 run's (the checkpoint is read-only); the T3
    # domain-split window rule (FI-W1-3) intentionally re-mines the tables, so
    # today's miner reproduces the recorded hash ONLY at wave 0 (the empty
    # pre-wave table, which is miner-independent) and DIVERGES at every later
    # wave.  This divergence is the reproducibility tripwire firing BY DESIGN
    # for a reviewed miner change -- kept as the receipt, mirroring §11.8's
    # invalid-then-corrected discipline.  Pre-change this asserted all-True.
    census = tc.build_census()
    assert census["hash_verification"]["all_waves_match"] is False
    for arm in ("governed", "ungoverned"):
        waves = census["hash_verification"][arm]
        assert waves[0]["match"] is True, (arm, "wave-0 empty-table hash stable")
        assert all(w["match"] is False for w in waves[1:]), \
            (arm, "post-T3 waves re-baselined")


def test_final_tables_reconstructed():
    # WP-T3-REAL re-baseline.  Pre-change: governed 5 macros / 2139, ungoverned
    # 6 / 2371.  The T3 math window relaxation coarsens the (width, kind-tuple)
    # clusters (quotes no longer split them), so the greedy per-wave miner takes
    # a DIFFERENT admission path: governed loses the even/odd op-slot macro
    # m_83b0ad76bcb0 (its (hyp,hyp) cluster over-generalizes past the H3
    # concreteness filter) -> 4 macros / 2168 (+29, a regression); ungoverned
    # re-mines to 4 / 2231 (-140).  See the WP-T3-REAL report for the full
    # trajectory; the -179 congruence gain is a counterfactual (below), NOT a
    # greedy-realizable admission on this corpus.
    census = tc.build_census()
    g = census["final_tables"]["governed"]
    u = census["final_tables"]["ungoverned"]
    assert g["count"] == 4 and g["corpus_dl"] == 2168.0
    assert u["count"] == 4 and u["corpus_dl"] == 2231.0


def test_slot_congruence_minus_179_counterfactual_and_windows_unblocked():
    # Tooth (a): the congruence triple now YIELDS windows (the §11.3 zero-window
    # blocker is fixed by the FI-W1-3 force-only math rule), and the one-slot
    # congruence body admits at a strict DL drop of -179 against the final
    # governed table -- RELATIONAL: recompute both sides and assert equality.
    census = tc.build_census()
    slot = census["slot_measurement"]["governed"]
    adm = slot["slot_admission"]
    assert adm["delta"] == -179.0
    assert adm["admit"] is True
    assert adm["uses"] == 3

    # RELATIONAL recompute of the same -179 from first principles, against the
    # SAME baseline table the census priced against (the reconstructed final
    # governed table): corpus_dl(with) - corpus_dl(without) must equal the
    # census's reported delta.  The congruence macro is NOT in the final table
    # (the greedy cannot mine it -- its cluster over-generalizes), so this is a
    # genuine counterfactual, not a re-add of a present macro.
    from tools import tower_census as _tc
    records = _tc._load_records()
    dreams = _tc._dream_readings(records)
    gtab, gexo, _ = _tc._replay_arm(records, "governed", True, dreams)
    cand_meta = slot["slot_candidate"]
    cand = {"name": cand_meta["name"], "params": cand_meta["params"],
            "body": cand_meta["body"]}
    assert cand["name"] not in gtab             # counterfactual, not a re-add
    before = mdl_macros.corpus_dl(gexo, gtab)["total"]
    after = mdl_macros.corpus_dl(gexo, {**gtab, cand["name"]: cand})["total"]
    assert round(after - before, 3) == adm["delta"] == -179.0

    # per-op flat variants remain inadmissible (uses == 1)
    for fv in slot["flat_variants"]:
        assert fv["admission"]["admit"] is False
        assert fv["admission"]["uses"] == 1
    # the blocker is FIXED: the [h1,h2,c] cluster now yields a covering window in
    # every one of the three congruence readings (was 0 pre-change).
    assert slot["total_windows_covering_cong_cluster"] == 3
    for dw in slot["demand_windows"]:
        assert dw["n_windows"] > 0
        assert dw["spans_covering_window"] == 1


def test_tower_gate_metric_is_realizable():
    # Corrected pass-2 headline (reviewer finding): the GATE metric is the
    # REALIZABLE adjacent-witness count -- a pair counts only where its covered
    # statements are uniform in (force, quote) across the union of both
    # invocations (H2, recurrence._demand_windows).  Under that gate the
    # governed MM census reads max=1 with ZERO pairs at/above the >=7 bar.
    census = tc.build_census()
    tw = census["tower_census"]["governed"]
    assert tw["gate_metric"] == "realizable_adjacent_witnesses"
    assert tw["level2_witness_bar"] == 7
    assert tw["max_witness_macro_macro_pair"] == 1
    assert tw["macro_macro_pairs_at_or_above_bar"] == 0
    assert tw["any_macro_pairs_at_or_above_bar"] == 0
    # every listed pair's realizable count never exceeds its raw count, and no
    # MM pair is realizable at/above the bar
    for p in tw["pairs"]:
        assert p["witnesses"] <= p["raw_adjacent_witnesses"]
        if p["category"] == "MM":
            assert p["witnesses"] < tc.LEVEL2_WITNESS_BAR


def test_tower_raw_adjacency_kept_as_secondary():
    # The pre-H2 raw adjacency is retained as a clearly-labeled SECONDARY,
    # explicitly not-the-gate: one MM pair reaches 14 raw adjacencies yet
    # collapses to 0 realizable (its two invocations straddle a force/quote
    # boundary) -- the exact inflation the raw-count gate mis-measured.
    census = tc.build_census()
    tw = census["tower_census"]["governed"]
    assert "NOT the gate metric" in tw["raw_adjacent_note"]
    assert tw["max_raw_adjacent_witness_macro_macro_pair"] == 14
    assert tw["raw_adjacent_macro_macro_pairs_at_or_above_bar"] == 1


def test_subtree_numbers_present():
    census = tc.build_census()
    sub = census["subtree_census"]["governed"]["levels"]
    for lv in ("0", "1", "2"):
        assert "nonalias_at_least_2" in sub[lv]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)

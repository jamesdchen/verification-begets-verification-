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


def test_wave_hashes_verify():
    census = tc.build_census()
    assert census["hash_verification"]["all_waves_match"] is True
    for arm in ("governed", "ungoverned"):
        for h in census["hash_verification"][arm]:
            assert h["match"] is True, (arm, h["wave"])


def test_final_tables_reconstructed():
    census = tc.build_census()
    g = census["final_tables"]["governed"]
    u = census["final_tables"]["ungoverned"]
    # 51-source continuation: the macro COUNTS are unchanged (no new macro was
    # admitted in the continuation waves 5-6 -- the new readings reuse the
    # frozen vocabulary), but the reconstructed corpus_dl grows with the 10 new
    # priced readings.
    assert g["count"] == 5 and g["corpus_dl"] == 2920.0
    assert u["count"] == 6 and u["corpus_dl"] == 3208.0


def test_slot_reproduces_minus_179():
    census = tc.build_census()
    adm = census["slot_measurement"]["governed"]["slot_admission"]
    assert adm["delta"] == -179.0
    assert adm["admit"] is True
    assert adm["uses"] == 3
    # per-op flat variants are inadmissible (uses == 1)
    for fv in census["slot_measurement"]["governed"]["flat_variants"]:
        assert fv["admission"]["admit"] is False
        assert fv["admission"]["uses"] == 1
    # the blocker: zero demand windows over the congruence cluster
    assert census["slot_measurement"]["governed"][
        "total_windows_covering_cong_cluster"] == 0


def test_tower_gate_metric_is_realizable():
    # Corrected pass-2 headline (reviewer finding): the GATE metric is the
    # REALIZABLE adjacent-witness count -- a pair counts only where its covered
    # statements are uniform in (force, quote) across the union of both
    # invocations (H2, recurrence._demand_windows).  Under that gate the
    # governed MM census reads max=2 (up from 1 on the frozen run: the new
    # congruence/divides readings add realizable adjacencies) but STILL ZERO
    # pairs at/above the >=7 bar -- the T1 gate stays correctly deferred.
    census = tc.build_census()
    tw = census["tower_census"]["governed"]
    assert tw["gate_metric"] == "realizable_adjacent_witnesses"
    assert tw["level2_witness_bar"] == 7
    assert tw["max_witness_macro_macro_pair"] == 2
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
    # explicitly not-the-gate: the top MM pair reaches 17 raw adjacencies
    # (up from 14 on the frozen run) yet collapses to max realizable 2 -- the
    # inflation the raw-count gate mis-measured.  Two MM pairs now clear the
    # >=7 bar on RAW count while none clear it on the realizable gate metric.
    census = tc.build_census()
    tw = census["tower_census"]["governed"]
    assert "NOT the gate metric" in tw["raw_adjacent_note"]
    assert tw["max_raw_adjacent_witness_macro_macro_pair"] == 17
    assert tw["raw_adjacent_macro_macro_pairs_at_or_above_bar"] == 2


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

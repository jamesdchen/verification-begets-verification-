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
    assert g["count"] == 5 and g["corpus_dl"] == 2139.0
    assert u["count"] == 6 and u["corpus_dl"] == 2371.0


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


def test_tower_and_subtree_numbers_present():
    census = tc.build_census()
    tw = census["tower_census"]["governed"]
    assert tw["max_witness_macro_macro_pair"] >= 1
    assert tw["level2_witness_bar"] == 7
    sub = census["subtree_census"]["governed"]["levels"]
    for lv in ("0", "1", "2"):
        assert "nonalias_at_least_2" in sub[lv]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)

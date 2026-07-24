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

from buildloop import mdl_macros  # noqa: E402
from tools import tower_census as tc  # noqa: E402


def _census_pair():
    """TWO independent full builds, shared by every test in this file (the
    test_cluster_key `_measured` pattern -- one computation, many teeth).  The
    pricing memo is CLEARED between the two builds, so the pair is two genuine
    end-to-end computations and comparing them keeps the byte-stability teeth
    exactly as strong as two cold runs."""
    if not hasattr(_census_pair, "_p"):
        a = tc.build_census()
        mdl_macros.clear_pricing_cache()
        b = tc.build_census()
        _census_pair._p = (a, b)
    return _census_pair._p


def _census():
    """The first of the pair -- the build every non-stability test reads."""
    return _census_pair()[0]


def _reg():
    """The corpus-era registration -- the one re-baseline point for shared
    corpus-growth pins (specs/mathsources/registration.json)."""
    import json, os
    return json.load(open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "specs", "mathsources", "registration.json")))


def test_json_byte_stable_across_two_runs():
    # SCOPE: this pins byte-identity across two builds in the SAME PROCESS on
    # this interpreter -- it proves the tool has no timestamp/hash-seed/set-
    # ordering nondeterminism within a run.  It does NOT prove cross-platform
    # or cross-interpreter byte stability (float formatting, hash randomization
    # across processes, etc. are out of its reach); the determinism the plan
    # relies on is same-checkpoint -> same-output on a fixed toolchain.
    ca, cb = _census_pair()          # memo cleared between the two builds
    a = tc.render_json(ca)
    b = tc.render_json(cb)
    assert a == b, "tower_census JSON is not byte-stable across runs"


def test_markdown_byte_stable_across_two_runs():
    ca, cb = _census_pair()          # memo cleared between the two builds
    a = tc.render_md(ca)
    b = tc.render_md(cb)
    assert a == b, "tower_census Markdown is not byte-stable across runs"


def test_wave_hashes_verify():
    census = _census()
    assert census["hash_verification"]["all_waves_match"] is True
    for arm in ("governed", "ungoverned"):
        for h in census["hash_verification"][arm]:
            assert h["match"] is True, (arm, h["wave"])


def test_final_tables_reconstructed():
    # WP-FLIP (§12.1): the census-of-record is now `math_mode="refined"` + the
    # re-mine-time GC.  The reconstructed governed corpus_dl is the committed
    # post-flip value (2377.0 at the 55-source corpus; 2850.0 after the C2
    # census-sourced growth to 59 sources / 52 certified: legacy lineage
    # 3417.0, refined greedy 2859.0, the final-table GC retires the two
    # non-negative-marginal macros -> 8 macros @ 2850.0).  These are the
    # census-of-record REPRODUCTION pins (the point of the artifact).
    census = _census()
    assert census["census_math_mode"] == "refined"
    g = census["final_tables"]["governed"]
    u = census["final_tables"]["ungoverned"]
    reg = _reg()["census_of_record"]
    assert g["count"] == reg["governed"]["macro_count"]
    assert g["corpus_dl"] == reg["governed"]["corpus_dl"]
    assert u["count"] == reg["ungoverned"]["macro_count"]
    assert u["corpus_dl"] == reg["ungoverned"]["corpus_dl"]
    # the frozen LEGACY reconstruction is still the checkpoint's hash lineage.
    assert census["hash_verification"]["all_waves_match"] is True


def test_slot_congruence_realized_and_gc_adjudicated():
    # WP-FLIP (§12.1): under the refined census-of-record the congruence body is
    # realized by the greedy path, but the final-table GC retires it for its
    # non-negative marginal.  Priced against the refined+GC table it RE-adds at
    # +7.0 (admit False) -- the realized cost that justified the GC retirement.
    # Legacy pre-flip this was the -179 counterfactual against a table WITHOUT
    # the macro; the flip realized-then-adjudicated it.
    census = _census()
    slot = census["slot_measurement"]["governed"]
    adm = slot["slot_admission"]
    assert adm["delta"] == 7.0
    assert adm["admit"] is False
    assert adm["uses"] == 3
    # per-op flat variants are inadmissible (uses == 1)
    for fv in slot["flat_variants"]:
        assert fv["admission"]["admit"] is False
        assert fv["admission"]["uses"] == 1
    # the §11.3 zero-window blocker is LIFTED: force-only math windows now cover
    # the congruence cluster (0 -> 3).
    assert slot["total_windows_covering_cong_cluster"] == 3


def test_tower_gate_metric_is_realizable():
    # Corrected pass-2 headline (reviewer finding): the GATE metric is the
    # REALIZABLE adjacent-witness count -- a pair counts only where its covered
    # statements are uniform in (force, quote) across the union of both
    # invocations (H2, recurrence._demand_windows).  Under the WP-FLIP refined
    # census-of-record the governed MM census reads max=0 (C3 cycle-17 grown
    # corpus, where the GC pass retired five macros and the governed final table
    # fell 13 -> 11) with STILL ZERO pairs at/above the >=7 bar -- the T1 gate
    # stays correctly deferred, as it has through every era of this measurement
    # (the flip changes the rewritten stream the census walks, not the deferral;
    # §12.3 T1R re-registers its predicate against exactly this refined stream).
    # The max is a MOVING corpus measurement: what the tooth pins is the
    # deferral, not the height.
    census = _census()
    tw = census["tower_census"]["governed"]
    assert tw["gate_metric"] == "realizable_adjacent_witnesses"
    assert tw["level2_witness_bar"] == 7
    assert tw["max_witness_macro_macro_pair"] == 0
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
    # explicitly not-the-gate: the top MM pair reaches 32 raw adjacencies
    # (14 on the frozen run; it climbs with the corpus) yet collapses to max
    # realizable 0 -- the inflation the raw-count gate mis-measured, and the
    # collapse is now TOTAL.  The raw number is a MOVING corpus measurement;
    # what the tooth is really for is the collapse, and the pair count clearing
    # the bar.  One MM pair clears the >=7 bar on RAW count while none clears it
    # on the realizable gate metric.
    census = _census()
    tw = census["tower_census"]["governed"]
    assert "NOT the gate metric" in tw["raw_adjacent_note"]
    assert tw["max_raw_adjacent_witness_macro_macro_pair"] == 32
    assert tw["raw_adjacent_macro_macro_pairs_at_or_above_bar"] == 1


def test_subtree_numbers_present():
    census = _census()
    sub = census["subtree_census"]["governed"]["levels"]
    for lv in ("0", "1", "2"):
        assert "nonalias_at_least_2" in sub[lv]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)

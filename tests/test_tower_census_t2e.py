"""WP-T2E teeth: the gapped-idiom instrument + math_mode retrofit of the census.

Deterministic, LLM-free (house rule 5).  New file for a new package.  The teeth
are hand-built fixture corpora that pin the gapped-idiom DEFINITION exactly, plus
the two provenance / byte-identity guarantees the package promises:

  (a) a one-statement-gapped idiom is counted with the right witness count;
  (b) a two-statement gap is NOT counted (G is fixed at 1);
  (c) a gap straddling a force boundary is NOT counted (flanks non-uniform);
  (d) dream (system-origin) readings never add witnesses (E3);
  (e) the producing math_mode lands in the census provenance;
  (f) the DEFAULT census invocation is byte-identical to the committed artifact.

All fixtures are built here -- no checkpoint, no model -- except (e)/(f), which
run the tool on the committed checkpoint.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from bench import bench_formalize as bench           # noqa: E402
from tools import tower_census as tc      # noqa: E402


# --------------------------------------------------------------- tiny fixtures
def _stmt(sid, force, kind, *, quote="", op="="):
    return {"id": sid, "force": force, "quote": quote,
            "lf": {"kind": kind,
                   "pred": {"op": op, "args": [{"ref": "a"}, {"ref": "b"}]}}}


def _reading(sid, stmts, *, origin="exogenous", certified=True):
    return {"theorem": "t", "statements": stmts, "origin": origin,
            "_certified": certified, "_sid": sid}


def _gapped(readings):
    """Run the instrument in legacy mode with an empty table (governed filter)."""
    return tc._gapped_idiom_census(readings, {}, bench._EXO, "legacy")


# ------------------------------------------------------------------- the teeth
def test_a_one_statement_gap_counted_with_witnesses():
    # [A .. GAP .. B]: A and B uniform in (force, quote); the single interposed
    # statement carries a different force (a genuine interruption, so [A,G,B] is
    # NOT itself a contiguous window).  Two exogenous readings witness the SAME
    # flanking-kind idiom -> witness count 2.
    def mk(sid):
        return _reading(sid, [
            _stmt(sid + "-A", "assume", "hyp"),
            _stmt(sid + "-G", "choose", "amb"),      # the one interposed statement
            _stmt(sid + "-B", "assume", "hyp"),
        ])
    out = _gapped([mk("r1"), mk("r2")])
    assert out["g"] == 1
    assert out["n_distinct_gapped_idioms"] == 1
    idiom = out["gapped_idioms_g1"][0]
    assert idiom["gap"] == 1
    assert idiom["left_flank_len"] == 1
    assert idiom["witnesses"] == 2
    assert idiom["witness_sids"] == ["r1", "r2"]
    assert out["gapped_idioms_g1_at_least_2_witnesses"] == 1


def test_b_two_statement_gap_not_counted():
    # A and B recur two statements apart, and the interposed block is a different
    # force -- no single-statement (G=1) window can bridge the flanks, so the pair
    # is NOT a gapped idiom.  Zero idioms.
    def mk(sid):
        return _reading(sid, [
            _stmt(sid + "-A", "assume", "hypA"),
            _stmt(sid + "-P", "choose", "gapP"),     # two interposed statements,
            _stmt(sid + "-Q", "choose", "gapQ"),     # a different force
            _stmt(sid + "-B", "assume", "hypB"),
        ])
    out = _gapped([mk("r1"), mk("r2")])
    assert out["n_distinct_gapped_idioms"] == 0
    assert out["gapped_idioms_g1"] == []


def test_c_gap_straddling_force_boundary_not_counted():
    # The flanks sit on opposite sides of a force change: A is `assume`, B is
    # `conclude`.  The (force, quote) rule the miner enforces rejects the pair, so
    # the one-statement gap does NOT yield an idiom.
    def mk(sid):
        return _reading(sid, [
            _stmt(sid + "-A", "assume", "hyp"),
            _stmt(sid + "-G", "choose", "amb"),
            _stmt(sid + "-B", "conclude", "concl"),  # force boundary at the gap
        ])
    out = _gapped([mk("r1"), mk("r2")])
    assert out["n_distinct_gapped_idioms"] == 0


def test_c2_quote_boundary_not_counted_legacy():
    # Same shape but the boundary is a QUOTE change (legacy is strict-(force,
    # quote)); the flanks disagree on quote -> not counted.
    def mk(sid):
        return _reading(sid, [
            _stmt(sid + "-A", "demand", "hyp", quote="p"),
            _stmt(sid + "-G", "choose", "amb"),
            _stmt(sid + "-B", "demand", "hyp", quote="q"),  # quote boundary
        ])
    out = _gapped([mk("r1"), mk("r2")])
    assert out["n_distinct_gapped_idioms"] == 0


def test_d_dreams_never_witness():
    # Two exogenous readings + one dream (system-origin) reading, all three with
    # the same gapped idiom.  The dream must not add a witness: count stays 2.
    def mk(sid, **kw):
        return _reading(sid, [
            _stmt(sid + "-A", "assume", "hyp"),
            _stmt(sid + "-G", "choose", "amb"),
            _stmt(sid + "-B", "assume", "hyp"),
        ], **kw)
    out = _gapped([mk("r1"), mk("r2"),
                   mk("d1", origin="system", certified=True)])
    assert out["n_distinct_gapped_idioms"] == 1
    idiom = out["gapped_idioms_g1"][0]
    assert idiom["witnesses"] == 2
    assert "d1" not in idiom["witness_sids"]
    assert idiom["witness_sids"] == ["r1", "r2"]


def test_d2_uncertified_exogenous_does_not_witness():
    # Witness discipline mirrors the tower census: only CERTIFIED exogenous
    # readings witness.  An uncertified exogenous reading is not a witness.
    def mk(sid, **kw):
        return _reading(sid, [
            _stmt(sid + "-A", "assume", "hyp"),
            _stmt(sid + "-G", "choose", "amb"),
            _stmt(sid + "-B", "assume", "hyp"),
        ], **kw)
    out = _gapped([mk("r1"), mk("r2"), mk("u1", certified=False)])
    idiom = out["gapped_idioms_g1"][0]
    assert idiom["witness_sids"] == ["r1", "r2"]


# ---------------------------------------------- provenance + byte-identity teeth
def test_e_math_mode_provenance_lands_in_artifact():
    for mode in ("legacy", "refined"):
        census = tc.build_census(math_mode=mode, gapped_instrument=True)
        assert census["provenance"]["math_mode"] == mode
        assert census["provenance"]["gapped_idiom_g"] == 1
        gic = census["gapped_idiom_census"]["governed"]
        assert gic["g"] == 1
        assert "contiguous_admissible_remaining" in gic
        assert "gapped_idioms_g1" in gic
    # the DEFAULT build carries NO provenance / instrument block (byte-identity).
    default = tc.build_census()
    assert "provenance" not in default
    assert "gapped_idiom_census" not in default


def test_f_default_invocation_byte_identical_to_committed():
    committed_json = os.path.join(_ROOT, "results", "tower_census.json")
    committed_md = os.path.join(_ROOT, "results", "tower_census.md")
    with open(committed_json) as fh:
        want_json = fh.read()
    with open(committed_md) as fh:
        want_md = fh.read()
    census = tc.build_census()                 # default: legacy, no instrument
    assert tc.render_json(census) == want_json, \
        "default census JSON drifted from the committed artifact"
    assert tc.render_md(census) == want_md, \
        "default census Markdown drifted from the committed artifact"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)

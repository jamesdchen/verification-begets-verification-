"""Teeth for buildloop/lanes.py, buildloop/growth_protocol.py, and
tools/flywheel_probe.py.  Lean-gated pieces skip honestly; everything else
runs everywhere."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop import lanes, growth_protocol
from tools import flywheel_probe


# ---------------------------------------------------------------- lanes
def test_token_free_lane_makes_llm_calls_raise(monkeypatch):
    monkeypatch.delenv("CGB_TASK_TIME", raising=False)
    from buildloop.llm import call_llm, TaskTimeLLMViolation
    with lanes.token_free("test-lane"):
        assert lanes.current_lane() == "test-lane"
        with pytest.raises(TaskTimeLLMViolation):
            call_llm("this must never reach the CLI")
    # exact restoration: guard off again outside the lane.
    assert os.environ.get("CGB_TASK_TIME") is None
    assert lanes.current_lane() is None


def test_token_free_lane_nests_and_restores(monkeypatch):
    monkeypatch.setenv("CGB_TASK_TIME", "1")     # already guarded outside
    monkeypatch.setenv("CGB_LANE", "outer")
    with lanes.token_free("inner"):
        assert lanes.current_lane() == "inner"
    assert os.environ["CGB_TASK_TIME"] == "1"
    assert os.environ["CGB_LANE"] == "outer"


# ------------------------------------------------------- growth protocol
def test_every_registered_grower_conforms():
    for name in growth_protocol.GROWERS:
        roles = growth_protocol.conformance(name)
        assert set(roles) == set(growth_protocol.ROLES), name
        # at least one role of each grower is real resolvable code, so the
        # registry can never degenerate into pure prose.
        assert "code" in roles.values(), name


def test_drifted_dotted_name_fails_loudly():
    with pytest.raises((ImportError, AttributeError)):
        growth_protocol.resolve("generators.operator_growth.no_such_function")


def test_anti_list_is_disjoint_from_growers():
    for trust_root in growth_protocol.ANTI_LIST:
        assert trust_root not in growth_protocol.GROWERS


# -------------------------------------------------------- flywheel probe
def test_props_collect_deterministically():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    a_rows, a_skips = flywheel_probe.collect_props(root)
    b_rows, b_skips = flywheel_probe.collect_props(root)
    assert a_rows == b_rows and a_skips == b_skips
    # every committed reading lands somewhere: props or a NAMED skip.
    import glob
    n_readings = len(glob.glob(os.path.join(
        root, "specs", "mathsources", "readings", "*.json")))
    assert n_readings > 0
    assert len({r["source"] for r in a_rows}) + sum(a_skips.values()) \
        >= n_readings


def test_probe_defers_honestly_without_lean():
    if common.lean_available():
        pytest.skip("lean present: the gated test below covers this")
    rep = flywheel_probe.probe()
    assert rep["close_rate"] == "deferred: lean toolchain absent"
    assert rep["prop_set_sha"]                   # identity even when deferred


@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent (Lean-lane test)")
def test_probe_closes_ground_props_under_lean():
    rep = flywheel_probe.probe()
    if rep["n_props"] == 0:
        pytest.skip("no Nat-scope props in the committed corpus (honest zero)")
    assert isinstance(rep["close_rate"], float)
    # ground truths of the fragment must close on the frozen ladder.
    assert rep["close_rate"] > 0.0
    for rung in rep["by_rung"]:
        assert rung in ("decide", "omega", "norm_num", "simp")

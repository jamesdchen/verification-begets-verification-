"""Teeth for tools/regen_downstream.py -- the downstream-regeneration DAG.

LLM-free, network-free, and CHEAP: nothing here executes the heavy steps
(the committed-artifact tests already verify their outputs); these teeth pin
the DAG itself -- every step exists, the load-bearing order constraints
hold, and the CLI's list/resume surface works.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import regen_downstream as rd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_step_tool_exists():
    for name, cmd in rd.STEPS:
        path = os.path.join(ROOT, cmd[1])
        assert os.path.isfile(path), f"{name}: {cmd[1]} missing"


def _group_index(name):
    for gi, group in enumerate(rd.GROUPS):
        for chain in group:
            if name in chain:
                return gi
    raise AssertionError(f"{name} not in GROUPS")


def _chain_of(name):
    for group in rd.GROUPS:
        for chain in group:
            if name in chain:
                return chain
    raise AssertionError(f"{name} not in GROUPS")


def test_load_bearing_order_constraints():
    """The orderings the tools themselves enforce with STOP guards (shared-
    stream drift, KT-anchor reconciliation) plus the registry mutation:
    admit_proposals moves the admitted registry, so every replay-based
    artifact must come after it.  Concurrency is only legal ACROSS chains;
    ordered pairs must share a chain (in order) or sit in ordered groups."""
    def before(a, b):
        if _chain_of(a) is _chain_of(b):
            c = _chain_of(a)
            assert c.index(a) < c.index(b), f"{a} must precede {b} in-chain"
        else:
            assert _group_index(a) < _group_index(b), \
                f"{a}'s group must precede {b}'s (no edge inside a group)"

    before("entropy_refs", "ppm_ref")          # ppm_ref's drift guard
    before("ppm_ref", "c2_report")             # c2's KT reconciliation anchor
    before("subtree_mine", "admit_proposals")  # proposals staged before pricing
    for later in ("tower_census", "entropy_refs", "ppm_ref", "c2_report",
                  "measure_cluster_key", "campaign_dashboard"):
        before("admit_proposals", later)       # registry mutation first
    before("entropy_refs", "entropy_stack_fig")
    before("ppm_ref", "entropy_stack_fig")
    before("ppm_ref", "service_refs")  # math-domain numbers feed the profile
    # the dashboard renders across the parallel group's outputs: strictly after
    for earlier in ("tower_census", "c2_report", "measure_cluster_key",
                    "dl_trajectories_fig"):
        before(earlier, "campaign_dashboard")
    # frontier reads the census rollup: strictly after census_portfolio, and
    # in a group of its own (no edge inside a group -> it must not share one).
    before("census_portfolio", "frontier")
    before("frontier", "proof_queue")          # hammer pair after the DAG's
    before("proof_queue", "hammer_batch")      # census-facing artifacts


def test_flattened_steps_cover_groups_exactly():
    flat = [n for n, _ in rd.STEPS]
    from_groups = [n for g in rd.GROUPS for c in g for n in c]
    assert flat == from_groups
    assert len(flat) == len(set(flat)), "duplicate step"


def test_cli_list_and_unknown_step():
    r = subprocess.run(
        [sys.executable, "tools/regen_downstream.py", "--list"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0
    assert r.stdout.split() == [n for n, _ in rd.STEPS]
    r = subprocess.run(
        [sys.executable, "tools/regen_downstream.py", "--from", "nope"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 2
    assert "unknown step" in r.stdout

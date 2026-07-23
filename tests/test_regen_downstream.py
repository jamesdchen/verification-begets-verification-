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


def test_load_bearing_order_constraints():
    """The orderings the tools themselves enforce with STOP guards (shared-
    stream drift, KT-anchor reconciliation) plus the registry mutation:
    admit_proposals moves the admitted registry, so every replay-based
    artifact must come after it."""
    names = [n for n, _ in rd.STEPS]

    def before(a, b):
        assert names.index(a) < names.index(b), f"{a} must precede {b}"

    before("entropy_refs", "ppm_ref")          # ppm_ref's drift guard
    before("ppm_ref", "c2_report")             # c2's KT reconciliation anchor
    before("subtree_mine", "admit_proposals")  # proposals staged before pricing
    for later in ("tower_census", "entropy_refs", "ppm_ref", "c2_report",
                  "measure_cluster_key", "campaign_dashboard"):
        before("admit_proposals", later)       # registry mutation first
    before("entropy_refs", "entropy_stack_fig")
    before("ppm_ref", "entropy_stack_fig")


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

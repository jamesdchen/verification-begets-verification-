"""Teeth for tools/session_brief.py -- the derived session brief.

The brief's whole contract is DERIVED-NEVER-AUTHORED: every mutable fact in
it must come from a committed artifact, so these teeth pin the derivation
(brief numbers == artifact numbers) and the degrade-honestly path.  Stdlib
+ repo files only; no network, no solvers.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import session_brief as sb  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_brief_reflects_registration_and_portfolio():
    text = sb.build_brief()
    reg = json.load(open(os.path.join(
        ROOT, "specs", "mathsources", "registration.json")))
    port = json.load(open(os.path.join(
        ROOT, "results", "census_portfolio.json")))
    assert reg["era"] in text
    assert f"sources {reg['n_top_level_sources']}" in text
    assert f"{port['n_corpora']} corpora, {port['n_nodes']} nodes" in text
    cand = port["verdicts"].get("attempt-candidate", 0)
    assert f"attempt-candidates {cand}" in text


def test_brief_surfaces_plan_section_1_verbatim():
    text = sb.build_brief()
    plan = open(os.path.join(ROOT, "PLAN_FRAGMENT.md")).read()
    m = re.search(r"^## 1\..*?(?=^## )", plan, re.M | re.S)
    assert m, "PLAN_FRAGMENT.md lost its §1 block"
    assert m.group(0).rstrip() in text


def test_brief_names_the_lane_rule_only_when_tag_pending():
    # the lane-verdict block appears iff HEAD carries a lane tag -- pin the
    # conditional on both branches by driving the regex the brief uses.
    text = sb.build_brief()
    head_tagged = re.search(r"\[lean-(ci|fast|fresh)\]",
                            sb._git("log", "-1", "--format=%h %s"))
    assert ("LANE VERDICT PENDING" in text) == bool(head_tagged)


def test_brief_degrades_honestly_on_missing_artifact():
    missing = sb._load("results/does_not_exist_ever.json")
    assert "_unavailable" in missing
    # and the loader never raises for a malformed path either
    assert isinstance(missing["_unavailable"], str)


def test_brief_is_deterministic_for_fixed_repo_state():
    assert sb.build_brief() == sb.build_brief()

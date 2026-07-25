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


def test_brief_reports_the_supply_verdict_and_every_path_count():
    """The line that separates an idle machine from a wedged one.  Same
    recompute-and-assert contract as the rows above: every number in the
    SUPPLY line is re-read from results/supply_status.json, never authored
    here."""
    text = sb.build_brief()
    sup = json.load(open(os.path.join(ROOT, "results", "supply_status.json")))
    assert f"SUPPLY: {sup['verdict']}" in text
    assert f"ready {sup['frontier_ready']['count']}" in text
    for row in sup["paths"]:
        assert f"{row['path']}={row['count']}" in text


def test_brief_sits_the_supply_line_directly_after_purchases():
    """Ordering is the contract: supply reads the purchase queue, so it must
    land where a reader has just seen it -- not below the lane block."""
    lines = sb.build_brief().splitlines()
    purchases = [i for i, l in enumerate(lines) if l.startswith("PURCHASES:")]
    supply = [i for i, l in enumerate(lines) if l.startswith("SUPPLY:")]
    assert len(purchases) == len(supply) == 1
    assert supply[0] == purchases[0] + 1


def test_brief_shouts_when_the_supply_is_blocked_or_unknown(monkeypatch):
    """A blocked supply must not read as a quiet cycle.  Driven through
    SYNTHETIC verdicts, because the committed tree is not guaranteed to be
    wedged on any given day -- and the wedged rendering is exactly the one
    that must never rot."""
    real = sb._load

    def fake(rel, doc=None):
        return doc if rel == "results/supply_status.json" else real(rel)

    blocked = {"verdict": "supply-blocked: new-corpus-intake (6 corpora "
                          "already intaken)",
               "frontier_ready": {"count": 0, "known": True},
               "paths": [{"path": "new-corpus-intake", "count": 6}]}
    monkeypatch.setattr(sb, "_load", lambda rel: fake(rel, blocked))
    text = sb.build_brief()
    assert "SUPPLY BLOCKED" in text
    assert "new-corpus-intake=6" in text
    assert "SUPPLY UNKNOWN" not in text

    unknown = dict(blocked, verdict="supply-unknown: results/frontier.json")
    monkeypatch.setattr(sb, "_load", lambda rel: fake(rel, unknown))
    text = sb.build_brief()
    assert "SUPPLY UNKNOWN" in text
    assert "SUPPLY BLOCKED" not in text

    moving = dict(blocked, verdict="ready-work-available")
    monkeypatch.setattr(sb, "_load", lambda rel: fake(rel, moving))
    text = sb.build_brief()
    assert "SUPPLY: ready-work-available" in text
    assert "SUPPLY BLOCKED" not in text and "SUPPLY UNKNOWN" not in text


def test_brief_survives_a_missing_supply_reading(monkeypatch):
    """A half-built tree still gets a brief: the SUPPLY line degrades to a
    named line naming its own regeneration command, never a crash."""
    real = sb._load
    monkeypatch.setattr(sb, "_load", lambda rel: (
        {"_unavailable": "results/supply_status.json: missing"}
        if rel == "results/supply_status.json" else real(rel)))
    text = sb.build_brief()
    assert "SUPPLY: results/supply_status.json: missing" in text
    assert "python3 tools/supply_status.py" in text


def test_brief_degrades_honestly_on_missing_artifact():
    missing = sb._load("results/does_not_exist_ever.json")
    assert "_unavailable" in missing
    # and the loader never raises for a malformed path either
    assert isinstance(missing["_unavailable"], str)


def test_brief_is_deterministic_for_fixed_repo_state():
    assert sb.build_brief() == sb.build_brief()

"""A row's bill_class prices its AUTHORING; this prices whether the thing
authored would then decide anything.

For one row on the board those two questions have different answers, and
three consecutive firings measured that the hard way: PR #203, PR #212 and
the firing that added this module each ran `tools/lean_env_probe.py`, each
read `lean-local`, each was licensed by PLAN_FRAGMENT §3.1 rule 3 to take a
tower-class row, and each declined for a reason no instrument carried.
`tests/test_set_carrier_box_domain.py` had MEASURED the reason; it lived in
that module's docstrings, so the selection instrument a driver actually reads
(`results/purchase_frontier.json`) still routed the row to attendance.

CLAUDE.md: "a decision that branches on machine-readable state never ships as
a paragraph -- it ships as a tool the paragraph points at."  These teeth pin
the tool.

Everything asserted here is DERIVED at both ends: the domain arithmetic reads
`math_eval._box_size`, `math_eval.EXISTS_SHADOW_MAX_ASSIGNMENTS` and
`run/anchor.py::BOUND` live, and the published artifact is compared against a
fresh derivation rather than against a remembered number.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.math_eval import EXISTS_SHADOW_MAX_ASSIGNMENTS, _box_size
import tools.purchase_frontier as pf  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROW = "refusal-set-carrier"


def _artifact() -> dict:
    with open(os.path.join(HERE, "results", "purchase_frontier.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def _row(doc: dict, pid: str = ROW) -> dict:
    return next(r for r in doc["purchases"] if r["purchase_id"] == pid)


def _fresh() -> dict:
    """A FRESH derivation.  The committed artifact alone cannot red a builder
    regression -- it still carries yesterday's field until someone
    regenerates -- so every presence tooth below asserts against both."""
    return pf.build_purchase_frontier(HERE)


def test_the_bound_is_read_off_anchor_and_not_retyped():
    """A re-bound of the gate must re-price the row with no edit here."""
    assert pf._bound_of_record(HERE) == 8


def test_the_open_row_publishes_a_decision_domain_at_all():
    """The whole point: the price is ON the artifact a driver selects from."""
    for doc, where in ((_artifact(), "committed"), (_fresh(), "fresh")):
        row = _row(doc)
        assert row["status"] == "open", where
        assert "decision_domain" in row, (
            f"({where}) the open tower-class row no longer carries its "
            "decision-domain price; a driver reading this artifact is back "
            "to routing it to attendance, which is not its exit")


def test_the_published_domain_reproduces_from_the_live_gate_constants():
    """Byte-for-byte against a fresh derivation, so the number cannot rot."""
    published = _row(_artifact())["decision_domain"]
    fresh = pf._decision_domain(ROW, HERE)
    assert published == fresh


def test_the_lead_subject_prices_outside_the_decision_procedure():
    """The finding, stated as the artifact states it."""
    d = _row(_artifact())["decision_domain"]
    width = _box_size(["x"], {"x": "Int"}, 8)
    assert d["box_width"] == width == 17
    assert d["assignments"] == (2 ** width) ** 2 * width == 292057776128
    assert d["ceiling"] == EXISTS_SHADOW_MAX_ASSIGNMENTS
    assert d["inside_decision_procedure"] is False
    assert "ATTENDANCE IS NOT THIS ROW'S EXIT" in d["reading"]


def test_the_hazard_is_a_hang_and_not_an_honest_skip():
    """The sharper half.  `exists_shadow_shape` returns `forall-only` before
    it consults the ceiling, so the ceiling guards the exists path alone --
    and this row's lead subject is a DEFINITION, i.e. forall-only.  A paid
    tower would therefore not be honest-skipped as `exists-domain-too-large`.

    A row that merely returns 0 reads as unprofitable; a row that would HANG
    reads as something else, and the artifact has to say which."""
    d = _row(_artifact())["decision_domain"]
    assert d["ceiling_guards_this_subject"] is False
    assert d["hazard"] and "nothing would stop it" in d["hazard"]


def test_the_projection_separates_this_zero_from_a_co_refusal_zero():
    """Two different reasons for `returns_to_ready == 0`, and only one of
    them is retired by buying something else.

    The projection already carried `held_by_a_signal_this_row_does_not_meet`,
    which says "a co-refusal holds it" and invites meeting that co-refusal.
    For this row that would be the wrong next purchase: the sweep cannot run
    whatever else is met."""
    for doc, where in ((_artifact(), "committed"), (_fresh(), "fresh")):
        proj = next(r for r in doc["refill_projection"]["by_purchase"]
                    if r["purchase_id"] == ROW)
        assert proj["returns_to_ready"] == 0, where
        assert proj["held_by_a_signal_this_row_does_not_meet"] >= 1, where
        assert "outside_decision_domain" in proj, (
            f"({where}) the projection reports this row's 0 as pure "
            "co-refusal again")
        assert ("NOT only co-refusal"
                in proj["outside_decision_domain"]["reading"]), where


def test_a_row_with_no_measured_shape_publishes_nothing_rather_than_a_guess():
    """Omission must read as `not measured`, never as `decidable`.  Every
    other row on the board is unpriced on this axis, and none of them may
    acquire an `inside_decision_procedure: true` by default."""
    for doc, where in ((_artifact(), "committed"), (_fresh(), "fresh")):
        priced = {r["purchase_id"] for r in doc["purchases"]
                  if "decision_domain" in r}
        assert priced == set(pf.DECISION_DOMAINS), (where, priced)
        for r in doc["purchases"]:
            if r["purchase_id"] not in priced:
                assert "decision_domain" not in r, where
    assert pf._decision_domain("refusal-connectives", HERE) is None


def test_the_same_construct_at_one_nat_binder_prices_INSIDE():
    """The split line, executed rather than argued -- and the mutation that
    proves these teeth can go the other way.

    A row that is impossible at one carrier and cheap at another is two rungs
    wearing one name (the P8 and P9 finding).  Re-declaring the shape as ONE
    set binder over a Nat box flips `inside_decision_procedure` to True, so
    the classifier is measuring the shape and not hard-coding a verdict."""
    pid = "refusal-set-carrier"
    saved = pf.DECISION_DOMAINS[pid]
    try:
        pf.DECISION_DOMAINS[pid] = dict(saved, set_binders=1, carrier="Nat")
        cheap = pf._decision_domain(pid, HERE)
    finally:
        pf.DECISION_DOMAINS[pid] = saved
    assert cheap["box_width"] == _box_size(["x"], {"x": "Nat"}, 8) == 9
    assert cheap["assignments"] == (2 ** 9) * 9 == 4608
    assert cheap["inside_decision_procedure"] is True
    assert "DECIDABLE" in cheap["reading"]
    # and the row as actually declared is still the expensive one
    assert pf._decision_domain(pid, HERE)["inside_decision_procedure"] is False


def test_the_class_claim_cites_the_measurement_that_made_it():
    """`bill_class` is a declared intention; a declaration that USED to be
    measured is exactly the state house law forbids keeping in prose.  The
    builder enforces that a cited file exists and still contains the named
    test AND that the row's notes cite the same path -- this pins that the
    citation is actually present on this row."""
    declared = pf.PURCHASES[ROW]
    cites = declared.get("class_evidence") or []
    assert cites, "the tower-class claim stands on prose again"
    for path, needle in cites:
        assert os.path.isfile(os.path.join(HERE, path)), path
        with open(os.path.join(HERE, path), encoding="utf-8") as fh:
            assert needle in fh.read(), (path, needle)
        assert path in declared["notes"], (
            "class_evidence cites a measurement the published notes do not, "
            "so a reader cannot reach it")


def test_the_builder_reds_when_a_cited_measurement_stops_saying_it():
    """Mutation, in the direction that matters: renaming the proof out from
    under the declaration must RED rather than silently pass."""
    saved = pf.PURCHASES[ROW]["class_evidence"]
    try:
        pf.PURCHASES[ROW]["class_evidence"] = [
            ["tests/test_set_carrier_box_domain.py",
             "test_a_name_no_measurement_has_ever_carried"]]
        with pytest.raises(ValueError, match="class claim standing on a"):
            pf.build_purchase_frontier(HERE)
    finally:
        pf.PURCHASES[ROW]["class_evidence"] = saved

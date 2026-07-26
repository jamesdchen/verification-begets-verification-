"""Teeth for tools/supply_status.py -- the reading that must say WEDGED.

The defect this tool exists to abolish is an INSTRUMENT defect, not a data
defect: every fact needed to tell "idle with nothing to do" from "idle with
nothing it CAN do" was already committed, and no tool computed the
difference, so a wedged machine reported healthy.  The tooth that matters
here is therefore not a schema tooth: it is

    test_a_wedged_tree_must_say_supply_blocked_and_name_a_path

which drives a SYNTHETIC wedged tree (ready empty, no actionable purchase)
and demands that the verdict both says supply-blocked AND names a concrete
path with a concrete count.  Neuter the verdict logic into optimism and that
test is the one that goes red.

THE SECOND MEASURED DEFECT, and the second load-bearing tooth.  The tool
above shipped with the wedge's OWN blind spot: it counted census DEMAND and
never asked whether an unattended session may take the row carrying it, so
on a night when every open queue row was outside the additive class it
reported ``purchase-work-available`` at a machine that could not start one
of them -- and the watchdog reading it reported both loops healthy for eight
hours.  The tooth is

    test_tonights_committed_state_must_not_report_purchase_work_available

which runs the reading over the COMMITTED artifacts exactly as they are and
demands the answer agree with the queue's own declared bill classes.  It is
deliberately not a fixture: the state that was misreported was the real
tree's, and a tooth that can only fire on a synthetic one would have missed
it.  Per-class fixtures beside it pin the rule in both directions (an
additive row IS takeable; a tower-class row is NOT; a mixed queue reports
the additive one and names the other), because a whitelist checked only on
the days it says no is half a whitelist.

Everything else pins the derivation the way its siblings are pinned (the
test_frontier / test_purchase_frontier precedent): seed-drift byte identity,
determinism, ``derived_from`` pins so a moved input reads as STALENESS
distinct from a WRONG derivation, and every count re-derived from the
primary artifact rather than typed in here -- a hardcoded number in this
file would reintroduce exactly the staleness the tool measures.

Synthetic fixtures cover all four verdict shapes, because the shapes that
matter (wedged, unknown) are precisely the ones the committed tree is not
guaranteed to be sitting in on any given day.

Stdlib + repo files only; no network, no solvers, no wall-clock.
"""
import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common  # noqa: E402
from tools.supply_status import (  # noqa: E402
    ATTENDANCE_ROUTES,
    CANDIDATE_REGISTRY,
    DECLARATION_ACTIONABLE,
    INPUT_ABSENT,
    INPUTS,
    LEAN_ENV_IS_NOT_A_PERMISSION,
    PROMPT_TOKENS,
    UNATTENDED_BILL_CLASSES,
    UNBLOCKED_BY,
    VERDICT_CRITICAL,
    _write,
    build_supply_status,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
ARTIFACT = os.path.join(RESULTS, "supply_status.json")

_PATHS = set(UNBLOCKED_BY)
_ROW_FIELDS = {"path", "known", "available", "machine_actionable", "count",
               "count_of", "unblocked_by", "detail"}
_OPEN_ROW_FIELDS = {"purchase_id", "bill_class", "live_prices",
                    "live_refusal_demand", "declares_signals",
                    "has_live_demand", "unattended_takeable",
                    "machine_actionable"}
#: A declared class OUTSIDE the additive family, taken from the committed
#: queue rather than invented here -- a literal would let the whitelist and
#: the tooth drift apart, which is the shape of defect this file exists for.
_TOWER_CLASS = "tower-class"


def _committed():
    with open(ARTIFACT) as fh:
        return json.load(fh)


def _rows(doc):
    return {r["path"]: r for r in doc["paths"]}


def _frontier():
    with open(os.path.join(RESULTS, "frontier.json")) as fh:
        return json.load(fh)


# ------------------------------------------------------- synthetic fixtures
_TREE = itertools.count()


def _candidate_row(name, status):
    """A declared registry row carrying every field the registry requires,
    so no fixture exercises the declaration filter through a schema break it
    did not mean to test."""
    return {"adapter": "blueprint", "declared_by": "a fixture",
            "name": name, "project": "p", "rationale": "r",
            "source": f"https://example.invalid/{name}/", "status": status}


def _fixture(tmp_path, *, ready=(), blocked=(), purchases=(), parks=(),
             prompt="run tools/intake_from_frontier.py --ready --take N",
             n_corpora=3, candidates=(), registry=None, omit=()):
    """A tree carrying only this tool's declared inputs.

    Synthesized rather than copied: the shapes we most need to pin (a wedged
    supply, an unreadable queue) are states the committed tree may never be
    in, and a tooth that can only fire on today's data is not a tooth.

    Each call gets its OWN root: several teeth build two trees that differ by
    exactly one file, and a shared root would let the first tree's inputs
    survive the second tree's ``omit`` -- silently disarming every
    unreadable-input tooth."""
    root = os.path.join(str(tmp_path), f"tree{next(_TREE)}")
    os.makedirs(os.path.join(root, "results"), exist_ok=True)
    os.makedirs(os.path.join(root, os.path.dirname(CANDIDATE_REGISTRY)),
                exist_ok=True)

    def write(rel, text):
        if rel in omit:
            return
        with open(os.path.join(root, rel), "w") as fh:
            fh.write(text)

    write("results/frontier.json", json.dumps({
        "derived_from": {}, "honesty": "x",
        "ready": [{"corpus": "c", "node_id": n, "text_sha256": "0" * 64,
                   "suggested_source_name": n} for n in ready],
        "blocked": [{"signal": sig, "node_count": len(nodes),
                     "nodes": [{"corpus": "c", "node_id": nid,
                                "text_sha256": sha}
                               for nid, sha in nodes]}
                    for sig, nodes in blocked],
    }))
    write("results/purchase_frontier.json", json.dumps({
        "derived_from": {}, "honesty": "x", "purchases": list(purchases)}))
    write("results/census_portfolio.json", json.dumps({
        "n_corpora": n_corpora, "n_nodes": 1, "verdicts": {},
        "miss_histogram": {}, "honesty": "x", "corpora": []}))
    write("results/frontier_parks.jsonl",
          "".join(json.dumps(r, sort_keys=True) + "\n" for r in parks))
    write("C3_PROMPTS.md", prompt)
    # ``registry`` is the raw-bytes escape hatch for the unreadable case; the
    # ordinary path builds a well-formed registry from ``candidates``.
    write(CANDIDATE_REGISTRY,
          registry if registry is not None
          else json.dumps({"candidates": list(candidates)}))
    return root


def _open_row(pid, bill_class, prices=None, refusals=None, **extra):
    """An OPEN queue row.  ``bill_class`` is REQUIRED here exactly as the
    queue builder requires it, so no fixture can accidentally exercise the
    reading with the field the attendance rule turns on left out."""
    row = {"purchase_id": pid, "status": "open", "bill_class": bill_class,
           "prices_signals": dict(prices or {}),
           "blocking_refusals": dict(refusals or {})}
    row.update(extra)
    return row


def _wedged(tmp_path, **kw):
    """Ready empty, every purchase already purchased: the measured wedge."""
    kw.setdefault("purchases", [
        {"purchase_id": "p1", "status": "purchased",
         "prices_signals": {"sequences-sums": 111},
         "blocking_refusals": {}},
        {"purchase_id": "p5", "status": "trust-root",
         "prices_signals": {"real-analysis": 152},
         "blocking_refusals": {"iff-connective": 2}},
    ])
    kw.setdefault("blocked", [
        ("refused:iff-connective", [("n1", "a" * 64), ("n2", "b" * 64)]),
        ("refused:mod-operator", [("n1", "a" * 64)]),
    ])
    return _fixture(tmp_path, ready=(), **kw)


# ============================================================ THE MAIN TOOTH
def test_a_wedged_tree_must_say_supply_blocked_and_name_a_path(tmp_path):
    """HEALTHY and WEDGED must not be the same reading.

    Ready is empty and no purchase is actionable -- the exact state in which
    the watchdog reported both loops healthy.  The verdict must say
    supply-blocked, and it must NAME at least one concrete supply path with
    a concrete count: "blocked" with no named exit is a mood, not an
    instrument, and a count is what makes the name checkable."""
    doc = build_supply_status(_wedged(tmp_path))
    assert doc["frontier_ready"]["count"] == 0
    rows = _rows(doc)
    assert not any(r["machine_actionable"] for r in doc["paths"]), \
        "fixture is not wedged: something is machine-actionable"

    verdict = doc["verdict"]
    assert verdict.startswith("supply-blocked: "), verdict
    named = re.findall(r"([a-z][a-z-]+) \((\d+) ", verdict)
    assert named, f"verdict named no path with a count: {verdict}"
    for path, count in named:
        assert path in _PATHS, path
        assert rows[path]["count"] == int(count), path
        # a named path must actually be a path with supply behind it
        assert rows[path]["available"], path


def test_the_wedge_verdict_is_not_reachable_by_accident(tmp_path):
    """The same tree with ONE ready row must stop saying blocked -- the
    verdict has to be sensitive to the thing it claims to measure, otherwise
    a constant string would pass the tooth above."""
    blocked_doc = build_supply_status(_wedged(tmp_path))
    moving = _wedged(tmp_path)  # rewritten in place with a ready row
    with open(os.path.join(moving, "results/frontier.json")) as fh:
        f = json.load(fh)
    f["ready"] = [{"corpus": "c", "node_id": "n", "text_sha256": "0" * 64,
                   "suggested_source_name": "99_n"}]
    with open(os.path.join(moving, "results/frontier.json"), "w") as fh:
        json.dump(f, fh)
    assert blocked_doc["verdict"].startswith("supply-blocked: ")
    assert build_supply_status(moving)["verdict"] == "ready-work-available"


# ================================================= THE ATTENDANCE RULE TOOTH
def test_tonights_committed_state_must_not_report_purchase_work_available():
    """The reading over the COMMITTED artifacts must agree with the queue's
    own declared bill classes.

    This is the measured defect, pinned against the tree that carried it: on
    the night this tooth was written every OPEN row was outside the additive
    family, and the tool said purchase-work-available -- a green light at a
    machine that could not start one of them.  So the expectation is DERIVED
    from the queue rather than typed here, and it binds in BOTH directions:
    with no takeable row open the verdict may not be purchase-work-available,
    and with one open it must be.  Nothing here is a literal, so the tooth
    keeps meaning what it says as the queue turns over."""
    with open(os.path.join(RESULTS, "purchase_frontier.json")) as fh:
        opens = [r for r in json.load(fh)["purchases"] if r["status"] == "open"]
    doc = build_supply_status(ROOT)
    row = _rows(doc)["census-signal-ungating"]
    takeable = sorted(r["purchase_id"] for r in opens
                      if r.get("bill_class") in UNATTENDED_BILL_CLASSES)
    with_demand = {r["purchase_id"] for r in row["detail"]["open"]
                   if r["has_live_demand"]}

    assert row["detail"]["actionable_purchase_ids"] == [
        pid for pid in takeable if pid in with_demand]
    assert [p["purchase_id"] for p in
            row["detail"]["blocked_pending_attendance"]] == sorted(
        r["purchase_id"] for r in opens
        if r.get("bill_class") not in UNATTENDED_BILL_CLASSES
        and r["purchase_id"] in with_demand)

    if not row["detail"]["actionable_purchase_ids"]:
        assert doc["verdict"] != "purchase-work-available", (
            "the queue holds no open row an unattended session may take, and "
            "the reading said one was available -- this is the measured "
            "defect, not a stale expectation")
        assert not row["machine_actionable"] and row["count"] == 0
        if (doc["frontier_ready"]["count"] == 0
                and row["detail"]["blocked_pending_attendance"]):
            assert doc["verdict"].startswith(
                "supply-blocked: tower-class-only ("), doc["verdict"]
    else:
        assert doc["verdict"] in ("ready-work-available",
                                  "purchase-work-available"), doc["verdict"]


def test_an_additive_row_with_live_demand_is_machine_actionable(tmp_path):
    """The whitelist's YES side.  Every additive class must actually pass --
    a rule that only ever says no would stop the loop rather than describe
    it."""
    for bill_class in UNATTENDED_BILL_CLASSES:
        doc = build_supply_status(_fixture(
            tmp_path, ready=(),
            blocked=[("sets-cardinality", [("n", "a" * 64)])],
            purchases=[_open_row("p", bill_class,
                                 prices={"sets-cardinality": 0})]))
        row = _rows(doc)["census-signal-ungating"]
        assert row["detail"]["open"][0]["unattended_takeable"] is True, \
            bill_class
        assert row["machine_actionable"] and row["count"] == 1, bill_class
        assert doc["verdict"] == "purchase-work-available", bill_class


def test_a_tower_class_row_with_live_demand_is_not_machine_actionable(
        tmp_path):
    """The whitelist's NO side, and the exact state that was misreported.

    The row carries real, live, re-derived demand -- and PLAN_FRAGMENT §3.1
    rule 3 still forbids an unattended session from taking it.  Demand is
    not permission, and the verdict must say which of the two it has."""
    doc = build_supply_status(_fixture(
        tmp_path, ready=(),
        blocked=[("refused:set-membership", [("n", "a" * 64)])],
        purchases=[_open_row("refusal-set-carrier", _TOWER_CLASS,
                             refusals={"set-membership": 9})]))
    row = _rows(doc)["census-signal-ungating"]
    open_row = row["detail"]["open"][0]
    assert open_row["has_live_demand"] is True
    assert open_row["unattended_takeable"] is False
    assert open_row["machine_actionable"] is False
    assert row["machine_actionable"] is False and row["count"] == 0
    # the row is OPEN and it is SUPPLY -- reported, never dropped
    assert row["available"] is True and row["detail"]["n_open"] == 1
    assert row["detail"]["blocked_pending_attendance"] == [
        {"purchase_id": "refusal-set-carrier", "bill_class": _TOWER_CLASS}]

    verdict = doc["verdict"]
    assert verdict.startswith("supply-blocked: tower-class-only (1 open rows "
                              "need attendance or lean-local: "), verdict
    assert f"refusal-set-carrier [{_TOWER_CLASS}]" in verdict
    # blocked, never dead: the other exits stay named in the same breath
    assert "new-corpus-intake (" in verdict


def test_a_mixed_queue_reports_the_additive_row_and_names_the_other(tmp_path):
    """One takeable row and one not: the loop CAN move, so the verdict says
    so -- and the blocked row is still counted where a reader will see it,
    rather than vanishing behind the good news."""
    doc = build_supply_status(_fixture(
        tmp_path, ready=(),
        blocked=[("sets-cardinality", [("n", "a" * 64)]),
                 ("refused:set-membership", [("m", "b" * 64)])],
        purchases=[_open_row("p6", "additive-reflect",
                             prices={"sets-cardinality": 0}),
                   _open_row("p9", _TOWER_CLASS,
                             refusals={"set-membership": 0})]))
    row = _rows(doc)["census-signal-ungating"]
    assert doc["verdict"] == "purchase-work-available"
    assert row["detail"]["actionable_purchase_ids"] == ["p6"]
    assert row["count"] == 1 and row["detail"]["n_open"] == 2
    assert [p["purchase_id"] for p in
            row["detail"]["blocked_pending_attendance"]] == ["p9"]


def test_a_tower_row_without_live_demand_is_not_counted_as_pending(tmp_path):
    """blocked-pending-attendance counts rows with MATERIAL behind them.  A
    tower-class row whose signals price to zero is blocked twice over and is
    not the thing the verdict is reporting."""
    doc = build_supply_status(_fixture(
        tmp_path, ready=(), blocked=[("live-signal", [("n", "a" * 64)])],
        purchases=[_open_row("p9", _TOWER_CLASS,
                             prices={"dead-signal": 99})]))
    row = _rows(doc)["census-signal-ungating"]
    assert row["detail"]["open"][0]["has_live_demand"] is False
    assert row["detail"]["blocked_pending_attendance"] == []
    assert row["detail"]["open"][0]["unattended_takeable"] is False
    verdict = doc["verdict"]
    assert verdict.startswith("supply-blocked: ")
    assert "tower-class-only" not in verdict


def test_an_open_row_without_a_bill_class_fails_safe_to_unknown(tmp_path):
    """The field the attendance rule turns on is REQUIRED on an open row.
    Missing, empty or non-string, it is a schema break exactly like a
    missing status -- and a queue row whose bill shape we cannot read may
    never compute to "and you may take it"."""
    for bad in ({}, {"bill_class": ""}, {"bill_class": ["tower-class"]}):
        row = dict({"purchase_id": "p", "status": "open",
                    "prices_signals": {"s": 1}}, **bad)
        doc = build_supply_status(_fixture(
            tmp_path, ready=(), blocked=[("s", [("n", "a" * 64)])],
            purchases=[row]))
        path = _rows(doc)["census-signal-ungating"]
        assert path["known"] is False and "bill_class" in \
            path["detail"]["unavailable"], bad
        assert doc["verdict"].startswith("supply-unknown: "), bad
    # a NON-open row is never asked for one: the rule is about what a driver
    # firing may start, and a purchased row starts nothing.
    doc = build_supply_status(_fixture(
        tmp_path, ready=(),
        purchases=[{"purchase_id": "p1", "status": "purchased"}]))
    assert _rows(doc)["census-signal-ungating"]["known"] is True


def test_an_unlisted_bill_class_is_blocked_not_silently_allowed(tmp_path):
    """The whitelist fails toward inaction: a class nobody has argued into
    UNATTENDED_BILL_CLASSES is not takeable, whatever it is called.  A
    blacklist here would let the next bill class ship as a green light."""
    doc = build_supply_status(_fixture(
        tmp_path, ready=(), blocked=[("s", [("n", "a" * 64)])],
        purchases=[_open_row("p", "brand-new-bill-class", prices={"s": 0})]))
    row = _rows(doc)["census-signal-ungating"]
    assert row["detail"]["open"][0]["unattended_takeable"] is False
    assert not row["machine_actionable"]
    assert "brand-new-bill-class" in doc["verdict"]


def test_lean_env_is_never_read_as_a_permission(tmp_path):
    """Rule 3's capability condition admits only a probe RUN in-session.

    A committed results/lean_env.json saying lean-local is evidence about the
    machine that WROTE it, so this derived reading must be bit-for-bit
    indifferent to it -- and the artifact must SAY that, since an omission
    with no stated reason is the kind a later edit "fixes"."""
    assert "results/lean_env.json" not in INPUTS
    root = _fixture(
        tmp_path, ready=(), blocked=[("refused:s", [("n", "a" * 64)])],
        purchases=[_open_row("p", _TOWER_CLASS, refusals={"s": 1})])
    before = build_supply_status(root)
    with open(os.path.join(root, "results/lean_env.json"), "w") as fh:
        json.dump({"verdict": "lean-local", "scope": "the container"}, fh)
    after = build_supply_status(root)
    assert before == after
    assert after["verdict"].startswith("supply-blocked: tower-class-only (")
    note = _rows(after)["census-signal-ungating"]["detail"]["lean_env_note"]
    assert note == LEAN_ENV_IS_NOT_A_PERMISSION
    assert "RUN IN-SESSION" in note


def test_the_blocked_row_names_both_routes_that_would_unblock_it(tmp_path):
    """A tower-class reading that names no exit is the mood the whole tool
    forbids.  Both routes rule 3 actually grants must be named -- and no
    third one invented."""
    doc = build_supply_status(_fixture(
        tmp_path, ready=(), blocked=[("refused:s", [("n", "a" * 64)])],
        purchases=[_open_row("p", _TOWER_CLASS, refusals={"s": 1})]))
    routes = _rows(doc)["census-signal-ungating"]["detail"][
        "attendance_routes"]
    assert routes == ATTENDANCE_ROUTES
    assert "ATTENDED session" in routes
    assert "lean_env_probe.py RUN IN THE SESSION" in routes
    # UNBRACKETED by design: the route must be NAMED, but the bracketed form
    # is the lane's commit-message trigger and this string is one drivers are
    # instructed to quote.  tests/test_authoring_route.py owns that rule; here
    # we only pin that naming the route survived the respelling.
    assert "lean-hammer" in routes and "run/reflect_ride.py" in routes
    assert "[lean-hammer]" not in routes
    # the unblocker clause on the path row says the same thing, so a reader
    # who only reads the row still gets the exits
    assert ATTENDANCE_ROUTES in \
        _rows(doc)["census-signal-ungating"]["unblocked_by"]


# ------------------------------------------------- all four verdict shapes
def test_shape_ready_work_available(tmp_path):
    doc = build_supply_status(_fixture(tmp_path, ready=("n1", "n2")))
    assert doc["verdict"] == "ready-work-available"
    assert doc["frontier_ready"] == {"count": 2, "known": True}


def test_shape_purchase_work_available(tmp_path):
    """Ready empty, but an OPEN purchase carries a live nonzero price AND a
    bill class an unattended session may take: the purchase driver can move
    even though the corpus driver cannot."""
    root = _fixture(
        tmp_path, ready=(),
        blocked=[("sets-cardinality", [("n1", "a" * 64)])],
        purchases=[_open_row("p6", "additive-reflect",
                             prices={"sets-cardinality": 0})])
    doc = build_supply_status(root)
    assert doc["verdict"] == "purchase-work-available"
    row = _rows(doc)["census-signal-ungating"]
    assert row["machine_actionable"] and row["count"] == 1
    assert row["detail"]["actionable_purchase_ids"] == ["p6"]
    assert row["detail"]["blocked_pending_attendance"] == []
    assert row["detail"]["open"][0]["live_prices"] == {"sets-cardinality": 1}


def test_a_refusal_driven_purchase_counts_as_demand(tmp_path):
    """A refusal-driven row declares its demand as the refused:<signal>
    groups it would retire, NOT as a census price.  Counting only the price
    map would report a queue full of real demand as unactionable -- the same
    false-idle this tool exists to abolish."""
    root = _fixture(
        tmp_path, ready=(),
        blocked=[("refused:iff-connective", [("n1", "a" * 64),
                                             ("n2", "b" * 64)])],
        purchases=[_open_row("refusal-connectives", "additive-desugaring",
                             refusals={"iff-connective": 8})])
    doc = build_supply_status(root)
    row = _rows(doc)["census-signal-ungating"]
    open_row = row["detail"]["open"][0]
    # 8 is the queue's OWN number; 2 is the live frontier group -- we report
    # the one we re-derived.
    assert open_row["live_refusal_demand"] == {"iff-connective": 2}
    assert open_row["has_live_demand"] and open_row["declares_signals"]
    assert open_row["machine_actionable"]
    assert doc["verdict"] == "purchase-work-available"


def test_shape_supply_blocked_names_parks_when_parks_are_the_supply(tmp_path):
    root = _wedged(tmp_path, blocked=[], parks=[
        {"parked_by": "r", "reason": "evenodd-coverage-decision",
         "subject_sha256": "a" * 64},
        {"parked_by": "r", "reason": "evenodd-coverage-decision",
         "subject_sha256": "b" * 64},
    ])
    doc = build_supply_status(root)
    assert doc["verdict"].startswith("supply-blocked: ")
    assert "park-lifts (2 park ledger rows)" in doc["verdict"]
    assert "refusal-retirement" not in doc["verdict"], \
        "a path with no supply behind it must not be named as an exit"


def test_shape_supply_unknown_when_a_critical_input_does_not_read(tmp_path):
    """Reads fail safe: an errored read never impersonates an answer."""
    for rel in VERDICT_CRITICAL:
        doc = build_supply_status(_wedged(tmp_path, omit=(rel,)))
        assert doc["verdict"].startswith("supply-unknown: "), rel
        assert rel in doc["verdict"], rel
    # both gone -> both named, sorted
    doc = build_supply_status(_wedged(tmp_path, omit=tuple(VERDICT_CRITICAL)))
    assert doc["verdict"] == "supply-unknown: " + ", ".join(
        sorted(VERDICT_CRITICAL))


def test_every_verdict_is_in_the_declared_vocabulary(tmp_path):
    """The verdict is matched mechanically downstream, so the vocabulary is
    closed: four HEADS (three of them bare words), five shapes -- the two
    blocked shapes share a head on purpose, so tools/session_brief.py's
    ``startswith('supply-blocked')`` keeps meaning what it meant while a
    reader gets the distinction the head cannot carry."""
    seen, shapes = set(), set()
    for doc in (build_supply_status(_fixture(tmp_path, ready=("n",))),
                build_supply_status(_fixture(
                    tmp_path,
                    purchases=[_open_row("p", "additive-reflect",
                                         prices={"s": 0})],
                    blocked=[("s", [("n", "a" * 64)])])),
                build_supply_status(_fixture(
                    tmp_path,
                    purchases=[_open_row("p", _TOWER_CLASS, prices={"s": 0})],
                    blocked=[("s", [("n", "a" * 64)])])),
                build_supply_status(_wedged(tmp_path)),
                build_supply_status(_wedged(
                    tmp_path, omit=("results/frontier.json",))),
                _committed()):
        v = doc["verdict"]
        head = v.split(":")[0]
        assert head in {"ready-work-available", "purchase-work-available",
                        "supply-blocked", "supply-unknown"}, v
        if ":" in v:
            assert v.split(": ", 1)[1].strip(), f"empty verdict body: {v}"
        seen.add(head)
        shapes.add(head + ("/tower-class-only" if "tower-class-only" in v
                           else ""))
    assert len(seen) == 4, f"fixtures did not cover all four heads: {seen}"
    assert len(shapes) == 5, f"fixtures did not cover all five shapes: {shapes}"


# ------------------------------------------------------------- seed drift
def test_regenerate_byte_identical(tmp_path):
    """Re-derive from the committed inputs and byte-compare -- the
    seed-drift tooth."""
    out = tmp_path / "supply_status.json"
    _write(build_supply_status(ROOT), str(out))
    with open(out, "rb") as fh:
        regenerated = fh.read()
    with open(ARTIFACT, "rb") as fh:
        committed = fh.read()
    assert regenerated == committed, \
        ("supply_status.json drifted from its source -- regenerate: "
         "python3 tools/supply_status.py")


def test_determinism():
    """No wall-clock, no set-order leak, no dict-iteration surprise."""
    a = common.canonical_json(build_supply_status(ROOT))
    b = common.canonical_json(build_supply_status(ROOT))
    assert a == b


# ------------------------------------------- staleness is not wrongness
def test_derived_from_pins_current_inputs():
    """Every declared input is pinned by sha256.  A mismatch is recorded
    STALENESS demand (regenerate), reported distinctly from a WRONG
    derivation -- which is what the byte-compare tooth above catches."""
    doc = _committed()
    assert set(doc["derived_from"]) == set(INPUTS)
    stale = []
    for rel in INPUTS:
        full = os.path.join(ROOT, rel)
        live = INPUT_ABSENT
        if os.path.isfile(full):
            with open(full, "rb") as fh:
                live = common.sha256_bytes(fh.read())
        if doc["derived_from"][rel] != live:
            stale.append(rel)
    assert not stale, (f"input moved (staleness demand, not a wrong "
                       f"derivation): {stale} -- regenerate: "
                       f"python3 tools/supply_status.py")


def test_a_missing_input_is_pinned_absent_not_omitted(tmp_path):
    """A vanished input keeps its KEY and carries a sentinel: dropping the
    key would make "the input is gone" and "this artifact predates the pin"
    the same observation."""
    root = _wedged(tmp_path, omit=("C3_PROMPTS.md",))
    fresh = build_supply_status(root)
    assert set(fresh["derived_from"]) == set(INPUTS)
    assert fresh["derived_from"]["C3_PROMPTS.md"] == INPUT_ABSENT
    for rel in INPUTS:
        if rel != "C3_PROMPTS.md":
            assert re.fullmatch(r"[0-9a-f]{64}", fresh["derived_from"][rel]), rel


# ------------------------------------------------------------------ schema
def test_top_level_schema():
    doc = _committed()
    assert set(doc) == {"derived_from", "frontier_ready", "honesty", "paths",
                        "verdict"}
    assert set(doc["frontier_ready"]) == {"count", "known"}
    assert isinstance(doc["frontier_ready"]["count"], int)


def test_honesty_string_is_present_and_says_what_the_counts_are_not():
    doc = _committed()
    assert isinstance(doc["honesty"], str) and doc["honesty"].strip()
    # the claims the reading must never be read as making
    assert "never predictions" in doc["honesty"]
    assert "NEVER as absent" in doc["honesty"]
    assert "supply-unknown" in doc["honesty"]
    # and the two the attendance rule adds: a declared class is a
    # DECLARATION, and a blocked row is not a dead one
    assert "DECLARED bill_class" in doc["honesty"]
    assert "blocked, NEVER dead" in doc["honesty"]
    assert "results/lean_env.json is not consulted" in doc["honesty"]


def test_row_schema_exact_and_sorted():
    doc = _committed()
    assert [r["path"] for r in doc["paths"]] == sorted(_PATHS)
    for r in doc["paths"]:
        assert set(r) == _ROW_FIELDS, r["path"]
        assert isinstance(r["count"], int) and r["count"] >= 0
        for field in ("known", "available", "machine_actionable"):
            assert isinstance(r[field], bool), (r["path"], field)
        assert r["count_of"].strip()
        assert r["unblocked_by"] == UNBLOCKED_BY[r["path"]]
        assert r["unblocked_by"].strip()


def test_every_path_names_its_unblocker():
    """A blocked reading whose paths do not name their exits is a mood."""
    assert set(UNBLOCKED_BY) == {"census-signal-ungating", "new-corpus-intake",
                                 "park-lifts", "refusal-retirement"}
    for path, clause in UNBLOCKED_BY.items():
        assert len(clause.split()) >= 8, path


# --------------------------------------- counts are read, never authored
def test_refusal_counts_are_rederived_from_the_frontier():
    """Re-derive the refused rollup from the primary artifact.  A number
    typed into this test would reintroduce the staleness the tool measures,
    so nothing here is a literal."""
    f = _frontier()
    groups = [g for g in f["blocked"] if g["signal"].startswith("refused:")]
    subjects = {n["text_sha256"] for g in groups for n in g["nodes"]}
    row = _rows(_committed())["refusal-retirement"]
    assert row["detail"]["n_groups"] == len(groups)
    assert row["detail"]["n_group_entries"] == sum(
        g["node_count"] for g in groups)
    assert row["detail"]["n_distinct_subjects"] == len(subjects)
    assert row["count"] == len(subjects)
    assert row["available"] == bool(subjects)
    assert row["detail"]["by_signal"] == {
        g["signal"]: g["node_count"] for g in groups}


def test_ready_count_is_rederived_from_the_frontier():
    assert _committed()["frontier_ready"]["count"] == len(_frontier()["ready"])


def test_park_count_is_rederived_from_the_ledger():
    ledger = os.path.join(RESULTS, "frontier_parks.jsonl")
    rows = [l for l in open(ledger).read().splitlines() if l.strip()] \
        if os.path.exists(ledger) else []
    row = _rows(_committed())["park-lifts"]
    assert row["count"] == len(rows)
    assert row["available"] == bool(rows)


def test_corpora_count_is_rederived_from_the_census():
    with open(os.path.join(RESULTS, "census_portfolio.json")) as fh:
        census = json.load(fh)
    assert _rows(_committed())["new-corpus-intake"]["count"] == \
        census["n_corpora"]


def test_open_purchase_prices_are_rederived_from_the_frontier_not_the_queue(
        tmp_path):
    """The queue file carries its own priced counts; we must NOT copy them.

    The fixture prices a signal the frontier does not carry at all and gives
    the queue a fat number for it: trusting the queue would compute
    actionable, re-deriving computes zero."""
    root = _fixture(
        tmp_path, ready=(), blocked=[("live-signal", [("n", "a" * 64)])],
        purchases=[_open_row("p9", "additive-reflect",
                             prices={"stale-signal": 999},
                             refusals={"stale-refusal": 999})])
    doc = build_supply_status(root)
    row = _rows(doc)["census-signal-ungating"]
    assert row["detail"]["open"][0]["live_prices"] == {"stale-signal": 0}
    assert row["detail"]["open"][0]["live_refusal_demand"] == {
        "stale-refusal": 0}
    assert not row["machine_actionable"]
    assert doc["verdict"].startswith("supply-blocked: ")


def test_committed_queue_statuses_are_read_not_assumed():
    """The census-ungating row reflects the OPEN rows of the committed
    queue, whatever they happen to be today -- including each row's DECLARED
    bill_class, re-read from the queue rather than restated here."""
    with open(os.path.join(RESULTS, "purchase_frontier.json")) as fh:
        queue = json.load(fh)
    opens = [r for r in queue["purchases"] if r["status"] == "open"]
    row = _rows(_committed())["census-signal-ungating"]
    assert row["detail"]["n_open"] == len(opens)
    assert [r["purchase_id"] for r in row["detail"]["open"]] == sorted(
        r["purchase_id"] for r in opens)
    # and every demand number on those rows is the LIVE frontier count, for
    # both the ways a row may declare demand
    live = {g["signal"]: g["node_count"] for g in _frontier()["blocked"]}
    by_id = {r["purchase_id"]: r for r in opens}
    for r in row["detail"]["open"]:
        assert set(r) == _OPEN_ROW_FIELDS, r["purchase_id"]
        src = by_id[r["purchase_id"]]
        assert r["bill_class"] == src["bill_class"]
        assert r["live_prices"] == {
            s: live.get(s, 0) for s in src.get("prices_signals", {})}
        assert r["live_refusal_demand"] == {
            s: live.get("refused:" + s, 0)
            for s in src.get("blocking_refusals", {})}
        assert r["has_live_demand"] == any(
            n > 0 for n in list(r["live_prices"].values())
            + list(r["live_refusal_demand"].values()))
        assert r["unattended_takeable"] == (
            src["bill_class"] in UNATTENDED_BILL_CLASSES)
        assert r["machine_actionable"] == (
            r["has_live_demand"] and r["unattended_takeable"])


# ------------------------------------- the queue may grow; we may not guess
def test_unknown_queue_fields_are_tolerated(tmp_path):
    """The queue is free to grow rows and fields; we read only the three we
    have always read, and new ones must not perturb the reading."""
    plain = build_supply_status(_fixture(
        tmp_path, purchases=[_open_row("p", "additive-reflect",
                                       prices={"s": 0})],
        blocked=[("s", [("n", "a" * 64)])]))
    grown = build_supply_status(_fixture(
        tmp_path, purchases=[_open_row(
            "p", "additive-reflect", prices={"s": 0},
            refill_projection={"eta": "later"}, brand_new_field=[1, 2, 3])],
        blocked=[("s", [("n", "a" * 64)])]))
    assert plain["paths"] == grown["paths"]
    assert plain["verdict"] == grown["verdict"] == "purchase-work-available"


def test_a_row_without_a_status_fails_safe_to_unknown(tmp_path):
    """A schema break is not a measurement: we may not report "nothing is
    open" from a queue we could not read."""
    doc = build_supply_status(_fixture(
        tmp_path, purchases=[{"purchase_id": "p", "prices_signals": {}}]))
    row = _rows(doc)["census-signal-ungating"]
    assert row["known"] is False and "unavailable" in row["detail"]
    assert doc["verdict"].startswith("supply-unknown: ")


def test_an_open_row_declaring_no_signals_is_open_but_not_actionable(tmp_path):
    """Both signal maps absent: the row is open, but nothing we can
    re-derive says anything moves.  Reported as open-and-unactionable, never
    silently dropped from the count of what is open."""
    doc = build_supply_status(_fixture(
        tmp_path, purchases=[_open_row("p", "additive-reflect")]))
    row = _rows(doc)["census-signal-ungating"]
    assert row["known"] and row["available"] and not row["machine_actionable"]
    assert row["detail"]["n_open"] == 1
    assert row["detail"]["open"][0]["declares_signals"] is False
    assert row["detail"]["open"][0]["unattended_takeable"] is True
    # takeable class, no material: blocked on DEMAND, not on attendance
    assert row["detail"]["blocked_pending_attendance"] == []
    assert doc["verdict"].startswith("supply-blocked: ")
    assert "tower-class-only" not in doc["verdict"]


# ------------------------------------ the prompt reading fails toward unknown
def test_prompt_automation_miss_reads_unknown_never_absent(tmp_path):
    """A substring we did not find is evidence about a file, never proof
    about the loop -- and the file is edited by other work."""
    for prompt, expect in (
            ("nothing relevant here", "unknown"),
            ("run tools/intake_from_frontier.py", "automates-ready-list-only"),
            ("run tools/intake_corpus.py --name X", "automates-new-corpus-intake"),
    ):
        doc = build_supply_status(_fixture(tmp_path, prompt=prompt))
        row = _rows(doc)["new-corpus-intake"]
        assert row["detail"]["prompt_automation"] == expect, prompt
        assert set(row["detail"]["prompt_mentions"]) == set(PROMPT_TOKENS)
    # an unreadable prompt is unknown too, and never crashes the reading
    doc = build_supply_status(_fixture(tmp_path, omit=("C3_PROMPTS.md",)))
    assert _rows(doc)["new-corpus-intake"]["detail"]["prompt_automation"] == \
        "unknown"


def test_new_corpus_intake_is_always_available_and_always_named(tmp_path):
    """The supply is outside the tree, so this path is never exhausted --
    which is what keeps a supply-blocked verdict from degenerating into a
    bare word with no exit named."""
    doc = build_supply_status(_wedged(tmp_path, blocked=[], parks=[]))
    row = _rows(doc)["new-corpus-intake"]
    assert row["available"] is True
    assert "new-corpus-intake (" in doc["verdict"]
    assert "driver-automation:" in doc["verdict"]


# ------------------------------------------------- THE DECLARATION FILTER
# The attendance filter's defect, one path over, and measured the same way:
# on 2026-07-26 (C3 cycle 21) the driver's own selector answered
# `registry-exhausted` and this reading named new-corpus-intake as an exit in
# the same firing's supply-blocked verdict, because machine_actionable was
# gated on a grep of the PROMPT and never on the REGISTRY the prompt sends
# the driver to.  These teeth pin the rule in both directions -- a whitelist
# checked only on the days it says no is half a whitelist.
def test_a_dry_registry_is_available_but_not_machine_actionable(tmp_path):
    """The prompt knows the command; there is no row to run it on.

    AVAILABLE and MACHINE-ACTIONABLE must part company here: the supply is
    outside the tree (an attended session may name any corpus), so the path
    stays available and stays NAMED in the verdict -- but no driver firing
    can walk it, and the verdict a watchdog quotes verbatim must say so."""
    prompt = "run python3 tools/intake_corpus.py --name X"
    for candidates, expect in (
            ((), "registry-empty"),
            ((_candidate_row("spent", "intaken"),
              _candidate_row("refused_one", "refused")), "registry-exhausted"),
    ):
        doc = build_supply_status(
            _wedged(tmp_path, prompt=prompt, candidates=candidates))
        row = _rows(doc)["new-corpus-intake"]
        assert row["detail"]["declaration_reason"] == expect, expect
        assert row["detail"]["prompt_automation"] == \
            "automates-new-corpus-intake", expect
        assert row["available"] is True, expect
        assert row["machine_actionable"] is False, expect
        # the verdict is the watchdog's only view: it must carry the reason
        assert f"declaration: {expect} -- NOT unattended-takeable" in \
            doc["verdict"], doc["verdict"]
        assert doc["verdict"].startswith("supply-blocked: "), doc["verdict"]


def test_a_declared_candidate_is_machine_actionable(tmp_path):
    """The other direction: one row marked ``candidate`` and the path IS
    walkable unattended -- otherwise this gate would be a way of never
    reporting the one lever that has ever moved the ready list."""
    doc = build_supply_status(_wedged(
        tmp_path, prompt="run python3 tools/intake_corpus.py --name X",
        candidates=(_candidate_row("spent", "intaken"),
                    _candidate_row("declared", "candidate"))))
    row = _rows(doc)["new-corpus-intake"]
    assert row["detail"]["declaration_reason"] == "candidate-available"
    assert row["detail"]["declaration_reason"] in DECLARATION_ACTIONABLE
    assert row["machine_actionable"] is True
    assert "NOT unattended-takeable" not in doc["verdict"], doc["verdict"]


def test_both_halves_are_required_for_the_new_corpus_path(tmp_path):
    """A declared row does not make an UNAUTOMATED prompt walkable, and an
    automating prompt does not conjure a row.  Either half alone is the
    defect this filter closes, so neither alone may compute actionable."""
    declared = (_candidate_row("declared", "candidate"),)
    for prompt, candidates, expect in (
            ("run tools/intake_from_frontier.py --ready", declared, False),
            ("nothing relevant here", declared, False),
            ("run python3 tools/intake_corpus.py --name X", (), False),
            ("run python3 tools/intake_corpus.py --name X", declared, True),
    ):
        doc = build_supply_status(
            _wedged(tmp_path, prompt=prompt, candidates=candidates))
        assert _rows(doc)["new-corpus-intake"]["machine_actionable"] is expect, \
            (prompt, expect)


def test_an_unreadable_registry_is_never_read_as_no_candidates(tmp_path):
    """An errored read must not impersonate an answer -- in EITHER direction.

    It is not "there are candidates" (that would report a path a driver
    cannot walk) and it is not silently "registry-exhausted" either: it
    carries its own named reason, and inaction is the safe side."""
    for kw, expect in (
            ({"omit": (CANDIDATE_REGISTRY,)}, "registry-absent"),
            ({"registry": "{not json at all"}, "registry-unreadable"),
            ({"registry": json.dumps({"candidates": "not a list"})},
             "registry-unreadable"),
    ):
        doc = build_supply_status(_wedged(
            tmp_path, prompt="run python3 tools/intake_corpus.py --name X",
            **kw))
        row = _rows(doc)["new-corpus-intake"]
        assert row["detail"]["declaration_reason"] == expect, expect
        assert row["machine_actionable"] is False, expect
        # unreadable is not verdict-critical: the reading still answers
        assert doc["verdict"].startswith("supply-blocked: "), expect


def test_committed_declaration_state_is_read_from_the_selector_not_restated():
    """The tooth that would have fired on the day this defect was measured.

    Run over the COMMITTED tree exactly as it is (the bill_class tooth's
    precedent: the state that was misreported was the real tree's), and
    demand this reading agree with what a driver firing's OWN selector says
    -- delegated, never restated, because two implementations of one rule
    drift and that drift is the whole defect."""
    import tools.corpus_candidates as cc
    sel = cc.select()
    row = _rows(_committed())["new-corpus-intake"]
    assert row["detail"]["declaration_reason"] == sel["reason"]
    assert row["detail"]["declared_counts"] == sel["counts"]
    assert row["machine_actionable"] == (
        row["detail"]["prompt_automation"] == "automates-new-corpus-intake"
        and sel["reason"] in DECLARATION_ACTIONABLE)
    # and the committed verdict may never name this path as an exit a driver
    # can take while the selector is answering that it cannot
    if not row["machine_actionable"] and "new-corpus-intake (" in \
            _committed()["verdict"]:
        assert "NOT unattended-takeable" in _committed()["verdict"]


def test_park_lifts_and_refusals_are_never_machine_actionable(tmp_path):
    """Both wait on a human act (a decision, a purchase).  If either could
    compute to machine-actionable, this reading would be claiming authority
    it does not have."""
    doc = build_supply_status(_wedged(tmp_path, parks=[
        {"parked_by": "r", "reason": "evenodd-coverage-decision",
         "subject_sha256": "a" * 64}]))
    for path in ("park-lifts", "refusal-retirement"):
        assert _rows(doc)[path]["machine_actionable"] is False, path


def test_a_malformed_park_ledger_is_unknown_but_an_absent_one_is_zero(
        tmp_path):
    """An absent ledger IS zero rows by construction; a present unparseable
    one is not a measurement."""
    absent = build_supply_status(_wedged(
        tmp_path, omit=("results/frontier_parks.jsonl",)))
    assert _rows(absent)["park-lifts"] == dict(
        _rows(absent)["park-lifts"], known=True, count=0, available=False)

    root = _wedged(tmp_path)
    with open(os.path.join(root, "results/frontier_parks.jsonl"), "w") as fh:
        fh.write("{not json\n")
    row = _rows(build_supply_status(root))["park-lifts"]
    assert row["known"] is False and "unavailable" in row["detail"]
    # a non-critical input going dark degrades its row, never the verdict
    assert build_supply_status(root)["verdict"].startswith("supply-blocked: ")

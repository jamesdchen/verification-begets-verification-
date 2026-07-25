"""Teeth for tools/purchase_frontier.py -- the committed, plan-keyed view of
the §4 purchase queue with live census prices and live refusal demand.

LLM-free, Lean-free, network-free.  These teeth pin, against the COMMITTED
tree (results/purchase_frontier.json + the frontier + the census + the growth
registry):

- seed-drift byte identity and determinism (the test_frontier /
  test_proof_queue precedent);
- reconciliation via the PINNED input sha256s: "an input moved" reads as
  recorded STALENESS demand, distinct from "the derivation is wrong";
- exact schema, and row order == the declared queue order (§4's strict
  tractability order is DATA, not presentation);
- every price RE-DERIVED from the frontier artifact -- a hardcoded count here
  would be the thing this tool exists to abolish -- on BOTH axes: the census
  prices and the refusal groups the refusal-priced rows are declared against;
- the REFILL PROJECTION: re-derived node-by-node from the frontier's refused
  groups, reconciled against them signal-for-signal, and asserted to EXIST
  whenever the window is empty and open rows are declared (the reading whose
  absence let "0 open" coexist with a full refusal ledger);
- the dead-term canary applied to DEMAND: every refusal signal either names a
  real purchase row or carries the reason no purchase meets it, and a signal
  that names a row must actually be published on it;
- the vocabularies name their content: every BILL_CLASSES entry carries a
  description, every refusal signal is mapped, and every unmapped signal
  carries a REASON (a queue that silently drops a refusal is manufacturing
  its own tidiness);
- the status rule, exercised against SYNTHETIC registries so the derivation
  is pinned independently of what happens to be landed today;
- and the two rows that can never compute to purchased: P5 (trust-root, even
  with a grower row planted under its name) and the parked pair.
"""
import copy
import json
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common  # noqa: E402
from tools.purchase_frontier import (  # noqa: E402
    BILL_CLASSES,
    INPUTS,
    PURCHASES,
    RECEIPT_ABSENT,
    REFUSED_PREFIX,
    REGISTRY,
    SIGNAL_UNBLOCKED_BY,
    _STATUSES,
    _load_registry,
    _receipt_ok,
    _unblocked_by,
    _write,
    build_purchase_frontier,
    derive_status,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
ARTIFACT = os.path.join(RESULTS, "purchase_frontier.json")

#: Every receipt path any row declares, deduplicated -- p3-split and p4-split
#: deliberately share one document, so the pin set is over PATHS.
DECLARED_RECEIPTS = sorted({p for r in PURCHASES.values()
                            for p, _needle in r["receipts"]})


def _scratch_root(tmp_path, *, registry_text=None):
    """A second repo root carrying real copies of every input.

    The teeth below have to be able to say "the tool read THAT tree", which
    needs a tree that is not this one.  Copied rather than synthesized: the
    builder validates its declarations against the live census vocabulary and
    the live anti-list, and a synthetic stub would test a queue nobody ships."""
    for rel in list(INPUTS) + DECLARED_RECEIPTS:
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, rel), str(dest))
    if registry_text is not None:
        (tmp_path / REGISTRY).write_text(registry_text)
    return str(tmp_path)

_ROW_FIELDS = {"purchase_id", "plan_ref", "title", "bill_class", "status",
               "prices_signals", "blocking_refusals", "receipts", "notes"}


def _committed():
    with open(ARTIFACT) as fh:
        return json.load(fh)


def _frontier():
    with open(os.path.join(RESULTS, "frontier.json")) as fh:
        return json.load(fh)


def _frontier_counts():
    return {g["signal"]: g["node_count"] for g in _frontier()["blocked"]}


def _refused_by_node():
    """(corpus, node_id) -> frozenset of refusal signals, recomputed HERE.

    Deliberately a second implementation rather than an import of the tool's
    helper: the projection's whole claim is that it read the frontier, and a
    tooth that calls the same function to check it would only assert the
    function is deterministic."""
    per: dict = {}
    for g in _frontier()["blocked"]:
        if not g["signal"].startswith(REFUSED_PREFIX):
            continue
        sig = g["signal"][len(REFUSED_PREFIX):]
        for n in g["nodes"]:
            per.setdefault((n["corpus"], n["node_id"]), set()).add(sig)
    return {k: frozenset(v) for k, v in per.items()}


# --------------------------------------------------------------- seed drift
def test_regenerate_byte_identical(tmp_path):
    """Re-derive from the committed inputs and byte-compare against the
    committed artifact -- the seed-drift tooth."""
    fresh = build_purchase_frontier(ROOT)
    out = tmp_path / "purchase_frontier.json"
    _write(fresh, str(out))
    with open(out, "rb") as fh:
        regenerated = fh.read()
    with open(ARTIFACT, "rb") as fh:
        committed = fh.read()
    assert regenerated == committed, \
        "purchase_frontier.json drifted from its source"


def test_determinism():
    """Two independent builds are identical (no wall-clock, no set-order
    leak, no dict-iteration surprise)."""
    a = common.canonical_json(build_purchase_frontier(ROOT))
    b = common.canonical_json(build_purchase_frontier(ROOT))
    assert a == b


# --------------------------------------------------- reconciliation via pins
def test_derived_from_pins_current_inputs():
    """derived_from pins the sha256 of EVERY input file -- including the
    growth-registry SOURCE TEXT and every declared RECEIPT, because status is
    read off both.  A mismatch is recorded STALENESS demand (regenerate),
    reported distinctly from a wrong derivation (the byte-compare tooth
    above)."""
    doc = _committed()
    assert set(doc["derived_from"]) == set(INPUTS) | set(DECLARED_RECEIPTS)
    stale = []
    for rel in set(INPUTS) | set(DECLARED_RECEIPTS):
        full = os.path.join(ROOT, rel)
        live = RECEIPT_ABSENT
        if os.path.isfile(full):
            with open(full, "rb") as fh:
                live = common.sha256_bytes(fh.read())
        if doc["derived_from"][rel] != live:
            stale.append(rel)
    assert not stale, f"input moved (staleness demand): {stale}"


def test_a_missing_receipt_is_pinned_as_absent_not_omitted(tmp_path):
    """A receipt that vanishes must read as STALENESS, not as a schema
    change: the key stays and carries an explicit sentinel.  Dropping the key
    instead would make "the receipt is gone" and "this artifact predates
    receipt pinning" the same observation."""
    doc = _committed()
    assert DECLARED_RECEIPTS, "no row declares a receipt any more"
    for rel in DECLARED_RECEIPTS:
        assert rel in doc["derived_from"], rel
    root = _scratch_root(tmp_path)
    victim = DECLARED_RECEIPTS[0]
    os.remove(os.path.join(root, victim))
    fresh = build_purchase_frontier(root)
    assert fresh["derived_from"][victim] == RECEIPT_ABSENT
    assert fresh["derived_from"][victim] != doc["derived_from"][victim]


# -------------------------------------------------------------------- schema
def test_top_level_schema():
    doc = _committed()
    assert set(doc) == {"derived_from", "purchases", "refill_projection",
                        "honesty"}
    assert isinstance(doc["honesty"], str) and doc["honesty"].strip()


def test_row_schema_exact():
    doc = _committed()
    for r in doc["purchases"]:
        assert set(r) == _ROW_FIELDS, r["purchase_id"]
        assert r["status"] in _STATUSES
        assert r["bill_class"] in BILL_CLASSES
        assert isinstance(r["plan_ref"], str) and r["plan_ref"].strip()
        assert isinstance(r["title"], str) and r["title"].strip()
        assert isinstance(r["notes"], str) and r["notes"].strip()
        assert isinstance(r["prices_signals"], dict)
        for sig, n in r["prices_signals"].items():
            assert isinstance(n, int) and n >= 0, sig
        for sig, n in r["blocking_refusals"].items():
            assert isinstance(n, int) and n >= 0, sig
        assert r["receipts"] == sorted(r["receipts"])


def test_row_order_is_the_declared_queue_order():
    """§4's strict tractability order is DATA: each row rides the machinery
    the row above it bought (a split precedes its carrier), so the artifact
    preserves declaration order instead of re-sorting into alphabet."""
    doc = _committed()
    assert [r["purchase_id"] for r in doc["purchases"]] == list(PURCHASES)


# ------------------------------------------- prices are read, never authored
def test_prices_are_rederived_from_the_frontier():
    """Every priced count equals the live frontier blocked-group count.  A
    number typed into this queue by hand is exactly the staleness the tool
    exists to abolish."""
    counts = _frontier_counts()
    for r in _committed()["purchases"]:
        for sig, n in r["prices_signals"].items():
            assert n == counts.get(sig, 0), (r["purchase_id"], sig)


def test_prices_are_census_vocabulary():
    """A queue priced in words the census does not measure is priced in
    nothing."""
    with open(os.path.join(RESULTS, "census_portfolio.json")) as fh:
        vocab = set(json.load(fh)["miss_histogram"])
    for pid, row in PURCHASES.items():
        for sig in row["prices_signals"]:
            assert sig in vocab, (pid, sig)


def test_every_row_is_priced_on_one_axis_or_the_other():
    """Two axes price this queue -- census vocabulary and the measured
    refusal ledger -- and a row may sit on either or both, but never on
    neither.  An unpriced row is "we'll work out the bill later" written
    down as if it were a plan, which is the failure mode the whole
    declaration exists to prevent."""
    for pid, row in PURCHASES.items():
        assert row["prices_signals"] or row["unblocks_refusals"], pid


def test_a_row_priced_by_nothing_is_refused_by_the_builder():
    """...and the rule is enforced in the builder, not just asserted here:
    an unpriced row must red the tool that would publish it."""
    victim = copy.deepcopy(PURCHASES)
    victim["wishful"] = {
        "plan_ref": "nowhere", "title": "a bill to be worked out later",
        "prices_signals": [], "bill_class": "additive-reflect",
        "evidence": "grower", "grower_keys": [], "receipts": [],
        "unblocks_refusals": [], "notes": "no price on either axis",
    }
    import tools.purchase_frontier as pf
    saved = pf.PURCHASES
    try:
        pf.PURCHASES = victim
        with pytest.raises(ValueError, match="priced in nothing"):
            build_purchase_frontier(ROOT)
    finally:
        pf.PURCHASES = saved


def test_refusal_priced_rows_are_priced_by_live_groups_not_by_prose():
    """The refusal-priced block exists because §4's declaration stopped while
    the ledger kept measuring.  Each such row's numbers must come from the
    frontier's refused groups -- a row that names groups the frontier does
    not have is priced in recollection."""
    counts = _frontier_counts()
    refusal_priced = [pid for pid, row in PURCHASES.items()
                      if not row["prices_signals"]]
    assert refusal_priced, "the refusal-priced block vanished from the queue"
    by_id = {r["purchase_id"]: r for r in _committed()["purchases"]}
    for pid in refusal_priced:
        blocking = by_id[pid]["blocking_refusals"]
        assert blocking, pid
        for sig, n in blocking.items():
            assert n == counts.get(REFUSED_PREFIX + sig, 0), (pid, sig)


def test_blocking_refusals_invert_the_map_against_live_groups():
    counts = _frontier_counts()
    for r in _committed()["purchases"]:
        expect = {sig: counts.get("refused:" + sig, 0)
                  for sig in _unblocked_by(r["purchase_id"])}
        assert r["blocking_refusals"] == expect, r["purchase_id"]


def test_no_count_literals_in_the_declarations():
    """The declarations name signals; they never carry numbers.  (The
    frontier's own counts move every re-census -- pinning one here would red
    the gate one merge after landing, the PR #39 lesson.)"""
    for pid, row in PURCHASES.items():
        assert isinstance(row["prices_signals"], list), pid
        assert all(isinstance(s, str) for s in row["prices_signals"]), pid


# ------------------------------------------ vocabularies name their content
def test_bill_classes_all_described_and_all_used_classes_declared():
    for name, desc in BILL_CLASSES.items():
        assert isinstance(desc, str) and desc.strip(), name
        assert len(desc.split()) >= 8, f"{name}: a one-word gloss is not a "\
                                       f"description"
    for pid, row in PURCHASES.items():
        assert row["bill_class"] in BILL_CLASSES, pid


def test_signal_map_covers_the_whole_refusal_vocabulary_exactly():
    """Every measured-refusal signal is mapped -- no silent drops, no signals
    invented here that the ledger does not know."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import frontier_refusals as fr
    assert set(SIGNAL_UNBLOCKED_BY) == set(fr.SIGNALS)


def test_every_unmapped_signal_names_why_no_purchase_meets_it():
    """The vocabulary-names-its-lift tooth (the frontier_parks.REASONS
    pattern).  A signal filed under 'nothing' with no reason is a refusal
    quietly retired; a signal filed under a purchase must name a REAL row."""
    for sig, (key, reason) in SIGNAL_UNBLOCKED_BY.items():
        assert isinstance(reason, str) and reason.strip(), sig
        assert len(reason.split()) >= 8, f"{sig}: reason is not a reason"
        if key is not None:
            assert key in PURCHASES, f"{sig} names an unknown purchase {key!r}"


def test_row_unblocks_declaration_agrees_with_the_map():
    """One relation, two statements, one machine comparing them."""
    for pid, row in PURCHASES.items():
        assert sorted(row["unblocks_refusals"]) == _unblocked_by(pid), pid


def test_no_measured_refusal_is_unmapped_without_a_stated_reason():
    """THE DEAD-TERM CANARY, APPLIED TO DEMAND.

    The census canary reds when a declared term can never match anything;
    this is the same defect one axis over.  Every measured refusal signal
    must resolve in the SHIPPED ARTIFACT to one of exactly two readings: a
    purchase row that publishes it under ``blocking_refusals``, or an entry
    in ``no_purchase_meets`` carrying the reason none does.  A signal that
    resolves to neither has been quietly retired -- the queue tidying itself
    by forgetting demand, which is how "0 open" came to coexist with a full
    refusal ledger in the first place."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import frontier_refusals as fr
    doc = _committed()
    published = {sig for r in doc["purchases"]
                 for sig in r["blocking_refusals"]}
    unmet = {e["signal"]: e
             for e in doc["refill_projection"]["no_purchase_meets"]}
    for sig in fr.SIGNALS:
        assert (sig in published) ^ (sig in unmet), \
            f"{sig} resolves to neither a purchase nor a stated reason " \
            f"(or to both, which is two answers to one question)"
        if sig in unmet:
            reason = unmet[sig]["reason"]
            assert isinstance(reason, str) and len(reason.split()) >= 8, sig


def test_metatheoretic_subject_is_still_met_by_no_purchase():
    """The honesty this map must never lose.  tools/frontier_refusals.py
    documents the signal as naming a demand NO operator word and NO carrier
    can ever meet -- it asserts a property OF A DEFINITION rather than a
    proposition about carrier values -- and it was named apart from
    defined-predicate for exactly that reason.  Declaring new rows is how a
    queue restarts; filing this signal under one of them would be how it
    lies."""
    key, reason = SIGNAL_UNBLOCKED_BY["metatheoretic-subject"]
    assert key is None
    assert "NO PURCHASE MEETS THIS" in reason
    unmet = {e["signal"] for e
             in _committed()["refill_projection"]["no_purchase_meets"]}
    assert "metatheoretic-subject" in unmet


# ------------------------------------------------------- the refill reading
def test_refill_projection_schema():
    proj = _committed()["refill_projection"]
    assert set(proj) == {"ready_now", "refused_subjects",
                         "refused_group_memberships", "by_purchase",
                         "total_returns_to_ready",
                         "returns_if_every_open_row_lands",
                         "no_purchase_meets", "honesty"}
    for row in proj["by_purchase"]:
        assert set(row) == {"purchase_id", "status", "unblocks_refusals",
                            "refused_group_memberships", "returns_to_ready",
                            "held_by_a_signal_this_row_does_not_meet"}
        assert row["status"] in _STATUSES
    for entry in proj["no_purchase_meets"]:
        assert set(entry) == {"signal", "refused_nodes", "reason"}


def test_refill_projection_is_rederived_from_the_frontier():
    """Every number in the projection recomputed from the frontier's refused
    groups by an independent walk.  The counts that matter are per-SUBJECT
    (a subject returns only when its whole refusal set is met), so this is
    the tooth that would catch the tempting wrong answer: summing groups."""
    proj = _committed()["refill_projection"]
    per_node = _refused_by_node()
    counts = _frontier_counts()

    assert proj["ready_now"] == len(_frontier()["ready"])
    assert proj["refused_subjects"] == len(per_node)
    assert proj["refused_group_memberships"] == sum(
        n for sig, n in counts.items() if sig.startswith(REFUSED_PREFIX))

    by_id = {r["purchase_id"]: r for r in _committed()["purchases"]}
    for row in proj["by_purchase"]:
        pid = row["purchase_id"]
        assert row["unblocks_refusals"] == by_id[pid]["blocking_refusals"], pid
        assert row["status"] == by_id[pid]["status"], pid
        met = frozenset(row["unblocks_refusals"])
        assert row["refused_group_memberships"] == sum(
            counts.get(REFUSED_PREFIX + s, 0) for s in met), pid
        returns = [s for s in per_node.values() if s <= met]
        touched = [s for s in per_node.values() if s & met]
        assert row["returns_to_ready"] == len(returns), pid
        assert row["held_by_a_signal_this_row_does_not_meet"] == \
            len(touched) - len(returns), pid

    open_rows = [r for r in proj["by_purchase"] if r["status"] == "open"]
    assert proj["total_returns_to_ready"] == sum(
        r["returns_to_ready"] for r in open_rows)
    union = frozenset(s for r in open_rows for s in r["unblocks_refusals"])
    assert proj["returns_if_every_open_row_lands"] == len(
        [s for s in per_node.values() if s <= union])


def test_refill_projection_reconciles_to_the_refused_groups():
    """Signal-for-signal and node-for-node: every refused group is either
    named by a projected row or listed as met by nothing, exactly once, and
    the two partitions add back up to the frontier's own total.  A group that
    fell out of both would be demand the artifact stopped reporting."""
    proj = _committed()["refill_projection"]
    counts = _frontier_counts()
    live = {sig[len(REFUSED_PREFIX):]: n for sig, n in counts.items()
            if sig.startswith(REFUSED_PREFIX)}

    named = [s for r in proj["by_purchase"] for s in r["unblocks_refusals"]]
    unmet = [e["signal"] for e in proj["no_purchase_meets"]]
    assert len(named) == len(set(named)), "a group is claimed by two rows"
    assert set(named).isdisjoint(unmet)
    # every group with live nodes is accounted for on one side or the other
    assert set(live) <= set(named) | set(unmet), \
        f"unaccounted refused groups: {set(live) - set(named) - set(unmet)}"

    total = sum(r["refused_group_memberships"] for r in proj["by_purchase"])
    total += sum(e["refused_nodes"] for e in proj["no_purchase_meets"])
    assert total == proj["refused_group_memberships"] == sum(live.values())

    # and the subject-level readings stay inside the measured population
    assert proj["total_returns_to_ready"] <= \
        proj["returns_if_every_open_row_lands"] <= proj["refused_subjects"]


def test_when_ready_is_zero_the_artifact_says_what_would_refill_it():
    """THE READING WHOSE ABSENCE WAS THE BUG.

    "ready == 0" and "0 open" are each honest and together they are a stall,
    and for one whole era this artifact published the second while the
    frontier published the first and nothing joined them.  So: whenever the
    intake window is empty and open rows are declared, the artifact must say,
    in numbers, what landing them would return.  A stall may be true -- but
    it may never be SILENT."""
    doc = _committed()
    proj = doc["refill_projection"]
    opens = [r for r in doc["purchases"] if r["status"] == "open"]
    if proj["ready_now"] != 0 or not opens:
        pytest.skip("the window is not empty, or nothing is open: this tooth "
                    "is about the stall reading specifically")
    projected = {r["purchase_id"] for r in proj["by_purchase"]}
    for r in opens:
        if r["blocking_refusals"]:
            assert r["purchase_id"] in projected, r["purchase_id"]
    assert proj["by_purchase"], "empty window, open rows, and no projection"
    assert proj["total_returns_to_ready"] > 0, \
        "the artifact reports a stall and names nothing that would end it"


def test_refill_honesty_says_returning_is_selection_never_certification():
    """A returning subject passed SELECTION once; it has never been measured
    as certifiable, and the projection must not be readable as a forecast of
    green."""
    h = _committed()["refill_projection"]["honesty"]
    assert "SELECTION fact" in h
    assert "NEVER a promise it will certify" in h
    assert "only when ALL of them are met" in h


def test_honesty_string_says_signals_never_verdicts():
    doc = _committed()
    h = doc["honesty"]
    assert "never fidelity verdicts" in h
    assert "DECLARED intention" in h


# ---------------------------------------------- the status rule (synthetic)
def test_status_grower_evidence_synthetic():
    row = {"evidence": "grower", "grower_keys": ["a", "b"], "receipts": []}
    assert derive_status(row, {"a": {}, "b": {}}, ROOT) == "purchased"
    assert derive_status(row, {"a": {}}, ROOT) == "open"
    assert derive_status(row, {}, ROOT) == "open"


def test_status_empty_evidence_is_never_vacuously_purchased():
    """"No rows required" would make every unlanded purchase read as bought."""
    assert derive_status(
        {"evidence": "grower", "grower_keys": [], "receipts": []},
        {"a": {}}, ROOT) == "open"
    assert derive_status(
        {"evidence": "receipt", "grower_keys": [], "receipts": []},
        {}, ROOT) == "open"


def test_status_receipt_evidence_synthetic(tmp_path):
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "x_delta.md").write_text("a real receipt\n")
    row = {"evidence": "receipt", "grower_keys": [],
           "receipts": [["results/x_delta.md", "a real receipt"]]}
    assert derive_status(row, {}, str(tmp_path)) == "purchased"
    missing = {"evidence": "receipt", "grower_keys": [],
               "receipts": [["results/x_delta.md", "a real receipt"],
                            ["results/nope.md", "anything"]]}
    assert derive_status(missing, {}, str(tmp_path)) == "open"


def test_a_directory_or_an_empty_file_is_not_a_receipt(tmp_path):
    """The executed exploit against the bare ``os.path.exists`` reading:
    ``mkdir results/x_delta.md`` and ``touch results/x_delta.md`` BOTH
    computed ``purchased``.  Status is supposed to be a fact about the tree,
    and existence is the weakest possible reading of one."""
    row = {"evidence": "receipt", "grower_keys": [],
           "receipts": [["results/x_delta.md", "the needle"]]}

    d = tmp_path / "dir_case"
    (d / "results" / "x_delta.md").mkdir(parents=True)
    assert os.path.exists(str(d / "results" / "x_delta.md"))
    assert derive_status(row, {}, str(d)) == "open"

    e = tmp_path / "empty_case"
    (e / "results").mkdir(parents=True)
    (e / "results" / "x_delta.md").write_text("")
    assert derive_status(row, {}, str(e)) == "open"

    w = tmp_path / "whitespace_case"
    (w / "results").mkdir(parents=True)
    (w / "results" / "x_delta.md").write_text("   \n\n")
    assert derive_status(row, {}, str(w)) == "open"


def test_a_receipt_that_does_not_say_the_thing_is_not_evidence(tmp_path):
    """The needle is what makes ONE shared document answer TWO rows honestly.

    p3-split and p4-split cite the same ``results/p3_delta.md`` (one receipt,
    two instruments, deliberately not duplicated), so file existence could
    never distinguish them -- and historically, between a43619b and f3bc199,
    a receipt PREDATING its purchase satisfied the p4 row exactly as a real
    one would.  Each row now cites the sentence it is evidence FOR."""
    (tmp_path / "results").mkdir()
    doc = tmp_path / "results" / "shared_delta.md"
    doc.write_text("# a receipt about entropy-log and nothing else\n")
    p3 = {"evidence": "receipt", "grower_keys": [],
          "receipts": [["results/shared_delta.md", "entropy-log"]]}
    p4 = {"evidence": "receipt", "grower_keys": [],
          "receipts": [["results/shared_delta.md", "algebra-abstract"]]}
    assert derive_status(p3, {}, str(tmp_path)) == "purchased"
    assert derive_status(p4, {}, str(tmp_path)) == "open"
    doc.write_text("# now it addresses algebra-abstract and entropy-log\n")
    assert derive_status(p4, {}, str(tmp_path)) == "purchased"


def test_every_declared_receipt_actually_carries_its_needle():
    """The live half: each row's cited sentence is really in the document it
    cites.  A needle that drifts out of a receipt must red HERE, where it
    reads as evidence that moved, rather than silently flipping a status."""
    for pid, row in PURCHASES.items():
        for path, needle in row["receipts"]:
            assert _receipt_ok(ROOT, path, needle), \
                f"{pid}: {path} no longer contains {needle!r}"


def test_the_split_rows_share_one_document_under_distinct_needles():
    """The shape the needle exists for, asserted on the shipped queue rather
    than a fixture: two instrument rows, one receipt path, two sentences."""
    p3 = dict(PURCHASES["p3-split"]["receipts"])
    p4 = dict(PURCHASES["p4-split"]["receipts"])
    assert set(p3) == set(p4), "the split rows stopped sharing a receipt"
    assert set(p3.values()).isdisjoint(p4.values()), \
        "the split rows cite the same sentence; the needle distinguishes " \
        "nothing"


def test_status_is_read_off_the_tree_not_declared():
    """Build against an EMPTY registry: the grower-evidence rows must all
    read open.  If a status survived that, it was authored, not derived."""
    doc = build_purchase_frontier(ROOT, growers={})
    by_id = {r["purchase_id"]: r for r in doc["purchases"]}
    for pid, row in PURCHASES.items():
        if row.get("status_pin") is None and row["evidence"] == "grower":
            assert by_id[pid]["status"] == "open", pid


def test_landed_purchases_match_the_live_registry():
    """The committed statuses reconcile to the live growth registry and the
    live receipt files -- status is a fact about the tree."""
    from buildloop import growth_protocol as gp
    by_id = {r["purchase_id"]: r for r in _committed()["purchases"]}
    for pid, row in PURCHASES.items():
        if row.get("status_pin") is not None:
            continue
        if row["evidence"] == "grower":
            want = "purchased" if row["grower_keys"] and all(
                k in gp.GROWERS for k in row["grower_keys"]) else "open"
        else:
            want = "purchased" if row["receipts"] and all(
                _receipt_ok(ROOT, p, n) for p, n in row["receipts"]) else "open"
        assert by_id[pid]["status"] == want, pid


# ------------------------------------------ the rows that can never be bought
def test_p5_is_trust_root_and_a_planted_grower_cannot_buy_it():
    """The anti-list doctrine as control flow: the status pin is consulted
    BEFORE any evidence, so planting a registry row (or a receipt) named
    after the trust-root buys exactly nothing.  Trust roots never grow by
    purchase or economics, whatever the census prices them at."""
    row = copy.deepcopy(PURCHASES["p5"])
    assert row["status_pin"] == "trust-root"
    row["evidence"] = "grower"
    row["grower_keys"] = ["group-tactic-class"]
    row["receipts"] = ["results/p5_shadow.md"]
    assert derive_status(row, {"group-tactic-class": {}}, ROOT) == "trust-root"

    # and through the whole builder, with every declared key planted
    planted = {k: {} for row_ in PURCHASES.values()
               for k in row_["grower_keys"]}
    planted["group-tactic-class"] = {}
    doc = build_purchase_frontier(ROOT, growers=planted)
    by_id = {r["purchase_id"]: r for r in doc["purchases"]}
    assert by_id["p5"]["status"] == "trust-root"
    assert by_id["p5"]["bill_class"] == "trust-root-ceremony"


def test_p5_cites_a_live_anti_list_clause():
    """The row names the ANTI_LIST clause it is protected by, and the builder
    verifies the clause is still there -- deleting the doctrine reds this
    tool rather than quietly promoting the row."""
    from buildloop import growth_protocol as gp
    assert PURCHASES["p5"]["anti_list_ref"] in gp.ANTI_LIST


def test_p5_notes_cite_the_shadow_evidence_and_the_entrance_predicate():
    by_id = {r["purchase_id"]: r for r in _committed()["purchases"]}
    notes = by_id["p5"]["notes"]
    assert "results/p5_shadow.md" in notes
    assert "run/algebra_shadow.py" in notes
    assert "ENTRANCE PREDICATE" in notes
    assert os.path.exists(os.path.join(ROOT, "results", "p5_shadow.md"))
    assert os.path.exists(os.path.join(ROOT, "run", "algebra_shadow.py"))


def test_parked_rows_stay_parked_and_name_their_lift():
    """Parked items stay parked IN WRITING, and a park that names no way out
    is an indefinite hold, which house law forbids."""
    by_id = {r["purchase_id"]: r for r in _committed()["purchases"]}
    parked = [pid for pid, row in PURCHASES.items()
              if row.get("status_pin") == "parked"]
    assert parked, "the PARKED pair vanished from the queue"
    planted = {k: {} for row_ in PURCHASES.values()
               for k in row_["grower_keys"]}
    doc = build_purchase_frontier(ROOT, growers=planted)
    planted_by_id = {r["purchase_id"]: r for r in doc["purchases"]}
    for pid in parked:
        assert by_id[pid]["status"] == "parked"
        assert planted_by_id[pid]["status"] == "parked"
        assert "LIFTED BY:" in by_id[pid]["notes"], pid
        assert by_id[pid]["bill_class"] == "research-packet"


def test_anti_list_clause_removal_is_a_red_never_a_promotion(tmp_path):
    """Deleting the doctrine reds this tool rather than quietly promoting the
    row it protects.

    Exercised through a SECOND ROOT whose ``growth_protocol.py`` really has
    the clause removed, not by monkeypatching the imported module: the loader
    now reads the registry AT ``--root`` (see the tooth below), so a doctored
    file on disk is the only honest way to ask this question -- and it is a
    stronger one, because it is the registry the derivation actually reads."""
    with open(os.path.join(ROOT, REGISTRY)) as fh:
        doctored = fh.read().replace('"primitive ladder rungs",', "", 1)
    assert doctored != open(os.path.join(ROOT, REGISTRY)).read(), \
        "fixture did not apply"
    root = _scratch_root(tmp_path, registry_text=doctored)
    with pytest.raises(ValueError, match="ANTI_LIST"):
        build_purchase_frontier(root)


def test_the_registry_is_read_at_the_root_the_hashes_pin(tmp_path):
    """FIX for a pin over inputs the derivation never read.

    ``_load_registry`` used ``sys.path.insert`` + ``import_module``, which
    returns whatever ``sys.modules`` already holds under
    ``buildloop.growth_protocol`` -- in-process, THIS repo's module, no
    matter what ``--root`` said.  So a build against another root derived its
    statuses here and pinned the sha256 of the bytes over there: a
    reconciliation pin that reconciles nothing.  It also leaked its
    ``sys.path`` entry into every later import.

    The scratch root below carries a registry with EVERY grower row emptied
    out.  A loader that honours ``--root`` reports an empty registry; the old
    one reported this repo's."""
    with open(os.path.join(ROOT, REGISTRY)) as fh:
        real = fh.read()
    head, sep, tail = real.partition("GROWERS = {\n")
    assert sep, "GROWERS literal not found"
    emptied = head + "GROWERS = {}\nUNUSED_GROWERS = {\n" + tail
    root = _scratch_root(tmp_path, registry_text=emptied)

    saved_path = list(sys.path)
    growers, anti_list = _load_registry(root)
    assert growers == {}, \
        "the registry was read from this repo, not from --root"
    assert "primitive ladder rungs" in anti_list
    assert sys.path == saved_path, "_load_registry leaked a sys.path entry"

    # ...and the real root still reads the real registry, in the same process
    live_growers, _ = _load_registry(ROOT)
    assert live_growers, "the live registry came back empty"

    # end to end: every grower-evidence row reads open against that root
    doc = build_purchase_frontier(root)
    by_id = {r["purchase_id"]: r for r in doc["purchases"]}
    for pid, row in PURCHASES.items():
        if row.get("status_pin") is None and row["evidence"] == "grower":
            assert by_id[pid]["status"] == "open", pid

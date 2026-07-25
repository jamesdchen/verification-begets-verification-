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
  would be the thing this tool exists to abolish;
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
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common  # noqa: E402
from tools.purchase_frontier import (  # noqa: E402
    BILL_CLASSES,
    INPUTS,
    PURCHASES,
    SIGNAL_UNBLOCKED_BY,
    _STATUSES,
    _unblocked_by,
    _write,
    build_purchase_frontier,
    derive_status,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
ARTIFACT = os.path.join(RESULTS, "purchase_frontier.json")

_ROW_FIELDS = {"purchase_id", "plan_ref", "title", "bill_class", "status",
               "prices_signals", "blocking_refusals", "receipts", "notes"}


def _committed():
    with open(ARTIFACT) as fh:
        return json.load(fh)


def _frontier_counts():
    with open(os.path.join(RESULTS, "frontier.json")) as fh:
        f = json.load(fh)
    return {g["signal"]: g["node_count"] for g in f["blocked"]}


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
    growth-registry SOURCE TEXT, because status is read off it.  A mismatch
    is recorded STALENESS demand (regenerate), reported distinctly from a
    wrong derivation (the byte-compare tooth above)."""
    doc = _committed()
    assert set(doc["derived_from"]) == set(INPUTS)
    stale = []
    for rel in INPUTS:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            live = common.sha256_bytes(fh.read())
        if doc["derived_from"][rel] != live:
            stale.append(rel)
    assert not stale, f"input moved (staleness demand): {stale}"


# -------------------------------------------------------------------- schema
def test_top_level_schema():
    doc = _committed()
    assert set(doc) == {"derived_from", "purchases", "honesty"}
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
        assert isinstance(r["prices_signals"], dict) and r["prices_signals"]
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
        assert row["prices_signals"], pid
        for sig in row["prices_signals"]:
            assert sig in vocab, (pid, sig)


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
    (tmp_path / "results" / "x_delta.md").write_text("receipt\n")
    row = {"evidence": "receipt", "grower_keys": [],
           "receipts": ["results/x_delta.md"]}
    assert derive_status(row, {}, str(tmp_path)) == "purchased"
    missing = {"evidence": "receipt", "grower_keys": [],
               "receipts": ["results/x_delta.md", "results/nope.md"]}
    assert derive_status(missing, {}, str(tmp_path)) == "open"


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
                os.path.exists(os.path.join(ROOT, p))
                for p in row["receipts"]) else "open"
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


def test_anti_list_clause_removal_is_a_red_never_a_promotion(monkeypatch):
    from buildloop import growth_protocol as gp
    monkeypatch.setattr(gp, "ANTI_LIST", ("contract types",))
    try:
        build_purchase_frontier(ROOT)
    except ValueError as exc:
        assert "ANTI_LIST" in str(exc)
        return
    raise AssertionError("a missing anti-list clause must red the build")

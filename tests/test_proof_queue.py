"""Teeth for tools/proof_queue.py -- the committed, subject-hash-keyed proof
worklist reconciled from the anchor lattice, the import round-trip differential,
and the dual-arm formalization bench.

LLM-free, Lean-free, network-free.  These teeth pin, against the COMMITTED tree
(results/proof_queue.json + its three input artifacts):

- seed-drift byte identity: re-deriving the queue reproduces the committed bytes
  exactly (the tests/test_frontier.py precedent);
- reconciliation via the PINNED input sha256s: derived_from pins the current
  input files, so "an input moved" reads as recorded STALENESS demand (this
  tooth), distinct from "the derivation is wrong" (the byte-compare tooth);
- exact schema fields on every goal;
- dedupe correctness: 41/42/44 appear once each, provenance merged, and no
  subject sha256 is shared across two goals;
- status taxonomy counts (3 queued-exists + 63 bench queued + 1 excluded + 4
  infra-refused, i.e. 66 anchor+bench minus 3 dedupe + 4 rt);
- family taxonomy within the fixed enum;
- honesty: bench rows carry the fidelity string, never "TRUE"; refused rows are
  infra-refused only; no statement prose is written into results/;
- determinism.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.proof_queue import (
    INPUTS,
    build_proof_queue,
    classify_family,
    _write,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
QUEUE_PATH = os.path.join(RESULTS, "proof_queue.json")

_FAMILIES = {"linear", "dvd", "parity", "exists", "gcd", "other"}
_STATUSES = {"queued", "infra-refused", "shadow-refuted-excluded"}
_SOURCES = {"anchor-exists", "rt-failed", "bench-certified"}
_BENCH_LABEL = ("dual-arm bench-certified (Lean-free fidelity evidence; "
                "kernel statement-cert deferred)")


def _committed():
    with open(QUEUE_PATH) as fh:
        return json.load(fh)


# --------------------------------------------------------------- seed drift
def test_regenerate_byte_identical(tmp_path):
    """Re-derive from the committed inputs and byte-compare against the
    committed artifact -- the seed-drift tooth (test_frontier precedent)."""
    fresh = build_proof_queue(RESULTS)
    out = tmp_path / "proof_queue.json"
    _write(fresh, str(out))
    with open(out, "rb") as fh:
        regenerated = fh.read()
    with open(QUEUE_PATH, "rb") as fh:
        committed = fh.read()
    assert regenerated == committed, "proof_queue.json drifted from its source"


def test_determinism():
    """Two independent builds are identical (no wall-clock, no set-order leak)."""
    import common
    a = common.canonical_json(build_proof_queue(RESULTS))
    b = common.canonical_json(build_proof_queue(RESULTS))
    assert a == b


# --------------------------------------------------- reconciliation via pins
def test_derived_from_pins_current_inputs():
    """derived_from pins the sha256 of EVERY input file, matching the live
    tree.  A mismatch here is recorded STALENESS demand (regenerate the queue),
    reported distinctly from a wrong derivation (the byte-compare tooth)."""
    q = _committed()
    assert set(q["derived_from"]) == set(INPUTS)
    stale = []
    for path in INPUTS:
        with open(os.path.join(ROOT, path), "rb") as fh:
            live = hashlib.sha256(fh.read()).hexdigest()
        if q["derived_from"][path] != live:
            stale.append(path)
    assert not stale, f"input moved (staleness demand): {stale}"


# ----------------------------------------------------------------- schema
def test_top_level_schema():
    q = _committed()
    assert set(q) == {"derived_from", "goals", "honesty"}
    assert isinstance(q["honesty"], str) and q["honesty"]


def test_goal_schema_exact():
    q = _committed()
    for g in q["goals"]:
        assert set(g) == {"goal_id", "source", "subject", "status", "family",
                          "rung_hint", "provenance"}, g["goal_id"]
        assert set(g["subject"]) == {"ref", "sha256"}
        assert g["source"] in _SOURCES
        assert g["status"] in _STATUSES
        assert g["family"] in _FAMILIES
        assert isinstance(g["rung_hint"], str) and g["rung_hint"]
        assert isinstance(g["provenance"], dict)
        assert "sources" in g["provenance"]
        assert isinstance(g["provenance"]["label"], str)


def test_goals_sorted_by_id():
    q = _committed()
    ids = [g["goal_id"] for g in q["goals"]]
    assert ids == sorted(ids)


# ------------------------------------------------------------------ dedupe
def test_subject_sha_unique():
    """Dedupe key is subject sha256 -- no two goals share one."""
    q = _committed()
    shas = [g["subject"]["sha256"] for g in q["goals"]]
    assert len(shas) == len(set(shas)), "duplicate subject sha256 (dedupe leak)"


def test_dedupe_merges_41_42_44():
    """Sources 41/42/44 are in BOTH the anchor report and the bench state; each
    is ONE row, source anchor-exists, provenance carrying both arms."""
    q = _committed()
    by_id = {g["goal_id"]: g for g in q["goals"]}
    for sid in ("41_division_algorithm", "42_bezout_identity",
                "44_divides_witness"):
        g = by_id[sid]
        assert g["source"] == "anchor-exists"
        assert g["status"] == "queued"
        assert g["provenance"]["sources"] == ["anchor-exists", "bench-certified"]
        assert "anchor" in g["provenance"] and "bench" in g["provenance"]
        assert g["provenance"]["label"] == _BENCH_LABEL


# -------------------------------------------------------- status taxonomy
def test_status_taxonomy_counts():
    """Counts DERIVE from the input artifacts (self-reconciling: corpus
    growth moves the bench denominator every cycle -- hardcoded pins here
    redded the gate one merge after landing, the PR #39 lesson)."""
    import json as _json
    q = _committed()
    root = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(root, "results", "anchor_report.json")) as fh:
        anchor = _json.load(fh)
    n_anchor = len(anchor["readings"])
    n_anchor_refuted = sum(1 for r in anchor["readings"]
                           if r["shadow"]["verdict"] != "pass")
    with open(os.path.join(root, "results", "import_rt_report.json")) as fh:
        rt = _json.load(fh)
    n_rt_failed = rt["summary"]["by_verdict"]["failed"]
    bench_ids = set()
    with open(os.path.join(root, "results",
                           "formalize_bench_state.jsonl")) as fh:
        for line in fh:
            row = _json.loads(line)
            if row.get("arm") == "governed" and row.get("certified"):
                bench_ids.add(row["source_id"])
    n_anchor_queued = n_anchor - n_anchor_refuted   # merged into anchor rows

    by_status = {}
    by_source = {}
    for g in q["goals"]:
        by_status[g["status"]] = by_status.get(g["status"], 0) + 1
        by_source[g["source"]] = by_source.get(g["source"], 0) + 1

    assert by_source["anchor-exists"] == n_anchor
    assert by_source["rt-failed"] == n_rt_failed
    # bench-only rows = certified bench sources minus those deduped into
    # anchor rows (the queued anchor rows are exactly the overlap set)
    assert by_source["bench-certified"] == len(bench_ids) - n_anchor_queued
    assert by_status["infra-refused"] == n_rt_failed
    assert by_status["shadow-refuted-excluded"] == n_anchor_refuted
    assert by_status["queued"] == \
        len(q["goals"]) - n_rt_failed - n_anchor_refuted
    assert len(q["goals"]) == n_anchor + \
        (len(bench_ids) - n_anchor_queued) + n_rt_failed


def test_anchor_excluded_row_is_43_only():
    """The shadow-edge-refused row (43) is the ONLY excluded row and is NEVER
    queued as provable."""
    q = _committed()
    excluded = [g for g in q["goals"]
                if g["status"] == "shadow-refuted-excluded"]
    assert [g["goal_id"] for g in excluded] == ["43_larger_integer_exists"]
    assert excluded[0]["source"] == "anchor-exists"


def test_rt_rows_are_infra_refused_only():
    """Every rt-failed row is infra-refused -- gate/rendering demand, never
    proof demand, never queued."""
    q = _committed()
    rt = [g for g in q["goals"] if g["source"] == "rt-failed"]
    assert len(rt) == 4
    for g in rt:
        assert g["status"] == "infra-refused"
        assert g["provenance"]["rt"]["verdict"] == "failed"


# ---------------------------------------------------------------- family
def test_family_within_enum_and_precedence():
    q = _committed()
    for g in q["goals"]:
        assert g["family"] in _FAMILIES
    # precedence spot-checks: gcd beats the dvd sub-term (42_bezout), and an
    # ∃-shaped goal with no arithmetic-family trigger is exists (43).
    by_id = {g["goal_id"]: g for g in q["goals"]}
    assert by_id["42_bezout_identity"]["family"] == "gcd"
    assert by_id["43_larger_integer_exists"]["family"] == "exists"
    assert by_id["44_divides_witness"]["family"] == "dvd"


def test_classify_family_precedence_unit():
    assert classify_family({"gcd", "dvd"}) == "gcd"
    assert classify_family({"even", "dvd"}) == "parity"
    assert classify_family({"dvd", "exists"}) == "dvd"
    assert classify_family({"exists", "+"}) == "exists"
    assert classify_family({"+", "="}) == "linear"
    assert classify_family(set()) == "other"


# --------------------------------------------------------------- honesty
def test_bench_rows_carry_fidelity_string_never_true():
    q = _committed()
    blob = json.dumps(q)
    assert "certified TRUE" not in blob
    assert "TRUE" not in blob
    bench = [g for g in q["goals"]
             if "bench-certified" in g["provenance"]["sources"]]
    assert bench
    for g in bench:
        assert g["provenance"]["label"] == _BENCH_LABEL


def test_no_prose_leaked():
    """Only refs and hashes -- subject.sha256 is 64 hex chars, subject.ref is a
    source id / decl name, and no goal carries statement prose."""
    q = _committed()
    for g in q["goals"]:
        sha = g["subject"]["sha256"]
        assert len(sha) == 64
        int(sha, 16)
        # subject ref is a short id, never a sentence
        assert "\n" not in g["subject"]["ref"]

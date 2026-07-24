"""Teeth for tools/frontier.py -- the committed intake-frontier artifact.

LLM-free, Lean-free, network-free.  These teeth pin, against the COMMITTED
tree (results/frontier.json + the census + the corpus nodes.jsonl):

- seed-drift byte identity: re-deriving the frontier reproduces the committed
  bytes exactly (the repo's byte-identity discipline for derived artifacts);
- ready ∩ intaken = ∅, asserted ON HASHES (the bench _corpus_sources()
  read convention -- never labels or numeric prefixes);
- blocked group sizes reconcile per corpus to the census miss_histogram (a
  multi-signal node counts once per signal, in both);
- every ready/blocked node's text_sha256 is the actual sha256 of the corpus
  node's stripped prose;
- exact schema fields.
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.frontier import build_frontier, _write, _sha256

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "specs", "mathsources")
RESULTS = os.path.join(ROOT, "results")
FRONTIER_PATH = os.path.join(RESULTS, "frontier.json")


def _committed():
    with open(FRONTIER_PATH) as fh:
        return json.load(fh)


def _committed_corpora():
    return sorted(
        name for name in os.listdir(SOURCES)
        if os.path.isfile(os.path.join(SOURCES, name, "nodes.jsonl")))


def _intaken_hashes():
    out = set()
    for name in sorted(os.listdir(SOURCES)):
        p = os.path.join(SOURCES, name)
        if name.endswith(".txt") and os.path.isfile(p):
            with open(p) as fh:
                out.add(_sha256(fh.read().strip()))
    return out


def _node_prose_hashes():
    """(corpus, node_id) -> sha256(prose.strip()) for every committed node.
    Node ids are not unique across corpora, so this is keyed by corpus."""
    out = {}
    for corpus in _committed_corpora():
        with open(os.path.join(SOURCES, corpus, "nodes.jsonl")) as fh:
            for line in fh:
                if not line.strip():
                    continue
                node = json.loads(line)
                key = (corpus, node.get("label", "?"))
                out[key] = _sha256((node.get("prose", "") or "").strip())
    return out


# --------------------------------------------------------------- seed drift
def test_regenerate_byte_identical(tmp_path):
    """Re-derive from the committed census + corpus and byte-compare against
    the committed artifact -- the seed-drift tooth."""
    fresh = build_frontier(SOURCES, RESULTS)
    out = tmp_path / "frontier.json"
    _write(fresh, str(out))
    with open(out, "rb") as fh:
        regenerated = fh.read()
    with open(FRONTIER_PATH, "rb") as fh:
        committed = fh.read()
    assert regenerated == committed, "frontier.json drifted from its source"


# ----------------------------------------------------------------- schema
def test_schema_fields_exact():
    f = _committed()
    assert set(f) == {"derived_from", "ready", "blocked", "honesty"}
    assert set(f["derived_from"]) == {"census_portfolio_sha256",
                                      "frontier_refusals_rows",
                                      "frontier_parks_rows"}
    assert isinstance(f["honesty"], str) and f["honesty"]
    for r in f["ready"]:
        assert set(r) == {"corpus", "node_id", "text_sha256",
                          "suggested_source_name"}
    for g in f["blocked"]:
        assert set(g) == {"signal", "node_count", "nodes"}
        assert g["node_count"] == len(g["nodes"])
        for n in g["nodes"]:
            assert set(n) == {"corpus", "node_id", "text_sha256"}


def test_derived_from_matches_committed_census():
    f = _committed()
    with open(os.path.join(RESULTS, "census_portfolio.json"), "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    assert f["derived_from"]["census_portfolio_sha256"] == sha


def test_sorted_collections():
    f = _committed()
    ready_keys = [(r["corpus"], r["node_id"]) for r in f["ready"]]
    assert ready_keys == sorted(ready_keys)
    signals = [g["signal"] for g in f["blocked"]]
    assert signals == sorted(signals)
    for g in f["blocked"]:
        keys = [(n["corpus"], n["node_id"]) for n in g["nodes"]]
        assert keys == sorted(keys), g["signal"]


# ------------------------------------------------- ready ∩ intaken = ∅ (hash)
def test_ready_excludes_intaken_by_hash():
    f = _committed()
    intaken = _intaken_hashes()
    offenders = [r for r in f["ready"] if r["text_sha256"] in intaken]
    assert offenders == [], f"ready node already intaken by hash: {offenders}"


# ---------------------------------- blocked reconciles to census miss_histogram
def test_blocked_reconciles_to_census_per_corpus():
    f = _committed()
    roll = json.load(
        open(os.path.join(RESULTS, "census_portfolio.json")))
    by_corpus_signal = defaultdict(lambda: defaultdict(int))
    for g in f["blocked"]:
        if g["signal"].startswith(("refused:", "parked:")):
            continue  # demotion groups reconcile to their LEDGER teeth
        for n in g["nodes"]:
            by_corpus_signal[n["corpus"]][g["signal"]] += 1
    for row in roll["corpora"]:
        corpus = row["corpus"]
        got = dict(by_corpus_signal[corpus])
        assert got == row["miss_histogram"], corpus


# ------------------------------------- text hashes match the corpus prose
def test_text_hashes_match_corpus_prose():
    f = _committed()
    hashes = _node_prose_hashes()
    for r in f["ready"]:
        key = (r["corpus"], r["node_id"])
        assert key in hashes, key
        assert r["text_sha256"] == hashes[key], key
    for g in f["blocked"]:
        for n in g["nodes"]:
            key = (n["corpus"], n["node_id"])
            assert key in hashes, key
            assert n["text_sha256"] == hashes[key], key


def test_no_prose_leaked_into_artifact():
    """Only hashes -- statement prose is never duplicated into results/.
    Every recorded hash is 64 hex chars; nothing else carries prose."""
    f = _committed()
    for r in f["ready"]:
        assert len(r["text_sha256"]) == 64
        int(r["text_sha256"], 16)
    for g in f["blocked"]:
        for n in g["nodes"]:
            assert len(n["text_sha256"]) == 64
            int(n["text_sha256"], 16)


# ------------------------- measured-refusal demotion (the cycle-05 wedge fix)

def _ledger_by_subject():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
    import frontier_refusals as fr
    return fr.refused_by_subject(
        os.path.join(RESULTS, "frontier_refusals.jsonl"))


def test_refused_subjects_never_in_ready():
    f = _committed()
    refused = _ledger_by_subject()
    ready_hashes = {e["text_sha256"] for e in f["ready"]}
    assert not (set(refused) & ready_hashes), "refused subject re-entered ready"


def test_refused_groups_reconcile_to_ledger():
    f = _committed()
    refused = _ledger_by_subject()
    per_signal = {}
    for sha, signals in refused.items():
        for sig in signals:
            per_signal.setdefault("refused:" + sig, set()).add(sha)
    got = {g["signal"]: {n["text_sha256"] for n in g["nodes"]}
           for g in f["blocked"] if g["signal"].startswith("refused:")}
    for sig, shas in got.items():
        assert shas <= per_signal.get(sig, set()), sig
    assert set(got) <= set(per_signal)


def test_refusal_ledger_rows_are_canonical_and_provenanced():
    path = os.path.join(RESULTS, "frontier_refusals.jsonl")
    with open(path) as fh:
        for line in fh:
            row = json.loads(line)
            assert set(row) == {"measured_by", "signal", "subject_sha256"}
            assert row["measured_by"], "provenance mandatory: rows are evidence"
            assert len(row["subject_sha256"]) == 64
            assert line == json.dumps(
                row, sort_keys=True, separators=(",", ":")) + "\n"


# --------------------------- governance-park demotion (the cycle-07 wedge fix)
#
# A park is the OTHER way a subject leaves the intake window: it CERTIFIES,
# but an explicit decision holds it.  These teeth pin the distinction that
# makes the mechanism honest -- a park claims nothing about fidelity, and it
# is reversible, which is exactly what a refusal is not.

def _parks_module():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
    import frontier_parks as fp
    return fp


def _park_ledger_by_subject():
    return _parks_module().parked_by_subject(
        os.path.join(RESULTS, "frontier_parks.jsonl"))


def test_parked_subjects_never_in_ready():
    f = _committed()
    parked = _park_ledger_by_subject()
    ready_hashes = {e["text_sha256"] for e in f["ready"]}
    assert not (set(parked) & ready_hashes), "parked subject re-entered ready"


def test_parked_groups_reconcile_to_ledger():
    f = _committed()
    parked = _park_ledger_by_subject()
    per_reason = {}
    for sha, reasons in parked.items():
        for reason in reasons:
            per_reason.setdefault("parked:" + reason, set()).add(sha)
    got = {g["signal"]: {n["text_sha256"] for n in g["nodes"]}
           for g in f["blocked"] if g["signal"].startswith("parked:")}
    for reason, shas in got.items():
        assert shas <= per_reason.get(reason, set()), reason
    assert set(got) <= set(per_reason)


def test_park_ledger_rows_are_canonical_and_provenanced():
    path = os.path.join(RESULTS, "frontier_parks.jsonl")
    with open(path) as fh:
        for line in fh:
            row = json.loads(line)
            assert set(row) == {"parked_by", "reason", "subject_sha256"}
            assert row["parked_by"], "provenance mandatory: rows are evidence"
            assert len(row["subject_sha256"]) == 64
            assert line == json.dumps(
                row, sort_keys=True, separators=(",", ":")) + "\n"


def test_park_reasons_are_in_vocabulary_and_name_their_lift():
    """Every reason is vocabulary, and every reason says what lifts it --
    the analogue of a refusal signal naming its unblocking purchase.  A park
    with no stated way out is an indefinite hold, which house law forbids."""
    fp = _parks_module()
    for sha, reasons in _park_ledger_by_subject().items():
        for reason in reasons:
            assert reason in fp.REASONS, f"{reason} not in the vocabulary"
            assert fp.REASONS[reason].strip(), reason


def test_parked_subjects_are_not_already_intaken():
    """Parking holds material OUT of the corpus; a park on an already-intaken
    subject is a contradiction (you cannot hold back what has shipped)."""
    parked = _park_ledger_by_subject()
    offenders = sorted(set(parked) & _intaken_hashes())
    assert offenders == [], f"park row on an intaken subject: {offenders}"


def test_a_park_is_not_a_refusal():
    """The two ledgers stay disjoint: a subject is either MEASURED refused or
    HELD parked, never recorded as both -- conflating them would let a
    governance hold masquerade as a fidelity verdict (or the reverse)."""
    both = sorted(set(_park_ledger_by_subject()) & set(_ledger_by_subject()))
    assert both == [], f"subject in both the refusal and park ledgers: {both}"


def test_park_is_reversible(tmp_path):
    """The reversibility tooth: lifting a park returns its subjects to ready
    in listed order.  This is the property that makes ledgering a park an
    honest recording of a hold rather than a silent exclusion -- when the
    decision lands, the material comes back."""
    fp = _parks_module()
    committed = _committed()
    parked = _park_ledger_by_subject()
    assert parked, "no park rows committed -- tooth would be vacuous"

    # a scratch results/ dir: the committed census + refusal ledger, but an
    # EMPTY park ledger (every park lifted).
    scratch = tmp_path / "results"
    scratch.mkdir()
    for name in ("census_portfolio.json", "frontier_refusals.jsonl"):
        with open(os.path.join(RESULTS, name), "rb") as src:
            (scratch / name).write_bytes(src.read())
    (scratch / "frontier_parks.jsonl").write_text("")

    lifted = build_frontier(SOURCES, str(scratch))
    lifted_hashes = {e["text_sha256"] for e in lifted["ready"]}
    assert set(parked) <= lifted_hashes, "lifting a park did not restore ready"
    assert not any(g["signal"].startswith("parked:")
                   for g in lifted["blocked"])
    # and the lift is exactly the parked subjects -- nothing else moved
    assert lifted_hashes - {e["text_sha256"] for e in committed["ready"]} \
        == set(parked)

"""Teeth for specs/mathsources/registration.json -- the corpus-era registration.

The registration exists to make corpus growth a ONE-file re-baseline instead
of a literal hunt across the test tree (the C2-cycle lesson).  These teeth
keep it honest: every number in it must agree with the primary artifact it
summarizes, so the registration can never drift into an assertion the repo
does not reproduce.  LLM-free, network-free; reads only committed files.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG_PATH = os.path.join(ROOT, "specs", "mathsources", "registration.json")


def _reg():
    return json.load(open(REG_PATH))


def test_source_count_matches_manifest():
    reg = _reg()
    manifest = json.load(open(os.path.join(
        ROOT, "specs", "mathsources", "manifest.json")))
    assert reg["n_top_level_sources"] == len(manifest["files"])


def test_lineage_ends_at_current_era():
    reg = _reg()
    assert reg["lineage"], "lineage must be non-empty"
    last = reg["lineage"][-1]
    assert last["n_top_level_sources"] == reg["n_top_level_sources"]
    assert last["governed_legacy_dl"] == \
        reg["counting"]["governed_corpus_dl"]
    # lineage is monotone in corpus size (append-only history)
    sizes = [e["n_top_level_sources"] for e in reg["lineage"]]
    assert sizes == sorted(sizes)


def test_waves_are_contiguous_and_match_committed_csv():
    reg = _reg()
    assert reg["waves"] == list(range(reg["final_wave"] + 1))
    rows = list(csv.DictReader(open(os.path.join(
        ROOT, "results", "formalize_governed.csv"))))
    for arm in ("governed", "ungoverned"):
        waves = sorted({int(r["wave"]) for r in rows if r["arm"] == arm})
        assert waves == reg["waves"], arm


def test_counting_dls_match_committed_csv_final_wave():
    reg = _reg()
    rows = list(csv.DictReader(open(os.path.join(
        ROOT, "results", "formalize_governed.csv"))))
    fw = str(reg["final_wave"])
    gov = [r for r in rows if r["arm"] == "governed" and r["wave"] == fw][0]
    ung = [r for r in rows if r["arm"] == "ungoverned" and r["wave"] == fw][0]
    assert float(gov["reported_exogenous_dl"]) == \
        reg["counting"]["governed_corpus_dl"]
    assert float(ung["reported_exogenous_dl"]) == \
        reg["counting"]["ungoverned_corpus_dl"]
    # and the registered gaps are exactly the final-wave differences
    gaps = reg["final_wave_gaps"]
    assert gaps["hindsight"] == float(gov["reported_exogenous_dl"]) - \
        float(ung["reported_exogenous_dl"])
    assert gaps["prequential"] == float(gov["prequential_counting_dl"]) - \
        float(ung["prequential_counting_dl"])


def test_certified_count_matches_checkpoint():
    # n_readings = AUTHORED governed readings (the stream the entropy/DL
    # references walk); the manifest's declared non-transcribables author
    # None honestly and are absent from the stream.  n_certified is the
    # miner's corpus.
    reg = _reg()
    recs = [json.loads(l) for l in open(os.path.join(
        ROOT, "results", "formalize_bench_state.jsonl")) if l.strip()]
    gov = [r for r in recs if r["arm"] == "governed"]
    authored = [r for r in gov if r.get("reading_json")]
    assert len(authored) == reg["governed_exogenous"]["n_readings"]
    assert sum(1 for r in gov if r["certified"]) == \
        reg["governed_exogenous"]["n_certified"]


def test_census_of_record_matches_tower_census():
    reg = _reg()
    tower = json.load(open(os.path.join(ROOT, "results", "tower_census.json")))
    for arm in ("governed", "ungoverned"):
        ft = tower["final_tables"][arm]
        assert ft["count"] == reg["census_of_record"][arm]["macro_count"], arm
        assert ft["corpus_dl"] == reg["census_of_record"][arm]["corpus_dl"], arm


def test_cluster_key_block_obeys_its_own_law():
    ck = _reg()["cluster_key_reregistration"]
    assert ck["baseline_governed_dl"] == \
        _reg()["counting"]["governed_corpus_dl"]
    assert ck["accept_max_dl"] == ck["baseline_governed_dl"] - 29
    assert ck["max_macros"] == \
        round(8 / 37 * _reg()["governed_exogenous"]["n_certified"])


def test_holdout_registration_is_immutable_shape():
    h = _reg()["holdout_transfer_registration"]
    # the pre-registered digest + slice; the slice must predate every later
    # lineage era (registration happened at the 51-source corpus).
    assert h["table_digest_sha256_16"] == "ce5cb03fe2c5bdad"
    assert h["registered_max_stem"] == 51
    assert h["registered_max_stem"] <= _reg()["n_top_level_sources"]

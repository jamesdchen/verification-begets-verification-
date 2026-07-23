"""Teeth for planner/replay.py -- every condition C1-C7 has a planted
violation that must refuse WITH ITS OWN NAME, plus the positive path: a
chain the real planner produces must replay green.  The checker imports the
planner's coverage rule; these tests plant against real plan_for_features
output so checker and producer can never silently diverge."""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planner import plan_for_features
from planner.replay import replay_chain

# A two-link world: abnf -> ksy -> python-codec, plus a direct ksy generator.
KSY_GEN = {"name": "ksy-direct", "spec_language": "ksy",
           "output_language": "python-codec",
           "spec_grammar": {"atoms": ["magic", "str-fixed", "u2-be"]},
           "tier": "universal"}
ABNF_GEN = {"name": "abnf-chain", "spec_language": "abnf",
            "output_language": "ksy",
            "spec_grammar": {"atoms": ["literal", "repetition"],
                             "output": {"language": "ksy",
                                        "atoms": ["magic", "str-fixed"]}},
            "tier": "emit-check"}
ENTRIES = [KSY_GEN, ABNF_GEN]


def _normed_world():
    """plan_for_features normalizes entries (hash, tier defaults); replay
    must see the SAME normalized snapshot the producer saw."""
    chain = plan_for_features(ENTRIES, "abnf", ["literal"], "python-codec")
    assert chain is not None and len(chain) == 2
    # rebuild the normalized registry exactly as plan_for_features did: the
    # chain's own links carry the canonical hashes.
    direct = plan_for_features(ENTRIES, "ksy", ["magic"], "python-codec")
    snapshot = {l["generator_hash"]: l for l in chain + direct}
    return chain, list(snapshot.values())


def test_planner_chain_replays_green():
    chain, entries = _normed_world()
    res = replay_chain(chain, entries, "abnf", ["literal"], "python-codec")
    assert res["ok"], res
    assert res["n_links"] == 2
    assert res["rank_key"]["length"] == 2
    assert "not-checked" in res["optimality"]


def test_c1_empty_and_too_long():
    chain, entries = _normed_world()
    assert replay_chain([], entries, "abnf", [], "python-codec")[
        "refusal"]["condition"] == "C1"
    long_chain = chain * 4
    assert replay_chain(long_chain, entries, "abnf", ["literal"],
                        "python-codec")["refusal"]["condition"] == "C1"


def test_c2_foreign_and_tampered_links():
    chain, entries = _normed_world()
    foreign = copy.deepcopy(chain)
    foreign[0]["generator_hash"] = "f" * 64
    assert replay_chain(foreign, entries, "abnf", ["literal"],
                        "python-codec")["refusal"]["condition"] == "C2"
    tampered = copy.deepcopy(chain)
    tampered[1]["spec_grammar"] = {"atoms": ["magic", "str-fixed", "u2-be",
                                             "u4-le"]}
    res = replay_chain(tampered, entries, "abnf", ["literal"], "python-codec")
    assert res["refusal"]["condition"] == "C2"
    assert "tampered" in res["refusal"]["reason"]


def test_c3_pass_kind_refused():
    chain, entries = _normed_world()
    passer = copy.deepcopy(chain)
    passer[0]["kind"] = "pass"
    snapshot = entries + [passer[0]]        # registered, but kind=='pass'
    res = replay_chain(passer, snapshot, "abnf", ["literal"], "python-codec")
    assert res["refusal"]["condition"] in ("C2", "C3")
    # registered byte-equal pass link must hit C3 exactly:
    res2 = replay_chain([passer[0]], [passer[0]], "abnf", ["literal"], "ksy")
    assert res2["refusal"]["condition"] == "C3"


def test_c4_repeated_link():
    chain, entries = _normed_world()
    doubled = [chain[0], chain[0]]
    res = replay_chain(doubled, entries, "abnf", ["literal"], "python-codec")
    assert res["refusal"]["condition"] in ("C3", "C4", "C6")
    # force the pure C4 shape: same link twice where coverage would pass.
    res2 = replay_chain([chain[1], chain[1]], entries, "ksy",
                        ["magic"], "python-codec")
    assert res2["refusal"]["condition"] == "C4"


def test_c5_c6_coverage_refusals():
    chain, entries = _normed_world()
    # head does not cover: wrong input language.
    res = replay_chain(chain, entries, "ksy", ["magic"], "python-codec")
    assert res["refusal"]["condition"] == "C5"
    # C6: swap the two links -- the ksy generator cannot head an abnf input,
    # so build the C6 shape directly: head ok, second link uncovered.
    abnf_link = chain[0]
    bad_second = copy.deepcopy(chain[1])
    bad_second["spec_grammar"] = {"atoms": ["magic"]}   # drops str-fixed
    snapshot = [abnf_link, bad_second]
    res2 = replay_chain([abnf_link, bad_second], snapshot, "abnf",
                        ["literal"], "python-codec")
    assert res2["refusal"]["condition"] == "C6"


def test_c7_wrong_terminal():
    chain, entries = _normed_world()
    res = replay_chain(chain[:1], entries, "abnf", ["literal"],
                       "python-codec")
    assert res["refusal"]["condition"] == "C7"

"""Teeth for tools/blueprint_census.py (the 'faithfully stated' MVP scaffold).

LLM-free, Lean-free, network-free.  The fixture nodes below are SYNTHETIC
(authored for this test, in blueprint-node shape) -- they are NOT quotes from
any real blueprint; the real-corpus run is a fetch + one command wherever
network egress allows.
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.blueprint_census import census, census_node, render_md

FIXTURE = [
    # in-fragment arithmetic: no miss signal, fragment vocabulary present.
    {"label": "fix:dvd-sum", "kind": "lemma",
     "prose": "If d divides a and d divides b then d divides a + b, for "
              "natural numbers a, b, d.",
     "lean_names": ["dvd_add"]},
    # entropy/probability: the PFR-shaped out-of-fragment class.  Names BOTH
    # split signals (entropy-log via "entropy"; probability-mass via "random
    # variables") -- the split narrows attribution without demoting the miss.
    {"label": "fix:ent-subadd", "kind": "lemma",
     "prose": "The entropy of a pair of random variables is at most the sum "
              "of their entropies.",
     "lean_names": ["entropy_pair_le"]},
    # rational-mass probability WITHOUT the log: the P3-un-blockable slice,
    # probability-mass ONLY (no entropy-log signal).
    {"label": "fix:fair-die", "kind": "lemma",
     "prose": "For two independent random variables the probability of the "
              "joint outcome is the product of the marginal probabilities.",
     "lean_names": []},
    # group theory: a second, distinct miss category.
    {"label": "fix:torsion", "kind": "definition",
     "prose": "An elementary abelian group of exponent two is a vector space "
              "over the field with two elements.",
     "lean_names": []},
    # prose the census recognizes in neither direction.
    {"label": "fix:opaque", "kind": "remark",
     "prose": "This chapter fixes notation.", "lean_names": []},
]


def test_verdicts_and_histogram():
    rep = census(FIXTURE)
    by = {r["label"]: r for r in rep["rows"]}
    assert by["fix:dvd-sum"]["verdict"] == "attempt-candidate"
    assert by["fix:dvd-sum"]["miss_signals"] == {}
    assert by["fix:ent-subadd"]["verdict"] == "out-of-fragment"
    # the split: the PFR-shaped node names BOTH classes.
    assert "entropy-log" in by["fix:ent-subadd"]["miss_signals"]
    assert "probability-mass" in by["fix:ent-subadd"]["miss_signals"]
    # the log-free rational-mass node is probability-mass ONLY (the P3 slice).
    assert by["fix:fair-die"]["verdict"] == "out-of-fragment"
    assert "probability-mass" in by["fix:fair-die"]["miss_signals"]
    assert "entropy-log" not in by["fix:fair-die"]["miss_signals"]
    assert by["fix:torsion"]["verdict"] == "out-of-fragment"
    assert "algebra-structures" in by["fix:torsion"]["miss_signals"]
    assert by["fix:opaque"]["verdict"] == "no-signal"
    assert rep["miss_histogram"]["entropy-log"] >= 1
    assert rep["miss_histogram"]["probability-mass"] >= 1
    assert rep["verdicts"]["attempt-candidate"] == 1
    # honesty string rides every report.
    assert "never a fidelity verdict" in rep["honesty"]


def test_deterministic():
    a, b = census(FIXTURE), census(FIXTURE)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_cli_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "nodes.jsonl")
        with open(src, "w") as fh:
            for n in FIXTURE:
                fh.write(json.dumps(n) + "\n")
        out = os.path.join(d, "census")
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        r = subprocess.run(
            [sys.executable, os.path.join(root, "tools", "blueprint_census.py"),
             src, "--out", out],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        rep = json.load(open(out + ".json"))
        assert rep["n_nodes"] == len(FIXTURE)
        md = open(out + ".md").read()
        assert "Miss histogram" in md and "fix:dvd-sum" in md


def test_markdown_renders_every_row():
    rep = census(FIXTURE)
    md = render_md(rep)
    for n in FIXTURE:
        assert n["label"] in md

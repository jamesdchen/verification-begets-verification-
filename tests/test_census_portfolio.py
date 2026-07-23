"""Teeth for tools/census_portfolio.py + the C1 done-predicate.

LLM-free, Lean-free, network-free.  Two layers:

- synthetic-fixture checks of the rollup math (corpora in a tempdir; the
  fixture nodes are authored here, not quotes from any real blueprint);
- the PLAN_FRAGMENT §3 C1 done-predicate against the committed tree:
  >=5 corpora under specs/mathsources/ with committed census results, and
  the committed rollup in sync with the committed intake (re-running the
  census on nodes.jsonl reproduces the committed verdict counts).
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.blueprint_census import census
from tools.census_portfolio import portfolio, render_portfolio_md

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIXTURE_A = [
    {"label": "fix:a-dvd", "kind": "lemma",
     "prose": "If d divides a then d divides a + a, for natural numbers.",
     "lean_names": []},
    {"label": "fix:a-ent", "kind": "lemma",
     "prose": "The entropy of a random variable is nonnegative.",
     "lean_names": []},
]
FIXTURE_B = [
    {"label": "fix:b-opaque", "kind": "remark",
     "prose": "This chapter fixes notation.", "lean_names": []},
]


def _write_corpus(root, name, nodes):
    d = os.path.join(root, name)
    os.makedirs(d)
    with open(os.path.join(d, "nodes.jsonl"), "w") as fh:
        for n in nodes:
            fh.write(json.dumps(n) + "\n")


def test_rollup_math_and_mining_queue():
    with tempfile.TemporaryDirectory() as d:
        _write_corpus(d, "alpha", FIXTURE_A)
        _write_corpus(d, "beta", FIXTURE_B)
        result = portfolio(d)
        roll = result["portfolio"]
        assert roll["n_corpora"] == 2
        assert roll["n_nodes"] == 3
        assert roll["verdicts"] == {"attempt-candidate": 1,
                                    "out-of-fragment": 1, "no-signal": 1}
        rows = {r["corpus"]: r for r in roll["corpora"]}
        assert rows["alpha"]["attempt_candidates"] == ["fix:a-dvd"]
        assert rows["beta"]["attempt_candidates"] == []
        # per-corpus reports are the plain census, unchanged in shape.
        assert result["reports"]["alpha"]["n_nodes"] == 2
        assert "never a fidelity verdict" in roll["honesty"]


def test_rollup_deterministic():
    with tempfile.TemporaryDirectory() as d:
        _write_corpus(d, "alpha", FIXTURE_A)
        a = portfolio(d)["portfolio"]
        b = portfolio(d)["portfolio"]
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_markdown_renders_every_corpus():
    with tempfile.TemporaryDirectory() as d:
        _write_corpus(d, "alpha", FIXTURE_A)
        _write_corpus(d, "beta", FIXTURE_B)
        roll = portfolio(d)["portfolio"]
        md = render_portfolio_md(roll)
        assert "alpha" in md and "beta" in md
        assert "C2 mining queue" in md and "fix:a-dvd" in md


def test_cli_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "sources")
        out = os.path.join(d, "out")
        os.makedirs(out)
        os.makedirs(src)
        _write_corpus(src, "alpha", FIXTURE_A)
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "census_portfolio.py"),
             "--sources", src, "--out-dir", out],
            capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stderr
        roll = json.load(open(os.path.join(out, "census_portfolio.json")))
        assert roll["n_corpora"] == 1
        assert os.path.exists(
            os.path.join(out, "blueprint_census_alpha.json"))


# ---------------------------------------------------------------------------
# PLAN_FRAGMENT §3 C1 done-predicate, evaluated (not prose): >=5 corpora
# under specs/mathsources/ with committed census results in sync.
# ---------------------------------------------------------------------------

def _committed_corpora():
    root = os.path.join(ROOT, "specs", "mathsources")
    return sorted(
        name for name in os.listdir(root)
        if os.path.isfile(os.path.join(root, name, "nodes.jsonl")))


def test_c1_done_predicate_portfolio_size():
    assert len(_committed_corpora()) >= 5


def test_c1_intake_pairs_complete():
    root = os.path.join(ROOT, "specs", "mathsources")
    for name in _committed_corpora():
        meta_path = os.path.join(root, name, "fetch_meta.json")
        assert os.path.isfile(meta_path), f"{name}: fetch_meta.json missing"
        meta = json.load(open(meta_path))
        assert meta.get("source"), f"{name}: no source URL recorded"
        assert meta.get("pages_sha256"), f"{name}: no per-page SHA-256"
        n = sum(1 for line in open(os.path.join(root, name, "nodes.jsonl"))
                if line.strip())
        assert meta.get("n_nodes") == n, f"{name}: meta n_nodes != jsonl"


def test_c1_committed_census_in_sync():
    root = os.path.join(ROOT, "specs", "mathsources")
    committed_roll = json.load(
        open(os.path.join(ROOT, "results", "census_portfolio.json")))
    by_corpus = {r["corpus"]: r for r in committed_roll["corpora"]}
    for name in _committed_corpora():
        rep_path = os.path.join(
            ROOT, "results", f"blueprint_census_{name}.json")
        assert os.path.isfile(rep_path), f"{name}: census result not committed"
        committed = json.load(open(rep_path))
        nodes = []
        with open(os.path.join(root, name, "nodes.jsonl")) as fh:
            for line in fh:
                if line.strip():
                    nodes.append(json.loads(line))
        fresh = census(nodes)
        assert fresh["verdicts"] == committed["verdicts"], name
        assert fresh["miss_histogram"] == committed["miss_histogram"], name
        assert name in by_corpus, f"{name}: absent from committed rollup"
        assert by_corpus[name]["verdicts"] == committed["verdicts"], name

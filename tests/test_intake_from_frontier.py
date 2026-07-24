"""Teeth for tools/intake_from_frontier.py -- frontier-driven intake scaffolding.

Fully hermetic: every assertion runs against a SYNTHETIC tmp mirror (a tmp
corpus nodes.jsonl + a tmp frontier.json built to the WS-B contract + tmp
manifest / registration mirrors).  The real repo tree is never written to and
is asserted untouched.  LLM-free, network-free, deterministic.

Contract (latency-plan-v2 §FRONTIER.JSON SCHEMA CONTRACT):
  ready[]   = {corpus, node_id, text_sha256, suggested_source_name}
  blocked[] = {signal, node_count, nodes:[{corpus, node_id, text_sha256}]}
  text_sha256 = sha256 of node prose after .strip()
  "intaken"  = sha256(stripped) over specs/mathsources/*.txt (top level).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "intake_from_frontier.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("intake_from_frontier", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# synthetic fixture
# --------------------------------------------------------------------------- #

_NODES = [
    ("toy", "ch1#problem-001", "Let \\(a\\) be an integer with \\(a+1=3\\) . Show that \\(a=2\\) ."),
    ("toy", "ch1#problem-002", "Let \\(b\\) be an integer with \\(2b=6\\) . Show that \\(b=3\\) ."),
    ("toy", "ch1#problem-003", "Let \\(c\\) be an integer with \\(c-4=0\\) . Show that \\(c=4\\) ."),
    ("toy", "ch2#problem-010", "Let \\(n\\) be an integer with \\(n^2 \\le 0\\) . Show that \\(n=0\\) ."),
]


def _build_fixture(base) -> dict:
    """Write a tmp mirror; return handy paths.  base is a pathlib.Path."""
    ms = base / "specs" / "mathsources"
    corpus = ms / "toy"
    corpus.mkdir(parents=True)
    (base / "results").mkdir(parents=True)

    # committed corpus nodes.jsonl
    with open(corpus / "nodes.jsonl", "w", encoding="utf-8") as fh:
        for _c, label, prose in _NODES:
            fh.write(json.dumps(
                {"kind": "problem", "label": label,
                 "lean_names": [], "prose": prose}) + "\n")

    # two pre-existing top-level sources (prefixes 01, 02) -- unrelated bytes
    (ms / "01_alpha.txt").write_text("EXISTING ALPHA source prose .\n",
                                     encoding="utf-8")
    (ms / "02_beta.txt").write_text("EXISTING BETA source prose .\n",
                                    encoding="utf-8")

    manifest = {
        "flood_idiom": "divides-both",
        "files": [
            {"file": "01_alpha.txt", "axes": ["plain"], "expect_transcribes": True},
            {"file": "02_beta.txt", "axes": ["plain"], "expect_transcribes": True},
        ],
    }
    (ms / "manifest.json").write_text(json.dumps(manifest, indent=1),
                                      encoding="utf-8")
    # n_top_level_sources synced to the manifest (the live EXPECTED_TOTAL)
    (ms / "registration.json").write_text(
        json.dumps({"n_top_level_sources": 2, "lineage": []}, indent=1),
        encoding="utf-8")

    # frontier per contract: ready in (corpus, node_id) order
    ready = []
    for _c, label, prose in _NODES[:3]:
        ready.append({"corpus": "toy", "node_id": label,
                      "text_sha256": _sha(prose),
                      "suggested_source_name": "99_" + label.split("#")[1].replace("-", "_")})
    blocked = [{
        "signal": "real-analysis", "node_count": 1,
        "nodes": [{"corpus": "toy", "node_id": _NODES[3][1],
                   "text_sha256": _sha(_NODES[3][2])}],
    }]
    frontier = {
        "derived_from": {"census_portfolio_sha256": "abc123"},
        "ready": ready, "blocked": blocked,
        "honesty": "signals never verdicts",
    }
    fpath = base / "results" / "frontier.json"
    fpath.write_text(json.dumps(frontier, indent=1), encoding="utf-8")

    return {"base": str(base), "ms": str(ms), "frontier": str(fpath),
            "nodes_by_id": {label: prose for _c, label, prose in _NODES}}


def _run(fx, *args):
    cmd = [sys.executable, TOOL, "--root", fx["base"],
           "--frontier", fx["frontier"], *args]
    return subprocess.run(cmd, capture_output=True, text=True)


# --------------------------------------------------------------------------- #
# 1. dry-run determinism
# --------------------------------------------------------------------------- #

def test_dry_run_is_default_and_byte_identical(tmp_path):
    fx = _build_fixture(tmp_path)
    r1 = _run(fx, "--ready", "--take", "2")
    r2 = _run(fx, "--ready", "--take", "2")
    assert r1.returncode == 0 and r2.returncode == 0, (r1.stderr, r2.stderr)
    assert r1.stdout == r2.stdout, "two dry-runs must be byte-identical"
    # default is dry-run: nothing written
    assert not any(n.startswith(("03_", "04_"))
                   for n in os.listdir(fx["ms"]))
    assert "DRY-RUN" in r1.stdout
    # honesty banner present (signals never verdicts; refusals first-class)
    assert "NO certification claim" in r1.stdout
    assert "REFUSAL" in r1.stdout


# --------------------------------------------------------------------------- #
# 2. --apply writes exactly the planned files, verbatim (hash-match to nodes)
# --------------------------------------------------------------------------- #

def test_apply_writes_verbatim_planned_files(tmp_path):
    fx = _build_fixture(tmp_path)
    before = set(os.listdir(fx["ms"]))
    r = _run(fx, "--ready", "--take", "2", "--apply")
    assert r.returncode == 0, r.stderr
    after = set(os.listdir(fx["ms"]))
    new = sorted(after - before)
    # exactly two new .txt sources (prefixes fresh: 03, 04)
    assert new == ["03_problem_001.txt", "04_problem_002.txt"], new
    # verbatim: stored file stripped-hash == the corpus node hash
    id_by_prefix = {"03_problem_001.txt": "ch1#problem-001",
                    "04_problem_002.txt": "ch1#problem-002"}
    for fname, nid in id_by_prefix.items():
        content = (tmp_path / "specs" / "mathsources" / fname).read_text(encoding="utf-8")
        assert _sha(content) == _sha(fx["nodes_by_id"][nid]), fname
        assert content.strip() == fx["nodes_by_id"][nid].strip(), fname
    # readings-module skeleton written at root, index 2 (no prior wp_c*)
    rmod = tmp_path / "wp_c2_readings.py"
    assert rmod.is_file()
    src = rmod.read_text(encoding="utf-8")
    assert "PROVENANCE = {" in src
    assert "READINGS = {}" in src
    # the tool NEVER authors readings: no un-commented READINGS[...] assignment
    for line in src.splitlines():
        assert not line.lstrip().startswith('READINGS["'), \
            f"tool must not author a reading body: {line!r}"
    # provenance carries the corpus + node_id (verbatim provenance, not prose)
    assert "ch1#problem-001" in src and "ch1#problem-002" in src
    # the WROTE lines enumerate exactly the files created
    wrote = sorted(l.split(" ", 1)[1] for l in r.stdout.splitlines()
                   if l.startswith("WROTE "))
    assert wrote == sorted(
        [str(tmp_path / "specs" / "mathsources" / "03_problem_001.txt"),
         str(tmp_path / "specs" / "mathsources" / "04_problem_002.txt"),
         str(rmod)])


# --------------------------------------------------------------------------- #
# 3. prefix allocation never collides with existing files
# --------------------------------------------------------------------------- #

def test_prefix_allocation_above_existing_max(tmp_path):
    fx = _build_fixture(tmp_path)
    r = _run(fx, "--ready", "--take", "3", "--apply")
    assert r.returncode == 0, r.stderr
    new = sorted(n for n in os.listdir(fx["ms"])
                 if n not in ("01_alpha.txt", "02_beta.txt")
                 and n.endswith(".txt"))
    prefixes = [int(n.split("_")[0]) for n in new]
    assert prefixes == [3, 4, 5], prefixes  # strictly above existing max (2)
    assert 1 not in prefixes and 2 not in prefixes


def test_allocate_guard_refuses_existing_name():
    """Direct unit test of the never-overwrite guard in _allocate."""
    mod = _load_module()
    cands = [{"corpus": "toy", "node_id": "x", "text_sha256": "h", "slug": "foo"}]
    # allocation would pick prefix 3 -> "03_foo.txt"; pre-declare it existing
    try:
        mod._allocate(cands, existing_prefixes={1, 2},
                      existing_names={"03_foo.txt"})
    except SystemExit as e:
        assert "already exists" in str(e)
    else:
        raise AssertionError("expected SystemExit on filename collision")


# --------------------------------------------------------------------------- #
# 4. never overwrites an existing top-level source (idempotence + guards)
# --------------------------------------------------------------------------- #

def test_second_apply_is_idempotent_no_overwrite(tmp_path):
    fx = _build_fixture(tmp_path)
    # intake ALL three ready nodes ...
    r1 = _run(fx, "--ready", "--take", "3", "--apply")
    assert r1.returncode == 0, r1.stderr
    snap = {n: (tmp_path / "specs" / "mathsources" / n).read_text(encoding="utf-8")
            for n in os.listdir(fx["ms"]) if n.endswith(".txt")}
    # ... a second run finds every ready node already intaken -> filters all
    # out (first-class NOTE), selects nothing, and writes nothing.
    r2 = _run(fx, "--ready", "--take", "3", "--apply")
    assert r2.returncode == 0, r2.stderr
    assert "already-intaken" in r2.stdout
    assert "WROTE " not in r2.stdout, "nothing new must be written"
    after = {n: (tmp_path / "specs" / "mathsources" / n).read_text(encoding="utf-8")
             for n in os.listdir(fx["ms"]) if n.endswith(".txt")}
    assert after == snap, "second apply must not overwrite or add sources"


def test_apply_never_clobbers_existing_readings_module(tmp_path):
    """A pre-existing wp_cK module makes the tool ALLOCATE THE NEXT index,
    never overwrite the existing one."""
    fx = _build_fixture(tmp_path)
    (tmp_path / "wp_c2_readings.py").write_text("SENTINEL\n", encoding="utf-8")
    r = _run(fx, "--ready", "--take", "1", "--apply")
    assert r.returncode == 0, r.stderr
    # existing c2 preserved verbatim; new skeleton lands at c3
    assert (tmp_path / "wp_c2_readings.py").read_text(encoding="utf-8") == "SENTINEL\n"
    assert (tmp_path / "wp_c3_readings.py").is_file()
    assert "PROVENANCE = {" in (tmp_path / "wp_c3_readings.py").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# 5. unblocked mode + integrity guards + real-tree untouched
# --------------------------------------------------------------------------- #

def test_unblocked_selects_named_group(tmp_path):
    fx = _build_fixture(tmp_path)
    r = _run(fx, "--unblocked", "real-analysis", "--take", "1", "--apply")
    assert r.returncode == 0, r.stderr
    new = sorted(n for n in os.listdir(fx["ms"])
                 if n.endswith(".txt") and n not in ("01_alpha.txt", "02_beta.txt"))
    assert len(new) == 1 and new[0].startswith("03_")
    content = (tmp_path / "specs" / "mathsources" / new[0]).read_text(encoding="utf-8")
    assert _sha(content) == _sha(fx["nodes_by_id"]["ch2#problem-010"])


def test_unknown_signal_errors(tmp_path):
    fx = _build_fixture(tmp_path)
    r = _run(fx, "--unblocked", "no-such-signal", "--take", "1")
    assert r.returncode != 0
    assert "no blocked group" in (r.stderr + r.stdout)


def test_stale_frontier_hash_is_rejected(tmp_path):
    fx = _build_fixture(tmp_path)
    front = json.loads((tmp_path / "results" / "frontier.json").read_text())
    front["ready"][0]["text_sha256"] = "0" * 64  # corrupt the hash
    (tmp_path / "results" / "frontier.json").write_text(json.dumps(front))
    r = _run(fx, "--ready", "--take", "1", "--apply")
    assert r.returncode != 0
    assert "mismatch" in (r.stderr + r.stdout)


def test_expected_total_read_live_not_hardcoded(tmp_path):
    """The 'new source total' must track registration.n_top_level_sources."""
    fx = _build_fixture(tmp_path)
    r = _run(fx, "--ready", "--take", "1")
    assert "live source total   : 2" in r.stdout
    assert "new source total    : 3" in r.stdout
    # bump the live registration and re-run: the tool must follow it
    reg = json.loads((tmp_path / "specs" / "mathsources" / "registration.json").read_text())
    reg["n_top_level_sources"] = 5
    (tmp_path / "specs" / "mathsources" / "registration.json").write_text(json.dumps(reg))
    r2 = _run(fx, "--ready", "--take", "1")
    assert "live source total   : 5" in r2.stdout
    assert "new source total    : 6" in r2.stdout


def test_real_repo_tree_untouched(tmp_path):
    """Running the tool against a tmp root must not write into the real repo."""
    real_ms = os.path.join(ROOT, "specs", "mathsources")
    before = sorted(os.listdir(real_ms))
    before_hash = hashlib.sha256(
        "".join(before).encode()).hexdigest()
    # snapshot the real root's wp modules BEFORE (never assert on a specific
    # numbered name: cycles legitimately mint the next wp_c<K>_readings.py,
    # which is exactly how a hardcoded "wp_c5 must not exist" went stale)
    wp_before = sorted(f for f in os.listdir(ROOT)
                       if f.startswith("wp_c") and f.endswith("_readings.py"))
    fx = _build_fixture(tmp_path)
    _run(fx, "--ready", "--take", "3", "--apply")
    _run(fx, "--unblocked", "real-analysis", "--take", "1", "--apply")
    after = sorted(os.listdir(real_ms))
    assert hashlib.sha256("".join(after).encode()).hexdigest() == before_hash
    assert before == after
    # and the run minted no wp_c*_readings.py at the real repo root
    wp_after = sorted(f for f in os.listdir(ROOT)
                      if f.startswith("wp_c") and f.endswith("_readings.py"))
    assert wp_before == wp_after

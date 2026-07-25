"""Teeth for tools/census_delta.py (the derived re-census delta table).

The point of the tool is that a receipt STOPS re-keying census numbers, so
the point of these teeth is that the rendering is exact and reproducible: a
table pasted into a receipt must be re-derivable byte-for-byte from the same
two inputs, or the paste is worth no more than the retype it replaced.

Deterministic, LLM-free, Lean-free, network-free -- and git-free: the fixtures
below are SYNTHETIC census dicts, never a repository, because the diff and the
rendering are pure functions over dicts (the purchase_bill_manifest.py
convention) and only ``main`` may reach for git.
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import census_delta as cd

# A before/after pair shaped like the split the census actually performed: one
# coarse signal retires, two finer ones appear, one count moves, and the
# mining queue both gains and loses members.
BEFORE = {
    "tool": "census_portfolio",
    "n_corpora": 2,
    "n_nodes": 10,
    "miss_histogram": {"probability-entropy": 4, "primality": 2},
    "verdicts": {"attempt-candidate": 3, "out-of-fragment": 7},
    "corpora": [
        {"corpus": "alpha", "attempt_candidates": ["a1", "a2"]},
        {"corpus": "beta", "attempt_candidates": ["b1"]},
    ],
}

AFTER = {
    "tool": "census_portfolio",
    "n_corpora": 2,
    "n_nodes": 10,
    "miss_histogram": {"probability-mass": 4, "entropy-log": 1,
                       "primality": 3},
    "verdicts": {"attempt-candidate": 2, "out-of-fragment": 8},
    "corpora": [
        {"corpus": "alpha", "attempt_candidates": ["a2", "a3"]},
        {"corpus": "beta", "attempt_candidates": []},
    ],
}

EXPECTED = """\
# Census delta — `BASE` → `HEAD`

Derived by `tools/census_delta.py` from `results/census_portfolio.json` at \
both points. Lexical census numbers: deterministic, LLM-free, Lean-free. \
Signals only — a moved count is a reading, never a fidelity verdict.

## Portfolio totals

| quantity | base | head | delta |
|---|---:|---:|---:|
| `corpora` | 2 | 2 | +0 |
| `nodes` | 10 | 10 | +0 |

## Miss histogram (the vocabulary-growth price list)

| signal | base | head | delta |
|---|---:|---:|---:|
| `entropy-log` | — | 1 | — |
| `primality` | 2 | 3 | +1 |
| `probability-entropy` | 4 | — | — |
| `probability-mass` | — | 4 | — |

## Verdicts

| verdict | base | head | delta |
|---|---:|---:|---:|
| `attempt-candidate` | 3 | 2 | -1 |
| `out-of-fragment` | 7 | 8 | +1 |

## Attempt candidates (per corpus)

| corpus | base | head | delta |
|---|---:|---:|---:|
| `alpha` | 2 | 2 | +0 |
| `beta` | 1 | 0 | -1 |

## Queue membership changes

- `alpha`
  - entering: `a3`
  - leaving: `a1`
- `beta`
  - leaving: `b1`

**Measured delta above.** Every number is derived; none is re-keyed.
"""


def _render(base=BEFORE, head=AFTER):
    return cd.render_md(cd.census_delta(base, head), "BASE", "HEAD")


def test_exact_table():
    assert _render() == EXPECTED


def test_deterministic():
    assert _render() == _render()
    a = cd.census_delta(BEFORE, AFTER)
    b = cd.census_delta(BEFORE, AFTER)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_inputs_are_not_mutated():
    """A receipt helper that edited its inputs would corrupt whatever else
    the caller holds; the diff is a reading, so it takes nothing away."""
    snapshot = json.dumps([BEFORE, AFTER], sort_keys=True)
    _render()
    assert json.dumps([BEFORE, AFTER], sort_keys=True) == snapshot


def test_absent_is_not_zero():
    """A signal that did not exist on one side renders as a dash, never 0.

    The split shape depends on this: reading `probability-entropy: 4 -> 0`
    would claim the demand vanished, when in truth the signal was renamed and
    its nodes are counted under the two finer rows."""
    out = _render()
    assert "| `probability-entropy` | 4 | — | — |" in out
    assert "| `probability-entropy` | 4 | 0 |" not in out
    rows = {k: (b, h, d)
            for k, b, h, d in cd.census_delta(BEFORE, AFTER)["miss_histogram"]}
    assert rows["probability-entropy"] == (4, None, None)
    assert rows["entropy-log"] == (None, 1, None)


def test_no_delta_is_recorded_as_evidence():
    """CLAUDE.md: a no-delta purchase is recorded evidence, never silently
    retried or widened -- so the table has to be able to SAY zero."""
    out = _render(BEFORE, BEFORE)
    assert "**No measured delta.** Recorded as evidence, not retried." in out
    assert "_none: no node entered or left the mining queue._" in out
    assert "| `primality` | 2 | 2 | +0 |" in out


def test_a_pure_signal_split_is_a_measured_delta():
    """The defect this tooth exists for, executed.

    A pure split -- one coarse signal retires, two finer ones appear, every
    other number identical -- has a delta column that is `None` in every
    moved row, because a key present on one side only carries no delta.  The
    verdict line read `any(d for ...)` over that column and therefore printed
    "**No measured delta.** Recorded as evidence, not retried." directly
    underneath a table showing the split.  That sentence is house law about a
    purchase, and printing it over the tool's own reason to exist is a
    distorted reading forced to a green.

    Both directions are pinned: the split SAYS measured, and a genuinely
    identical pair still says no-delta (the phrase must stay available, or
    the fix would have bought a false positive instead)."""
    before = {"n_corpora": 1, "n_nodes": 9,
              "miss_histogram": {"probability-entropy": 4},
              "verdicts": {"out-of-fragment": 4},
              "corpora": [{"corpus": "a", "attempt_candidates": ["x"]}]}
    after = {"n_corpora": 1, "n_nodes": 9,
             "miss_histogram": {"probability-mass": 3, "entropy-log": 1},
             "verdicts": {"out-of-fragment": 4},
             "corpora": [{"corpus": "a", "attempt_candidates": ["x"]}]}
    out = _render(before, after)
    assert "| `probability-entropy` | 4 | — | — |" in out
    assert "| `probability-mass` | — | 3 | — |" in out
    assert "**Measured delta above.**" in out
    assert "**No measured delta.**" not in out
    # the phrase is not merely deleted: an identical pair still earns it
    assert "**No measured delta.**" in _render(before, before)


def test_a_verdict_key_appearing_alone_is_a_measured_delta():
    """The same asymmetry on the verdict axis, and on the totals axis: a
    census that grows an `n_corpora` field, or a verdict that first appears,
    has moved even though no delta cell can be computed for it."""
    before = {"miss_histogram": {"primality": 2}, "verdicts": {},
              "corpora": []}
    after = {"miss_histogram": {"primality": 2},
             "verdicts": {"no-signal": 1}, "corpora": []}
    assert "**Measured delta above.**" in _render(before, after)
    assert "**Measured delta above.**" in _render(
        {"miss_histogram": {}, "verdicts": {}, "corpora": []},
        {"n_nodes": 3, "miss_histogram": {}, "verdicts": {}, "corpora": []})


def test_a_corpus_appearing_with_the_same_count_is_a_measured_delta():
    """A corpus present on one side only carries `None` on the other; when
    its candidate labels happen to coincide there is no entering/leaving row
    either, so the corpus table's own asymmetry has to count."""
    before = {"miss_histogram": {}, "verdicts": {},
              "corpora": [{"corpus": "a", "attempt_candidates": ["x"]}]}
    after = {"miss_histogram": {}, "verdicts": {},
             "corpora": [{"corpus": "a", "attempt_candidates": ["x"]},
                         {"corpus": "b", "attempt_candidates": []}]}
    out = _render(before, after)
    assert "| `b` | — | 0 | — |" in out
    assert "**Measured delta above.**" in out


def test_corpus_appearing_and_disappearing():
    head = json.loads(json.dumps(AFTER))
    head["corpora"] = [{"corpus": "gamma", "attempt_candidates": ["g1"]}]
    out = _render(BEFORE, head)
    assert "| `gamma` | — | 1 | — |" in out
    assert "| `alpha` | 2 | — | — |" in out
    assert "  - entering: `g1`" in out
    assert "  - leaving: `a1`, `a2`" in out


def test_empty_reports_render_without_crashing():
    out = _render({}, {})
    assert "_no rows on either side._" in out
    assert "_no corpora on either side._" in out
    assert "**No measured delta.**" in out


def test_pure_functions_are_git_free_and_clock_free():
    """Determinism has two enemies here: a clock in the output and a git call
    in the pure path.  Neither may exist -- the plumbing lives in ``main``."""
    assert not hasattr(cd, "time") and not hasattr(cd, "datetime")
    src = open(cd.__file__).read()
    # everything from the first helper down to the git plumbing is the pure
    # region; no subprocess, no filesystem, no environment may appear in it.
    pure = src.split("def _counts(", 1)[1].split("def _git_show(", 1)[0]
    for banned in ("subprocess", "open(", "os.environ", "time.", "datetime"):
        assert banned not in pure, f"{banned!r} leaked into the pure region"
    for fn in ("census_delta", "render_md"):
        assert f"def {fn}(" in pure
    # the lane declaration rides the CLI (LLM-free by tripwire, not by habit).
    assert "lanes.token_free(\"census-delta\")" in src
    with tempfile.TemporaryDirectory() as d:
        cwd = os.getcwd()
        os.chdir(d)  # no repository here at all
        try:
            assert _render() == EXPECTED
        finally:
            os.chdir(cwd)


def test_cli_exits_2_on_unreadable_input():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tool = os.path.join(root, "tools", "census_delta.py")
    with tempfile.TemporaryDirectory() as d:
        missing = os.path.join(d, "absent.json")
        r = subprocess.run(
            [sys.executable, tool, "--base", "HEAD", "--head", "HEAD",
             "--path", missing],
            capture_output=True, text=True, cwd=root)
        assert r.returncode == 2, r.stdout + r.stderr
        assert "unreadable census" in r.stderr

        bad = os.path.join(d, "bad.json")
        open(bad, "w").write("{not json")
        r = subprocess.run([sys.executable, tool, "--path", bad],
                           capture_output=True, text=True, cwd=root)
        assert r.returncode == 2, r.stdout + r.stderr


def test_cli_renders_the_real_rollup_against_itself():
    """End to end on the committed artifact: HEAD against the working tree
    with no census change is the no-delta reading, and it must print it.

    Pure-function teeth above pin the judgment logic (the
    test_purchase_bill_manifest convention); this one exercises the git
    plumbing too, so it SKIPS by name where GIT ITSELF is refused (CI runs
    pytest in a container whose uid trips git's dubious-ownership guard) --
    never a silent pass, never a red for an environment fact.

    THE PROBE IS `git rev-parse HEAD`, NOT `git show HEAD:<artifact>`.  The
    old probe conflated two failures under one skip: "git refuses to talk to
    this checkout" (an environment fact) and "the artifact is not in HEAD at
    all" (a defect -- a deleted or renamed census rollup), so deleting the
    committed artifact would have turned this tooth green-by-skip.  Probing
    for the repository alone keeps the environment escape and lets the
    artifact's absence RED where it belongs, in the run below."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    probe = subprocess.run(["git", "rev-parse", "HEAD"],
                           capture_output=True, text=True, cwd=root)
    if probe.returncode != 0:
        pytest.skip("git unavailable in this environment "
                    "(dubious-ownership guard); plumbing exercised where "
                    "git works")
    tool = os.path.join(root, "tools", "census_delta.py")
    r = subprocess.run([sys.executable, tool, "--base", "HEAD",
                        "--head", "HEAD"],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("# Census delta — `HEAD` → `HEAD`")
    assert "**No measured delta.**" in r.stdout
    again = subprocess.run([sys.executable, tool, "--base", "HEAD",
                            "--head", "HEAD"],
                           capture_output=True, text=True, cwd=root)
    assert again.stdout == r.stdout

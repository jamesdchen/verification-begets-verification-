"""WP-C: the Lean-free fidelity-gate cache (F-INT-2, closes G3).

The stage-2 non-vacuity and stage-4 instance-replay gates are pure decidable
arithmetic over the F-G fragment; a loop that re-serves the same reading pays
for them on every run.  WP-C memoizes them in a small JSON side-store owned by
``run/formalize.py`` (``formalize_cache(key TEXT PRIMARY KEY, value TEXT)``),
keyed on the post-gate input doc's hash + bound + a version, with an in-process
dict fallback when ``CGB_DB`` is unset (the demo path).  ⚠FI-4: the registry's
``cache_put`` silently drops non-``Certificate`` values, so this deliberately
does NOT use the registry hooks; ``certify_statement``'s existing
``cache_get``/``cache_put`` params keep their kernel-cert meaning.

C3 teeth:
  (i)   a second certify over the same reading+bound performs ZERO solver calls;
  (ii)  a hit and a miss produce byte-identical ``FormalizeResult`` fields
        except the ``('cache','hit')`` honesty marker;
  (iii) a changed ``bound`` misses;
  (iv)  a version bump misses;
  (v)   a stage-2 refusal is NEVER cached and recomputes.

cvc5 note (honest): the cvc5 python binding flaps with this container's sandbox
state -- present in some runs, ``ModuleNotFoundError`` in others (the plan's
"cvc5 may be absent").  WP-C's ``run/formalize.py`` degrades the dual-solver
channel honestly to a solver ``error`` when the binding is absent, and these
teeth count Z3 calls only (z3 is always present), so they are robust to the
flap.  The single cvc5-dependent byte in the demo (Part A's non-vacuity channel
verdict: ``sat`` present / ``error`` absent) is normalized out of the byte pin.
"""
import dataclasses
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

import common
import run.formalize as F
from run.formalize import certify_statement
from kernel.backends import SmtBackend

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_GOLDEN = pathlib.Path(__file__).resolve().parent / "golden" / \
    "formalize_demo_stdout.txt"


# --------------------------------------------------------------------------
# Fixtures: a valid reading (all gates green -> cacheable) and a contradictory
# one (refused at nonvacuity -> never cached).
# --------------------------------------------------------------------------
def _mk(theorem, statements):
    return json.dumps({"theorem": theorem, "statements": statements})


_VALID_SRC = "for every positive n and every k, n divides the product n times k"
_VALID = [
    {"id": "amb", "force": "choice", "quote": "",
     "lf": {"kind": "ambient", "carrier": "Int"}},
    {"id": "on", "force": "demand", "quote": "every positive n",
     "lf": {"kind": "object", "name": "n", "type": "Int"}},
    {"id": "ok", "force": "demand", "quote": "every k",
     "lf": {"kind": "object", "name": "k", "type": "Int"}},
    {"id": "q", "force": "demand", "quote": "for every positive n and every k",
     "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n", "k"]}},
    {"id": "h", "force": "presupposition", "quote": "positive n",
     "lf": {"kind": "hypothesis",
            "pred": {"op": "<", "args": [{"lit": 0}, {"ref": "n"}]}}},
    {"id": "c", "force": "demand", "quote": "n divides the product n times k",
     "lf": {"kind": "conclusion", "pred": {"op": "dvd", "args": [
         {"ref": "n"}, {"op": "*", "args": [{"ref": "n"}, {"ref": "k"}]}]}}},
]
_VALID_JSON = _mk("valid_cache", _VALID)

# T2: contradictory hypotheses (5 < n and n < 3) -> refused at nonvacuity.
_CONTRA_SRC = "for every n greater than five and less than three, n is even"
_CONTRA_JSON = _mk("contra_cache", [
    {"id": "amb", "force": "choice", "quote": "",
     "lf": {"kind": "ambient", "carrier": "Int"}},
    {"id": "o", "force": "demand", "quote": "every n",
     "lf": {"kind": "object", "name": "n", "type": "Int"}},
    {"id": "q", "force": "demand", "quote": "for every n",
     "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
    {"id": "h1", "force": "presupposition", "quote": "greater than five",
     "lf": {"kind": "hypothesis",
            "pred": {"op": "<", "args": [{"lit": 5}, {"ref": "n"}]}}},
    {"id": "h2", "force": "presupposition", "quote": "less than three",
     "lf": {"kind": "hypothesis",
            "pred": {"op": "<", "args": [{"ref": "n"}, {"lit": 3}]}}},
    {"id": "c", "force": "demand", "quote": "n is even",
     "lf": {"kind": "conclusion",
            "pred": {"op": "even", "args": [{"ref": "n"}]}}},
])


@pytest.fixture(autouse=True)
def _isolate_cache(monkeypatch):
    """Each test starts cold on the in-process store, with CGB_DB unset so the
    default path is the dict fallback (tests that want the SQLite side-store set
    CGB_DB explicitly via monkeypatch)."""
    monkeypatch.delenv("CGB_DB", raising=False)
    F._formalize_cache_clear()
    yield
    F._formalize_cache_clear()


class _Z3Counter:
    """Wrap SmtBackend.run_z3 with a call counter; z3 is always present, so this
    is the cvc5-flap-robust witness of 'no solver work' (F-INT-2)."""

    def __init__(self, monkeypatch):
        self.n = 0
        real = SmtBackend.run_z3

        def _wrapped(inner_self, *a, **k):
            self.n += 1
            return real(inner_self, *a, **k)

        monkeypatch.setattr(SmtBackend, "run_z3", _wrapped)


# ============================================================ C3 (i)
def test_second_certify_over_same_reading_zero_solver_calls(monkeypatch):
    ctr = _Z3Counter(monkeypatch)
    r1 = certify_statement(_VALID_SRC, _VALID_JSON)
    assert r1.ok, r1.error
    cold = ctr.n
    assert cold >= 1, "the cold run must actually consult z3 (representable hyp)"
    r2 = certify_statement(_VALID_SRC, _VALID_JSON)
    assert r2.ok
    warm = ctr.n - cold
    assert warm == 0, f"second certify must be solver-free, saw {warm} z3 calls"


# ============================================================ C3 (ii)
def _strip_markers(layers):
    """Drop the ('cache','hit') honesty marker and normalize every channel pair
    to a tuple, so hit and miss layers compare structurally."""
    out = []
    for name, ok, detail in layers:
        detail = [tuple(c) for c in detail if tuple(c) != ("cache", "hit")]
        out.append((name, ok, detail))
    return out


def _has_hit_marker(layers, stage):
    detail = next(d for n, _o, d in layers if n == stage)
    return ("cache", "hit") in [tuple(c) for c in detail]


def test_hit_and_miss_byte_identical_except_marker():
    cold = certify_statement(_VALID_SRC, _VALID_JSON)   # miss
    warm = certify_statement(_VALID_SRC, _VALID_JSON)   # hit
    assert cold.ok and warm.ok

    # The marker is present on the warm run's cached gates, absent on the cold.
    assert _has_hit_marker(warm.layers, "nonvacuity")
    assert _has_hit_marker(warm.layers, "instances")
    assert not _has_hit_marker(cold.layers, "nonvacuity")
    assert not _has_hit_marker(cold.layers, "instances")

    # Every other field is byte-identical.
    assert _strip_markers(cold.layers) == _strip_markers(warm.layers)
    c, w = dataclasses.asdict(cold), dataclasses.asdict(warm)
    for field in ("ok", "stage", "error", "lean_text", "statement_hash",
                  "provenance", "boundary_behavior", "statement_cert",
                  "examiner"):
        assert c[field] == w[field], f"field {field!r} diverged hit vs miss"


# ============================================================ C3 (iii)
def test_changed_bound_misses(monkeypatch):
    certify_statement(_VALID_SRC, _VALID_JSON, bound=8)     # populate @ bound 8
    ctr = _Z3Counter(monkeypatch)
    certify_statement(_VALID_SRC, _VALID_JSON, bound=6)     # different key -> miss
    assert ctr.n >= 1, "a changed bound must miss and re-run the solver"
    # And the same bound now hits (no further solver work).
    before = ctr.n
    certify_statement(_VALID_SRC, _VALID_JSON, bound=6)
    assert ctr.n == before, "the second call at bound=6 should hit"


def test_bound_is_in_the_key():
    sha = common.sha256_json(json.loads(_VALID_JSON))
    assert F._nonvacuity_key(sha, 8) != F._nonvacuity_key(sha, 6)
    assert F._instances_key(sha, 8) != F._instances_key(sha, 6)


# ============================================================ C3 (iv)
def test_version_bump_misses(monkeypatch):
    certify_statement(_VALID_SRC, _VALID_JSON)              # populate @ v1
    monkeypatch.setattr(F, "FORMALIZE_CACHE_VERSION",
                        F.FORMALIZE_CACHE_VERSION + 1)
    ctr = _Z3Counter(monkeypatch)
    certify_statement(_VALID_SRC, _VALID_JSON)             # new version -> miss
    assert ctr.n >= 1, "a version bump must invalidate the cache and re-solve"


def test_version_is_in_the_key(monkeypatch):
    sha = common.sha256_json(json.loads(_VALID_JSON))
    k1 = F._nonvacuity_key(sha, 8)
    monkeypatch.setattr(F, "FORMALIZE_CACHE_VERSION",
                        F.FORMALIZE_CACHE_VERSION + 1)
    assert F._nonvacuity_key(sha, 8) != k1


# ============================================================ C3 (v)
def test_stage2_refusal_is_never_cached_and_recomputes(monkeypatch):
    ctr = _Z3Counter(monkeypatch)
    r1 = certify_statement(_CONTRA_SRC, _CONTRA_JSON)
    assert not r1.ok and r1.stage == "nonvacuity"
    first = ctr.n
    assert first >= 1
    r2 = certify_statement(_CONTRA_SRC, _CONTRA_JSON)
    assert not r2.ok and r2.stage == "nonvacuity"
    # Recompute: the refusal was NOT cached, so z3 runs again.
    assert ctr.n - first >= 1, "a refused reading must recompute, not be cached"
    # And nothing landed under its nonvacuity key.
    sha = common.sha256_json(json.loads(_CONTRA_JSON))
    assert F.formalize_cache_get(F._nonvacuity_key(sha, 8)) is None


def test_stage4_refusal_is_never_cached(monkeypatch):
    # T3: wrong operator binding -- refused at stage-4 instances.  The stage-2
    # gate IS cached (it passes); the stage-4 refusal is not.
    src = "for all a and b, if a divides b then a divides b"
    t3 = _mk("t3_cache", [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "demand", "quote": "all a",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "demand", "quote": "b",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "for all a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h", "force": "presupposition", "quote": "a divides b",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}},
        {"id": "c", "force": "demand", "quote": "a divides b",
         "lf": {"kind": "conclusion",
                "pred": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}},
    ])
    r = certify_statement(src, t3)
    assert not r.ok and r.stage == "instances"
    sha = common.sha256_json(json.loads(t3))
    assert F.formalize_cache_get(F._instances_key(sha, 8)) is None, \
        "a stage-4 refusal must not be cached"


# ============================================================ SQLite side-store
def test_sqlite_side_store_persists_and_hits(tmp_path, monkeypatch):
    """The real F-INT-2 substrate: a ``formalize_cache`` table in the CGB_DB
    SQLite file (not just the in-process dict)."""
    db = tmp_path / "reg.sqlite"
    monkeypatch.setenv("CGB_DB", str(db))
    F._formalize_cache_clear()                       # dict empty -> DB is source

    ctr = _Z3Counter(monkeypatch)
    r1 = certify_statement(_VALID_SRC, _VALID_JSON)
    assert r1.ok
    cold = ctr.n
    # Clear the in-process dict to PROVE the second hit comes from SQLite.
    F._formalize_cache_clear()
    r2 = certify_statement(_VALID_SRC, _VALID_JSON)
    assert r2.ok
    assert ctr.n == cold, "the warm run must be served from the SQLite store"
    assert _has_hit_marker(r2.layers, "nonvacuity")

    # The table exists and is populated.
    import sqlite3
    conn = sqlite3.connect(str(db))
    try:
        rows = conn.execute("SELECT key FROM formalize_cache").fetchall()
    finally:
        conn.close()
    assert len(rows) >= 2, "nonvacuity + instances entries expected"


def test_cache_get_put_roundtrip_in_memory():
    key = "unit-test-key"
    assert F.formalize_cache_get(key) is None
    F.formalize_cache_put(key, {"ok": True, "channels": [["z3", "sat"]]})
    got = F.formalize_cache_get(key)
    assert got == {"ok": True, "channels": [["z3", "sat"]]}


# ============================================================ demo byte pin
def _normalize_cvc5(text):
    """Mask the ONE environment-dependent token: cvc5's solver verdict in Part
    A's non-vacuity channel (``sat`` when the binding is present, ``error`` when
    absent).  Everything else in the demo is deterministic."""
    return re.sub(r"\['cvc5', '(?:sat|unsat|error|unknown)'\]",
                  "['cvc5', '<verdict>']", text)


def test_demo_stdout_matches_golden_pin():
    """Pin the flag-off demo stdout to the committed golden.

    HONESTY NOTE (documented deviation): the plan asks the golden be captured
    from the CURRENT unedited code before any edit.  In this container the
    frozen-base demo does NOT run to completion -- it crashes in the unowned
    ``kernel/backends.py`` (``import cvc5`` sits outside its try) whenever the
    cvc5 binding is absent -- so a literal pre-edit stdout is a one-line prefix
    plus a traceback, not a usable byte substrate.  Moreover ⚠FI-19 (channels
    normalized to lists) is a MANDATED WP-C change that itself alters the
    channel rendering (tuples -> lists), so no frozen-base golden could survive
    it.  The golden therefore captures WP-C's flag-off output; this pin proves
    (a) the ``--cache`` flag does not perturb the default output and (b) drift
    detection.  The non-vacuous "caching does not change results" claim is
    carried by ``test_hit_and_miss_byte_identical_except_marker``.
    """
    assert _GOLDEN.exists(), "golden fixture missing"
    out = subprocess.run(
        [sys.executable, "demo_formalize.py"], cwd=str(_ROOT),
        capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    live = _normalize_cvc5(out.stdout)
    golden = _normalize_cvc5(_GOLDEN.read_text())
    assert live == golden, (
        "flag-off demo drifted from the golden (cvc5 token masked)")


def test_demo_cache_flag_leaves_default_output_unchanged():
    """The --cache flag only APPENDS Part C; the default core is unchanged."""
    off = subprocess.run(
        [sys.executable, "demo_formalize.py"], cwd=str(_ROOT),
        capture_output=True, text=True, timeout=120)
    on = subprocess.run(
        [sys.executable, "demo_formalize.py", "--cache"], cwd=str(_ROOT),
        capture_output=True, text=True, timeout=120)
    assert off.returncode == 0 and on.returncode == 0
    # The flag-on output starts with the exact flag-off output, then Part C.
    assert _normalize_cvc5(on.stdout).startswith(_normalize_cvc5(off.stdout))
    assert "Part C: the Lean-free fidelity-gate cache" in on.stdout

"""WP-LI0 teeth (PLAN_LEAN_IMPORT.md §4/§6) -- Lean-FREE tests for the
fragment-fit census (buildloop/census.py) and the queue runner's Lean-free
surface (tools/enumerate_mathlib.py).

Covers: fixture-row classification (in-fragment / single-blocker /
multi-blocker / unclassifiable), census counts incl. the unlock_counts vs
blocked_by distinction, byte-identical regeneration (the P-LI0-CENSUS
tooth), frontier-order determinism + permutation-invariance (P-LI0-ORDER),
live derivation of the resident set from generators/math_reading.py +
admitted.json, and the runner's clean refusal with Lean absent.

Lean-needing smoke enumeration is marked with the repo's REQUIRES_LEAN
convention -- ``pytest.mark.skipif(not common.lean_available(), ...)``
(tests/test_lean_backend.py's skip-with-reason discipline; the demo-side
spelling of the same convention is run_regression's REQUIRES_LEAN flag).
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import random
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import common
from buildloop import census
from generators import math_reading

_REPO = pathlib.Path(__file__).resolve().parent.parent
_RUNNER = _REPO / "tools" / "enumerate_mathlib.py"


def _load_runner_module():
    spec = importlib.util.spec_from_file_location("enumerate_mathlib",
                                                  _RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ===========================================================================
# Fixture queue: 16 hand-written rows in the exact WP-LI0 queue schema.
# statement_pp strings mimic the pinned pretty-printer surface
# (pp.fullNames true, pp.notation true: ℕ/ℤ, ∣, full names).
# ===========================================================================
def _row(decl, module, pp, kind="theorem"):
    return {"decl_name": decl, "module": module, "kind": kind,
            "statement_pp": pp, "statement_hash": common.sha256_json(
                {"mathlib_commit": common.MATHLIB_COMMIT,
                 "statement_pp": pp}),
            "status": "pending"}


FIXTURE_ROWS = [
    # -- in-fragment (6) ----------------------------------------------------
    _row("Nat.dvd_refl", "Mathlib.Data.Nat.Defs",
         "∀ (n : ℕ), n ∣ n"),
    _row("Even.add", "Mathlib.Algebra.Group.Even",
         "∀ {a b : ℕ}, Even a → Even b → Even (a + b)"),
    _row("Nat.gcd_comm", "Mathlib.Data.Nat.GCD.Basic",
         "∀ (m n : ℕ), Nat.gcd m n = Nat.gcd n m"),
    _row("Int.emod_emod_of_dvd", "Mathlib.Data.Int.Defs",
         "∀ (a b c : ℤ), c ∣ b → a % b % c = a % c"),
    _row("Nat.coprime_one_left", "Mathlib.Data.Nat.GCD.Basic",
         "∀ (n : ℕ), Nat.Coprime 1 n"),
    _row("Nat.exists_dvd_of_le", "Mathlib.Data.Nat.Defs",
         "∀ (n : ℕ), 1 ≤ n → ∃ m, m ∣ n "
         "∧ m ≠ 0"),
    # -- single-blocker (6) -------------------------------------------------
    _row("Nat.Prime.two_le", "Mathlib.Data.Nat.Prime.Basic",
         "∀ {p : ℕ}, Nat.Prime p → 2 ≤ p"),
    _row("Real.sq_nonneg", "Mathlib.Analysis.SpecialFunctions.Pow.Real",
         "∀ (x : ℝ), 0 ≤ x ^ 2"),
    _row("Finset.card_nonneg", "Mathlib.Data.Finset.Card",
         "∀ (s : Finset ℕ), 0 ≤ Finset.card s"),
    _row("List.length_nonneg", "Mathlib.Data.List.Basic",
         "∀ (l : List ℕ), 0 ≤ List.length l"),
    _row("Polynomial.mul_zero", "Mathlib.Algebra.Polynomial.Basic",
         "∀ (p : Polynomial ℕ), p * 0 = 0"),
    _row("Nat.even_iff", "Mathlib.Data.Nat.Parity",
         "∀ (n : ℕ), Even n ↔ n % 2 = 0"),
    # -- multi-blocker (3) --------------------------------------------------
    _row("Nat.Prime.exists_real_sqrt", "Mathlib.Analysis.Mixed",
         "∀ (p : ℕ), Nat.Prime p → ∃ x : ℝ, "
         "x * x = p"),
    _row("Finset.exists_prime_dvd_card", "Mathlib.Data.Finset.Mixed",
         "∃ (s : Finset ℕ), ∀ p, Nat.Prime p → "
         "p ∣ Finset.card s"),
    _row("Group.mul_inv", "Mathlib.Algebra.Group.Basic",
         "∀ {G : Type u_1} [inst : Group G] (a : G), "
         "a * a⁻¹ = 1"),
    # -- unclassifiable (1) -------------------------------------------------
    _row("Xyzzy.frobnicate_id", "Mathlib.Order.Xyzzy",
         "∀ (w : Xyzzy), Xyzzy.frobnicate w = w"),
]

# decl_name -> (in_fragment, missing tuple, unclassified)
EXPECTED = {
    "Nat.dvd_refl": (True, (), False),
    "Even.add": (True, (), False),
    "Nat.gcd_comm": (True, (), False),
    "Int.emod_emod_of_dvd": (True, (), False),
    "Nat.coprime_one_left": (True, (), False),
    "Nat.exists_dvd_of_le": (True, (), False),
    "Nat.Prime.two_le": (False, ("Prime",), False),
    "Real.sq_nonneg": (False, ("Real",), False),
    "Finset.card_nonneg": (False, ("Finset",), False),
    "List.length_nonneg": (False, ("List",), False),
    "Polynomial.mul_zero": (False, ("Polynomial",), False),
    "Nat.even_iff": (False, ("Iff",), False),
    "Nat.Prime.exists_real_sqrt": (False, ("Prime", "Real"), False),
    "Finset.exists_prime_dvd_card": (False, ("Finset", "Prime"), False),
    "Group.mul_inv": (False, ("Group", "Inv", "Type"), False),
    "Xyzzy.frobnicate_id": (False, (), True),
}


@pytest.fixture(scope="module")
def resident():
    return census.derive_resident_set()


@pytest.fixture(scope="module")
def fixture_census():
    return census.build_census(FIXTURE_ROWS)


# ======================================================= classification ====
def test_fixture_classification(resident):
    for row in FIXTURE_ROWS:
        exp_in, exp_missing, exp_uncls = EXPECTED[row["decl_name"]]
        c = census.classify_row(row["statement_pp"], resident)
        assert c["in_fragment"] is exp_in, (row["decl_name"], c)
        assert tuple(c["missing"]) == exp_missing, (row["decl_name"], c)
        assert c["unclassified"] is exp_uncls, (row["decl_name"], c)


def test_single_blocker_flag(resident):
    for row in FIXTURE_ROWS:
        exp_in, exp_missing, _ = EXPECTED[row["decl_name"]]
        c = census.classify_row(row["statement_pp"], resident)
        if not exp_in and len(exp_missing) == 1 and not c["residue"]:
            assert c["single_blocker"] == exp_missing[0]
        else:
            assert c["single_blocker"] is None, (row["decl_name"], c)


def test_multi_blocker_with_residue_is_never_single(resident):
    # Group.mul_inv has blockers AND residue (the type variable G): it must
    # count in blocked_by (see census test) but never as single-blocker.
    c = census.classify_row(
        "∀ {G : Type u_1} [inst : Group G] (a : G), a * a⁻¹ "
        "= 1", resident)
    assert c["single_blocker"] is None
    assert "G" in c["residue"]
    assert c["unclassified"] is False


def test_empty_statement_is_unclassified(resident):
    for s in ("", "   ", None):
        c = census.classify_row(s, resident)
        assert c["unclassified"] is True
        assert c["in_fragment"] is False
        assert c["single_blocker"] is None


# =============================================================== census ====
def test_census_counts(fixture_census):
    c = fixture_census
    assert c["pin"] == common.MATHLIB_COMMIT
    assert c["total"] == 16
    assert c["in_fragment"] == 6
    assert c["single_blocker_rows"] == 6
    assert c["multi_blocker_rows"] == 3
    assert c["unclassified"] == 1
    # unlock_counts: SINGLE-blocker semantics -- a row counts toward c iff
    # c is its ONLY missing constant.
    assert c["unlock_counts"] == {"Finset": 1, "Iff": 1, "List": 1,
                                  "Polynomial": 1, "Prime": 1, "Real": 1}
    # blocked_by: TOTAL rows mentioning c.  Prime is blocked_by 3 (one
    # single-blocker row + two multi-blocker rows) while unlocking only 1 --
    # the distinction the plan prices kernel growth with.
    assert c["blocked_by"] == {"Finset": 2, "Group": 1, "Iff": 1, "Inv": 1,
                               "List": 1, "Polynomial": 1, "Prime": 3,
                               "Real": 2, "Type": 1}
    assert c["blocked_by"]["Prime"] > c["unlock_counts"]["Prime"]
    assert c["co_occurrence"] == [["Finset+Prime", 1], ["Group+Inv", 1],
                                  ["Group+Type", 1], ["Inv+Type", 1],
                                  ["Prime+Real", 1]]
    # every blocked constant carries its documented miss_kind
    assert c["miss_kinds"]["Prime"] == "operator:prime"
    assert c["miss_kinds"]["Real"] == "carrier:Real"
    assert c["miss_kinds"]["Type"] == "kind:universe-polymorphism"


def test_census_byte_identical_regeneration(tmp_path):
    """P-LI0-CENSUS: census regeneration at the same pin is byte-identical.
    Two fully independent builds (fresh resident-set derivation each time)
    must serialize to the same bytes."""
    b1 = census.render_census_bytes(census.build_census(FIXTURE_ROWS))
    b2 = census.render_census_bytes(
        census.build_census(list(FIXTURE_ROWS),
                            resident=census.derive_resident_set()))
    assert b1 == b2
    assert b1.endswith(b"\n") and b"\r" not in b1


def test_census_end_to_end_cli(tmp_path, capsys):
    """The census runs end-to-end on the fixture queue via its CLI, twice,
    byte-identically (the file-level P-LI0-CENSUS tooth)."""
    queue = tmp_path / "queue.jsonl"
    with open(queue, "w", encoding="utf-8", newline="\n") as fh:
        for r in FIXTURE_ROWS:
            fh.write(common.canonical_json(r) + "\n")
    out1, out2 = tmp_path / "census1.json", tmp_path / "census2.json"
    assert census.main(["--queue", str(queue), "--out", str(out1)]) == 0
    assert census.main(["--queue", str(queue), "--out", str(out2)]) == 0
    assert out1.read_bytes() == out2.read_bytes()
    loaded = json.loads(out1.read_text(encoding="utf-8"))
    assert loaded["total"] == 16 and loaded["pin"] == common.MATHLIB_COMMIT


def test_census_cli_refuses_on_missing_queue(tmp_path, capsys):
    rc = census.main(["--queue", str(tmp_path / "nope.jsonl"),
                      "--out", str(tmp_path / "census.json")])
    assert rc == 2
    assert "REFUSED" in capsys.readouterr().err


# ======================================================= frontier order ====
def test_frontier_order_sections(fixture_census):
    order = census.frontier_order(FIXTURE_ROWS, fixture_census)
    names = [r["decl_name"] for r in order]
    assert len(names) == 16 and len(set(names)) == 16
    # section 1: in-fragment rows by (module, decl_name)
    in_frag = sorted(
        ((r["module"], r["decl_name"]) for r in FIXTURE_ROWS
         if EXPECTED[r["decl_name"]][0]))
    assert names[:6] == [d for _m, d in in_frag]
    # section 2: single-blocker rows; all unlock counts tie at 1 here, so
    # groups fall back to blocker-name ascending
    assert names[6:12] == ["Finset.card_nonneg", "Nat.even_iff",
                           "List.length_nonneg", "Polynomial.mul_zero",
                           "Nat.Prime.two_le", "Real.sq_nonneg"]
    # section 3: the rest by (module, decl_name)
    rest = sorted((r["module"], r["decl_name"]) for r in FIXTURE_ROWS
                  if r["decl_name"] not in names[:12])
    assert names[12:] == [d for _m, d in rest]


def test_frontier_order_groups_by_descending_unlock_count():
    # A census claiming Real unlocks more than everything else must pull the
    # Real group ahead of the alphabetically-earlier blockers.
    fake = {"unlock_counts": {"Real": 10, "Prime": 5}}
    names = [r["decl_name"]
             for r in census.frontier_order(FIXTURE_ROWS, fake)]
    singles = names[6:12]
    assert singles[0] == "Real.sq_nonneg"
    assert singles[1] == "Nat.Prime.two_le"
    # remaining unlock-0 blockers alphabetical: Finset, Iff, List, Polynomial
    assert singles[2:] == ["Finset.card_nonneg", "Nat.even_iff",
                           "List.length_nonneg", "Polynomial.mul_zero"]


def test_frontier_order_deterministic_and_permutation_invariant(
        fixture_census):
    base = [r["decl_name"]
            for r in census.frontier_order(FIXTURE_ROWS, fixture_census)]
    perms = [list(reversed(FIXTURE_ROWS))]
    for seed in (0, 1, 7):
        p = list(FIXTURE_ROWS)
        random.Random(seed).shuffle(p)
        perms.append(p)
    for p in perms:
        got = [r["decl_name"] for r in census.frontier_order(p,
                                                             fixture_census)]
        assert got == base


# ================================================ resident-set derivation ==
def test_resident_set_derived_from_math_reading(resident):
    """The derivation actually reads math_reading.py's vocabulary: every
    carrier and every carrier-indexed Lean operator name must be resident,
    computed here FROM the imported module, not from a copied list."""
    for carrier in math_reading.CARRIERS:
        assert carrier in resident.identifiers
    for word, info in math_reading.MATH_OPERATORS.items():
        for lean_name in info["lean"].values():
            assert lean_name in resident.identifiers, (word, lean_name)
    # notation spellings of the derived surface
    for sym in ("ℕ", "ℤ", "∣", "∀", "∃", "∧",
                "∨", "→", "≠", "≤"):
        assert sym in resident.symbols, hex(ord(sym))
    # deliberately-absent vocabulary must NOT be resident
    for absent in ("Nat.Prime", "Prime", "Real", "Finset"):
        assert absent not in resident.identifiers


def test_resident_set_tracks_math_reading_changes(monkeypatch):
    """Mutation probe against a hardcoded copy: grow MATH_OPERATORS and the
    resident set (and classification) must follow with no census.py edit."""
    monkeypatch.setitem(
        math_reading.MATH_OPERATORS, "xyzzy",
        {"lean": {"Nat": "Nat.xyzzy"}, "arity": 1, "role": "pred",
         "enum_only": False})
    grown = census.derive_resident_set()
    assert "Nat.xyzzy" in grown.identifiers
    stmt = "∀ (n : ℕ), Nat.xyzzy n"
    assert census.classify_row(stmt, grown)["in_fragment"] is True
    # and WITHOUT the grown operator the same statement is out of fragment
    monkeypatch.delitem(math_reading.MATH_OPERATORS, "xyzzy")
    base = census.derive_resident_set()
    assert census.classify_row(stmt, base)["in_fragment"] is False


def test_resident_set_reads_admitted_registry(tmp_path):
    """The derivation walks admitted.json live: the real registry derives
    cleanly; a registry whose definition mentions a non-kernel op (an R3
    eliminability violation) refuses with ValueError."""
    ok = census.derive_resident_set(admitted_path=census.ADMITTED_PATH)
    assert isinstance(ok.identifiers, frozenset) and ok.identifiers
    bad = tmp_path / "admitted.json"
    bad.write_text(json.dumps({
        "evil": {"row": {"word": "evil", "params": ["a"],
                         "definition": {"op": "frobnicate",
                                        "args": [{"ref": "a"}]}}}}),
        encoding="utf-8")
    with pytest.raises(ValueError):
        census.derive_resident_set(admitted_path=bad)
    # a missing registry is the documented no-op path, never an error
    none = census.derive_resident_set(admitted_path=tmp_path / "absent.json")
    assert none.identifiers == ok.identifiers


# ======================================================== queue runner =====
def test_runner_statement_hash_single_sourced():
    mod = _load_runner_module()
    pp = "∀ (n : ℕ), n ∣ n"
    assert mod.statement_hash(pp) == common.sha256_json(
        {"mathlib_commit": common.MATHLIB_COMMIT, "statement_pp": pp})


def test_runner_normalize_sorts_and_stamps(tmp_path):
    mod = _load_runner_module()
    raw = [
        json.dumps({"decl_name": "B.b", "module": "Mathlib.Z",
                    "kind": "theorem", "statement_pp": "x"}),
        json.dumps({"decl_name": "A.a", "module": "Mathlib.A",
                    "kind": "def", "statement_pp": "y"}),
        json.dumps({"decl_name": "A.z", "module": "Mathlib.A",
                    "kind": "theorem", "statement_pp": "z"}),
    ]
    rows = mod.normalize_raw_rows(raw)
    assert [(r["module"], r["decl_name"]) for r in rows] == [
        ("Mathlib.A", "A.a"), ("Mathlib.A", "A.z"), ("Mathlib.Z", "B.b")]
    for r in rows:
        assert r["status"] == "pending"
        assert r["statement_hash"] == mod.statement_hash(r["statement_pp"])
    # byte-stable queue writes (canonical_json + LF), twice identical
    q1, q2 = tmp_path / "q1.jsonl", tmp_path / "q2.jsonl"
    mod.write_queue(rows, q1)
    mod.write_queue(rows, q2)
    assert q1.read_bytes() == q2.read_bytes()
    assert q1.read_bytes().decode("ascii").splitlines()[0] == \
        common.canonical_json(rows[0])
    # malformed raw stream refuses, never best-effort
    with pytest.raises(ValueError):
        mod.normalize_raw_rows(['{"decl_name": "only"}'])
    with pytest.raises(ValueError):
        mod.normalize_raw_rows([raw[0], raw[0]])   # duplicate decl_name


def test_runner_refuses_cleanly_without_lean(tmp_path):
    """`python3 tools/enumerate_mathlib.py` refuses (exit 2, REFUSED line)
    when the lean toolchain is absent.  PATH is emptied for the child so the
    refusal path is exercised even on a host where Lean has appeared."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("CGB_LEAN",)}
    env["PATH"] = str(tmp_path)          # empty dir: no lake/lean anywhere
    env["CGB_LEAN"] = ""                 # falsy override -> real probe
    proc = subprocess.run(
        [sys.executable, str(_RUNNER), "--limit", "1"],
        cwd=str(_REPO), env=env, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    assert "REFUSED" in proc.stderr
    assert "lean toolchain absent" in proc.stderr


# ============================================== Lean-lane smoke (gated) ====
@pytest.mark.skipif(
    not common.lean_available(),
    reason="lean toolchain absent (REQUIRES_LEAN; common.lean_available() "
           "is False) -- deferred, not a failure")
@pytest.mark.skipif(
    not (pathlib.Path(common.LEAN_MATHLIB_DIR) / ".lake" / "build").exists(),
    reason="pinned Mathlib checkout not built yet (setup.sh --with-lean "
           "incomplete)")
def test_smoke_enumeration_single_module(tmp_path):
    """REQUIRES_LEAN smoke: enumerate one pinned module with --limit and
    check the queue contract end-to-end."""
    mod = _load_runner_module()
    out = tmp_path / "queue.jsonl"
    rc = mod.main(["--modules", "Mathlib.Data.Nat.GCD.Basic",
                   "--limit", "25", "--out", str(out)])
    assert rc == 0
    rows = [json.loads(l) for l in
            out.read_text(encoding="utf-8").splitlines()]
    assert 0 < len(rows) <= 25
    keys = [(r["module"], r["decl_name"]) for r in rows]
    assert keys == sorted(keys)
    for r in rows:
        assert set(r) == {"decl_name", "module", "kind", "statement_pp",
                          "statement_hash", "status"}
        assert r["status"] == "pending"
        assert r["statement_hash"] == mod.statement_hash(r["statement_pp"])

"""WP-A teeth: the Lean escape gate (F0.4), the pins/hashes (F0.1), and the
LeanBackend honest-degradation path (F-H).

Pure Python; runs NOW with no Lean toolchain.  The escape-gate teeth prove the
cheap-fast-reject fires; the trust boundary is the sandbox + L5 (exercised by
WP-G/WP-H once the toolchain lands).  Every method that would need a real
toolchain is gated with `skipif(not common.lean_available())` -- skip-with-
reason, never fail (⚠X7).
"""
import unicodedata

import pytest

import common
from buildloop import validate_lean
from kernel.backends import LeanBackend

# A pinned, in-whitelist import for the clean fixtures.
_PIN_IMPORT = common.MATHLIB_IMPORTS[0]

# A clean `:= sorry` statement over the fragment -- ASCII names, a pinned
# import, no metaprogramming.  This MUST pass the gate.
_CLEAN_SORRY = (
    f"import {_PIN_IMPORT}\n"
    "theorem cgb_stmt (n : Nat) (h : 2 < n) : n * 1 = n := sorry\n"
)


# =========================================================== escape-gate TEETH
def test_native_decide_refused():
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n"
        "theorem t (n : Nat) : n = n := by native_decide\n")
    assert ok is False
    assert "native_decide" in reason


def test_macro_escape_refused():
    # a planted `macro_rules` / `macro` metaprogramming escape.
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n"
        "macro_rules | `(tactic| cheat) => `(tactic| sorry)\n"
        "theorem t : True := by cheat\n")
    assert ok is False
    assert "macro" in reason


def test_bare_macro_keyword_refused():
    ok, reason = validate_lean.validate_lean("macro foo : term => `(1)\n")
    assert ok is False and "macro" in reason


def test_maxheartbeats_zero_refused():
    # maxHeartbeats 0 = unlimited -> REFUSE (⚠D12).
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n"
        "set_option maxHeartbeats 0 in\n"
        "theorem t (n : Nat) : n = n := by rfl\n")
    assert ok is False
    assert "maxHeartbeats" in reason


def test_maxheartbeats_in_range_passes():
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n"
        f"set_option maxHeartbeats {common.LEAN_MAXHEARTBEATS} in\n"
        "theorem t (n : Nat) : n = n := by rfl\n")
    assert ok is True, reason


def test_maxrecdepth_over_cap_refused():
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n"
        f"set_option maxRecDepth {common.LEAN_MAXRECDEPTH + 1} in\n"
        "theorem t (n : Nat) : n = n := by rfl\n")
    assert ok is False and "maxRecDepth" in reason


def test_nonwhitelisted_set_option_refused():
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n"
        "set_option pp.all true in\n"
        "theorem t (n : Nat) : n = n := by rfl\n")
    assert ok is False and "set_option" in reason


def test_homoglyph_identifier_refused():
    # a Cyrillic 'а' (U+0430) hidden inside an identifier -- non-ASCII word char.
    ident = "nаme"
    assert any(ord(c) > 0x7F for c in ident)
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n"
        f"theorem t ({ident} : Nat) : {ident} = {ident} := sorry\n")
    assert ok is False
    assert "non-ASCII" in reason


def test_guillemet_raw_identifier_refused():
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n"
        "theorem t : True := by «macro_rules»\n")
    assert ok is False


def test_fullwidth_macro_normalized_and_refused():
    # NFKC folds fullwidth letters to ASCII BEFORE matching; a fullwidth
    # 'macro' must still be caught.  (These are non-ASCII word chars too, so
    # the homoglyph rule also fires -- either refusal is correct.)
    fw = "ｍａｃｒｏ"  # ｍａｃｒｏ
    assert unicodedata.normalize("NFKC", fw) == "macro"
    ok, _ = validate_lean.validate_lean(f"{fw} foo : term => `(1)\n")
    assert ok is False


def test_out_of_pin_import_refused():
    ok, reason = validate_lean.validate_lean(
        "import Mathlib.Data.Real.Basic\n"
        "theorem t (x : Real) : x = x := sorry\n")
    assert ok is False
    assert "MATHLIB_IMPORTS" in reason or "import" in reason


def test_extern_attribute_refused():
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\n@[extern \"c_impl\"] def f : Nat := 0\n")
    assert ok is False


def test_eval_command_refused():
    ok, reason = validate_lean.validate_lean(f"import {_PIN_IMPORT}\n#eval 1\n")
    assert ok is False


def test_axiom_token_refused():
    ok, reason = validate_lean.validate_lean(
        f"import {_PIN_IMPORT}\naxiom sneaky : False\n")
    assert ok is False and "axiom" in reason


def test_clean_sorry_statement_passes():
    ok, reason = validate_lean.validate_lean(_CLEAN_SORRY)
    assert ok is True, reason


def test_every_pinned_import_is_accepted():
    # each pinned module, on its own, must survive the import whitelist.
    for m in common.MATHLIB_IMPORTS:
        ok, reason = validate_lean.validate_lean(
            f"import {m}\ntheorem t : True := sorry\n")
        assert ok is True, (m, reason)


# ============================================================ pins / hashes
def test_lean_available_false_here():
    assert common.lean_available() is False


def test_lean_available_deterministic():
    assert common.lean_available() == common.lean_available()


def test_lean_toolchain_hash_deterministic():
    a = common.lean_toolchain_hash()
    b = common.lean_toolchain_hash()
    assert a == b
    assert isinstance(a, str) and len(a) == 64


def test_validate_lean_hash_deterministic():
    a = common.validate_lean_hash()
    b = common.validate_lean_hash()
    assert a == b
    assert isinstance(a, str) and len(a) == 64


def test_toolchain_hash_folds_the_pins():
    # sanity: the joint hash actually depends on its inputs (single-sourced).
    base = common.lean_toolchain_hash()
    saved = common.MATHLIB_IMPORTS
    try:
        common.MATHLIB_IMPORTS = saved + ("Mathlib.Extra.Thing",)
        assert common.lean_toolchain_hash() != base
    finally:
        common.MATHLIB_IMPORTS = saved
    assert common.lean_toolchain_hash() == base


# ================================================= LeanBackend honest degrade
def test_elaborate_unavailable_here():
    be = LeanBackend()
    res = be.elaborate(_CLEAN_SORRY, expect_sorry=True)
    assert res["unavailable"] is True
    assert res["ok"] is False
    assert res["olean_path"] is None


def test_recheck_unavailable_here():
    be = LeanBackend()
    res = be.recheck("/nonexistent/CgbScratch.olean")
    assert res["unavailable"] is True
    assert res["ok"] is False
    assert res["axioms"] == []


def test_eval_props_unavailable_here():
    be = LeanBackend()
    out = be.eval_props(f"import {_PIN_IMPORT}", ["1 = 1", "2 + 2 = 4"])
    assert len(out) == 2
    for row in out:
        assert row["unavailable"] is True
        assert row["value"] == "unavailable"
        assert row["closed_by"] is None


def test_cache_key_deterministic_and_identity_sensitive():
    be = LeanBackend()
    k1 = be._cache_key("elaborate:sorry=True", b"theorem a := sorry")
    k2 = be._cache_key("elaborate:sorry=True", b"theorem a := sorry")
    k3 = be._cache_key("elaborate:sorry=True", b"theorem b := sorry")
    assert k1 == k2
    assert k1 != k3
    assert k1.startswith("lean:")


# --------- toolchain-requiring tests: skip-with-reason, never fail (⚠X7) -----
@pytest.mark.skipif(not common.lean_available(), reason="lean toolchain absent")
def test_elaborate_real_toolchain():
    be = LeanBackend()
    res = be.elaborate(_CLEAN_SORRY, expect_sorry=True)
    # a bare-sorry statement elaborates (run 1); the verdict is recheck()'s.
    assert res.get("unavailable") is not True


@pytest.mark.skipif(not common.lean_available(), reason="lean toolchain absent")
def test_recheck_real_toolchain_axioms_are_data():
    be = LeanBackend()
    el = be.elaborate(_CLEAN_SORRY, expect_sorry=True)
    rc = be.recheck(el["olean_path"])
    # a bare-sorry statement audits to sorryAx present (⚠D5).
    assert "sorryAx" in rc["axioms"]


if __name__ == "__main__":
    import sys
    raise SystemExit(pytest.main([__file__, "-q", *sys.argv[1:]]))

"""Teeth for tools/FgReflect.lean (reflection target 1, v0 slice).

Two layers, honest about what runs where:
  * the ESCAPE-GATE tooth runs in every container (the Lean backend re-gates
    everything it elaborates, so a gate-refused module is dead on arrival --
    catch that here, cheaply, without a toolchain);
  * the ELABORATION tooth runs only in the Lean lane (common.lean_available);
    elsewhere it skips with a named reason, never a silent pass.

The elaboration result is RUN-1 evidence (an elaboration typecheck inside
the jail, the run/import_rt.py honesty note verbatim); the two-run L5
adjudication applies when a cert is minted from this module, not here.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop.validate_lean import validate_lean

_SRC_PATH = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "FgReflect.lean")


def _source() -> str:
    with open(_SRC_PATH) as fh:
        return fh.read()


def test_source_passes_escape_gate():
    # The gate bans deriving/attributes/notation/non-ASCII identifiers; the
    # module is written inside that envelope BY DESIGN (its docstring's
    # CONSTRAINTS block).  A regression here means elaborate() would refuse
    # the file before Lean ever saw it.
    ok, reason = validate_lean(_source())
    assert ok, f"FgReflect.lean fails its own escape gate: {reason}"


def test_source_carries_no_sorry_and_no_axiom():
    src = _source()
    assert "sorry" not in src          # reflection means PROVEN, not deferred
    assert "axiom" not in src          # gate would refuse; belt and braces


def test_soundness_theorems_present():
    # The load-bearing names the Python side will cite when minting
    # reflection-backed verdicts; renaming them is an interface change.
    src = _source()
    for name in ("check_sound", "check_complete", "checkAll_sound",
                 "evalTm_subst", "denote_subst", "witness_of_check",
                 "checkAll_witness", "dvd_iff_emod_eq_zero",
                 "pdvd_denote_iff_dvd", "sex_of_template",
                 # S5: the box layer over full quantifier prefixes
                 "checkStmtBox_sound", "denoteStmt_of_box",
                 "checkStmtBox_sound_exOnly", "checkAll_sound_stmt",
                 "checkAll_witness_stmt",
                 # S6 first shape: guard-shape preservation
                 "sall_guard_iff", "compile_guard_shape",
                 "sall_guard_of_check",
                 # S6 shapes 2-5: chains, ∀ segments, mixed prefixes,
                 # conjoined conclusions (list folds, one lemma per shape)
                 "compile_hyp_chain_shape", "hyp_chain_of_check",
                 "compile_foralls_shape", "compile_prefix_shape",
                 "compile_conj_shape", "conj_of_check",
                 # S6-carrier: the Nat layer (truncated sub PROVEN)
                 "checkN_sound", "checkN_complete", "checkAllN_sound",
                 "evalTmN_subst", "denoteN_subst", "witness_of_checkN",
                 "checkAllN_witness",
                 # shape-6 first retirement: pow via unroll (D10)
                 "evalTm_powTm", "substTm_powTm",
                 # the Nat Stmt layer (search route crosses the carrier)
                 "checkStmtBoxN_sound", "denoteStmtN_of_box",
                 "checkStmtBoxN_sound_exOnly"):
        assert f"theorem {name}" in src, name


@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent (Lean-lane test)")
def test_elaborates_under_lean():
    from kernel.backends import LeanBackend
    res = LeanBackend().elaborate(_source(), expect_sorry=False)
    assert not res.get("unavailable"), res
    assert res.get("ok"), res

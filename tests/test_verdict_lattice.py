#!/usr/bin/env python3
"""FI-KA-2 acceptance -- the verdict lattice, LLM-free, Lean-free, fast.

`kernel.verdict_lattice` is a pure, total mapping of a (shadow, kernel) pair
(plus the divergence bit and the committed-artifact state) to §12.2's five-point
lattice.  These teeth prove:

  * the FROZEN five-point enum and the total 12-cell mapping table;
  * the HEADLINE tooth (§7.2 realized): the source-43 fixture cell
    shadow-refuted × kernel-proved maps to `kernel-proved`, NOT `divergent`;
  * the contradiction bit is set by EXACTLY the two named triggers (T-a / T-b)
    and forces `divergent` from any cell;
  * the sticky `unresolved_divergence` input pins `divergent` unconditionally;
  * the partial order (chain + incomparable `divergent`);
  * legal vs illegal transitions (kernel-proved terminal-but-for-divergent; no
    downward move; divergent released only by the human artifact);
  * terminal vs adjudication-demanding points;
  * the Lean-absent column: `unavailable` NEVER becomes `kernel-failed`;
  * an all-five round-trip (every lattice point is producible & reportable).

Runnable under pytest AND as a bare script
(`python3 tests/test_verdict_lattice.py` -> PASS lines, exit 0).
"""
from __future__ import annotations

import itertools
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from kernel import verdict_lattice as vl


def _expect_valueerror(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError(f"expected ValueError from {fn.__name__}({args}, {kwargs})")


# --------------------------------------------------------------------------- #
# Frozen enum + vocabularies.
# --------------------------------------------------------------------------- #
def test_frozen_enum_is_exactly_the_five():
    """The five §12.2 points, in the frozen order, no more no fewer."""
    assert vl.LATTICE_POINTS == (
        "kernel-proved", "shadow-certified", "shadow-edge-refused",
        "kernel-failed", "divergent")
    assert len(set(vl.LATTICE_POINTS)) == 5
    assert vl.SHADOW_INPUTS == ("pass", "refuted", "skip")
    assert vl.KERNEL_INPUTS == ("proved", "failed", "unavailable", "not-attempted")


def test_two_trigger_names_frozen():
    """Exactly two triggers may set the bit; their names match FI-KA-3's schema."""
    assert vl.TRIGGERS == (
        "in-bound-witness-contradiction", "decidable-instance-mismatch")
    assert vl.TRIGGER_IN_BOUND_WITNESS == "in-bound-witness-contradiction"   # T-a
    assert vl.TRIGGER_DECIDABLE_MISMATCH == "decidable-instance-mismatch"    # T-b
    assert len(vl.TRIGGERS) == 2


# --------------------------------------------------------------------------- #
# The total mapping table (12 cells, frozen).
# --------------------------------------------------------------------------- #
_FROZEN_TABLE = {
    ("pass", "proved"):           "kernel-proved",
    ("pass", "failed"):           "kernel-failed",
    ("pass", "unavailable"):      "shadow-certified",
    ("pass", "not-attempted"):    "shadow-certified",
    ("refuted", "proved"):        "kernel-proved",      # T-a false
    ("refuted", "failed"):        "kernel-failed",
    ("refuted", "unavailable"):   "shadow-edge-refused",
    ("refuted", "not-attempted"): "shadow-edge-refused",
    ("skip", "proved"):           "kernel-proved",
    ("skip", "failed"):           "kernel-failed",
    ("skip", "unavailable"):      None,                 # honest absence
    ("skip", "not-attempted"):    None,                 # honest absence
}


def test_mapping_is_total_and_matches_frozen_table():
    """Every (shadow, kernel) pair maps exactly as §12.2 freezes; `mapping_table`
    exposes the same 12 cells; the two honest-absence cells are `None`."""
    assert vl.mapping_table() == _FROZEN_TABLE
    for shadow in vl.SHADOW_INPUTS:
        for kernel in vl.KERNEL_INPUTS:
            got = vl.classify_verdict(shadow, kernel)          # no contradiction
            assert got == _FROZEN_TABLE[(shadow, kernel)], (shadow, kernel, got)
    # exactly two honest-absence cells, both under `skip`.
    absent = [k for k, v in _FROZEN_TABLE.items() if v is None]
    assert absent == [("skip", "unavailable"), ("skip", "not-attempted")]


def test_mapping_table_returns_a_copy():
    """`mapping_table` hands back a defensive copy -- mutating it can't poison
    the frozen table."""
    t = vl.mapping_table()
    t[("pass", "proved")] = "divergent"
    assert vl.classify_verdict("pass", "proved") == "kernel-proved"


# --------------------------------------------------------------------------- #
# TOOTH 1 (headline): the source-43 fixture cell.
# --------------------------------------------------------------------------- #
def test_source43_refuted_times_proved_is_kernel_proved_not_divergent():
    """(TOOTH) source 43 (`∀ n:Int, ∃ m:Int, n < m`): the bounded shadow refuses
    at the box edge (n=B), the kernel proves the unbounded theorem via the
    authored `m := n+1` term.  The lattice point is `kernel-proved`, NOT
    `divergent` -- the §7.2 permanent differential realized.  Divergence here
    requires trigger T-a to concretely fire, which for the honest edge-refusal
    it does not (m=n+1 lands OUT of the box)."""
    got = vl.classify_verdict("refuted", "proved", contradiction=False)
    assert got == "kernel-proved", got
    assert got != "divergent"


# --------------------------------------------------------------------------- #
# The contradiction bit: T-a / T-b force divergent; nothing else sets it.
# --------------------------------------------------------------------------- #
def test_contradiction_forces_divergent_from_every_cell():
    """A fired trigger (T-a or T-b) forces `divergent` from ANY cell, including
    source-43's refuted × proved."""
    for shadow, kernel in itertools.product(vl.SHADOW_INPUTS, vl.KERNEL_INPUTS):
        for trig in vl.TRIGGERS:
            got = vl.classify_verdict(
                shadow, kernel, contradiction=True, evidence={"trigger": trig})
            assert got == "divergent", (shadow, kernel, trig, got)


def test_ta_true_flips_refuted_proved_to_divergent():
    """The refuted × proved cell is the switch: T-a false => kernel-proved;
    T-a true (in-bound witness the shadow missed) => divergent."""
    false = vl.classify_verdict("refuted", "proved", contradiction=False)
    true = vl.classify_verdict(
        "refuted", "proved", contradiction=True,
        evidence={"trigger": vl.TRIGGER_IN_BOUND_WITNESS})
    assert false == "kernel-proved"
    assert true == "divergent"


def test_contradiction_requires_a_named_frozen_trigger():
    """contradiction=True with no trigger, an unknown trigger, or no evidence
    dict is refused -- the bit cannot be set by anything but T-a / T-b."""
    _expect_valueerror(vl.classify_verdict, "pass", "proved", contradiction=True)
    _expect_valueerror(vl.classify_verdict, "pass", "proved",
                       contradiction=True, evidence={})
    _expect_valueerror(vl.classify_verdict, "pass", "proved",
                       contradiction=True, evidence={"trigger": "made-up"})


def test_trigger_named_without_contradiction_is_inconsistent():
    """A trigger named while contradiction=False is a contradiction of inputs --
    the ONLY thing that may set the bit is a trigger, so the two must agree."""
    _expect_valueerror(
        vl.classify_verdict, "refuted", "proved",
        contradiction=False, evidence={"trigger": vl.TRIGGER_IN_BOUND_WITNESS})


# --------------------------------------------------------------------------- #
# Sticky unresolved-divergence input (FI-KA-3 coupling).
# --------------------------------------------------------------------------- #
def test_unresolved_divergence_pins_divergent_unconditionally():
    """While an unresolved artifact sits on the subject, EVERY cell returns
    `divergent` regardless of fresh channel inputs -- even the honest-absence
    cell and even with no contradiction."""
    for shadow, kernel in itertools.product(vl.SHADOW_INPUTS, vl.KERNEL_INPUTS):
        got = vl.classify_verdict(shadow, kernel, unresolved_divergence=True)
        assert got == "divergent", (shadow, kernel, got)
    # the sticky pin overrides even the source-43 permanent-differential cell.
    assert vl.classify_verdict(
        "refuted", "proved", unresolved_divergence=True) == "divergent"


# --------------------------------------------------------------------------- #
# Input validation.
# --------------------------------------------------------------------------- #
def test_unknown_inputs_are_refused():
    _expect_valueerror(vl.classify_verdict, "PASS", "proved")
    _expect_valueerror(vl.classify_verdict, "pass", "unknown")
    _expect_valueerror(vl.classify_verdict, "pass", "proved",
                       contradiction=True, evidence=["not", "a", "dict"])


# --------------------------------------------------------------------------- #
# Partial order.
# --------------------------------------------------------------------------- #
def test_partial_order_chain_and_incomparable_divergent():
    """kernel-failed ⊑ shadow-edge-refused ⊑ shadow-certified ⊑ kernel-proved;
    reflexive everywhere; `divergent` incomparable to every chain point."""
    chain = vl.ORDER_CHAIN
    assert chain == ("kernel-failed", "shadow-edge-refused",
                     "shadow-certified", "kernel-proved")
    # strict ascent along the chain.
    for lo, hi in zip(chain, chain[1:]):
        assert vl.leq(lo, hi) and not vl.leq(hi, lo)
    # transitive extreme.
    assert vl.leq("kernel-failed", "kernel-proved")
    assert not vl.leq("kernel-proved", "kernel-failed")
    # reflexive on all five.
    for p in vl.LATTICE_POINTS:
        assert vl.leq(p, p)
    # divergent is incomparable to each chain point (both directions False).
    for p in chain:
        assert not vl.leq("divergent", p)
        assert not vl.leq(p, "divergent")


def test_terminal_and_adjudication_partition():
    """The four terminal end-states report; `divergent` alone demands
    adjudication; the two roles partition the five points."""
    assert set(vl.TERMINAL_POINTS) == {
        "kernel-proved", "shadow-certified", "shadow-edge-refused", "kernel-failed"}
    assert vl.ADJUDICATION_DEMANDING == ("divergent",)
    for p in vl.LATTICE_POINTS:
        assert vl.is_terminal(p) != vl.demands_adjudication(p)   # exactly one
    assert vl.demands_adjudication("divergent")
    assert not vl.is_terminal("divergent")


# --------------------------------------------------------------------------- #
# TOOTH: legal / illegal transitions.
# --------------------------------------------------------------------------- #
def test_legal_transitions():
    """The frozen legal moves: evidence lands, toolchain repairs, a fresh
    attempt fails to kernel-failed, and any point trips to divergent."""
    legal = [
        ("shadow-certified", "kernel-proved"),      # kernel evidence lands
        ("shadow-edge-refused", "kernel-proved"),   # kernel evidence lands
        ("shadow-certified", "kernel-failed"),      # a fresh attempt failed
        ("shadow-edge-refused", "kernel-failed"),
        ("kernel-failed", "kernel-proved"),         # repaired toolchain/template
        ("shadow-edge-refused", "shadow-certified"),  # upward within the chain
    ]
    for src, dst in legal:
        assert vl.is_legal_transition(src, dst), (src, dst)
    # any point may trip to divergent.
    for p in vl.LATTICE_POINTS:
        assert vl.is_legal_transition(p, "divergent")
    # a stable point is not an illegal "change".
    for p in vl.LATTICE_POINTS:
        assert vl.is_legal_transition(p, p)


def test_illegal_transitions_refused():
    """kernel-proved is terminal but for divergent; no downward chain move;
    divergent is released only by the human artifact, never by code."""
    # kernel-proved -> anything except divergent is illegal.
    for dst in ("shadow-certified", "shadow-edge-refused", "kernel-failed"):
        assert not vl.is_legal_transition("kernel-proved", dst), dst
    # downward chain moves (other than the sanctioned -> kernel-failed) illegal.
    assert not vl.is_legal_transition("shadow-certified", "shadow-edge-refused")
    # divergent -> anything (other than staying divergent) is illegal BY CODE.
    for dst in ("kernel-proved", "shadow-certified",
                "shadow-edge-refused", "kernel-failed"):
        assert not vl.is_legal_transition("divergent", dst), dst


def test_transition_rejects_unknown_points():
    _expect_valueerror(vl.is_legal_transition, "bogus", "kernel-proved")
    _expect_valueerror(vl.is_legal_transition, "kernel-proved", "bogus")


# --------------------------------------------------------------------------- #
# TOOTH: the Lean-absent column -- unavailable is NEVER kernel-failed.
# --------------------------------------------------------------------------- #
def test_lean_absent_column_maps_to_shadow_never_kernel_failed():
    """In a toolchain-less container every ∃ reading rides the shadow column:
    pass -> shadow-certified, refuted -> shadow-edge-refused, skip -> honest
    absence.  `unavailable` (and `not-attempted`) is NEVER `kernel-failed` -- a
    Lean-free CI run must not report a wall of kernel-failed."""
    for kernel in ("unavailable", "not-attempted"):
        assert vl.classify_verdict("pass", kernel) == "shadow-certified"
        assert vl.classify_verdict("refuted", kernel) == "shadow-edge-refused"
        assert vl.classify_verdict("skip", kernel) is None
        # the whole column: no cell is ever kernel-failed.
        for shadow in vl.SHADOW_INPUTS:
            assert vl.classify_verdict(shadow, kernel) != "kernel-failed"


# --------------------------------------------------------------------------- #
# TOOTH: all-five round-trip.
# --------------------------------------------------------------------------- #
def test_all_five_round_trip_producible():
    """Every one of the five lattice points is producible through
    `classify_verdict` and classified by exactly one of terminal /
    adjudication-demanding -- the 5-valued field can never be booleanised."""
    producers = {
        "kernel-proved":       lambda: vl.classify_verdict("pass", "proved"),
        "shadow-certified":    lambda: vl.classify_verdict("pass", "unavailable"),
        "shadow-edge-refused": lambda: vl.classify_verdict("refuted", "unavailable"),
        "kernel-failed":       lambda: vl.classify_verdict("pass", "failed"),
        "divergent":           lambda: vl.classify_verdict(
            "refuted", "proved", contradiction=True,
            evidence={"trigger": vl.TRIGGER_DECIDABLE_MISMATCH}),
    }
    produced = {name: make() for name, make in producers.items()}
    # each producer yields its own point; together they cover all five, exactly.
    for name, point in produced.items():
        assert point == name, (name, point)
    assert set(produced.values()) == set(vl.LATTICE_POINTS)


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print("PASS", _name)
    print("verdict lattice holds "
          "(frozen 5-point enum; total 12-cell table; source-43 refuted×proved "
          "-> kernel-proved not divergent; T-a/T-b the only bit-setters; sticky "
          "unresolved-divergence; chain order + incomparable divergent; "
          "legal/illegal transitions; Lean-absent column never kernel-failed; "
          "all-five round-trip)")

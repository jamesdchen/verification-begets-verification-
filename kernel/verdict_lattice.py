"""FI-KA-2 — the verdict lattice (WP-KA, §12.2).

Replaces the ∃-anchor boolean with §12.2's five-point lattice: the honest
join of the *bounded shadow* verdict (recomputed fresh from
`math_eval.exists_instances` / `exists_shadow_shape` at the pipeline's bound)
and the *kernel* verdict (`kernel.check` on the v12 exists-anchor contract).

Pure and total: no I/O, no clock, no randomness, and **no imports from the
sibling KA builders' modules** — this file consumes only the frozen strings and
plain `bool`/`dict` inputs the spec (`KA_INTERFACES.md` FI-KA-2) freezes.
Computing the shadow verdict, the kernel verdict, and the two contradiction
triggers is the runner's job (FI-KA-1/B6); this module only *maps* those inputs
to a lattice point, *orders* the points, and *refuses* illegal transitions.

The package's whole tooth (§7.2 realized): **shadow-refuted × kernel-proved is
NOT `divergent`** — it is the permanent differential (source 43). The shadow
refutes only the *bounded* claim; that never contradicts the unbounded theorem.
`divergent` is reached only when a concrete trigger (T-a / T-b) fires, or while
an unresolved divergence artifact (FI-KA-3) sits on the subject.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# The enum — exactly §12.2's five, frozen order (KA_INTERFACES.md FI-KA-2).
# --------------------------------------------------------------------------- #
LATTICE_POINTS = ("kernel-proved", "shadow-certified", "shadow-edge-refused",
                  "kernel-failed", "divergent")

# --------------------------------------------------------------------------- #
# Inputs (frozen vocabularies).
#   shadow — recomputed fresh at the pipeline's bound, never parsed from a CSV.
#   kernel — proved iff kernel.check returned a Certificate; failed iff an
#            ErrorTranscript with the toolchain present; unavailable iff
#            common.lean_available() is False; not-attempted iff the emitter
#            skipped.  `unavailable` is NEVER `kernel-failed` (the Lean-absent
#            container mirrors _lean_kernel_channel's honest `unknown`).
# --------------------------------------------------------------------------- #
SHADOW_INPUTS = ("pass", "refuted", "skip")
KERNEL_INPUTS = ("proved", "failed", "unavailable", "not-attempted")

# --------------------------------------------------------------------------- #
# The contradiction bit — set by EXACTLY two triggers, nothing else (§12.2).
# Computing them is the runner's job (T-a needs `eval_term` over the accepted
# template; T-b needs a Lean `decide` disproof via `eval_props`).  This module
# only DOCUMENTS and ENFORCES their two names — the same strings FI-KA-3's
# divergence artifact records under its `trigger` key.
#
#   T-a  in-bound-witness contradiction:  kernel proved AND shadow refuted at
#        outer point o AND the accepted template's inner values at o all lie
#        INSIDE the bounded box — the shadow's exhaustive sweep should have
#        found that witness; one of enumerator / evaluator / kernel is wrong.
#   T-b  decidable-instance mismatch:  Python `eval_pred` says a fully
#        instantiated conclusion is True at an admitted point but Lean `decide`
#        on the same closed instance returns a disproof/False-class result (the
#        T4 mirror-divergence class on the kernel channel).  A mere tactic
#        failure to close is NOT T-b.
# --------------------------------------------------------------------------- #
TRIGGER_IN_BOUND_WITNESS = "in-bound-witness-contradiction"      # T-a
TRIGGER_DECIDABLE_MISMATCH = "decidable-instance-mismatch"       # T-b
TRIGGERS = (TRIGGER_IN_BOUND_WITNESS, TRIGGER_DECIDABLE_MISMATCH)

# --------------------------------------------------------------------------- #
# Terminal vs adjudication-demanding (§12.2).
#   Terminal — honest, reportable end-states for the wave record; the latter
#   three are supersedable UPWARD in later runs, kernel-proved is not.
#   Demands adjudication — `divergent` only (the absorbing tripwire).
# --------------------------------------------------------------------------- #
TERMINAL_POINTS = ("kernel-proved", "shadow-certified",
                   "shadow-edge-refused", "kernel-failed")
ADJUDICATION_DEMANDING = ("divergent",)

# --------------------------------------------------------------------------- #
# The partial order (evidence strength).  A single chain, with `divergent` the
# designated absorbing tripwire — incomparable to every chain point (§12.2):
#
#   kernel-failed ⊑ shadow-edge-refused ⊑ shadow-certified ⊑ kernel-proved
#
# ORDER_CHAIN is ascending; index == rank.
# --------------------------------------------------------------------------- #
ORDER_CHAIN = ("kernel-failed", "shadow-edge-refused",
               "shadow-certified", "kernel-proved")

# --------------------------------------------------------------------------- #
# The mapping (total function; frozen — KA_INTERFACES.md FI-KA-2).
#
#   shadow \ kernel | proved      | failed        | unavailable / not-attempted
#   ----------------+-------------+---------------+----------------------------
#   pass            | kernel-proved | kernel-failed | shadow-certified
#   refuted         | kernel-proved*| kernel-failed | shadow-edge-refused
#   skip            | kernel-proved | kernel-failed | None (honest absence)
#
#   * refuted × proved is kernel-proved when T-a is FALSE (the §7.2 permanent
#     differential — source 43's tooth); when T-a fires, `contradiction` forces
#     `divergent` before this table is consulted.
#
# The (skip, unavailable/not-attempted) cell is `None`: no anchor claim exists,
# honest absence — deliberately NOT a lattice point.
# --------------------------------------------------------------------------- #
_MAPPING: "dict[tuple[str, str], str | None]" = {
    ("pass", "proved"):          "kernel-proved",
    ("pass", "failed"):          "kernel-failed",
    ("pass", "unavailable"):     "shadow-certified",
    ("pass", "not-attempted"):   "shadow-certified",
    ("refuted", "proved"):       "kernel-proved",      # T-a false; T-a true => divergent
    ("refuted", "failed"):       "kernel-failed",
    ("refuted", "unavailable"):  "shadow-edge-refused",
    ("refuted", "not-attempted"): "shadow-edge-refused",
    ("skip", "proved"):          "kernel-proved",
    ("skip", "failed"):          "kernel-failed",
    ("skip", "unavailable"):     None,                 # honest absence
    ("skip", "not-attempted"):   None,                 # honest absence
}


def _require(value: str, allowed: tuple, name: str) -> None:
    if value not in allowed:
        raise ValueError(
            f"verdict-lattice: unknown {name} {value!r}; must be one of {allowed}")


def _validate_contradiction(contradiction: bool, evidence) -> None:
    """Enforce the ``nothing else may set the bit`` invariant: the bit is True
    iff exactly one of the two frozen triggers is named in ``evidence``.

    * ``contradiction`` True  => ``evidence['trigger']`` must be in ``TRIGGERS``.
    * ``contradiction`` False => ``evidence`` must not name a trigger.
    """
    named = None
    if evidence is not None:
        if not isinstance(evidence, dict):
            raise ValueError(
                "verdict-lattice: evidence must be a dict or None, "
                f"got {type(evidence).__name__}")
        named = evidence.get("trigger")
    if contradiction:
        if named not in TRIGGERS:
            raise ValueError(
                "verdict-lattice: contradiction=True requires "
                f"evidence['trigger'] in {TRIGGERS}; got {named!r}. Only T-a "
                "(in-bound-witness) / T-b (decidable-instance) may set the bit.")
    else:
        if named is not None:
            raise ValueError(
                f"verdict-lattice: evidence names trigger {named!r} but "
                "contradiction=False; a trigger is the ONLY thing that may set "
                "the divergence bit, so the two inputs are inconsistent.")


def classify_verdict(shadow: str, kernel: str, *,
                     contradiction: bool = False,
                     evidence: "dict | None" = None,
                     unresolved_divergence: bool = False) -> "str | None":
    """Map a (shadow, kernel) pair to its lattice point (§12.2, total function).

    Priority (highest first):
      1. ``unresolved_divergence`` — while an unresolved FI-KA-3 artifact sits
         on the subject, the point is ``divergent`` UNCONDITIONALLY, regardless
         of fresh channel inputs.  Only a human resolution artifact releases it;
         no code path in this module ever un-sets it.
      2. ``contradiction`` — a fired trigger (T-a or T-b) forces ``divergent``
         from ANY cell.
      3. the frozen mapping table.

    Returns a member of ``LATTICE_POINTS``, or ``None`` for the honest-absence
    cell (skip × unavailable/not-attempted) when no divergence governs it.
    """
    _require(shadow, SHADOW_INPUTS, "shadow")
    _require(kernel, KERNEL_INPUTS, "kernel")
    _validate_contradiction(contradiction, evidence)

    if unresolved_divergence:
        # Sticky: FI-KA-3's committed artifact governs; recomputation with the
        # trigger "gone" (e.g. after a bound change) never releases it — only a
        # human resolution field does (no such writer exists in this module).
        return "divergent"
    if contradiction:
        return "divergent"
    return _MAPPING[(shadow, kernel)]


def mapping_table() -> "dict[tuple[str, str], str | None]":
    """A copy of the frozen (shadow, kernel) -> point table (12 cells, total)."""
    return dict(_MAPPING)


# --------------------------------------------------------------------------- #
# Partial order.
# --------------------------------------------------------------------------- #
def leq(a: str, b: str) -> bool:
    """``a ⊑ b`` in the evidence-strength order.

    Reflexive on every lattice point.  On the chain, rank(a) ≤ rank(b).
    ``divergent`` is incomparable to every chain point (only ``divergent ⊑
    divergent`` holds) — the absorbing tripwire sits off to the side.
    """
    _require(a, LATTICE_POINTS, "point")
    _require(b, LATTICE_POINTS, "point")
    if a == b:
        return True
    if a == "divergent" or b == "divergent":
        return False
    return ORDER_CHAIN.index(a) < ORDER_CHAIN.index(b)


def is_terminal(point: str) -> bool:
    """True for the four honest end-states (kernel-proved is the only one not
    supersedable upward)."""
    _require(point, LATTICE_POINTS, "point")
    return point in TERMINAL_POINTS


def demands_adjudication(point: str) -> bool:
    """True for ``divergent`` only — the sole point that demands a human
    (FI-KA-3) adjudication artifact."""
    _require(point, LATTICE_POINTS, "point")
    return point in ADJUDICATION_DEMANDING


# --------------------------------------------------------------------------- #
# Legal / illegal transitions across runs.
#
# A "transition" = the point for a subject changing between evaluations (always
# via a fresh cache key, never mutation of an issued cert).  The frozen rules
# (§12.2):
#   * any point -> divergent           (a trigger fires)                legal
#   * shadow-*  -> kernel-proved        (kernel evidence lands)         legal
#   * kernel-failed -> kernel-proved    (repaired toolchain/template)   legal
#   * shadow-*  -> kernel-failed        (a fresh anchor attempt failed) legal
#   * upward chain moves                (evidence gained)               legal
#   * kernel-proved -> anything but divergent                         ILLEGAL
#   * any downward chain move (other than the sanctioned -> kernel-failed
#     re-evaluation sink)                                             ILLEGAL
#   * divergent -> anything             (only FI-KA-3's human artifact
#     releases it; the lattice function never does so BY CODE)       ILLEGAL
# --------------------------------------------------------------------------- #
def is_legal_transition(src: str, dst: str) -> bool:
    """True iff a subject may move from ``src`` to ``dst`` between runs."""
    _require(src, LATTICE_POINTS, "src point")
    _require(dst, LATTICE_POINTS, "dst point")
    if src == dst:
        return True                       # a stable point is not a "change"
    if dst == "divergent":
        return True                       # any point may trip the tripwire
    if src == "divergent":
        return False                      # released only by the human artifact
    if src == "kernel-proved":
        return False                      # terminal but for the divergent trip
    # src is one of the three supersedable points.
    if dst == "kernel-failed":
        return True                       # the sanctioned re-evaluation sink
    # otherwise: legal only upward in the chain (evidence gained).
    return ORDER_CHAIN.index(dst) > ORDER_CHAIN.index(src)

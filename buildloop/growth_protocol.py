"""The growth protocol: the one pattern behind every vocabulary grower.

THE OBSERVATION (long suspected, now written down as code): everything in
this repo that grows -- the generator library, operator words, mined macros,
and every planned grower (carriers, witness-template shapes, tactic combos,
proof abstractions) -- instantiates ONE schema:

    row          a candidate as pure data (never code);
    conserve     why admitting it cannot change what is true
                 (expansion-eliminability, anchoring to ground truth, or a
                 kernel-native definitional mechanism);
    battery      the correctness/quality checks (differential agreement,
                 round-trips, degeneracy refusals);
    price        the economics gate (strict DL descent in one currency);
    witnesses    real-usage evidence (the two-witness discipline);
    persist      tamper-safe storage (content-hash-bound certs).

WHY THIS FILE IS A REGISTRY AND NOT A REFACTOR.  The existing growers carry
COMMITTED cert byte-shapes (operator cert ids hash canonical rows; macro
admissions are persisted evidence).  Extracting a shared base class would
churn certified bytes for zero semantic gain -- exactly the encoding
lock-in R1-R4 warns about.  So the dedup runs FORWARD, not backward: new
growers implement this protocol; existing growers are REGISTERED against it
by dotted name, and the conformance test asserts every role resolves --
a living map of the pattern that fails CI when a grower's interface drifts,
without touching a single certified byte.

THE ANTI-LIST, equally load-bearing: kernel checkers, contract types, the
escape-gate blocklist, and the ladder's primitive rungs must NEVER grow by
this protocol.  They are trust roots -- they grow only by ceremony (one per
phase, TRUST.md entry) or by proof (reflection).  The boundary between the
registry below and this anti-list IS the trust architecture.
"""
from __future__ import annotations

import importlib

ROLES = ("row", "conserve", "battery", "price", "witnesses", "persist")

# Each grower maps every role to the dotted name of the code (or the named
# discipline) that fills it.  A dotted name must RESOLVE; a prose entry
# (parenthesized) names a discipline that lives outside a single callable.
GROWERS = {
    "generator-library": {
        "row": "buildloop.validate.validate_generator_spec",
        "conserve": "(emit-check tier: every output individually certified)",
        "battery": "buildloop.admission.admit",
        "price": "buildloop.mdl.admission_decision",
        "witnesses": "(backlog coverage: zero-coverage candidates refused)",
        "persist": "library.Registry.register",
    },
    "operator-words": {
        "row": "generators.operator_growth.canonical_row",
        "conserve": "generators.operator_growth._expand_definition_to_kernel",
        "battery": "generators.operator_growth._run_battery",
        "price": "generators.operator_growth._pricing_decision",
        "witnesses": "(two exogenous witnesses inside _pricing_decision)",
        "persist": "generators.operator_growth.save_admitted",
    },
    "reading-macros": {
        "row": "buildloop.mdl_macros.macro_admission_decision",
        "conserve": "(reference-lowering translation-cert per use, H58)",
        "battery": "buildloop.mdl_macros.macro_admission_decision",
        "price": "buildloop.mdl_macros.macro_admission_decision",
        "witnesses": "(Z-E: exogenous witnesses only; dreams never decide)",
        "persist": "(registry macro table, expansion_context in cache ids)",
    },
    "proof-abstractions": {
        "row": "tools.proof_mine.mine",
        "conserve": "tools.proof_mine.certify_rewrite",
        "battery": "(Lean typecheck + corpus recompile: the cold-loop batch)",
        "price": "(holdout transfer x DL descent; rank_for_verification)",
        "witnesses": "tools.proof_mine.rank_for_verification",
        "persist": "tools.proof_mine.update_ledger",
    },
}

# Planned growers, registered as intentions so the map stays complete; their
# rows flip to dotted names as the code lands.
PLANNED = {
    "carriers": "L1: anchor to Mathlib's definitions; census-priced (WP-LI0)",
    "witness-template-shapes": "grammar growth fed by no-template-found skips",
    "tactic-combos": "expansion-defined rungs over the frozen primitives",
}

ANTI_LIST = (
    "kernel checkers", "contract types", "escape-gate blocklist",
    "primitive ladder rungs",
)


def resolve(dotted: str):
    """Resolve a dotted name to the object it names; parenthesized prose
    entries resolve to themselves (they name disciplines, not callables).
    The module/attribute boundary is found by importing the longest
    importable prefix (``library.Registry.register`` = module ``library``,
    then attributes ``Registry.register``)."""
    if dotted.startswith("("):
        return dotted
    parts = dotted.split(".")
    obj = None
    for i in range(len(parts), 0, -1):
        try:
            obj = importlib.import_module(".".join(parts[:i]))
            rest = parts[i:]
            break
        except ImportError:
            continue
    else:
        raise ImportError(f"no importable prefix in {dotted!r}")
    for part in rest:
        obj = getattr(obj, part)
    return obj


def conformance(grower_name: str) -> dict:
    """Every role present and resolvable.  Returns {role: kind} where kind is
    'code' or 'discipline'; raises on a missing role or a dotted name that no
    longer resolves -- the CI tooth against silent interface drift."""
    spec = GROWERS[grower_name]
    out = {}
    for role in ROLES:
        if role not in spec:
            raise KeyError(f"{grower_name}: role {role!r} unfilled")
        obj = resolve(spec[role])
        out[role] = "discipline" if isinstance(obj, str) else "code"
    return out

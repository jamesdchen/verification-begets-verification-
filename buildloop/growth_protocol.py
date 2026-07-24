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

ROLES = ("row", "conserve", "battery", "price", "witnesses", "persist",
         "teeth")

# Signature pins (tooth upgrade 1): resolution proves a name EXISTS; these
# prove its INTERFACE hasn't drifted.  Whitespace-normalized inspect
# signatures, captured at registration; a shape change without a registry
# update fails conformance.  (Semantic rewrites behind a stable signature
# remain the batteries' jurisdiction -- see module docstring.)
SIGNATURE_PINS = {
    "buildloop.validate.validate_generator_spec": "(text: 'str') -> 'dict'",
    "buildloop.admission.admit":
        "(registry, candidate, backlog, *, use_corpus=False, "
        "certificates_extra=())",
    "buildloop.mdl.admission_decision":
        "(live_generators, candidate, backlog) -> 'dict'",
    "library.Registry.register":
        "(self, *, name, tier, spec_language, output_language, spec_grammar, "
        "emit_entrypoint, contract, provenance, certificates=(), "
        "description_length=0.0, kind=None) -> 'str'",
    "generators.operator_growth.canonical_row": "(row: 'dict') -> 'dict'",
    "generators.math_reading._check_bigop": "(term, objects, in_bigop)",
    "generators.math_reading._check_setbuild": "(term, objects, in_bigop)",
    "generators.math_reading._check_card": "(term, objects, in_bigop)",
    "generators.operator_growth._expand_definition_to_kernel":
        "(row, registry)",
    "generators.operator_growth._run_battery":
        "(row, registry, bound, max_instances)",
    "generators.operator_growth._pricing_decision":
        "(row, registry, pricing_corpus)",
    "generators.operator_growth.save_admitted":
        "(entry: 'dict', op_dir=None, *, pricing_corpus=None, bound=4, "
        "max_instances=24) -> 'str'",
    "buildloop.mdl_macros.macro_admission_decision":
        "(readings: 'list', candidate: 'dict', macro_table: 'dict' = None, "
        "*, witness_filter=None, canon: 'bool' = True) -> 'dict'",
    "tools.proof_mine.mine": "(programs, *, top_k=10)",
    "tools.proof_mine.certify_rewrite":
        "(programs, candidate_sexpr: 'str', *, name='A0', "
        "cache: 'dict | None' = None) -> 'dict'",
    "tools.proof_mine.rank_for_verification": "(candidates)",
    "tools.proof_mine.update_ledger":
        "(mined: 'dict', programs, path: 'str') -> 'dict'",
}

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
        "teeth": [["milestones.py", "mutate"]],
    },
    "operator-words": {
        "row": "generators.operator_growth.canonical_row",
        "conserve": "generators.operator_growth._expand_definition_to_kernel",
        "battery": "generators.operator_growth._run_battery",
        "price": "generators.operator_growth._pricing_decision",
        "witnesses": "(two exogenous witnesses inside _pricing_decision)",
        "persist": "generators.operator_growth.save_admitted",
        "teeth": [["tests/test_operator_growth.py",
                   "test_multiple_of_is_grandfathered"],
                  ["tests/test_operator_symbolic.py",
                   "test_planted_universal_unsat_refuses"]],
    },
    "reading-macros": {
        "row": "buildloop.mdl_macros.macro_admission_decision",
        "conserve": "(reference-lowering translation-cert per use, H58)",
        "battery": "buildloop.mdl_macros.macro_admission_decision",
        "price": "buildloop.mdl_macros.macro_admission_decision",
        "witnesses": "(Z-E: exogenous witnesses only; dreams never decide)",
        "persist": "(registry macro table, expansion_context in cache ids)",
        "teeth": [["tests/test_witness_filter.py",
                   "test_dream_only_pattern_mined_but_refused"]],
    },
    # Registered by the completeness canary's FIRST run: this grower was
    # absent from the map's first draft -- the staleness failure mode, caught
    # by the tooth built to catch it.
    "canonicalization-rungs": {
        "row": "buildloop.rung_registry.canonical_row",
        "conserve": "(rung-free pin: empty registry => canon is identity)",
        "battery": "buildloop.rung_registry.admit_rung",
        "price": "(argued-safe syntactic class + adversarial battery)",
        "witnesses": "(proposed/ staging; only the battery admits)",
        "persist": "buildloop.rung_registry.save_admitted",
        "teeth": [["tests/test_rung.py", "refus"]],
    },
    "proof-abstractions": {
        "row": "tools.proof_mine.mine",
        "conserve": "tools.proof_mine.certify_rewrite",
        "battery": "(Lean typecheck + corpus recompile: the cold-loop batch)",
        "price": "(holdout transfer x DL descent; rank_for_verification)",
        "witnesses": "tools.proof_mine.rank_for_verification",
        "persist": "tools.proof_mine.update_ledger",
        "teeth": [["tests/test_smt_proof_probe.py",
                   "test_certify_rewrite_unused_candidate_refuses"],
                  ["tests/test_smt_proof_probe.py",
                   "test_certify_rewrite_roundtrip_and_collision"]],
    },
    # PLAN_FRAGMENT §4 P1: the bounded big-operator node CLASS
    # (bigsum/bigprod).  NOT a mint path -- a one-time STRUCTURAL purchase,
    # frozen in the grammar by code change through the full admission bill;
    # there is no runtime admitter and nothing autonomous grows here.  The
    # row is registered so the map stays complete (a structural extension
    # that bypassed the registry would be exactly the staleness the canary
    # exists to catch) and so its batteries are indexed as teeth.
    "bigop-node-class": {
        "row": "generators.math_reading._check_bigop",
        "conserve": "(four-translation agreement: gate / math_eval / "
                    "math_smt unroll / math_compile Finset -- T4 mirror "
                    "discipline, index scoped identically in every walker)",
        "battery": "(differential value + symbolic batteries over planted "
                   "closed forms, dual-solver: tests/test_bigop_battery.py)",
        "price": "(census-priced: sequences-sums, PLAN_FRAGMENT §4 P1; "
                 "the §2 re-census delta is the purchase's receipt)",
        "witnesses": "(literal bounds only -- symbolic bound / nesting are "
                     "first-class FragmentMisses, demand data for the next "
                     "purchase, never silent widenings)",
        "persist": "(frozen in generators.math_reading._BIGOPS; grows only "
                   "by a new purchase through the same bill)",
        "teeth": [["tests/test_bigop_battery.py",
                   "test_lossy_lowering_gets_no_certificate"],
                  ["tests/test_bigop_battery.py",
                   "test_symbolic_bound_is_a_fragment_miss"]],
    },
    # PLAN_FRAGMENT §4 P2: the bounded Finset carrier + cardinality node CLASS
    # (setbuild/card).  Like bigop-node-class, this is NOT a mint path -- a
    # one-time STRUCTURAL purchase riding P1's binding machinery, frozen in the
    # grammar by code change through the full admission bill; no runtime
    # admitter and nothing autonomous grows here.  Registered so the map stays
    # complete and its batteries are indexed as teeth.
    "finset-card-node-class": {
        "row": "generators.math_reading._check_card",
        "conserve": "(four-translation agreement: gate / math_eval count / "
                    "math_smt indicator-sum unroll / math_compile "
                    "Finset.card+filter -- T4 mirror discipline, the set index "
                    "scoped identically in every walker, riding P1's literal-"
                    "bound machinery)",
        "battery": "(differential value + symbolic batteries over planted "
                   "cards, dual-solver: tests/test_finset_battery.py)",
        "price": "(census-priced: sets-cardinality, PLAN_FRAGMENT §4 P2; "
                 "the §2 re-census delta is the purchase's receipt)",
        "witnesses": "(literal bounds only -- a symbolic bound is "
                     "set:symbolic-bound; any binder inside a setbuild filter "
                     "is set:nested; an object-dependent filter is the named "
                     "reflect skip card:object-filter, demand data for the "
                     "next purchase, never silent widenings)",
        "persist": "(frozen in generators.math_reading._SETOPS; grows only "
                   "by a new purchase through the same bill)",
        "teeth": [["tests/test_finset_battery.py",
                   "test_lossy_filter_gets_no_certificate"],
                  ["tests/test_finset_battery.py",
                   "test_symbolic_bound_is_a_fragment_miss"]],
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


def _normalize_sig(s: str) -> str:
    return " ".join(s.split())


def conformance(grower_name: str, *, root=None) -> dict:
    """Every role present, resolvable, signature-pinned, and toothed.

    Three tooth grades beyond existence (the upgrade over v0's pure
    referential integrity):
      * SIGNATURE PINS -- every dotted name with a pin in SIGNATURE_PINS
        must match the live ``inspect.signature`` (whitespace-normalized);
        interface drift without a registry update raises;
      * TEETH INDEX -- the ``teeth`` role lists (path, needle) pairs naming
        the grower's planted-violation coverage; each file must exist and
        contain its needle, so deleting a grower's behavioral teeth fails
        conformance here even if the grower's own suite forgets;
      * prose entries remain labeled 'discipline' -- but every grower's
        BEHAVIORAL guarantees must be reachable through its teeth, which is
        where prose cells get their falsifiability.
    Raises on any violation; returns {role: kind}."""
    import inspect
    import os
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = GROWERS[grower_name]
    out = {}
    for role in ROLES:
        if role not in spec:
            raise KeyError(f"{grower_name}: role {role!r} unfilled")
        if role == "teeth":
            entries = spec[role]
            if not entries:
                raise ValueError(f"{grower_name}: teeth role is empty -- a "
                                 f"grower without planted violations is "
                                 f"unguarded")
            for path, needle in entries:
                full = os.path.join(root, path)
                if not os.path.exists(full):
                    raise FileNotFoundError(
                        f"{grower_name}: teeth file {path} is gone")
                if needle not in open(full).read():
                    raise ValueError(
                        f"{grower_name}: planted tooth {needle!r} no longer "
                        f"in {path}")
            out[role] = "teeth"
            continue
        obj = resolve(spec[role])
        if isinstance(obj, str):
            out[role] = "discipline"
            continue
        pin = SIGNATURE_PINS.get(spec[role])
        if pin is not None:
            try:
                live = _normalize_sig(str(inspect.signature(obj)))
            except (ValueError, TypeError):
                live = "<unsignaturable>"
            if live != _normalize_sig(pin):
                raise ValueError(
                    f"{grower_name}: {spec[role]} signature drifted:\n"
                    f"  pinned {pin}\n  live   {live}\n"
                    f"(update SIGNATURE_PINS deliberately, in the same "
                    f"commit as the interface change)")
        out[role] = "code"
    return out


# Completeness canary: a module that both prices in the DL currency and
# defines an admission/persist entry point is grower-shaped; every such
# module must be registered above or allowlisted here WITH A REASON.  An
# unregistered grower is exactly how the map goes silently stale.
_GROWER_SMELL_PRICE = ("admission_decision", "price_operator",
                      "macro_admission_decision", "_leaf_count")
_GROWER_SMELL_ADMIT = ("def admit", "def save_admitted", "def update_ledger",
                       "def register(")
NON_GROWERS = {
    "buildloop/mdl.py": "the currency itself, not a grower",
    "buildloop/dl.py": "ledger arithmetic, not a grower",
    "buildloop/growth_protocol.py": "this registry",
}


def _registered_modules() -> set:
    """Module paths derived from GROWERS' dotted names -- registration IS
    accounting, so the scan never needs a parallel hand-kept list (the
    fact-2 discipline again)."""
    out = set()
    for spec in GROWERS.values():
        for role, val in spec.items():
            if role == "teeth" or not isinstance(val, str) \
                    or val.startswith("("):
                continue
            parts = val.split(".")
            for i in range(len(parts), 0, -1):
                mod = ".".join(parts[:i])
                try:
                    importlib.import_module(mod)
                except ImportError:
                    continue
                path = mod.replace(".", "/")
                out.add(path + ".py")
                out.add(path + "/__init__.py")
                break
    return out


def completeness_scan(root=None) -> dict:
    """Return {"accounted": [...], "unaccounted": [...]} over grower-shaped
    modules.  The tooth asserts unaccounted == [] -- adding a grower without
    registering it (or allowlisting it with a reason) fails CI."""
    import os
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    accounted, unaccounted = [], []
    for sub in ("buildloop", "generators", "tools"):
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".py"):
                continue
            rel = f"{sub}/{fn}"
            text = open(os.path.join(base, fn)).read()
            pricing = any(s in text for s in _GROWER_SMELL_PRICE)
            admitting = any(s in text for s in _GROWER_SMELL_ADMIT)
            if not (pricing and admitting):
                continue
            if rel in NON_GROWERS or rel in _registered_modules():
                accounted.append(rel)
            else:
                unaccounted.append(rel)
    return {"accounted": accounted, "unaccounted": unaccounted}

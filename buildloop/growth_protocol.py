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
    # P8 widened these three by one OPTIONAL parameter: the function
    # environment in scope, so a definition body and a big-operator body are
    # walked by the same checker rather than by two that drift.  Default None
    # keeps every existing call site byte-identical.
    "generators.math_reading._check_bigop":
        "(term, objects, in_bigop, definitions=None)",
    "generators.math_reading._check_setbuild":
        "(term, objects, in_bigop, definitions=None)",
    "generators.math_reading._check_card":
        "(term, objects, in_bigop, definitions=None)",
    "generators.math_reading._check_definition":
        "(lf, sid, objects, definitions, param_carrier)",
    "generators.math_reading._unfold_term": "(term, definitions)",
    "generators.math_reading._check_carrier_ops":
        "(pred, objects, ambient, sid)",
    "generators.math_reading._zmod_modulus": "(ty)",
    "generators.math_reading._check_zmod_ops": "(pred, objects, ambient, sid)",
    "generators.math_reading._check_connective_nnf":
        "(pred, sid, negated=False)",
    "generators.math_reading._dual_atom": "(pred)",
    "generators.math_reading._check_pow_exponent": "(exp, carrier, sid)",
    "generators.math_smt._term_uses_enum": "(term) -> 'bool'",
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
    # PLAN_FRAGMENT §4 P3: the RATIONAL carrier.  The first purchase in this
    # family that grows the CARRIER whitelist rather than the node grammar --
    # and so the first whose conserve argument is about what a carrier is
    # ALLOWED to do, not about what a binder unrolls to.  Like its two
    # predecessors it is NOT a mint path: a one-time purchase frozen by code
    # change through the full bill, with no runtime admitter.  Registered so
    # the map stays complete and its refusals are indexed as teeth.
    "rat-carrier": {
        "row": "generators.math_reading._check_carrier_ops",
        "conserve": "(carrier admissibility is a REFUSAL surface, not a "
                    "widening: `/` is admitted only where Lean's HDiv is "
                    "field division, the divisibility family and the "
                    "Nat-indexed binders are refused at Rat, and a Rat/integer "
                    "mix is refused outright (rat:no-coercion) -- so every "
                    "translation stays a total single-carrier function and the "
                    "Nat/Int readings are byte-unchanged)",
        "battery": "(differential value + symbolic batteries over exact "
                   "Fraction arithmetic and the totalised q/0, dual-solver "
                   "over QF_LRA/QF_NRA: tests/test_rat_battery.py -- the "
                   "battery half of the §4 P3 bill)",
        "price": "(census-priced: rational-arithmetic, PLAN_FRAGMENT §4 P3; "
                 "the §2 re-census delta is the purchase's receipt)",
        "witnesses": "(no coercion, no floor division, no remainder over a "
                     "field: every one of those is a named FragmentMiss "
                     "(`operator:/@Nat`, `operator:%@Rat`, "
                     "`operator:bigsum@Rat`) carrying demand data for the next "
                     "purchase, never a silent widening; the reflect slice's "
                     "own limit is the named skip "
                     "`carrier-out-of-reflect-slice:Rat`)",
        "persist": "(frozen in generators.math_reading.CARRIERS + "
                   "_BUILTIN_OP_CARRIERS; grows only by a new purchase "
                   "through the same bill)",
        # One tooth per HALF of the bill, which is the shape the other rows
        # use: the GATE tooth lives with the gate it guards (a refusal is
        # decided there, not in a battery), and the DIVERGENCE tooth rides the
        # battery, because that is where a lowering is caught lying.  Indexing
        # both is the point -- a grower whose teeth all sat in one file could
        # lose the other half of its coverage without conformance noticing.
        # (`test_rat_carrier_mixing_is_refused`, the rat:no-coercion gate
        # tooth, stays in tests/test_math_reading.py alongside its sibling;
        # it is covered by the battery's own `test_mixed_rat_and_integer_
        # carriers_refuse` as well, so it is not the load-bearing index here.)
        "teeth": [["tests/test_math_reading.py",
                   "test_div_outside_rat_is_a_fragment_miss"],
                  ["tests/test_rat_battery.py",
                   "test_lossy_division_gets_no_certificate"]],
    },
    # PLAN_FRAGMENT §4 P4: the parametric residue carrier `ZMod n`.  The SECOND
    # purchase on the carrier axis (P3 bought Rat), and the first anywhere here
    # to buy a FAMILY rather than a type: it is carried by a PREDICATE
    # (`_zmod_modulus`) rather than by an entry in the CARRIERS tuple, so every
    # consumer that ENUMERATES carriers -- the census aliases, the operator
    # table, the admitted-operator cert rows -- keeps its pre-P4 behaviour
    # byte-for-byte.  Like its three predecessors it is NOT a mint path: a
    # one-time structural purchase frozen in the grammar by code change through
    # the full admission bill; no runtime admitter, nothing autonomous grows.
    "zmod-carrier": {
        "row": "generators.math_reading._zmod_modulus",
        "conserve": "generators.math_reading._check_zmod_ops",
        "battery": "(differential value + symbolic batteries over planted "
                   "residue identities, dual-solver, plus the D8-class "
                   "carrier-divergence witness that makes the atom mod-wrap "
                   "load-bearing)",
        "price": "(census-priced: algebra-structures, PLAN_FRAGMENT §4 P4; "
                 "the §2 re-census delta is the purchase's receipt)",
        "witnesses": "(LITERAL moduli only -- a symbolic modulus is "
                     "carrier:zmod-symbolic-modulus and the degenerate n = 0 "
                     "is carrier:zmod-zero-modulus; the order atoms and the "
                     "mod/divisibility family at a residue carrier are "
                     "operator:<op>@ZMod <n>; a binder inside a residue "
                     "reading is zmod:binder-index-carrier -- demand data for "
                     "the next purchase, never silent widenings)",
        "persist": "(frozen in generators.math_reading._zmod_modulus's "
                   "literal-modulus pattern; grows only by a new purchase "
                   "through the same bill)",
        # One tooth per HALF of the bill, the shape every row above uses: the
        # GATE tooth lives with the gate it guards (the modulus freeze is
        # decided at the reading, not in a battery), and the DIVERGENCE tooth
        # rides the battery, because that is where a lowering is caught lying.
        "teeth": [["tests/test_math_reading.py",
                   "test_symbolic_modulus_is_a_fragment_miss"],
                  ["tests/test_zmod_battery.py",
                   "test_lossy_mod_drop_gets_no_certificate"]],
    },
    # PLAN_FRAGMENT §4 P6: the propositional connectives `not` and `iff`.  The
    # first purchase on the CONNECTIVE axis, the first priced by MEASURED
    # REFUSALS rather than by census vocabulary, and the first whose bill came
    # in SMALLER than the queue declared: §4 P6 declared tower-class against
    # the possibility that negation needs a `Pd` constructor, and the
    # measurement says it does not -- `iff` is desugaring and `not` is
    # negation-normal form, so nothing enters `Tm`/`Pd` and no `Decidable`
    # instance is written.  Additive-class under §3.1 rule 3, measured rather
    # than assumed, and the declared-larger bill is what kept the smaller one
    # from being claimed before it was shown.  Like every row above it is NOT a
    # mint path: a one-time purchase frozen by code change through the full
    # bill, with no runtime admitter.
    "connective-node-class": {
        "row": "generators.math_reading._check_connective_nnf",
        "conserve": "generators.math_reading._dual_atom",
        "battery": "(differential truth-table + symbolic batteries over "
                   "planted connective rows, dual-solver, plus the involution "
                   "and desugaring identities that say the two new words add "
                   "no new meaning: tests/test_connective_battery.py)",
        "price": "(REFUSAL-priced, not census-priced -- PLAN_FRAGMENT §4 P6's "
                 "measured groups not-connective / iff-connective / "
                 "definition-biconditional; the receipt is the refusal "
                 "retirement the NEXT corpus cycle realizes through "
                 "intake_from_frontier --unblocked, and the §2 re-census "
                 "delta for this row is honestly ZERO)",
        "witnesses": "(the negations NNF cannot push are named, not widened: "
                     "`dvd` and `coprime` carry no dual in the fragment, so a "
                     "negation reaching one is `not:<op>-no-dual` -- demand "
                     "data for the negation-constructor purchase §4 P6 "
                     "declared and this one deliberately did not make; the "
                     "reflect slice's own quoting rides a later commit and "
                     "keeps its existing fail-closed "
                     "`op-out-of-reflect-slice:` skip until it does)",
        "persist": "(frozen in generators.math_reading._CONNECTIVES + "
                   "_CONNECTIVE_ARITY + _ATOM_DUALS; grows only by a new "
                   "purchase through the same bill)",
        # One tooth per HALF of the bill, the shape every row above uses: the
        # GATE tooth lives with the gate it guards (whether a negation can be
        # pushed is decided at the reading, not in a battery), and the
        # DIVERGENCE tooth rides the battery, because that is where a lowering
        # is caught lying.
        "teeth": [["tests/test_math_reading.py",
                   "test_negated_dvd_is_a_fragment_miss"],
                  ["tests/test_connective_battery.py",
                   "test_lossy_demorgan_flip_gets_no_certificate"]],
    },
    "pow-symbolic-exponent": {
        "row": "generators.math_reading._check_pow_exponent",
        # What CONSERVES here is not a rewrite that preserves meaning (P6's
        # `_dual_atom`) but a ROUTER that keeps an unrenderable node off the
        # solver.  A symbolic exponent has no SMT-LIB rendering at all -- no
        # exponentiation in the theory, and the k-fold unroll needs a k -- so
        # the soundness-preserving act is to route the reading to enumeration
        # instead of approximating it.  This is the first enum-only route keyed
        # to a node SHAPE rather than to an operator WORD, which is why it is
        # named here rather than left implicit in `_ENUM_ONLY`.
        "conserve": "generators.math_smt._term_uses_enum",
        "battery": "(instantiation differential over a base x width box -- the "
                   "reference for `a ^ n` at n = k is the fragment's OWN "
                   "literal-exponent term `a ^ k` through the same evaluator, "
                   "never a Python re-implementation -- plus the byte-unchanged "
                   "literal path at all four consumers, the truncated-exponent "
                   "divergence tooth, the carrier fence in BOTH directions and "
                   "the Int.toNat/max(e,0) mirror: "
                   "tests/test_pow_battery.py.  NOTE the b2-analogue symbolic "
                   "battery is ABSENT and recorded as absent: there is no SMT "
                   "rendering to run a dual-solver differential against, which "
                   "is a real reduction in corroboration for this row alone)",
        "price": "(REFUSAL-priced, not census-priced -- PLAN_FRAGMENT §4 P7's "
                 "measured `refused:symbolic-exponent` group, 12 subject-rows, "
                 "and P1's own receipt results/p1_delta.md, which named this "
                 "successor when it recorded P1's zero re-census delta; the "
                 "receipt is the refusal retirement a LATER corpus cycle "
                 "realizes through intake_from_frontier --unblocked, and the "
                 "§2 re-census delta for this row is honestly ZERO)",
        "witnesses": "(the limits are named, not widened.  P7 buys the TERM "
                     "CONSTRUCTOR and the enumeration route; it does NOT buy "
                     "the discharge -- enumeration is exhaustive over a box and "
                     "is not a proof of `for all n`, the reflect slice's "
                     "box-lift lemmas still meet a universal with `nomatch "
                     "hex`, and the missing ingredient is an INDUCTION "
                     "principle the slice does not have.  The residual demand "
                     "is `pow:symbolic-exponent@Int`: an exponent that may be "
                     "negative is still outside the integer carriers, which is "
                     "measured rather than argued -- Lean itself refuses `HPow "
                     "Int Int` to synthesize)",
        "persist": "(frozen in generators.math_reading._check_pow_exponent's "
                   "carrier rule, the FgReflect `Tm.pow` constructor and the "
                   "six walker cases over it; grows only by a new purchase "
                   "through the same bill)",
        # One tooth per HALF of the bill, the shape every row above uses: the
        # GATE tooth lives with the gate it guards (which carriers admit a
        # symbolic exponent is decided at the reading), and the DIVERGENCE
        # tooth rides the battery, because truncating an exponent to a literal
        # width is where this row would be caught lying.
        "teeth": [["tests/test_symbolic_exponent_demand.py",
                   "test_a_symbolic_exponent_at_carrier_Nat_is_no_longer_demand"],
                  ["tests/test_pow_battery.py",
                   "test_truncating_a_symbolic_exponent_gets_no_certificate"]],
    },
    "funcdef-definitional-extension": {
        "row": "generators.math_reading._check_definition",
        # What CONSERVES here is an ELIMINATION, the same shape as P6's
        # `_dual_atom` and for the same reason: the new vocabulary is defined
        # away rather than represented.  `_unfold_term` rewrites every
        # application to the body it names, so the reading that reaches the
        # evaluator, the SMT mirror, the Lean emitter and the reflect slice
        # contains no application at all.  That is what conservativity MEANS
        # for a definitional extension, and it is executable rather than
        # argued.
        "conserve": "generators.math_reading._unfold_term",
        "battery": "(differential + symbolic batteries over planted "
                   "definition rows, dual-solver: every admitted reading is "
                   "measured against its HAND-UNFOLDED twin at all four "
                   "consumers -- same eval verdict on a box, same SMT verdict "
                   "from both solvers, byte-identical Lean text and "
                   "statement_hash -- plus the substitution-capture and "
                   "wrong-body divergence teeth: "
                   "tests/test_funcdef_battery.py)",
        "price": "(REFUSAL-priced, not census-priced -- PLAN_FRAGMENT §4 P8's "
                 "measured `refused:function-symbol` group, 11 subject-rows; "
                 "the receipt is the refusal retirement the NEXT corpus cycle "
                 "realizes through intake_from_frontier --unblocked, and it "
                 "is honestly expected to be SMALL: "
                 "tests/test_function_symbol_class.py measured the row's "
                 "ceiling at five subjects, and this bill buys the "
                 "NON-RECURSIVE half of the mechanism, so the recurrence "
                 "subjects stay held by funcdef:recursive-body)",
        "witnesses": "(the three freezes are named, not widened, and each is "
                     "first-class demand: `funcdef:recursive-body` (a body "
                     "may not apply itself or a later definition -- the "
                     "recurrence demand this row prices and deliberately does "
                     "NOT buy, since a symbolic index has no finite "
                     "unfolding), `funcdef:binder-body` (no bigop/set binder "
                     "in a body, which is what makes the use-site "
                     "substitution capture-free BY CONSTRUCTION rather than "
                     "by argument) and `funcdef:open-body` (a body mentions "
                     "its parameters only, never a declared object).  The "
                     "reflect slice takes NO new constructor and NO new "
                     "Decidable story: tests/test_function_symbol_class.py "
                     "finding (4) priced both against an UNINTERPRETED "
                     "symbol, and a symbol with an explicit body is "
                     "eliminable instead -- so `Tm`/`Pd` are byte-unchanged "
                     "and PLAN_FRAGMENT §3.1 rule 3(a) is not reached)",
        "persist": "(frozen in generators.math_reading.MATH_LF_KINDS's "
                   "`definition` entry, its _MLF_FIELDS/_MLF_FORCES rows and "
                   "the `app` branch of _check_term; grows only by a new "
                   "purchase through the same bill)",
        # One tooth per HALF of the bill, the shape every row above uses: the
        # GATE tooth lives with the gate it guards (whether a body may recur
        # is decided at the reading), and the DIVERGENCE tooth rides the
        # battery, because substituting the WRONG body is where an
        # elimination is caught lying.
        "teeth": [["tests/test_math_reading.py",
                   "test_a_recursive_definition_body_is_a_fragment_miss"],
                  ["tests/test_funcdef_battery.py",
                   "test_unfolding_a_wrong_body_gets_no_certificate"]],
    },
}

# Planned growers, registered as intentions so the map stays complete; their
# rows flip to dotted names as the code lands.
PLANNED = {
    # The generic "carriers" intention RETIRED with P3 and P4: both carrier
    # growers now have real rows above (`rat-carrier`, `zmod-carrier`), so an
    # intention naming either would double-count it.  What stays planned is the
    # REST of the axis -- ordered / field / abstract typeclass carriers -- still
    # L1-anchored and census-priced, and still unpurchased.
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

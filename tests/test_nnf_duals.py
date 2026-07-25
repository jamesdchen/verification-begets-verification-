"""NEGATION-NORMAL FORM over the CURRENT fragment semantics: is `not` additive?

THE QUESTION THIS FILE ANSWERS MECHANICALLY.  PLAN_FRAGMENT §4 P6 (the
connectives row of `tools/purchase_frontier.py`) declares a DESIGN QUESTION it
refuses to settle by preference: a `not` CONSTRUCTOR in `Pd` is tower-class
under §3.1 rule 3(a) -- every certified walker over the type must then answer
it -- but negation may need no constructor at all, because it can be PUSHED TO
ATOMS at quote time, and `iff` unfolds to the `and` of two `implies`.  Which
bill the purchase really is, is a FACT ABOUT THE SLICE, and §4 says the answer
decides attended vs unattended rather than the other way round.  So it is
measured here, before the re-declaration that rests on it, and the queue row
cites this file BY NAME (the growth-protocol teeth-needle idiom) so the class
claim and its proof cannot drift apart.

WHAT COUNTS AS A PROOF HERE (and why it is not a second opinion).  The dual
rules are asserted against `generators/math_eval.eval_pred` -- the fragment's
OWN evaluator, the third translation of the one grammar (F2.1/F2.2) -- and
never against a re-implementation of the semantics.  A re-implementation would
only show that two statements of one belief agree; the evaluator is the thing
the gates actually run, so agreement with IT is evidence about the fragment.
Concretely: for a pred `p` and its pushed form `push_not(p)`, we require

    eval_pred(push_not(p), x)  ==  not eval_pred(p, x)      at EVERY x in a box,

which is pointwise semantic negation with the negation taken in PYTHON, on the
evaluator's own answer.  Exhaustive over the box, deterministic (no clocks, no
randomness, no solver), Lean-free and network-free.

THE BOXES.  Every carrier the reading grammar admits, each swept whole:
`Int` and `Nat` (the two layers `tools/FgReflect.lean` proves), `Rat` on the
Farey grid `math_eval.rat_values` (a DENSE order -- the one box where an
"off-by-one" reading of `not (a <= b)` would survive an integer sweep and die
here), and `ZMod n`, where `=`/`!=` reduce at the ATOM and a dual has to
survive that reduction.  Atom shapes are enumerated over a term pool per box,
so both argument orders of every binary atom are covered by construction.

THE MEASURED RESIDUE, reported rather than tidied.  Two atoms have no dual
among the atoms over their OWN arguments: `dvd` and `coprime`.  That is the
narrow control, and it is what makes a named `not:negated-dvd` skip honest
rather than lazy.  But the wider reading is the finding this file exists to
publish: `not dvd(a, b)` IS pointwise equal to `b % a != 0` over every box --
Lean's totalisations line up exactly (`x % 0 = x` and `0 | b <-> b = 0`, D9/
D13), so the equivalence needs no side condition -- and `%` is `Tm.tmod`,
already IN the reflect slice.  So the skip is CONSERVATIVE, not forced.
`coprime`'s dual `gcd(a, b) != 1` is the same shape one step out of reach:
`gcd` is not a `Tm` constructor, so that atom keeps its existing
`op-out-of-reflect-slice` skip whatever negation does.  Neither residue
touches the class question -- no constructor is added on either route -- which
is precisely why the class can be re-declared on this evidence.
"""
import itertools
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.math_eval import eval_pred, rat_values  # noqa: E402
from generators.math_reading import (  # noqa: E402
    _BUILTIN_ATOM_OPS, _CONNECTIVES, MATH_OPERATORS)


# --------------------------------------------------------------------------- #
# The claim, written ONCE, as a rewrite on the pred AST.
#
# This IS the quote-time encoding the connectives purchase would ship: `not`
# never becomes a node, it is pushed through the connectives by De Morgan and
# lands on an atom's dual.  `iff` is one level up and never becomes a node
# either.  An atom with no dual raises rather than guessing -- a fail-CLOSED
# residue is the shape §3.1 rule 3(e) asks of a carrier check, and the same
# discipline applies to an atom the encoding cannot reach.
# --------------------------------------------------------------------------- #
class NoDual(Exception):
    """An atom the push cannot reach: it becomes a NAMED skip, never a
    widening and never a silent pass-through."""


def push_not(pred: dict) -> dict:
    """The negation of `pred`, in negation-normal form over the EXISTING
    grammar: no new node kind, no new constructor, nothing but atoms the
    fragment already has.

    The atom duals: `=`/`!=`; `<=`/`<` WITH THE ARGUMENTS SWAPPED (a total
    order, so `not (a <= b)` is `b < a` -- the swap is the whole content of
    the rule and forgetting it is the planted violation below); `even`/`odd`.
    The connectives: De Morgan for `and`/`or` (n-ary, exactly as the
    evaluator folds them), and `not (p -> q)` = `p and not q`."""
    op = pred["op"]
    args = pred["args"]
    if op == "=":
        return {"op": "!=", "args": args}
    if op == "!=":
        return {"op": "=", "args": args}
    if op == "<=":
        return {"op": "<", "args": [args[1], args[0]]}
    if op == "<":
        return {"op": "<=", "args": [args[1], args[0]]}
    if op == "even":
        return {"op": "odd", "args": args}
    if op == "odd":
        return {"op": "even", "args": args}
    if op == "and":
        return {"op": "or", "args": [push_not(a) for a in args]}
    if op == "or":
        return {"op": "and", "args": [push_not(a) for a in args]}
    if op == "implies":                      # not (p -> q) == p and not q
        return {"op": "and", "args": [args[0], push_not(args[1])]}
    raise NoDual(op)


#: The atoms the push cannot reach, each with the ENCODING that would reach it
#: and the reason the encoding is or is not inside the reflect slice.  A
#: residue that names no way out is an indefinite hold, which house law
#: forbids -- so each names one.
NO_DUAL_ATOMS = {
    "dvd": "b % a != 0 -- an existing Pd atom over an existing Tm term "
           "(Tm.tmod), so the named skip is CONSERVATIVE, not forced",
    "coprime": "gcd(a, b) != 1 -- an existing atom over a term `gcd` that is "
               "NOT a Tm constructor, so this atom keeps its existing "
               "op-out-of-reflect-slice skip whatever negation does",
}


def desugar_iff(p: dict, q: dict) -> dict:
    """`p <-> q` on the existing grammar: the `and` of two `implies`.  No node
    is added, which is the whole of the `iff` half of the class question."""
    return {"op": "and", "args": [{"op": "implies", "args": [p, q]},
                                  {"op": "implies", "args": [q, p]}]}


# --------------------------------------------------------------------------- #
# The boxes.  Each is a carrier assignment plus the EXACT value set swept per
# object -- exhaustive, so "at every point" means what it says.
# --------------------------------------------------------------------------- #
def _ref(n):
    return {"ref": n}


def _lit(k):
    return {"lit": k}


def _t(op, *args):
    return {"op": op, "args": list(args)}


A, B, C = _ref("a"), _ref("b"), _ref("c")

#: Integer term pool: the atom's own arguments, small literals, and one term
#: per builtin arithmetic op in BOTH orders where the op is not commutative
#: (`-` truncates at Nat, D8, so the two orders are genuinely two terms).
_INT_POOL = {
    "a": A, "b": B, "0": _lit(0), "1": _lit(1), "2": _lit(2),
    "a+b": _t("+", A, B), "a-b": _t("-", A, B), "b-a": _t("-", B, A),
    "a*b": _t("*", A, B), "a%b": _t("%", A, B), "b%a": _t("%", B, A),
}
#: Rat drops the whole divisibility family (`%` refuses at Rat) and ZMod is an
#: unordered ring whose admissible atoms are `=`/`!=` only (math_reading's v1
#: freeze), so each box carries the pool its gate would actually admit.
_FIELD_POOL = {
    "a": A, "b": B, "0": _lit(0), "1": _lit(1), "2": _lit(2),
    "a+b": _t("+", A, B), "a-b": _t("-", A, B), "a*b": _t("*", A, B),
}

#: `(carrier_of, values, dualable binary atoms, unary atoms)`.  The Rat grid is
#: taken at bound 4 -- nine values, dense enough that no integer-lattice
#: shortcut survives it, small enough that the sweep stays a second.
BOXES = {
    "Int": ({"a": "Int", "b": "Int"}, {"a": range(-4, 5), "b": range(-4, 5)},
            _INT_POOL, ("=", "!=", "<=", "<"), ("even", "odd")),
    "Nat": ({"a": "Nat", "b": "Nat"}, {"a": range(0, 7), "b": range(0, 7)},
            _INT_POOL, ("=", "!=", "<=", "<"), ("even", "odd")),
    "Rat": ({"a": "Rat", "b": "Rat"},
            {"a": rat_values(4), "b": rat_values(4)},
            _FIELD_POOL, ("=", "!=", "<=", "<"), ()),
    "ZMod 5": ({"a": "ZMod 5", "b": "ZMod 5"},
               {"a": range(0, 5), "b": range(0, 5)},
               _FIELD_POOL, ("=", "!="), ()),
}

#: The connective sweep needs a third object so `and`/`or`/`implies` combine
#: preds that are not about the same two values.  Integer carriers only: the
#: connectives are carrier-blind (the evaluator folds them before any term is
#: touched), and the atom sweep above is where the carriers earn their keep.
CONN_BOXES = {
    "Int": ({"a": "Int", "b": "Int", "c": "Int"},
            {n: range(-3, 4) for n in "abc"}),
    "Nat": ({"a": "Nat", "b": "Nat", "c": "Nat"},
            {n: range(0, 5) for n in "abc"}),
}

#: Base atoms for the connective sweep -- one per dualable atom shape, chosen
#: so that no two are the same predicate under a different name.
_BASE_ATOMS = (
    _t("=", A, B), _t("!=", _t("+", A, C), B), _t("<=", A, B),
    _t("<", B, C), _t("even", _t("*", A, B)), _t("odd", C),
)


def _points(values):
    """Every assignment over the box, in a fixed order (sorted names, product
    in the declared value order): deterministic by construction."""
    names = sorted(values)
    for combo in itertools.product(*(values[n] for n in names)):
        yield dict(zip(names, combo))


def _truth(pred, carrier_of, values):
    """The pred's truth TABLE over the whole box, from the fragment's own
    evaluator.  Tables are what the controls below compare -- semantic
    equivalence over a box is exactly table equality."""
    return tuple(eval_pred(pred, x, carrier_of, None) for x in _points(values))


def _assert_dual(pred, carrier_of, values, label):
    """`push_not(pred)` is pointwise the negation of `pred` over the box."""
    pushed = push_not(pred)
    for x in _points(values):
        got = eval_pred(pushed, x, carrier_of, None)
        want = not eval_pred(pred, x, carrier_of, None)
        assert got == want, (
            f"{label}: the pushed form disagrees with semantic negation at "
            f"{x} (pushed says {got}, `not` says {want})")


def _atom_shapes(pool, binary_ops, unary_ops):
    """Every atom over the pool: binary ops over the ORDERED product (so both
    argument orders are swept, which is the whole content of the `<=`/`<`
    rule), unary ops over each term."""
    for op in binary_ops:
        for x, y in itertools.product(sorted(pool), repeat=2):
            yield f"{op}({x},{y})", _t(op, pool[x], pool[y])
    for op in unary_ops:
        for x in sorted(pool):
            yield f"{op}({x})", _t(op, pool[x])


# ------------------------------------------------------------- the headline
def test_every_pd_atom_and_connective_has_a_pointwise_dual():
    """THE CLAIM, exhaustively: over every carrier the grammar admits, every
    atom shape the box's gate would accept has a dual in the EXISTING
    vocabulary that is pointwise the semantic negation -- no new `Pd`
    constructor anywhere in the answer.

    This is the test the queue row cites by name; the focused teeth below say
    the same thing shape by shape so a failure names its shape."""
    swept = 0
    for name, (carrier_of, values, pool, binops, unops) in BOXES.items():
        for label, atom in _atom_shapes(pool, binops, unops):
            _assert_dual(atom, carrier_of, values, f"{name}: {label}")
            swept += 1
    assert swept > 800, f"the atom sweep collapsed to {swept} shapes"


def test_peq_and_pne_are_duals_including_under_the_residue_reduction():
    """`=`/`!=` -- and the ZMod box is not decoration: the residue atom
    reduces BOTH sides `% n` at the atom (P4, the one node where the quotient
    is observable), so a dual has to survive that reduction rather than the
    raw integer comparison."""
    for name in ("Int", "Nat", "Rat", "ZMod 5"):
        carrier_of, values, pool, _binops, _unops = BOXES[name]
        for x, y in itertools.product(sorted(pool), repeat=2):
            for op in ("=", "!="):
                _assert_dual(_t(op, pool[x], pool[y]), carrier_of, values,
                             f"{name}: {op}({x},{y})")


def test_ple_and_plt_are_duals_in_BOTH_argument_orders():
    """`not (a <= b)` is `b < a` and `not (a < b)` is `b <= a`: the SWAP is
    the rule's whole content.  Swept in both orders over the pool, and over
    the DENSE Rat grid as well as the integer lattices -- a rule that quietly
    assumed a successor (`b <= a - 1`) passes an integer box and dies on the
    rationals."""
    for name in ("Int", "Nat", "Rat"):
        carrier_of, values, pool, _binops, _unops = BOXES[name]
        for x, y in itertools.product(sorted(pool), repeat=2):
            for op in ("<=", "<"):
                _assert_dual(_t(op, pool[x], pool[y]), carrier_of, values,
                             f"{name}: {op}({x},{y})")


def test_peven_and_podd_are_duals():
    """`even`/`odd` by `n % 2`, on both integer layers -- including negative
    values, where the parity of `-3` has to come out odd for the pair to be a
    partition rather than a coincidence about non-negatives."""
    for name in ("Int", "Nat"):
        carrier_of, values, pool, _binops, _unops = BOXES[name]
        for x in sorted(pool):
            for op in ("even", "odd"):
                _assert_dual(_t(op, pool[x]), carrier_of, values,
                             f"{name}: {op}({x})")


def test_de_morgan_and_implication_over_every_binary_combination():
    """`and`/`or`/`implies` at depth 1: every ordered pair of base atoms under
    every connective, pushed and compared pointwise."""
    swept = 0
    for name, (carrier_of, values) in CONN_BOXES.items():
        for p, q in itertools.product(_BASE_ATOMS, repeat=2):
            for conn in sorted(_CONNECTIVES):
                _assert_dual(_t(conn, p, q), carrier_of, values,
                             f"{name}: {conn}")
                swept += 1
    assert swept == 2 * len(_BASE_ATOMS) ** 2 * len(_CONNECTIVES)


def test_de_morgan_survives_nesting_and_the_n_ary_fold():
    """Depth 2, plus the n-ary shape: the evaluator folds `and`/`or` with
    `all`/`any` over an argument LIST, so the push has to be n-ary too.  A
    binary-only De Morgan would pass every test above and drop arguments
    here."""
    for name, (carrier_of, values) in CONN_BOXES.items():
        p, q, r = _BASE_ATOMS[0], _BASE_ATOMS[2], _BASE_ATOMS[3]
        nested = [
            _t("and", _t("or", p, q), _t("implies", q, r)),
            _t("or", _t("and", p, q), _t("and", q, r)),
            _t("implies", _t("and", p, q), _t("or", q, r)),
            _t("and", p, q, r),                      # n-ary
            _t("or", p, q, r),                       # n-ary
            _t("implies", _t("or", p, q, r), _t("and", p, q, r)),
        ]
        for i, pred in enumerate(nested):
            _assert_dual(pred, carrier_of, values, f"{name}: nested[{i}]")


def test_double_negation_returns_the_original_meaning():
    """`push_not(push_not(p))` denotes `p` -- pointwise, not syntactically.
    The pushed-twice form is a DIFFERENT AST (the `<=`/`<` swap goes out and
    comes back), so this is a semantic identity and the only honest way to
    state it is over the box."""
    subjects = list(_BASE_ATOMS) + [
        _t("and", _BASE_ATOMS[0], _BASE_ATOMS[2]),
        _t("or", _BASE_ATOMS[1], _BASE_ATOMS[3]),
        _t("implies", _BASE_ATOMS[2], _BASE_ATOMS[4]),
        _t("implies", _t("and", _BASE_ATOMS[0], _BASE_ATOMS[3]),
           _BASE_ATOMS[5]),
    ]
    for name, (carrier_of, values) in CONN_BOXES.items():
        for i, pred in enumerate(subjects):
            twice = push_not(push_not(pred))
            for x in _points(values):
                assert eval_pred(twice, x, carrier_of, None) == \
                    eval_pred(pred, x, carrier_of, None), \
                    f"{name}: double negation moved the meaning of subject {i}"


# --------------------------------------------------------------- the `iff`
def test_iff_desugars_to_the_and_of_two_implications_pointwise():
    """The other half of the class question.  `p <-> q` read as
    `(p -> q) and (q -> p)` is ADDITIVE -- it is the existing grammar,
    verbatim -- and this asserts it MEANS the biconditional at every point:
    the desugaring agrees with `eval(p) == eval(q)`, which is the
    biconditional taken in Python on the evaluator's own answers."""
    for name, (carrier_of, values) in CONN_BOXES.items():
        for p, q in itertools.product(_BASE_ATOMS, repeat=2):
            desugared = desugar_iff(p, q)
            for x in _points(values):
                want = (eval_pred(p, x, carrier_of, None)
                        == eval_pred(q, x, carrier_of, None))
                assert eval_pred(desugared, x, carrier_of, None) == want, \
                    f"{name}: the iff desugaring is not the biconditional"


def test_negated_iff_pushes_through_the_desugaring():
    """...and a NEGATED biconditional needs no separate rule: pushing `not`
    through the desugared form already lands in the existing grammar, and it
    means exclusive-or, pointwise."""
    for name, (carrier_of, values) in CONN_BOXES.items():
        for p, q in itertools.product(_BASE_ATOMS, repeat=2):
            pushed = push_not(desugar_iff(p, q))
            for x in _points(values):
                want = (eval_pred(p, x, carrier_of, None)
                        != eval_pred(q, x, carrier_of, None))
                assert eval_pred(pushed, x, carrier_of, None) == want, \
                    f"{name}: the negated iff is not exclusive-or"


# ------------------------------------------------------ the pdvd controls
def test_the_push_refuses_the_residue_atoms_by_name():
    """Fail-CLOSED, and by name.  `dvd` and `coprime` raise rather than
    falling through to some nearest-looking atom; a push that guessed would
    be the silent widening §3.1 rule 3(e) exists to forbid."""
    for op in NO_DUAL_ATOMS:
        with pytest.raises(NoDual) as exc:
            push_not(_t(op, A, B))
        assert op in str(exc.value)


def test_pdvd_has_no_dual_among_the_atoms_over_its_own_arguments():
    """THE NEGATIVE CONTROL that makes the named skip necessary rather than
    lazy: over the atom's OWN arguments and small literals, NO atom the
    fragment has -- in either argument order, on either integer layer --
    has the truth table of `not dvd(a, b)`.  So the dual really is absent
    where the other atoms find theirs, and a skip is not a failure of
    searching.  (`coprime` measured the same way, on its own carrier.)"""
    narrow = {k: _INT_POOL[k] for k in ("a", "b", "0", "1", "2")}
    for name in ("Int", "Nat"):
        carrier_of, values, _pool, binops, unops = BOXES[name]
        for op in ("dvd",) + (("coprime",) if name == "Nat" else ()):
            target = tuple(not v for v in
                           _truth(_t(op, A, B), carrier_of, values))
            hits = [lbl for lbl, atom in _atom_shapes(
                narrow, binops + ("dvd",), unops)
                if _truth(atom, carrier_of, values) == target]
            assert hits == [], \
                f"{name}: {op} DOES have a same-argument dual: {hits}"


def test_negated_dvd_is_reachable_through_tmod_so_the_skip_is_conservative():
    """THE FINDING, published rather than tidied away.

    `not dvd(a, b)` IS pointwise `b % a != 0` -- on both integer layers, over
    the whole box, with no side condition, because the two totalisations line
    up exactly: Lean reads `0 | b <-> b = 0` and `x % 0 = x` (D9/D13), and
    `b % 0 = b`, so the `a = 0` column agrees with the rest instead of being
    an exception.  `%` is `Tm.tmod`, ALREADY a constructor of the reflect
    slice's term type.

    So the honest reading of the `not:negated-dvd` skip is CONSERVATIVE, not
    forced: the encoding exists, and the skip is the choice not to rewrite a
    source's divisibility claim into a modular one at quote time.  Either way
    no constructor is added, which is why the residue does not touch the
    class question -- but the queue must say which of the two it is, because
    "the one shape with no dual" and "the one shape we chose not to rewrite"
    are different sentences and only the second is true."""
    encoded = _t("!=", _t("%", B, A), _lit(0))
    for name in ("Int", "Nat"):
        carrier_of, values, _pool, _binops, _unops = BOXES[name]
        for x in _points(values):
            assert eval_pred(encoded, x, carrier_of, None) == \
                (not eval_pred(_t("dvd", A, B), x, carrier_of, None)), \
                f"{name}: the tmod encoding of not-dvd fails at {x}"


def test_every_wide_match_for_negated_dvd_goes_through_tmod():
    """...and the reachability is really THROUGH `tmod`, not an accident of a
    generous pool: over the full integer pool, every atom whose table equals
    `not dvd(a, b)` mentions `%`.  (At `Nat` the ordered atoms `0 < b % a`
    and `1 <= b % a` join the two `!=` spellings; on `Int` a remainder can be
    negative, so only the `!=` pair survives -- a carrier difference worth
    recording, since it is exactly the sort of thing an integer-only reading
    of "the dual" would have generalised wrongly.)"""
    for name in ("Int", "Nat"):
        carrier_of, values, pool, binops, unops = BOXES[name]
        target = tuple(not v for v in
                       _truth(_t("dvd", A, B), carrier_of, values))
        hits = [lbl for lbl, atom in _atom_shapes(pool, binops + ("dvd",),
                                                  unops)
                if _truth(atom, carrier_of, values) == target]
        assert hits, f"{name}: the tmod encoding vanished from the sweep"
        assert all("%" in lbl for lbl in hits), \
            f"{name}: a match that does not go through tmod: {hits}"


def test_coprime_dual_needs_a_term_the_reflect_slice_does_not_have():
    """The second residue, measured the same way and disposed of differently:
    `not coprime(a, b)` IS `gcd(a, b) != 1` pointwise, but `gcd` is not a `Tm`
    constructor, so the atom stays outside the reflect slice under its
    EXISTING `op-out-of-reflect-slice` skip whatever negation does.  Recorded
    so the connectives row is not read as owing a `not:negated-coprime` skip
    it does not owe."""
    carrier_of, values, _pool, _binops, _unops = BOXES["Nat"]
    encoded = _t("!=", _t("gcd", A, B), _lit(1))
    for x in _points(values):
        assert eval_pred(encoded, x, carrier_of, None) == \
            (not eval_pred(_t("coprime", A, B), x, carrier_of, None))


# ------------------------------------------------------------------- teeth
def test_a_planted_dual_flip_is_caught_by_these_boxes():
    """THE PLANTED VIOLATION.  A sweep that proves a rule green has to be
    shown capable of reddening: three plausible mis-statements of the rules
    above -- the `<=` swap forgotten, De Morgan's connective left unflipped,
    and `not (p -> q)` read as an implication -- must each be caught by the
    same boxes, at some point, on some shape.  A tooth that cannot bite is
    decoration."""
    carrier_of, values = CONN_BOXES["Int"]
    p, q = _BASE_ATOMS[0], _BASE_ATOMS[3]
    planted = {
        "le-swap-forgotten": (_t("<=", A, B), _t("<", A, B)),
        "de-morgan-unflipped": (_t("and", p, q),
                                _t("and", push_not(p), push_not(q))),
        "implies-not-conjoined": (_t("implies", p, q),
                                  _t("implies", p, push_not(q))),
    }
    for label, (subject, wrong) in planted.items():
        caught = any(
            eval_pred(wrong, x, carrier_of, None)
            != (not eval_pred(subject, x, carrier_of, None))
            for x in _points(values))
        assert caught, f"{label}: the box cannot see this error"


def test_the_push_covers_the_declared_predicate_vocabulary_exactly():
    """THE COMPLETENESS CANARY, derived rather than typed.  The reading
    grammar's predicate vocabulary is `_BUILTIN_ATOM_OPS` plus every
    `MATH_OPERATORS` row whose role is `pred`, plus `_CONNECTIVES`; every
    member must either be PUSHED or be a NAMED residue, and nothing may be
    named that the grammar does not have.  A later purchase that mints a new
    atom then reds HERE -- where it reads as "negation has an unclassified
    shape" -- instead of silently inheriting a `not` that cannot reach it."""
    declared = set(_BUILTIN_ATOM_OPS) | set(_CONNECTIVES) | {
        w for w, spec in MATH_OPERATORS.items() if spec["role"] == "pred"}
    pushed, residue = set(), set()
    for op in sorted(declared):
        if op in _CONNECTIVES:               # connectives take PREDS, not terms
            probe = _t(op, _BASE_ATOMS[0], _BASE_ATOMS[2])
        elif MATH_OPERATORS.get(op, {}).get("arity", 2) == 1:
            probe = _t(op, A)
        else:
            probe = _t(op, A, B)
        try:
            push_not(probe)
        except NoDual:
            residue.add(op)
        else:
            pushed.add(op)
    assert pushed | residue == declared
    assert residue == set(NO_DUAL_ATOMS), \
        f"the residue moved: {residue} vs the declared {set(NO_DUAL_ATOMS)}"
    for op, way_out in NO_DUAL_ATOMS.items():
        assert op in declared, f"{op} is not an atom the grammar has"
        assert len(way_out.split()) >= 8, \
            f"{op}: a residue that names no encoding is an indefinite hold"


def test_no_new_constructor_is_needed_anywhere_in_the_answer():
    """The class question, stated as an assertion about the OUTPUT.  Every
    pushed form and every desugared `iff` uses only ops the evaluator already
    knows -- so nothing above requires a new `Tm`/`Pd` constructor, which is
    §3.1 rule 3(a)'s criterion read off the artifact rather than argued."""
    known_preds = set(_BUILTIN_ATOM_OPS) | set(_CONNECTIVES) | {
        w for w, spec in MATH_OPERATORS.items() if spec["role"] == "pred"}

    def ops_of(pred):
        out = {pred["op"]}
        if pred["op"] in _CONNECTIVES:
            for a in pred["args"]:
                out |= ops_of(a)
        return out

    subjects = []
    for _name, (_carrier_of, _values, pool, binops, unops) in BOXES.items():
        subjects += [atom for _lbl, atom in _atom_shapes(pool, binops, unops)]
    for p, q in itertools.product(_BASE_ATOMS, repeat=2):
        for conn in sorted(_CONNECTIVES):
            subjects.append(_t(conn, p, q))
        subjects.append(desugar_iff(p, q))
    for pred in subjects:
        assert ops_of(push_not(pred)) <= known_preds, pred["op"]

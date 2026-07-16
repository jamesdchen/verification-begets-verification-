"""Property tests for kernel/rung.py -- the §11.5 obligations for WP-T6a-CORE.

The pilot rule set lives HERE (a fixture, never in specs/): commutativity
ordering for {+,*,and,or,=,!=} via sort-children, plus flatten rules for nested
same-op {+,*}, under the lexicographic measure ["size","inversions"].  RNG is
seeded and confined to these tests; the module itself is pure.
"""
import random

import pytest

from common import canonical_json
from generators import math_reading
from kernel import rung
from kernel.rung import lower, match, subst, validate_rung, SpecError, FragmentMiss

COMMUTATIVE = ("+", "*", "and", "or", "=", "!=")


# --------------------------------------------------------- the pilot fixture
def _flatten_rules(op, maxarity=6):
    """Every (outer-arity O, nested position p, inner-arity I) merge rule with
    result arity <= maxarity: linear pattern->template rules that dissolve one
    level of same-op nesting.  Flatten removes an op-wrapper, so SIZE (the first
    lexicographic component) strictly falls."""
    rules = []
    for O in range(2, maxarity + 1):
        for I in range(2, maxarity + 1):
            if (O - 1) + I > maxarity:
                continue
            for p in range(O):
                inner = [f"i{j}" for j in range(I)]
                pat, tmpl = [], []
                for j in range(O):
                    if j == p:
                        pat.append({"op": op, "args": [{"var": v} for v in inner]})
                        tmpl.extend({"use": v} for v in inner)
                    else:
                        v = f"o{j}"
                        pat.append({"var": v})
                        tmpl.append({"use": v})
                rules.append({"id": f"flat_{op}_{O}_{p}_{I}",
                              "pattern": {"op": op, "args": pat},
                              "template": {"op": op, "args": tmpl}})
    return rules


def _sort_rules():
    return [{"id": f"sort_{op}", "primitive": "sort-children",
             "op": op, "key": "canonical"} for op in COMMUTATIVE]


PILOT = validate_rung({
    "rung": "canon", "over": "pred", "measure": ["size", "inversions"],
    "rules": _flatten_rules("+") + _flatten_rules("*") + _sort_rules(),
})


# --------------------------------------------------------- AST generators
_LEAVES = [{"ref": n} for n in "abcd"] + [{"lit": i} for i in range(3)]


def _gen_term(rng, depth, parent):
    if depth <= 0 or rng.random() < 0.4:
        return dict(rng.choice(_LEAVES))
    op = rng.choice([o for o in ("+", "*", "-", "%", "gcd") if o != parent])
    k = rng.randint(2, 4) if op in ("+", "*") else 2
    return {"op": op, "args": [_gen_term(rng, depth - 1, op) for _ in range(k)]}


def _gen_atom(rng):
    op = rng.choice(("=", "!=", "<=", "<", "dvd"))
    return {"op": op, "args": [_gen_term(rng, 2, None), _gen_term(rng, 2, None)]}


def _gen_pred(rng, depth, parent=None):
    if depth <= 0:
        return _gen_atom(rng)
    r = rng.random()
    if r < 0.4:
        op = rng.choice([o for o in ("and", "or") if o != parent])
        k = rng.randint(2, 3)
        return {"op": op, "args": [_gen_pred(rng, depth - 1, op) for _ in range(k)]}
    if r < 0.5 and parent != "implies":
        return {"op": "implies",
                "args": [_gen_pred(rng, depth - 1, "implies"),
                         _gen_pred(rng, depth - 1, "implies")]}
    if r < 0.65:
        return {"op": rng.choice(("even", "odd")), "args": [_gen_term(rng, 2, None)]}
    return _gen_atom(rng)


def _renest(op, args, rng):
    """Wrap a run of consecutive args in a same-op child -- associativity noise
    (leaf multiset preserved), the mixed-NESTING half of the orbit."""
    if len(args) < 3 or rng.random() < 0.5:
        return args
    i = rng.randrange(0, len(args) - 1)
    j = rng.randrange(i + 2, len(args) + 1)
    if j - i == len(args):
        return args
    return args[:i] + [{"op": op, "args": args[i:j]}] + args[j:]


def _scramble(node, rng):
    """A meaning-preserving orbit member: permute commutative args (mixed ORDER)
    and re-nest same-op {+,*} runs (mixed NESTING)."""
    if not isinstance(node, dict) or "args" not in node:
        return dict(node)
    op = node["op"]
    args = [_scramble(a, rng) for a in node["args"]]
    if op in COMMUTATIVE:
        rng.shuffle(args)
        if op in ("+", "*"):
            args = _renest(op, args, rng)
    return {"op": op, "args": args}


def _is_normal(node):
    """Independent oracle: fully flattened (+,*) and every commutative node's args
    ascending by canonical_json.  Does not reference the module's measure."""
    if not isinstance(node, dict) or "args" not in node:
        return True
    op, args = node["op"], node["args"]
    if op in COMMUTATIVE:
        if op in ("+", "*") and any(isinstance(a, dict) and a.get("op") == op
                                    for a in args):
            return False
        keys = [canonical_json(a) for a in args]
        if keys != sorted(keys):
            return False
    return all(_is_normal(a) for a in args)


# --------------------------------------------------------- (a) ORBIT TEST
def test_orbit_confluence():
    """random pred ASTs x random permutations/associations -> identical normal
    forms across each orbit (the §11.5 confluence obligation), and the normal
    form is genuinely canonical."""
    rng = random.Random(20240716)
    changed = 0
    for _ in range(120):
        seed = _gen_pred(rng, 3)
        members = [_scramble(seed, rng) for _ in range(5)]
        forms = {canonical_json(lower(PILOT, m)) for m in members}
        assert len(forms) == 1, "orbit reached >1 normal form"
        nf = lower(PILOT, members[0])
        assert _is_normal(nf), "normal form is not flat+sorted"
        if any(canonical_json(m) != next(iter(forms)) for m in members):
            changed += 1
    assert changed > 0, "generators never produced a non-trivial orbit"


# --------------------------------------------------------- (b) TERMINATION
def test_termination_refuses_measure_preserving_cycle():
    """A swap rule whose naive application cycles forever: under `size` the swap
    never strictly drops, so the driver refuses it and halts immediately (the
    measure check IS the totality guard)."""
    swap = {"id": "swap",
            "pattern": {"op": "+", "args": [{"var": "A"}, {"var": "B"}]},
            "template": {"op": "+", "args": [{"use": "B"}, {"use": "A"}]}}
    r = validate_rung({"rung": "c", "over": "term", "measure": "size",
                       "rules": [swap]})
    x = {"op": "+", "args": [{"ref": "b"}, {"ref": "a"}]}
    assert lower(r, x) is x           # refused; terminates with input identity


def test_termination_well_founded_progress():
    """The same swap under `inversions` sorts ONCE (strict drop) then halts (the
    reverse swap would raise inversions and is refused)."""
    swap = {"id": "swap",
            "pattern": {"op": "+", "args": [{"var": "A"}, {"var": "B"}]},
            "template": {"op": "+", "args": [{"use": "B"}, {"use": "A"}]}}
    r = validate_rung({"rung": "c", "over": "term", "measure": "inversions",
                       "rules": [swap]})
    x = {"op": "+", "args": [{"ref": "b"}, {"ref": "a"}]}
    y = lower(r, x)
    assert y == {"op": "+", "args": [{"ref": "a"}, {"ref": "b"}]}
    assert lower(r, y) == y


# --------------------------------------------------------- (c) IDEMPOTENCE
def test_idempotence_byte_identical():
    rng = random.Random(99)
    for _ in range(70):
        x = _scramble(_gen_pred(rng, 3), rng)
        y = lower(PILOT, x)
        assert canonical_json(lower(PILOT, y)) == canonical_json(y)


def test_flatten_and_sort_known_case():
    x = {"op": "+", "args": [{"op": "+", "args": [{"ref": "b"}, {"ref": "a"}]},
                             {"ref": "c"}]}
    assert lower(PILOT, x) == {"op": "+", "args": [{"ref": "a"}, {"ref": "b"},
                                                   {"ref": "c"}]}


# --------------------------------------------------------- (d) EMPTY REGISTRY
def test_empty_rung_is_identity():
    empty = {"rung": "nop", "over": "pred", "measure": "size", "rules": []}
    x = _gen_pred(random.Random(3), 3)
    assert lower(empty, x) is x       # byte-identical AND same object


# --------------------------------------------------------- (e) LINEARITY / VALIDATION
def test_match_linearity():
    p = {"op": "=", "args": [{"var": "X"}, {"var": "X"}]}
    assert match(p, {"op": "=", "args": [{"ref": "a"}, {"ref": "a"}]}, {}) is not None
    assert match(p, {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]}, {}) is None


def test_match_does_not_mutate_env():
    env = {}
    match({"var": "X"}, {"ref": "a"}, env)
    assert env == {}


def test_match_type_strict():
    # True must never match an integer literal 1
    assert match({"lit": 1}, {"lit": True}, {}) is None


def test_subst_unbound_use_is_spec_error():
    with pytest.raises(SpecError):
        subst({"use": "Z"}, {})


def test_validate_rejects_unknown_measure():
    with pytest.raises(SpecError):
        validate_rung({"rung": "r", "over": "pred", "measure": "disorder",
                       "rules": []})


def test_validate_rejects_dollar_op_in_template():
    bad = {"id": "b", "pattern": {"op": "+", "args": [{"var": "A"}, {"var": "B"}]},
           "template": {"op": "$F", "args": [{"use": "A"}, {"use": "B"}]}}
    with pytest.raises(SpecError):
        validate_rung({"rung": "r", "over": "term", "measure": "size",
                       "rules": [bad]})


def test_validate_rejects_var_in_op_position():
    bad = {"id": "b", "pattern": {"op": "+", "args": [{"var": "F"}, {"var": "A"}]},
           "template": {"op": {"use": "F"}, "args": [{"use": "A"}]}}
    with pytest.raises(SpecError):
        validate_rung({"rung": "r", "over": "term", "measure": "size",
                       "rules": [bad]})


def test_validate_rejects_unbound_template_use():
    bad = {"id": "b", "pattern": {"op": "even", "args": [{"var": "A"}]},
           "template": {"op": "odd", "args": [{"use": "B"}]}}
    with pytest.raises(SpecError):
        validate_rung({"rung": "r", "over": "pred", "measure": "size",
                       "rules": [bad]})


def test_validate_rejects_unknown_operator():
    bad = {"id": "b", "pattern": {"op": "frobnicate", "args": [{"var": "A"}]},
           "template": {"use": "A"}}
    with pytest.raises(SpecError):
        validate_rung({"rung": "r", "over": "pred", "measure": "size",
                       "rules": [bad]})


def test_validate_rejects_noncommutative_sort_children():
    bad = {"id": "b", "primitive": "sort-children", "op": "-", "key": "canonical"}
    with pytest.raises(SpecError):
        validate_rung({"rung": "r", "over": "term", "measure": "size",
                       "rules": [bad]})


def test_sort_statements_is_fragment_miss():
    bad = {"id": "b", "primitive": "sort-statements", "kind": "hypothesis",
           "key": "canonical"}
    with pytest.raises(FragmentMiss):
        validate_rung({"rung": "r", "over": "pred", "measure": "size",
                       "rules": [bad]})


def test_vocab_matches_grammar():
    """Anti-drift pin: the hardcoded operator vocabulary equals the F-G grammar
    in generators/math_reading.py (avoids a kernel->generators import while
    guaranteeing the two can never diverge)."""
    assert set(rung._TERM_OPS) == set(math_reading._TERM_OPS)
    assert set(rung._ATOM_OPS) == set(math_reading._ATOM_OPS)
    assert set(rung._CONNECTIVES) == set(math_reading._CONNECTIVES)

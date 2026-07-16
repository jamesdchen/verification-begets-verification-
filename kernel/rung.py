"""The minimal meta-interpreter (WP-T6a-CORE): three functions, two primitives,
one measure whitelist, under the §6 law amended by §11.5.

Pure and total: structural recursion over the input AST only; no I/O, no clock,
no randomness, no eval / imports-of-spec-content / callbacks / string-to-code.
The interpreter EXECUTES lowerings and certifies nothing (§6 "never the judge");
rung-below checkers validate every output in the later integration package.

The floor (kernel/rung_spec.md is the full schema):
  * ``match``  -- linear structural patterns.
  * ``subst``  -- template splicing.
  * ``lower``  -- a fixpoint driver that accepts a rewrite iff a whitelisted
                  well-founded measure STRICTLY drops (the only guard; there are
                  no per-rule guards in the schema).
  * primitives ``sort-children`` (the engine sorts an n-ary op's args; §11.5)
    and ``sort-statements`` (reserved, refused -- the pilot descopes it).
  * one closed measure-key whitelist with order-invariant (multiset-canonical)
    keys, which knowingly bakes the normalizer into the measure (§6 amendment).
"""
from __future__ import annotations

from common import canonical_json

# AST operator vocabulary.  Hardcoded (NOT imported) to keep kernel/ free of a
# generators/ dependency, and pinned equal to generators/math_reading.py by
# tests/test_rung_interp.test_vocab_matches_grammar so it can never drift.  These
# are exactly the ops _check_term / _check_pred admit.
_TERM_OPS = frozenset({"+", "*", "-", "%", "^", "gcd", "mod"})
_ATOM_OPS = frozenset({"=", "!=", "<=", "<", "dvd", "even", "odd", "coprime"})
_CONNECTIVES = frozenset({"and", "or", "implies"})
_ALL_OPS = _TERM_OPS | _ATOM_OPS | _CONNECTIVES

# Per-operator ARITY, pinned equal to what generators/math_reading.py's
# _check_term / _check_pred enforce (the SOURCE OF TRUTH) so a rung-spec that
# passes validate_rung can never carry a template that emits an AST the grammar
# would reject at lowering -- refuse at LOAD, not discover at lower().
# ``("exact", n)`` = exactly n operands; ``("min", n)`` = at least n.  Word ops
# take their MATH_OPERATORS arity (dvd 2, even 1, odd 1, gcd 2, coprime 2,
# mod 2).  ``^`` is exactly 2 with an extra exponent rule in _check_shape (a
# non-negative literal, in a template).  Pinned against math_reading by
# tests/test_rung_interp.test_arity_matches_grammar (import at TEST time, the same
# anti-drift pattern as test_vocab_matches_grammar).
_ARITY = {
    "^": ("exact", 2), "-": ("exact", 2), "%": ("exact", 2),
    "+": ("min", 2), "*": ("min", 2),
    "gcd": ("exact", 2), "mod": ("exact", 2),
    "dvd": ("exact", 2), "even": ("exact", 1), "odd": ("exact", 1),
    "coprime": ("exact", 2),
    "=": ("exact", 2), "!=": ("exact", 2), "<=": ("exact", 2), "<": ("exact", 2),
    "implies": ("exact", 2), "and": ("min", 2), "or": ("min", 2),
}

# The frozen commutative-op set: the only ops the ``inversions`` measure orders
# and the only ops ``sort-children`` may sort.  Specs do not get to define
# commutativity; they NAME the measure / select where to sort.
_COMMUTATIVE = frozenset({"+", "*", "and", "or", "=", "!="})

_MEASURE_KEYS = frozenset({"size", "inversions", "quantifier_count"})
_SORT_KEY_NAMES = frozenset({"canonical"})


class SpecError(Exception):
    """A rung-spec is malformed -- raised at LOAD by ``validate_rung`` (and by
    ``subst`` on an unbound ``use``).  Never a runtime default."""


class FragmentMiss(Exception):
    """A driver-level refusal: a construct that is inside the schema's reserved
    surface but not implemented (the ``sort-statements`` slot)."""


# ---------------------------------------------------------------- helpers
def _copy(x):
    """A pure deep copy (dicts/lists rebuilt, scalars shared-immutable)."""
    if isinstance(x, dict):
        return {k: _copy(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_copy(v) for v in x]
    return x


def _is_var(node):
    return isinstance(node, dict) and set(node) == {"var"}


def _is_use(node):
    return isinstance(node, dict) and set(node) == {"use"}


# ---------------------------------------------------------------- match
def match(pattern, node, env):
    """Linear structural match.  Returns a NEW env extending ``env`` on success,
    or ``None`` on failure; never mutates ``env``.

    ``{"var": X}`` binds X to ``node``; a re-binding succeeds iff it is
    canonical_json-equal to the first (linearity by structural equality).  Dicts
    match key-by-key on an identical key set; lists element-wise, same length;
    scalars by value AND type (so True never matches 1).  No segment variables,
    no backtracking.
    """
    if _is_var(pattern):
        name = pattern["var"]
        if name in env:
            return env if canonical_json(env[name]) == canonical_json(node) else None
        out = dict(env)
        out[name] = node
        return out
    if isinstance(pattern, dict):
        if not isinstance(node, dict) or set(pattern) != set(node):
            return None
        cur = env
        for k in sorted(pattern):
            cur = match(pattern[k], node[k], cur)
            if cur is None:
                return None
        return cur
    if isinstance(pattern, list):
        if not isinstance(node, list) or len(pattern) != len(node):
            return None
        cur = env
        for p, n in zip(pattern, node):
            cur = match(p, n, cur)
            if cur is None:
                return None
        return cur
    return env if type(pattern) is type(node) and pattern == node else None


# ---------------------------------------------------------------- subst
def subst(template, env):
    """Splice ``{"use": X}`` (a deep copy of ``env[X]``); copy everything else
    verbatim.  An unbound ``use`` is a SpecError, never a runtime default."""
    if _is_use(template):
        name = template["use"]
        if name not in env:
            raise SpecError(f"template uses unbound variable {name!r}")
        return _copy(env[name])
    if isinstance(template, dict):
        return {k: subst(v, env) for k, v in template.items()}
    if isinstance(template, list):
        return [subst(x, env) for x in template]
    return template


# ---------------------------------------------------------------- measure
def _canon(node):
    """The multiset-canonical normal form used ONLY for measure keys: recursively
    flatten nested same-op commutative children and sort commutative args by
    their own canonical key.  Baking this into the measure is what makes
    commutativity-sort confluent (§6 amendment, accepted explicitly)."""
    if not isinstance(node, dict) or "args" not in node:
        return node
    op = node.get("op")
    args = [_canon(a) for a in node["args"]]
    if op in _COMMUTATIVE:
        flat = []
        for a in args:
            if isinstance(a, dict) and a.get("op") == op and "args" in a:
                flat.extend(a["args"])            # children already canonical
            else:
                flat.append(a)
        flat.sort(key=canonical_json)
        args = flat
    out = dict(node)
    out["args"] = args
    return out


def _canon_key(node):
    return canonical_json(_canon(node))


def _size(node):
    if not isinstance(node, dict) or "args" not in node:
        return 1
    return 1 + sum(_size(a) for a in node["args"])


def _inversions(node):
    total = 0
    if isinstance(node, dict) and "args" in node:
        if node.get("op") in _COMMUTATIVE:
            keys = [_canon_key(a) for a in node["args"]]
            n = len(keys)
            for i in range(n):
                for j in range(i + 1, n):
                    if keys[i] > keys[j]:
                        total += 1
        for a in node["args"]:
            total += _inversions(a)
    return total


def _quantifier_count(node):
    c = 1 if isinstance(node, dict) and node.get("kind") == "quantifier" else 0
    if isinstance(node, dict) and "args" in node:
        for a in node["args"]:
            c += _quantifier_count(a)
    return c


_KEY_FN = {"size": _size, "inversions": _inversions,
           "quantifier_count": _quantifier_count}
_SORT_KEY_FN = {"canonical": _canon_key}


def _measure_value(measure, node):
    """A single natural (a named key) or a lexicographic tuple of them."""
    if isinstance(measure, str):
        return _KEY_FN[measure](node)
    return tuple(_KEY_FN[k](node) for k in measure)


# ---------------------------------------------------------------- driver
def _apply(rule, node):
    """The single-node action of a rule, or ``None`` if it does not fire here."""
    prim = rule.get("primitive")
    if prim == "sort-children":
        if not (isinstance(node, dict) and node.get("op") == rule["op"]
                and "args" in node):
            return None
        if "pattern" in rule and match(rule["pattern"], node, {}) is None:
            return None
        key = _SORT_KEY_FN[rule["key"]]
        new_args = sorted(node["args"], key=key)       # stable
        if new_args == node["args"]:
            return None                                # already sorted: no-op
        out = dict(node)
        out["args"] = new_args
        return out
    if prim is not None:                               # reserved, unimplemented
        raise FragmentMiss(f"primitive {prim!r} is reserved but not implemented")
    env = match(rule["pattern"], node, {})
    return None if env is None else subst(rule["template"], env)


def _rewrites(node, rules):
    """Yield whole-``node`` rewrites in frozen bottom-up-leftmost order (each
    child fully explored before this node), trying rules in list order."""
    if isinstance(node, dict) and "args" in node:
        for i, child in enumerate(node["args"]):
            for nc in _rewrites(child, rules):
                out = dict(node)
                new_args = list(node["args"])
                new_args[i] = nc
                out["args"] = new_args
                yield out
    for rule in rules:
        res = _apply(rule, node)
        if res is not None:
            yield res


def lower(rung, ast):
    """Fixpoint driver.  Repeatedly take the FIRST candidate rewrite (in the
    frozen order) whose whole-tree measure STRICTLY drops, restarting at root
    after each; halt when none does.  The strict-drop check is the totality
    enforcement AND the only guard.  Empty rules ⇒ identity (same object).

    ``rung`` is assumed already validated by ``validate_rung`` (validation is at
    load, not trusted at run)."""
    rules = rung["rules"]
    measure = rung["measure"]
    cur = ast
    while True:
        base = _measure_value(measure, cur)
        nxt = None
        for cand in _rewrites(cur, rules):
            if _measure_value(measure, cand) < base:
                nxt = cand
                break
        if nxt is None:
            return cur
        cur = nxt


# ---------------------------------------------------------------- validation
def _check_shape(node, is_template, seen, path):
    """Validate a pattern (is_template=False) or template (True) ranges only over
    the AST kinds _check_pred / _check_term admit, collecting var/use names into
    ``seen``.  Raises SpecError on anything else."""
    want, other = ("use", "var") if is_template else ("var", "use")
    if isinstance(node, dict) and set(node) == {want}:
        nm = node[want]
        if not (isinstance(nm, str) and nm):
            raise SpecError(f"{path}: {want} name must be a non-empty string")
        seen.add(nm)
        return
    if isinstance(node, dict) and set(node) == {other}:
        raise SpecError(f"{path}: {other!r} node is not allowed in a "
                        f"{'template' if is_template else 'pattern'}")
    if not isinstance(node, dict):
        raise SpecError(f"{path}: expected an AST-node object, got {node!r}")
    keys = set(node)
    if keys == {"ref"}:
        if not (isinstance(node["ref"], str) and node["ref"]):
            raise SpecError(f"{path}: ref must be a non-empty string")
        return
    if keys == {"lit"}:
        v = node["lit"]
        if not isinstance(v, int) or isinstance(v, bool):
            raise SpecError(f"{path}: lit must be an integer")
        return
    if keys == {"op", "args"}:
        op = node["op"]
        if not isinstance(op, str):
            raise SpecError(f"{path}: op must be a literal operator, not a "
                            f"variable (callee-as-argument trap, §11.2)")
        if op.startswith("$"):
            raise SpecError(f"{path}: '$'-variable in op position "
                            f"(callee-as-argument trap, §11.2)")
        if op not in _ALL_OPS:
            raise SpecError(f"{path}: unknown operator {op!r}")
        args = node["args"]
        if not isinstance(args, list) or not args:
            raise SpecError(f"{path}: args must be a non-empty list")
        # Arity gate (mirrors generators/math_reading.py exactly): refuse at LOAD
        # any node whose operand COUNT the AST grammar would reject at lowering.
        # A {var}/{use} arg counts toward the length -- length is checkable even
        # when the contents are variables.
        kind, n = _ARITY[op]
        if kind == "exact" and len(args) != n:
            raise SpecError(f"{path}: operator {op!r} takes exactly {n} arg(s), "
                            f"got {len(args)}")
        if kind == "min" and len(args) < n:
            raise SpecError(f"{path}: operator {op!r} takes at least {n} args, "
                            f"got {len(args)}")
        if op == "^":
            # Exponent position (^ is arity 2, so args[1] exists).  In a TEMPLATE
            # require a non-negative literal: a {use} there could splice a
            # non-literal exponent, outside the SMT-LIB fragment (D10) -- refuse
            # at validation.  In a PATTERN allow {lit} or a var: matching binds
            # anything, but the input AST was already legal so the bound value is.
            exp = args[1]
            if is_template:
                if not (isinstance(exp, dict) and set(exp) == {"lit"}
                        and isinstance(exp["lit"], int)
                        and not isinstance(exp["lit"], bool)
                        and exp["lit"] >= 0):
                    raise SpecError(
                        f"{path}.args[1]: '^' exponent in a template must be a "
                        f"non-negative integer literal (a use-var could splice a "
                        f"non-literal exponent, outside the fragment)")
            elif not (_is_var(exp) or (isinstance(exp, dict)
                                       and set(exp) == {"lit"})):
                raise SpecError(
                    f"{path}.args[1]: '^' exponent in a pattern must be an "
                    f"integer literal or a variable")
        for i, a in enumerate(args):
            _check_shape(a, is_template, seen, f"{path}.args[{i}]")
        return
    raise SpecError(f"{path}: not a legal AST node (keys {sorted(keys)})")


def _validate_rule(rule, ids):
    if not isinstance(rule, dict):
        raise SpecError(f"rule must be an object: {rule!r}")
    rid = rule.get("id")
    if not (isinstance(rid, str) and rid):
        raise SpecError(f"rule id must be a non-empty string: {rid!r}")
    if rid in ids:
        raise SpecError(f"duplicate rule id {rid!r}")
    ids.add(rid)
    if "primitive" in rule:
        prim = rule["primitive"]
        if prim == "sort-children":
            if set(rule) - {"id", "primitive", "op", "key", "pattern"}:
                raise SpecError(f"{rid}: unexpected sort-children keys")
            if rule.get("op") not in _COMMUTATIVE:
                raise SpecError(f"{rid}: sort-children op must be commutative "
                                f"{sorted(_COMMUTATIVE)}, got {rule.get('op')!r}")
            if rule.get("key") not in _SORT_KEY_NAMES:
                raise SpecError(f"{rid}: sort-children key must be one of "
                                f"{sorted(_SORT_KEY_NAMES)}")
            if "pattern" in rule:
                _check_shape(rule["pattern"], False, set(), f"{rid}.pattern")
            return
        if prim == "sort-statements":
            raise FragmentMiss(
                f"{rid}: sort-statements is reserved but not implemented "
                f"(the pilot descopes hypothesis sort; §11.5)")
        raise SpecError(f"{rid}: unknown primitive {prim!r}")
    if set(rule) - {"id", "pattern", "template"} or "pattern" not in rule \
            or "template" not in rule:
        raise SpecError(f"{rid}: a rewrite rule needs exactly id/pattern/template")
    bound, used = set(), set()
    _check_shape(rule["pattern"], False, bound, f"{rid}.pattern")
    _check_shape(rule["template"], True, used, f"{rid}.template")
    unbound = used - bound
    if unbound:
        raise SpecError(f"{rid}: template uses unbound var(s) {sorted(unbound)}")


def validate_rung(spec):
    """Validate a rung-spec at LOAD.  Returns the spec unchanged on success;
    raises SpecError (or FragmentMiss for a reserved primitive).

    ``over: pred|term`` is ADVISORY here: lower() never consults it and this
    validator only checks it is one of the two words -- enforcing that a rung
    actually ranges over the declared sort is deferred to the integration
    package's rung-below checkers.  That is sound because §6 "never the judge"
    makes every downstream consumer re-validate lowering outputs, so an output
    that a rung mislabels is caught at the consumer, not trusted from here."""
    if not isinstance(spec, dict) or set(spec) != {"rung", "over", "measure",
                                                   "rules"}:
        raise SpecError("rung-spec keys must be exactly "
                        "{rung, over, measure, rules}")
    if not (isinstance(spec["rung"], str) and spec["rung"]):
        raise SpecError("rung must be a non-empty id")
    if spec["over"] not in ("pred", "term"):
        raise SpecError("over must be 'pred' or 'term'")
    measure = spec["measure"]
    if isinstance(measure, str):
        names = [measure]
    elif isinstance(measure, list) and measure:
        names = measure
    else:
        raise SpecError("measure must be a key name or a non-empty list of keys")
    for k in names:
        if k not in _MEASURE_KEYS:
            raise SpecError(f"measure names a non-whitelisted key {k!r} "
                            f"(whitelist {sorted(_MEASURE_KEYS)})")
    if not isinstance(spec["rules"], list):
        raise SpecError("rules must be a list")
    ids = set()
    for rule in spec["rules"]:
        _validate_rule(rule, ids)
    return spec

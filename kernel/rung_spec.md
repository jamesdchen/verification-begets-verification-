# The rung-spec schema and the minimal meta-interpreter (WP-T6a-CORE)

`kernel/rung.py` is the §6 minimal meta-interpreter under its §11.5 amendment.
It is `kernel/`-class: pure, total, escape-free, reviewed as trusted surface.
Nothing here certifies anything — the interpreter executes lowerings; rung-below
checkers (norm-cert, instance replay, dual solver) validate every output. That
per-use validation is a LATER integration package; this package is the engine
and its schema only.

## The floor: three functions, two primitives, one whitelist

- `match(pattern, node, env) -> env | None` — linear structural matching.
- `subst(template, env) -> node` — template splicing.
- `lower(rung, ast) -> ast` — the fixpoint driver.
- primitives: `sort-children` (implemented), `sort-statements` (reserved,
  refused).
- one closed measure-key whitelist (below).

### `match` — linear structural patterns
- `{"var": X}` binds `X` to the whole `node`. **Linearity:** re-binding `X`
  succeeds iff the new node is `canonical_json`-equal to the first binding,
  else the match fails. (Chosen rule: structural equality, documented per §1.)
- a non-marker dict matches key-by-key: same key SET, each value matched
  recursively (op strings / lit ints match by value+type; `True`/`1` never
  cross-match).
- a list matches element-wise, same length. No segment variables, no
  backtracking.
- `match` never mutates the passed `env`; it returns a fresh extended dict.

### `subst` — template splicing
- `{"use": X}` splices a deep copy of `env[X]`. An **unbound** `use` raises
  `SpecError` — a spec-validation error, never a runtime default.
- everything else is copied verbatim (dicts key-by-key, lists element-wise,
  scalars as-is). Op strings are scalars and are preserved literally.

### `lower` — the fixpoint driver
- **frozen bottom-up-leftmost traversal, frozen rule order.** Candidate
  rewrites are enumerated deepest-leftmost-child first, then this node, trying
  rules in list order.
- **RESTART AT ROOT after every accepted rewrite** (§11.5).
- **accept a rewrite iff the rung's whitelisted measure STRICTLY drops**
  (per-step, whole-tree check). This single check is BOTH the totality
  enforcement AND the only guard: **there are no per-rule guards in the
  schema.** A commutativity swap on an already-sorted node fails to decrease
  the measure and is refused by the same check that enforces termination.
- an **empty rules list ⇒ `lower` is the identity** (returns the same object).
  This is the rung-free pin's substrate. (Multi-rung composition to a joint
  fixpoint — the `rung_pipeline_hash` of §11.5 — is the later integration
  package; this engine delivers the single-rung total driver.)

### Primitives (§11.5 amendment)
Linear pattern→template rules cannot reorder an n-ary argument list, so sorting
enters as an engine primitive: the rule SELECTS where it applies, the engine
sorts.
- `sort-children(op, key)` — sorts the matched op-node's `args` by the named
  key (stable sort). Restricted to the frozen commutative-op set.
- `sort-statements(kind, key)` — **reserved but NOT implemented** (the pilot
  descopes hypothesis sort, §11.5: it would permute the statement list and drag
  ids/provenance/probe keys). The slot is recognized by the schema; any rung
  that carries such a rule is refused with a `FragmentMiss` at load.

## Measure whitelist (closed enum, order-invariant keys — §11.5)

Specs **NAME** measures; they never define them. A measure is either a single
key name or a list of key names (a lexicographic tuple, compared left-to-right).

Key vocabulary:
- **`size`** — total node count.
- **`inversions`** — over every node whose op is in the frozen commutative set
  `{+, *, and, or, =, !=}`, the number of out-of-order pairs `(i<j)` in its
  `args`, ordered by the **multiset-canonical child key**
  `key(child) = canonical_json(_canon(child))`, where `_canon` recursively
  **flattens nested same-op children and sorts commutative args by this same
  key**. The key is computed **as if the child were already normalized**, so an
  unsorted inner subtree creates no phantom inversions at the parent — that is
  exactly what makes commutativity-sort **confluent**. This knowingly **bakes
  the normalizer into the measure** (§6 amendment accepts this explicitly).
- **`quantifier_count`** — count of `kind == "quantifier"` nodes. The pred/term
  fragment has none, so this key is **0 over every pred/term** and is
  **reserved** for the statement-level / `exists`-finitization rung (T6b). A
  lexicographic measure led by a constant-0 key is still well-founded because
  the driver's strict-drop check requires some later key to fall.

Well-foundedness: every key is a natural number; single keys and fixed-length
tuples of naturals under `<` are well-founded, so a strictly-decreasing sequence
is finite ⇒ `lower` terminates on ANY rule set.

### The pilot's measure
The canonicalization pilot uses the lexicographic measure **`["size",
"inversions"]`**:
- **flatten** (`+(+(a,b),c) → +(a,b,c)`) removes an op-wrapper ⇒ `size` strictly
  falls (first component), accepted regardless of what it does to `inversions`
  (flattening can transiently RAISE inversions — this is why a pure-inversions
  measure fails and the lexicographic pair is required).
- **sort** keeps `size` equal and strictly drops `inversions`.

## Rung-spec schema (JSON) and load-time validation

```
{ "rung": <id>, "over": "pred"|"term",
  "measure": <key> | [<key>, ...],
  "rules": [ rule, ... ] }
```
Two rule shapes:
```
rewrite:   { "id": <id>, "pattern": <pattern>, "template": <template> }
primitive: { "id": <id>, "primitive": "sort-children",
             "op": <commutative-op>, "key": "canonical", "pattern"?: <pattern> }
```
`validate_rung(spec)` (run at LOAD, never trusted at run) checks:
- keys are exactly `{rung, over, measure, rules}`; `over ∈ {pred, term}`.
- the named measure is in the whitelist (a key or a non-empty list of keys).
- rule ids are non-empty and unique.
- patterns/templates range only over AST kinds `_check_pred` / `_check_term`
  admit (`{ref}`, `{lit}`, `{op,args}` with `op ∈` the frozen operator
  vocabulary — kept in sync with `generators/math_reading.py` by a test).
- every `{"use": X}` in a template is bound by a `{"var": X}` in the pattern.
- **no `$`-prefixed string and no variable node in an `"op"`-key position of a
  template** — §11.2's callee-as-argument trap (dynamic dispatch is
  unpriceable), enforced here too. Op positions must be literal operators.
- `sort-children`: `op` in the commutative set, `key == "canonical"`, optional
  `pattern` well-formed.
- `sort-statements`: recognized (reserved slot) but refused with `FragmentMiss`.

Errors: `SpecError` for load/validation failures; `FragmentMiss` for
driver-level refusals (the reserved-but-unimplemented primitive).

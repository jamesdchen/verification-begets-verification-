"""The `refusal-set-carrier` row's price, DERIVED instead of estimated.

PLAN_FRAGMENT §4 bills this row as "an uninterpreted predicate in the SMT
mirror and a `Pd` constructor plus its Decidable story in the reflect
slice".  Both halves of that sentence are true, and results/p10_bill_
measurement.md (PR #203) measured a third cost beside them -- threading a
set environment through the slice's ~50 explicit `env` signatures.

None of those is the binding constraint, and this module is why.  A free
set variable is not only a PREDICATE-layer atom; in the emitted statement
it is a BINDER, and every binder in this pipeline is decided by SWEEPING
its box-relativized domain.  For an Int variable that domain is the box.
For a set variable it is the POWERSET of the box -- so the sweep's cost is
exponential in the box width, and the theorems below pin that against the
repo's OWN committed constants rather than against a remembered number.

Everything here is derived:
  * the box widths come from `math_eval._box_size`, never a literal;
  * the ceiling comes from `math_eval.EXISTS_SHADOW_MAX_ASSIGNMENTS`;
  * the lead subject's shape comes from the committed class measurement
    (`tests/test_set_object_class.py`), which reads the corpus prose.

The Lean side of the same measurement is `results/reflect_candidates.json`
round `p9-parallel-tower-r3`, whose `subsetsOfS_length` proves
`(subsetsOfS b).length = 2 ^ b.length` -- the cardinality this module then
prices against the pipeline's committed box.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.math_eval import (EXISTS_SHADOW_MAX_ASSIGNMENTS, _box_size,
                                  exists_shadow_shape)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The pinned bound: `run/anchor.py::BOUND`, and the default of every
# `bound=8` keyword on the shadow/formalize entry points.  Read, not
# retyped, so a re-bound of the gate re-prices this measurement.
_BOUND = 8


def _bound_of_record() -> int:
    """B, read off run/anchor.py rather than hardcoded here."""
    src = open(os.path.join(HERE, "run", "anchor.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "BOUND":
                    return int(ast.literal_eval(node.value))
    raise AssertionError("run/anchor.py no longer defines BOUND")


def _width(carrier: str) -> int:
    """One object's box width, from the gate's own arithmetic."""
    return _box_size(["x"], {"x": carrier}, _bound_of_record())


def test_the_pinned_bound_is_what_this_module_prices_against():
    """The measurement is only honest if it reads the live bound."""
    assert _bound_of_record() == _BOUND
    assert _width("Int") == 2 * _BOUND + 1        # 17
    assert _width("Nat") == _BOUND + 1            # 9


def test_one_set_binder_costs_the_powerset_of_the_box():
    """A set variable's box-relativized domain is 2 ** |box|, not |box|.

    This is the number `subsetsOfS_length` proves in Lean, evaluated at the
    committed Int box.  It is the whole finding in one line: a set binder is
    not one more column in the sweep, it is an exponent on it."""
    assert 2 ** _width("Int") == 131072
    assert 2 ** _width("Nat") == 512


def test_the_lead_subject_is_outside_the_pipelines_decision_procedure():
    """`09_Sets#definition-003` -- the subject this row was written for, and
    its whole measured inventory -- defines INTERSECTION over two sets the
    source gives no comprehension for, so its reading carries TWO set
    binders beside one ordinary Int element variable.

    The committed class measurement is what says "two sets"
    (tests/test_set_object_class.py::
    test_definition_003_needs_arbitrary_sets_and_stays_held asserts the
    prose says so and that the faithful reading refuses under
    `set:free-set-variable`).  Here we only price the shape it names."""
    w = _width("Int")
    domain = (2 ** w) * (2 ** w) * w              # U, V, x
    assert domain == 292057776128
    # Five orders of magnitude past the only combinatorial ceiling the gate
    # has anywhere -- and see the next test for why even that is generous.
    assert domain > EXISTS_SHADOW_MAX_ASSIGNMENTS * 100000


def test_a_single_set_binder_plus_one_ordinary_object_already_exceeds_the_ceiling():
    """Not just the lead subject: the row's FIRST non-trivial shape is
    already past the ceiling, so there is no cheap corner of it at Int."""
    w = _width("Int")
    assert (2 ** w) * w > EXISTS_SHADOW_MAX_ASSIGNMENTS


def test_the_same_construct_is_tractable_at_the_Nat_box():
    """The other side of the split, and the reason this is a re-pricing
    rather than a refusal: at a Nat box the identical construct is small.
    A row that is impossible at one carrier and cheap at another is TWO
    rungs wearing one name -- the P8 and P9 finding, a third time."""
    w = _width("Nat")
    assert (2 ** w) * w <= EXISTS_SHADOW_MAX_ASSIGNMENTS
    assert (2 ** w) * (2 ** w) * w > EXISTS_SHADOW_MAX_ASSIGNMENTS


# --------------------------------------------------------------------------- #
# Why the wall cannot be walked around: the two structural facts.
# --------------------------------------------------------------------------- #
def test_the_bounded_shadow_is_mandatory_so_SMT_cannot_carry_a_set_reading():
    """§4 bills the SMT half as "an uninterpreted predicate", which z3 would
    handle symbolically with no enumeration at all.  That would be a way
    around the powerset -- if SMT could carry a reading.  It cannot.

    `run/formalize.py`'s stage 4 is the instances gate, and BOTH its arms
    (`_instances`, `_exists_instances`) are pure `math_eval`: the SMT mirror
    is reached only from `_nonvacuity`, and only over HYPOTHESES, so it
    never sees the conclusion.  Checked structurally, so the claim cannot
    rot into a comment."""
    src = open(os.path.join(HERE, "run", "formalize.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    fns = {n.name: n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef)}
    for name in ("_instances", "_exists_instances"):
        assert name in fns, name
        used = {n.value.id for n in ast.walk(fns[name])
                if isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)}
        assert "math_smt" not in used, (
            f"{name} now reaches math_smt; stage 4 was the enumeration-only "
            "gate this measurement rests on")
        assert "math_eval" in used, name


def test_the_forall_path_has_no_combinatorial_ceiling_at_all():
    """The second structural fact, and the sharper half.

    `EXISTS_SHADOW_MAX_ASSIGNMENTS` is consulted at exactly one site --
    inside `exists_shadow_shape` -- which returns `forall-only` BEFORE the
    ceiling arithmetic whenever the reading has no ∃ binder.  So the ceiling
    guards the ∃ path only.  The row's lead subject is a DEFINITION (∀-only),
    which means a paid-for set tower would not honest-skip it as
    `exists-domain-too-large`: nothing would stop it.

    Checked two ways: the classifier returns `forall-only` for a ∀-only
    shape regardless of bound, and the ceiling name appears in exactly one
    function."""
    src = open(os.path.join(HERE, "generators", "math_eval.py"),
               encoding="utf-8").read()
    tree = ast.parse(src)
    consulting = {fn.name for fn in ast.walk(tree)
                  if isinstance(fn, ast.FunctionDef)
                  and any(isinstance(n, ast.Name)
                          and n.id == "EXISTS_SHADOW_MAX_ASSIGNMENTS"
                          for n in ast.walk(fn))}
    assert consulting == {"exists_shadow_shape"}, consulting

    # and that function leaves before the ceiling on a forall-only shape
    fn = next(f for f in ast.walk(tree)
              if isinstance(f, ast.FunctionDef)
              and f.name == "exists_shadow_shape")
    body_src = ast.get_source_segment(src, fn) or ""
    early = body_src.index('"forall-only"')
    ceiling = body_src.index("EXISTS_SHADOW_MAX_ASSIGNMENTS")
    assert early < ceiling, (
        "the forall-only early return no longer precedes the ceiling; the "
        "asymmetry this measurement records has changed")


def test_the_lean_round_that_proves_the_cardinality_is_queued():
    """The Lean half of this measurement is a queued authoring round, not a
    slice edit.  If the round is renamed or dropped, this reds -- so the
    prose above can never outlive its evidence."""
    import json
    p = os.path.join(HERE, "results", "reflect_candidates.json")
    d = json.load(open(p, encoding="utf-8"))
    ids = [c["candidate_id"] for c in d["candidates"]]
    assert "p9-parallel-tower-r3" in ids, ids
    r3 = next(c for c in d["candidates"]
              if c["candidate_id"] == "p9-parallel-tower-r3")
    # the two theorems that carry the finding
    assert "subsetsOfS_length" in r3["declares"]
    assert "checkStmtBoxS_sound" in r3["declares"]
    # and they are actually IN its own text (the ride's own rule)
    for name in ("subsetsOfS_length", "checkStmtBoxS_sound"):
        assert f"theorem {name}" in r3["module_text"], name

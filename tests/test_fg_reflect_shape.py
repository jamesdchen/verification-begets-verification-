"""The additive-class rule, mechanized: a STRUCTURE PIN on the reflect slice.

PLAN_FRAGMENT §3.1 rule 3 binds every UNATTENDED purchase to the additive
class, and three of its five criteria are structural facts about
`tools/FgReflect.lean` rather than judgements: (a) no new `Tm`/`Pd`
constructor, (c) decidability INHERITED -- i.e. no new `Decidable` instance
alongside `decDenote`/`decDenoteN` -- and (d) no new import.  Stated only in
prose, those criteria are checked by whoever happens to read the diff; stated
as a pin, they are checked by the suite in the container that authored the
purchase.  That is the point: no done-condition of this loop may live only as
prose -- the same defect that let the census's dead terms sit unmeasured for
cycles.  The precedents this file copies are `kernel/certs.py`'s pinned
tuples and `tests/test_hammer_bench.py`'s equality teeth: a frozen surface
plus an equality, so drift is a red, never a discovery.

WHAT A FAILURE HERE MEANS.  This purchase added a constructor, an instance,
or an import -- that is TOWER-class, which §3.1 rule 3 makes ATTENDED-ONLY.
An unattended session does not take it: yield, naming the criterion that
failed and the tower-class work as a named attended follow-up (the P3
precedent, results/p3_delta.md -- the signal split shipped, the carrier did
not).  If the growth IS intended and a maintainer is present to read the red,
update the pin below IN THE SAME COMMIT and say so in the delta receipt:
growing this tuple is the deliberate, reviewable act that records leaving the
additive class.  Never widen the pin to make a bill fit.

WHAT THIS FILE DOES NOT CHECK.  Criterion (b) -- the substitution lemma stays
UNCONDITIONAL -- and criterion (e) -- carrier checks that fail CLOSED -- are
proof-shaped and carrier-shaped, not lexical; (b) is discharged by the slice's
own `substPd_*`/`substTm_*` theorems in the Lean lane and (e) by the reading
path's fail-closed tests.  A green here is therefore evidence about the
structural half only, never a verdict on the whole rule.

Lean-free and textual by construction, so it runs in every container (the
no-local-Lean policy): the module is PARSED, never elaborated, and never
edited by this file.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE = os.path.join(ROOT, "tools", "FgReflect.lean")
PLAN = os.path.join(ROOT, "PLAN_FRAGMENT.md")

# --- THE PIN ---------------------------------------------------------------
#
# The reflect slice's whole structural surface as of P4 (the ZMod congruence
# image).  Every purchase since P1 has landed INSIDE these tuples and said so
# in its own block comment: the P1 fold layer ("no binding constructor enters
# `Tm` ... a SEPARATE purchase, not a widening of this one") and the P2
# cardinality layer ("adds NO binding constructor to `Tm` ... a SEPARATE
# purchase and a NAMED reflect skip") are the disposition §3.1 rule 3 names
# verbatim, and P3/P4 held the same line (`zmodEq` is a plain `def` over the
# EXISTING `pdvd` atom, results/p3_delta.md refused the rational tower).
#
# So: growing any tuple below is not a mechanical chore, it is the moment the
# slice leaves the additive class.  It is allowed -- deliberately, reviewably,
# in the same commit as the Lean edit, with the class change named in the
# receipt -- and it is ATTENDED-ONLY under §3.1 rule 3.  An unattended session
# that finds itself editing this block has misclassified its bill.
TM_CONSTRUCTORS = ("lit", "tvar", "add", "sub", "mul", "tmod", "pow")
PD_CONSTRUCTORS = ("peq", "ple", "plt", "pne", "pdvd", "peven", "podd",
                   "pand", "por", "pimp")
# The inductive types themselves: a whole new inductive is the same escape as
# a new constructor (it is what "a new evaluation tower" looks like in text),
# so the type list is pinned alongside the constructor lists.
INDUCTIVES = ("Tm", "Pd", "Stmt", "Bnd")
# Decidability is INHERITED, criterion (c): these two instances -- the Int
# tower's and the Nat tower's -- are the entire `Decidable` surface, and every
# purchase since has routed its predicates through them.  A third instance
# means a new atom decided a new way.
INSTANCES = ("decDenote", "decDenoteN")
# Criterion (d), stated as a count rather than a list: the module's scope
# claim is that its trusted surface is the Lean kernel and NOTHING else, so
# the honest pin is ZERO imports.  Widening `common.MATHLIB_IMPORTS` is its
# own purchase; widening this is not a substitute for it.
IMPORT_COUNT = 0

_FAILURE_ADVICE = (
    "this purchase added a constructor/instance/import to the reflect slice "
    "-- that is TOWER-class, which PLAN_FRAGMENT §3.1 rule 3 makes "
    "ATTENDED-ONLY.  An unattended session yields here, naming the failed "
    "criterion and the tower-class work as an attended follow-up.  If the "
    "growth IS intended, update the pin in tests/test_fg_reflect_shape.py in "
    "THIS commit and say so in the delta receipt."
)


# --- the parser (textual; the module is read, never written) ---------------

def _module_text() -> str:
    with open(MODULE, encoding="utf-8") as fh:
        return fh.read()


def strip_comments(text: str) -> str:
    """Blank out Lean comments, preserving line structure.

    Necessary, not decorative: the slice's own design commentary contains
    lines that begin with the word ``instance`` (the decDenote block comment
    at the top of the decision layer, and the shape-4 discussion), so a naive
    grep over the raw file would count prose as declarations.  We match what
    the elaborator sees.  Block comments nest, per Lean; doc comments
    (``/-- ... -/``) open with ``/-`` and so are covered by the same scanner.
    """
    out = []
    i, n, depth = 0, len(text), 0
    while i < n:
        if text.startswith("/-", i):
            depth += 1
            i += 2
            continue
        if depth and text.startswith("-/", i):
            depth -= 1
            i += 2
            continue
        if depth:
            out.append("\n" if text[i] == "\n" else " ")
            i += 1
            continue
        if text.startswith("--", i):
            j = text.find("\n", i)
            if j < 0:
                out.append(" " * (n - i))
                break
            out.append(" " * (j - i))
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def inductive_names(code: str) -> tuple:
    """Every top-level ``inductive`` type name, in declaration order."""
    return tuple(re.findall(r"(?m)^inductive\s+([A-Za-z_][A-Za-z0-9_']*)",
                            code))


def constructors(code: str, ty: str) -> tuple:
    """The constructor names of ``inductive ty``, in declaration order.

    The block runs from the header to the first line that starts a new
    top-level declaration; indented continuation lines belong to the
    constructor above them.
    """
    m = re.search(r"(?m)^inductive\s+%s\b[^\n]*\n" % re.escape(ty), code)
    assert m, f"FgReflect.lean has no `inductive {ty}` -- {_FAILURE_ADVICE}"
    names = []
    for line in code[m.end():].splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            names.append(stripped[1:].split(":")[0].strip())
            continue
        if line[:1].isspace():          # continuation of the ctor above
            continue
        break
    return tuple(names)


def instance_names(code: str) -> tuple:
    """Every top-level ``instance <name>`` declaration name."""
    return tuple(re.findall(r"(?m)^instance\s+([A-Za-z_][A-Za-z0-9_']*)",
                            code))


def import_lines(code: str) -> tuple:
    """Every ``import`` line (criterion (d): there must be none)."""
    return tuple(re.findall(r"(?m)^\s*import\s+.*$", code))


def _code() -> str:
    return strip_comments(_module_text())


# --- the teeth -------------------------------------------------------------

def test_tm_constructors_match_the_pin():
    # Criterion (a), term half.  The P1 fold and the P2 cardinality both
    # reflect through UNROLLS precisely so this tuple does not move.
    assert constructors(_code(), "Tm") == TM_CONSTRUCTORS, _FAILURE_ADVICE


def test_pd_constructors_match_the_pin():
    # Criterion (a), predicate half.  P4's congruence image rides the
    # EXISTING `pdvd` atom for exactly this reason.
    assert constructors(_code(), "Pd") == PD_CONSTRUCTORS, _FAILURE_ADVICE


def test_inductive_types_match_the_pin():
    # A new inductive is what "a new evaluation tower" looks like in text.
    assert inductive_names(_code()) == INDUCTIVES, _FAILURE_ADVICE


def test_decidable_instances_match_the_pin():
    # Criterion (c): decidability is INHERITED from these two instances.  A
    # third one means a new atom is decided a new way -- tower-class.
    assert instance_names(_code()) == INSTANCES, _FAILURE_ADVICE


def test_module_imports_nothing():
    # Criterion (d), and the module's own scope claim: the trusted surface is
    # the Lean kernel and nothing else.  Checked on the comment-stripped text
    # (what the elaborator sees) AND on the raw file, since the escape gate is
    # lexical over the whole file including prose.
    assert len(import_lines(_code())) == IMPORT_COUNT, _FAILURE_ADVICE
    assert len(import_lines(_module_text())) == IMPORT_COUNT, _FAILURE_ADVICE


def test_rule_and_mechanism_cannot_drift_apart():
    """The plan text must name this file.

    growth_protocol.conformance()'s teeth index is the idiom: a rule whose
    mechanism is unnamed decays back into prose the first time someone
    rewrites the paragraph.  So §3.1 rule 3 cites this filename, and this
    tooth is what keeps the citation there.
    """
    with open(PLAN, encoding="utf-8") as fh:
        plan = fh.read()
    needle = "tests/test_fg_reflect_shape.py"
    assert needle in plan, (
        f"PLAN_FRAGMENT.md no longer names {needle}: §3.1 rule 3's structural "
        "criteria would be prose again.  Restore the citation, or delete this "
        "pin deliberately -- never let the rule and its mechanism drift apart."
    )
    # ...and it must be cited where the rule lives, not merely somewhere.
    idx = plan.index(needle)
    # Whitespace-normalized: the plan is hard-wrapped, so the rule's own
    # heading straddles a line break.
    window = " ".join(plan[max(0, idx - 4000):idx].split())
    assert "additive-class rule" in window.lower(), (
        f"{needle} is cited in PLAN_FRAGMENT.md but no longer inside the "
        "additive-class rule (§3.1 rule 3)."
    )

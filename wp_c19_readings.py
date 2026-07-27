"""C19 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus addition below.  Sibling of wp_c2/c3/c4_readings.py;
same discipline, next batch.

PROVENANCE.  The source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    133_sets_problem_017         <- math2001 09_Sets#problem-017

THE BATCH THIS ONE CAME OUT OF.  C3 cycle 28 took FOUR subjects through
`intake_from_frontier --unblocked refused:set-membership` -- every subject
P9 paid for, and the first take against that row.  ONE certified and is read
here; THREE refused and are recorded in the ledger as first-class demand
data, each gate or evaluator verdict quoted verbatim in
results/c3_cycle_28.md.  The refused three had their laid-down source files
removed: a refused subject is demand data, never a corpus source.

THIS IS THE CORPUS'S FIRST READING TO NAME A SET.  `setdef` + `mem` are what
P9 bought, and the reading below uses both -- which is the whole reason the
subject was re-selected.  It also inherits the cycle-16 caveat in full, so
that is stated here rather than left to the green:

  THE HAND STEP, DECLARED.  The source's OUTER set is a powerset
  comprehension, `{s : P(N) | 3 in s}`, whose parameter ranges over SETS.
  That is `set:set-valued-param` -- explicitly what P9 does NOT buy
  (generators/math_reading.py, the P9 block), because its body applies
  membership to a set the reading has no body for.  The outer membership is
  taken at a LITERAL set, however, so it unfolds definitionally in one step:
  `{n | even n} in {s | 3 in s}` IS `3 in {n | even n}`.  The reading below
  takes that one step BY HAND and states what remains -- 3 is not in the set
  of even numbers -- with the vocabulary P9 did buy.  The inner
  comprehension is carried as a real `setdef`, so this is NOT the fully
  flattened `not (even 3)` that source 125 (`10 notin {n | n odd}`, cycle
  16) had to settle for.  That difference is the delta P9 bought here.

  WHAT THE GREEN IS AND IS NOT.  Cycle 16 recorded that a green reached
  through a literal-set unfolding is COVERAGE and not evidence of set
  coverage, and tests/test_set_object_class.py (4) says the same about this
  subject in advance.  Nothing below revises that: the tower-class residue
  `refusal-set-carrier` stays open and priced, and this reading is not
  evidence against it.  What it IS evidence of is narrower and real -- P9
  made the subject EXPRESSIBLE, where before the gate refused at `mem`
  outright.

The READING below was authored by the driver session (UNMETERED; reused
identically by both arms), gate-checked and box-verified TRUE before it was
written down.
"""


PROVENANCE = {
    '133_sets_problem_017': {
        "corpus": 'math2001',
        "node_id": '09_Sets#problem-017',
        "text_sha256": 'cf25fc424c4d6f85e9a1cb4259a96802c7f27f2a0aeac4641e11b035dca51470',
    },
}


def _amb(carrier):
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}


def _obj(i, name, quote, typ):
    return {"id": i, "force": "presupposition", "quote": quote,
            "lf": {"kind": "object", "name": name, "type": typ}}


def _q(sid, objects, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "quantifier", "binder": "forall",
                   "objects": objects}}


def _hyp(i, pred, quote, force="demand"):
    return {"id": i, "force": force, "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _con(pred, quote):
    return {"id": "c", "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def _opw(i, word, carrier):
    return {"id": i, "force": "choice", "quote": "",
            "lf": {"kind": "operator", "word": word, "carrier": carrier}}


def _setdef(i, name, param, body, quote):
    return {"id": i, "force": "presupposition", "quote": quote,
            "lf": {"kind": "setdef", "name": name, "param": param,
                   "body": body}}


def r(name):
    return {"ref": name}


def lit(n):
    return {"lit": n}


def op(o, *args):
    return {"op": o, "args": list(args)}


def in_(term, s):
    return {"op": "mem", "args": [term, {"set": s}]}


READINGS = {}

# 133 <- 09_Sets#problem-017: "Show that {n : N | n is even} notin
# {s : P(N) | 3 in s}."  The inner comprehension is named `a` with a real
# `setdef` -- the corpus's first -- and the conclusion is the outer
# membership after its ONE definitional unfolding at the literal set (the
# hand step declared in this module's docstring).  Carrier `Nat` is the
# source's own type ascription, not a preference.
READINGS['133_sets_problem_017'] = {
    "theorem": "nat_evens_are_not_a_set_containing_three",
    "statements": [
        _amb("Nat"),
        _opw("opev", "even", "Nat"),
        _setdef("sd", "a", "k", op("even", r("k")),
                r"\{n:\mathbb{N}\mid n\text{ is even}\}"),
        _con(op("not", in_(lit(3), "a")),
             r"\{n:\mathbb{N}\mid n\text{ is even}\}\notin"
             r"\{s:\mathcal{P}(\mathbb{N})\mid 3 ∈s\}"),
    ]}

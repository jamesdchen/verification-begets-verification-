"""NAMED FUNCTION SYMBOLS over the CURRENT fragment: what is the P8 row's
bill really, and what does it really return?

THE QUESTION THIS FILE ANSWERS MECHANICALLY.  `results/purchase_frontier.json`
carries a row `refusal-function-symbol` declared `bill_class:
"definitional-extension"` and priced at eleven blocking refusals, with the
prose "factorial, the recurrences a_n/d_n/F_n, the Bezout coefficients: each
is an arbitrary NAMED function the corpus introduces and the fragment has no
word for."  A `definitional-extension` is attended-only under PLAN_FRAGMENT
§3.1 rule 3, so this one declaration is load-bearing for whether the purchase
loop can turn at all.  P6 is the precedent for refusing to settle such a
declaration by preference: `not` was declared tower-class on the ASSUMPTION it
needed a `Pd` constructor, and `tests/test_nnf_duals.py` measured that it
pushes to duals the fragment already had.  Which bill P8 really is -- and,
separately, which subjects it really returns -- are two FACTS ABOUT THE SLICE,
and they are measured here rather than argued.

WHAT COUNTS AS A PROOF HERE (and why it is not a second opinion).  Every
claim below is asserted against the repo's OWN machinery -- the gate
`generators/math_reading.parse_math_reading`, the evaluator
`generators/math_eval`, the compiler `generators/math_compile` and the SMT
mirror `generators/math_smt` -- and never against a re-implementation of the
fragment's semantics.  The subject set is not transcribed either: it is read
out of `results/frontier_refusals.jsonl` and `results/frontier.json` and the
prose is re-derived from the primary corpus artifacts by content hash, so a
re-census that moves a subject moves this file's answer with it instead of
leaving a stale claim behind.  Offline, deterministic, Lean-free.

THE FINDING, in the order the tests below establish it.

  (1) THE PRICE IS OVERSTATED BY SIX.  Six of the eleven subjects carry a
      SECOND refusal, `symbolic-exponent`, and the gate refuses a variable
      exponent independently of anything to do with function symbols
      (`^` takes a literal exponent only; D10).  A function-symbol mechanism
      bought alone returns none of those six.  The ceiling on the row is FIVE
      subjects, not eleven.

  (2) TWO OF THE ROW'S THREE NAMED EXEMPLARS ARE ALREADY IN THE FRAGMENT.
      * FACTORIAL IS `bigprod`.  `n!` at a literal `n` is
        `bigprod(i, 1, n, i)` -- P1's bounded big-operator, bought two
        purchases ago -- and it rides all four channels unchanged: the gate
        admits it, the evaluator computes 720, the compiler emits
        `Finset.prod (Finset.Icc 1 6)`, the SMT mirror unrolls it to
        `(* 1 2 3 4 5 6)`.  The FAITHFUL reading of the factorial subject at
        its stated generality refuses `bigop:symbolic-bound` -- P1's own
        freeze, the demand the census already prices under `sequences-sums`
        -- and not for want of a word for the function.
      * THE BEZOUT COEFFICIENTS ARE SKOLEM WITNESSES.  `gcd` is a lexicon
        term word at `Int` and the fragment binds `exists`, so
        `a*x + b*y = gcd(a, b)` parses today and the evaluator witnesses it at
        every one of the 169 integer pairs in the box.  The repo already
        carries exactly that reading's source
        (`specs/mathsources/42_bezout_identity.txt`).  Against the math2001
        node's OWN prose the same reading refuses on GROUNDEDNESS -- the
        existential is not a span the text contains -- which is a fact about
        that sentence's shape, not about the fragment's reach.

  (3) A RECURRENCE AT A LITERAL INDEX UNFOLDS AND THE FUNCTION VANISHES.
      This is the source-121/122 shape: an object DEFINED AT THE POINT OF USE
      by an in-fragment condition needs no word of its own.  `a_5 = 2^5 +
      (-1)^5` becomes six declared objects and four defining hypotheses, all
      of them `= + * -` over literals; the gate admits it and the evaluator
      agrees on the nose (and refutes both one-off perturbations).  Same for
      `x_3 ≡ 1 mod 4` and for `a_4 ≡ 1 or 5 mod 6`.

  (4) AND YET THE MECHANISM IS STILL TOWER-CLASS -- which is the half of this
      measurement that does NOT overturn the declaration.  At its stated
      generality a recurrence is an INDEXED FAMILY, and the reading that
      drops the index parses into something else entirely (test (8) below:
      a free object is unconstrained, and the evaluator produces nine
      counterexamples to a statement the source asserts).  Closing that needs
      an application node: `tools/FgReflect.lean`'s `Tm` has six constructors
      and not one of them applies anything, and `decDenote` decides every
      `Pd` BY COMPUTATION -- an uninterpreted symbol constrained only by
      axioms has no computable interpretation, so the rung forces both a new
      constructor and a new `Decidable` story.  That is §3.1 rule 3(a) read
      off the artifact rather than argued, and it is why the row stays
      attended-only.

THE HONEST NET.  `definitional-extension` SURVIVES as a class verdict; the
row's PRICE and its EXEMPLARS do not.  The bill that returns subjects is
five-wide, not eleven, and buying it would not touch the six subjects the
symbolic exponent holds.  No additive slice returns any of the eleven -- the
literal-index instances are already expressible, so what they ask of us is a
reading discipline, not a purchase.  Recording that the cheaper route is
EMPTY is as much a result as finding one would have been (§3.2), and it is
recorded here so the class claim and its evidence cannot drift apart.
"""
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.math_compile import compile_math_reading      # noqa: E402
from generators.math_eval import (                            # noqa: E402
    conclusion_holds, eval_term, hypotheses_hold)
from generators.math_reading import (                         # noqa: E402
    BadMathReading, FragmentMiss, MATH_OPERATORS, parse_math_reading)
from generators.math_smt import render_term                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The signal under measurement, and its sibling on the same subjects.
SIGNAL = "function-symbol"
SIBLING = "symbolic-exponent"

#: The subjects, keyed by the SHORT LABEL used throughout this file.  The
#: values are the corpus coordinates ONLY -- prose is never transcribed here,
#: it is re-derived from the primary artifact by content hash below, so this
#: table can go stale about a node's identity but never about its words.
SUBJECTS = {
    "edge-disjoint": ("equational_theories", "edge-disjoint"),
    "p005": ("math2001", "06_Induction#problem-005"),
    "p006": ("math2001", "06_Induction#problem-006"),
    "p007": ("math2001", "06_Induction#problem-007"),
    "p009": ("math2001", "06_Induction#problem-009"),
    "p010": ("math2001", "06_Induction#problem-010"),
    "p011": ("math2001", "06_Induction#problem-011"),
    "p012": ("math2001", "06_Induction#problem-012"),
    "p015": ("math2001", "06_Induction#problem-015"),
    "p016": ("math2001", "06_Induction#problem-016"),
    "t010": ("math2001", "06_Induction#theorem-010"),
}

#: The CLASSIFICATION this file measures, one row per subject.  "function
#: symbol" is not one demand and the whole point of the exercise is to stop
#: the row pricing it as though it were:
#:   already-expressible -- the fragment has the word; what refused was the
#:                          reading's shape against that sentence, not a
#:                          missing capability;
#:   literal-index       -- expressible today at a literal index (the
#:                          definitional-unfolding shape); at the stated
#:                          generality it is held by a SYMBOLIC INDEX, which
#:                          is a different demand with a different row;
#:   needs-mechanism     -- no unfolding reaches it at any index, because the
#:                          function is not definable in the fragment at all.
#: `returned_by_p8` is the SEPARATE question -- would the row as declared,
#: bought alone, release this subject -- and the two columns disagree on
#: purpose.  `edge-disjoint` is the case that makes the distinction earn its
#: keep: it genuinely needs a mechanism, but the mechanism is a MAGMA CARRIER
#: (its `L_y` is a left translation, not an arithmetic function) plus the
#: symbolic exponent, so a named function symbol over Nat/Int returns it no
#: more than an unfolding does.  It is filed under this signal by accident of
#: vocabulary; the census reports signals, never verdicts.
CLASSIFICATION = {
    # the Bezout row: gcd is a lexicon word, the coefficients are an
    # existential the fragment already binds
    "t010": {"class": "already-expressible", "returned_by_p8": True},
    # factorial: `bigprod` at a literal bound, held by `bigop:symbolic-bound`
    "p009": {"class": "literal-index", "returned_by_p8": True},
    "p010": {"class": "literal-index", "returned_by_p8": False},
    # the recurrences: defining hypotheses at a literal index
    "p005": {"class": "literal-index", "returned_by_p8": True},
    "p006": {"class": "literal-index", "returned_by_p8": True},
    "p011": {"class": "literal-index", "returned_by_p8": False},
    "p012": {"class": "literal-index", "returned_by_p8": True},
    "p015": {"class": "literal-index", "returned_by_p8": False},
    "p016": {"class": "literal-index", "returned_by_p8": False},
    "p007": {"class": "literal-index", "returned_by_p8": False},
    # the magma left-translation: a carrier we do not have, filed here by
    # accident of vocabulary -- a named function over Nat/Int gives no magma
    "edge-disjoint": {"class": "needs-mechanism", "returned_by_p8": False},
}

#: What the row bought would return, counted off `returned_by_p8`.  Pinned as
#: a number so a re-reading of the slice has to move it deliberately.
P8_CEILING = 5

#: The lines the finding QUOTES, each with the file it was read from.  A
#: measurement that quotes a line the tree no longer contains has stopped
#: being a measurement, so the quotes are re-read below rather than trusted.
BLOCKING_LINES = {
    "generators/math_reading.py": (
        # the factorial subject's real refusal -- P1's bound freeze
        "bound must be a LITERAL -- bounded iteration ",
        # the Bezout node's real refusal -- groundedness, not capability
        "does not occur in the source ",
        # the sibling signal that independently holds six of the eleven
        "^ requires a non-negative LITERAL exponent (SMT-LIB has no ",
    ),
    "tools/FgReflect.lean": (
        # no application node, and every denotation decided by computation
        "inductive Tm where",
        "instance decDenote (env : Nat -> Int) : (p : Pd) -> "
        "Decidable (denote env p)",
    ),
}


# --------------------------------------------------------------------------- #
# The ledgers and the corpus, read rather than transcribed.
# --------------------------------------------------------------------------- #
def _refusals():
    path = os.path.join(ROOT, "results", "frontier_refusals.jsonl")
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _frontier_nodes(signal):
    with open(os.path.join(ROOT, "results", "frontier.json")) as fh:
        frontier = json.load(fh)
    for row in frontier["blocked"]:
        if row["signal"] == f"refused:{signal}":
            return row["nodes"]
    raise AssertionError(f"refused:{signal} is not a blocked frontier row")


def _corpus_prose():
    """(corpus, label) -> prose, and sha256(prose) -> (corpus, label), for the
    two corpora the eleven subjects live in.  The hash is the join key the
    refusal ledger itself uses, so nothing here re-invents an identity."""
    by_label, by_sha = {}, {}
    for corpus in sorted({c for c, _ in SUBJECTS.values()}):
        path = os.path.join(ROOT, "specs", "mathsources", corpus, "nodes.jsonl")
        with open(path) as fh:
            for line in fh:
                if not line.strip():
                    continue
                node = json.loads(line)
                prose = node.get("prose", "")
                by_label[(corpus, node["label"])] = prose
                by_sha[hashlib.sha256(prose.encode()).hexdigest()] = \
                    (corpus, node["label"])
    return by_label, by_sha


PROSE_BY_LABEL, LABEL_BY_SHA = _corpus_prose()


def prose(label):
    """The subject's words, straight off the corpus artifact."""
    return PROSE_BY_LABEL[SUBJECTS[label]]


def _reading(theorem, source, statements):
    """The gate, called exactly as the pipeline calls it."""
    doc = json.dumps({"theorem": theorem, "statements": statements})
    return parse_math_reading(doc, source)


# --------------------------------------------------------------------------- #
# (0) The subject set is the ledger's, not this file's.
# --------------------------------------------------------------------------- #
def test_the_eleven_subjects_are_exactly_the_refusal_ledger_rows():
    """The join the row's price rests on, re-run: every `function-symbol`
    refusal resolves through the corpus content hash to one of the subjects
    classified below, and there are no others.  A re-census that retires a
    subject fails HERE rather than leaving the classification quietly
    describing a slice that moved."""
    shas = [r["subject_sha256"] for r in _refusals() if r["signal"] == SIGNAL]
    assert len(shas) == 11, f"the row prices 11 refusals; the ledger has {len(shas)}"
    resolved = sorted(SUBJECTS[k] for k in SUBJECTS)
    got = sorted(LABEL_BY_SHA[s] for s in shas)
    assert got == resolved, f"the ledger's subjects are not the classified ones: {got}"
    # and the derived frontier row agrees about the same eleven nodes
    nodes = _frontier_nodes(SIGNAL)
    assert len(nodes) == 11
    assert sorted((n["corpus"], n["node_id"]) for n in nodes) == resolved
    assert set(CLASSIFICATION) == set(SUBJECTS), \
        "every refused subject must carry a class -- an unclassified subject " \
        "is exactly the unpriced reach the row was declared on"


# --------------------------------------------------------------------------- #
# (1) The price: six of eleven are held by a second, independent refusal.
# --------------------------------------------------------------------------- #
def test_six_of_eleven_carry_the_symbolic_exponent_refusal_as_well():
    """The row prices eleven subjects against one mechanism.  Six of them are
    ALSO refused for `symbolic-exponent`, which no function-symbol node
    touches -- so the mechanism's honest ceiling is five, and the six are
    demand the sibling row already carries.  Overlapping signals never sum to
    a node total (the frontier's own honesty note); here the overlap is the
    finding."""
    by_sha = {}
    for row in _refusals():
        by_sha.setdefault(row["subject_sha256"], set()).add(row["signal"])
    co_signalled = set()
    for sha, signals in by_sha.items():
        if SIGNAL in signals and SIBLING in signals:
            co_signalled.add(LABEL_BY_SHA[sha])
    assert len(co_signalled) == 6, sorted(co_signalled)
    labels = {lbl for lbl, coord in SUBJECTS.items() if coord in co_signalled}
    assert labels == {"edge-disjoint", "p007", "p010", "p011", "p015", "p016"}
    # none of the six is claimed as returned by the mechanism under measurement
    for lbl in labels:
        assert not CLASSIFICATION[lbl]["returned_by_p8"], \
            f"{lbl} is held by a symbolic exponent; a function symbol does " \
            f"not release it, and pricing it here double-counts the subject"
    returned = [l for l, c in CLASSIFICATION.items() if c["returned_by_p8"]]
    assert len(returned) == P8_CEILING, sorted(returned)


def test_a_symbolic_exponent_refuses_on_its_own_account():
    """The independence claim above, measured at the gate rather than read off
    the ledger: strip every named function out of `a_n = 2^n + (-1)^n` -- let
    the sequence value be a bare declared object -- and the reading still
    refuses, on the exponent.  So the six co-signalled subjects stay refused
    whatever P8 buys."""
    src = prose("p011")
    with pytest.raises(BadMathReading) as excinfo:
        _reading("p011_symbolic", src, [
            {"id": "amb", "force": "choice", "quote": "",
             "lf": {"kind": "ambient", "carrier": "Int"}},
            {"id": "on", "force": "demand",
             "quote": "for all natural numbers \\(n\\)",
             "lf": {"kind": "object", "name": "n", "type": "Int"}},
            {"id": "oa", "force": "choice", "quote": "",
             "lf": {"kind": "object", "name": "an", "type": "Int"}},
            {"id": "q", "force": "demand",
             "quote": "for all natural numbers \\(n\\)",
             "lf": {"kind": "quantifier", "binder": "forall",
                    "objects": ["n"]}},
            {"id": "c", "force": "demand", "quote": "\\(a_n=2^n+(-1)^n\\)",
             "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
                 {"ref": "an"},
                 {"op": "+", "args": [
                     {"op": "^", "args": [{"lit": 2}, {"ref": "n"}]},
                     {"op": "^", "args": [{"lit": -1}, {"ref": "n"}]}]}]}}},
        ])
    assert "exponent" in str(excinfo.value), str(excinfo.value)


# --------------------------------------------------------------------------- #
# (2a) Factorial: the fragment's word for it is `bigprod`, bought at P1.
# --------------------------------------------------------------------------- #
#: `6!` in the fragment.  Not a function application: P1's bounded fold, whose
#: literal bounds are the whole reason the class is decidable.
FACTORIAL_6 = {"op": "bigprod",
               "args": [{"var": "i"}, {"lit": 1}, {"lit": 6}, {"ref": "i"}]}

#: A paraphrase source for the literal-index instance.  The instance is a
#: PROBE, not a corpus node, and it is spelled out in words so every demand
#: below quotes a span the sentence actually contains -- groundedness is not
#: something a measurement gets to waive for itself.
FACTORIAL_SRC = ("Every natural number d with 1 <= d <= 6 is a factor of 6 "
                 "factorial, the product of the integers from 1 to 6.")

FACTORIAL_STATEMENTS = [
    {"id": "amb", "force": "choice", "quote": "",
     "lf": {"kind": "ambient", "carrier": "Nat"}},
    {"id": "od", "force": "demand", "quote": "Every natural number d",
     "lf": {"kind": "object", "name": "d", "type": "Nat"}},
    {"id": "opd", "force": "choice", "quote": "",
     "lf": {"kind": "operator", "word": "dvd", "carrier": "Nat"}},
    {"id": "qd", "force": "demand",
     "quote": "Every natural number d with 1 <= d <= 6",
     "lf": {"kind": "quantifier", "binder": "forall", "objects": ["d"]}},
    {"id": "h", "force": "presupposition", "quote": "1 <= d <= 6",
     "lf": {"kind": "hypothesis", "pred": {"op": "and", "args": [
         {"op": "<=", "args": [{"lit": 1}, {"ref": "d"}]},
         {"op": "<=", "args": [{"ref": "d"}, {"lit": 6}]}]}}},
    {"id": "c", "force": "demand",
     "quote": "is a factor of 6 factorial, the product of the integers from 1 to 6",
     "lf": {"kind": "conclusion",
            "pred": {"op": "dvd", "args": [{"ref": "d"}, FACTORIAL_6]}}},
]


def test_factorial_is_bigprod_and_rides_all_four_channels_unchanged():
    """The row's first exemplar, measured.  `n!` at a literal `n` is not a
    function the fragment lacks a word for -- it is P1's `bigprod`, and it
    passes the gate, the evaluator, the compiler and the SMT mirror with no
    node any of them did not already carry."""
    reading = _reading("factorial_literal", FACTORIAL_SRC, FACTORIAL_STATEMENTS)
    assert eval_term(FACTORIAL_6, {}, {"d": "Nat"}, "Nat") == 720
    for d in range(1, 7):
        assert conclusion_holds(reading, {"d": d}), d
    # a divisor OUTSIDE the hypothesis that does not divide 720, so the
    # conclusion is a claim about the value and not a tautology of the shape
    assert not conclusion_holds(reading, {"d": 7})
    lean = compile_math_reading(reading)["lean_text"]
    assert "Finset.prod (Finset.Icc 1 6)" in lean, lean
    assert render_term(FACTORIAL_6, {"d": "Nat"}, "Nat") == "(* 1 2 3 4 5 6)"


def test_the_factorial_subject_refuses_for_a_symbolic_BOUND():
    """The FAITHFUL reading of the factorial subject at its stated generality
    -- no instantiation, no weakening, `n!` transcribed as the fold it is --
    and the refusal it earns.  `bigop:symbolic-bound` is P1's own freeze and
    the demand the census prices under `sequences-sums`; it is not, and was
    never, a missing word for a named function.  This is the single line that
    moves the subject off the P8 row."""
    src = prose("p009")
    with pytest.raises(FragmentMiss) as excinfo:
        _reading("p009_symbolic", src, [
            {"id": "amb", "force": "choice", "quote": "",
             "lf": {"kind": "ambient", "carrier": "Nat"}},
            {"id": "on", "force": "demand",
             "quote": "Let \\(n\\) be a natural number",
             "lf": {"kind": "object", "name": "n", "type": "Nat"}},
            {"id": "od", "force": "demand",
             "quote": "every natural number \\(d\\)",
             "lf": {"kind": "object", "name": "d", "type": "Nat"}},
            {"id": "opd", "force": "choice", "quote": "",
             "lf": {"kind": "operator", "word": "dvd", "carrier": "Nat"}},
            {"id": "qn", "force": "demand",
             "quote": "Let \\(n\\) be a natural number",
             "lf": {"kind": "quantifier", "binder": "forall",
                    "objects": ["n"]}},
            {"id": "qd", "force": "demand",
             "quote": "every natural number \\(d\\) with \\(1\\le d\\le n\\)",
             "lf": {"kind": "quantifier", "binder": "forall",
                    "objects": ["d"]}},
            {"id": "h", "force": "presupposition",
             "quote": "\\(1\\le d\\le n\\)",
             "lf": {"kind": "hypothesis", "pred": {"op": "and", "args": [
                 {"op": "<=", "args": [{"lit": 1}, {"ref": "d"}]},
                 {"op": "<=", "args": [{"ref": "d"}, {"ref": "n"}]}]}}},
            {"id": "c", "force": "demand",
             "quote": "is a factor of \\(n!\\)",
             "lf": {"kind": "conclusion", "pred": {"op": "dvd", "args": [
                 {"ref": "d"},
                 {"op": "bigprod", "args": [{"var": "i"}, {"lit": 1},
                                            {"ref": "n"}, {"ref": "i"}]}]}}},
        ])
    assert excinfo.value.missing_kind_guess == "bigop:symbolic-bound"


# --------------------------------------------------------------------------- #
# (2b) The Bezout coefficients: Skolem witnesses of an existential we bind.
# --------------------------------------------------------------------------- #
def _bezout_statements(q_forall, q_exists, q_concl):
    return [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "demand", "quote": q_forall,
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "demand", "quote": q_forall,
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "ox", "force": "demand", "quote": q_exists,
         "lf": {"kind": "object", "name": "x", "type": "Int"}},
        {"id": "oy", "force": "demand", "quote": q_exists,
         "lf": {"kind": "object", "name": "y", "type": "Int"}},
        {"id": "opg", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "gcd", "carrier": "Int"}},
        {"id": "qf", "force": "demand", "quote": q_forall,
         "lf": {"kind": "quantifier", "binder": "forall",
                "objects": ["a", "b"]}},
        {"id": "qe", "force": "demand", "quote": q_exists,
         "lf": {"kind": "quantifier", "binder": "exists",
                "objects": ["x", "y"]}},
        {"id": "c", "force": "demand", "quote": q_concl,
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [
                 {"op": "*", "args": [{"ref": "a"}, {"ref": "x"}]},
                 {"op": "*", "args": [{"ref": "b"}, {"ref": "y"}]}]},
             {"op": "gcd", "args": [{"ref": "a"}, {"ref": "b"}]}]}}},
    ]


def test_the_bezout_coefficients_are_already_expressible():
    """The row's third exemplar, measured against the repo's OWN Bezout source
    -- `specs/mathsources/42_bezout_identity.txt`, committed long before this
    question was asked.  `gcd` is a `MATH_OPERATORS` term word at `Int` and
    the fragment binds `exists`, so the identity parses today, and the
    evaluator witnesses it at EVERY pair in the box: the reading is not merely
    well-formed, it is true of the arithmetic the evaluator computes."""
    assert MATH_OPERATORS["gcd"]["role"] == "term"
    assert "Int" in MATH_OPERATORS["gcd"]["lean"]
    src_path = os.path.join(ROOT, "specs", "mathsources",
                            "42_bezout_identity.txt")
    with open(src_path) as fh:
        source = fh.read()
    reading = _reading("bezout_identity", source, _bezout_statements(
        "Here a and b are integers",
        "There exist integers x and y",
        "a times x plus b times y equals the greatest common divisor of a and b"))
    box = range(-6, 7)
    unwitnessed = []
    for a in box:
        for b in box:
            if not any(conclusion_holds(reading, {"a": a, "b": b,
                                                  "x": x, "y": y})
                       for x in range(-12, 13) for y in range(-12, 13)):
                unwitnessed.append((a, b))
    assert not unwitnessed, f"Bezout unwitnessed at {unwitnessed[:5]}"
    assert len(box) ** 2 == 169


def test_bezout_against_its_own_node_refuses_on_GROUNDEDNESS():
    """...and the honest other half, which is why the subject sits in the
    ledger at all.  The math2001 node states the identity with the two
    recursive coefficient functions BY NAME, and its sentence contains no
    existential span, so the witnessing reading above cannot be grounded in
    it: the gate refuses the fabricated quote, exactly as it should.  That is
    a fact about this sentence's shape -- what it chooses to name -- and not
    about the fragment's reach, and the distinction is the whole content of
    the `already-expressible` class."""
    src = prose("t010")
    assert "L(a,b)" in src and "exist" not in src.lower()
    with pytest.raises(BadMathReading) as excinfo:
        _reading("t010_skolemised", src, _bezout_statements(
            "For all integers \\(a\\) and \\(b\\)",
            "there exist integers x and y",
            "\\[L(a,b)a+R(a,b)b=\\operatorname{gcd}(a,b).\\]"))
    msg = str(excinfo.value)
    assert "does not occur in the source" in msg, msg
    assert not isinstance(excinfo.value, FragmentMiss), \
        "a groundedness refusal is not demand data for a fragment purchase " \
        "-- filing it as one is how a row buys reach it does not need"


# --------------------------------------------------------------------------- #
# (3) The recurrences at a literal index: definitional unfolding.
# --------------------------------------------------------------------------- #
def _obj(name):
    return {"id": f"o_{name}", "force": "choice", "quote": "",
            "lf": {"kind": "object", "name": name, "type": "Int"}}


def _hyp(sid, quote, pred):
    return {"id": sid, "force": "presupposition", "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


#: `a_{k+1} = a_k + 2 a_{k-1}`, `a_0 = 2`, `a_1 = 1` -- the math2001 sequence
#: whose closed form is `2^n + (-1)^n`.  At index 5: 2, 1, 5, 7, 17, 31, and
#: `2^5 + (-1)^5 = 31`.  Nothing here is a function application: the sequence
#: values are DECLARED OBJECTS and the recurrence is four ordinary equations.
P011_SRC = ("The sequence a is defined by a0 = 2, a1 = 1 and a2 = a1 + 2 a0, "
            "a3 = a2 + 2 a1, a4 = a3 + 2 a2, a5 = a4 + 2 a3. "
            "Then a5 = 2 to the power 5 plus negative 1 to the power 5.")
P011_TRUE = {"a0": 2, "a1": 1, "a2": 5, "a3": 7, "a4": 17, "a5": 31}


def _p011_reading():
    def step(hi, prev, prev2):
        return {"op": "=", "args": [
            {"ref": hi},
            {"op": "+", "args": [{"ref": prev},
                                 {"op": "*", "args": [{"lit": 2},
                                                      {"ref": prev2}]}]}]}
    stmts = [{"id": "amb", "force": "choice", "quote": "",
              "lf": {"kind": "ambient", "carrier": "Int"}}]
    stmts += [_obj(f"a{n}") for n in range(6)]
    stmts += [
        _hyp("h0", "a0 = 2",
             {"op": "=", "args": [{"ref": "a0"}, {"lit": 2}]}),
        _hyp("h1", "a1 = 1",
             {"op": "=", "args": [{"ref": "a1"}, {"lit": 1}]}),
        _hyp("h2", "a2 = a1 + 2 a0", step("a2", "a1", "a0")),
        _hyp("h3", "a3 = a2 + 2 a1", step("a3", "a2", "a1")),
        _hyp("h4", "a4 = a3 + 2 a2", step("a4", "a3", "a2")),
        _hyp("h5", "a5 = a4 + 2 a3", step("a5", "a4", "a3")),
        {"id": "c", "force": "demand",
         "quote": "a5 = 2 to the power 5 plus negative 1 to the power 5",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"ref": "a5"},
             {"op": "+", "args": [
                 {"op": "^", "args": [{"lit": 2}, {"lit": 5}]},
                 {"op": "^", "args": [{"lit": -1}, {"lit": 5}]}]}]}}},
    ]
    return _reading("recurrence_literal_index", P011_SRC, stmts)


def test_a_recurrence_at_a_literal_index_unfolds_into_the_existing_fragment():
    """The source-121/122 shape, on the row's second exemplar: a sequence
    value DEFINED AT THE POINT OF USE by in-fragment equations is a declared
    object, and the named function vanishes in the unfolding.  The gate
    admits it and the evaluator agrees on the nose -- and refutes both one-off
    perturbations, so the agreement is about the arithmetic and not about the
    shape."""
    reading = _p011_reading()
    assert hypotheses_hold(reading, P011_TRUE)
    assert conclusion_holds(reading, P011_TRUE)
    for wrong in (30, 32):
        perturbed = dict(P011_TRUE, a5=wrong)
        assert not hypotheses_hold(reading, perturbed), wrong
        assert not conclusion_holds(reading, perturbed), wrong


def test_the_congruence_recurrences_unfold_the_same_way():
    """The two subjects the symbolic exponent does NOT also hold -- `x_n ≡ 1
    mod 4` and `a_m ≡ 1 or 5 mod 6`.  `%` and `or` are both in the fragment,
    so once the index is literal there is nothing left for a purchase to
    supply; these are the subjects whose whole remaining demand is the index."""
    # x_0 = 5, x_{k+1} = 2 x_k - 1  (closed form 2^{n+2} + 1); x_3 = 33
    src = ("The sequence x is defined by x0 = 5 and x1 = 2 x0 - 1, "
           "x2 = 2 x1 - 1, x3 = 2 x2 - 1. "
           "Then the remainder of x3 on division by 4 is 1.")

    def step(hi, prev):
        return {"op": "=", "args": [
            {"ref": hi},
            {"op": "-", "args": [{"op": "*", "args": [{"lit": 2},
                                                      {"ref": prev}]},
                                 {"lit": 1}]}]}
    stmts = [{"id": "amb", "force": "choice", "quote": "",
              "lf": {"kind": "ambient", "carrier": "Int"}}]
    stmts += [_obj(f"x{n}") for n in range(4)]
    stmts += [
        _hyp("h0", "x0 = 5", {"op": "=", "args": [{"ref": "x0"}, {"lit": 5}]}),
        _hyp("h1", "x1 = 2 x0 - 1", step("x1", "x0")),
        _hyp("h2", "x2 = 2 x1 - 1", step("x2", "x1")),
        _hyp("h3", "x3 = 2 x2 - 1", step("x3", "x2")),
        {"id": "c", "force": "demand",
         "quote": "the remainder of x3 on division by 4 is 1",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "%", "args": [{"ref": "x3"}, {"lit": 4}]}, {"lit": 1}]}}},
    ]
    reading = _reading("congruence_recurrence", src, stmts)
    true = {"x0": 5, "x1": 9, "x2": 17, "x3": 33}
    assert hypotheses_hold(reading, true)
    assert conclusion_holds(reading, true)
    assert not conclusion_holds(reading, dict(true, x3=34))


def test_a_recurrence_at_a_SYMBOLIC_index_states_something_else_entirely():
    """The half of the measurement that does NOT overturn the declaration, and
    the reason the class survives.  Drop the index -- let `b_n` be a declared
    object, which is the only thing the fragment can do with it -- and the
    reading PASSES the gate while asserting a different proposition: the
    object is unconstrained, and the evaluator produces counterexamples the
    source's claim does not have.  A reading that certifies while meaning
    something weaker is worse than a refusal, which is exactly why the
    indexed family cannot be faked and why the demand is real."""
    src = prose("p005")
    reading = _reading("p005_symbolic", src, [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "on", "force": "demand", "quote": "for all \\(n\\)",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "ob", "force": "demand", "quote": "the integer \\(b_n\\)",
         "lf": {"kind": "object", "name": "bn", "type": "Int"}},
        {"id": "opo", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "odd", "carrier": "Int"}},
        {"id": "q", "force": "demand", "quote": "for all \\(n\\)",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "c", "force": "demand",
         "quote": "the integer \\(b_n\\) is odd",
         "lf": {"kind": "conclusion",
                "pred": {"op": "odd", "args": [{"ref": "bn"}]}}},
    ])
    counterexamples = [(n, b) for n in range(3) for b in range(5)
                       if not conclusion_holds(reading, {"n": n, "bn": b})]
    assert len(counterexamples) == 9, counterexamples
    assert (0, 0) in counterexamples


# --------------------------------------------------------------------------- #
# (4) The additive discriminator, read off the artifact.
# --------------------------------------------------------------------------- #
#: `tools/FgReflect.lean`'s term constructors, as the file actually spells
#: them.  The discriminator §3.1 rule 3(a) asks for is whether the smallest
#: useful version adds one of these -- so the list is asserted, not assumed.
FGREFLECT_TM_CONSTRUCTORS = ("lit", "tvar", "add", "sub", "mul", "tmod")


def test_a_function_symbol_forces_a_constructor_and_a_decidable_story():
    """Why the class verdict SURVIVES the price correction.  `Tm` carries six
    constructors and not one of them applies anything to anything: an
    application node is new structure, which is §3.1 rule 3(a)'s tower-class
    criterion outright.  Worse for the bill, `decDenote` decides every `Pd` BY
    COMPUTATION over `evalTm`, and an uninterpreted symbol constrained only by
    axioms has no computable value -- so the rung would owe a new `Decidable`
    story as well, not merely a new case.  Neither cost is reachable by an
    additive purchase, and that is the whole of the answer to `is the P8 row
    attended-only`: yes, and for this reason rather than the one it gives."""
    with open(os.path.join(ROOT, "tools", "FgReflect.lean")) as fh:
        lean = fh.read()
    head = lean.split("inductive Tm where", 1)[1].split("inductive Pd", 1)[0]
    declared = tuple(line.split("|", 1)[1].split(":", 1)[0].strip()
                     for line in head.splitlines()
                     if line.strip().startswith("| "))
    assert declared == FGREFLECT_TM_CONSTRUCTORS, declared
    # no constructor takes a function into a term: every argument position is
    # a BARE `Int`, `Nat` or `Tm`, so there is nowhere in the type for an
    # applied symbol -- or for the environment one would have to be read from
    # -- to live.  This is the constructor-shape check, not a name check.
    for line in head.splitlines():
        if not line.strip().startswith("| "):
            continue
        signature = line.split(":", 1)[1]
        for token in signature.replace("->", " ").split():
            assert token in ("Int", "Nat", "Tm"), (line, token)
    assert "instance decDenote" in lean
    assert "def evalTm" in lean


def test_the_quoted_blocking_lines_are_still_in_their_sources():
    """The finding quotes source lines; this re-reads them.  A quote that has
    drifted out of the tree is a claim about a repo that no longer exists, and
    it should fail here rather than survive in prose."""
    for relpath, lines in BLOCKING_LINES.items():
        with open(os.path.join(ROOT, relpath)) as fh:
            text = fh.read()
        for line in lines:
            assert line in text, f"{relpath}: quoted line has drifted: {line!r}"


def test_the_smallest_useful_version_is_not_reachable_additively():
    """The bill, stated as an assertion about the classification rather than
    as prose.  No subject in the slice is returned by an additive purchase:
    the `already-expressible` and `literal-index` rows are already reachable
    (and so buy nothing when bought), and everything that remains is held by
    a symbolic index, a symbolic exponent, or a carrier we do not have.
    Recording an EMPTY cheaper route is a §3.2 result; leaving the row's
    eleven-wide price standing would not be."""
    classes = {lbl: row["class"] for lbl, row in CLASSIFICATION.items()}
    assert sum(1 for c in classes.values() if c == "already-expressible") == 1
    assert sum(1 for c in classes.values() if c == "literal-index") == 9
    assert sum(1 for c in classes.values() if c == "needs-mechanism") == 1
    # the ceiling: five subjects, and the six the sibling signal holds are not
    # among them
    returned = {l for l, r in CLASSIFICATION.items() if r["returned_by_p8"]}
    assert returned == {"t010", "p005", "p006", "p009", "p012"}
    assert len(returned) == P8_CEILING < len(SUBJECTS)

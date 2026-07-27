"""SET OBJECTS over the CURRENT fragment: what is the P9 row's bill really,
and what does it really return?

THE QUESTION THIS FILE ANSWERS MECHANICALLY.  `results/purchase_frontier.json`
carries a row `refusal-set-carrier` declared `bill_class: "tower-class"` and
priced at four blocking refusals, with the prose "P2 bought `setbuild` only as
`card`'s ARGUMENT, so a set can be COUNTED but never inhabited, named, or
compared".  A tower-class bill is attended-only under PLAN_FRAGMENT §3.1
rule 3 unless the container reads `lean-local`, so the declaration is
load-bearing for whether an unattended session may turn this row at all.  P6 is
the precedent for refusing to settle such a declaration by preference (`not`
was declared tower-class on the ASSUMPTION it needed a `Pd` constructor, and
`tests/test_nnf_duals.py` measured that it pushes to duals the fragment already
had); P8 is the precedent for the row splitting in two under measurement.
Which bill P9 really is -- and, separately, which subjects it really returns --
are two FACTS ABOUT THE SLICE, and they are measured here rather than argued.

WHAT COUNTS AS A PROOF HERE.  Every claim below is asserted against the repo's
OWN machinery -- the gate `generators.math_reading.parse_math_reading` and the
evaluator `generators.math_eval` -- never against a re-implementation of the
fragment's semantics.  The subject set is not transcribed either: it is read
out of `results/frontier_refusals.jsonl` and `results/frontier.json` and the
prose is re-derived from the primary corpus artifacts by content hash, so a
re-census that moves a subject moves this file's answer with it instead of
leaving a stale claim behind.  Offline, deterministic, Lean-free.

THE FINDING, in the order the tests below establish it.

  (1) THE ROW IS TWO ROWS.  The mechanism the four subjects need splits at a
      line the row's own prose already draws and then prices as one thing:
      a set the source GIVES A COMPREHENSION FOR versus a set it does not.
      The first is ELIMINABLE -- `e in {x | phi(x)}` IS `phi(e)`, so the
      membership never reaches a consumer and nothing enters `Tm`/`Pd`.  That
      half is additive-desugaring, P8's shape exactly, and it is what P9
      buys.  The second is not eliminable at any price: an arbitrary `U` has
      no body to substitute, so membership in it SURVIVES unfolding.  That
      half is the genuine tower-class purchase, and it stays OPEN, priced
      under `set:free-set-variable` and `set:set-valued-param`.

  (2) ONLY ONE OF THE FOUR SUBJECTS NEEDS THE TOWER-CLASS HALF, and it is the
      one the row's prose leads with.  `09_Sets#definition-003` defines
      intersection over two ARBITRARY sets `U` and `V` in a type `X`; there is
      no comprehension anywhere in it to substitute.  It is held, and this
      file measures that it is held by the residue rather than by the
      mechanism P9 buys.

  (3) TWO OF THE REMAINING THREE ARE NOT BLOCKED BY VOCABULARY AT ALL, and
      this is the sharpest thing measured here because it lowers the row's
      real price rather than raising it.  `09_Sets#problem-014` and
      `#problem-015` each state a relation between a comprehension over ℤ and
      a comprehension over ℕ.  The fragment reads ONE carrier per reading
      (`rat:no-coercion`'s rule, generalised), so either the mismatch is a
      transcription artifact of the extraction -- in which case reading it at
      a single carrier is a CHOICE a corpus cycle must make and defend -- or
      it is what the source says, in which case no set purchase reaches it.
      And `#problem-015` is worse than blocked: read at a single carrier its
      two comprehensions are the SAME SET, so the claimed empty intersection
      is FALSE, and the evaluator refutes it below at n = 1, 6, 11, ...  A
      subject whose blocker is a TRUTH FACT is not demand for any primitive,
      and no purchase on the board returns it.

  (4) THE ONE SUBJECT THIS BILL PLAINLY REACHES IT REACHES DEGENERATELY.
      `09_Sets#problem-017` (`{n | n even} notin {s | 3 in s}`) is a powerset
      comprehension, and read FAITHFULLY it needs `set:set-valued-param` --
      the residue again.  But its outer membership is at a LITERAL set, so it
      unfolds definitionally to `not (3 in {n | n even})` and then to
      `odd 3` -- the cycle-16 source-121 pattern exactly, and cycle 16 already
      recorded that such a green is coverage and NOT evidence of set
      coverage.  Whether to take it that way is a corpus cycle's call; what is
      measured here is only that P9 makes it EXPRESSIBLE, where before the
      gate refused at `mem` outright.

  So the four-subject price is honest as a COUNT and misleading as a
  FORECAST, and the refill of record is the next corpus cycle's `--unblocked
  refused:set-membership` run, exactly as P8's was.  Nothing here raises a
  number on a projection.
"""
import hashlib
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from generators import math_eval as ME  # noqa: E402
from generators import math_reading as MR  # noqa: E402

SIGNAL = "set-membership"


# --------------------------------------------------------------------------- #
# The subject set, READ from the committed artifacts rather than transcribed.
# --------------------------------------------------------------------------- #
def _refused_shas():
    """Every subject the ledger demoted under this row's signal."""
    path = os.path.join(HERE, "results", "frontier_refusals.jsonl")
    out = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                if row.get("signal") == SIGNAL:
                    out.add(row["subject_sha256"])
    return out


def _corpus_prose():
    """text_sha256 -> (corpus, node_id, prose) over the whole portfolio, so a
    subject is matched by CONTENT and never by a label this file wrote down."""
    root = os.path.join(HERE, "specs", "mathsources")
    out = {}
    for corpus in sorted(os.listdir(root)):
        nodes = os.path.join(root, corpus, "nodes.jsonl")
        if not os.path.exists(nodes):
            continue
        with open(nodes, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                n = json.loads(line)
                prose = n.get("prose")
                if isinstance(prose, str):
                    sha = hashlib.sha256(prose.encode("utf-8")).hexdigest()
                    out[sha] = (corpus, n.get("label"), prose)
    return out


def _subjects():
    """The row's subjects as {label: prose}, derived end to end."""
    prose = _corpus_prose()
    out = {}
    for sha in _refused_shas():
        if sha in prose:
            _, label, text = prose[sha]
            out[label] = text
    return out


def test_the_row_prices_exactly_the_subjects_this_file_reasons_about():
    """The derivation tooth: if a re-census moves the group, this file's
    answer must move with it rather than keep asserting about a set that is no
    longer there.  Four subjects, all in `09_Sets`, all recovered by content
    hash from the primary artifacts."""
    subs = _subjects()
    assert set(subs) == {"09_Sets#definition-003", "09_Sets#problem-014",
                         "09_Sets#problem-015", "09_Sets#problem-017"}, \
        sorted(subs)
    assert all(lbl.startswith("09_Sets#") for lbl in subs)


# --------------------------------------------------------------------------- #
# (1) The row is two rows: eliminable comprehension vs. arbitrary set.
# --------------------------------------------------------------------------- #
def _reading(statements, src, theorem="cls"):
    return MR.parse_math_reading(
        json.dumps({"theorem": theorem, "statements": statements}), src)


def _base(src, carrier="Int", objects=("n",)):
    out = [{"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}]
    out += [{"id": f"o{o}", "force": "choice", "quote": "",
             "lf": {"kind": "object", "name": o, "type": carrier}}
            for o in objects]
    return out


def test_a_named_comprehension_is_eliminable_and_a_free_set_is_not():
    """FINDING (1), the whole split, in one test and against the gate itself.

    Same sentence, same membership, one difference: whether the set has a
    comprehension.  With one, the gate returns a pred in the PRE-P9 fragment
    (the body at the element) -- so no consumer learns anything and no
    constructor is needed.  Without one, the gate refuses, because there is
    nothing to substitute and the membership would have to be REPRESENTED."""
    src = "Let n be given and let a be a set. Then n is in a."
    body = {"op": "even", "args": [{"ref": "k"}]}
    with_body = _base(src) + [
        {"id": "opev", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "even", "carrier": "Int"}},
        {"id": "sd", "force": "choice", "quote": "",
         "lf": {"kind": "setdef", "name": "a", "param": "k", "body": body}},
        {"id": "c", "force": "demand", "quote": "n is in a",
         "lf": {"kind": "conclusion",
                "pred": {"op": "mem",
                         "args": [{"ref": "n"}, {"set": "a"}]}}}]
    concl = [s for s in _reading(with_body, src).statements
             if s["lf"]["kind"] == "conclusion"][0]["lf"]["pred"]
    assert concl == {"op": "even", "args": [{"ref": "n"}]}

    without_body = _base(src, objects=("n", "a")) + [
        {"id": "c", "force": "demand", "quote": "n is in a",
         "lf": {"kind": "conclusion",
                "pred": {"op": "mem",
                         "args": [{"ref": "n"}, {"set": "a"}]}}}]
    with pytest.raises(MR.FragmentMiss) as e:
        _reading(without_body, src)
    assert e.value.missing_kind_guess == "set:free-set-variable"


def test_the_eliminable_half_adds_no_constructor_to_the_reflect_slice():
    """Why FINDING (1)'s first half is additive-desugaring and not
    tower-class, checked as a property of the SLICE rather than asserted: the
    reflect slice's inductives carry no set and no membership, and after this
    purchase they still do not -- because nothing membership-shaped survives
    the gate to reach them."""
    slice_path = os.path.join(HERE, "tools", "FgReflect.lean")
    text = open(slice_path, encoding="utf-8").read()
    # the constructor lists are what a tower-class purchase would have to grow
    assert "mem" not in text.split("inductive Pd")[1].split("\n\n")[0]
    for banned in ("Set ", "Membership", "setOf"):
        assert banned not in text, banned


# --------------------------------------------------------------------------- #
# (2) definition-003 is the one subject that needs the residue.
# --------------------------------------------------------------------------- #
def test_definition_003_needs_arbitrary_sets_and_stays_held():
    """FINDING (2).  The subject defines intersection over two sets the source
    never gives bodies for; the prose is checked to say so, and the faithful
    reading is checked to refuse under the residue's signal -- not under any
    freeze P9 could relax."""
    prose = _subjects()["09_Sets#definition-003"]
    assert "two sets" in prose and "\\cap" in prose
    # ... and neither U nor V is given by a comprehension: the only brace in
    # the sentence is the DEFINIENS, whose body is the membership itself.
    assert prose.count("\\{") == 1

    src = prose
    stmts = _base(src, objects=("x", "u", "v")) + [
        {"id": "c", "force": "demand", "quote": "x \\in U \\land x \\in V",
         "lf": {"kind": "conclusion",
                "pred": {"op": "and", "args": [
                    {"op": "mem", "args": [{"ref": "x"}, {"set": "u"}]},
                    {"op": "mem", "args": [{"ref": "x"}, {"set": "v"}]}]}}}]
    with pytest.raises(MR.FragmentMiss) as e:
        _reading(stmts, src)
    assert e.value.missing_kind_guess == "set:free-set-variable"


# --------------------------------------------------------------------------- #
# (3) Two subjects are not blocked by vocabulary at all.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("label", ["09_Sets#problem-014", "09_Sets#problem-015"])
def test_the_carrier_mismatch_is_in_the_prose_itself(label):
    """FINDING (3), first half.  Each of these two states a relation between a
    comprehension over ℤ and one over ℕ.  A reading uses ONE carrier, so this
    mismatch is a fact about the SUBJECT that no set purchase touches -- and
    it is read off the committed prose rather than remembered."""
    prose = _subjects()[label]
    assert "\\mathbb{Z}" in prose and "\\mathbb{N}" in prose, prose


def test_problem_015_is_refuted_at_a_single_carrier():
    """FINDING (3), second half, and the sharpest measurement in this file.
    Collapse problem-015's carrier mismatch the only way a reading could --
    read both comprehensions at one carrier -- and its two set-builders become
    the SAME SET, so the claimed empty intersection is false.  The evaluator
    refutes it; a subject whose blocker is a TRUTH FACT is demand for no
    primitive, and naming it here stops a later cycle spending a purchase on
    it."""
    prose = _subjects()["09_Sets#problem-015"]
    # both comprehension bodies really are the same congruence, verbatim
    assert prose.count("n\\equiv 1\\mod 5") == 2, prose

    src = prose
    body = {"op": "=", "args": [
        {"op": "mod", "args": [{"ref": "k"}, {"lit": 5}]}, {"lit": 1}]}
    stmts = _base(src) + [
        {"id": "opm", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "mod", "carrier": "Int"}},
        {"id": "sa", "force": "choice", "quote": "",
         "lf": {"kind": "setdef", "name": "sa", "param": "k", "body": body}},
        {"id": "sb", "force": "choice", "quote": "",
         "lf": {"kind": "setdef", "name": "sb", "param": "k", "body": body}},
        {"id": "c", "force": "demand", "quote": "=\\emptyset",
         "lf": {"kind": "conclusion",
                "pred": {"op": "not", "args": [{"op": "and", "args": [
                    {"op": "mem", "args": [{"ref": "n"}, {"set": "sa"}]},
                    {"op": "mem", "args": [{"ref": "n"},
                                           {"set": "sb"}]}]}]}}}]
    concl = [s for s in _reading(stmts, src).statements
             if s["lf"]["kind"] == "conclusion"][0]["lf"]["pred"]
    # the gate ADMITS it -- the vocabulary is there now, which is the point --
    # and the evaluator then refutes it at every residue-1 point.
    witnesses = [n for n in range(-20, 21)
                 if ME.eval_pred(concl, {"n": n}, {"n": "Int"}, "Int") is False]
    assert witnesses, "the intersection is empty after all -- re-derive (3)"
    assert 1 in witnesses and 6 in witnesses and 11 in witnesses, witnesses


# --------------------------------------------------------------------------- #
# (4) problem-017 becomes expressible, degenerately.
# --------------------------------------------------------------------------- #
def test_problem_017_is_faithfully_the_residue_and_degenerately_reachable():
    """FINDING (4), both halves, because reporting either alone would mislead.

    Read FAITHFULLY -- the outer set as the comprehension the source writes,
    binding `s` over the powerset -- it refuses under `set:set-valued-param`,
    the residue.  Read by DEFINITIONAL UNFOLDING at its literal element (the
    cycle-16 source-121 move, an equivalence) it collapses to `odd 3` and the
    gate admits it.  That collapse is exactly why cycle 16 recorded source
    121's green as coverage and NOT as evidence of set coverage; the same
    caveat is what this subject would ship under."""
    prose = _subjects()["09_Sets#problem-017"]
    assert "\\mathcal{P}" in prose and "\\notin" in prose, prose

    src = prose
    even_body = {"op": "even", "args": [{"ref": "k"}]}
    faithful = _base(src, carrier="Nat") + [
        {"id": "opev", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "even", "carrier": "Nat"}},
        {"id": "sa", "force": "choice", "quote": "",
         "lf": {"kind": "setdef", "name": "sa", "param": "k",
                "body": even_body}},
        # the OUTER comprehension: its parameter ranges over SETS
        {"id": "sp", "force": "choice", "quote": "",
         "lf": {"kind": "setdef", "name": "sp", "param": "s",
                "body": {"op": "mem",
                         "args": [{"lit": 3}, {"set": "s"}]}}},
        {"id": "c", "force": "demand", "quote": "3 ∈s",
         "lf": {"kind": "conclusion",
                "pred": {"op": "mem",
                         "args": [{"ref": "n"}, {"set": "sp"}]}}}]
    with pytest.raises(MR.FragmentMiss) as e:
        _reading(faithful, src)
    assert e.value.missing_kind_guess == "set:set-valued-param"

    unfolded = _base(src, carrier="Nat") + [
        {"id": "opev", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "even", "carrier": "Nat"}},
        {"id": "opod", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "odd", "carrier": "Nat"}},
        {"id": "sa", "force": "choice", "quote": "",
         "lf": {"kind": "setdef", "name": "sa", "param": "k",
                "body": even_body}},
        {"id": "c", "force": "demand", "quote": "3 ∈s",
         "lf": {"kind": "conclusion",
                "pred": {"op": "not", "args": [
                    {"op": "mem",
                     "args": [{"lit": 3}, {"set": "sa"}]}]}}}]
    concl = [s for s in _reading(unfolded, src).statements
             if s["lf"]["kind"] == "conclusion"][0]["lf"]["pred"]
    assert concl == {"op": "not",
                     "args": [{"op": "even", "args": [{"lit": 3}]}]}
    assert ME.eval_pred(concl, {}, {}, "Nat") is True
    # and the degeneracy is the finding: NO set structure is left in it
    assert "mem" not in json.dumps(concl) and "set" not in json.dumps(concl)


# --------------------------------------------------------------------------- #
# The standing conclusion, pinned so a later session starts from the reading.
# --------------------------------------------------------------------------- #
def test_the_measured_ceiling_is_recorded_not_projected():
    """What this file licenses a receipt to say, and nothing beyond it: the
    four-subject price is a COUNT of ledger rows, one subject needs the
    tower-class residue, two carry a carrier mismatch in the prose (one of
    them refuted outright at a single carrier), and one is reachable only by
    the degenerate unfolding.  So the honest expectation for the next
    `--unblocked refused:set-membership` run is SMALL -- and the number of
    record is that run, never this file."""
    subs = _subjects()
    assert len(subs) == 4
    held_by_residue = {"09_Sets#definition-003", "09_Sets#problem-017"}
    carrier_mismatch = {"09_Sets#problem-014", "09_Sets#problem-015"}
    assert held_by_residue | carrier_mismatch == set(subs)
    assert not held_by_residue & carrier_mismatch

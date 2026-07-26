#!/usr/bin/env python3
"""Purchase frontier: the committed, plan-keyed view of the §4 purchase queue
with LIVE census prices and LIVE refusal demand attached.

The corpus side of the flywheel has had a derived worklist since
``tools/frontier.py``: a session asks "what do I intake next?" and gets a
computed answer.  The PURCHASE side has had none -- "which purchase is next,
what does it price, and has it landed?" lived only in PLAN_FRAGMENT §4 prose
plus a reader's recollection of which growth-registry rows exist.  That is
exactly the shape of state house law forbids keeping in prose: the counts
move every re-census, and "purchased" is a fact about the tree, not a memory.
So the queue gets the same treatment the intake window got -- recompute beats
recollection:

- PRICES come from ``results/frontier.json``'s blocked groups (the census
  signal counts), never from this file.  A purchase declares WHICH signals it
  prices; the numbers are read.
- STATUS is derived from the tree: a fragment purchase is ``purchased`` when
  its ``buildloop/growth_protocol.py`` GROWERS rows exist (registration IS
  accounting -- the registry is the receipt), and an instrument purchase
  (a census signal split, which grows no grammar and therefore registers no
  grower) is ``purchased`` when its delta receipt is a real, non-empty file
  that CONTAINS the needle the row cites it for.  Each row DECLARES which
  evidence kind it is answerable to; neither kind is ever inferred.
- BLOCKING REFUSALS invert ``SIGNAL_UNBLOCKED_BY`` -- the measured-refusal
  vocabulary of ``tools/frontier_refusals.py``, every signal of which is
  mapped to the purchase that would meet it or to ``None`` WITH A REASON.
  Naming a purchase that does not actually meet a signal would manufacture
  demand out of a plan, which is the same sin as distorting a reading to
  force a green.
- The REFILL PROJECTION answers the question whose absence let this artifact
  report "0 open" while the frontier held a full window of demoted subjects:
  per open row, how many currently-refused subjects would RETURN TO READY if
  it landed.  See the section below.

THE QUEUE IS PRICED ON TWO AXES, AND ONLY ONE OF THEM WAS EVER DECLARED.
The §4 rows are priced by CENSUS vocabulary; the refusal ledger prices a
second axis entirely -- attempt-candidates that ALREADY PASSED selection and
were demoted by a MEASURED refusal (``tools/frontier.py`` precedence: refused
beats ready).  While every §4 row read ``purchased`` and every refusal signal
mapped to ``None``, this file computed "0 open" over a frontier whose
``ready`` was empty and whose ``refused:`` groups were not -- a FALSE ZERO,
and the same defect class as a census term nothing can ever match: the
DECLARATION stopped, and a stopped declaration reads exactly like exhausted
demand.  So the refusal-priced rows are declared here beside the §4 rows,
each row grounded in the groups the ledger actually measured and priced by
NUMBERS READ FROM THE FRONTIER, never authored.  A row is priced by census
signals, by refusal signals, or by both -- and the builder refuses a row
priced by NEITHER, because a queue entry priced in nothing is a wish.

THE REFILL PROJECTION (top-level ``refill_projection``).  "0 ready" and "0
open" are each honest readings and together they are a stall, so the artifact
publishes the join: for every open row, the refusal groups it would retire,
and the number of refused SUBJECTS whose whole signal set that row meets.
The two numbers differ on purpose.  Group memberships count a subject once
per signal it carries, while ``tools/frontier.py`` returns a subject to
``ready`` only when EVERY refusal against it is retired -- so a row can name
a group and refill nothing from it, which is precisely what the set-carrier
row measures today.  Summing groups would have published a bigger number and
a worse reading.

Deterministic, LLM-free, Lean-free, network-free; no wall-clock.  Same
canonical-JSON discipline as the other ``results/`` writers.

TWO ROWS CAN NEVER COMPUTE TO ``purchased``, by construction:

- **P5** (the abstract-algebra discharge route) is ``trust-root`` ALWAYS.  It
  touches ``ANCHOR_DISCHARGE_RUNGS``, i.e. the ANTI_LIST's "primitive ladder
  rungs" -- trust roots never grow by purchase or economics, whatever the
  census prices them at (CLAUDE.md; PLAN_FRAGMENT §4 P5, §5).  The status pin
  is checked BEFORE any evidence is consulted, so planting a grower row named
  after it cannot buy it; and the builder verifies its declared anti-list
  clause is still IN ``ANTI_LIST``, so deleting the doctrine reds this tool
  rather than silently promoting the row.
- **PARKED** rows (entropy proper, real-analysis) are ``parked`` ALWAYS, and
  each carries the lift condition in writing -- parked items stay parked in
  writing, and a park that names no way out is an indefinite hold.

DERIVED_FROM pins the sha256 of every input, including the growth-protocol
SOURCE TEXT and every declared RECEIPT (with an explicit absent sentinel):
"an input moved" then reads as recorded STALENESS demand (regenerate),
distinct from "the derivation is wrong" (a red byte-compare) -- the
``tools/proof_queue.py`` convention.  Receipts belong in that pin because
status is read off them; leaving them out meant a receipt could be rewritten
under a status this artifact still asserted.

REGEN-DAG MEMBER (final group, beside the hammer pair): the census moves the
prices every growth cycle, so this artifact must regenerate mechanically or
its byte teeth red the next merge (the PR #39 lesson, paid once already).

OUTPUT: ``results/purchase_frontier.json`` (schema: ``derived_from``,
``purchases``, ``refill_projection``, ``honesty``).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common

# --------------------------------------------------------------------------- #
# Inputs (pinned into ``derived_from`` by repo-relative path).
# --------------------------------------------------------------------------- #
FRONTIER = "results/frontier.json"
CENSUS = "results/census_portfolio.json"
REGISTRY = "buildloop/growth_protocol.py"
INPUTS = (FRONTIER, CENSUS, REGISTRY)

#: What ``derived_from`` records for a DECLARED receipt that is not on disk.
#: A receipt is an input to the derivation exactly as the census is, so its
#: absence has to be pinned as a fact rather than omitted as a silence: a key
#: that simply vanishes from ``derived_from`` when the file does reads as a
#: schema change, while an explicit sentinel reads as what it is -- a receipt
#: appearing or disappearing is recorded STALENESS demand (regenerate),
#: distinct from a wrong derivation (a red byte-compare).  The
#: ``tools/proof_queue.py`` convention, extended to the evidence files.
RECEIPT_ABSENT = "(absent)"

_HONESTY = (
    "prices are LEXICAL census signals, never fidelity verdicts: a priced "
    "count says how many nodes mention the vocabulary, never how many would "
    "certify; overlapping signals never sum to a node total (a node carrying "
    "several signals is counted under each); bill_class is a DECLARED "
    "intention, not a computed prediction of the diff a purchase will need; "
    "status is read off the tree (registry rows / delta receipts), never off "
    "this file's prose; the trust-root row can never compute to purchased, "
    "and parked rows stay parked in writing")

# --------------------------------------------------------------------------- #
# Declared vocabularies (the ``frontier_parks.REASONS`` pattern: every entry
# carries a non-empty description, and the teeth assert it -- a vocabulary
# whose members mean whatever the reader assumes is not a vocabulary).
#
# The first three are the PURCHASE-BILL shapes.  The last two name the
# NON-bills, kept in the same vocabulary so that every row's class resolves
# and no row is silently classless -- a queue entry with no declared shape is
# how "we'll work out the bill later" gets written down as if it were a plan.
# --------------------------------------------------------------------------- #
BILL_CLASSES = {
    "census-instrument":
        "buys a MEASUREMENT, not a fragment extension: a census signal split "
        "that makes a later delta honestly attributable (P3's "
        "probability-mass / entropy-log split is the worked example).  It "
        "grows no grammar, so it registers no grower and its receipt is the "
        "delta document itself.",
    "additive-reflect":
        "the full §4 bill paid ADDITIVELY: validator + lexicon, eval "
        "semantics, SMT mirror, Lean table, differential + symbolic "
        "batteries, growth-registry row, teeth, and a reflect slice that "
        "extends by CONSTRUCTOR ADDITION only (the P1 unroll precedent), so "
        "nothing already certified moves and no certified byte churns.",
    "additive-desugaring":
        "the SMALLEST bill in the queue, and the one PLAN_FRAGMENT §4 P6 "
        "declared tower-class against: the full §4 bill paid with NO new "
        "constructor anywhere, because the new vocabulary is ELIMINABLE into "
        "vocabulary already certified (`iff` into the `and` of two `implies`; "
        "`not` into the atom duals, by negation-normal form).  Distinguished "
        "from additive-reflect because that class still ADDS a constructor "
        "and this one adds none -- the difference between a tower that grew "
        "and a tower that did not have to -- so §3.1 rule 3(a) is not "
        "reached at all, and the shapes the elimination cannot reach are "
        "named misses rather than widenings.",
    "tower-class":
        "a purchase whose faithful shape re-bases the certification TOWER -- "
        "a carrier threading every walker's type discipline rather than "
        "adding a constructor beside it.  Named so the queue can say when a "
        "row's honest shape is this and the session scoped it down to "
        "additive-reflect behind a fail-closed skip, instead of pretending "
        "the smaller bill was the whole bill.  A new PROPOSITION constructor "
        "is the same shape read from the other side: PLAN_FRAGMENT §3.1 rule "
        "3(a) puts any new Tm/Pd constructor outside the additive class, "
        "because every certified walker over the type must then answer it.",
    "iteration-class":
        "a purchase whose bound is not a literal: iteration over a SYMBOLIC "
        "bound, which no unrolling reaches (no SMT unroll, a true binding "
        "constructor in the reflect slice, induction rather than exhaustive "
        "computation).  results/p1_delta.md named this class by name when "
        "P1's re-census came back zero -- literal-bound machinery is bought, "
        "and the corpus keeps asking for the symbolic shape instead.",
    "definitional-extension":
        "buys a MECHANISM rather than vocabulary: the ability to introduce a "
        "NAMED function or predicate with a body and to reason through the "
        "name.  Distinct from every carrier and node class in §4, which add "
        "words the reader already knows; this one adds the ability for the "
        "SOURCE to add words, which is why unfolding a definition by hand "
        "only ever relocates the demand it is asked to meet.",
    "research-packet":
        "NOT a purchase bill: the material needs a different certifying story "
        "(interval-arithmetic / polyrith-class routes), i.e. its own research "
        "packet and its own shadow ceremony before any bill can be written "
        "(PLAN_FRAGMENT §4 PARKED).  The census keeps measuring it; nothing "
        "here promises it.",
    "trust-root-ceremony":
        "NOT a purchase bill either, and not purchasable at any price: the "
        "S4a -> S4a' -> S4b route (shadow channel, durable agreement ledger, "
        "numeric entrance predicate, ONE-commit ceremony with explicit user "
        "sign-off).  The anti-list overrides the price list.",
}

#: The §4 queue, in §4's own STRICT TRACTABILITY ORDER -- the order is DATA
#: (each row rides the machinery the row above it bought), so the artifact
#: preserves declaration order rather than re-sorting it into alphabet.
#:
#: Fields: ``plan_ref``/``title``/``notes`` are prose the plan already owns;
#: ``prices_signals`` names WHICH census signals a row prices (never how
#: many -- the counts are read from the frontier artifact).  It is EMPTY on a
#: refusal-priced row, whose demand is measured on the other axis entirely
#: (``unblocks_refusals``); the builder requires each row to be priced by one
#: axis or the other, so an empty list is a declaration of where the price
#: lives and never an omission.  ``bill_class``
#: is the declared bill shape; ``evidence`` selects the status rule
#: ("grower" -> its GROWERS rows exist; "receipt" -> its declared
#: (path, needle) receipts each CONTAIN their needle; "none" -> the row is
#: status-pinned and answers to neither);
#:
#: ``receipts`` are (path, needle) pairs on the ``conformance()`` teeth
#: pattern, never bare paths.  p3-split and p4-split cite the SAME document
#: on purpose (one receipt, two instruments), so existence could never tell
#: them apart; each names the sentence it is evidence FOR, and a receipt that
#: stops saying it stops counting.
#: ``status_pin`` freezes a row that must never be computed; ``anti_list_ref``
#: (P5 only) is verified live against ANTI_LIST at build time.
#:
#: ``class_evidence`` is the same (path, needle) teeth idiom pointed at a
#: DIFFERENT question.  ``bill_class`` is a declared intention (the honesty
#: string says so), and a declaration that USED to be measured is the exact
#: shape of state house law forbids keeping in prose: the connectives row was
#: declared tower-class on the reading that a `not` constructor would be
#: needed, and it stops being tower-class the moment something MEASURES that
#: negation pushes to atoms instead.  A row whose class rests on a
#: measurement therefore cites the file that made it, the builder verifies
#: the file still exists and still contains the named test, and it verifies
#: the row's own notes cite the same path -- one relation, two statements,
#: one machine comparing them.  Deleting or renaming the proof reds this tool
#: rather than leaving a class claim dangling over a citation that no longer
#: says anything.  It is NOT pinned in ``derived_from``: no published number
#: is read off it, so an edit to the proof is a teeth question, never a
#: regeneration of the artifact.
#:
#: ``unblocks_refusals`` is the row's READING of which measured refusals it
#: would retire.  SIGNAL_UNBLOCKED_BY below is the single source the artifact
#: actually inverts; this field states the same claim from the purchase's
#: side, and a tooth asserts the two agree exactly.  Two statements of one
#: relation are a drift hazard unless a machine compares them -- so one does.
#:
#: Per-purchase declarations live TOOL-LOCALLY on purpose.  They are a
#: reading of §4, not a growth-registry fact, and the registry is
#: ceremony-fenced; migrating them into ``growth_protocol.PLANNED`` is a
#: later registry edit, not a side effect of building a view.
PURCHASES = {
    "p1": {
        "plan_ref": "PLAN_FRAGMENT §4 P1",
        "title": "bounded big-operators (bigsum/bigprod)",
        "prices_signals": ["sequences-sums"],
        "bill_class": "additive-reflect",
        "evidence": "grower",
        "grower_keys": ["bigop-node-class"],
        "receipts": [["results/p1_delta.md", "P1 purchase receipt"]],
        "unblocks_refusals": [],
        "notes": "the one structural extension: a binding AST node CLASS with "
                 "an explicit literal bound, decidable by exhaustive "
                 "computation, SMT by unrolling, Lean via Finset.range.  "
                 "Everything later rides its binding machinery, which is why "
                 "it is first; the receipt is results/p1_delta.md and the "
                 "commit is the repo's worked example of a full bill.",
    },
    "p2": {
        "plan_ref": "PLAN_FRAGMENT §4 P2",
        "title": "bounded Finset carrier + cardinality",
        "prices_signals": ["sets-cardinality"],
        "bill_class": "additive-reflect",
        "evidence": "grower",
        "grower_keys": ["finset-card-node-class"],
        "receipts": [["results/p2_delta.md", "P2 purchase receipt"]],
        "unblocks_refusals": [],
        "notes": "rides P1's literal-bound binding machinery; same bill.  "
                 "Bought setbuild only as card's ARGUMENT -- a set can be "
                 "counted but never inhabited, named, or compared -- which is "
                 "why the set-membership refusal signal is NOT filed against "
                 "this row (see SIGNAL_UNBLOCKED_BY).",
    },
    "p3-split": {
        "plan_ref": "PLAN_FRAGMENT §4 P3 (prerequisite)",
        "title": "census signal split: probability-mass vs entropy-log",
        "prices_signals": ["probability-mass", "entropy-log"],
        "bill_class": "census-instrument",
        "evidence": "receipt",
        "grower_keys": [],
        "receipts": [["results/p3_delta.md", "entropy-log"]],
        "unblocks_refusals": [],
        "notes": "§4 P3 requires this split BEFORE the carrier, so the "
                 "carrier's delta is honestly attributable: the mass slice is "
                 "reachable with rational arithmetic, the log slice is not "
                 "reachable at all.  It grows no grammar and registers no "
                 "grower -- an instrument purchase answers to its receipt, "
                 "results/p3_delta.md, and to nothing else.",
    },
    "p3-carrier": {
        "plan_ref": "PLAN_FRAGMENT §4 P3",
        "title": "the rational carrier (the mass-arithmetic slice)",
        "prices_signals": ["probability-mass"],
        "bill_class": "additive-reflect",
        "evidence": "grower",
        "grower_keys": ["rat-carrier"],
        "receipts": [],
        "unblocks_refusals": [],
        "notes": "the honest shape of a new carrier is tower-class -- a "
                 "carrier threads every walker's type discipline -- and this "
                 "session lands it additive-reflect-SCOPED instead: the "
                 "reflect slice takes a fail-closed named skip on the new "
                 "carrier rather than widening the certified tower, so the "
                 "smaller bill is never claimed as the whole bill.  The "
                 "corpus-wide rational-arithmetic signal is the same "
                 "carrier's broader reach; it is deliberately NOT priced "
                 "here, because §4's stated target is the mass slice and a "
                 "queue must not bill itself for reach it has not argued.",
    },
    "p4-split": {
        "plan_ref": "PLAN_FRAGMENT §4 P4 (prerequisite)",
        "title": "census signal split: algebra-abstract attribution",
        "prices_signals": ["algebra-abstract"],
        "bill_class": "census-instrument",
        "evidence": "receipt",
        "grower_keys": [],
        "receipts": [["results/p3_delta.md", "algebra-abstract"]],
        "unblocks_refusals": [],
        "notes": "typeclass-parametric statements stay out-of-fragment under "
                 "their OWN sub-signal, so P4's concrete purchase can never "
                 "silently claim them.  Landed as the addendum inside "
                 "results/p3_delta.md (one receipt, two instruments) -- the "
                 "receipt path is shared on purpose rather than duplicated.",
    },
    "p4-carrier": {
        "plan_ref": "PLAN_FRAGMENT §4 P4",
        "title": "concrete algebra: the ZMod n carrier",
        "prices_signals": ["algebra-structures"],
        "bill_class": "additive-reflect",
        "evidence": "grower",
        "grower_keys": ["zmod-carrier"],
        "receipts": [],
        "unblocks_refusals": [],
        "notes": "finite carriers are per-instance decidable, so the "
                 "concrete residue is buyable while the abstract remainder "
                 "is not.  PARTIAL by declaration: the priced count is the "
                 "whole algebra-structures signal, and only the concrete "
                 "slice of it is reachable -- the count is demand, never a "
                 "forecast of the delta.",
    },
    "p5": {
        "plan_ref": "PLAN_FRAGMENT §4 P5",
        "title": "abstract algebra discharge route (TRUST ROOT, not a purchase)",
        "prices_signals": ["algebra-abstract"],
        "bill_class": "trust-root-ceremony",
        "evidence": "none",
        "status_pin": "trust-root",
        "anti_list_ref": "primitive ladder rungs",
        "grower_keys": [],
        "receipts": [["results/p5_shadow.md", "P5 shadow channel"]],
        "unblocks_refusals": [],
        "notes": "a new discharge rung touches ANCHOR_DISCHARGE_RUNGS "
                 "(PINNED, kernel/certs.py, FI-KA-1/4), i.e. the ANTI_LIST "
                 "clause 'primitive ladder rungs' -- no queue entry may "
                 "shortcut the S4a -> S4a' -> S4b ceremony, whatever the "
                 "census prices it at.  S4a/S4a' evidence so far: the paired "
                 "shadow channel run/algebra_shadow.py and its receipt "
                 "results/p5_shadow.md; the numeric ENTRANCE PREDICATE that "
                 "S4b would be asked to meet is measured from that channel's "
                 "durable agreement ledger, and it is not met and not "
                 "proposed here.",
    },
    "parked-entropy-log": {
        "plan_ref": "PLAN_FRAGMENT §4 PARKED",
        "title": "entropy proper (log is transcendental)",
        "prices_signals": ["entropy-log"],
        "bill_class": "research-packet",
        "evidence": "none",
        "status_pin": "parked",
        "grower_keys": [],
        "receipts": [],
        "unblocks_refusals": [],
        "notes": "LIFTED BY: its own research packet -- a certifying story "
                 "for a transcendental function (interval-arithmetic or a "
                 "polyrith-class route) argued and shadow-measured before any "
                 "bill is written.  P3's split exists precisely so this "
                 "slice stays visibly separate from the mass slice instead of "
                 "riding in on it.",
    },
    "parked-real-analysis": {
        "plan_ref": "PLAN_FRAGMENT §4 PARKED",
        "title": "real analysis (limits / continuity are undecidable)",
        "prices_signals": ["real-analysis"],
        "bill_class": "research-packet",
        "evidence": "none",
        "status_pin": "parked",
        "grower_keys": [],
        "receipts": [],
        "unblocks_refusals": [],
        "notes": "LIFTED BY: its own research packet and its own shadow "
                 "ceremony.  The census keeps measuring it -- a large price "
                 "is not an argument, and this row exists so the large price "
                 "cannot be mistaken for one.",
    },
    # ----------------------------------------------------------------- #
    # THE REFUSAL-PRICED BLOCK.  §4's queue is priced by census vocabulary
    # and it is exhausted; the ledger's demand was never declared at all,
    # which is why this artifact could report "0 open" over a frontier full
    # of demoted subjects.  Each row below names groups the ledger MEASURED
    # -- attempt-candidates that passed selection and were demoted by a
    # measured refusal -- and nothing else: no row is opened for a signal
    # SIGNAL_UNBLOCKED_BY leaves at None, because manufacturing demand to
    # tidy the queue is the same sin as distorting a reading to force a
    # green.  These are NOT §4 rows and do not claim to be; each cites the
    # ledger (and, where the plan already named the demand, the plan).
    #
    # Ordered by declared bill weight, lightest first, on the same
    # tractability principle §4's own order encodes: the connectives are a
    # node-class purchase with a known bill shape (PLAN_FRAGMENT §1 names
    # them as next supply (b)), symbolic bounds are the iteration-class bill
    # results/p1_delta.md named, function symbols need a mechanism the
    # fragment has never had, and a set OBJECT carrier re-bases the tower.
    # ----------------------------------------------------------------- #
    "refusal-connectives": {
        "plan_ref": "results/frontier_refusals.jsonl (cycle-09/16 rows); "
                    "PLAN_FRAGMENT §1 'cycle-16 connective demands'",
        "title": "propositional connectives: negation and the biconditional",
        "prices_signals": [],
        "bill_class": "additive-desugaring",
        "evidence": "grower",
        "grower_keys": ["connective-node-class"],
        "class_evidence": [
            ["tests/test_nnf_duals.py",
             "test_every_pd_atom_and_connective_has_a_pointwise_dual"]],
        "receipts": [["results/p6_delta.md", "P6 purchase receipt"]],
        "unblocks_refusals": ["definition-biconditional", "iff-connective",
                              "not-connective"],
        "notes": "the largest measured refill on the ledger, and the row "
                 "that answered its own design question instead of assuming "
                 "it.  DECLARED tower-class, because a `not` CONSTRUCTOR in "
                 "`Pd` is outside the additive class under PLAN_FRAGMENT "
                 "§3.1 rule 3(a); MEASURED as the smaller bill, because "
                 "every atom the fragment carries has its dual IN the "
                 "fragment (=/!=, <=/< with the arguments SWAPPED, "
                 "even/odd), so negation-normal form pushes `not` down to an "
                 "atom and `iff` unfolds to the `and` of two `implies` -- "
                 "nothing enters `Tm`/`Pd` and no `Decidable` instance is "
                 "written.  Landed additive-desugaring "
                 "(results/p6_delta.md); declaring the larger bill is what "
                 "kept the smaller from being claimed before it was shown.  "
                 "The elimination's NAMED limits, reported rather than "
                 "hidden: `dvd` and `coprime` carry no dual, so a negation "
                 "reaching either is `not:<op>-no-dual` (`not:dvd-no-dual`, "
                 "`not:coprime-no-dual`) -- first-class "
                 "demand for the negation-constructor purchase this row did "
                 "NOT make.  The `dvd` half of that residue is CONSERVATIVE "
                 "rather than forced, and the same sweep says so: `not "
                 "dvd(a, b)` IS pointwise `b % a != 0` over every box, with "
                 "no side condition, and `%` is `Tm.tmod` -- already a "
                 "constructor of the reflect slice -- so the skip is the "
                 "choice not to rewrite a source's divisibility claim into a "
                 "modular one at quote time, not the absence of an encoding.  "
                 "`coprime` is the other case honestly: its dual needs "
                 "`gcd`, which is not a `Tm` constructor at all, so it keeps "
                 "its existing op-out-of-reflect-slice skip whatever "
                 "negation does.  Neither residue adds a constructor, which "
                 "is why neither touches the class.  And the reflect slice's quoting of the two "
                 "words rides a later commit, until which a reading using "
                 "them keeps the existing fail-closed "
                 "`op-out-of-reflect-slice:` skip.  RESIDUE, measured and "
                 "reported rather than hidden: several subjects filed here "
                 "carry a SECOND refusal this row does not meet "
                 "(mod-operator, predicate-variable, set-membership, "
                 "exists-only-shape), so they stay demoted until those land "
                 "too -- see refill_projection, which counts subjects rather "
                 "than summing groups.  THE MEASUREMENT ITSELF is tests/test_nnf_duals.py::test_every_pd_atom_and_connective_has_a_pointwise_dual -- the artifact cites it so a reader can reach the evidence the class rests on rather than taking the class on trust.",
    },
    "refusal-symbolic-exponent": {
        "plan_ref": "results/frontier_refusals.jsonl (symbolic-exponent "
                    "rows); results/p1_delta.md (the P1 no-delta receipt); "
                    "results/p7_delta.md (the purchase receipt)",
        "title": "symbolic exponents (iteration over a non-literal bound)",
        "prices_signals": [],
        "bill_class": "iteration-class",
        "evidence": "grower",
        "grower_keys": ["pow-symbolic-exponent"],
        "receipts": [["results/p7_delta.md", "P7 delta"]],
        "unblocks_refusals": ["symbolic-exponent"],
        "notes": "PURCHASED (results/p7_delta.md): `Tm.pow` plus the six "
                 "walker cases over it, admitted at carrier Nat ONLY -- "
                 "non-negativity by type is what keeps the power Monoid.npow, "
                 "and Lean itself refuses `HPow Int Int` to synthesize.  Two "
                 "things the receipt keeps in writing rather than in the "
                 "status: the SMT bill item is paid as a REFUSAL (no "
                 "exponentiation in SMT-LIB, so the reading routes to "
                 "enumeration -- the first enum-only route keyed to a node "
                 "SHAPE rather than an operator WORD), and the UNBOUNDED "
                 "UNIVERSAL IS STILL NOT DISCHARGED, because the box-lift "
                 "lemmas meet a universal with `nomatch hex` and the missing "
                 "ingredient is an induction principle the slice does not "
                 "have.  Residual demand stays first-class as "
                 "`pow:symbolic-exponent@Int`.  The ORIGINAL pricing, kept "
                 "because it is why the row exists: the bound IS the "
                 "exponent, so nothing bounded-by-a-literal "
                 "reaches it and P1's binding machinery does not help.  This "
                 "row is not an invention of the queue: results/p1_delta.md "
                 "recorded P1's ZERO re-census delta as §2 evidence to buy "
                 "differently and named the successor in the same sentence "
                 "-- 'the next iteration-class purchase should target "
                 "symbolic bounds (a genuinely harder certifying story: no "
                 "SMT unroll, a true binding constructor in the reflect "
                 "slice)'.  The ledger has since priced that sentence.  "
                 "Note the joint hold with the function-symbol row: the "
                 "06_Induction subjects mostly carry BOTH signals, so "
                 "neither purchase refills them alone -- the projection "
                 "reports that as a per-row held count, never as a sum.",
    },
    "refusal-function-symbol": {
        "plan_ref": "results/frontier_refusals.jsonl (function-symbol rows; "
                    "cycle-15 note on the div-operator boundary)",
        "title": "named function symbols (a definitional-extension mechanism)",
        "prices_signals": [],
        # DECLARED definitional-extension (attended-only under §3.1 rule 3);
        # MEASURED additive-desugaring, the P6 shape -- see the notes.
        "bill_class": "additive-desugaring",
        "evidence": "grower",
        "grower_keys": ["funcdef-definitional-extension"],
        "receipts": [["results/p8_delta.md", "P8 purchase receipt"]],
        "unblocks_refusals": ["function-symbol"],
        "notes": "PURCHASED, and SPLIT (results/p8_delta.md).  What landed is "
                 "the NON-RECURSIVE half: a `definition` statement gives a "
                 "named function an EXPLICIT body over its own parameters, "
                 "and `{app}` applies it -- at a SYMBOLIC argument, which is "
                 "the thing the literal-index unfolding could never reach.  "
                 "The row answered its own design question rather than "
                 "assuming it (P6's precedent, which "
                 "tests/test_function_symbol_class.py names): finding (4) "
                 "priced the rung at an application node in `Tm` PLUS a new "
                 "`Decidable` story, both correct ABOUT AN UNINTERPRETED "
                 "SYMBOL -- and a symbol with an explicit body is ELIMINABLE, "
                 "so the gate desugars it by capture-free substitution, the "
                 "reflect slice is byte-unchanged and rule 3(a) is not "
                 "reached.  WHAT IS STILL OPEN, and it is the headline the "
                 "status must not bury: the RECURRENCES are NOT bought.  A "
                 "body that applies the function being defined has no finite "
                 "unfolding at a symbolic index, and it now refuses by name "
                 "as `funcdef:recursive-body` -- so the refill this row "
                 "returns is honestly expected to be SMALL or zero, and the "
                 "cycle that runs `intake_from_frontier --unblocked "
                 "refused:function-symbol` is the number of record.  "
                 "Originally: factorial, the recurrences a_n/d_n/F_n, the Bezout "
                 "coefficients: each is an arbitrary NAMED function the "
                 "corpus introduces and the fragment has no word for.  No "
                 "carrier and no bounded node class supplies one, which is "
                 "why the signal sat unmapped while the queue was priced on "
                 "census vocabulary alone.  The census `maps-functions` "
                 "signal is adjacent and is deliberately NOT priced here: it "
                 "measures statements ABOUT maps (injectivity, composition), "
                 "while this row buys the ability to APPLY a named function "
                 "to carrier values, and a queue must not bill itself for "
                 "reach it has not argued (the p3-carrier disposition).  "
                 "Sibling boundary already measured: `div` is ONE standard "
                 "operator word and is filed apart, exactly as `mod` was.",
    },
    "refusal-set-carrier": {
        "plan_ref": "results/frontier_refusals.jsonl (cycle-16 "
                    "set-membership rows); results/c3_cycle_16.md",
        "title": "set objects: a set carrier and its membership atom",
        "prices_signals": ["sets-cardinality"],
        "bill_class": "tower-class",
        "evidence": "grower",
        "grower_keys": [],
        "receipts": [],
        "unblocks_refusals": ["set-membership"],
        "notes": "P2 bought `setbuild` only as `card`'s ARGUMENT, so a set "
                 "can be COUNTED but never inhabited, named, or compared; "
                 "cycle 16 (results/c3_cycle_16.md) walked the 09_Sets "
                 "window and measured exactly that residue, each time as the "
                 "SECOND blocker behind a connective.  PARTIAL by "
                 "declaration on the census axis: the priced count is the "
                 "WHOLE sets-cardinality signal, of which P2 already bought "
                 "the counting slice, so the number is demand and not a "
                 "forecast of the delta (the p4-carrier disposition).  "
                 "Boundary the same cycle measured on the other side: "
                 "membership in a COMPREHENSION at a literal element unfolds "
                 "definitionally and SHIPS (source 121), so this row is for "
                 "set objects that survive unfolding, not for every "
                 "appearance of the membership sign.  The sharpest reading "
                 "in the projection is this row's: each of its subjects also "
                 "carries a connective refusal, so it refills NOTHING on its "
                 "own and refills only beside the connectives row -- which "
                 "is precisely why the projection counts subjects instead of "
                 "summing groups.",
    },
}

#: Every measured-refusal signal (``tools/frontier_refusals.SIGNALS``) mapped
#: to the PURCHASES key that would meet it, or to ``None`` WITH A REASON.
#:
#: The reasons are the point.  A refusal is demand data, and the honest
#: answer to "which purchase unblocks it?" is frequently "none of them" --
#: the §4 queue buys CARRIERS and bounded node CLASSES priced by census
#: vocabulary, while the refusal ledger measures missing PRIMITIVES on
#: individual subjects, and the two axes only partly meet.  Filing a signal
#: under the nearest-looking purchase would manufacture demand that purchase
#: does not meet, and a purchase that arrives without retiring the rows filed
#: against it would then read as a failure it never promised.
#:
#: WHAT CHANGED, and why it is not a widening of that doctrine.  Every signal
#: here once mapped to None, and while §4 was live that was a true reading:
#: no QUEUED row met any of them.  It stopped being true the moment §4 ran
#: out, because "no queued purchase meets this" was silently doing the work
#: of "no purchase meets this" -- a reason about the QUEUE read as a reason
#: about the DEMAND.  The six signals below now name refusal-priced rows
#: declared for them; the nine that remain None keep their reasons unchanged
#: in substance, because their reasons were always about the demand itself.
#: metatheoretic-subject stays the anchor case: tools/frontier_refusals.py
#: documents it as meeting NO purchase, and it is not filed under one here.
SIGNAL_UNBLOCKED_BY = {
    "symbolic-exponent": (
        "refusal-symbolic-exponent",
        "the bound is the exponent itself, so nothing bounded-by-a-literal "
        "reaches it: it needs iteration over a symbolic bound, which is "
        "exactly the iteration-class successor results/p1_delta.md named "
        "when P1's re-census came back zero",
    ),
    "function-symbol": (
        "refusal-function-symbol",
        "an arbitrary NAMED function (factorial, the sequences a_n/d_n/F_n, "
        "the Bezout coefficients) needs a definitional-extension mechanism; "
        "no carrier and no bounded node class supplies one, so the row filed "
        "here buys the mechanism rather than more vocabulary",
    ),
    "mod-operator": (
        None,
        "ALREADY MET, and not by a §4 row: mod is an admitted operator word "
        "(the operator-words grower).  The rows stay as pre-purchase "
        "evidence -- evidence is never re-measured to force a green -- and "
        "they are not live demand against this queue",
    ),
    "nonvacuity": (
        None,
        "a measurement about the SUBJECT (the faithful reading is vacuous), "
        "not a missing primitive; no vocabulary purchase can change what the "
        "source says",
    ),
    "cmp-outside-lexicon": (
        None,
        "MEASURED NOT MET (C3 cycle 20, results/c3_cycle_20.md), correcting "
        "the earlier reading that called this mintable at no purchase cost: "
        "`>` and `>=` are not in generators/math_reading.py::_BUILTIN_ATOM_OPS "
        "({=, !=, <=, <}) and the reading gate refuses them outright "
        "(\"unknown atom/connective '>'\"), while the operator-words grower "
        "mines TEMPLATES over readings and so can never mint an ATOM OP that "
        "no reading is allowed to contain -- the mechanism does not reach "
        "this signal.  The only green available is the CONVERSE reading "
        "(`b < a` for the source's `a > b`), which certifies fully and is "
        "declined on fidelity, not on capability: it reverses the source's "
        "written order, the same rewriting the readings discipline refuses "
        "when it keeps a quadratic in the source's own spelling.  So the "
        "honest home is an atom-lexicon purchase, still to be priced on the "
        "purchase axis; this stays None because no §4 row buys it yet, and a "
        "row is never authored from a corpus cycle",
    ),
    "exists-only-shape": (
        None,
        "the demand is on the ANCHOR/witness-template axis (run/anchor.py, "
        "the witness-template-shapes planned grower), not on the fragment's "
        "carrier or node-class axis",
    ),
    "definition-biconditional": (
        "refusal-connectives",
        "a DEFINITION's content IS the biconditional, and the connectives "
        "row is what makes that content sayable at all; the "
        "definitional-extension mechanism stays a SEPARATE demand, so a "
        "definition whose definiendum is itself outside the lexicon keeps "
        "its other refusal row and does not return on this purchase alone",
    ),
    "iff-connective": (
        "refusal-connectives",
        "a propositional primitive: when this signal was measured "
        "_CONNECTIVES was exactly {and, or, implies}; the connectives row "
        "has since landed the biconditional as the `and` of two "
        "implications, so these ledger rows are RETIRED demand awaiting "
        "the re-measurement a corpus cycle performs with --unblocked",
    ),
    "not-connective": (
        "refusal-connectives",
        "the same propositional axis as iff-connective -- when the signal "
        "was measured the fragment had no negation of an atom -- and the "
        "same bill, which is why the two are filed on ONE row instead of "
        "two competing ones; the row has since landed negation as the atom "
        "duals, and a subject returns to ready only when EVERY signal it "
        "carries is met",
    ),
    "predicate-variable": (
        None,
        "a SECOND-ORDER binder (quantifying over a property); objects are "
        "carrier-typed values only, so no carrier purchase reaches it",
    ),
    "hypothesis-quantifier": (
        None,
        "the hypothesis carries its own binder and flattening states a "
        "different theorem; the fix is a binder-scoping purchase on the "
        "reading grammar, not vocabulary",
    ),
    "defined-predicate": (
        None,
        "the subject USES a predicate the corpus defines elsewhere, and the "
        "nearest row (function symbols) buys definitional extension for "
        "NAMED FUNCTIONS over carrier values, not for propositions -- and "
        "even extended, the ledger's own measurement is that unfolding "
        "RELOCATES this subject's demand onto its definition's body (prime, "
        "already priced on the census axis), so filing it under that row "
        "would promise a return the measurement says would not happen",
    ),
    "metatheoretic-subject": (
        None,
        "NO PURCHASE MEETS THIS, by construction: the subject asserts a "
        "property OF A DEFINITION rather than a proposition about carrier "
        "values.  No operator word and no carrier would help, which is "
        "exactly why the signal was named apart from defined-predicate",
    ),
    "div-operator": (
        None,
        "the near miss worth naming: this is INTEGER division (the "
        "quotient), and P3's rational carrier brings FIELD division -- a "
        "different operator on a different carrier.  Filing it under P3 "
        "would manufacture demand P3 does not meet; the honest home is one "
        "operator-word purchase, the shape mod already retired",
    ),
    "set-membership": (
        "refusal-set-carrier",
        "P2 bought setbuild only as card's ARGUMENT, so a set can be counted "
        "but never inhabited: this needs a set OBJECT carrier and its "
        "membership atom, which is the NEW row declared for it.  It is still "
        "not filed under P2, which is purchased and did not meet it",
    ),
}

_STATUSES = ("purchased", "open", "trust-root", "parked")

#: How ``tools/frontier.py`` names a measured-refusal demotion group.  One
#: spelling, used by every reader here, so a rename reds one line.
REFUSED_PREFIX = "refused:"

_REFILL_HONESTY = (
    "a refused subject returning to ready is a SELECTION fact and NEVER a "
    "promise it will certify: it passed selection once and was demoted by a "
    "MEASURED refusal, so retiring that refusal returns it to the intake "
    "window -- where it is a candidate again, exactly as it was before; "
    "returns_to_ready counts SUBJECTS whose whole refusal set a row meets, "
    "while refused_group_memberships counts a subject once per signal it "
    "carries, so the two never sum to each other and the group total is "
    "always the looser reading; a subject carrying several refusals returns "
    "only when ALL of them are met, which is why a row can name a group and "
    "refill nothing from it; counts are over refused NODES because ready "
    "rows are written per node, while the ledger keys on subject TEXT, so "
    "verbatim-equal nodes count once each here exactly as they would in "
    "ready; totals cover OPEN rows only (a landed row's refusal rows stay in "
    "the append-only ledger until a driver re-measures the subject, and "
    "counting those into a PURCHASE projection would promise a refill no "
    "purchase is going to deliver) -- which is exactly why the landed side "
    "is reported SEPARATELY as awaiting_unblock_run rather than folded in: "
    "those subjects need no purchase at all, only a corpus cycle running "
    "`intake_from_frontier --unblocked refused:<signal>`, and before this "
    "field existed the artifact read `0 ready, nothing would refill it` over "
    "supply that was already paid for; it is an UPPER BOUND on the same terms "
    "as everything else here, since a returning subject still has to clear "
    "the demotions named next; and "
    "a returning subject still has to clear the ready computation's other "
    "demotions -- already intaken, or independently parked -- which this "
    "projection does not model")


# --------------------------------------------------------------------------- #
# Loaders / derivations.
# --------------------------------------------------------------------------- #
def _signal_counts(frontier: dict) -> dict:
    """signal name -> node_count over the frontier's blocked groups.  Both
    census signals (bare) and demotion groups (``refused:``/``parked:``
    prefixed) live in one namespace here, exactly as the artifact writes
    them."""
    return {g["signal"]: g["node_count"] for g in frontier["blocked"]}


def _refused_subjects(frontier: dict) -> dict:
    """(corpus, node_id) -> frozenset of the refusal signals measured on it.

    The frontier writes one entry per (node, signal), so a subject refused
    for two reasons appears in two groups; this inverts that back into the
    reading the refill question actually needs, because ``tools/frontier.py``
    returns a subject to ``ready`` only when NONE of its refusals survive.

    Keyed by NODE, not by subject text.  The ledger keys on the text sha256
    (one measurement covers every verbatim-equal copy), but ``ready`` rows
    are written per node, so a text refused once and appearing twice refills
    two rows -- counting shas here would under-report the window by exactly
    the duplicates the frontier's own docstring warns about."""
    out: dict = {}
    for group in frontier["blocked"]:
        signal = group["signal"]
        if not signal.startswith(REFUSED_PREFIX):
            continue
        name = signal[len(REFUSED_PREFIX):]
        for node in group["nodes"]:
            out.setdefault((node["corpus"], node["node_id"]), set()).add(name)
    return {k: frozenset(v) for k, v in out.items()}


def _refill_projection(frontier: dict, rows: list) -> dict:
    """What would REFILL the intake window, per open purchase and in total.

    THE READING THIS ARTIFACT WAS MISSING.  ``ready == 0`` and "0 open" are
    each honest and together they say the flywheel has stopped -- but they
    said it over a ledger measuring, when this reading was added, 46 refused
    subjects across 61 group memberships, every one of them an
    attempt-candidate that passed selection and was demoted by a MEASURED
    refusal.  Nothing in the tree joined those two facts, so the stall read
    as exhausted demand rather than as undeclared demand.  It is published
    here, per row and in total, and it is derived from the SAME
    ``blocking_refusals`` the rows already carry -- one relation, never a
    second hand-kept list.

    Two numbers per row on purpose: the groups a row would retire, and the
    SUBJECTS whose whole refusal set it meets.  Summing groups is the easy
    number and the wrong one; the difference is carried as
    ``held_by_a_signal_this_row_does_not_meet`` so a row that names a group
    and refills nothing from it says so in its own line."""
    counts = _signal_counts(frontier)
    subjects = _refused_subjects(frontier)

    by_purchase = []
    for row in rows:
        blocking = row["blocking_refusals"]
        if not blocking:
            continue
        met = frozenset(blocking)
        returns = [sigs for sigs in subjects.values() if sigs <= met]
        touched = [sigs for sigs in subjects.values() if sigs & met]
        by_purchase.append({
            "purchase_id": row["purchase_id"],
            "status": row["status"],
            "unblocks_refusals": dict(blocking),
            "refused_group_memberships": sum(blocking.values()),
            "returns_to_ready": len(returns),
            "held_by_a_signal_this_row_does_not_meet":
                len(touched) - len(returns),
        })

    # Totals over OPEN rows only -- see _REFILL_HONESTY.  The union reading
    # is separate from the sum because the sum is per-row-alone: subjects the
    # 06_Induction window carries need TWO of these rows before either helps.
    open_rows = [r for r in by_purchase if r["status"] == "open"]
    open_met = frozenset(s for r in open_rows for s in r["unblocks_refusals"])

    # THE READING THIS ARTIFACT WAS MISSING A SECOND TIME, and it is the
    # first one's mirror image.  The totals above count only what an
    # UNLANDED purchase would return -- so the moment a refusal-priced
    # purchase LANDS, its subjects vanish from the projection while still
    # sitting in the ledger, demoted.  They are not stalled and they are not
    # ready: they are AWAITING THE UNBLOCK RUN, because the ledger is
    # append-only and the route back is the next corpus cycle's
    # `intake_from_frontier --unblocked refused:<signal>` (§3.2 path (d)),
    # never the purchase itself.  Between those two events the old reading
    # reported "0 ready, nothing would refill it" over supply that was fully
    # paid for -- a stall that is not merely silent but WRONG.  Measured
    # after P8 (results/p8_delta.md), which is the firing that first left
    # this artifact in that state.
    purchased_met = frozenset(s for r in by_purchase
                              if r["status"] == "purchased"
                              for s in r["unblocks_refusals"])
    awaiting = sorted(name for name, sigs in subjects.items()
                      if sigs and sigs <= purchased_met)

    # Every signal the map leaves at None, with the reason it leaves it
    # there, carrying its LIVE group size.  The artifact then states its own
    # unmet demand instead of leaving it to be reconstructed from the tool's
    # source -- and the reasons travel with the numbers, which is the only
    # arrangement in which "no purchase meets this" stays checkable.
    unmet = [{"signal": sig,
              "refused_nodes": counts.get(REFUSED_PREFIX + sig, 0),
              "reason": reason}
             for sig, (key, reason) in sorted(SIGNAL_UNBLOCKED_BY.items())
             if key is None]

    return {
        "ready_now": len(frontier["ready"]),
        "refused_subjects": len(subjects),
        "refused_group_memberships": sum(
            n for sig, n in counts.items() if sig.startswith(REFUSED_PREFIX)),
        "by_purchase": by_purchase,
        "total_returns_to_ready": sum(r["returns_to_ready"]
                                      for r in open_rows),
        "returns_if_every_open_row_lands": len(
            [s for s in subjects.values() if s <= open_met]),
        # Supply that is PAID FOR and not yet collected: every signal holding
        # these subjects is met by a LANDED purchase, so the only thing
        # between them and the intake window is a corpus cycle running
        # `intake_from_frontier --unblocked`.  Named subjects, not just a
        # count, so the next driver can act on it without re-deriving it.
        "awaiting_unblock_run": len(awaiting),
        "awaiting_unblock_subjects": awaiting,
        "no_purchase_meets": unmet,
        "honesty": _REFILL_HONESTY,
    }


def _load_registry(root: str):
    """The growth registry AT ``root``, READ-ONLY (GROWERS + ANTI_LIST).
    Loaded rather than parsed: the registry is ceremony-fenced, and a view
    that re-derived its contents from source text could disagree with the
    module the rest of the repo runs.

    LOADED BY PATH, not by name.  ``sys.path.insert`` + ``import_module``
    returns whatever ``sys.modules`` already holds under
    ``buildloop.growth_protocol`` -- which, in-process, is the module the
    CALLER imported, not the one at ``--root``.  So a build against a
    non-default root derived its statuses from THIS repo's registry while
    ``derived_from`` pinned the sha256 of the OTHER root's bytes: a
    reconciliation pin over inputs the derivation never read, which is worse
    than no pin at all.  It also left the injected ``sys.path`` entry behind
    for every later import in the process.  ``spec_from_file_location``
    against the root's own file answers both, and the ``finally`` restores
    the path whatever the module does on the way up."""
    path = os.path.join(root, REGISTRY)
    saved = list(sys.path)
    try:
        sys.path.insert(0, root)
        spec = importlib.util.spec_from_file_location(
            "_purchase_frontier_registry", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"growth registry not loadable at {path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = saved
    return dict(mod.GROWERS), tuple(mod.ANTI_LIST)


def _receipt_ok(root: str, path: str, needle: str) -> bool:
    """Is this receipt REAL evidence -- a regular, non-empty file that
    actually says the thing it is cited for?

    THE DEFECT (a bare ``os.path.exists``).  Status is supposed to be a fact
    about the tree, and existence is the weakest possible reading of one: a
    DIRECTORY named ``results/p3_delta.md`` and a zero-byte file both read
    ``purchased``.  Worse, p3-split and p4-split declare the SAME path (one
    receipt, two instruments, deliberately not duplicated), so existence
    could not distinguish them at all -- and historically, between a43619b
    and f3bc199, a receipt that PREDATED its purchase satisfied the p4 row
    exactly as a real one would.

    So receipts adopt the repo's own ``growth_protocol.conformance()`` teeth
    idiom: a (path, needle) pair, the file must be a regular file, non-empty,
    and contain its needle.  That is what makes one shared document answer
    two rows honestly -- each cites the sentence it is evidence FOR, and a
    receipt that stops saying it stops counting."""
    full = os.path.join(root, path)
    if not os.path.isfile(full):
        return False
    try:
        with open(full, encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError):
        return False
    return bool(text.strip()) and needle in text


def derive_status(row: dict, growers, root: str) -> str:
    """A purchase's status, DERIVED from the tree.

    Precedence is fixed and the pin comes FIRST: a status-pinned row
    (``trust-root``/``parked``) can never be computed into ``purchased``, so
    planting a registry row or a receipt named after P5 buys exactly nothing.
    That ordering IS the anti-list doctrine expressed as control flow.

    Otherwise the row's DECLARED evidence kind decides, and an empty
    evidence list is never vacuously satisfied -- "no rows required" would
    make every unlanded purchase read as bought.

    Receipt evidence is a (path, needle) pair per ``_receipt_ok``: existence
    alone certified a directory, an empty file, and a receipt predating its
    own purchase."""
    pin = row.get("status_pin")
    if pin is not None:
        return pin
    if row["evidence"] == "grower":
        keys = row["grower_keys"]
        return "purchased" if keys and all(k in growers for k in keys) \
            else "open"
    if row["evidence"] == "receipt":
        pairs = row["receipts"]
        return "purchased" if pairs and all(
            _receipt_ok(root, p, n) for p, n in pairs) else "open"
    return "open"


def _unblocked_by(purchase_id: str) -> list:
    """The refusal signals filed against one purchase, by INVERTING the
    single-source map (never a second hand-kept list to drift against)."""
    return sorted(sig for sig, (key, _reason) in SIGNAL_UNBLOCKED_BY.items()
                  if key == purchase_id)


# --------------------------------------------------------------------------- #
# The builder.
# --------------------------------------------------------------------------- #
def build_purchase_frontier(root: str, *, growers=None) -> dict:
    """Join the declared §4 queue against the live census prices, the live
    refusal groups, and the live growth registry.

    ``growers`` is injectable so the status rule can be exercised against
    synthetic registries in the teeth; the default reads the real module."""
    with open(os.path.join(root, FRONTIER)) as fh:
        frontier = json.load(fh)
    with open(os.path.join(root, CENSUS)) as fh:
        census = json.load(fh)

    live_growers, anti_list = _load_registry(root)
    if growers is None:
        growers = live_growers

    counts = _signal_counts(frontier)
    census_vocab = set(census["miss_histogram"])

    rows = []
    for pid, row in PURCHASES.items():
        # A priced signal that is not census vocabulary is a typo or a
        # renamed category, and a queue priced in words the census does not
        # measure is a queue priced in nothing.
        unknown = [s for s in row["prices_signals"] if s not in census_vocab]
        if unknown:
            raise ValueError(
                f"{pid}: prices_signals not in the census vocabulary: "
                f"{unknown} (regenerate the census, or fix the declaration)")
        # A row is priced on the census axis, on the refusal axis, or on
        # both -- never on neither.  The empty list is how a refusal-priced
        # row DECLARES where its price lives, so the check is over the pair;
        # a row priced by nothing is a wish written into a queue, which is
        # the shape "we'll work out the bill later" takes when nobody looks.
        if not row["prices_signals"] and not row["unblocks_refusals"]:
            raise ValueError(
                f"{pid}: priced by neither census signals nor refusal "
                f"signals -- a queue entry priced in nothing is a wish, not "
                f"a purchase")
        # The anti-list clause a trust-root row cites must still BE on the
        # anti-list; deleting the doctrine reds this tool instead of quietly
        # promoting the row it protects.
        clause = row.get("anti_list_ref")
        if clause is not None and clause not in anti_list:
            raise ValueError(
                f"{pid}: anti_list_ref {clause!r} is no longer in "
                f"growth_protocol.ANTI_LIST -- the trust-root doctrine this "
                f"row cites moved; that is a ceremony question, never a "
                f"regeneration")
        # A class claim that rests on a MEASUREMENT cites the file that made
        # it, and the citation has to keep saying the thing: the file must
        # exist, be non-empty, and still contain the NAMED test (the
        # growth_protocol.conformance teeth idiom), and the row's own notes
        # must cite the same path so the published prose and the checked
        # evidence are one citation.  Renaming the proof out from under the
        # declaration is how "measured" quietly becomes "asserted".
        for path, needle in row.get("class_evidence", []):
            if not _receipt_ok(root, path, needle):
                raise ValueError(
                    f"{pid}: bill_class {row['bill_class']!r} cites {path} "
                    f"for {needle!r}, and that file is gone, empty, or no "
                    f"longer contains it -- a class claim standing on a "
                    f"citation that says nothing; re-measure or re-declare, "
                    f"never regenerate past it")
            if path not in row["notes"]:
                raise ValueError(
                    f"{pid}: class_evidence cites {path} but the published "
                    f"notes do not, so the artifact's reader cannot reach "
                    f"the measurement the class rests on")
        status = derive_status(row, growers, root)
        if status not in _STATUSES:
            raise ValueError(f"{pid}: status {status!r} outside the declared "
                             f"vocabulary {_STATUSES}")
        rows.append({
            "purchase_id": pid,
            "plan_ref": row["plan_ref"],
            "title": row["title"],
            "bill_class": row["bill_class"],
            "status": status,
            "prices_signals": {s: counts.get(s, 0)
                               for s in row["prices_signals"]},
            "blocking_refusals": {
                sig: counts.get("refused:" + sig, 0)
                for sig in _unblocked_by(pid)},
            # PATHS only in the artifact: the needle is how the derivation
            # reads a receipt, not a fact about the queue, and the row's
            # published shape stays what a reader wants (which document).
            "receipts": sorted({p for p, _needle in row["receipts"]}),
            "notes": row["notes"],
        })

    derived_from = {}
    for rel in INPUTS:
        with open(os.path.join(root, rel), "rb") as fh:
            derived_from[rel] = common.sha256_bytes(fh.read())
    # Receipts are inputs too -- status is read off them -- so they are pinned
    # beside the census and the registry, with an explicit sentinel where a
    # declared receipt is not on disk.  A receipt appearing or disappearing
    # then reads as recorded STALENESS demand (regenerate), never as a
    # silently different derivation.
    for rel in sorted({p for r in PURCHASES.values() for p, _n in r["receipts"]}):
        full = os.path.join(root, rel)
        if os.path.isfile(full):
            with open(full, "rb") as fh:
                derived_from[rel] = common.sha256_bytes(fh.read())
        else:
            derived_from[rel] = RECEIPT_ABSENT

    return {
        "derived_from": derived_from,
        "purchases": rows,
        "refill_projection": _refill_projection(frontier, rows),
        "honesty": _HONESTY,
    }


def _write(doc: dict, out_path: str) -> None:
    with open(out_path, "w") as fh:
        fh.write(common.canonical_json(doc) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))),
        help="repo root (inputs are read at their repo-relative paths)")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("purchase-frontier"):
        doc = build_purchase_frontier(args.root)
    out_path = os.path.join(args.root, "results", "purchase_frontier.json")
    _write(doc, out_path)
    by_status: dict = {}
    for r in doc["purchases"]:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    proj = doc["refill_projection"]
    print(f"purchase_frontier: {len(doc['purchases'])} rows "
          f"({by_status}) -> {out_path}")
    # The stall reading, printed beside the status counts: "0 open" next to a
    # full refusal ledger was the FALSE ZERO this section exists to end, and
    # a session reading only stdout should not have to open the file to see
    # what would refill the window.
    print(f"  ready now {proj['ready_now']}; "
          f"{proj['refused_subjects']} refused subjects "
          f"({proj['refused_group_memberships']} group memberships); "
          f"open rows would return {proj['total_returns_to_ready']} "
          f"one at a time, {proj['returns_if_every_open_row_lands']} if all "
          f"land")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
  grower) is ``purchased`` when its delta receipt exists.  Each row DECLARES
  which evidence kind it is answerable to; neither kind is ever inferred.
- BLOCKING REFUSALS invert ``SIGNAL_UNBLOCKED_BY`` -- the measured-refusal
  vocabulary of ``tools/frontier_refusals.py``, every signal of which is
  mapped to the purchase that would meet it or to ``None`` WITH A REASON.
  Naming a purchase that does not actually meet a signal would manufacture
  demand out of a plan, which is the same sin as distorting a reading to
  force a green.

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
SOURCE TEXT: "an input moved" then reads as recorded STALENESS demand
(regenerate), distinct from "the derivation is wrong" (a red byte-compare) --
the ``tools/proof_queue.py`` convention.

REGEN-DAG MEMBER (final group, beside the hammer pair): the census moves the
prices every growth cycle, so this artifact must regenerate mechanically or
its byte teeth red the next merge (the PR #39 lesson, paid once already).

Deterministic, LLM-free, Lean-free, network-free; no wall-clock.  Same
canonical-JSON discipline as the other ``results/`` writers.

OUTPUT: ``results/purchase_frontier.json`` (schema: ``derived_from``,
``purchases``, ``honesty``).
"""
from __future__ import annotations

import argparse
import importlib
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
    "tower-class":
        "a purchase whose faithful shape re-bases the certification TOWER -- "
        "a carrier threading every walker's type discipline rather than "
        "adding a constructor beside it.  Named so the queue can say when a "
        "row's honest shape is this and the session scoped it down to "
        "additive-reflect behind a fail-closed skip, instead of pretending "
        "the smaller bill was the whole bill.",
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
#: many -- the counts are read from the frontier artifact); ``bill_class``
#: is the declared bill shape; ``evidence`` selects the status rule
#: ("grower" -> its GROWERS rows exist; "receipt" -> its delta receipts
#: exist; "none" -> the row is status-pinned and answers to neither);
#: ``status_pin`` freezes a row that must never be computed; ``anti_list_ref``
#: (P5 only) is verified live against ANTI_LIST at build time.
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
        "receipts": ["results/p1_delta.md"],
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
        "receipts": ["results/p2_delta.md"],
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
        "receipts": ["results/p3_delta.md"],
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
        "receipts": ["results/p3_delta.md"],
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
        "receipts": ["results/p5_shadow.md"],
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
SIGNAL_UNBLOCKED_BY = {
    "symbolic-exponent": (
        None,
        "the bound is the exponent itself, so nothing bounded-by-a-literal "
        "reaches it: it needs induction over exponents, a proof-shape "
        "purchase no §4 row is",
    ),
    "function-symbol": (
        None,
        "an arbitrary NAMED function (factorial, the sequences a_n/d_n/F_n, "
        "the Bezout coefficients) needs a definitional-extension mechanism; "
        "no carrier and no bounded node class supplies one",
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
        "a comparison the operator-words grower can price as an ordinary "
        "word; that mechanism already exists, so this is a candidate for the "
        "operator mint, not a §4 queue entry",
    ),
    "exists-only-shape": (
        None,
        "the demand is on the ANCHOR/witness-template axis (run/anchor.py, "
        "the witness-template-shapes planned grower), not on the fragment's "
        "carrier or node-class axis",
    ),
    "definition-biconditional": (
        None,
        "a DEFINITION's content is the biconditional; the fragment has no "
        "definitional-extension mechanism, which is a distinct purchase from "
        "every carrier and node class in the queue",
    ),
    "iff-connective": (
        None,
        "a propositional primitive: _CONNECTIVES is exactly {and, or, "
        "implies}.  Growing it is its own bill and is not queued in §4",
    ),
    "not-connective": (
        None,
        "the same propositional axis as iff-connective -- the fragment has no "
        "negation of an atom -- and the same answer: its own bill, not a "
        "queued one",
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
        "the subject USES a predicate the corpus defines elsewhere; unfolding "
        "RELOCATES the demand rather than meeting it, and the definitional "
        "mechanism it really needs is not queued",
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
        None,
        "P2 bought setbuild only as card's ARGUMENT, so a set can be counted "
        "but never inhabited: this needs a set OBJECT carrier and its "
        "membership atom, a NEW queue entry no §4 row covers.  It is not "
        "filed under P2, which is already purchased and did not meet it",
    ),
}

_STATUSES = ("purchased", "open", "trust-root", "parked")


# --------------------------------------------------------------------------- #
# Loaders / derivations.
# --------------------------------------------------------------------------- #
def _signal_counts(frontier: dict) -> dict:
    """signal name -> node_count over the frontier's blocked groups.  Both
    census signals (bare) and demotion groups (``refused:``/``parked:``
    prefixed) live in one namespace here, exactly as the artifact writes
    them."""
    return {g["signal"]: g["node_count"] for g in frontier["blocked"]}


def _load_registry(root: str):
    """The growth registry, READ-ONLY (GROWERS + ANTI_LIST).  Imported rather
    than parsed: the registry is ceremony-fenced, and a view that re-derived
    its contents from source text could disagree with the module the rest of
    the repo runs."""
    sys.path.insert(0, root)
    mod = importlib.import_module("buildloop.growth_protocol")
    return dict(mod.GROWERS), tuple(mod.ANTI_LIST)


def derive_status(row: dict, growers, root: str) -> str:
    """A purchase's status, DERIVED from the tree.

    Precedence is fixed and the pin comes FIRST: a status-pinned row
    (``trust-root``/``parked``) can never be computed into ``purchased``, so
    planting a registry row or a receipt named after P5 buys exactly nothing.
    That ordering IS the anti-list doctrine expressed as control flow.

    Otherwise the row's DECLARED evidence kind decides, and an empty
    evidence list is never vacuously satisfied -- "no rows required" would
    make every unlanded purchase read as bought."""
    pin = row.get("status_pin")
    if pin is not None:
        return pin
    if row["evidence"] == "grower":
        keys = row["grower_keys"]
        return "purchased" if keys and all(k in growers for k in keys) \
            else "open"
    if row["evidence"] == "receipt":
        paths = row["receipts"]
        return "purchased" if paths and all(
            os.path.exists(os.path.join(root, p)) for p in paths) else "open"
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
            "receipts": sorted(row["receipts"]),
            "notes": row["notes"],
        })

    derived_from = {}
    for rel in INPUTS:
        with open(os.path.join(root, rel), "rb") as fh:
            derived_from[rel] = common.sha256_bytes(fh.read())

    return {
        "derived_from": derived_from,
        "purchases": rows,
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
    print(f"purchase_frontier: {len(doc['purchases'])} rows "
          f"({by_status}) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

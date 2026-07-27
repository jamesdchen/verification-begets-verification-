#!/usr/bin/env python3
"""Supply status: CAN THE LOOP ACTUALLY MAKE PROGRESS, and by which path?

The instrument gap this closes.  Every meter we owned reported a LOOP: the
frontier reports its ready/blocked split, the purchase queue reports its
statuses, the watchdog reports whether a driver fired.  None of them reports
the SUPPLY -- whether any of those loops has material to consume -- and so
the two states we most need to tell apart became indistinguishable:

    HEALTHY = the drivers are firing and there is nothing to do
    WEDGED  = the drivers are firing and there is nothing they CAN do

Both read as "idle, no corrective action" to a watchdog whose healthy case
is idleness.  Meanwhile every fact needed to separate them was already sitting
in committed artifacts: ``results/frontier.json`` ready was zero, the park
ledger held zero rows, the purchase queue held zero OPEN rows, and 45 distinct
subjects sat in ``refused:*`` groups waiting on purchases that would un-gate
their signals.  Discoverable, and nothing computed it.  This tool computes it,
and says the word WEDGED out loud when it is true.

THE FOUR SUPPLY PATHS.  Ready work is the loop's OUTPUT; these are the four
ways new ready work can come into existence, and each is priced from the
artifact that owns it:

  census-signal-ungating  a purchase lands and its census signal stops
                          gating -- the only path a driver can walk
                          UNATTENDED, so it is the only one that can compute
                          to ``purchase-work-available``.  Read off the OPEN
                          rows of ``results/purchase_frontier.json``, counting
                          BOTH ways a row declares demand (``prices_signals``
                          for a fragment purchase, ``blocking_refusals`` for a
                          refusal-driven one), with every count RE-DERIVED
                          from the frontier's live blocked-group counts (a
                          number copied out of the queue file would inherit
                          exactly the staleness this tool exists to catch),
                          and then filtered by the row's declared
                          ``bill_class`` -- see THE ATTENDANCE FILTER below.
  park-lifts              a maintainer decision retires a ``parked:<reason>``
                          hold.  Counted from ``results/frontier_parks.jsonl``.
                          Never machine-actionable BY DESIGN: a park is a
                          decision, and this reading never makes it.
  refusal-retirement      a purchase retires a ``refused:<signal>`` group --
                          measured demand, counted off the frontier's own
                          refused groups.  Also never machine-actionable: it
                          waits on the purchase, not on this reading.
  new-corpus-intake       intake material the census has never priced.  This
                          path is ALWAYS available -- the supply is outside
                          the tree -- but AVAILABLE and MACHINE-ACTIONABLE
                          part company here, and the second of them is read
                          off the DECLARATION POINT: see THE DECLARATION
                          FILTER below.

THE ATTENDANCE FILTER (the blind spot this tool shipped WITH, measured and
closed).  Demand is not the whole question.  A row can carry live census
demand and still be work no unattended session may start, because
PLAN_FRAGMENT §3.1 rule 3 binds an unattended session to the ADDITIVE class:
anything that adds a `Tm`/`Pd` constructor, a new evaluation tower, or an
import-pin widening is TOWER-class and "splits out as a NAMED attended
follow-up".  The first cut of this reading counted demand and stopped there,
so on a night when every OPEN row was outside the additive family it
reported ``purchase-work-available`` at a machine that could not take a
single one of them -- the tool built to say WEDGED had the wedge's own blind
spot, and the watchdog above it reported healthy for eight hours.  So the
declared ``bill_class`` is now READ, and it gates ``machine_actionable``:

  * takeable unattended  the additive family, ``UNATTENDED_BILL_CLASSES`` --
                         additive-reflect and additive-desugaring by rule 3's
                         own clauses, census-instrument because it grows no
                         grammar at all, so rule 3(a) is never reached.
  * blocked-pending-attendance  every other declared class.  Reported with
                         its own verdict shape and its own count; NOT
                         silently folded into "nothing is open" (the row IS
                         open, and a maintainer may take it today), and NOT
                         counted as work a driver firing can start.
  * no ``bill_class`` at all  a schema break on an OPEN row, handled exactly
                         like a missing ``status``: the whole path goes
                         unknown.  A queue row whose bill shape we cannot
                         read is not a measurement of anything.

WE DO NOT READ ``results/lean_env.json``, ON PURPOSE.  Rule 3's capability
condition does lift the additive-only restriction -- but only for a probe RUN
IN THE SESSION, because (that artifact's own ``scope`` field says it) a
committed ``lean-local`` is evidence about the machine that WROTE it and
licenses nothing for the machine reading it.  A derived, offline artifact
like this one can never satisfy that condition, so it never claims to: it
reports the tower-class rows as blocked and NAMES the two routes that would
unblock them (``ATTENDANCE_ROUTES``).  Reading the file here and "taking it
into account" would manufacture exactly the stale permission rule 3 clause
(ii) exists to forbid.

THE DECLARATION FILTER (the attendance filter's shape, applied to the one
path this reading called machine-actionable on a dry registry).  Automating
the intake path did not make every intake unattended-takeable; it moved the
human judgment from per-cycle to PER-CANDIDATE, into
``specs/mathsources/corpus_candidates.json``.  A driver firing reaches that
path through ``tools/corpus_candidates.py``, which selects the first row
still marked ``candidate`` IN DECLARATION ORDER -- and when no such row
exists it answers ``registry-exhausted``/``registry-empty``, at which point
the DRIVER prompt's own words send the driver to a corpus "the maintainer
has NAMED", which is attendance.  So the prompt grep answers only half the
question: it says the driver KNOWS the command, never that the driver has a
row to run it on.  Gating on the grep alone reproduced the attendance
filter's original defect one path over -- MEASURED on 2026-07-26 (C3 cycle
21), when this reading named ``new-corpus-intake`` as an exit in a
``supply-blocked`` verdict on the very firing whose selector had just
answered ``registry-exhausted``.  The declaration state is therefore READ,
from the selector itself rather than re-derived here (two implementations of
one rule drift; one does not), and it gates ``machine_actionable``:

  * ``candidate-available``   a declared row is selectable -- and only then
                              can a driver firing walk this path unattended.
  * exhausted / empty         the path stays AVAILABLE (the supply is outside
                              the tree and an attended session may name any
                              corpus) and is NOT machine-actionable.  The
                              named exit becomes the true one: a maintainer
                              appending one row.
  * absent / unreadable       ``unknown``, never "no candidates" -- an
                              errored read never impersonates an answer, and
                              inaction is the safe side, so it is not
                              machine-actionable either.

THE PROMPT READING IS LEXICAL AND FAILS TOWARD UNKNOWN.  A grep of a prose
file is evidence about that file's TEXT, never proof about the loop's
behaviour, and the file is edited by other work.  So a token we do not find
reads as ``unknown``, never as "the driver cannot do this"; only a token we
DO find licenses a positive claim.  The registry read above is NOT lexical --
it is the selector's own answer about its own file -- which is why it may
gate where the grep alone may not.

READS FAIL SAFE.  If a verdict-critical input is unreadable we report
``supply-unknown: <the inputs we could not read>``.  An errored read must
never impersonate an answer -- reporting "blocked" from a file we could not
open would manufacture the same false confidence we are trying to abolish.

Verdict vocabulary (deliberately tiny, so it can be matched mechanically):

    ready-work-available          the corpus driver has listed work now
    purchase-work-available       ready is empty, but an OPEN purchase carries
                                  a live nonzero census price AND a bill class
                                  an unattended session may take
    supply-blocked:               ready is empty and every open row with live
      tower-class-only <rows>     demand is outside the additive class: work
                                  EXISTS and no driver firing may start it,
                                  which is a different sentence from both of
                                  the two below
    supply-blocked: <paths>       nothing at all is takeable -- and here are
                                  the named paths, with counts, that could
                                  unblock it
    supply-unknown: <inputs>      a verdict-critical artifact did not read

The two blocked shapes share a prefix deliberately: every downstream matcher
(``tools/session_brief.py``) keys on ``supply-blocked`` and stays correct,
while a reader gets the distinction the first cut of this vocabulary could
not express.

Deterministic, offline, LLM-free, Lean-free, no wall-clock: same canonical
JSON discipline as the census/frontier writers (sorted keys, fixed indent,
trailing newline), and ``derived_from`` pins every input by sha256 so an
input that MOVED reads as recorded staleness demand, distinct from a
derivation that is WRONG.

OUTPUT: ``results/supply_status.json`` (schema: ``derived_from``,
``frontier_ready``, ``honesty``, ``paths``, ``verdict``).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from tools import corpus_candidates

#: The declaration point the new-corpus path is gated on, as a repo-relative
#: path (it is also an INPUT, so a moved registry reads as staleness).
CANDIDATE_REGISTRY = "specs/mathsources/corpus_candidates.json"

#: Every file this reading consumes, pinned by sha256 in ``derived_from``.
INPUTS = (
    "C3_PROMPTS.md",
    CANDIDATE_REGISTRY,
    "results/census_portfolio.json",
    "results/frontier.json",
    "results/frontier_parks.jsonl",
    "results/purchase_frontier.json",
)

#: The ONE selector answer under which a driver firing may walk the
#: new-corpus path unattended.  A whitelist for the attendance filter's own
#: reason: a reason invented later is unattended-BLOCKED until someone argues
#: it into this tuple, which is the fail-safe direction.
DECLARATION_ACTIONABLE = ("candidate-available",)

#: Pin sentinel for a declared input that is not on disk.  The KEY stays, so
#: "the input vanished" and "this artifact predates the pin" never collapse
#: into the same observation (the purchase_frontier receipt-pin precedent).
INPUT_ABSENT = "(absent)"

#: Inputs whose loss makes the VERDICT unknowable rather than merely
#: less-detailed: without the frontier we cannot count ready work, and
#: without the purchase queue we cannot say no purchase is actionable.
VERDICT_CRITICAL = ("results/frontier.json", "results/purchase_frontier.json")

#: The declared bill classes an UNATTENDED session may take under
#: PLAN_FRAGMENT §3.1 rule 3 -- the ADDITIVE family, and nothing else.  The
#: first two are rule 3's own additive class (constructor addition only /
#: no constructor at all); ``census-instrument`` grows no grammar whatever,
#: so rule 3(a) is not reached and its bill is a measurement plus a receipt.
#: Membership is a WHITELIST on purpose: a bill class invented later is
#: unattended-BLOCKED until someone argues it into this tuple, which is the
#: fail-safe direction for a reading whose whole job is to stop reporting
#: work a driver firing cannot start.
UNATTENDED_BILL_CLASSES = (
    "additive-desugaring",
    "additive-reflect",
    "census-instrument",
)

#: The two routes that turn a tower-class row into work an unattended session
#: may take.  Named in the reading itself, because "blocked" without an exit
#: is a mood -- and named as ACTS, since neither is a state this artifact can
#: observe: both happen in a session, after this file was written.
ATTENDANCE_ROUTES = (
    "an ATTENDED session (a maintainer present to read the red) takes it "
    "deliberately; or tools/lean_env_probe.py RUN IN THE SESSION reads "
    "lean-local, which is PLAN_FRAGMENT §3.1 rule 3's capability condition; "
    # UNBRACKETED deliberately: the bracketed form is the lane's commit-message
    # TRIGGER, matched anywhere in a head commit message, and this string is
    # quoted by driver summaries.  A bracketed marker here would let a session
    # fire the lane by reporting the verdict it was told to report.
    "or the lean-hammer batch ride's AUTHORING kind "
    "(results/reflect_candidates.json -> run/reflect_ride.py, PLAN_HAMMER.md "
    "H-H1.3) lets an unattended session iterate on tower-class slice text at "
    "a session boundary per ride"
)

#: Why ``results/lean_env.json`` is NOT in INPUTS and is never consulted.
#: Kept as a named constant, and published on the row, so the omission reads
#: as a decision with a reason rather than an oversight a later edit "fixes".
LEAN_ENV_IS_NOT_A_PERMISSION = (
    "results/lean_env.json is deliberately NOT read here: its own scope field "
    "says a committed lean-local verdict is evidence about the machine that "
    "WROTE it and licenses nothing for the machine reading it, so rule 3's "
    "capability condition is satisfied only by a probe RUN IN-SESSION -- "
    "which a derived offline artifact can never be"
)

#: The prompt tokens whose presence licenses a positive automation claim.
#: Ordered most-specific first: finding the new-corpus command outranks
#: finding only the ready-list one.
PROMPT_TOKENS = ("intake_corpus", "intake_from_frontier")

#: path -> what would make that path yield ready work.  Naming the unblocker
#: is the point of the reading: "blocked" without a named exit is a mood.
UNBLOCKED_BY = {
    "census-signal-ungating":
        "a purchase in results/purchase_frontier.json moving to purchased, "
        "which un-gates its census signal; the corpus driver then runs "
        "intake_from_frontier --unblocked SIGNAL -- and for a row whose "
        "declared bill_class is outside the additive family, that purchase "
        "needs attendance first: " + ATTENDANCE_ROUTES,
    "new-corpus-intake":
        "tools/intake_corpus.py on a source the census has never priced, "
        "then the regen chain; the supply is outside the tree, so this path "
        "is never exhausted -- but a DRIVER FIRING reaches it only through "
        "tools/corpus_candidates.py, so unattended it waits on a maintainer "
        "appending one row (name, source, adapter, project, declared_by, "
        "rationale) to specs/mathsources/corpus_candidates.json; with the "
        "registry dry the exit is ATTENDED -- a corpus the maintainer names",
    "park-lifts":
        "an explicit maintainer decision per park reason (a C3 decision PR "
        "carrying only the --lift rows and the regen chain); never taken by "
        "a driver, and this reading never takes it",
    "refusal-retirement":
        "the purchase named by each refused:<signal> group landing, after "
        "which the refused subjects are re-read as ordinary demand",
}

_HONESTY = (
    "counts are ARTIFACT ROW COUNTS, never predictions: a priced signal says "
    "how many nodes mention the vocabulary, never how many would certify, and "
    "a named path is a path that COULD unblock the loop, never a "
    "recommendation to walk it; machine_actionable means only that a "
    "committed driver prompt reaches the path unattended AND (on the purchase "
    "path) that the row's DECLARED bill_class is one PLAN_FRAGMENT §3.1 rule "
    "3 lets an unattended session take AND (on the new-corpus path) that the "
    "DECLARATION POINT specs/mathsources/corpus_candidates.json still holds a "
    "row marked candidate, asked of tools/corpus_candidates.py itself so the "
    "reading and the driver cannot disagree -- a dry registry leaves that "
    "path AVAILABLE (an attended session may name any corpus; the supply is "
    "outside the tree) and NOT machine-actionable, and an absent or "
    "unreadable registry reads as its own named reason and is not "
    "machine-actionable either; never that the work is small and "
    "never a prediction of the diff -- bill_class is a declared intention, "
    "so a row this reading calls blocked-pending-attendance is blocked by "
    "what the queue SAYS it is, not by anything measured about the material; "
    "a tower-class row is blocked, NEVER dead, and a maintainer may take it "
    "today; results/lean_env.json is not consulted at all, because a "
    "committed lean-local verdict is evidence about the machine that wrote "
    "it and rule 3's capability condition admits only a probe RUN in-session; "
    "the driver-automation reading is a LEXICAL grep of "
    "C3_PROMPTS.md, so a token we did not find reads as unknown and NEVER as "
    "absent (the file is edited by other work); refused-group entries "
    "double-count a subject carrying several signals, which is why subjects "
    "and entries are reported separately; and a verdict-critical input that "
    "did not read yields supply-unknown -- an errored read never impersonates "
    "an answer"
)


# ------------------------------------------------------------------ readers
def _read_bytes(root: str, rel: str):
    try:
        with open(os.path.join(root, rel), "rb") as fh:
            return fh.read()
    except OSError:
        return None


def _read_json(root: str, rel: str):
    """Parsed JSON, or a ``{"_unavailable": ...}`` marker -- the brief's
    degrade convention, reused so a half-built tree still gets a reading."""
    raw = _read_bytes(root, rel)
    if raw is None:
        return {"_unavailable": f"{rel}: missing"}
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        return {"_unavailable": f"{rel}: {e.__class__.__name__}"}


def _read_jsonl(root: str, rel: str):
    """(rows, unavailable_reason).  An ABSENT ledger is zero rows by
    construction (``frontier_parks.load_rows`` says the same), which is a
    measurement; a ledger that is present and unparseable is not."""
    raw = _read_bytes(root, rel)
    if raw is None:
        return [], None
    rows = []
    try:
        for line in raw.decode("utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except (UnicodeDecodeError, ValueError) as e:
        return [], f"{rel}: {e.__class__.__name__}"
    return rows, None


def _pins(root: str) -> dict:
    out = {}
    for rel in INPUTS:
        raw = _read_bytes(root, rel)
        out[rel] = INPUT_ABSENT if raw is None else common.sha256_bytes(raw)
    return out


def _row(path: str, *, known: bool, available: bool, machine_actionable: bool,
         count: int, count_of: str, detail: dict) -> dict:
    return {
        "path": path,
        "known": known,
        "available": available,
        "machine_actionable": machine_actionable,
        "count": count,
        "count_of": count_of,
        "unblocked_by": UNBLOCKED_BY[path],
        "detail": detail,
    }


# ------------------------------------------------------------- the four paths
def _blocked_counts(frontier) -> dict:
    """signal -> live node_count, off the frontier's blocked groups."""
    if "_unavailable" in frontier:
        return {}
    return {g["signal"]: g["node_count"] for g in frontier.get("blocked", [])
            if isinstance(g, dict) and "signal" in g}


#: What we count on this path, and therefore what the verdict says.  The
#: phrase carries BOTH halves of the question on purpose: the first cut said
#: only "with live nonzero census demand", and a count_of that names only
#: demand is how a count of unavailable work got read as available work.
_UNGATING_COUNT_OF = ("open purchases with live nonzero census demand an "
                      "unattended session may take")


def _census_signal_ungating(purchase_frontier, live_counts: dict) -> dict:
    """Open purchase rows, priced against the LIVE frontier counts and then
    filtered by the ATTENDANCE rule.

    We read only the five fields the queue has always carried
    (``purchase_id``, ``status``, ``bill_class``, ``prices_signals``,
    ``blocking_refusals``); the queue may grow new rows and new fields
    freely.  BOTH signal maps count as demand and both are re-derived here: a
    fragment purchase declares its demand as a census price, while a
    refusal-driven purchase declares it as the ``refused:<signal>`` groups it
    would retire, and a reading that saw only the first would report the
    second's rows as unactionable -- the same false-idle the whole tool
    exists to abolish.

    Demand alone is NOT actionability, and conflating them is the defect this
    function was measured to have: ``has_live_demand`` (is there material?)
    and ``unattended_takeable`` (may a driver firing start it?) are separate
    fields, and only their CONJUNCTION is machine-actionable.  The old single
    ``actionable`` field is gone rather than redefined, because the name was
    itself the error -- it meant the first and was read as the second.

    A row with no ``status``, and an OPEN row with no ``bill_class``, are
    schema breaks rather than measurements, so either takes the whole path to
    unknown -- fail safe toward inaction, never toward a confident "nothing
    is open" or a confident "and you may take it"."""
    def unknown(reason: str) -> dict:
        return _row("census-signal-ungating", known=False, available=False,
                    machine_actionable=False, count=0,
                    count_of=_UNGATING_COUNT_OF,
                    detail={"unavailable": reason})

    if "_unavailable" in purchase_frontier:
        return unknown(purchase_frontier["_unavailable"])
    rows = purchase_frontier.get("purchases")
    if not isinstance(rows, list):
        return unknown("results/purchase_frontier.json: no purchases list")
    open_rows = []
    for r in rows:
        if not isinstance(r, dict) or "status" not in r:
            return unknown(
                "results/purchase_frontier.json: a row carries no status")
        if r["status"] != "open":
            continue
        bill_class = r.get("bill_class")
        if not isinstance(bill_class, str) or not bill_class:
            return unknown("results/purchase_frontier.json: an open row "
                           "carries no bill_class")
        priced = r.get("prices_signals")
        priced = priced if isinstance(priced, dict) else {}
        blocking = r.get("blocking_refusals")
        blocking = blocking if isinstance(blocking, dict) else {}
        live_prices = {sig: live_counts.get(sig, 0) for sig in sorted(priced)}
        # refusal demand lives under the frontier's refused:<signal> groups,
        # which is where the queue's own bare signal names resolve.
        live_refusals = {sig: live_counts.get("refused:" + sig, 0)
                         for sig in sorted(blocking)}
        demand = (any(n > 0 for n in live_prices.values())
                  or any(n > 0 for n in live_refusals.values()))
        takeable = bill_class in UNATTENDED_BILL_CLASSES
        open_rows.append({
            "purchase_id": str(r.get("purchase_id", "?")),
            "bill_class": bill_class,
            "live_prices": live_prices,
            "live_refusal_demand": live_refusals,
            "declares_signals": bool(priced or blocking),
            "has_live_demand": demand,
            "unattended_takeable": takeable,
            "machine_actionable": demand and takeable,
        })
    open_rows.sort(key=lambda r: r["purchase_id"])
    actionable = [r["purchase_id"] for r in open_rows if r["machine_actionable"]]
    # rows with real material that no driver firing may start.  Reported as
    # their own number: folding them into the actionable count is the bug,
    # and dropping them entirely would be the opposite lie.
    pending = [{"purchase_id": r["purchase_id"], "bill_class": r["bill_class"]}
               for r in open_rows
               if r["has_live_demand"] and not r["unattended_takeable"]]
    return _row(
        "census-signal-ungating",
        known=True,
        available=bool(open_rows),
        machine_actionable=bool(actionable),
        count=len(actionable),
        count_of=_UNGATING_COUNT_OF,
        detail={"n_open": len(open_rows), "open": open_rows,
                "actionable_purchase_ids": sorted(actionable),
                "unattended_bill_classes": list(UNATTENDED_BILL_CLASSES),
                "blocked_pending_attendance": pending,
                "attendance_routes": ATTENDANCE_ROUTES,
                "lean_env_note": LEAN_ENV_IS_NOT_A_PERMISSION},
    )


def _park_lifts(rows: list, unavailable) -> dict:
    if unavailable is not None:
        return _row("park-lifts", known=False, available=False,
                    machine_actionable=False, count=0,
                    count_of="park ledger rows",
                    detail={"unavailable": unavailable})
    by_reason: dict = {}
    for r in rows:
        reason = str(r.get("reason", "?")) if isinstance(r, dict) else "?"
        by_reason[reason] = by_reason.get(reason, 0) + 1
    return _row(
        "park-lifts",
        known=True,
        available=bool(rows),
        # a park is lifted by a DECISION; no driver may take it, so this
        # path can never compute to machine-actionable.
        machine_actionable=False,
        count=len(rows),
        count_of="park ledger rows",
        detail={"n_rows": len(rows), "by_reason": by_reason},
    )


def _refusal_retirement(frontier) -> dict:
    if "_unavailable" in frontier:
        return _row("refusal-retirement", known=False, available=False,
                    machine_actionable=False, count=0,
                    count_of="distinct subjects in refused:* groups",
                    detail={"unavailable": frontier["_unavailable"]})
    groups, entries, subjects = {}, 0, set()
    for g in frontier.get("blocked", []):
        if not isinstance(g, dict) or not str(g.get("signal", "")).startswith(
                "refused:"):
            continue
        groups[g["signal"]] = g.get("node_count", 0)
        entries += g.get("node_count", 0)
        for n in g.get("nodes", []):
            subjects.add(n.get("text_sha256"))
    return _row(
        "refusal-retirement",
        known=True,
        available=bool(subjects),
        # retiring a refusal waits on the purchase named by its signal.
        machine_actionable=False,
        count=len(subjects),
        count_of="distinct subjects in refused:* groups",
        detail={"n_groups": len(groups), "n_group_entries": entries,
                "n_distinct_subjects": len(subjects), "by_signal": groups},
    )


def _prompt_automation(prompt_text):
    """(state, mentions) from a LEXICAL grep of the driver prompt.

    Positive findings only: the new-corpus command outranks the ready-list
    one, and finding NEITHER is ``unknown`` -- we do not get to conclude
    "the driver cannot do this" from a substring we did not see."""
    if prompt_text is None:
        return "unknown", {tok: False for tok in PROMPT_TOKENS}
    mentions = {tok: (tok in prompt_text) for tok in PROMPT_TOKENS}
    if mentions["intake_corpus"]:
        return "automates-new-corpus-intake", mentions
    if mentions["intake_from_frontier"]:
        return "automates-ready-list-only", mentions
    return "unknown", mentions


def _declaration(root: str) -> dict:
    """The DECLARATION POINT's own answer, asked of the selector.

    Delegated rather than re-derived: ``tools/corpus_candidates.py`` is what
    a driver firing actually consults, so asking it directly is the only way
    this reading and the driver cannot disagree about whether a row exists.
    Its reasons are already a fixed vocabulary and its failures are already
    named (``registry-absent``/``registry-unreadable``), so an errored read
    arrives here as a reason, never as a crash and never as "no candidates"."""
    sel = corpus_candidates.select(os.path.join(root, CANDIDATE_REGISTRY))
    return {"declaration_reason": sel["reason"],
            "declared_counts": dict(sel["counts"])}


def _new_corpus_intake(prompt_text, census, root) -> dict:
    state, mentions = _prompt_automation(prompt_text)
    n_corpora = census.get("n_corpora") if "_unavailable" not in census else None
    declared = _declaration(root)
    detail = {"prompt_automation": state, "prompt_mentions": mentions}
    detail.update(declared)
    if n_corpora is None:
        detail["unavailable"] = (census.get("_unavailable")
                                 if "_unavailable" in census
                                 else "results/census_portfolio.json: "
                                      "no n_corpora")
        n_corpora = 0
    return _row(
        "new-corpus-intake",
        known=True,
        # the supply is OUTSIDE the tree: this path is never exhausted, which
        # is why it stays AVAILABLE whatever the registry says.
        available=True,
        # ...but walking it UNATTENDED needs both halves: the prompt must
        # know the command AND the registry must declare a row to run it on.
        # The grep alone was the measured defect (see THE DECLARATION FILTER).
        machine_actionable=(
            state == "automates-new-corpus-intake"
            and declared["declaration_reason"] in DECLARATION_ACTIONABLE),
        count=int(n_corpora),
        count_of="corpora already intaken",
        detail=detail,
    )


#: Why the route is DERIVED here instead of recalled by the session.  The
#: prompt used to say "on the cycle immediately after a purchase lands, run
#: --unblocked instead" -- and cycle 23, the cycle immediately after P7
#: landed (measured 2026-07-26), consumed --ready anyway, because
#: "immediately after" lived in session memory and nothing in the brief said
#: so.  A directive computed from the committed ledger-vs-registry state is
#: stateless: it stays correct however many cycles skip it, and it clears
#: itself only when the unblock run actually happens (the run retires the
#: ledger rows this reads).
#:
#: MEASURED cycle 29, and it is why the branch reads `selectable_awaiting_
#: subjects` rather than `awaiting_unblock_run`: "the run retires the rows"
#: is FALSE for a subject that is ALREADY A CORPUS SOURCE.  The selector
#: skips those ("skipping already-intaken node"), so it retires nothing, so
#: the route re-prints the same six commands next cycle -- forever.  All 11
#: awaiting subjects were in exactly that state, which made a self-clearing
#: directive into a permanent one.  See `_selectable_awaiting`.
_NEXT_SELECTION_HONESTY = (
    "route says which intake selection the NEXT corpus cycle runs FIRST: "
    "`unblocked` while any landed purchase's paid subjects sit demoted in "
    "the append-only refusal ledger (supply already bought -- consuming "
    "--ready ahead of it strands paid supply, the cycle-23 miss), else "
    "`ready` while the ready list is non-empty, else `refill`; signals list "
    "every refused:* group whose refusals are ALL met by landed purchases "
    "AND which still holds live nodes, i.e. exactly the arguments "
    "`intake_from_frontier --unblocked` takes; the subject count is the "
    "projection's awaiting_unblock_run and inherits its upper-bound "
    "honesty; unknown inputs make the route `unknown`, never a guess")


def _selectable_awaiting(root: str, frontier, proj) -> int:
    """How many awaiting-unblock subjects `intake_from_frontier --unblocked`
    would ACTUALLY select -- the projection's count MINUS the ones already
    laid down as corpus sources.

    WHY THIS IS NOT `awaiting_unblock_run` ITSELF (measured, cycle 29).  That
    field is an UPPER BOUND and says so in its own honesty note: "a returning
    subject still has to clear the ready computation's other demotions --
    already intaken, or independently parked -- which this projection does not
    model".  Honest for a PROJECTION; wrong for a BRANCH.  Cycle 29 measured
    the degenerate case: all 11 awaiting subjects were already intaken, so all
    six printed `--unblocked` commands selected ZERO, retired nothing, and the
    route stayed `unblocked` on the next cycle -- and every cycle after it.
    The comment above promised the route "clears itself only when the unblock
    run actually happens"; the run DID happen and cleared nothing, because a
    run has nothing to retire for a subject that is already a source.

    The already-intaken predicate is IMPORTED from the selector rather than
    restated here, so the branch and the tool it routes to cannot drift: the
    number that decides the route is computed by the code that acts on it."""
    awaiting = int(proj.get("awaiting_unblock_run", 0) or 0)
    subjects = proj.get("awaiting_unblock_subjects")
    # READS FAIL SAFE, and here safe means DO NOT NARROW.  An absent or
    # malformed subject list is an input we could not read, never evidence
    # that nothing is selectable -- narrowing on it would drop the route the
    # cycle-23 miss exists to protect.  Fall back to the projection's bound.
    if not isinstance(subjects, list):
        return awaiting
    try:
        from tools.intake_from_frontier import _existing_sources
    except ImportError:
        return awaiting
    _, intaken, _ = _existing_sources(os.path.join(root, "specs", "mathsources"))
    sha = {(n.get("corpus"), n.get("node_id")): n.get("text_sha256")
           for g in frontier.get("blocked", []) if isinstance(g, dict)
           for n in g.get("nodes", []) or [] if isinstance(n, dict)}
    n = 0
    for subj in subjects:
        if not isinstance(subj, (list, tuple)) or len(subj) != 2:
            continue
        h = sha.get((subj[0], subj[1]))
        # An unmappable subject counts as selectable: this reading may narrow
        # the route only on a subject it positively READ as already intaken.
        if h is None or h not in intaken:
            n += 1
    return n


def _next_selection(purchase_frontier, frontier, ready_count: int,
                    root: str) -> dict:
    """The intake route the next corpus cycle takes, derived (see honesty)."""
    if "_unavailable" in purchase_frontier or "_unavailable" in frontier:
        return {"route": "unknown", "signals": [], "awaiting_subjects": 0,
                "selectable_awaiting_subjects": 0,
                "honesty": _NEXT_SELECTION_HONESTY}
    proj = purchase_frontier.get("refill_projection", {})
    awaiting = int(proj.get("awaiting_unblock_run", 0) or 0)
    selectable = _selectable_awaiting(root, frontier, proj)
    live = _blocked_counts(frontier)
    purchased_met = {s for row in proj.get("by_purchase", [])
                     if row.get("status") == "purchased"
                     for s in row.get("unblocks_refusals", {})}
    signals = sorted(f"refused:{s}" for s in purchased_met
                     if live.get(f"refused:{s}", 0) > 0)
    if selectable > 0 and signals:
        route = "unblocked"
    elif ready_count > 0:
        route = "ready"
    else:
        route = "refill"
    return {"route": route, "signals": signals if route == "unblocked" else [],
            "awaiting_subjects": awaiting,
            "selectable_awaiting_subjects": selectable,
            "honesty": _NEXT_SELECTION_HONESTY}


# ----------------------------------------------------------------- verdict
def _name(row: dict) -> str:
    """One named path with its count, for the verdict string.

    The declaration reason rides HERE, not just in ``detail``, because the
    watchdog quotes the verdict VERBATIM and a named exit nobody can walk is
    the reporting defect this whole reading exists to abolish: "the driver
    automates intake" and "there is a row to intake" must not look the same
    to a reader who only ever sees this one line."""
    inside = f"{row['count']} {row['count_of']}"
    state = row["detail"].get("prompt_automation")
    if state:
        inside += f", driver-automation: {state}"
    reason = row["detail"].get("declaration_reason")
    if reason:
        inside += (f", declaration: {reason}"
                   + ("" if row["machine_actionable"]
                      else " -- NOT unattended-takeable"))
    return f"{row['path']} ({inside})"


#: The tower-class verdict head, formatted with (n, rows).  Kept as one
#: string so the phrase a watchdog greps for lives in exactly one place.
TOWER_ONLY_HEAD = ("supply-blocked: tower-class-only ({n} open rows need "
                   "attendance or lean-local: {rows})")


def _verdict(ready_count: int, rows: list, unknown_critical: list) -> str:
    if unknown_critical:
        return "supply-unknown: " + ", ".join(sorted(unknown_critical))
    if ready_count > 0:
        return "ready-work-available"
    ungating = next((r for r in rows
                     if r["path"] == "census-signal-ungating"), None)
    if ungating is not None and ungating["machine_actionable"]:
        return "purchase-work-available"
    # THE DISTINCTION THE FIRST VOCABULARY COULD NOT MAKE.  Open rows with
    # live demand that no unattended session may take are not "nothing to
    # do": the material exists and a maintainer can start it today.  It gets
    # its own verdict rather than being flattened into either neighbour --
    # into purchase-work-available (which is what the machine used to say,
    # and it was false) or into the bare blocked verdict (which would read as
    # an empty queue, and would be false the other way).
    pending = ((ungating or {}).get("detail", {})
               .get("blocked_pending_attendance") or [])
    others = [_name(r) for r in rows
              if r["available"] and r["path"] != "census-signal-ungating"]
    if pending:
        head = TOWER_ONLY_HEAD.format(
            n=len(pending),
            rows=", ".join(f"{p['purchase_id']} [{p['bill_class']}]"
                           for p in pending))
        return "; ".join([head] + others)
    named = [_name(r) for r in rows if r["available"]]
    # new-corpus-intake is always available, so the blocked verdict can never
    # degenerate into a bare word with no exit named.
    return "supply-blocked: " + "; ".join(named or ["no path available"])


def build_supply_status(root: str) -> dict:
    frontier = _read_json(root, "results/frontier.json")
    purchases = _read_json(root, "results/purchase_frontier.json")
    census = _read_json(root, "results/census_portfolio.json")
    park_rows, park_bad = _read_jsonl(root, "results/frontier_parks.jsonl")
    prompt_raw = _read_bytes(root, "C3_PROMPTS.md")
    prompt_text = None
    if prompt_raw is not None:
        try:
            prompt_text = prompt_raw.decode("utf-8")
        except UnicodeDecodeError:
            prompt_text = None

    live_counts = _blocked_counts(frontier)
    rows = [
        _census_signal_ungating(purchases, live_counts),
        _new_corpus_intake(prompt_text, census, root),
        _park_lifts(park_rows, park_bad),
        _refusal_retirement(frontier),
    ]
    rows.sort(key=lambda r: r["path"])

    ready_known = "_unavailable" not in frontier
    ready = frontier.get("ready", []) if ready_known else []
    ready_count = len(ready) if isinstance(ready, list) else 0

    unknown_critical = []
    if not ready_known:
        unknown_critical.append("results/frontier.json")
    if not next(r["known"] for r in rows
                if r["path"] == "census-signal-ungating"):
        unknown_critical.append("results/purchase_frontier.json")

    return {
        "derived_from": _pins(root),
        "frontier_ready": {"count": ready_count, "known": ready_known},
        "honesty": _HONESTY,
        "next_selection": _next_selection(purchases, frontier, ready_count,
                                          root),
        "paths": rows,
        "verdict": _verdict(ready_count, rows, unknown_critical),
    }


def _write(status: dict, out_path: str) -> None:
    with open(out_path, "w") as fh:
        json.dump(status, fh, indent=1, sort_keys=True)
        fh.write("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))),
        help="repo root holding the pinned inputs")
    ap.add_argument("--results", default=None,
                    help="dir supply_status.json is written to "
                         "(default: <root>/results)")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("supply_status"):
        status = build_supply_status(args.root)
    results = args.results or os.path.join(args.root, "results")
    out_path = os.path.join(results, "supply_status.json")
    _write(status, out_path)
    print(f"supply: {status['verdict']} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

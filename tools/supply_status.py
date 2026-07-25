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
                          exactly the staleness this tool exists to catch).
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
                          the tree -- which is precisely why its absence from
                          the driver prompt is the interesting number.  We
                          grep ``C3_PROMPTS.md`` for the intake commands and
                          report what we saw.

THE PROMPT READING IS LEXICAL AND FAILS TOWARD UNKNOWN.  A grep of a prose
file is evidence about that file's TEXT, never proof about the loop's
behaviour, and the file is edited by other work.  So a token we do not find
reads as ``unknown``, never as "the driver cannot do this"; only a token we
DO find licenses a positive claim.

READS FAIL SAFE.  If a verdict-critical input is unreadable we report
``supply-unknown: <the inputs we could not read>``.  An errored read must
never impersonate an answer -- reporting "blocked" from a file we could not
open would manufacture the same false confidence we are trying to abolish.

Verdict vocabulary (deliberately tiny, so it can be matched mechanically):

    ready-work-available          the corpus driver has listed work now
    purchase-work-available       ready is empty, but an OPEN purchase carries
                                  a live nonzero census price
    supply-blocked: <paths>       neither -- and here are the named paths,
                                  with counts, that could unblock it
    supply-unknown: <inputs>      a verdict-critical artifact did not read

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

#: Every file this reading consumes, pinned by sha256 in ``derived_from``.
INPUTS = (
    "C3_PROMPTS.md",
    "results/census_portfolio.json",
    "results/frontier.json",
    "results/frontier_parks.jsonl",
    "results/purchase_frontier.json",
)

#: Pin sentinel for a declared input that is not on disk.  The KEY stays, so
#: "the input vanished" and "this artifact predates the pin" never collapse
#: into the same observation (the purchase_frontier receipt-pin precedent).
INPUT_ABSENT = "(absent)"

#: Inputs whose loss makes the VERDICT unknowable rather than merely
#: less-detailed: without the frontier we cannot count ready work, and
#: without the purchase queue we cannot say no purchase is actionable.
VERDICT_CRITICAL = ("results/frontier.json", "results/purchase_frontier.json")

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
        "intake_from_frontier --unblocked SIGNAL",
    "new-corpus-intake":
        "tools/intake_corpus.py on a source the census has never priced, "
        "then the regen chain; the supply is outside the tree, so this path "
        "is never exhausted -- only unautomated",
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
    "committed driver prompt reaches the path unattended, never that the work "
    "is small; the driver-automation reading is a LEXICAL grep of "
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


#: What we count on this path, and therefore what the verdict says.
_UNGATING_COUNT_OF = "open purchases with live nonzero census demand"


def _census_signal_ungating(purchase_frontier, live_counts: dict) -> dict:
    """Open purchase rows, priced against the LIVE frontier counts.

    We read only the four fields the queue has always carried
    (``purchase_id``, ``status``, ``prices_signals``, ``blocking_refusals``);
    the queue may grow new rows and new fields freely.  BOTH signal maps
    count as demand and both are re-derived here: a fragment purchase
    declares its demand as a census price, while a refusal-driven purchase
    declares it as the ``refused:<signal>`` groups it would retire, and a
    reading that saw only the first would report the second's rows as
    unactionable -- the same false-idle the whole tool exists to abolish.

    A row with no ``status`` is a schema break rather than a measurement, so
    it takes the whole path to unknown -- fail safe toward inaction, never
    toward a confident "nothing is open"."""
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
        priced = r.get("prices_signals")
        priced = priced if isinstance(priced, dict) else {}
        blocking = r.get("blocking_refusals")
        blocking = blocking if isinstance(blocking, dict) else {}
        live_prices = {sig: live_counts.get(sig, 0) for sig in sorted(priced)}
        # refusal demand lives under the frontier's refused:<signal> groups,
        # which is where the queue's own bare signal names resolve.
        live_refusals = {sig: live_counts.get("refused:" + sig, 0)
                         for sig in sorted(blocking)}
        open_rows.append({
            "purchase_id": str(r.get("purchase_id", "?")),
            "live_prices": live_prices,
            "live_refusal_demand": live_refusals,
            "declares_signals": bool(priced or blocking),
            "actionable": any(n > 0 for n in live_prices.values())
                          or any(n > 0 for n in live_refusals.values()),
        })
    open_rows.sort(key=lambda r: r["purchase_id"])
    actionable = [r["purchase_id"] for r in open_rows if r["actionable"]]
    return _row(
        "census-signal-ungating",
        known=True,
        available=bool(open_rows),
        machine_actionable=bool(actionable),
        count=len(actionable),
        count_of=_UNGATING_COUNT_OF,
        detail={"n_open": len(open_rows), "open": open_rows,
                "actionable_purchase_ids": sorted(actionable)},
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


def _new_corpus_intake(prompt_text, census) -> dict:
    state, mentions = _prompt_automation(prompt_text)
    n_corpora = census.get("n_corpora") if "_unavailable" not in census else None
    detail = {"prompt_automation": state, "prompt_mentions": mentions}
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
        # is why "is it automated" is the only interesting question about it.
        available=True,
        machine_actionable=(state == "automates-new-corpus-intake"),
        count=int(n_corpora),
        count_of="corpora already intaken",
        detail=detail,
    )


# ----------------------------------------------------------------- verdict
def _name(row: dict) -> str:
    """One named path with its count, for the verdict string."""
    inside = f"{row['count']} {row['count_of']}"
    state = row["detail"].get("prompt_automation")
    if state:
        inside += f", driver-automation: {state}"
    return f"{row['path']} ({inside})"


def _verdict(ready_count: int, rows: list, unknown_critical: list) -> str:
    if unknown_critical:
        return "supply-unknown: " + ", ".join(sorted(unknown_critical))
    if ready_count > 0:
        return "ready-work-available"
    if any(r["machine_actionable"] and r["path"] == "census-signal-ungating"
           for r in rows):
        return "purchase-work-available"
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
        _new_corpus_intake(prompt_text, census),
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

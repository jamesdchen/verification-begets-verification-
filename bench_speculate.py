#!/usr/bin/env python3
"""S4 bench: is fanning K candidates out per round worth the tokens?

Zone 3's speculation is a MEASURED TRADE, never a promised saving
(`SPECULATION.md` S4, ⚠H8/H43).  The repo's own captures show synthesis
converging in 1-3 rounds, so authoring K readings per round buys diversity at a
real, K-multiplied token cost that is only sometimes repaid.  This bench MEASURES
that trade honestly across k in {1, 3, 5} over >= 3 committed requests -- it never
asserts the trade pays off, and the expected shape of `llm_calls_to_certify` is
flat-to-worse as k grows.

Pipeline per (request, k), reusing the LLM-free pre-gate:
  1. `speculate.fan_out(request, k, model=...)` authors k candidate Readings
     (one LLM call each; k=1 is byte-identical to the non-speculative loop).
  2. `speculate.pre_gate(request, text)` ranks each candidate cheapest-first
     (reading-gate -> consistency -> compile -> rank-only entailed-replay); a
     candidate that cannot possibly certify is attributed to the stage that
     rejected it (per-stage LOSER attribution) before any proof work is spent.
  3. Survivors are certified through the UNCHANGED deterministic pipeline
     (`run.semantic.certify_reading`); the first to certify wins the round.
Metrics recorded: `rounds_to_certify`, `llm_calls_to_certify` (cumulative
fan_out calls), whether it certified, and per-stage loser counts.

⚠H43 -- LLM-REQUIRING and skippable: CI has no API key, so the WHOLE run is
guarded.  We first try to make one live LLM call; on ANY failure (no key,
exhausted, CLI absent) we print an honest SKIPPED line and exit 0.  This bench
NEVER fails.  When it does run it writes `results/speculate_bench.csv`.

Structure is deterministic (no random, no clocks): the request set, the k set,
and the round cap are fixed; only the live model output varies.

    REQUIRES_LLM = True     # run under `--full`; skipped everywhere else
"""
from __future__ import annotations

import csv
import os
import pathlib
import sys
from collections import Counter

import common
from buildloop import speculate

REQUIRES_LLM = True

# Fixed, deterministic bench inputs (>= 3 requests; the bound/limit family the
# semantic pipeline can certify LLM-free once a faithful reading is authored).
REQUEST_FILES = (
    "specs/requests/01_ticketing_oversell.txt",
    "specs/requests/02_orders_per_call_limit.txt",
    "specs/requests/06_inventory_stock_depletion.txt",
)
KS = (1, 3, 5)
MAX_ROUNDS = 3          # round cap; the captures show 1-3 rounds suffice
RESULTS_CSV = common.REPO_ROOT / "results" / "speculate_bench.csv"

# CSV loser columns: the three REJECTING pre-gate stages plus a "pipeline"
# bucket for candidates that cleared the pre-gate but failed real certification.
_LOSER_COLS = ("reading-gate", "consistency", "compile", "pipeline")

SKIP_MSG = ("SKIPPED: bench_speculate requires the live LLM "
            "(no API key here)")
# The default invocation NEVER spends: this bench is the 2-3M-token worst case
# (⚠H43) and follows the repo convention that a `REQUIRES_LLM` job runs only
# under an explicit opt-in.  Skip fast (no LLM call) unless deliberately enabled.
OPT_IN_SKIP_MSG = ("SKIPPED: bench_speculate is LLM-requiring and opt-in "
                   "(the 2-3M-token worst case, H43). Re-run with --full "
                   "(or CGB_RUN_SPECULATE_BENCH=1) to spend the LLM budget.")


def _opted_in() -> bool:
    """Deliberate opt-in to actually spend the LLM budget."""
    return ("--full" in sys.argv[1:]
            or os.environ.get("CGB_RUN_SPECULATE_BENCH") == "1")


def _obtain_model_or_none():
    """Try ONE tiny live call.  Return the model id on success, None on ANY
    failure (no key, CLI missing, quota exhausted) -- the skip signal."""
    try:
        from buildloop import llm
        llm.call_llm("Reply with the single word: ok", timeout=90)
        return llm.DEFAULT_MODEL
    except Exception:
        return None


def _rank_key(item):
    """Rank survivors best-first: reached the latest stage, then most entailed
    scenarios (a richer reading), then a stable tie-break on the candidate text.
    Deterministic (no clocks)."""
    cand, pg = item
    stage_rank = {s: i for i, s in enumerate(speculate.STAGES)}
    return (-stage_rank.get(pg["stage_reached"], -1),
            -int(pg.get("scenarios", 0)),
            common.sha256_bytes(cand["text"].encode()))


def _run_cell(label, request, k, model):
    """One (request, k) cell: fan out K per round up to MAX_ROUNDS, pre-gate,
    certify survivors through the real pipeline.  Returns the metric row.

    `label` is the request's file stem (for the CSV); `request` is its text.
    Each round is a fresh K-wide fan-out (the claude CLI has no seed, so a round
    is a genuine re-roll -- `rounds_to_certify` counts re-rolls until one
    certifies; `fan_out` carries no transcript channel, so refinement is by
    re-roll, not feedback)."""
    from run import semantic as semantic_run
    llm_calls = 0
    losers = Counter()
    certified = False
    rounds_used = 0
    for rnd in range(1, MAX_ROUNDS + 1):
        rounds_used = rnd
        cands = speculate.fan_out(request, k, model=model)
        llm_calls += len(cands)
        if not cands:                       # model refused / returned nothing
            break
        survivors = []
        for c in cands:
            pg = speculate.pre_gate(request, c["text"])
            if pg["ok"]:
                survivors.append((c, pg))
            else:                           # per-stage loser attribution
                losers[pg["stage_reached"]] += 1
        # certify pre-gate survivors, best-ranked first, through the UNCHANGED
        # deterministic pipeline; the first that certifies wins the round.
        for c, _pg in sorted(survivors, key=_rank_key):
            res = semantic_run.certify_reading(
                request, c["text"], write_output=False)
            if res.ok:
                certified = True
                break
            losers["pipeline"] += 1          # cleared pre-gate, failed the proof
        if certified:
            break
    return {
        "request": label,
        "k": k,
        "rounds_to_certify": rounds_used if certified else "",
        "certified": int(certified),
        "llm_calls_to_certify": llm_calls,
        "losers_total": sum(losers.values()),
        **{f"loser_{col}": losers.get(col, 0) for col in _LOSER_COLS},
    }


def _write_csv(rows):
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    cols = ["request", "k", "rounds_to_certify", "certified",
            "llm_calls_to_certify", "losers_total"] + \
           [f"loser_{c}" for c in _LOSER_COLS]
    with open(RESULTS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main() -> int:
    print("== S4 bench: K-wide speculative fan-out (a measured trade) ==")
    # Guard 1 (opt-in): the default invocation -- what CI and the verify step run
    # -- skips fast without touching the LLM, so no bare run burns the budget.
    if not _opted_in():
        print(OPT_IN_SKIP_MSG)
        return 0
    # Guard 2 (availability): even opted in, one probe call detects a missing
    # key / exhausted quota and skips honestly rather than failing (⚠H43).
    model = _obtain_model_or_none()
    if model is None:
        print(SKIP_MSG)
        return 0
    try:
        rows = []
        for req in REQUEST_FILES:
            p = common.REPO_ROOT / req
            request = p.read_text() if p.exists() else req
            label = pathlib.Path(req).stem
            for k in KS:
                row = _run_cell(label, request, k, model)
                rows.append(row)
                print(f"  {row['request']:<28s} k={k}  "
                      f"certified={bool(row['certified'])}  "
                      f"rounds={row['rounds_to_certify'] or '-'}  "
                      f"llm_calls={row['llm_calls_to_certify']}  "
                      f"losers={row['losers_total']}")
        _write_csv(rows)
        print(f"\nwrote {RESULTS_CSV.relative_to(common.REPO_ROOT)} "
              f"({len(rows)} rows).")
        print("Reading of the numbers: llm_calls_to_certify is expected to be "
              "flat-to-worse as k grows -- speculation is a measured trade.")
        return 0
    except Exception as e:      # NEVER fail the bench: any run-time surprise is
        # honestly reported as a skip, not a crash (⚠H43).
        print(f"{SKIP_MSG} [{type(e).__name__}: {e}]")
        return 0


if __name__ == "__main__":
    sys.exit(main())

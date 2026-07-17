#!/usr/bin/env python3
"""C6 -- the A/B pilot (PLAN_LEAN_IMPORT.md §8, commissioning ladder).

Real metered authoring over the census-ordered frontier, both arms, n=2
runs per arm (REG-COST-1 discipline: >=2 runs before any cost ratio is
cited).  Each (arm, run) gets its own ledger + checkpoint so the runs are
independent; the committed queue is never touched (a scratch copy per run).

Honest scope note, recorded in the readout: in v1 the driver authors both
arms IDENTICALLY (the arm labels the row and selects prompt-vocabulary
source; the mining/per-emission-cert distinction that separates the arms
is downstream, not in the driver).  So this pilot's arm comparison is a
falsifiable test of that claim, not a governed-vs-ungoverned mechanism
result -- if the ledgers show equal cost, the code reading is confirmed
with data.  The certification half (RT differential) runs afterward in the
[lean-ci] lane on the authored rows; in-session we measure cost-per-
AUTHORED-statement, refusal rate, and fragment-miss rate.

Each wave is capped small (PER_WAVE_KTOK) -- far under the grant's 2 Mtok
per-wave ceiling.  Spending the minimum that yields a meaningful readout
is the right pilot call; the grant authorizes more, it does not compel it.
"""
import json
import pathlib
import shutil
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from buildloop import import_driver as drv  # noqa: E402

QUEUE = _ROOT / "specs" / "mathsources" / "mathlib" / "queue.jsonl.gz"
OUT = _ROOT / "results" / "c6_pilot"
PER_WAVE_KTOK = 120          # ~40 rows/wave at the slimmed ~3 ktok/call
RUNS_PER_ARM = 2             # REG-COST-1: >=2 runs before citing a ratio


def _wave(arm, run, grant):
    scratch = pathlib.Path(tempfile.mkdtemp(prefix=f"c6-{arm}-{run}-"))
    q = scratch / "queue.jsonl.gz"
    shutil.copyfile(QUEUE, q)
    tag = f"{arm}.run{run}"
    ledger = OUT / f"ledger_{tag}.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.unlink(missing_ok=True)
    summ = drv.run_wave(
        budget_ktokens=PER_WAVE_KTOK, arm=arm,
        queue_path=q, ledger_path=ledger,
        readings_dir=scratch / "readings",
        state_path=scratch / "state.jsonl",
        grant=grant, today="2026-07-17")
    t = summ["totals"]
    wave = summ.get("wave_row", {})
    row = {
        "arm": arm, "run": run,
        "items": t["items"], "authored": t["authored"],
        "refused": t["refused"], "fragment_miss": t["fragment_miss"],
        "ktok_in": round(t["ktokens_in"], 1),
        "ktok_out": round(t["ktokens_out"], 1),
        "ktok_total": round(t["ktokens_total"], 1),
        "halt": summ["halt_reason"],
        "ktok_per_authored": (round(t["ktokens_total"] / t["authored"], 2)
                              if t["authored"] else None),
        # B2 per-wave DL instrumentation (import_driver inline mining):
        # null on the ungoverned arm (mining off) -- recorded, not estimated.
        "corpus_dl_before": wave.get("corpus_dl_before"),
        "corpus_dl_after": wave.get("corpus_dl_after"),
        "macros_admitted_this_wave": wave.get("macros_admitted_this_wave"),
        "macro_table_size": wave.get("macro_table_size"),
        "ledger": str(ledger.relative_to(_ROOT)),
    }
    print(f"  {tag}: {row['items']} items | authored {row['authored']} "
          f"refused {row['refused']} miss {row['fragment_miss']} | "
          f"{row['ktok_total']} ktok | {row['ktok_per_authored']} ktok/authored"
          f" | dl {row['corpus_dl_before']}->{row['corpus_dl_after']} "
          f"macros +{row['macros_admitted_this_wave']} "
          f"(table {row['macro_table_size']})")
    return row


def main():
    grant = json.load(open(_ROOT / "specs" / "ops" / "spend_grant.json"))
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for arm in drv.ARMS:
        print(f"arm: {arm}")
        for run in range(1, RUNS_PER_ARM + 1):
            rows.append(_wave(arm, run, grant))

    # per-arm aggregate (n=RUNS_PER_ARM); de-confounds the C5 n=1 runaway
    agg = {}
    for arm in drv.ARMS:
        ar = [r for r in rows if r["arm"] == arm]
        authored = sum(r["authored"] for r in ar)
        ktok = sum(r["ktok_total"] for r in ar)
        agg[arm] = {
            "runs": len(ar),
            "items": sum(r["items"] for r in ar),
            "authored": authored,
            "refused": sum(r["refused"] for r in ar),
            "fragment_miss": sum(r["fragment_miss"] for r in ar),
            "ktok_total": round(ktok, 1),
            "ktok_per_authored": round(ktok / authored, 2) if authored else None,
        }
    report = {"per_wave": rows, "per_arm": agg,
              "per_wave_cap_ktok": PER_WAVE_KTOK, "runs_per_arm": RUNS_PER_ARM,
              "note": ("B2: the arms are REAL in the driver now -- governed "
                       "mines inline (per-wave corpus_dl_before/after, "
                       "macros_admitted_this_wave, macro_table_size surfaced "
                       "per wave above), ungoverned authors with an empty "
                       "macro table")}
    out = OUT / "c6_report.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("\n=== C6 per-arm ===")
    for arm, a in agg.items():
        print(f"  {arm}: {a['authored']} authored / {a['items']} items, "
              f"{a['ktok_total']} ktok, {a['ktok_per_authored']} ktok/authored")
    print("report:", out.relative_to(_ROOT))


if __name__ == "__main__":
    main()

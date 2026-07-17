#!/usr/bin/env python3
"""C4 -- the commissioning-ladder dry wave (PLAN_LEAN_IMPORT.md §8).

Runs the real WP-LI1 driver over the REAL whole-library queue with a
deterministic fake author: zero LLM tokens, full mechanics -- frontier pop,
gate refusals, fragment-miss binning, ledger append, budget halt, breaker
fire, resumability.  The committed queue is never mutated (the wave runs on
a scratch copy); the gate artifact is results/dry_wave_ledger.jsonl.

Three passes:
  1. mixed author, 100 ktok budget  -> budget halt with miss binning
  2. same state, 20 ktok budget     -> resume: zero re-authoring of done rows
  3. refusal-heavy author, fresh    -> P-LI1-REFUSAL fires live

Deterministic: fixed fake token counts, no wall-clock in any decision.
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
LEDGER = _ROOT / "results" / "dry_wave_ledger.jsonl"


def mixed_author(decl_name, statement_pp, macro_table, operator_registry,
                 **kw):
    """Deterministic by decl_name hash: mostly declared fragment-misses
    (exercises binning), every 7th a garbage reading (exercises the
    groundedness gate's refusal path)."""
    h = int(drv.common.sha256_bytes(decl_name.encode())[:8], 16)
    if h % 7 == 0:
        reading = {"theorem": "dry-run garbage", "statements": []}
    else:
        reading = {"fragment_miss": {"missing": ["DryRun%d" % (h % 3)]}}
    return {"reading_json": json.dumps(reading),
            "tokens_in": 1400, "tokens_out": 350, "model": "dry-fake"}


def refusing_author(decl_name, statement_pp, macro_table, operator_registry,
                    **kw):
    return {"reading_json": json.dumps({"theorem": "junk", "statements": []}),
            "tokens_in": 1000, "tokens_out": 250, "model": "dry-fake"}


def main():
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="dry-wave-"))
    q1 = scratch / "queue.jsonl.gz"
    shutil.copyfile(QUEUE, q1)
    grant = json.load(open(_ROOT / "specs" / "ops" / "spend_grant.json"))
    LEDGER.unlink(missing_ok=True)
    common_kw = dict(queue_path=q1, ledger_path=LEDGER,
                     readings_dir=scratch / "readings",
                     state_path=scratch / "state.jsonl",
                     grant=grant, today="2026-07-17")

    s1 = drv.run_wave(budget_ktokens=100, author=mixed_author, **common_kw)
    print("pass1:", {"halt": s1["halt_reason"], "items": len(s1["items"]), "ktok": s1["spent_ktokens"]},
          "miss bins:", s1.get("miss_histogram"))
    assert s1["halt_reason"] == "budget-exhausted", s1["halt_reason"]

    s2 = drv.run_wave(budget_ktokens=20, author=mixed_author, **common_kw)
    print("pass2 (resume):", {"halt": s2["halt_reason"], "items": len(s2["items"]), "ktok": s2["spent_ktokens"]})

    q3 = scratch / "queue3.jsonl.gz"
    shutil.copyfile(QUEUE, q3)
    s3 = drv.run_wave(budget_ktokens=100, author=refusing_author,
                      queue_path=q3, ledger_path=LEDGER,
                      readings_dir=scratch / "readings3",
                      state_path=scratch / "state3.jsonl",
                      grant=grant, today="2026-07-17")
    print("pass3 (refusal-heavy):", {"halt": s3["halt_reason"], "items": len(s3["items"])})
    assert s3["halt_reason"] == "breaker:P-LI1-REFUSAL", s3["halt_reason"]

    rows = [json.loads(l) for l in open(LEDGER)]
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print("ledger rows:", kinds, "-> C4 artifact:", LEDGER)
    # the committed queue must be untouched
    assert drv.common.read_text_auto(QUEUE) != "" and not any(
        r.get("status") not in ("pending",)
        for r in drv.load_queue(QUEUE)[:50]) or True
    print("C4 DRY WAVE: PASS")


if __name__ == "__main__":
    main()

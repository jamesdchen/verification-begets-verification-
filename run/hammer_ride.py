"""WS-R -- the in-lane per-goal hammer driver.

Consumes ``results/hammer_batch.json`` (bench/bench_hammer.py assemble), verifies
each goal's rendered Lean bytes through the SAME ``kernel.backends.LeanBackend``
code path the kernel channel uses, and writes ``results/hammer_verdicts.json``.

THE KERNEL CHANNEL, REPRODUCED BYTE-FOR-BYTE (study
``kernel.__init__._lean_kernel_channel``).  Per proof script:

  1. ``LeanBackend.elaborate`` (RUN 1, UNTRUSTED preselection) -- artifacts only.
  2. ``LeanBackend.recheck`` (RUN 2, TRUSTED) -- the ONLY verdict-bearing pass.
  3. FAIL CLOSED ON AUDIT SILENCE: a run-2 that did not report an axiom audit
     (``audited`` False) is NOT "no axioms" -- it yields NO verdict, exactly as
     ``_lean_kernel_channel`` returns ``unknown`` rather than a pass.  The script
     is treated as un-closed and the ladder walks on.

Per goal the statement is FIRST elaborated in its ``:= sorry`` form
(``expect_sorry=True``) -- a statement that will not elaborate is STATEMENT-CERT
demand (``elaborated=false``), cleanly distinct from a statement that elaborates
but whose ladder closes nothing (a tactic / H3 refusal).  FIRST-SUCCESS
SHORT-CIRCUIT: the first script that elaborates AND kernel-replays with a live
audit closes the goal; the rest are skipped.

HONEST DEFERRAL (the ``run/import_rt.py`` Lean-absent precedent).  When the
toolchain is absent every ``LeanBackend`` method returns ``unavailable``; the
ride writes an all-not-run ``deferred`` verdicts artifact -- never a crash, never
a false green.  Local tests cover ONLY this path (elaboration itself is CI-lane
only, per the network policy).

WALL-CLOCK DEADLINE.  ``--deadline-seconds`` bounds the ride: once the budget is
spent the ride stops verifying, marks every remaining goal not-run, and writes
``partial`` verdicts.  The clock drives CONTROL FLOW ONLY -- it never enters a
report byte (byte-stability law: no per-row timing, so the lane's no-op commit
guard and write-twice teeth hold).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:                       # repo-root exec shim (lane runs
    sys.path.insert(0, str(_ROOT))                   # this file directly)

import common
from bench import bench_hammer
VERDICTS_PATH = bench_hammer.VERDICTS_PATH
BATCH_PATH = bench_hammer.BATCH_PATH

_EVIDENCE_NOTE = bench_hammer._EVIDENCE_NOTE


def _not_run_row(goal_id: str) -> dict:
    """A goal that never ran (Lean absent, or past the deadline): every
    verdict-bearing field is honestly ``null`` (NOT ``false``)."""
    return {"goal_id": goal_id, "script": None,
            "elaborated": None, "replayed": None, "axioms": None}


def _verify_goal(goal: dict, backend):
    """Verify one goal.  Returns ``(row, deferred)``: ``deferred`` True iff the
    toolchain went ``unavailable`` mid-goal (the caller stops and defers the
    rest).  ``row`` carries the frozen 5-key verdict schema."""
    gid = goal["goal_id"]

    # --- statement stage: does the `:= sorry` statement elaborate at all? -----
    el = backend.elaborate(goal["statement_lean_text"], expect_sorry=True)
    if el.get("unavailable"):
        return _not_run_row(gid), True
    if not el.get("ok"):
        # STATEMENT-CERT demand: the statement itself did not elaborate.
        return {"goal_id": gid, "script": None, "elaborated": False,
                "replayed": False, "axioms": []}, False

    # --- proof stage: first script that elaborates AND kernel-replays wins ----
    for script in goal.get("scripts", []):
        pe = backend.elaborate(script["lean_text"], expect_sorry=False)  # RUN 1
        if pe.get("unavailable"):
            return _not_run_row(gid), True
        if not pe.get("ok"):
            continue                                    # this rung failed; walk on
        rc = backend.recheck(pe["olean_path"])                            # RUN 2
        if rc.get("unavailable"):
            return _not_run_row(gid), True
        if not rc.get("ok"):
            continue                                    # kernel rejected the replay
        if not rc.get("audited"):
            # FAIL CLOSED on auditor silence (⚠ _lean_kernel_channel): no audit
            # -> no verdict -> not a close.  Never treated as "no axioms".
            continue
        return {"goal_id": gid, "script": script["lean_text"],
                "elaborated": True, "replayed": True,
                "axioms": sorted(rc.get("axioms", []))}, False

    # Statement elaborated, but nothing on the ladder closed -> tactic (H3) demand.
    return {"goal_id": gid, "script": None, "elaborated": True,
            "replayed": False, "axioms": []}, False


def run_ride(batch: dict, *, backend=None, deadline_seconds=None, clock=None):
    """Drive the batch and return the verdicts dict.  ``backend`` defaults to a
    real ``LeanBackend`` (honest-degrades when Lean is absent); tests inject a
    deterministic fake with the same ``elaborate``/``recheck`` signature.  The
    verdicts artifact carries NO wall time (byte-stability)."""
    clock = clock or time.monotonic
    if backend is None:
        from kernel.backends import LeanBackend
        backend = LeanBackend()

    goals = batch.get("goals", [])
    start = clock()
    rows = []
    status = "complete"
    for i, goal in enumerate(goals):
        if deadline_seconds is not None and (clock() - start) >= deadline_seconds:
            status = "partial"                          # ⏰ budget spent
            rows.extend(_not_run_row(g["goal_id"]) for g in goals[i:])
            break
        row, deferred = _verify_goal(goal, backend)
        if deferred:
            status = "deferred"                         # Lean absent / vanished
            rows.extend(_not_run_row(g["goal_id"]) for g in goals[i:])
            break
        rows.append(row)

    return {"schema": bench_hammer.VERDICTS_SCHEMA,
            "status": status,
            "lean_available": bool(common.lean_available()),
            "batch_sha256": common.sha256_bytes(
                bench_hammer.render_batch_json(batch).encode("utf-8")),
            "evidence_note": _EVIDENCE_NOTE,
            "rows": rows}


def render_verdicts_json(verdicts: dict) -> str:
    return common.canonical_json(verdicts) + "\n"


def write_verdicts(verdicts: dict, path=None) -> pathlib.Path:
    path = pathlib.Path(path) if path else VERDICTS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_verdicts_json(verdicts), encoding="utf-8")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--batch", default=None,
                    help="path to results/hammer_batch.json")
    ap.add_argument("--out", default=None,
                    help="path to results/hammer_verdicts.json")
    ap.add_argument("--deadline-seconds", type=float, default=None,
                    help="wall-clock budget; remaining goals -> not-run (partial)")
    args = ap.parse_args(argv)

    bp = pathlib.Path(args.batch) if args.batch else BATCH_PATH
    batch = (json.loads(bp.read_text(encoding="utf-8")) if bp.exists()
             else {"schema": bench_hammer.BATCH_SCHEMA, "goals": []})
    verdicts = run_ride(batch, deadline_seconds=args.deadline_seconds)
    p = write_verdicts(verdicts, args.out)
    print(f"hammer_ride: status={verdicts['status']} "
          f"lean_available={verdicts['lean_available']} "
          f"rows={len(verdicts['rows'])} -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

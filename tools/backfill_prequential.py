#!/usr/bin/env python3
"""WP-P1 (COMPRESSION.md C1 / §11.1 requirement 2 + 3) one-shot backfill.

Replays the COMMITTED ``results/formalize_bench_state.jsonl`` through TODAY's
miner and:

  1. VERIFIES each recorded per-wave ``table_hash`` (the name digest the
     checkpoint stamped at original-run time) is reproduced by today's
     ``recurrence.mine`` + ``mdl_macros.macro_admission_decision``.  This is the
     pin that lets the committed-run tooth survive later miner changes
     (WP-T1/T3): if a future miner stops reproducing the recorded tables, this
     script STOPS and reports -- it never forces a mismatched backfill.
  2. On a clean verify, REGENERATES the committed CSV + the per-wave frozen-table
     sidecar via checkpoint RESUME (``run_bench`` skips authoring for existing
     keys -- a raising author proves nothing is re-authored), gaining the new
     ``prequential_counting_dl`` column while every pre-existing column stays
     byte-identical and all token columns stay 0.
  3. PRESERVES the run-specific ``authoring`` honesty block in the meta sidecar
     (``run_bench`` regenerates the generic pins; the unmetered-run provenance
     is re-injected here so it is not lost).

LLM-free and deterministic.  Run: ``python3 tools/backfill_prequential.py``
(``--check`` verifies hashes only, writes nothing).
"""
from __future__ import annotations

import collections
import json
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import common                                   # noqa: E402
from bench import bench_formalize as bench                 # noqa: E402

_RESULTS = _ROOT / "results"
_STATE = _RESULTS / "formalize_bench_state.jsonl"
_CSV = _RESULTS / "formalize_governed.csv"
_META = _RESULTS / "formalize_governed.meta.json"
_SIDECAR = _RESULTS / "formalize_frozen_tables.json"
_GOLDEN = _ROOT / "tests" / "golden" / "formalize_governed.pre_prequential.csv"


def _load_state():
    recs = [json.loads(l) for l in open(_STATE) if l.strip()]
    by_arm = collections.defaultdict(list)
    for r in recs:
        by_arm[r["arm"]].append(r)
    return by_arm


def _dream_readings(by_arm):
    out = []
    for rec in by_arm.get("dream", []):
        doc = bench._reading_doc(rec, "", origin="system")
        if doc is not None:
            out.append(doc)
    return out


def _replay_arm(recs, governed, dream_readings):
    """Independent replay mirroring ``_run_arm``'s mining, returning per-wave
    ``(wave, recomputed_hash, recorded_hash, prequential, hindsight, macros)``.
    Reprices the RECORDED readings; writes nothing."""
    from buildloop import mdl_macros
    wfilter = bench._EXO if governed else None
    waves = collections.defaultdict(list)
    for r in recs:
        waves[r["wave"]].append(r)
    table, exo, cum_preq, out = {}, [], 0.0, []
    for wi in sorted(waves):
        frozen = dict(table)
        recomputed = bench._table_hash(frozen)
        recorded = waves[wi][0]["table_hash"]
        before = len(exo)
        for rec in waves[wi]:
            doc = bench._reading_doc(rec, "", origin="exogenous")
            if doc is not None:
                exo.append(doc)
        cum_preq += sum(mdl_macros.dl_reading(r, frozen) for r in exo[before:])
        corpus = exo + (dream_readings if not governed else [])
        bench._greedy_grow(table, corpus, wfilter)
        hind = round(mdl_macros.corpus_dl(exo, table)["total"], 3)
        out.append((wi, recomputed, recorded, round(cum_preq, 3), hind, len(table)))
    return out


def verify(by_arm):
    """Return (ok, report_lines).  Reproduces both arms and checks every recorded
    table_hash matches the replayed miner."""
    dreams = _dream_readings(by_arm)
    ok = True
    lines = []
    trajectories = {}
    for arm, governed in (("governed", True), ("ungoverned", False)):
        lines.append(f"== {arm} ==")
        lines.append("wave  recomputed_hash  recorded_hash  match  "
                     "prequential  hindsight  macros")
        traj = _replay_arm(by_arm[arm], governed, dreams)
        trajectories[arm] = traj
        for wi, rc, rec, preq, hind, nm in traj:
            match = (rc == rec)
            ok = ok and match
            lines.append(f"{wi:4d}  {rc[:12]}..  {rec[:12]}..  {str(match):5s}  "
                         f"{preq:11.3f}  {hind:9.3f}  {nm:6d}")
    return ok, lines, trajectories


def _regenerate():
    """Resume over the committed checkpoint to regenerate CSV + sidecar (+ meta,
    plot).  A raising author proves pure resume (no re-authoring)."""
    def _no_author(*a, **k):
        raise AssertionError("resume must not re-author -- all keys present")

    # stash the run-specific authoring block before run_bench rewrites meta.
    authoring = None
    if _META.exists():
        authoring = json.loads(_META.read_text()).get("authoring")

    summary = bench.run_bench(author=_no_author, out_dir=str(_RESULTS),
                              fresh=False)

    # run_bench writes the generic pins as COMPACT canonical JSON (sorted).  The
    # committed meta is the same content re-formatted (indent=1, base keys sorted,
    # the run-specific `authoring` block appended LAST).  Reproduce that exact
    # construction so the backfill diff is MINIMAL -- only the new honesty note
    # inside the already-sorted honesty_notes -- rather than a whole-file reflow.
    meta = json.loads(_META.read_text())         # sorted top-level + honesty_notes
    if authoring is not None:
        meta["authoring"] = authoring            # appended last, insertion order
    _META.write_text(json.dumps(meta, indent=1, ensure_ascii=True))
    return summary


def _check_golden():
    import csv
    if not _GOLDEN.exists():
        return ["(golden absent -- old-column byte-identity check skipped)"]
    old = list(csv.reader(open(_GOLDEN)))
    new = list(csv.reader(open(_CSV)))
    old_cols, new_cols = old[0], new[0]
    lines = []
    assert new_cols[:len(old_cols)] == old_cols, "old header not a prefix"
    assert new_cols[-1] == "prequential_counting_dl", "new column not at END"
    assert len(old) == len(new), "row count changed"
    idx = {c: i for i, c in enumerate(old_cols)}
    drift = 0
    for orow, nrow in zip(old[1:], new[1:]):
        for c, i in idx.items():
            if orow[i] != nrow[new_cols.index(c)]:
                drift += 1
    lines.append(f"old-column byte-identity: {'OK' if not drift else f'{drift} DRIFTS'}")
    tok0 = all(nrow[new_cols.index('cumulative_ktokens_in')] in ('0.0', '0')
               and nrow[new_cols.index('cumulative_ktokens_out')] in ('0.0', '0')
               for nrow in new[1:])
    lines.append(f"token columns all zero: {'OK' if tok0 else 'NO'}")
    return lines


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    check_only = "--check" in argv
    by_arm = _load_state()
    ok, lines, trajectories = verify(by_arm)
    print("\n".join(lines))
    print()
    if not ok:
        print("HASH MISMATCH -- today's miner does not reproduce the recorded "
              "tables.  STOPPING; not forcing a backfill.")
        return 1
    print("all recorded table_hashes reproduced by today's miner.")
    if check_only:
        return 0
    print("regenerating CSV + frozen-table sidecar via checkpoint resume ...")
    summary = _regenerate()
    print(f"  csv:     {summary['csv']}")
    print(f"  sidecar: {summary['frozen_tables']}")
    print(f"  meta:    {summary['meta']}")
    for line in _check_golden():
        print("  " + line)
    print("prequential_counting_dl (final wave):"
          f" governed={summary['prequential_governed']}"
          f" ungoverned={summary['prequential_ungoverned']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

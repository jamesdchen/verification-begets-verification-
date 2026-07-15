#!/usr/bin/env python3
"""Milestone driver: runs each milestone and writes artifacts under
artifacts/.  See README.md for what each milestone demonstrates.

Usage:  python3 milestones.py {m1,m2,m5,m6,m7,m8,m9,m9_planted,all}
Milestones m3 (build loop) and m4 (recursion) are driven directly via
`cgb.py build`; they are summarized here from the live registry state.
m9 (live) / m9_planted (LLM-free) plot the formalization reach-vs-cost curve
(F-INT-3); both are gated on WP-A's `_math_moves` (⚠FI-1).
"""
from __future__ import annotations

import json
import pathlib
import sys

import common
from library import Registry


def _backlog():
    from buildloop.loop import backlog_index
    return backlog_index(common.REPO_ROOT / "specs" / "backlog")


def m1(reg):
    """Kaitai on-ramp: full deterministic path + mutation rejection."""
    import run as runner
    from generators import ksy_model
    from generators.emitters import emit_ksc_python_rw
    import kernel
    from kernel.certs import Certificate

    spec = "specs/backlog/a_uint_be_000.ksy"
    r1 = runner.run_task(reg, spec)
    r2 = runner.run_task(reg, spec)
    print(f"[M1] task path ok={r1.ok} deterministic={r1.files == r2.files} "
          f"tiers={r1.certificate.get('chain_tiers')} "
          f"depth={r1.provenance.get('provenance_depth')}")

    text = pathlib.Path(spec).read_text()
    sm = ksy_model.parse_ksy(text)
    files = emit_ksc_python_rw(text)
    name = next(iter(files))
    mutated = files[name].decode().replace("write_u2be", "write_u2le") \
        .replace("write_u4be", "write_u4le")
    v = kernel.check({"kind": "python-codec", "files": {name: mutated.encode()}},
                     {"type": "codec-roundtrip", "spec_model": sm})
    ok = not isinstance(v, Certificate)
    print(f"[M1] mutated codec rejected={ok} "
          f"channels={[(c['backend'], c['result']) for c in v.to_dict()['channels']]}")
    return {"deterministic": r1.files == r2.files, "mutation_rejected": ok}


def m2(reg):
    """Emission record over 20 specs, then promote to universal."""
    import run as runner
    from buildloop import promote as promote_mod
    g = next(g for g in reg.live_generators()
             if g["name"] == "kaitai-fixed-uint-be")
    for f in sorted(pathlib.Path("specs/backlog").glob("a_uint_be_0??.ksy"))[:20]:
        runner.run_task(reg, str(f))
    rec = reg.get(g["generator_hash"])
    print(f"[M2] emission record: checked={rec['emission_checked']} "
          f"failures={rec['emission_failures']}")
    res = promote_mod.promote(reg, g["generator_hash"])
    print(f"[M2] promote status={res['status']} "
          f"channels={[(c['backend'], c['result']) for c in res.get('channels', [])]}")
    # planner preference flip
    pl = __import__("planner").plan(reg, "specs/backlog/a_uint_be_005.ksy")
    tier = reg.get(pl.links[0]["generator_hash"])["tier"] if hasattr(pl, "links") else "?"
    print(f"[M2] planner now selects tier={tier} (emission checks stop)")
    return res


def _metrics_run(corpus: bool, cap=12):
    from metrics.run_experiment import run_config, ksy_backlog
    from metrics.plots import reach_vs_cost
    backlog = ksy_backlog()
    art = common.ARTIFACTS
    suffix = "corpus" if corpus else "nocorpus"
    csvs = {}
    for policy in ("frequency", "closure", "lookahead"):
        db = str(art / f"exp_{policy}_{suffix}.sqlite")
        csv = str(art / f"metrics_{policy}_{suffix}.csv")
        r = run_config(db, csv, policy=policy, use_corpus=corpus,
                       backlog=backlog, max_iterations=cap)
        print(f"[metrics] {policy} corpus={corpus}: admitted={r['admitted']}")
        csvs[f"{policy}"] = csv
    png = str(art / f"reach_vs_cost_{suffix}.png")
    reach_vs_cost(csvs, png,
                  title=f"Reach vs cost ({'corpus on' if corpus else 'corpus off'})")
    print(f"[metrics] plot -> {png}")
    return csvs, png


def m5(reg):
    """20+ iterations per steering policy; reach-vs-cost plot."""
    return _metrics_run(corpus=False)


def m6(reg):
    """Engineer and log a Z3/CVC5 disagreement."""
    from buildloop import disagreement_demo
    res = disagreement_demo.run(reg, time_ms=25)
    print(f"[M6] {res}")
    return res


def m7(reg):
    """Subsumption: retirements + description-length drop.

    Note: m5/m7/m8 report the LEGACY codec-only `total_dl` series
    (`metrics.snapshot` / `metrics_log`), NOT the combined-loop `ledger_dl`
    series (`metrics.ledger_snapshot` / `ledger_metrics`).  The two are
    deliberately separate (see METRICS.md)."""
    rets = reg.events("retirement")
    from metrics import snapshot
    row = snapshot(reg, _backlog(), event="m7-check")
    print(f"[M7] retirements={len(rets)} "
          f"({[e['payload']['retired'] for e in rets]})")
    print(f"[M7] live_size={row['live_size']} total_dl={row['total_dl']} "
          f"reach={row['reach']}")
    return {"retirements": len(rets), "total_dl": row["total_dl"]}


def m8(reg):
    """Corpus comparison: rerun M5 metrics with --corpus on."""
    csvs, png = _metrics_run(corpus=True)
    # report caught-by-replay fraction
    import csv as csvmod
    for label, path in csvs.items():
        rows = list(csvmod.DictReader(open(path)))
        last = rows[-1]
        cc, fc = int(last["corpus_caught"]), int(last["fresh_caught"])
        tot = cc + fc
        frac = cc / tot if tot else 0.0
        print(f"[M8] {label} corpus-on: rejections caught by replay={cc} "
              f"fresh={fc} (replay fraction={frac:.2f})")
    return {"plot": png}


# ==========================================================================
# WP-B (F-INT-3): m9 / m9_planted -- the formalization reach-vs-cost curve.
#
# The math reach series is `math_covered / math_total` (F-INT-3), plotted via
# the established shim (milestones.py:74-92 `_metrics_run` precedent): an
# intermediate CSV with reach, `verifier_seconds = 0` (so the cost axis is
# kilotokens only -- E6 is respected, tokens are NEVER summed with seconds),
# and the cumulative token columns, handed to the existing `reach_vs_cost`.
#
# ⚠FI-1 (declared ordering edge): the live loop cannot PROPOSE a `math` move
# until WP-A lands `_math_moves` in buildloop/loop.py -- `dispatch=` overrides
# EXECUTORS, never PROPOSALS.  Both m9 and m9_planted therefore only retire math
# rows once WP-A merges; until then the curve is empty and an honest deferred
# note is printed (the unit teeth SKIP with reason "requires WP-A _math_moves").
# ==========================================================================
_SYN_TOKENS_IN = 1200.0   # synthetic per-serve token increments (⚠FI-21): with
_SYN_TOKENS_OUT = 400.0   # 3 committed fixtures + zero real cost the plot would
#                           be a degenerate zero-width artifact; these give the
#                           x-axis real width and are LABELLED synthetic in the
#                           plot title.  They are NEVER conflated with real LLM
#                           counters in a live m9 run (m9 uses the real dispatch).


def _wp_a_ready() -> bool:
    """⚠FI-1: math moves are proposed only once WP-A lands `_math_moves`."""
    from buildloop import loop
    return hasattr(loop, "_math_moves")


def _llm_available() -> bool:
    import shutil
    return bool(shutil.which(common.CLAUDE_CLI)
                or pathlib.Path(common.CLAUDE_CLI).exists())


def _seed_math_backlog(reg) -> dict:
    """Seed the specs/mathsources corpus as math-source demand rows (the cgb
    `_ledger_sync` math-source scheme, demand_id = sha256('math-source:'+relpath)).
    Top-level *.txt are EXOGENOUS ground truth; dream/d*.txt are SYSTEM-origin
    paraphrases.  Written here (not via cgb) so ONLY math rows enter the ledger:
    the combined loop then proposes only math moves and the LLM-free planted
    dispatch is the sole executor exercised."""
    root = common.REPO_ROOT
    ms = root / "specs" / "mathsources"
    counts = {"exogenous": 0, "dream": 0}

    def _ingest(p, origin):
        relpath = str(p.resolve().relative_to(root))
        did = common.sha256_bytes(("math-source:" + relpath).encode())
        if reg.demand_get(did) is None:
            reg.demand_upsert({
                "demand_id": did, "kind": "math-source", "origin": origin,
                "status": "open", "language": None, "features": None,
                "payload_ref": relpath, "size_bytes": p.stat().st_size})
        return did

    for p in sorted(ms.glob("*.txt")):
        _ingest(p, "exogenous")
        counts["exogenous"] += 1
    dream = ms / "dream"
    if dream.exists():
        for p in sorted(dream.glob("d*.txt")):
            _ingest(p, "system")
            counts["dream"] += 1
    return counts


def _committed_fixture_readings() -> dict:
    """demand_id -> the committed reading_doc {theorem, statements} for each
    specs/mathsources/readings/*.json fixture (READ, never edited).  The
    reading_doc is exactly obj['reading'] -- no `origin` key (⚠FI-13)."""
    root = common.REPO_ROOT
    rdir = root / "specs" / "mathsources" / "readings"
    out = {}
    for jf in sorted(rdir.glob("*.json")):
        obj = json.loads(jf.read_text())
        txt = rdir.parent / (jf.stem + ".txt")
        relpath = str(txt.resolve().relative_to(root))
        did = common.sha256_bytes(("math-source:" + relpath).encode())
        out[did] = obj["reading"]
    return out


def _planted_math_dispatch(fixtures):
    """A deterministic, LLM-free `math` executor (F-INT-1 signature) serving the
    committed fixtures, with synthetic per-serve token increments (⚠FI-21).  It
    is injected as `dispatch={'math': planted}`; WP-A's `_math_moves` proposes
    the row, this serves it."""
    def planted(move, snap, registry, backlog, policy, use_corpus, model):
        did = move.get("demand_id") or move["candidate_key"].split("math:", 1)[-1]
        # Synthetic spend on EVERY serve so the cost axis grows monotonically
        # even for a row with no committed fixture (labelled synthetic).
        registry.counter_add("llm_input_tokens", _SYN_TOKENS_IN)
        registry.counter_add("llm_output_tokens", _SYN_TOKENS_OUT)
        reading_doc = fixtures.get(did)
        if reading_doc is None:
            registry.log_event("math-refused",
                               {"demand_id": did, "reason": "no-planted-fixture"})
            return {"status": "math-refused", "demand_id": did,
                    "stage": None, "reason": "no-planted-fixture"}
        registry.reading_add(did, common.canonical_json(reading_doc),
                             "planted:" + did)
        registry.demand_set_status(did, "covered", None)
        return {"status": "math-certified", "demand_id": did, "stage": None}
    return planted


def _run_math_curve(reg, *, n_iter, dispatch, label, title, out_png):
    """Run the combined loop N iterations, log per-iteration math_covered/
    math_total + cumulative token counters, and plot the reach series via the
    F-INT-3 shim.  Returns the collected series."""
    from buildloop.loop import run_iteration
    from metrics import snapshot
    from metrics.plots import reach_vs_cost
    series = []
    for i in range(n_iter):
        run_iteration(reg, [], dispatch=dispatch)
        row = snapshot(reg, [], event=f"{label}-iter-{i}")
        series.append(row)
        if row["math_total"]:
            print(f"[{label}] iter {i}: math_covered={row['math_covered']}/"
                  f"{row['math_total']} "
                  f"ktokens={(row['llm_input_tokens']+row['llm_output_tokens'])/1000:.1f}")
    # F-INT-3 shim CSV: reach = math_covered/math_total, verifier_seconds = 0
    # (cost axis is kilotokens only), cumulative token columns.
    shim = common.ARTIFACTS / f"{label}_shim.csv"
    with open(shim, "w", newline="") as f:
        import csv as _csv
        w = _csv.writer(f)
        w.writerow(["reach", "llm_input_tokens", "llm_output_tokens",
                    "verifier_seconds"])
        for row in series:
            reach = row["math_covered"] / max(1, row["math_total"])
            w.writerow([round(reach, 4), row["llm_input_tokens"],
                        row["llm_output_tokens"], 0])
    reach_vs_cost({label: str(shim)}, str(out_png), title=title)
    print(f"[{label}] plot -> {out_png}")
    return series


def m9(reg):
    """Formalization reach-vs-cost over the live combined loop (F-INT-3 B2).

    Seeds the specs/mathsources corpus, runs N=20 combined-loop iterations with
    the LIVE `math` dispatch (real LLM authoring), and plots the reach series.
    REQUIRES an LLM endpoint AND WP-A's `_math_moves` -- honest-skips otherwise
    (H43 / ⚠FI-1), never faking green."""
    results = common.REPO_ROOT / "results"
    results.mkdir(exist_ok=True)
    out_png = results / "math_reach_vs_cost.png"
    if not _wp_a_ready():
        print("[m9] DEFERRED: buildloop.loop lacks _math_moves (WP-A ordering "
              "edge, ⚠FI-1); the live curve verifies only after WP-A merges.")
        return {"deferred": "requires WP-A _math_moves"}
    if not _llm_available():
        print("[m9] SKIPPED (REQUIRES_LLM): no LLM endpoint; run the LLM-free "
              "m9_planted for the deterministic curve (H43).")
        return {"skipped": "REQUIRES_LLM: no endpoint"}
    reg = Registry(db_path=str(common.ARTIFACTS / "m9_live.sqlite"))
    counts = _seed_math_backlog(reg)
    print(f"[m9] seeded math backlog: {counts}")
    _run_math_curve(reg, n_iter=20, dispatch=None, label="m9",
                    title="Formalization reach vs cost (live combined loop)",
                    out_png=out_png)
    return {"plot": str(out_png)}


def m9_planted(reg):
    """LLM-free, deterministic reach-vs-cost curve (F-INT-3 B3).

    Same runner as m9 but with an injected `dispatch={'math': planted}` serving
    the committed specs/mathsources/readings fixtures, plus SYNTHETIC per-serve
    token increments (⚠FI-21) so the x-axis has real width.  Reach is monotone
    nondecreasing and cost strictly increasing.  Also gated on WP-A (⚠FI-1):
    m9_planted exercises move PROPOSAL, not just dispatch."""
    results = common.REPO_ROOT / "results"
    results.mkdir(exist_ok=True)
    out_png = results / "math_reach_vs_cost.png"
    reg = Registry(db_path=str(common.ARTIFACTS / "m9_planted.sqlite"))
    counts = _seed_math_backlog(reg)
    print(f"[m9_planted] seeded math backlog: {counts}")
    if not _wp_a_ready():
        print("[m9_planted] DEFERRED: buildloop.loop lacks _math_moves (WP-A "
              "ordering edge, ⚠FI-1); the loop proposes no math move, so the "
              "curve stays empty until WP-A merges.  Plot written for shape.")
    fixtures = _committed_fixture_readings()
    dispatch = {"math": _planted_math_dispatch(fixtures)}
    series = _run_math_curve(
        reg, n_iter=20, dispatch=dispatch, label="m9_planted",
        title="Formalization reach vs cost (planted, synthetic token x-axis)",
        out_png=out_png)
    covered = [row["math_covered"] for row in series]
    assert covered == sorted(covered), "math_covered must be nondecreasing"
    return {"plot": str(out_png), "final_covered": covered[-1] if covered else 0,
            "fixtures": len(fixtures)}


MILESTONES = {"m1": m1, "m2": m2, "m5": m5, "m6": m6, "m7": m7, "m8": m8,
              "m9": m9, "m9_planted": m9_planted}


def main():
    common.ensure_dirs()
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    reg = Registry()
    targets = list(MILESTONES) if which == "all" else [which]
    out = {}
    for t in targets:
        if t not in MILESTONES:
            print(f"unknown milestone {t}; choose from {list(MILESTONES)} or 'all'")
            sys.exit(1)
        print(f"\n===== {t} =====")
        out[t] = MILESTONES[t](reg)
    (common.ARTIFACTS / "milestones_summary.json").write_text(
        json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()

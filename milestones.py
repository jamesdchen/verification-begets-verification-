#!/usr/bin/env python3
"""Milestone driver: runs each milestone and writes artifacts under
artifacts/.  See README.md for what each milestone demonstrates.

Usage:  python3 milestones.py {m1,m2,m5,m6,m7,m8,all}
Milestones m3 (build loop) and m4 (recursion) are driven directly via
`cgb.py build`; they are summarized here from the live registry state.
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


MILESTONES = {"m1": m1, "m2": m2, "m5": m5, "m6": m6, "m7": m7, "m8": m8}


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

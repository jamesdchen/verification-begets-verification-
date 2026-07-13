#!/usr/bin/env python3
"""Certified Generator Bootstrap -- command-line interface.

Subcommands:
  seed                 register the opening library (Kaitai emit-check tier),
                       driven through the kernel like any other candidate
  gen-backlog          (re)generate the fixed ~200-spec backlog
  run SPEC             task-time path: spec -> planner -> generators -> code
  promote HASH|NAME    attempt universal-tier upgrade
  build [--policy ...] one build-loop iteration (LLM proposes a spec)
  status               registry summary
  events [KIND]        dump logged events
  metrics-snapshot     record a metrics row
  export-csv PATH      dump metrics_log to CSV
"""
from __future__ import annotations

import argparse
import json
import sys

import common
from library import Registry


def _find_generator(reg, ident):
    for g in reg.all_generators():
        if g["generator_hash"] == ident or g["generator_hash"].startswith(ident) \
                or g["name"] == ident:
            return g
    raise SystemExit(f"no generator matching {ident!r}")


def cmd_seed(args):
    reg = Registry()
    from buildloop import admission
    from metrics import backlog as backlog_mod, snapshot
    bl_dir = backlog_mod.generate()
    from buildloop.loop import backlog_index
    backlog = backlog_index(bl_dir)
    # Seed candidate: Kaitai over fixed-width unsigned ints, big-endian.
    # Even the seed is admitted only after a kernel emission check.
    cand = {
        "name": "kaitai-fixed-uint-be", "spec_language": "ksy",
        "output_language": "python-codec",
        "spec_grammar": {"atoms": ["endian:be", "uint:1", "uint:2",
                                   "uint:4", "uint:8"]},
        "emit_entrypoint": {"kind": "ksc-python-rw"},
        "contract": {"type": "codec-roundtrip"},
        "provenance": {"author": "human-seed",
                       "parents": ["kaitai-struct-compiler"], "depth": 1,
                       "note": "opening library inventory (Kaitai Struct)"},
    }
    try:
        ev = admission.admit(reg, cand, backlog, use_corpus=args.corpus)
        print("seeded:", json.dumps(ev, indent=2))
    except admission.AdmissionFailure as e:
        print("seed admission FAILED:", e)
        if e.transcript:
            print(e.transcript.get("llm_feedback", "")[:800])
        sys.exit(1)
    snapshot(reg, backlog, event="seed",
             corpus=args.corpus)
    print(f"backlog: {len(backlog)} specs at {bl_dir}")


def cmd_gen_backlog(args):
    from metrics import backlog as backlog_mod
    d = backlog_mod.generate()
    print("backlog generated at", d)


def cmd_run(args):
    reg = Registry()
    import run as runner
    res = runner.run_task(reg, args.spec, use_corpus=args.corpus)
    if res.ok:
        print(f"OK -> {res.out_dir}")
        print("  chain tiers:", res.certificate["chain_tiers"])
        print("  provenance depth:", res.provenance["provenance_depth"])
        print("  emission checks:", res.certificate["emission_checks"])
    else:
        print("FAILED:", res.error)
        if res.transcript:
            print(res.transcript.get("llm_feedback", "")[:800])
        if res.miss:
            print("  miss:", res.miss.get("reason"), res.miss.get("missing_atoms"))
        sys.exit(2)


def cmd_promote(args):
    reg = Registry()
    from buildloop import promote as promote_mod
    from metrics import snapshot
    from buildloop.loop import backlog_index
    g = _find_generator(reg, args.ident)
    res = promote_mod.promote(reg, g["generator_hash"])
    print(json.dumps({k: v for k, v in res.items() if k != "channels"}, indent=2))
    if res.get("channels"):
        print("agreeing channels:",
              [c["backend"] + ":" + c["result"] for c in res["channels"]])
    if res["status"] == "promoted":
        backlog = backlog_index(common.REPO_ROOT / "specs" / "backlog")
        snapshot(reg, backlog, event=f"promote:{g['name']}")


def cmd_build(args):
    reg = Registry()
    from buildloop import loop
    from metrics import snapshot
    from buildloop.loop import backlog_index
    backlog = backlog_index(common.REPO_ROOT / "specs" / "backlog")
    res = loop.run_iteration(reg, backlog, policy=args.policy,
                             use_corpus=args.corpus, model=args.model)
    print(json.dumps({k: v for k, v in res.items()
                      if k not in ("transcripts",)}, indent=2))
    if res["status"] in ("admitted",):
        snapshot(reg, backlog, event="admission", policy=args.policy,
                 corpus=args.corpus)


def cmd_status(args):
    reg = Registry()
    print(f"DB: {reg.path}")
    for g in reg.all_generators():
        flag = " [RETIRED]" if g["retired"] else ""
        print(f"  {g['tier']:10s} {g['name']:28s} "
              f"{g['spec_language']}->{g['output_language']} "
              f"checked={g['emission_checked']} fail={g['emission_failures']}"
              f"{flag}")
        print(f"             atoms={sorted(g['spec_grammar']['atoms'])}")
    ev_kinds = {}
    for e in reg.events():
        ev_kinds[e["kind"]] = ev_kinds.get(e["kind"], 0) + 1
    print("events:", ev_kinds)


def cmd_events(args):
    reg = Registry()
    for e in reg.events(args.kind):
        print(f"[{e['id']}] {e['kind']}: "
              f"{json.dumps(e['payload'])[:400]}")


def cmd_metrics_snapshot(args):
    reg = Registry()
    from metrics import snapshot
    from buildloop.loop import backlog_index
    backlog = backlog_index(common.REPO_ROOT / "specs" / "backlog")
    row = snapshot(reg, backlog, event=args.event, policy=args.policy,
                   corpus=args.corpus)
    print(json.dumps(row, indent=2))


def cmd_export_csv(args):
    reg = Registry()
    from metrics import export_csv
    print("wrote", export_csv(reg, args.path))


def main():
    p = argparse.ArgumentParser(prog="cgb")
    p.add_argument("--corpus", action="store_true",
                   help="enable counterexample-corpus screening")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("seed").set_defaults(func=cmd_seed)
    sub.add_parser("gen-backlog").set_defaults(func=cmd_gen_backlog)
    sp = sub.add_parser("run"); sp.add_argument("spec"); sp.set_defaults(func=cmd_run)
    sp = sub.add_parser("promote"); sp.add_argument("ident"); sp.set_defaults(func=cmd_promote)
    sp = sub.add_parser("build")
    sp.add_argument("--policy", choices=["frequency", "closure"], default="frequency")
    sp.add_argument("--model", default=None)
    sp.set_defaults(func=cmd_build)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sp = sub.add_parser("events"); sp.add_argument("kind", nargs="?"); sp.set_defaults(func=cmd_events)
    sp = sub.add_parser("metrics-snapshot")
    sp.add_argument("--event", default="manual"); sp.add_argument("--policy", default="")
    sp.set_defaults(func=cmd_metrics_snapshot)
    sp = sub.add_parser("export-csv"); sp.add_argument("path"); sp.set_defaults(func=cmd_export_csv)

    args = p.parse_args()
    common.ensure_dirs()
    args.func(args)


if __name__ == "__main__":
    main()

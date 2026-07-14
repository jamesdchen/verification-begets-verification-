#!/usr/bin/env python3
"""Certified Generator Bootstrap -- command-line interface.

Subcommands:
  seed                 register the opening library (Kaitai emit-check tier),
                       driven through the kernel like any other candidate
  gen-backlog          (re)generate the fixed ~200-spec backlog
  run SPEC             task-time path: spec -> planner -> generators -> code
  service SPEC         compose a whole service: certify every tool schema,
                       constraint, the protocol, and the composed dispatcher
  synthesize REQUEST   LLM authors a service meta-spec (spec only) from a
                       natural-language request; pipeline certifies it end-to-end
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


def cmd_differential(args):
    """Path (i): certify a spec's codec by cross-implementation differential
    (Kaitai vs. an independent reference codec) + Dafny proof."""
    import pathlib as _pl
    from generators import ksy_model
    from generators.emitters import emit_ksc_python_rw
    import kernel as _kernel
    from kernel.certs import Certificate
    text = _pl.Path(args.spec).read_text()
    sm = ksy_model.parse_ksy(text)
    files = emit_ksc_python_rw(text)
    v = _kernel.check({"kind": "python-codec", "files": files},
                      {"type": "codec-differential", "spec_model": sm})
    if isinstance(v, Certificate):
        print("CERTIFIED via independent channels:",
              [(c["backend"], c["result"]) for c in v.channels])
    else:
        t = v.to_dict()
        print(f"NOT certified ({t['verdict']}):",
              [(c["backend"], c["result"]) for c in t["channels"]])
        sys.exit(2)


def cmd_tool(args):
    """Task-time: certify an agent tool contract (JSON Schema) via two
    independent validators -- strict Pydantic + the jsonschema reference."""
    import pathlib as _pl
    from generators import toolgen
    import kernel as _kernel
    from kernel.certs import Certificate
    schema_text = _pl.Path(args.schema).read_text()
    files = toolgen.emit_pydantic_tool(schema_text)
    v = _kernel.check({"kind": "tool", "files": files},
                      {"type": "tool-differential", "schema_text": schema_text})
    if isinstance(v, Certificate):
        print("TOOL CERTIFIED via independent validators:",
              [(c["backend"], c["result"]) for c in v.channels])
        od = common.ARTIFACTS / "out" / f"tool-{v.subject_hash[:8]}"
        od.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (od / name).write_bytes(data)
        (od / "certificate.json").write_text(json.dumps(v.to_dict(), indent=2))
        print("  ->", od)
    else:
        t = v.to_dict()
        print(f"NOT certified ({t['verdict']}):",
              [(c["backend"], c["result"]) for c in t["channels"]])
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        if fail.get("detail"):
            print("  detail:", fail["detail"][:400])
        sys.exit(2)


def cmd_protocol(args):
    """Certify a stateful protocol: prove sequencing safety (Z3 AND CVC5 BMC)
    and check the emitted session validator against a reference simulator."""
    import pathlib as _pl
    from generators import protocol_model, protocol_gen
    import kernel as _kernel
    from kernel.certs import Certificate
    spec_text = _pl.Path(args.spec).read_text()
    m = protocol_model.parse_protocol_spec(spec_text)
    K, complete, _depth = m.acyclic_bound()
    files = protocol_gen.emit_validator(m)
    v = _kernel.check({"kind": "protocol-validator", "files": files},
                      {"type": "protocol-cert", "spec_text": spec_text})
    tag = "complete" if complete else f"bounded (K={K})"
    if isinstance(v, Certificate):
        print(f"PROTOCOL CERTIFIED [{tag}] (safety proof + conformance):",
              [(c["backend"], c["result"]) for c in v.channels])
    else:
        t = v.to_dict()
        print(f"NOT certified ({t['verdict']}) [{tag}]:",
              [(c["backend"], c["result"]) for c in t["channels"]])
        cx = protocol_gen.counterexample(m, K)
        if cx:
            print("  solver counterexample (illegal trace):", json.dumps(cx))
        sys.exit(2)


def cmd_constraint(args):
    """Certify a cross-field constraint contract: prove constraints => invariant
    (Z3 AND CVC5) and check the emitted validator against solver-generated
    boundary inputs."""
    import pathlib as _pl
    from generators import constraint_gen
    import kernel as _kernel
    from kernel.certs import Certificate
    spec_text = _pl.Path(args.spec).read_text()
    from generators import constraint_model
    m = constraint_model.parse_constraint_spec(spec_text)
    files = constraint_gen.emit_validator(m)
    v = _kernel.check({"kind": "constraint-validator", "files": files},
                      {"type": "constraint-cert", "spec_text": spec_text})
    if isinstance(v, Certificate):
        print("CONSTRAINT CERTIFIED (proof + solver-boundary):",
              [(c["backend"], c["result"]) for c in v.channels])
    else:
        t = v.to_dict()
        print(f"NOT certified ({t['verdict']}):",
              [(c["backend"], c["result"]) for c in t["channels"]])
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        if fail.get("detail"):
            print("  detail:", str(fail["detail"])[:400])
        sys.exit(2)


def cmd_service(args):
    """Compose a whole service from one meta-spec: certify every tool schema,
    every cross-field constraint, the protocol sequencing, and that the emitted
    dispatcher faithfully ANDs the four certified layers together."""
    import pathlib as _pl
    from run import service as _svc
    spec_text = _pl.Path(args.spec).read_text()
    reg = Registry()
    r = _svc.certify_service(spec_text, event_sink=reg.log_event,
                             cache_get=reg.cache_get, cache_put=reg.cache_put)
    for L in r.layers:
        mark = "OK " if L["certified"] else "XX "
        print(f"  {mark}{L['layer']:<28} {L['channels']}")
    if r.ok:
        print(f"SERVICE '{r.name}' CERTIFIED -- {len(r.layers)} layers composed")
        print("  ->", r.out_dir)
    else:
        print(f"SERVICE '{r.name}' NOT certified: first failing layer = "
              f"{r.failed_layer}")
        sys.exit(2)


def cmd_synthesize(args):
    """Close the flywheel: the LLM authors a service meta-spec (a spec only)
    from a natural-language request, and the deterministic pipeline certifies
    the whole service -- schemas, constraints, protocol, and composition."""
    import pathlib as _pl
    from buildloop import service_loop
    request = _pl.Path(args.request).read_text() if _pl.Path(args.request).exists() \
        else args.request
    reg = Registry()
    if args.semantic:
        res = service_loop.synthesize_semantic(
            request, max_rounds=args.rounds, model=args.model,
            event_sink=reg.log_event, cache_get=reg.cache_get,
            cache_put=reg.cache_put, examiner=not args.no_intent)
    else:
        res = service_loop.synthesize_service(
            request, max_rounds=args.rounds, model=args.model,
            event_sink=reg.log_event, cache_get=reg.cache_get,
            cache_put=reg.cache_put, intent=not args.no_intent)
    if res["status"] == "certified":
        print(f"SERVICE '{res['name']}' SYNTHESIZED + CERTIFIED in "
              f"{res['rounds']} round(s), {res['tokens']} tokens")
        for layer, ok, ch in res["layers"]:
            print(f"  {'OK' if ok else 'XX'} {layer:<28} {ch}")
        print("  ->", res["out_dir"])
        print("  spec:", json.dumps(res["spec"]))
        if "provenance" in res:
            print("  provenance:", json.dumps(res["provenance"]))
    else:
        print(f"NOT certified ({res['status']}) after {res['rounds']} round(s)")
        for t in res.get("last", []):
            print("  last transcript:", t[:600])
        sys.exit(2)


def cmd_lift(args):
    """Schema-lift: infer a JSON Schema from an incumbent validator and certify
    the inferred schema by differential against that incumbent."""
    import pathlib as _pl
    from buildloop import schema_lift
    src = _pl.Path(args.incumbent).read_text()
    name = args.name or _pl.Path(args.incumbent).stem
    res = schema_lift.lift(src, name, model=args.model)
    print(json.dumps({k: v for k, v in res.items() if k != "last"}, indent=2))
    if res["status"] != "lifted":
        sys.exit(2)


def cmd_chain_differential(args):
    """Rung differential: certify an ABNF spec's codec by two independent
    end-to-end routes -- the tree-sitter chain (parser->ksy->Kaitai) vs. the
    reference route (reference tokenizer->independent mapper->reference codec)."""
    import pathlib as _pl
    from generators import ksy_model, abnf_chain
    from generators.emitters import emit_ksc_python_rw
    import kernel as _kernel
    from kernel.certs import Certificate
    reg = Registry()
    text = _pl.Path(args.spec).read_text()
    toks = abnf_chain.tokenize(text)
    # Route A: prefer the registered emitted parser (full-rung); fall back to
    # the reference tokenizer for the ksy mapper if no parser is registered.
    ksy_a = None
    for g in reg.live_generators():
        if g["spec_language"] == "abnf" and g["emit_entrypoint"].get("artifact_dir"):
            ad = _pl.Path(g["emit_entrypoint"]["artifact_dir"])
            ksy_a = abnf_chain.abnf_to_ksy_via_parser(
                (ad / "parser.so").read_bytes(), text,
                (ad / "grammar.json").read_bytes())
            break
    if ksy_a is None:
        ksy_a = abnf_chain.tokens_to_ksy(toks, common.sha256_bytes(text.encode()))
    spec_a = ksy_model.parse_ksy(ksy_a)
    files_a = emit_ksc_python_rw(ksy_a)
    fields_b = abnf_chain.abnf_tokens_to_fields(toks)  # independent route
    v = _kernel.check({"kind": "python-codec", "files": files_a},
                      {"type": "codec-differential", "spec_model": spec_a,
                       "ref_fields": fields_b})
    if isinstance(v, Certificate):
        print("RUNG CERTIFIED (chain route == independent route):",
              [(c["backend"], c["result"]) for c in v.channels])
    else:
        t = v.to_dict()
        print(f"NOT certified ({t['verdict']}):",
              [(c["backend"], c["result"]) for c in t["channels"]])
        sys.exit(2)


def cmd_ledger(args):
    """The one demand ledger (Combined-Loop W0).

      ledger sync    ingest specs/backlog, specs/requests, specs/incumbent as
                     exogenous demand rows (idempotent; existing rows are never
                     re-tagged), then ingest any task-time toll counters.
      ledger status  summarize the ledger by kind/status and the ledger_dl.
    """
    import pathlib as _pl
    reg = Registry()
    action = args.action or "sync"
    if action == "sync":
        n = _ledger_sync(reg)
        toll = reg.ingest_toll_jsonl(common.ARTIFACTS / "toll.jsonl")
        reg.log_event("ledger-sync", {"rows_seen": n["seen"],
                                      "rows_added": n["added"],
                                      "toll_records_ingested": toll})
        print(f"ledger sync: {n['added']} new / {n['seen']} seen "
              f"(spec-file={n['spec-file']}, nl-request={n['nl-request']}, "
              f"caged-incumbent={n['caged-incumbent']}); "
              f"toll records ingested: {toll}")
    elif action == "status":
        from buildloop import dl as dl_mod
        rows = reg.demand_all()
        by = {}
        for r in rows:
            by[(r["kind"], r["status"])] = by.get((r["kind"], r["status"]), 0) + 1
        for (k, s), c in sorted(by.items()):
            print(f"  {k:<16} {s:<10} {c}")
        total = dl_mod.ledger_dl(reg)
        print(f"  ledger_dl = {round(total['ledger_dl'], 3)}  "
              f"(covered spec={total['covered_spec']}/{total['total_spec']}, "
              f"request={total['covered_request']}/{total['total_request']})")
    else:
        raise SystemExit(f"unknown ledger action {action!r}")


def _ledger_sync(reg) -> dict:
    """Ingest the committed, static demand sources as EXOGENOUS rows.  Fixed,
    LLM-free code (house rule 5).  demand_id = sha256(kind + ':' + relpath);
    payload_ref = repo-relative path.  spec-file rows get their feature atoms
    now; nl-request / caged-incumbent features stay NULL (a request is
    backfilled from its Reading by the W0.2 hook; an incumbent's tool alphabet
    is only observable by learning it -- the W4 lift backfills it)."""
    import pathlib as _pl
    import planner as planner_mod
    root = common.REPO_ROOT
    system_payloads = reg.demand_payload_hashes()
    counts = {"seen": 0, "added": 0, "spec-file": 0, "nl-request": 0,
              "caged-incumbent": 0}

    def _relpath(p):
        return str(_pl.Path(p).resolve().relative_to(root))

    def _ingest(p, kind, language, features):
        relpath = _relpath(p)
        # house rule 12: a committed system rewrite cannot launder itself back
        # into an exogenous row (payload-hash collision guard).
        if relpath in system_payloads:
            return
        did = common.sha256_bytes((kind + ":" + relpath).encode())
        size = _pl.Path(p).stat().st_size
        before = reg.demand_get(did)
        reg.demand_upsert({
            "demand_id": did, "kind": kind, "origin": "exogenous",
            "status": "open", "language": language, "features": features,
            "payload_ref": relpath, "size_bytes": size})
        counts["seen"] += 1
        counts[kind] += 1
        if before is None:
            counts["added"] += 1

    # spec-file demand: the codec/format backlog
    bl = root / "specs" / "backlog"
    if bl.exists():
        for p in sorted(bl.glob("*")):
            if p.suffix not in (".ksy", ".abnf"):
                continue
            try:
                language, _text, atoms = planner_mod.load_spec(p)
                feats = sorted(atoms)
            except Exception:
                language, feats = None, None
            _ingest(p, "spec-file", language, feats)

    # nl-request demand: natural-language service requests
    rq = root / "specs" / "requests"
    if rq.exists():
        for p in sorted(rq.glob("*.txt")):
            _ingest(p, "nl-request", None, None)

    # caged-incumbent demand: world-code to convert
    inc = root / "specs" / "incumbent"
    if inc.exists():
        for p in sorted(inc.glob("*.py")):
            _ingest(p, "caged-incumbent", None, None)

    return counts


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
    sp = sub.add_parser("differential"); sp.add_argument("spec"); sp.set_defaults(func=cmd_differential)
    sp = sub.add_parser("chain-differential"); sp.add_argument("spec"); sp.set_defaults(func=cmd_chain_differential)
    sp = sub.add_parser("tool"); sp.add_argument("schema"); sp.set_defaults(func=cmd_tool)
    sp = sub.add_parser("constraint"); sp.add_argument("spec"); sp.set_defaults(func=cmd_constraint)
    sp = sub.add_parser("protocol"); sp.add_argument("spec"); sp.set_defaults(func=cmd_protocol)
    sp = sub.add_parser("service"); sp.add_argument("spec"); sp.set_defaults(func=cmd_service)
    sp = sub.add_parser("synthesize"); sp.add_argument("request")
    sp.add_argument("--rounds", type=int, default=5)
    sp.add_argument("--model", default=None)
    sp.add_argument("--no-intent", action="store_true",
                    help="skip the independent scenario cross-check")
    sp.add_argument("--semantic", action="store_true",
                    help="LLM authors a Reading (quoted, force-tagged semantic "
                         "analysis); a deterministic compiler builds the spec")
    sp.set_defaults(func=cmd_synthesize)
    sp = sub.add_parser("lift"); sp.add_argument("incumbent")
    sp.add_argument("--name", default=None); sp.add_argument("--model", default=None)
    sp.set_defaults(func=cmd_lift)
    sp = sub.add_parser("promote"); sp.add_argument("ident"); sp.set_defaults(func=cmd_promote)
    sp = sub.add_parser("build")
    sp.add_argument("--policy", choices=["frequency", "closure"], default="frequency")
    sp.add_argument("--model", default=None)
    sp.set_defaults(func=cmd_build)
    sp = sub.add_parser("ledger")
    sp.add_argument("action", nargs="?", choices=["sync", "status"],
                    default="sync")
    sp.set_defaults(func=cmd_ledger)
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

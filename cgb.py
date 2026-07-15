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
              f"caged-incumbent={n['caged-incumbent']}, "
              f"math-source={n['math-source']}); "
              f"toll records ingested: {toll}")
    elif action == "seed-readings":
        n = _seed_readings(reg)
        reg.log_event("ledger-seed-readings", n)
        print(f"seed-readings: {n['certified']} certified "
              f"(real={n['real']}, dream={n['dream']}), "
              f"{n['failed']} failed / {n['seen']} seen")
        m = _seed_math_readings(reg)
        reg.log_event("ledger-seed-math-readings", m)
        print(f"seed-math-readings: {m['covered']} covered "
              f"(fidelity-tier; F0 kernel statement-cert deferred when Lean is "
              f"absent), {m['failed']} failed / {m['seen']} seen")
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
              f"request={total['covered_request']}/{total['total_request']}, "
              f"math={total['covered_math']}/{total['total_math']}, "
              f"dream_rows={total['dream_rows']})")
    else:
        raise SystemExit(f"unknown ledger action {action!r}")


def _seed_readings(reg, root=None) -> dict:
    """Seed the readings table from committed specs/readings/ files (Zone 3 S0.2).

    Fixed, LLM-free (house rule 5).  Provenance is DERIVED from the demand
    ledger's `origin`, never inferred from a path (H55):
      * a top-level specs/readings/*.json is REAL: its `request` MUST byte-match a
        committed specs/requests/*.txt file (H44 -- enforcement lives here, where
        `ledger sync` already byte-matches payloads); the reading joins that
        request's exogenous nl-request row (demand_id = sha256("nl-request:"+relpath),
        identical to _ledger_sync).  A real-classified reading with no byte-match is
        a HARD ERROR.
      * a specs/readings/dream/*.json is a DREAM: it is seeded against a fresh
        SYSTEM-origin nl-request row, so the witness filter (S5) can exclude it.
    Each reading is CERTIFIED at seed time via the LLM-free `certify_reading`
    (dl.py treats any readings row as coverage, so an uncertified seed would
    silently improve ledger_dl -- H46b: certify-at-seed is the honest default),
    and only certified readings are persisted with their composed cert_id."""
    import pathlib as _pl
    from buildloop.reading_corpus import load_readings
    from run.semantic import certify_reading
    root = _pl.Path(root) if root is not None else common.REPO_ROOT
    rdir = root / "specs" / "readings"
    counts = {"seen": 0, "certified": 0, "real": 0, "dream": 0, "failed": 0}
    if not rdir.exists():
        return counts

    req_index = {}                      # committed request TEXT -> repo-rel path
    rq = root / "specs" / "requests"
    if rq.exists():
        for p in sorted(rq.glob("*.txt")):
            req_index[p.read_text()] = str(p.resolve().relative_to(root))

    def _seed_one(entry, dream):
        counts["seen"] += 1
        obj = json.loads(entry.source)
        svc = obj["reading"]["service"]
        reading_text = common.canonical_json(
            {"service": svc, "statements": entry.statements})
        relpath = req_index.get(entry.request)
        if dream:
            did = common.sha256_bytes(
                ("nl-request:dream:"
                 + common.sha256_bytes(entry.request.encode())).encode())
            reg.demand_upsert({
                "demand_id": did, "kind": "nl-request", "origin": "system",
                "status": "open", "language": None, "features": None,
                "payload_ref": relpath or ("dream:" + svc),
                "size_bytes": len(entry.request)})
        else:
            if relpath is None:
                raise SystemExit(
                    f"reading for service {svc!r} is real-classified (top-level) "
                    f"but its request has NO committed specs/requests byte-match "
                    f"(H44); move it under specs/readings/dream/ or commit its "
                    f"request")
            did = common.sha256_bytes(("nl-request:" + relpath).encode())
            if reg.demand_get(did) is None:
                reg.demand_upsert({
                    "demand_id": did, "kind": "nl-request", "origin": "exogenous",
                    "status": "open", "language": None, "features": None,
                    "payload_ref": relpath,
                    "size_bytes": (root / relpath).stat().st_size})
        holder = {}
        res = certify_reading(
            entry.request, reading_text, event_sink=reg.log_event,
            cache_get=reg.cache_get, cache_put=reg.cache_put, write_output=False,
            macro_table=reg.macro_table(),
            on_certified=lambda result, cert_id: holder.__setitem__("cert_id",
                                                                    cert_id))
        if not res.ok:
            counts["failed"] += 1
            reg.log_event("reading-seed-failed",
                          {"service": svc, "stage": res.stage,
                           "error": res.error[:400]})
            return
        reg.reading_add(did, reading_text, holder.get("cert_id", "reading-cert"))
        counts["certified"] += 1
        counts["dream" if dream else "real"] += 1

    for entry in load_readings(rdir):
        _seed_one(entry, dream=False)
    ddir = rdir / "dream"
    if ddir.exists():
        for entry in load_readings(ddir):
            _seed_one(entry, dream=True)
    return counts


def _seed_math_readings(reg, root=None) -> dict:
    """Certify committed MathReadings and persist them into the readings table
    keyed by their math-source demand_id (F3.2), the analogue of _seed_readings.

    Fixed, LLM-free (house rule 5).  Provenance is byte-matched (H44): a
    `specs/mathsources/readings/NN_slug.json` = {source, reading} MUST have a
    `source` that byte-matches the committed `specs/mathsources/NN_slug.txt`
    (the exogenous ground truth), and it joins that corpus row
    (demand_id = sha256("math-source:" + relpath), identical to _ledger_sync).
    A reading with no byte-match is a HARD ERROR.

    Each reading is certified at seed time via the LLM-free `certify_statement`.
    COVERAGE (T10): the F0 kernel statement-cert requires a Lean toolchain and is
    DEFERRED when absent, so coverage here is the FIDELITY tier -- the refusal
    gates (non-vacuity + entailed instances) passed.  dl.py prices a math-source
    row as covered once a reading is present (the nl-request convention), so only
    fidelity-certified readings are persisted; a Lean run upgrades the cert."""
    import pathlib as _pl
    from run.formalize import certify_statement
    root = _pl.Path(root) if root is not None else common.REPO_ROOT
    rdir = root / "specs" / "mathsources" / "readings"
    counts = {"seen": 0, "covered": 0, "failed": 0}
    if not rdir.exists():
        return counts
    for jf in sorted(rdir.glob("*.json")):
        counts["seen"] += 1
        obj = json.loads(jf.read_text())
        source = obj["source"]
        reading_json = common.canonical_json(obj["reading"])
        txt = root / "specs" / "mathsources" / (jf.stem + ".txt")
        if not (txt.exists() and txt.read_text().strip() == source.strip()):
            raise SystemExit(
                f"math reading {jf.name} has no committed specs/mathsources/"
                f"{jf.stem}.txt byte-match (H44); commit its source statement")
        relpath = str(txt.resolve().relative_to(root))
        did = common.sha256_bytes(("math-source:" + relpath).encode())
        if reg.demand_get(did) is None:
            reg.demand_upsert({
                "demand_id": did, "kind": "math-source", "origin": "exogenous",
                "status": "open", "language": None, "features": None,
                "payload_ref": relpath, "size_bytes": txt.stat().st_size})
        res = certify_statement(source, reading_json, event_sink=reg.log_event,
                                cache_get=reg.cache_get, cache_put=reg.cache_put)
        if not res.ok:
            counts["failed"] += 1
            reg.log_event("math-reading-seed-failed",
                          {"theorem": jf.stem, "stage": res.stage,
                           "error": res.error[:400]})
            continue
        cert_id = "statement-cert:" + res.statement_hash \
            if res.statement_cert is None else res.statement_cert.cert_id
        reg.reading_add(did, reading_json, cert_id)
        reg.demand_set_status(did, "covered", None)
        counts["covered"] += 1
    return counts


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
              "caged-incumbent": 0, "math-source": 0}

    def _relpath(p):
        return str(_pl.Path(p).resolve().relative_to(root))

    def _ingest(p, kind, language, features, origin="exogenous"):
        relpath = _relpath(p)
        # house rule 12: a committed system rewrite cannot launder itself back
        # into an exogenous row (payload-hash collision guard).
        if relpath in system_payloads:
            return
        did = common.sha256_bytes((kind + ":" + relpath).encode())
        size = _pl.Path(p).stat().st_size
        before = reg.demand_get(did)
        reg.demand_upsert({
            "demand_id": did, "kind": kind, "origin": origin,
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

    # math-source demand (F3.1): committed English math statements.  Top-level
    # files are the EXOGENOUS ground truth; specs/mathsources/dream/d*.txt are
    # SYSTEM-origin dream paraphrases (they PROPOSE vocabulary but must never
    # bill -- E3).  `d*.txt` matches the manifest's dream convention, so the
    # dir's README.txt (a system-origin note, not a statement) is never a row.
    # Features stay NULL until a MathReading backfills them (like nl-request).
    ms = root / "specs" / "mathsources"
    if ms.exists():
        for p in sorted(ms.glob("*.txt")):
            _ingest(p, "math-source", None, None)
        dream = ms / "dream"
        if dream.exists():
            for p in sorted(dream.glob("d*.txt")):
                _ingest(p, "math-source", None, None, origin="system")

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


def _fragment_report(reg, root=None) -> list:
    """F4.2: rank candidate fragment extensions by demand unlocked per kernel
    surface added.  Deterministic, LLM-free.

    Groups logged `fragment-miss` events (F-I) by `missing_kind_guess`, and for
    each candidate counts the pending `math-source` corpus sentences that WOULD
    transcribe if that kind were added -- read from the corpus MANIFEST's
    non-transcribable entries (`expect_transcribes == false` with a matching
    `miss_kind_guess`; ⚠X14 -- the manifest is the tag source, not a hardcoded
    map), labelled as an accounting ESTIMATE.  The surface cost is a fixed
    descriptor (a new LF kind is kernel-adjacent surface); admission stays
    human-gated (F4.3).  The system prices; a person decides."""
    import pathlib as _pl
    root = _pl.Path(root) if root is not None else common.REPO_ROOT
    # observed misses per guessed kind
    observed = {}
    for e in reg.events("fragment-miss"):
        g = (e["payload"] or {}).get("missing_kind_guess")
        if g:
            observed[g] = observed.get(g, 0) + 1
    # the manifest is the tag source for demand-unlocked estimates (X14)
    unlock = {}
    man_path = root / "specs" / "mathsources" / "manifest.json"
    if man_path.exists():
        man = json.loads(man_path.read_text())
        for f in man.get("files", []):
            if not f.get("expect_transcribes", True) and f.get("miss_kind_guess"):
                g = f["miss_kind_guess"]
                unlock[g] = unlock.get(g, 0) + 1
    kinds = sorted(set(observed) | set(unlock))
    rows = [{"missing_kind_guess": g,
             "observed_misses": observed.get(g, 0),
             "demand_unlocked_estimate": unlock.get(g, 0),
             "surface_cost": "new compile rule + SMT/decidable mirror + prompt lines"}
            for g in kinds]
    # rank by demand unlocked (desc), then observed misses (desc), then kind
    rows.sort(key=lambda r: (-r["demand_unlocked_estimate"],
                             -r["observed_misses"], r["missing_kind_guess"]))
    return rows


def cmd_fragment(args):
    """`cgb fragment report`: the F4.2 frontier-growth ranking (the S2 lookahead
    one rung up, v1 as a REPORT -- admission is human-gated, F4.3)."""
    reg = Registry()
    action = getattr(args, "action", "report") or "report"
    if action != "report":
        raise SystemExit(f"unknown fragment action {action!r}")
    rows = _fragment_report(reg)
    print(f"{'MISSING KIND':<22}{'MISSES':>8}{'UNLOCKED(est)':>15}  SURFACE COST")
    print("-" * 78)
    for r in rows:
        print(f"{r['missing_kind_guess']:<22}{r['observed_misses']:>8}"
              f"{r['demand_unlocked_estimate']:>15}  {r['surface_cost']}")
    if not rows:
        print("  (no fragment-miss events and no non-transcribable corpus tags)")
    print("\nnote: unlock counts are an accounting ESTIMATE from the corpus "
          "manifest; a new LF kind is kernel-adjacent surface and lands ONLY "
          "through the human-gated W5 checklist (specs/mathsources/"
          "FRAGMENT_GROWTH.md).  The system prices; a person decides.")


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
    sp.add_argument("--policy", choices=["frequency", "closure", "lookahead"], default="frequency")
    sp.add_argument("--model", default=None)
    sp.set_defaults(func=cmd_build)
    sp = sub.add_parser("ledger")
    sp.add_argument("action", nargs="?",
                    choices=["sync", "status", "seed-readings"], default="sync")
    sp.set_defaults(func=cmd_ledger)
    sp = sub.add_parser("fragment")
    sp.add_argument("action", nargs="?", choices=["report"], default="report")
    sp.set_defaults(func=cmd_fragment)
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

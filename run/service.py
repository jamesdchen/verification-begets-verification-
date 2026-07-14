"""Service composition: one meta-spec fans out to all four certified
generator families and binds their certificates into a whole-service.

    certify_service(spec_text)
      for each tool:   tool-differential   (its input JSON Schema)
      for each tool
        with cross-field logic: constraint-cert (proved constraints=>invariant)
      the tool set:    protocol-cert        (sequencing safety, dual BMC)
      the composition: service-conformance   (dispatcher faithfully ANDs the
                        four layers, checked vs an independent reference + a
                        liveness non-vacuity witness)

Each layer keeps its own certificate -- the composition does NOT re-prove them.
The service certificate binds every sub-certificate id to the composed
dispatcher's artifact hash, so trust in the whole service reduces to trust in
its four certified layers plus the one conformance check that they compose.

On failure the orchestrator names the FIRST layer that did not certify, so a
break anywhere in the stack is localized to schema / constraint / protocol /
composition rather than reported as an opaque whole-service failure.
"""
from __future__ import annotations

import concurrent.futures as cf
import dataclasses
import json
import os
import pathlib

import common
import kernel
from kernel.certs import Certificate, artifact_hash
from generators import (service_model, service_gen, toolgen, protocol_model,
                        protocol_gen, constraint_gen, constraint_model)


@dataclasses.dataclass
class ServiceResult:
    ok: bool
    name: str = ""
    layers: list = dataclasses.field(default_factory=list)  # per-layer records
    certificate: dict = dataclasses.field(default_factory=dict)
    files: dict = dataclasses.field(default_factory=dict)
    out_dir: str = ""
    failed_layer: str = ""
    error: str = ""


def _channels(v):
    return [(c["backend"], c["result"]) for c in
            (v.channels if isinstance(v, Certificate) else v.to_dict()["channels"])]


def _build_jobs(m, spec_text):
    """Emit each layer's (name, artifact, contract) up front (deterministic
    codegen).  The layers are mutually independent, so they can be checked in
    any order / concurrently; only their certificates are assembled in this
    fixed order afterward, keeping the service certificate byte-identical
    regardless of completion order."""
    jobs = []
    for t in m.tools:                                  # tool schemas
        files = toolgen.emit_pydantic_tool(t.schema_text)
        jobs.append((f"tool:{t.name}", {"kind": "tool", "files": files},
                     {"type": "tool-differential", "schema_text": t.schema_text}))
    for t in m.tools:                                  # cross-field constraints
        if not t.constraints:
            continue
        cspec = json.dumps(t.constraints)
        cm = constraint_model.parse_constraint_spec(cspec)
        cfiles = constraint_gen.emit_validator(cm)
        jobs.append((f"constraint:{t.name}",
                     {"kind": "constraint-validator", "files": cfiles},
                     {"type": "constraint-cert", "spec_text": cspec}))
    pspec = m.protocol_spec_text()                     # sequencing safety
    pm = protocol_model.parse_protocol_spec(pspec)
    K, complete, depth = pm.acyclic_bound()
    pfiles = protocol_gen.emit_validator(pm)
    tag = "complete" if complete else "bounded"
    label = (f"protocol (K={K}, {tag}, D={depth})" if depth
             else f"protocol (K={K}, {tag})")
    jobs.append((label,
                 {"kind": "protocol-validator", "files": pfiles},
                 {"type": "protocol-cert", "spec_text": pspec}))
    svc_files = service_gen.emit_service(m)            # composition
    jobs.append(("composition", {"kind": "service", "files": svc_files},
                 {"type": "service-conformance", "spec_text": spec_text}))
    return jobs, svc_files


def certify_service(spec_text: str, *, event_sink=None, cache_get=None,
                    cache_put=None, write_output=True, max_workers=None):
    """Certify a whole service from one meta-spec.  Returns ServiceResult.

    Scheduling is at CHANNEL granularity: every independent evidence channel of
    every uncached layer becomes its own process task, so the two channels of the
    slowest layer land on two cores (not back-to-back) and the pool packs the
    cores optimally.  Running each channel in its own process also isolates the
    (non-thread-safe) z3 state for free.  The registry's cache and event sink are
    single-threaded (SQLite), so cache lookups, cache writes, adjudication and
    disagreement logging happen on THIS thread; workers run only the pure
    kernel.run_channel.  Unchanged layers hit the cache and never re-run (instant
    re-certification, e.g. across refinement rounds that changed one tool)."""
    m = service_model.parse_service_spec(spec_text)
    jobs, svc_files = _build_jobs(m, spec_text)

    # phase 1 (this thread): cache lookups
    results = [None] * len(jobs)
    misses = []
    for i, (_name, art, con) in enumerate(jobs):
        hit = cache_get(kernel.cache_key(art, con)) if cache_get else None
        if hit is not None:
            results[i] = hit
        else:
            misses.append(i)

    # phase 2: decompose each miss layer into channels, run ALL channels across
    # one flat process pool (channel-granular: overlaps a slow layer's channels
    # and fills cores; each channel's process isolates z3).
    if misses:
        plans = {}                       # i -> [kind, subject, chash, cdesc, chans]
        tasks = []                       # (i, j, spec)
        for i in misses:
            _name, art, con = jobs[i]
            subject, cdesc = kernel._subject_and_cdesc(art, con)
            kind, specs = kernel.channel_specs(art, con)
            plans[i] = [kind, subject, common.sha256_json(cdesc), cdesc,
                        [None] * len(specs)]
            for j, spec in enumerate(specs):
                tasks.append((i, j, spec))
        def _err(spec, e):
            # a crashed channel is an "error" evidence channel -- the layer
            # fails with the exception as its detail (dual-checker: error is
            # not a pass), instead of the whole orchestration crashing
            return {"backend": f"channel:{spec[0]}", "result": "error",
                    "detail": repr(e)[:1200]}
        workers = max_workers or min(8, (os.cpu_count() or 4), len(tasks))
        if workers <= 1 or len(tasks) == 1:
            for i, j, spec in tasks:
                try:
                    plans[i][4][j] = kernel.run_channel(spec)
                except Exception as e:
                    plans[i][4][j] = _err(spec, e)
        else:
            with cf.ProcessPoolExecutor(max_workers=workers) as ex:
                futs = {ex.submit(kernel.run_channel, spec): (i, j, spec)
                        for i, j, spec in tasks}
                for fut in cf.as_completed(futs):
                    i, j, spec = futs[fut]
                    try:
                        plans[i][4][j] = fut.result()
                    except Exception as e:
                        plans[i][4][j] = _err(spec, e)
        # phase 3 (this thread): adjudicate each layer, cache, log disagreements
        for i in misses:
            kind, subject, chash, cdesc, chans = plans[i]
            v = kernel.adjudicate(kind, subject, chash, cdesc, chans,
                                  event_sink=event_sink)
            results[i] = v
            if cache_put:
                cache_put(kernel.cache_key(jobs[i][1], jobs[i][2]), v)

    # assemble per-layer records in fixed job order
    layers = []
    for (name, _art, _con), v in zip(jobs, results):
        ok = isinstance(v, Certificate)
        rec = {"layer": name, "certified": ok, "channels": _channels(v)}
        rec["cert" if ok else "transcript"] = v.to_dict()
        layers.append(rec)

    failed = next((r for r in layers if not r["certified"]), None)
    if failed:
        return _fail(m, layers, failed["layer"], files=svc_files)

    # --- all layers certified: bind them into a service certificate ---
    cert = {
        "kind": "composed-service-certificate",
        "service": m.name,
        "artifact_hash": artifact_hash(svc_files),
        "spec_hash": common.sha256_bytes(spec_text.encode()),
        "layer_certs": [{"layer": r["layer"],
                         "cert_id": r["cert"]["cert_id"],
                         "channels": r["channels"]} for r in layers],
        "created_at": common.now_iso(),
    }
    out_dir = ""
    if write_output:
        od = common.ARTIFACTS / "out" / f"service-{m.name}-{cert['spec_hash'][:8]}"
        od.mkdir(parents=True, exist_ok=True)
        for name, data in svc_files.items():
            (od / name).write_bytes(data)
        (od / "service_certificate.json").write_text(json.dumps(cert, indent=2))
        for r in layers:
            (od / f"cert-{r['layer'].split()[0].replace(':', '_')}.json").write_text(
                json.dumps(r["cert"], indent=2))
        out_dir = str(od)

    return ServiceResult(ok=True, name=m.name, layers=layers, certificate=cert,
                         files=svc_files, out_dir=out_dir)


def _fail(m, layers, failed_layer, files=None):
    return ServiceResult(ok=False, name=m.name, layers=layers,
                         failed_layer=failed_layer, files=files or {},
                         error=f"layer '{failed_layer}' did not certify")

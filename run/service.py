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

import dataclasses
import json
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


def certify_service(spec_text: str, *, event_sink=None, write_output=True):
    """Certify a whole service from one meta-spec.  Returns ServiceResult."""
    m = service_model.parse_service_spec(spec_text)
    layers = []          # {"layer","subject","certified","channels","cert"?}

    def record(layer, verdict):
        ok = isinstance(verdict, Certificate)
        rec = {"layer": layer, "certified": ok, "channels": _channels(verdict)}
        if ok:
            rec["cert"] = verdict.to_dict()
        else:
            rec["transcript"] = verdict.to_dict()
        layers.append(rec)
        return ok

    # --- layer 1: every tool's input schema (tool-differential) ------------
    for t in m.tools:
        files = toolgen.emit_pydantic_tool(t.schema_text)
        v = kernel.check({"kind": "tool", "files": files},
                         {"type": "tool-differential", "schema_text": t.schema_text},
                         event_sink=event_sink)
        if not record(f"tool:{t.name}", v):
            return _fail(m, layers, f"tool:{t.name}")

    # --- layer 2: every declared cross-field constraint (constraint-cert) ---
    for t in m.tools:
        if not t.constraints:
            continue
        cspec = json.dumps(t.constraints)
        cm = constraint_model.parse_constraint_spec(cspec)
        cfiles = constraint_gen.emit_validator(cm)
        v = kernel.check({"kind": "constraint-validator", "files": cfiles},
                         {"type": "constraint-cert", "spec_text": cspec},
                         event_sink=event_sink)
        if not record(f"constraint:{t.name}", v):
            return _fail(m, layers, f"constraint:{t.name}")

    # --- layer 3: sequencing safety of the whole tool set (protocol-cert) --
    pspec = m.protocol_spec_text()
    pm = protocol_model.parse_protocol_spec(pspec)
    K, complete = pm.acyclic_bound()
    pfiles = protocol_gen.emit_validator(pm)
    v = kernel.check({"kind": "protocol-validator", "files": pfiles},
                     {"type": "protocol-cert", "spec_text": pspec},
                     event_sink=event_sink)
    if not record(f"protocol (K={K}, {'complete' if complete else 'bounded'})", v):
        return _fail(m, layers, "protocol")

    # --- layer 4: the composition faithfully ANDs the four layers ----------
    svc_files = service_gen.emit_service(m)
    v = kernel.check({"kind": "service", "files": svc_files},
                     {"type": "service-conformance", "spec_text": spec_text},
                     event_sink=event_sink)
    if not record("composition", v):
        return _fail(m, layers, "composition", files=svc_files)

    # --- all four layers certified: bind them into a service certificate ---
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

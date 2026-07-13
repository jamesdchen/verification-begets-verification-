"""Task-time runner: spec file in -> code out.  ZERO LLM involvement.

    run spec.file -> planner -> generator chain (emitted code sandboxed)
                  -> emission checks for emit-check-tier links
                  -> output code + composed certificate + provenance

The path is deterministic: same spec, same registry state => byte-identical
output code.  buildloop.llm installs a guard that makes any LLM call raise
while a task run is in flight; run/ never imports the LLM client.
"""
from __future__ import annotations

import dataclasses
import json
import os
import pathlib

import common
import kernel
import planner as planner_mod
from generators import ksy_model
from generators.emitters import emit_ksc_python_rw
from generators.abnf_chain import abnf_to_ksy_via_parser
from kernel.certs import Certificate, artifact_hash

TASK_TIME_ENV = "CGB_TASK_TIME"


@dataclasses.dataclass
class RunResult:
    ok: bool
    spec_hash: str = ""
    files: dict = dataclasses.field(default_factory=dict)
    certificate: dict = dataclasses.field(default_factory=dict)
    provenance: dict = dataclasses.field(default_factory=dict)
    out_dir: str = ""
    error: str = ""
    transcript: dict = dataclasses.field(default_factory=dict)
    miss: dict = dataclasses.field(default_factory=dict)


def _emit_stage(entry, language, text, registry):
    kind = entry["emit_entrypoint"]["kind"]
    if kind == "ksc-python-rw":
        assert language == "ksy"
        spec_model = ksy_model.parse_ksy(text)
        return "python-codec", emit_ksc_python_rw(text), spec_model
    if kind == "abnf-to-ksy":
        assert language == "abnf"
        art_dir = pathlib.Path(entry["emit_entrypoint"]["artifact_dir"])
        parser_so = (art_dir / "parser.so").read_bytes()
        return "ksy", abnf_to_ksy_via_parser(parser_so, text), None
    raise ValueError(f"unknown emit entrypoint kind {kind}")


def run_task(registry, spec_path, *, use_corpus=False, write_output=True):
    os.environ[TASK_TIME_ENV] = "1"
    try:
        return _run_task(registry, spec_path, use_corpus=use_corpus,
                         write_output=write_output)
    finally:
        os.environ.pop(TASK_TIME_ENV, None)


def _run_task(registry, spec_path, *, use_corpus, write_output):
    pl = planner_mod.plan(registry, spec_path)
    if isinstance(pl, planner_mod.CoverageMiss):
        registry.log_event("coverage-miss", pl.to_dict())
        return RunResult(ok=False, error=f"coverage miss: {pl.reason}",
                         miss=pl.to_dict())

    language, text, _ = planner_mod.load_spec(spec_path)
    files, spec_model = {}, None
    stage_records = []
    for entry in pl.links:
        out_lang, out, sm = _emit_stage(entry, language, text, registry)
        stage_records.append({
            "generator": entry["generator_hash"], "name": entry["name"],
            "tier": entry["tier"],
            "provenance_depth": entry["provenance"].get("depth", 1)})
        if out_lang == "python-codec":
            files, spec_model = out, sm
            language = out_lang
        else:
            language, text = out_lang, out

    assert files and spec_model is not None, "chain did not terminate in code"

    emission_certs = []
    emit_check_links = [e for e in pl.links if e["tier"] == "emit-check"]
    if emit_check_links:
        corpus_inputs = registry.corpus_inputs(spec_model.atoms) if use_corpus else None
        verdict = kernel.check(
            {"kind": "python-codec", "files": files},
            {"type": "codec-roundtrip", "spec_model": spec_model},
            event_sink=registry.log_event,
            cache_get=registry.cache_get, cache_put=registry.cache_put,
            corpus_inputs=corpus_inputs)
        ok = isinstance(verdict, Certificate)
        for e in emit_check_links:
            registry.bump_emission_record(e["generator_hash"], ok)
        if not ok:
            t = verdict.to_dict()
            caught_by = "corpus-replay" if any(
                c.get("backend") == "corpus-replay" and c["result"] != "pass"
                for c in t["channels"]) else "fresh"
            registry.corpus_add("codec-roundtrip",
                                pl.spec_hash, spec_model.atoms,
                                t.get("failing_input", ""), t)
            registry.log_event("emission-rejection", {
                "spec_hash": pl.spec_hash, "caught_by": caught_by,
                "transcript_excerpt": t["llm_feedback"][:1500]})
            return RunResult(ok=False, spec_hash=pl.spec_hash,
                             error="emission check failed", transcript=t)
        registry.store_certificate(verdict,
                                   emit_check_links[0]["generator_hash"])
        emission_certs.append(verdict.to_dict())

    composed = {
        "kind": "composed-run-certificate",
        "spec_hash": pl.spec_hash,
        "artifact_hash": artifact_hash(files),
        "chain": [e["generator_hash"] for e in pl.links],
        "chain_tiers": [e["tier"] for e in pl.links],
        "emission_checks": [c["cert_id"] for c in emission_certs] or
                           ["not-required: all links universal tier"],
        "created_at": common.now_iso(),
    }
    provenance = {
        "spec_path": str(spec_path), "spec_hash": pl.spec_hash,
        "spec_language": pl.spec_language,
        "emitted_by": stage_records,
        "provenance_depth": max(s["provenance_depth"] for s in stage_records),
        "certificate": common.sha256_json(
            {k: composed[k] for k in composed if k != "created_at"}),
        "trust_tiers": sorted({e["tier"] for e in pl.links}),
    }

    out_dir = ""
    if write_output:
        stem = pathlib.Path(str(spec_path)).stem
        od = common.ARTIFACTS / "out" / f"{stem}-{pl.spec_hash[:8]}"
        od.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (od / name).write_bytes(data)
        (od / "certificate.json").write_text(json.dumps(composed, indent=2))
        (od / "provenance.json").write_text(json.dumps(provenance, indent=2))
        for i, c in enumerate(emission_certs):
            (od / f"emission-cert-{i}.json").write_text(json.dumps(c, indent=2))
        out_dir = str(od)

    return RunResult(ok=True, spec_hash=pl.spec_hash, files=files,
                     certificate=composed, provenance=provenance,
                     out_dir=out_dir)

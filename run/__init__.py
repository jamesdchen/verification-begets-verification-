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

TASK_TIME_ENV = common.TASK_TIME_ENV


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
        grammar_json = (art_dir / "grammar.json").read_bytes()
        return "ksy", abnf_to_ksy_via_parser(parser_so, text, grammar_json), None
    raise ValueError(f"unknown emit entrypoint kind {kind}")


def _abnf_translation_cert(entry, high_text, low_ksy, registry):
    """W1.3b: issue the per-emission `translation-cert` at the abnf->ksy stage
    (the `fixed-deriver` anchor).  Returns None when `entry` is NOT an
    abnf->ksy emit -- the guard that keeps a run WITHOUT an abnf stage
    byte-untouched.  For an abnf stage it lowers the emitted ksy to its python
    codec (the channel-2 subject) and runs kernel.check with the fixed-deriver
    contract, threading the registry cache/event sink exactly like the
    emit-check block below.  DAFNY-FREE: the fixed-deriver anchor's two channels
    (compile-identity + codec-differential) never touch the Dafny codec proof,
    so this runs at task time in the sandbox.  Returns the kernel verdict (a
    Certificate on pass, a transcript on refute); it never raises past
    kernel.check itself."""
    if (entry.get("emit_entrypoint") or {}).get("kind") != "abnf-to-ksy":
        return None
    low_files = emit_ksc_python_rw(low_ksy)
    contract = {"type": "translation-cert", "anchor": "fixed-deriver",
                "high_language": "abnf", "high_spec_text": high_text,
                "low_spec_text": low_ksy, "low_artifact_files": low_files}
    return kernel.check(
        {"kind": "translation", "files": low_files}, contract,
        event_sink=registry.log_event,
        cache_get=registry.cache_get, cache_put=registry.cache_put)


def _record_translation_cert(verdict, entry, stage_rec, registry):
    """Fold the abnf->ksy translation-cert verdict into the stage record and,
    on pass, the run's certificate store -- analogous to the emit-check
    handling.  ADDITIVE and NON-FATAL: a refutation is logged like an emission
    rejection but does NOT abort the run (the mapper cross-check is advisory at
    the stage; the codec emit-check below remains the blocking gate).  Returns
    the certificate dict on pass, else None."""
    ok = isinstance(verdict, Certificate)
    t = verdict.to_dict()
    channels = [(c.get("backend"), c.get("result"))
                for c in t.get("channels", [])]
    stage_rec["translation_cert"] = {
        "ok": ok, "cert_id": t.get("cert_id"), "channels": channels}
    if ok:
        registry.store_certificate(verdict, entry["generator_hash"])
        return t
    registry.log_event("translation-cert-rejection", {
        "generator_hash": entry.get("generator_hash"),
        "high_language": "abnf", "channels": channels,
        "transcript_excerpt": (t.get("llm_feedback") or "")[:1500]})
    return None


def run_task(registry, spec_path, *, use_corpus=False, write_output=True):
    with common.task_time_guard():
        return _run_task(registry, spec_path, use_corpus=use_corpus,
                         write_output=write_output)


def _run_task(registry, spec_path, *, use_corpus, write_output):
    pl = planner_mod.plan(registry, spec_path)
    if isinstance(pl, planner_mod.CoverageMiss):
        registry.log_event("coverage-miss", pl.to_dict())
        return RunResult(ok=False, error=f"coverage miss: {pl.reason}",
                         miss=pl.to_dict())

    language, text, _ = planner_mod.load_spec(spec_path)
    files, spec_model = {}, None
    stage_records = []
    translation_certs = []
    for entry in pl.links:
        out_lang, out, sm = _emit_stage(entry, language, text, registry)
        rec = {
            "generator": entry["generator_hash"], "name": entry["name"],
            "tier": entry["tier"],
            "provenance_depth": entry["provenance"].get("depth", 1)}
        # W1.3b: per-emission translation-cert at the abnf->ksy stage.  Guarded
        # on the emit kind (`text` is still the abnf source, `out` the emitted
        # ksy at this point), so a run without an abnf stage is untouched;
        # additive and non-fatal (logged, never aborts -- the codec emit-check
        # below stays the blocking gate).  DAFNY-FREE: the fixed-deriver anchor.
        tverdict = _abnf_translation_cert(entry, text, out, registry)
        if tverdict is not None:
            tcert = _record_translation_cert(tverdict, entry, rec, registry)
            if tcert is not None:
                translation_certs.append(tcert)
        stage_records.append(rec)
        if out_lang == "python-codec":
            files, spec_model = out, sm
            language = out_lang
        else:
            language, text = out_lang, out

    assert files and spec_model is not None, "chain did not terminate in code"

    emission_certs = list(translation_certs)
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

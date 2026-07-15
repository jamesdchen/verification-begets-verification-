"""Admission of candidate generators (seed-time and build-loop).

Emit-check tier admission = light vetting:
  * spec-only validation already done by the caller,
  * the candidate's emissions for up to K sample specs must pass the kernel's
    dual-checker emission check (corpus screening first when enabled),
  * the MDL gate must pass (or the admission is an expansion event).

Nothing is trusted without a kernel verdict: even the human-seeded Kaitai
entry goes through this path.
"""
from __future__ import annotations

import pathlib
import time

import common
import kernel
from kernel.certs import Certificate
from generators import ksy_model, json_codec
from generators.emitters import (emit_ksc_python_rw, emit_tree_sitter_parser,
                                 emit_tree_sitter_parser_linked)
from generators.abnf_chain import abnf_to_ksy_via_parser, AbnfError
from buildloop import mdl

SAMPLE_K = 3


class AdmissionFailure(Exception):
    def __init__(self, msg, transcript=None):
        super().__init__(msg)
        self.transcript = transcript or {"llm_feedback": msg}


def candidate_entry_from_spec(doc: dict, provenance: dict) -> dict:
    """Build the (unregistered) registry entry for a validated generator spec."""
    if doc["spec_language"] == "ksy":
        return {
            "name": doc["name"], "spec_language": "ksy",
            "output_language": "python-codec",
            "spec_grammar": {"atoms": sorted(set(doc["grammar_atoms"]))},
            "emit_entrypoint": {"kind": "ksc-python-rw"},
            "contract": {"type": "codec-roundtrip"},
            "provenance": provenance,
        }
    if doc["spec_language"] == "json-subset":
        # ts-recursive-codec species: a recursive tree-sitter grammar emitted to
        # a self-contained parser (Impl A), certified against an independent
        # recursive-descent codec (Impl B) by the vpl-differential contract.
        return {
            "name": doc["name"], "spec_language": "json-subset",
            "output_language": "python-codec",
            "spec_grammar": {"atoms": sorted(set(doc["grammar_atoms"]))},
            "emit_entrypoint": {"kind": "ts-recursive-codec", "artifact_dir": None},
            "contract": {"type": "vpl-differential",
                         "depth_bound": json_codec.json_depth_bound(
                             doc["grammar_atoms"])},
            "provenance": provenance,
            "_grammar_js": doc["grammar_js"],
        }
    # abnf chain generator: LLM-authored tree-sitter grammar -> emitted parser
    return {
        "name": doc["name"], "spec_language": "abnf",
        "output_language": "ksy",
        "spec_grammar": {"atoms": sorted(set(doc["grammar_atoms"])),
                         "output": {"language": "ksy",
                                    "atoms": ["magic", "str-fixed"]}},
        "emit_entrypoint": {"kind": "abnf-to-ksy", "artifact_dir": None},
        "contract": {"type": "codec-roundtrip"},
        "provenance": provenance,
        "_grammar_js": doc["grammar_js"],
    }


def _sample_specs(candidate, backlog, k=SAMPLE_K):
    covered = [s for s in backlog
               if s["language"] == candidate["spec_language"]
               and set(s["atoms"]) <= set(candidate["spec_grammar"]["atoms"])]
    covered.sort(key=lambda s: s["path"])
    step = max(1, len(covered) // k)
    return covered[::step][:k]


def _check_sample_json(registry, parser_files, depth_bound):
    """json-subset sample check: certify the emitted recursive parser (Impl A)
    against the independent recursive-descent codec (Impl B) via the kernel's
    vpl-differential contract.  No ksy/Kaitai intermediate, so the ksy-coverage
    check does not apply to this species."""
    t0 = time.monotonic()
    verdict = kernel.check(
        {"kind": "json-codec", "files": parser_files},
        {"type": "vpl-differential", "grammar_js": json_codec.JSON_GRAMMAR_JS,
         "depth_bound": depth_bound, "max_examples": 60},
        event_sink=registry.log_event,
        cache_get=registry.cache_get, cache_put=registry.cache_put)
    registry.counter_add("verifier_seconds", time.monotonic() - t0)
    return verdict


def _check_sample_ksy(registry, ksy_text, use_corpus):
    spec_model = ksy_model.parse_ksy(ksy_text)
    files = emit_ksc_python_rw(ksy_text)
    corpus_inputs = registry.corpus_inputs(spec_model.atoms) if use_corpus else None
    t0 = time.monotonic()
    verdict = kernel.check(
        {"kind": "python-codec", "files": files},
        {"type": "codec-roundtrip", "spec_model": spec_model},
        event_sink=registry.log_event,
        cache_get=registry.cache_get, cache_put=registry.cache_put,
        corpus_inputs=corpus_inputs)
    registry.counter_add("verifier_seconds", time.monotonic() - t0)
    return verdict, spec_model


def admit(registry, candidate, backlog, *, use_corpus=False,
          certificates_extra=()):
    """Run vetting + MDL gate; register on success.  Returns event dict.
    Raises AdmissionFailure with a kernel transcript on rejection."""
    live = registry.live_generators()

    # --- build-time artifacts for abnf chain candidates -------------------
    grammar_js = candidate.pop("_grammar_js", None)
    # fact 6: the LLM-authored payload (a tree-sitter grammar_js, up to 20 KB)
    # rides only the PRE-admission candidate dict; register() never stores it, so
    # a persisted generator would price its authored bytes at ~0.  Record the
    # authored LENGTH onto the persisted emit_entrypoint so `dl.generator_dl`
    # (which ledger_dl sums over persisted generators) can pay for it.
    candidate["emit_entrypoint"]["authored_bytes"] = len(grammar_js or "")
    parser_files = None
    if candidate["spec_language"] == "abnf":
        parser_files = emit_tree_sitter_parser(grammar_js)  # raises EmitError
    elif candidate["spec_language"] == "json-subset":
        # Recursive tree-sitter grammar with the runtime STATICALLY LINKED so
        # the parser is drivable via the C API (no python tree_sitter binding
        # here).  This species has no ksy intermediate -> the ksy-coverage check
        # below is skipped for it.
        parser_files = emit_tree_sitter_parser_linked(grammar_js)  # raises EmitError

    samples = _sample_specs(candidate, backlog)
    if not samples:
        raise AdmissionFailure(
            "candidate grammar covers zero backlog specs; propose atoms that "
            "cover at least one outstanding coverage miss")

    certs = []
    for s in samples:
        if candidate["spec_language"] == "json-subset":
            # json-subset: the artifact is the emitted recursive parser; certify
            # it with the vpl-differential contract.  ksy-coverage is SKIPPED.
            verdict = _check_sample_json(
                registry, parser_files, candidate["contract"]["depth_bound"])
            if not isinstance(verdict, Certificate):
                t = verdict.to_dict()
                registry.log_event("admission-rejection", {
                    "candidate": candidate["name"], "sample": s["path"],
                    "caught_by": "vpl-differential", "verdict": t["verdict"],
                    "transcript_excerpt": t["llm_feedback"][:1200]})
                raise AdmissionFailure(
                    f"kernel rejected the recursive codec for sample {s['path']}",
                    transcript=t)
            certs.append(verdict)
            continue
        text = pathlib.Path(s["path"]).read_text()
        if candidate["spec_language"] == "abnf":
            try:
                text = abnf_to_ksy_via_parser(parser_files["parser.so"], text,
                                              parser_files["grammar.json"])
            except (AbnfError, Exception) as e:
                registry.log_event("admission-rejection", {
                    "candidate": candidate["name"], "sample": s["path"],
                    "caught_by": "chain-stage-1", "reason": str(e)[:400]})
                raise AdmissionFailure(
                    f"chain stage 1 failed on sample {s['path']}: {e}. "
                    "The emitted tree-sitter parser must produce named nodes "
                    "'literal', 'repetition', 'core_rule' matching the ABNF "
                    "elements in order.")
            ksy_atoms = ksy_model.atoms_of_ksy(text)
            if not any(g["output_language"] == "python-codec"
                       and g["spec_language"] == "ksy"
                       and set(ksy_atoms) <= set(g["spec_grammar"]["atoms"])
                       for g in live):
                raise AdmissionFailure(
                    f"no live ksy generator covers the chain's intermediate "
                    f"spec atoms {sorted(ksy_atoms)}; a ksy generator "
                    "covering magic+str-fixed must be admitted first")
        verdict, _sm = _check_sample_ksy(registry, text, use_corpus)
        if not isinstance(verdict, Certificate):
            t = verdict.to_dict()
            caught_by = "corpus-replay" if any(
                c.get("backend") == "corpus-replay" and c["result"] != "pass"
                for c in t["channels"]) else "fresh"
            registry.log_event("admission-rejection", {
                "candidate": candidate["name"], "sample": s["path"],
                "caught_by": caught_by, "verdict": t["verdict"],
                "transcript_excerpt": t["llm_feedback"][:1200]})
            raise AdmissionFailure(
                f"kernel rejected emission for sample {s['path']}",
                transcript=t)
        certs.append(verdict)

    # --- MDL gate ---------------------------------------------------------
    decision = mdl.admission_decision(live, candidate, backlog)
    if not decision["admit"]:
        registry.log_event("admission-rejection", {
            "candidate": candidate["name"], "caught_by": "mdl-gate",
            "decision": decision})
        raise AdmissionFailure(
            f"MDL gate: admitting would raise total description length "
            f"({decision['dl_before']} -> {decision['dl_after']}) without new "
            "coverage. Propose a broader grammar that consolidates existing "
            "generators, or one that covers currently unreachable specs.")

    ghash = registry.register(
        tier="emit-check",
        name=candidate["name"],
        spec_language=candidate["spec_language"],
        output_language=candidate["output_language"],
        spec_grammar=candidate["spec_grammar"],
        emit_entrypoint=candidate["emit_entrypoint"],
        contract=candidate["contract"],
        provenance=candidate["provenance"],
        certificates=list(certs) + list(certificates_extra),
        description_length=mdl.generator_dl(candidate))

    if parser_files is not None:
        art_dir = common.ARTIFACTS / "generators" / ghash
        art_dir.mkdir(parents=True, exist_ok=True)
        for name, data in parser_files.items():
            (art_dir / name).write_bytes(data)
        (art_dir / "grammar.js").write_text(grammar_js)
        entry = registry.get(ghash)
        entry["emit_entrypoint"]["artifact_dir"] = str(art_dir)
        registry.db.execute(
            "UPDATE generators SET emit_entrypoint=? WHERE generator_hash=?",
            (common.canonical_json(entry["emit_entrypoint"]), ghash))
        registry.db.commit()

    # --- subsumption ------------------------------------------------------
    new_entry = registry.get(ghash)
    retired = []
    for g in mdl.find_subsumed(registry.live_generators(), new_entry):
        registry.retire(g["generator_hash"], ghash)
        retired.append(g["name"])
        registry.log_event("retirement", {
            "retired": g["name"], "retired_hash": g["generator_hash"],
            "subsumed_by": ghash})

    event = {"generator": candidate["name"], "generator_hash": ghash,
             "tier": "emit-check", "samples_checked": len(samples),
             "mdl": decision, "retired": retired,
             "expansion": decision["expansion"]}
    registry.log_event("expansion" if decision["expansion"] else "admission",
                       event)
    return event

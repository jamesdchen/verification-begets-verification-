"""Promotion: attempt to upgrade an emit-check generator to the universal
tier.

Universal verdicts also obey the dual-checker rule:
  channel 1: Dafny proof over the generator itself -- the static-offset
             implementation model is proven correct for ALL specs in the
             generator's grammar (generators/codec_model.dfy + the
             UNIVERSAL_FIXED_UINT obligation);
  channel 2: Hypothesis spec-level fuzz -- randomly sampled specs from the
             grammar are emitted through the REAL pipeline and their real
             codecs are property-tested in the sandbox.

On success the tier flips, emission checks stop, and the planner's
preference flips to this generator.
"""
from __future__ import annotations

import random
import time

import kernel
from kernel.certs import Certificate
from generators import ksy_model
from generators.emitters import emit_ksc_python_rw

SPEC_FUZZ_N = 8


def _random_fixed_uint_ksy(rng, idx, atoms):
    endian = "le" if "endian:le" in atoms else "be"
    widths = [int(a.split(":")[1]) for a in atoms if a.startswith("uint:")]
    n = rng.randint(1, 6)
    lines = ["meta:", f"  id: promo_fuzz_{idx}", f"  endian: {endian}", "seq:"]
    for i in range(n):
        w = rng.choice(widths)
        lines += [f"  - id: f{i}", f"    type: u{w}"]
    return "\n".join(lines) + "\n"


def promote(registry, generator_hash: str, seed: int = 7):
    entry = registry.get(generator_hash)
    if entry["tier"] == "universal":
        return {"status": "already-universal"}
    atoms = frozenset(entry["spec_grammar"]["atoms"])

    rng = random.Random(seed)
    sampled = []
    for i in range(SPEC_FUZZ_N):
        text = _random_fixed_uint_ksy(rng, i, atoms)
        sm = ksy_model.parse_ksy(text)
        files = emit_ksc_python_rw(text)
        sampled.append((sm, files))

    t0 = time.monotonic()
    verdict = kernel.check(
        {"kind": "generator", "files": {
            "generator.json": __import__("common").canonical_json(
                {"spec_grammar": entry["spec_grammar"],
                 "emit_entrypoint": entry["emit_entrypoint"]}).encode()}},
        {"type": "universal-fixed-uint", "grammar_atoms": atoms,
         "sampled_emissions": sampled},
        event_sink=registry.log_event,
        cache_get=registry.cache_get, cache_put=registry.cache_put)
    registry.counter_add("verifier_seconds", time.monotonic() - t0)

    if not isinstance(verdict, Certificate):
        t = verdict.to_dict()
        registry.log_event("promotion-rejected", {
            "generator": entry["name"], "verdict": t["verdict"],
            "transcript_excerpt": t["llm_feedback"][:1200]})
        return {"status": "rejected", "transcript": t}

    registry.store_certificate(verdict, generator_hash)
    registry.set_tier(generator_hash, "universal")
    registry.log_event("promotion", {
        "generator": entry["name"], "generator_hash": generator_hash,
        "cert_id": verdict.cert_id,
        "emission_record_at_promotion": {
            "checked": entry["emission_checked"],
            "failures": entry["emission_failures"]},
        "channels": [c["backend"] for c in verdict.channels]})
    return {"status": "promoted", "cert_id": verdict.cert_id,
            "channels": verdict.channels}

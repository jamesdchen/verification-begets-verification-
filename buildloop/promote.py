"""Promotion: attempt to upgrade a generator to the universal tier.

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

TIER ROUTING (W5.1 -- verified hazard).  The promotion DECISION is the
certificate's own tier, never the mere existence of a certificate.  A
certificate is ALWAYS stored as evidence, but the generator flips to the
`universal` tier IFF the certificate literally claims `tier == "universal"`
(`_should_set_universal`).  Only `universal` stops per-emission checks and
flips the planner's preference (interface-freeze item 12).  A non-universal
outcome (e.g. a bounded `complete-to-size(N)` adjudication) is an explicit
promotion REFUSAL that RETAINS the generator's emit-check duty; its
certificate is kept as evidence only.  `promote()` therefore must never
`set_tier` from a non-universal-tier certificate.
"""
from __future__ import annotations

import random
import time

import kernel
from kernel.certs import Certificate
from generators import ksy_model
from generators.emitters import emit_ksc_python_rw

SPEC_FUZZ_N = 8


def _should_set_universal(cert) -> bool:
    """The promotion DECISION, isolated and pure so it is unit-testable
    without Dafny/LLM/registry.

    Returns True IFF the certificate positively claims the `universal` tier.
    Every other tier -- including the empty/default tier and the honest bounded
    `complete-to-size(N)` refusal -- returns False, and callers must leave the
    generator on its existing (emit-check-bearing) tier.
    """
    return getattr(cert, "tier", "") == "universal"


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

    # Dispatch on the registry entry's kind (W2.1 added the column:
    # 'emitter' | 'translator' | 'pass').
    kind = entry.get("kind", "emitter")
    if kind == "emitter":
        return _promote_emitter(registry, generator_hash, entry, seed)
    if kind == "translator":
        # The `universal-translation` kernel contract (W5.1 channel design) is
        # not landed yet.  Guard this branch so it is REACHABLE and never
        # crashes; the kernel owner wires the real check + adjudication in when
        # the contract lands.  Nothing is stored and the tier is untouched.
        return {"status": "unsupported-pending-kernel", "kind": kind,
                "contract": "universal-translation"}
    # 'pass' generators are planner-invisible and never promoted; any other
    # kind is likewise not a promotion subject.
    return {"status": "unsupported-kind", "kind": kind}


def _promote_emitter(registry, generator_hash: str, entry: dict, seed: int):
    """The emitter promotion path: the `universal-fixed-uint` contract."""
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

    # The certificate is ALWAYS kept as evidence -- even a bounded refusal is a
    # real, hash-bound adjudication worth retaining.
    registry.store_certificate(verdict, generator_hash)

    # TIER ROUTING: flip to `universal` IFF the certificate claims that tier.
    # A non-universal certificate is an explicit REFUSAL: the tier is left
    # untouched, so per-emission checks continue.
    if not _should_set_universal(verdict):
        registry.log_event("promotion-refused-bounded", {
            "generator": entry["name"], "generator_hash": generator_hash,
            "cert_id": verdict.cert_id, "cert_tier": verdict.tier,
            "channels": [c["backend"] for c in verdict.channels]})
        return {"status": "refused-bounded", "cert_id": verdict.cert_id,
                "tier": verdict.tier, "channels": verdict.channels}

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

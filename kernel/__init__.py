"""The kernel: the only component trusted by fiat.

check(artifact, contract) -> Certificate | ErrorTranscript

It is deliberately small: it derives obligations, dispatches to backends,
enforces the DUAL-CHECKER RULE, and never trusts a single checker.  Every
"pass" certificate names at least two independent agreeing evidence
channels.  Channel disagreement is never discarded: it is logged as a
first-class event through the injected event sink and yields NO certificate.

The kernel is swap-ready: it holds no state; caching and event logging are
injected by the caller (library/registry).
"""
from __future__ import annotations

from typing import Callable, Optional

import common
from kernel.certs import Certificate, ErrorTranscript, artifact_hash
from kernel.backends import HypothesisBackend, DafnyBackend, SmtBackend

_hyp = HypothesisBackend()
_daf = DafnyBackend()
_smt = SmtBackend()


def _transcript(verdict, subject, contract_hash, channels):
    failing = next((c for c in channels if c["result"] != "pass"), {})
    t = failing.get("transcript", {}) or {}
    fb_lines = [f"Kernel verdict: {verdict}."]
    for c in channels:
        fb_lines.append(f"- channel {c['backend']}: {c['result']} -- "
                        f"{str(c.get('detail'))[:600]}")
    if t.get("error"):
        fb_lines.append(f"Failing behavior: {t['error']}")
    if t.get("failing_input"):
        fb_lines.append(f"Failing input (hex): {t['failing_input']}")
    return ErrorTranscript(
        verdict=verdict, subject_hash=subject, contract_hash=contract_hash,
        channels=channels,
        failing_input=t.get("failing_input", ""),
        observed=str(t.get("observed", t.get("error", "")))[:1000],
        expected=str(t.get("expected", "contract satisfied"))[:1000],
        llm_feedback="\n".join(fb_lines))


def check(artifact: dict, contract: dict, *,
          event_sink: Optional[Callable] = None,
          cache_get: Optional[Callable] = None,
          cache_put: Optional[Callable] = None,
          corpus_inputs: Optional[list] = None):
    """Adjudicate one artifact against one contract.

    artifact: {"kind": ..., "files": {name: bytes}}  (files may be empty for
              pure-logic contracts)
    contract: {"type": "codec-roundtrip", "spec_model": SpecModel}
            | {"type": "universal-fixed-uint", "grammar_atoms": frozenset,
               "sampled_emissions": [(SpecModel, files), ...]}
            | {"type": "smt-obligation", "smtlib": str, "description": str}
    """
    subject = artifact_hash(artifact.get("files", {})) if artifact.get("files") \
        else common.sha256_bytes(contract.get("smtlib", "").encode())
    cdesc = {"type": contract["type"]}
    if contract["type"] in ("codec-roundtrip", "codec-differential"):
        cdesc["spec_hash"] = common.sha256_bytes(
            contract["spec_model"].source.encode())
    elif contract["type"] == "universal-fixed-uint":
        cdesc["grammar_atoms"] = sorted(contract["grammar_atoms"])
    elif contract["type"] == "smt-obligation":
        cdesc["smtlib_hash"] = common.sha256_bytes(contract["smtlib"].encode())
    contract_hash = common.sha256_json(cdesc)

    cache_key = f"{subject}:{contract_hash}"
    if cache_get:
        hit = cache_get(cache_key)
        if hit is not None:
            return hit

    kind, channels = _dispatch(artifact, contract, corpus_inputs)

    passes = [c for c in channels if c["result"] == "pass"]
    fails = [c for c in channels if c["result"] in ("fail", "unknown", "error")]

    if len(passes) >= 2 and not fails:
        out = Certificate.make(kind, subject, contract_hash, channels)
    else:
        # Classify the non-admission.  A behavioral-witness channel that
        # observed a concrete counterexample on the real artifact is
        # authoritative: the artifact is broken -> "fail" (not a disagreement,
        # even if a proof channel about the *contract model* passed).  A
        # genuine "disagreement" -- reserved for human eyes -- is when
        # channels adjudicating the SAME obligation conflict (Z3 vs CVC5), or
        # when testing found no counterexample yet the proof failed/timed out
        # (edge of decidability).
        witness_fail = any(c["result"] == "fail"
                           and c.get("role") in ("behavioral-witness",
                                                 "cross-impl-differential")
                           for c in fails)
        if witness_fail:
            verdict = "fail"
        else:
            verdict = "disagreement" if passes and fails else "fail"
        out = _transcript(verdict, subject, contract_hash, channels)
        if verdict == "disagreement" and event_sink:
            event_sink("dual-checker-disagreement", {
                "subject_hash": subject, "contract_hash": contract_hash,
                "contract": cdesc, "channels": channels})
    if cache_put:
        cache_put(cache_key, out)
    return out


def _dispatch(artifact, contract, corpus_inputs):
    ctype = contract["type"]
    if ctype == "codec-roundtrip":
        spec = contract["spec_model"]
        channels = []
        # corpus screening happens BEFORE fresh adversarial generation
        if corpus_inputs:
            rep = _hyp.replay_corpus(artifact["files"], spec, corpus_inputs)
            channels.append(rep)
            if rep["result"] != "pass":
                # caught by replay -- skip the expensive fresh channels but
                # still record which stage caught it
                return "emission-check", channels
        channels.append(_hyp.check_codec(
            artifact["files"], spec,
            max_examples=contract.get("max_examples", 100)))
        channels.append(_daf.check_codec_spec(spec))
        # corpus replay is screening, not an independent evidence channel;
        # drop it from the agreement count when it passed
        channels = [c for c in channels if c["backend"] != "corpus-replay"] \
            if len(channels) > 2 else channels
        return "emission-check", channels
    if ctype == "codec-differential":
        # Path (i): two independent evidence channels --
        #   channel 1: Kaitai codec vs. an independent reference codec
        #              (behavioral cross-implementation differential),
        #   channel 2: Dafny proof of the spec-level contract (logical).
        # The two channels share no implementation, so agreement is genuine
        # N-version evidence, not a single artifact checked twice.
        spec = contract["spec_model"]
        channels = [
            _hyp.check_differential(artifact["files"], spec,
                                    max_examples=contract.get("max_examples", 100),
                                    ref_fields=contract.get("ref_fields")),
            _daf.check_codec_spec(spec),
        ]
        return "differential-admission", channels
    if ctype == "universal-fixed-uint":
        channels = [_daf.check_universal(contract["grammar_atoms"])]
        # channel 2: independent evidence -- Hypothesis over *sampled specs*
        # of the grammar, against real emissions
        sampled = contract.get("sampled_emissions", [])
        if not sampled:
            channels.append({"backend": "hypothesis", "result": "fail",
                             "detail": "no sampled emissions supplied for the "
                                       "spec-fuzz channel"})
        else:
            results = [_hyp.check_codec(files, sm, max_examples=50)
                       for sm, files in sampled]
            bad = [r for r in results if r["result"] != "pass"]
            channels.append({
                "backend": "hypothesis", "result": "fail" if bad else "pass",
                "detail": f"spec-level fuzz over {len(sampled)} sampled specs"
                          + ("" if not bad else f"; first failure: {bad[0]['detail'][:400]}"),
                **({"transcript": bad[0].get("transcript", {})} if bad else {})})
        return "promotion", channels
    if ctype == "smt-obligation":
        z = _smt.run_z3(contract["smtlib"])
        c = _smt.run_cvc5(contract["smtlib"])
        return "admission", [z, c]
    raise ValueError(f"unknown contract type {ctype}")

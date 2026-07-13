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
    elif contract["type"] in ("tool-differential", "tool-lift"):
        cdesc["schema_hash"] = common.sha256_bytes(contract["schema_text"].encode())
        if contract["type"] == "tool-lift":
            cdesc["incumbent_hash"] = common.sha256_json(sorted(
                common.sha256_bytes(v if isinstance(v, bytes) else v.encode())
                for v in contract["incumbent_files"].values()))
    elif contract["type"] in ("constraint-cert", "protocol-cert",
                              "service-conformance"):
        cdesc["spec_hash"] = common.sha256_bytes(contract["spec_text"].encode())
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
        # "disagreement" is reserved for channels adjudicating the SAME
        # obligation that conflict -- the two SMT solvers on one proof
        # (proof_split), or a proof that testing contradicts.  Channels that
        # check *different* things (a proof failing while a behavioral channel
        # passes) are not a disagreement -- that is a clean, localized fail.
        proof = [c for c in channels if c.get("role") == "smt-proof"]
        proof_split = (any(c["result"] == "pass" for c in proof)
                       and any(c["result"] != "pass" for c in proof))
        proof_bad = any(c["result"] != "pass" for c in proof)
        witness_fail = any(c["result"] != "pass"
                           and c.get("role") in ("behavioral-witness",
                                                 "cross-impl-differential")
                           for c in channels)
        if proof_split:
            verdict = "disagreement"
        elif witness_fail or proof_bad:
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
    if ctype == "tool-differential":
        # Tool contract (i): two independent validators --
        #   channel 1: the Pydantic validator satisfies round-trip + rejection,
        #   channel 2: Pydantic and the jsonschema-library reference agree on
        #              accept/reject over generated + mutated instances.
        # Independence is free here: two separately-authored validator libs.
        schema = contract["schema_text"]
        mx = contract.get("max_examples", 100)
        channels = [
            _hyp.check_tool(artifact["files"], schema, max_examples=mx),
            _hyp.check_tool_differential(artifact["files"], schema, max_examples=mx),
        ]
        return "tool-admission", channels
    if ctype == "protocol-cert":
        # Sequencing safety -- the layer per-message validation cannot reach.
        # Three channels: PROVE (bounded model checking, Z3 AND CVC5) that no
        # invariant-violating state is reachable via legal transitions within
        # the bound (complete when the control graph is acyclic); plus a
        # validator-conformance differential vs an independent reference
        # simulator on solver-generated legal + illegal traces.
        from generators import protocol_model as _pm, protocol_gen as _pg
        m = _pm.parse_protocol_spec(contract["spec_text"])
        K, _complete = m.acyclic_bound()
        obl = _pg.bmc_smtlib(m, K)
        z = _smt.run_z3(obl); z["backend"] = "z3-safety"; z["role"] = "smt-proof"
        c = _smt.run_cvc5(obl); c["backend"] = "cvc5-safety"; c["role"] = "smt-proof"
        conf = _hyp.check_protocol_conformance(artifact["files"], m, K)
        return "protocol-admission", [z, c, conf]
    if ctype == "constraint-cert":
        # The hard case: cross-field semantic constraints JSON Schema cannot
        # express.  Two kinds of evidence, three channels:
        #   channels 1&2: PROVE  constraints => invariant  with Z3 AND CVC5
        #                 independently (the dual-checker on a load-bearing,
        #                 decidable QF_LIA theorem -- not an engineered split);
        #   channel 3:    the emitted validator matches the solver's verdict on
        #                 Z3-generated boundary inputs (solver-as-adversary),
        #                 plus non-vacuity (a valid input must exist).
        from generators import constraint_model as _cm, constraint_gen as _cg
        m = _cm.parse_constraint_spec(contract["spec_text"])
        if m.invariant is None:
            raise ValueError("constraint-cert requires an invariant to prove")
        obl = _cg.obligation_smt(m)
        z = _smt.run_z3(obl); z["backend"] = "z3-invariant"; z["role"] = "smt-proof"
        c = _smt.run_cvc5(obl); c["backend"] = "cvc5-invariant"; c["role"] = "smt-proof"
        boundary = _hyp.check_constraint_boundary(
            artifact["files"], _cg.boundary_inputs(m))
        return "constraint-admission", [z, c, boundary]
    if ctype == "tool-lift":
        # Schema-lift: certify that an inferred JSON Schema faithfully captures
        # an INCUMBENT validator's contract. Two independent channels --
        #   channel 1: the inferred validator is internally sound (round-trip
        #              + rejection),
        #   channel 2: it agrees with the incumbent (the ground-truth anchor)
        #              on accept/reject over generated + mutated instances.
        schema = contract["schema_text"]
        mx = contract.get("max_examples", 100)
        channels = [
            _hyp.check_tool(artifact["files"], schema, max_examples=mx),
            _hyp.check_incumbent_differential(
                artifact["files"], schema, contract["incumbent_files"],
                max_examples=mx),
        ]
        return "tool-lift-admission", channels
    if ctype == "service-conformance":
        # Composition: bind the four certified layers (tool schema, per-call
        # constraint, protocol sequencing, guard/update) into ONE dispatcher and
        # check the dispatcher faithfully ANDs them.  Two independent channels:
        #   channel 1: the dispatcher matches an INDEPENDENT jsonschema-based
        #              reference service on layer-exercising call sequences
        #              (a dropped/misordered layer is caught), and
        #   channel 2: non-vacuity -- the dispatcher accepts a full legal run.
        # This does not re-prove the layers (each already has its own cert); it
        # certifies that the *composition* preserves them.
        from generators import service_model as _svm
        m = _svm.parse_service_spec(contract["spec_text"])
        channels = [
            _hyp.check_service_conformance(artifact["files"], m),
            _hyp.check_service_liveness(artifact["files"], m),
        ]
        return "service-admission", channels
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

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


def _subject_and_cdesc(artifact, contract):
    """The content-addressed identity of (artifact, contract): the subject hash
    and the contract descriptor.  Extracted so the cache key can be computed
    without running a check -- lets an orchestrator look up the cache on its own
    thread and run only the misses (the registry's SQLite handle is single-
    threaded, so worker threads must not touch it)."""
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
    elif contract["type"] == "intent-scenarios":
        cdesc["spec_hash"] = common.sha256_bytes(contract["spec_text"].encode())
        cdesc["scenarios_hash"] = common.sha256_bytes(
            contract["scenarios_text"].encode())
    elif contract["type"] in ("smt-obligation", "reading-consistency"):
        cdesc["smtlib_hash"] = common.sha256_bytes(contract["smtlib"].encode())
    return subject, cdesc


def cache_key(artifact: dict, contract: dict) -> str:
    """Public: the cache key for (artifact, contract), identical to the key
    check() uses internally."""
    subject, cdesc = _subject_and_cdesc(artifact, contract)
    return f"{subject}:{common.sha256_json(cdesc)}"


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
    subject, cdesc = _subject_and_cdesc(artifact, contract)
    contract_hash = common.sha256_json(cdesc)

    ckey = f"{subject}:{contract_hash}"
    if cache_get:
        hit = cache_get(ckey)
        if hit is not None:
            return hit

    kind, channels = _dispatch(artifact, contract, corpus_inputs)
    out = adjudicate(kind, subject, contract_hash, cdesc, channels,
                     event_sink=event_sink)
    if cache_put:
        cache_put(ckey, out)
    return out


def adjudicate(kind, subject, contract_hash, cdesc, channels, *,
               event_sink=None):
    """Apply the DUAL-CHECKER RULE to a contract's collected channels and issue
    the verdict.  This is the kernel's adjudication, factored out of check() so
    an orchestrator can produce the channels however it likes (e.g. one process
    per channel) and still get an identical verdict -- the classification is a
    pure function of the channel list."""
    passes = [c for c in channels if c["result"] == "pass"]
    fails = [c for c in channels if c["result"] in ("fail", "unknown", "error")]

    if len(passes) >= 2 and not fails:
        return Certificate.make(kind, subject, contract_hash, channels)
    # Classify the non-admission.  A behavioral-witness channel that observed a
    # concrete counterexample on the real artifact is authoritative: the
    # artifact is broken -> "fail" (not a disagreement, even if a proof channel
    # about the *contract model* passed).  A genuine "disagreement" -- reserved
    # for human eyes -- is when channels adjudicating the SAME obligation
    # conflict (Z3 vs CVC5), or when testing found no counterexample yet the
    # proof failed/timed out (edge of decidability).
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
    return out


def channel_specs(artifact, contract):
    """Decompose a contract into its independent, picklable channel tasks so an
    orchestrator can run EACH channel in its own process -- overlapping even a
    single contract's channels and isolating z3 per process (no lock needed).
    Returns (kind, [spec, ...]); each spec is consumed by run_channel().  Covers
    the service-composition contracts; other contracts use check()/_dispatch."""
    ctype = contract["type"]
    files = artifact.get("files", {})
    if ctype == "tool-differential":
        s = contract["schema_text"]; mx = contract.get("max_examples", 100)
        return "tool-admission", [("tool_self", files, s, mx),
                                  ("tool_diff", files, s, mx)]
    if ctype == "constraint-cert":
        from generators import constraint_model as _cm, constraint_gen as _cg
        m = _cm.parse_constraint_spec(contract["spec_text"])
        if m.invariant is None:
            raise ValueError("constraint-cert requires an invariant to prove")
        obl = _cg.obligation_smt(m)
        return "constraint-admission", [
            ("smt", obl, "z3", "z3-invariant"),
            ("smt", obl, "cvc5", "cvc5-invariant"),
            ("constraint_boundary", files, contract["spec_text"])]
    if ctype == "protocol-cert":
        from generators import protocol_model as _pm, protocol_gen as _pg
        m = _pm.parse_protocol_spec(contract["spec_text"])
        K, _ = m.acyclic_bound()
        obl = _pg.bmc_smtlib(m, K)
        return "protocol-admission", [
            ("smt", obl, "z3", "z3-safety"),
            ("smt", obl, "cvc5", "cvc5-safety"),
            ("protocol_conf", files, contract["spec_text"])]
    if ctype == "service-conformance":
        return "service-admission", [("svc_conf", files, contract["spec_text"]),
                                     ("svc_live", files, contract["spec_text"])]
    if ctype == "intent-scenarios":
        st, sc = contract["spec_text"], contract["scenarios_text"]
        return "intent-admission", [("intent_disp", files, sc),
                                    ("intent_ref", files, st, sc)]
    raise ValueError(f"channel_specs: unsupported contract {ctype}")


def run_channel(spec):
    """Execute ONE channel spec (from channel_specs) and return its channel dict.
    Top-level with primitive-only args so it pickles to a worker process; each
    worker re-derives any model from the spec text, keeping z3 state per-process.
    Reproduces the exact channel (backend name, role) that _dispatch produces, so
    adjudicate() yields an identical verdict."""
    kind = spec[0]
    if kind == "tool_self":
        return _hyp.check_tool(spec[1], spec[2], max_examples=spec[3])
    if kind == "tool_diff":
        return _hyp.check_tool_differential(spec[1], spec[2], max_examples=spec[3])
    if kind == "smt":
        _, obl, solver, backend = spec
        d = _smt.run_z3(obl) if solver == "z3" else _smt.run_cvc5(obl)
        d["backend"] = backend; d["role"] = "smt-proof"
        return d
    if kind == "constraint_boundary":
        from generators import constraint_model as _cm, constraint_gen as _cg
        m = _cm.parse_constraint_spec(spec[2])
        return _hyp.check_constraint_boundary(spec[1], _cg.boundary_inputs(m))
    if kind == "protocol_conf":
        from generators import protocol_model as _pm
        m = _pm.parse_protocol_spec(spec[2])
        K, _ = m.acyclic_bound()
        return _hyp.check_protocol_conformance(spec[1], m, K)
    if kind == "svc_conf":
        from generators import service_model as _svm
        return _hyp.check_service_conformance(spec[1], _svm.parse_service_spec(spec[2]))
    if kind == "svc_live":
        from generators import service_model as _svm
        return _hyp.check_service_liveness(spec[1], _svm.parse_service_spec(spec[2]))
    if kind == "intent_disp":
        import json as _json
        return _hyp.check_intent_dispatcher(
            spec[1], _json.loads(spec[2])["scenarios"])
    if kind == "intent_ref":
        import json as _json
        from generators import service_model as _svm
        return _hyp.check_intent_reference(
            spec[1], _svm.parse_service_spec(spec[2]),
            _json.loads(spec[3])["scenarios"])
    raise ValueError(f"run_channel: unknown spec kind {kind!r}")


def _par(*thunks):
    """Run independent, z3-FREE evidence channels concurrently, returning results
    in the given order.  Restricted to contracts whose channels are pure sandbox
    / Dafny-subprocess work: those are process-isolated and thread-safe, unlike
    the z3/cvc5 bindings (whose process-global context is not).  The dual-checker
    adjudication that follows is unchanged -- only channel *production* overlaps,
    and the returned order is fixed, so certificates stay deterministic.

    An orchestrator that already fans *layers* out across processes sets
    CGB_KERNEL_SERIAL=1 so channels run sequentially in each worker -- otherwise
    process x thread nesting oversubscribes the cores and runs slower.  On the
    standalone single-contract path the variable is unset and channels overlap."""
    import os
    if os.environ.get("CGB_KERNEL_SERIAL") == "1" or len(thunks) <= 1:
        return [t() for t in thunks]
    import concurrent.futures as _cf
    with _cf.ThreadPoolExecutor(max_workers=len(thunks)) as ex:
        return [f.result() for f in [ex.submit(t) for t in thunks]]


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
        # the behavioral (sandbox) and Dafny (subprocess) channels are z3-free
        # and independent -> run them concurrently
        channels.extend(_par(
            lambda: _hyp.check_codec(
                artifact["files"], spec,
                max_examples=contract.get("max_examples", 100)),
            lambda: _daf.check_codec_spec(spec)))
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
        channels = _par(
            lambda: _hyp.check_tool(artifact["files"], schema, max_examples=mx),
            lambda: _hyp.check_tool_differential(
                artifact["files"], schema, max_examples=mx))
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
        channels = _par(
            lambda: _hyp.check_tool(artifact["files"], schema, max_examples=mx),
            lambda: _hyp.check_incumbent_differential(
                artifact["files"], schema, contract["incumbent_files"],
                max_examples=mx))
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
    if ctype == "intent-scenarios":
        # The language->spec gap, dual-checked one rung up the tower.  The
        # scenarios (accept/reject expectations over concrete call traces) were
        # authored INDEPENDENTLY of the spec's semantics -- the scenario author
        # saw the request and the tool interface only, never the guards/updates/
        # constraints/safety.  Two channels replay them:
        #   channel 1: the certified dispatcher,
        #   channel 2: the independent reference interpreter of the spec.
        # Agreement means two independent linguistic derivations of the request
        # (spec semantics vs. expected behaviours) converge -- N-version
        # evidence at the intent level.  This is NOT kernel-grade proof of
        # intent fidelity (nothing can be); see TRUST.md.
        import json as _json
        from generators import service_model as _svm
        m = _svm.parse_service_spec(contract["spec_text"])
        scenarios = _json.loads(contract["scenarios_text"])["scenarios"]
        channels = [
            _hyp.check_intent_dispatcher(artifact["files"], scenarios),
            _hyp.check_intent_reference(artifact["files"], m, scenarios),
        ]
        return "intent-admission", channels
    if ctype == "codec-differential":
        # Path (i): two independent evidence channels --
        #   channel 1: Kaitai codec vs. an independent reference codec
        #              (behavioral cross-implementation differential),
        #   channel 2: Dafny proof of the spec-level contract (logical).
        # The two channels share no implementation, so agreement is genuine
        # N-version evidence, not a single artifact checked twice.
        spec = contract["spec_model"]
        channels = _par(
            lambda: _hyp.check_differential(
                artifact["files"], spec,
                max_examples=contract.get("max_examples", 100),
                ref_fields=contract.get("ref_fields")),
            lambda: _daf.check_codec_spec(spec))
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
    if ctype == "reading-consistency":
        # The demand set of a Reading must be jointly satisfiable: a world
        # obeying every quoted demand exists.  unsat = the request's demands
        # contradict each other; refuse before any code exists.  Dual-checked
        # (same obligation, both solvers, expect sat).
        z = _smt.run_z3(contract["smtlib"], expect="sat")
        z["backend"] = "z3-consistency"; z["role"] = "smt-proof"
        c = _smt.run_cvc5(contract["smtlib"], expect="sat")
        c["backend"] = "cvc5-consistency"; c["role"] = "smt-proof"
        return "reading-admission", [z, c]
    raise ValueError(f"unknown contract type {ctype}")

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
from kernel.certs import (Certificate, ErrorTranscript, artifact_hash,
                          CERTS_VERSION, norm_cert_cdesc)
from kernel.backends import HypothesisBackend, DafnyBackend, SmtBackend

# Contract types whose verdict depends on the fuzzing budget: max_examples must
# enter the contract descriptor, or a cheap (few-example) verdict is silently
# served for an expensive (many-example) request.
_MAX_EXAMPLES_TYPES = frozenset({
    "codec-roundtrip", "codec-differential", "tool-differential", "tool-lift",
    "vpl-differential"})

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


def _tier_classify(spec_text):
    """P5.1: build a protocol spec's CONTROL-SKELETON DFA and run the dual-channel
    star-free classifier (generators.monoid -- pure, z3-free, so it runs
    in-process; no sandbox, no solver).  TOTAL by construction: a parse failure, a
    pushdown/nested protocol (no plain DFA skeleton), and the monoid feasibility
    cliff (|Q|>8 / 10^6 cap) all return an honest 'unclassified' result rather than
    raising -- never a crash, never a false star-free claim.  Returns a
    monoid.classify()-shaped dict {tier, channels, detail, ...} where each channel
    carries result in {star-free, not star-free, unclassified}."""
    from generators import protocol_model as _pm, monoid as _mono

    def _unclassified(reason):
        return {"tier": "tier-unclassified (not a regular control skeleton)",
                "detail": reason,
                "channels": [
                    {"backend": "monoid-algebra", "result": "unclassified",
                     "detail": reason},
                    {"backend": "counter-free-search", "result": "unclassified",
                     "detail": "not run: no plain DFA control skeleton"}]}
    try:
        m = _pm.parse_protocol_spec(spec_text)
    except Exception as e:
        return _unclassified(f"spec does not parse as a protocol: {str(e)[:200]}")
    dfa = m.control_skeleton_dfa()
    if dfa is None:
        return _unclassified(
            "protocol uses a call/return stack or acts non-deterministically on "
            "the control alphabet (pushdown control); the star-free method is for "
            "REGULAR control only")
    return _mono.classify(dfa)


def _tier_tag(res):
    """The positive control-skeleton tag of a _tier_classify result, or None when
    the skeleton is unclassified (cap/pushdown) or the two channels disagree (a
    tripwire that never fires on correct code)."""
    t = res.get("tier", "")
    if t == "control-skeleton star-free":
        return "star-free"
    if t == "not star-free":
        return "not-star-free"
    return None


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
        if contract["type"] == "codec-differential":
            # ref_fields flips the differential's verdict (it selects the
            # reference codec's field list), so it MUST enter the cache identity
            # -- otherwise the clean route and a corrupt-ref route collide on one
            # key and the corrupt route is served the clean certificate.
            cdesc["ref_fields"] = common.canonical_json(contract.get("ref_fields"))
    elif contract["type"] == "vpl-differential":
        # identity = the recursive grammar (Impl A) + the named depth bound; the
        # subject is the emitted parser artifact.  The depth is surfaced as a
        # cert claim (tuple form, per the frozen Certificate.claims: tuple), and
        # the tier is emit-check (no Dafny for the recursive language).
        depth = contract.get("depth_bound", 4)
        cdesc["grammar_hash"] = common.sha256_bytes(
            contract["grammar_js"].encode())
        cdesc["tier"] = "emit-check"
        cdesc["claims"] = (("depth_bound", depth),)
    elif contract["type"] == "universal-fixed-uint":
        cdesc["grammar_atoms"] = sorted(contract["grammar_atoms"])
        # The spec-fuzz channel's verdict is a pure function of the sampled
        # emissions; they MUST enter the cache identity or a promotion (the
        # highest-trust, tier-flip verdict) can be served a stale result when
        # the sample set changes (e.g. a different promote() seed).
        cdesc["sampled_hash"] = common.sha256_json(
            [[sm.source, artifact_hash(files)]
             for sm, files in contract.get("sampled_emissions", [])])
        # W5.1: a universal-fixed-uint certificate IS the universal-tier promotion
        # verdict -- stamp the tier onto the certificate so promote()'s tier
        # routing (set_tier only iff cert.tier=='universal') recognises it.  A
        # non-universal outcome would be an honest bounded refusal that retains
        # emit-check duty.
        cdesc["tier"] = "universal"
    elif contract["type"] in ("tool-differential", "tool-lift"):
        cdesc["schema_hash"] = common.sha256_bytes(contract["schema_text"].encode())
        if contract["type"] == "tool-lift":
            cdesc["incumbent_hash"] = common.sha256_json(sorted(
                common.sha256_bytes(v if isinstance(v, bytes) else v.encode())
                for v in contract["incumbent_files"].values()))
    elif contract["type"] in ("constraint-cert", "protocol-cert",
                              "service-conformance"):
        cdesc["spec_hash"] = common.sha256_bytes(contract["spec_text"].encode())
        if contract["type"] == "protocol-cert":
            # P4a: a NESTED protocol carries its bounded-stack honesty on the
            # certificate -- the BMC bound K, the stack depth D, and whether the
            # exploration is complete-to-depth(D) or merely bounded-K.  A
            # non-nested protocol adds nothing here, so its cache identity (and
            # cert_id) are byte-identical to pre-P4a.
            try:
                from generators import protocol_model as _pm
                _m = _pm.parse_protocol_spec(contract["spec_text"])
            except Exception:
                _m = None
            if _m is not None and _m.has_stack():
                _K, _complete, _D = _m.acyclic_bound()
                cdesc["tier"] = ("complete-to-depth(D)" if _complete
                                 else "bounded-K")
                cdesc["claims"] = (("bmc_bound_K", _K), ("stack_depth_D", _D),
                                   ("completeness", cdesc["tier"]))
    elif contract["type"] == "intent-scenarios":
        cdesc["spec_hash"] = common.sha256_bytes(contract["spec_text"].encode())
        cdesc["scenarios_hash"] = common.sha256_bytes(
            contract["scenarios_text"].encode())
    elif contract["type"] == "monitor-cert":
        # Identity of a certified monitor DFA: the LTLf demand (kind + the RAW
        # action names it references) AND the TRACE SET the agreement is checked
        # over (the sorted alphabet + the max trace length).  The trace set MUST
        # be in the cache identity: channel 1 (SMT agreement) and channel 2
        # (flloat cross-check) both range over exactly those traces, so a change
        # to the alphabet or the length bound is a different obligation -- omit it
        # and a stale, weaker verdict is served for a stronger request.
        max_len = int(contract.get("max_len", 4))
        cdesc["kind"] = contract["kind"]
        cdesc["params"] = common.canonical_json(contract["params"])
        cdesc["alphabet"] = sorted(contract["alphabet"])
        cdesc["max_len"] = max_len
        # honest tier/claims surfaced onto the certificate (adjudicate threads
        # them from here).  The agreement is verified for all traces up to the
        # bound, so the tier is bounded-K; claims name the bound and the demand.
        cdesc["tier"] = "bounded-K"
        cdesc["claims"] = (("monitor_agreement_trace_len", max_len),
                           ("ltlf_kind", contract["kind"]))
    elif contract["type"] == "cage-conformance":
        # Identity of a certified CAGE (run/guarded.py): the SUBJECT is every cage
        # file (dispatcher + per-tool input validators + egress output validators
        # + incumbent + monitors) via artifact_hash; the cdesc adds the REIFIED
        # cage hash (canonical-JSON of the dispatcher/monitor/egress/incumbent
        # hashes PLUS the sandbox run-parameter dict and the sandbox `_INNER`
        # template hash -- the "sandbox profile" is not otherwise reifiable) and
        # the service spec.  Every one of those dimensions enters the cache
        # identity, so a changed incumbent, dispatcher, monitor OR sandbox profile
        # is a clean miss, never a stale false-green.
        cdesc["spec_hash"] = common.sha256_bytes(contract["spec_text"].encode())
        cdesc["cage_hash"] = contract["cage_hash"]
        cdesc["sandbox_params"] = common.canonical_json(
            contract.get("sandbox_params"))
        # Honest tier surfaced onto the certificate (adjudicate stamps these): the
        # cage is certified (containment + transparency), the CARGO -- the
        # incumbent's business logic -- explicitly is NOT.  Tuples, never dicts.
        cdesc["tier"] = "monitored"
        cdesc["claims"] = (
            ("cage_boundary",
             "ingress(sequencing/schema/constraint/guard/obligation)"
             " + egress(output_schema) + OS sandbox"),
            ("containment",
             "contract-violating calls rejected where the bare sandboxed"
             " incumbent acts, on solver-generated inputs"),
            ("transparency",
             "legal runs byte-identical to the bare incumbent"
             " (common.canonical_json)"),
            ("cage_hash", contract["cage_hash"]))
        cdesc["non_claims"] = (
            ("incumbent_correctness",
             "the caged incumbent's business logic is NOT verified; only the"
             " cage boundary is certified"),
            ("incumbent_liveness",
             "the cage does not certify the incumbent does anything useful,"
             " only that it cannot cross the boundary"),
            ("containment_scope",
             "containment checked on solver-generated boundary inputs to the"
             " model's structural bound, not proved for all inputs"),
            ("egress_semantics",
             "egress validates output SHAPE against output_schema, never"
             " output truthfulness"))
    elif contract["type"] == "tier-classification":
        # P5.1: identity = the protocol spec text; the control skeleton (and thus
        # its star-free classification) is a pure function of it.  The honest tier
        # and the tier-tag CLAIM are threaded onto the certificate here (adjudicate
        # stamps them).  Both channels are pure/z3-free so classifying twice (here
        # for the tier/claims, again in _dispatch for the channels) is cheap and
        # deterministic -- the same pattern protocol-cert uses for its nested tier.
        cdesc["spec_hash"] = common.sha256_bytes(contract["spec_text"].encode())
        tag = _tier_tag(_tier_classify(contract["spec_text"]))
        if tag == "star-free":
            cdesc["tier"] = "control-skeleton-star-free"
            cdesc["claims"] = (("control_skeleton", "star-free"),)
        elif tag == "not-star-free":
            cdesc["tier"] = "control-skeleton-not-star-free"
            cdesc["claims"] = (("control_skeleton", "not-star-free"),)
        else:
            # pushdown / |Q|>8 / cap: an honest non-certificate (no positive tag);
            # the tier field says so, and _dispatch yields a non-cert verdict.
            cdesc["tier"] = "tier-unclassified"
            cdesc["claims"] = ()
        # Honesty (house rule 4): the tag is CONTROL-SKELETON only.
        cdesc["non_claims"] = (
            ("data_and_guards",
             "guards, integer context and any call/return stack are OUTSIDE the "
             "control-skeleton DFA and are NOT classified by this certificate"),)
    elif contract["type"] == "macro-expansion-cert":
        # P5.2: identity of a macro-expansion certificate.  The SUBJECT is the
        # expanded reading's emitted service (artifact_hash of files); the cdesc
        # binds the two COMPILE-HASHES the contract certifies equal -- the
        # hand-inlined reading's compiled spec and the macro-EXPANDED reading's
        # compiled spec -- plus the request and the macro table used to expand.
        # Every dimension enters the cache identity, so a changed reading, macro
        # or request is a clean miss, never a stale false-green.  Compiling is
        # deterministic and z3-free (parse + compositional compile), the same
        # pattern tier-classification uses (classify in the cdesc AND _dispatch).
        from generators import reading as _rd, reading_compile as _rc
        req = contract["request"]
        try:
            r_in = _rd.parse_reading(contract["inlined_reading"], req)
            r_ex = _rd.parse_reading(contract["expanded_reading"], req,
                                     macro_table=contract["macro_table"])
            h_in = common.sha256_bytes(_rc.compile_reading(r_in)[0].encode())
            h_ex = common.sha256_bytes(_rc.compile_reading(r_ex)[0].encode())
        except Exception as e:
            # an unexpandable / uncompilable expansion still needs a stable cache
            # key; a marker keeps _dispatch's honest fail from crashing on cdesc.
            h_in = common.sha256_bytes(("inlined-error:" + str(e))[:400].encode())
            h_ex = common.sha256_bytes(("expanded-error:" + str(e))[:400].encode())
        cdesc["inlined_compile_hash"] = h_in
        cdesc["expanded_compile_hash"] = h_ex
        cdesc["request_hash"] = common.sha256_bytes(req.encode())
        cdesc["macro_table_hash"] = common.sha256_json(contract["macro_table"])
        # honest tier/claims (tuples, per the frozen Certificate fields).  This is
        # an EMIT-CHECK-grade equivalence: the expanded artifact matches the
        # hand-inlined one at the spec level (byte-identical) and agrees on the
        # inlined reading's solver-entailed scenarios -- not a proof about the
        # macro's meaning for other requests.
        cdesc["tier"] = "emit-check"
        cdesc["claims"] = (
            ("macro_expansion",
             "the macro-expanded reading compiles to a spec byte-identical to"
             " the hand-inlined reading's compiled spec"),
            ("shared_compile_hash", h_ex),
            ("behavioral_agreement",
             "the expanded reading's emitted dispatcher satisfies the inlined"
             " reading's solver-entailed scenarios"))
        cdesc["non_claims"] = (
            ("macro_generality",
             "certifies THIS expansion equals THIS inlined reading, not that the"
             " macro is meaningful or correct for any other request"),
            ("scenario_scope",
             "behavioural agreement is checked on the solver-entailed scenarios"
             " to the model's structural bound, not for all inputs"))
    elif contract["type"] == "translation-cert":
        # W1: the generic per-emission translation certificate Spec_high ->
        # Spec_low, anchored on a NAMED independent anchor (house rule 11).  The
        # cdesc folds EVERY verdict-flipping input so a changed high spec,
        # translator, anchor, or (crucially) channel-2 oracle is a clean cache
        # miss, never a stale false-green -- the completeness-pass hazard a
        # trapdoor otherwise exploits by reproducing an honest cache key.
        from generators import derivers as _dv
        anchor = contract["anchor"]
        cdesc["anchor"] = anchor
        cdesc["high_language"] = contract["high_language"]
        cdesc["high_spec_hash"] = common.sha256_bytes(
            contract["high_spec_text"].encode())
        cdesc["translator_hash"] = (contract.get("translator_hash")
                                    or _dv.lowering_pipeline_hash())
        if anchor == "reference-lowering":
            # bind the trusted reference input, the expansion context, the
            # grounding request, and the fixed lowering-module hash; then fold
            # the two COMPILE hashes the contract certifies equal (the macro-cert
            # pattern, fact 3) so identity is content-addressed to the specs, not
            # the translator under test.
            cdesc["reference_hash"] = common.sha256_bytes(
                contract["reference_lowering"].encode())
            cdesc["context_hash"] = common.sha256_json(
                contract.get("expansion_context") or {})
            cdesc["request_hash"] = common.sha256_bytes(
                contract.get("request", "").encode())
            cdesc["lowering_pipeline_hash"] = _dv.lowering_pipeline_hash()
            hl = contract["high_language"]
            ctx = {**(contract.get("expansion_context") or {}),
                   "request": contract.get("request", "")}
            try:
                low = _dv.LOWERINGS[hl]["lower"]
                cdesc["low_compile_hash"] = common.sha256_bytes(
                    low(contract["high_spec_text"], ctx)["spec"].encode())
                cdesc["ref_compile_hash"] = common.sha256_bytes(
                    low(contract["reference_lowering"], ctx)["spec"].encode())
            except Exception as e:      # keep a STABLE key for the honest fail
                cdesc["low_compile_hash"] = common.sha256_bytes(
                    ("low-error:" + str(e))[:400].encode())
                cdesc["ref_compile_hash"] = common.sha256_bytes(
                    ("ref-error:" + str(e))[:400].encode())
            cdesc["tier"] = "emit-check"
        elif anchor == "fixed-deriver":
            cdesc["low_spec_hash"] = common.sha256_bytes(
                contract.get("low_spec_text", "").encode())
            cdesc["lowering_pipeline_hash"] = _dv.lowering_pipeline_hash()
            # The channel-2 oracle (the independent reference fields) and the
            # channel-1 obligation (the reference token list) are DERIVED from
            # the high spec by the fixed deriver.  Fold both so a corrupt-ref
            # route cannot collide with the clean route -- mirroring
            # codec-differential's ref_fields fold (a shared key would serve the
            # corrupt route the clean route's certificate).  high_spec_hash and
            # lowering_pipeline_hash already pin the inputs; binding the derived
            # oracle makes the verdict dependency explicit and survives any
            # change to what the deriver produces.  A malformed high spec keeps a
            # STABLE key via the error fallback (no cdesc crash).
            hl = contract["high_language"]
            try:
                _obl, _harn = _dv.DERIVERS[hl]
                cdesc["obligations_hash"] = common.sha256_json(
                    _obl(contract["high_spec_text"]))
                cdesc["ref_fields_hash"] = common.canonical_json(
                    _harn(contract["high_spec_text"]).get("ref_fields"))
            except Exception as e:      # keep a STABLE key for the honest fail
                cdesc["obligations_hash"] = common.sha256_bytes(
                    ("deriver-error:" + str(e))[:400].encode())
                cdesc["ref_fields_hash"] = cdesc["obligations_hash"]
            cdesc["tier"] = "emit-check"
        elif anchor == "incumbent-differential":
            # the conversion oracle (W4.2): the oracle MUST enter identity or a
            # trapdoor incumbent byte-identical up to bound n reproduces the
            # honest incumbent's cache key and is served its PASS verdict.
            cdesc["oracle_ref"] = common.canonical_json(
                contract.get("oracle_ref"))
            cdesc["low_spec_hash"] = common.sha256_bytes(
                contract.get("low_spec_text", "").encode())
            cdesc["tier"] = "conformance-relative(n)"
        if contract.get("chain_links") is not None:
            # the emission-time chain below the low spec (caller-supplied; the
            # kernel is stateless): [{generator_hash, tier}, ...].
            cdesc["chain_links"] = common.canonical_json(contract["chain_links"])
        cdesc["claims"] = (
            ("translation_preservation",
             "the translator's output, lowered by the named anchor, matches the "
             "reference lowering and reproduces its solver-entailed scenarios"),
            ("anchor", anchor),
            ("translator_hash", cdesc["translator_hash"]))
        cdesc["non_claims"] = (
            ("translation_generality",
             "certifies THIS emission's translation, not that the translator is "
             "correct for any other input"),
            ("scenario_scope",
             "behavioural agreement is checked on solver-entailed scenarios to "
             "the model's structural bound, not for all inputs"))
    elif contract["type"] == "universal-translation":
        # W5.1: promote a TRANSLATOR.  Channel 1 is a proof over the translator
        # (Dafny where a family has one; else bounded-exhaustive enumeration to
        # size N, adjudicated by the reading compiler + Z3/CVC5-derived
        # scenarios); channel 2 is spec-level behavioural fuzz through the REAL
        # pipeline -- genuinely different procedures.  We have no unbounded proof
        # for the reading compiler, so the honest outcome is `complete-to-size(N)`
        # (a bounded REFUSAL of universality that keeps emit-check duty), never a
        # mislabelled `universal`.  Every sampled input hashes into the identity.
        cdesc["high_language"] = contract["high_language"]
        cdesc["translator_hash"] = contract["translator_hash"]
        samples = contract.get("samples", [])
        # Fold EVERY verdict-flipping per-sample input, INCLUDING the emitted
        # artifact hash: channel 2 replays scenarios against s["files"], and the
        # subject artifact here is empty, so two attempts with identical
        # (high, reference, context, request) but different artifacts would
        # otherwise collide on one cache key and be served a stale verdict.
        cdesc["samples_hash"] = common.sha256_json(
            [[s.get("high_spec_text", ""), s.get("reference_lowering", ""),
              common.canonical_json(s.get("expansion_context") or {}),
              s.get("request", ""), artifact_hash(s.get("files", {}))]
             for s in samples])
        cdesc["size_n"] = len(samples)
        cdesc["tier"] = "complete-to-size(N)"
        cdesc["claims"] = (
            ("bounded_translation_universality",
             "every sampled translator input up to size N lowers identically to "
             "its reference and reproduces its solver-entailed scenarios"),
            ("size_n", len(samples)),
            ("translator_hash", contract["translator_hash"]))
        cdesc["non_claims"] = (
            ("unbounded_universality",
             "NOT a proof the translator is correct for inputs beyond the sampled "
             "size-N corpus; the tier is complete-to-size(N), not universal"),)
    elif contract["type"] in ("statement-cert", "proof-cert"):
        # FORMALIZATION F0.2 / F0.3 -- the Lean proof-assistant contracts.  Both
        # are NON-POOLED, direct-path (the monitor-cert / tier-classification
        # pattern): not in POOL_SUPPORTED, no channel_specs/run_channel, so the
        # channel-parity tripwire is untouched (⚠A8).
        #
        # L2 cache identity folds the FULL checking apparatus so a changed
        # statement, proof, import set, pin, escape gate, or runner/driver is a
        # clean cache miss, never a stale false-green (⚠T6/L2/F-C): the Lean-text
        # bytes (for proof-cert the text is statement+proof, so the proof bytes
        # are folded here), the narrow import set, the joint toolchain+Mathlib
        # pin (lean_toolchain_hash), the escape-gate source hash
        # (validate_lean_hash), and the runner/driver source hash (the
        # LeanBackend-provided sha over kernel/backends.py).
        from kernel.backends import LeanBackend as _LB
        _ct = contract["type"]
        # subject = the statement (or proof) identity, never the empty-files hash.
        subject = (contract.get("statement_hash") or contract.get("proof_hash")
                   or subject)
        cdesc["lean_text_hash"] = common.sha256_bytes(
            contract["lean_text"].encode())
        cdesc["import_set"] = sorted(contract.get("import_set")
                                     or common.MATHLIB_IMPORTS)
        cdesc["toolchain_hash"] = common.lean_toolchain_hash()
        cdesc["mathlib_commit"] = (contract.get("mathlib_commit")
                                   or common.MATHLIB_COMMIT)
        cdesc["toolchain"] = contract.get("toolchain") or common.LEAN_TOOLCHAIN
        cdesc["gate_hash"] = common.validate_lean_hash()      # F0.4 source hash
        cdesc["driver_hash"] = _LB._driver_hash()             # runner/driver sha
        # The axiom set / independence tier / triviality / boundary facts are the
        # TRUSTED run-2 audit's outputs (L5), supplied by the pipeline (WP-H) and
        # RE-VERIFIED by channel 1 in _dispatch (a caller cannot forge the axioms
        # claim -- channel 1 fails if the declared set != the run-2 audit, ⚠T8).
        _axioms = tuple(sorted(contract.get("axioms", ())))
        _indep = contract.get("independence", "kernel-family")   # ⚠D6/L4
        if _ct == "statement-cert":
            # ⚠A9/T5: NOT the free-standing `kernel-checked` string (which would
            # raise against the frozen TIERS) -- a `sorry`-placeholder statement
            # is CHECKED, not proved, so tier `emit-check`.
            cdesc["tier"] = "emit-check"
            cdesc["claims"] = (
                ("statement_hash", subject),
                ("mathlib_commit", cdesc["mathlib_commit"]),
                ("toolchain", cdesc["toolchain"]),
                ("axioms", _axioms),
                ("independence", _indep),
                ("trivially_closed",
                 bool(contract.get("trivially_closed", False))),
                ("boundary_behavior",
                 common.canonical_json(contract.get("boundary_behavior", []))),
            )
            cdesc["non_claims"] = (
                ("fidelity_to_text",
                 "beyond the named gates (F2.1 non-vacuity + F2.2 entailed"
                 " instances) fidelity of the statement to the source text is NOT"
                 " claimed; the examiner is evidence, not a claim (⚠T10)"),
                ("provability",
                 "a `sorry`-placeholder statement is NOT proved; the kernel replay"
                 " re-typechecks the statement, it does not corroborate meaning"),
                ("novelty",
                 "the statement's mathematical importance or novelty is NOT"
                 " judged (out-of-scope item 1)"),
                ("kernel_independence",
                 "channel 1 is `kernel-family` -- lean4checker links Lean's OWN"
                 " kernel, not an independent reimplementation (⚠D6/L4), weaker"
                 " than Z3-vs-CVC5; the disjoint evidence is the tool-independent"
                 " fidelity gates"),
            )
        else:   # proof-cert
            # F0.3: the WP-G TIERS amendment -- a kernel-checked proof term whose
            # run-2 audit shows NO sorryAx and axioms subset of the standard three.
            cdesc["tier"] = "kernel-checked"
            cdesc["claims"] = (
                ("proof_hash", contract.get("proof_hash", subject)),
                ("statement_hash", contract.get("statement_hash", "")),
                ("mathlib_commit", cdesc["mathlib_commit"]),
                ("toolchain", cdesc["toolchain"]),
                ("axioms", _axioms),
                ("independence", _indep),
                ("kernel_checked", True),
            )
            cdesc["non_claims"] = (
                ("fidelity_to_text",
                 "the proof is checked against the STATEMENT; fidelity of the"
                 " statement to the source text is the statement-cert's gates,"
                 " not this certificate (⚠T10)"),
                ("novelty",
                 "mathematical importance or novelty is NOT judged"),
                ("kernel_independence",
                 "`kernel-family` unless lean4lean participates (then"
                 " `kernel-independent`, L4); weaker than Z3-vs-CVC5"),
                ("proof_search",
                 "the tactic script/term is UNTRUSTED input (L1); only the"
                 " kernel-checked proof term is trusted -- beating provers is"
                 " not the thesis"),
            )
    elif contract["type"] in ("smt-obligation", "reading-consistency"):
        cdesc["smtlib_hash"] = common.sha256_bytes(contract["smtlib"].encode())
    elif contract["type"] == "norm-cert":
        # Wave-1 FI-W1-2 (COMPRESSION.md §11.9 / §11.5): the cache identity of a
        # minted norm-cert.  The SUBJECT is the RAW statement hash -- the store,
        # ledger and audit chain key on raw bytes; the canonical form is a VIEW
        # carried in claims, NEVER the identity (FI-W1-2).  The cdesc is
        # certs.norm_cert_cdesc, the SINGLE source of truth shared with
        # make_norm_cert, so kernel.cache_key reproduces a minted cert's
        # contract_hash byte-for-byte and the two can never drift (schema
        # reviewer's advisory).  A norm-cert is minted DIRECTLY by its producer
        # (buildloop.rung_registry.norm_certs_for_reading), never channel-run, so
        # it stays ABSENT from IMPLEMENTED_CONTRACT_TYPES / _dispatch -- this
        # branch wires the identity ONLY (`contract["type"]`, not the `ctype`
        # dispatch literal the allowlist pins).
        subject = contract.get("statement_hash") or subject
        cdesc = norm_cert_cdesc(contract["canonical_form_hash"],
                                contract["rung_pipeline_hash"],
                                contract["meta_equivalence_class"])
    if contract["type"] in _MAX_EXAMPLES_TYPES:
        cdesc["max_examples"] = contract.get("max_examples", 100)
    return subject, cdesc


def cache_key(artifact: dict, contract: dict) -> str:
    """Public: the cache key for (artifact, contract), identical to the key
    check() uses internally.  The CERTS_VERSION prefix means a schema/obligation
    bump makes every older entry a clean miss, never a silently-stale hit."""
    subject, cdesc = _subject_and_cdesc(artifact, contract)
    return f"v{CERTS_VERSION}:{subject}:{common.sha256_json(cdesc)}"


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

    ckey = f"v{CERTS_VERSION}:{subject}:{contract_hash}"
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
        # tier/claims/non_claims flow from the contract descriptor; absent -> the
        # frozen defaults ("" / () / ()), so every existing contract's cert_id is
        # unchanged (non_claims already defaults to () inside the cert_id body).
        # The `monitored`-tier cage uses non_claims to machine-readably decline to
        # praise the cargo it wraps.
        return Certificate.make(kind, subject, contract_hash, channels,
                                tier=cdesc.get("tier", ""),
                                claims=cdesc.get("claims") or (),
                                non_claims=cdesc.get("non_claims") or ())
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


# The registry of pool-safe contract types: those channel_specs()+run_channel()
# can reproduce so certify_service can fan them across a process pool.  The
# parity tripwire (tests/test_channel_parity.py) asserts that for every type
# here the pooled path yields _dispatch's exact channels+verdict, and that every
# type the pooling orchestrator (certify_service._build_jobs) emits is in here.
# codec-roundtrip / reading-consistency deliberately use the direct check()
# path (not the pool) and are not listed.
POOL_SUPPORTED = ("tool-differential", "constraint-cert", "protocol-cert",
                  "service-conformance", "intent-scenarios")

# The contract types this kernel's _dispatch implements.  The allowlist test
# (house rule 6, tests/test_contract_allowlist.py) pins this SUBSET of the
# frozen vocabulary = the 16 pre-existing types + the two Combined-Loop
# additions (translation-cert, universal-translation) + the two FORMALIZATION
# F0 additions (statement-cert, proof-cert), so a rogue new contract type
# cannot slip into the kernel unpinned.
IMPLEMENTED_CONTRACT_TYPES = frozenset({
    "codec-roundtrip", "codec-differential", "vpl-differential",
    "universal-fixed-uint", "tool-differential", "tool-lift",
    "constraint-cert", "protocol-cert", "service-conformance",
    "intent-scenarios", "monitor-cert", "cage-conformance",
    "tier-classification", "macro-expansion-cert", "smt-obligation",
    "reading-consistency",
    # Combined-Loop additions:
    "translation-cert", "universal-translation",
    # FORMALIZATION F0 additions (WP-G) -- non-pooled, direct-path Lean contracts:
    "statement-cert", "proof-cert",
})


def channel_specs(artifact, contract):
    """Decompose a contract into its independent, picklable channel tasks so an
    orchestrator can run EACH channel in its own process -- overlapping even a
    single contract's channels and isolating z3 per process (no lock needed).
    Returns (kind, [spec, ...]); each spec is consumed by run_channel().  Covers
    the pool-supported contracts (POOL_SUPPORTED); other contracts use
    check()/_dispatch."""
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
        from generators import (protocol_model as _pm, protocol_gen as _pg,
                                ltlf_smt as _lt)
        m = _pm.parse_protocol_spec(contract["spec_text"])
        K = m.acyclic_bound()[0]
        obl = _pg.bmc_smtlib(m, K)
        specs = [("smt", obl, "z3", "z3-safety"),
                 ("smt", obl, "cvc5", "cvc5-safety")]
        KT = _pg.temporal_bound(m, K)      # per-demand LTLf queries (parity with
        for o in m.obligations:            # _dispatch)
            try:
                tobl = _lt.protocol_temporal_smtlib(m, o, KT)
            except _lt.UnsupportedObligation:
                specs.append(("temporal_unknown", o["id"], contract["spec_text"]))
                continue
            specs.append(("smt", tobl, "z3", f"z3-temporal-{o['id']}"))
            specs.append(("smt", tobl, "cvc5", f"cvc5-temporal-{o['id']}"))
        specs.append(("protocol_conf", files, contract["spec_text"]))
        return "protocol-admission", specs
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
    if kind == "temporal_unknown":
        # reproduce _dispatch's honest "unknown" channel for an unsupported
        # temporal kind (keeps the pooled path in parity with the direct path).
        from generators import (protocol_model as _pm, protocol_gen as _pg,
                                ltlf_smt as _lt)
        oid = spec[1]
        m = _pm.parse_protocol_spec(spec[2])
        KT = _pg.temporal_bound(m, m.acyclic_bound()[0])
        o = next(o for o in m.obligations if o["id"] == oid)
        try:
            _lt.protocol_temporal_smtlib(m, o, KT)
            raise ValueError("expected UnsupportedObligation")
        except _lt.UnsupportedObligation as e:
            return {"backend": f"temporal-{oid}", "result": "unknown",
                    "role": "smt-proof", "detail": str(e)[:400]}
    if kind == "protocol_conf":
        from generators import protocol_model as _pm
        m = _pm.parse_protocol_spec(spec[2])
        K = m.acyclic_bound()[0]
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


# The standard Mathlib kernel axioms (⚠D5): a real proof may use these three; a
# bare-`sorry` statement additionally shows `sorryAx`.  Builders must NOT write
# an equality test expecting all four on a `sorry` statement -- it shows sorryAx
# alone over this fragment.
_STANDARD_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})


def _lean_kernel_channel(lean_text, *, expect_sorry, forbid_sorry, contract):
    """The F0.2/F0.3 kernel channel (channel 1): the L5 two-run audit.

    RUN 1 (UNTRUSTED) elaborates the subject in the OS sandbox; its outputs are
    artifacts, not evidence.  RUN 2 (TRUSTED) replays the exported environment
    under lean4checker and the axiom audit is read from THAT pass -- never from
    the elaboration session, which the subject could forge (⚠T1/T2).  This is a
    `kernel-family` channel (L4, sharpened by ⚠D6: lean4checker links Lean's OWN
    kernel, not an independent reimplementation), so genuine dual-checker
    independence is met by the fidelity gates (channels 2+), NOT by two
    kernel-family passes (⚠T3).

    role='behavioral-witness': a failing kernel audit is an AUTHORITATIVE
    observation of the real compiled artifact, so adjudicate refuses cleanly
    (never a spurious 'disagreement').  With the Lean toolchain absent every
    LeanBackend method honest-degrades to `unavailable`, and this returns
    result='unknown' -> NO certificate, even when the fidelity channels all pass.
    That is the correct behavior: there is no false green without the kernel.

    Every verdict-bearing fact is extracted here in TRUSTED code (L5/⚠T8): the
    caller-declared `axioms` (populated by WP-H from this same trusted audit)
    must equal the run-2 audit, so the cert's `axioms` claim cannot be forged.
    """
    from buildloop import validate_lean
    from kernel.backends import LeanBackend
    base = {"backend": "lean-elaborate+lean4checker", "role": "behavioral-witness",
            "independence": contract.get("independence", "kernel-family")}

    # Defense in depth: the escape gate (F0.4) re-checks even the deterministic
    # compiler's own output BEFORE any elaboration.  It is NEVER the trust
    # boundary (⚠T7) -- the OS sandbox + L5 are; it is a cheap, loud fast-reject.
    ok, reason = validate_lean.validate_lean(lean_text)
    if not ok:
        return {**base, "result": "fail",
                "detail": f"escape-gate refusal (pre-sandbox): {reason}"}

    be = LeanBackend()
    el = be.elaborate(lean_text, expect_sorry=expect_sorry)          # RUN 1
    if el.get("unavailable"):
        return {**base, "result": "unknown",
                "detail": "lean toolchain absent -- no verdict-bearing kernel "
                          "audit (honest degrade, L5); no certificate issued"}
    if not el.get("ok"):
        return {**base, "result": "fail",
                "detail": ("elaboration (run 1) did not build: "
                           + str(el.get("reason") or el.get("detail", ""))[:600])}

    rc = be.recheck(el["olean_path"])                                # RUN 2 (trusted)
    if rc.get("unavailable"):
        return {**base, "result": "unknown",
                "detail": "lean4checker unavailable -- no trusted run-2 audit (L5)"}
    if not rc.get("ok"):
        return {**base, "result": "fail",
                "detail": "lean4checker (run 2) rejected the replayed environment"}
    if not rc.get("audited"):
        # FAIL CLOSED on auditor silence: an absent/unparseable axiom audit is
        # NOT "no axioms" -- treating it so let a smuggled-sorry proof-cert
        # through as a false green (caught by the L5 teeth on the first real
        # toolchain run).  No audit -> no verdict -> no certificate.
        return {**base, "result": "unknown",
                "detail": ("run-2 axiom-audit driver did not report (auditor "
                           "liveness) -- fail closed, no certificate: "
                           + str(rc.get("transcript", ""))[-400:])}

    audited = set(rc.get("axioms", []))
    has_sorry = "sorryAx" in audited
    non_sorry = audited - {"sorryAx"}
    if forbid_sorry:
        # proof-cert (F0.3): NO sorryAx, axioms subset of the standard three.
        # ⚠T2 -- this environment audit, NOT the escape gate, is the axiom
        # defense (an axiom smuggled via Lean.addDecl carries no `axiom` token).
        if has_sorry:
            return {**base, "result": "fail",
                    "detail": f"proof-cert audit found sorryAx: {sorted(audited)}"}
        if not non_sorry <= _STANDARD_AXIOMS:
            return {**base, "result": "fail",
                    "detail": ("axiom(s) outside the standard three: "
                               f"{sorted(non_sorry - _STANDARD_AXIOMS)}")}
    else:
        # statement-cert (F0.2): a bare-`sorry` statement shows sorryAx PRESENT
        # and any other axiom in the standard three (⚠D5).
        if not has_sorry:
            return {**base, "result": "fail",
                    "detail": ("statement-cert expected a `sorry` placeholder "
                               f"(sorryAx absent); axioms={sorted(audited)}")}
        if not non_sorry <= _STANDARD_AXIOMS:
            return {**base, "result": "fail",
                    "detail": ("axiom(s) outside {sorryAx} u the standard three: "
                               f"{sorted(non_sorry - _STANDARD_AXIOMS)}")}

    # ⚠T8: the caller's declared axioms (from WP-H's run-2 audit) must MATCH this
    # trusted audit, so the cert's `axioms` claim is extracted per L5, not forged.
    declared = contract.get("axioms")
    if declared is not None and set(declared) != audited:
        return {**base, "result": "fail",
                "detail": (f"declared axioms {sorted(set(declared))} != run-2 "
                           f"audit {sorted(audited)}")}

    # pp-roundtrip sub-check (⚠D6): the elaborated statement pretty-printed under
    # pp.all must re-elaborate to a DEFINITIONALLY-EQUAL term -- catching the
    # silent-coercion / wrong-instance class, this plan's whole mission.  The
    # frozen F-H runner API (elaborate/recheck/eval_props) exposes no pp
    # primitive, so this is delegated: a runner `pp_roundtrip` if one is added,
    # else a caller-supplied result verified per L5.  Absent both, D6 is UNWIRED
    # -> 'unknown' (never a faked pass).
    ppr = None
    if hasattr(be, "pp_roundtrip"):
        ppr = be.pp_roundtrip(lean_text)
    elif contract.get("pp_roundtrip") is not None:
        ppr = contract["pp_roundtrip"]
    if ppr is None or ppr.get("unavailable"):
        return {**base, "result": "unknown",
                "detail": "pp.all round-trip (D6) not wired on this runner and "
                          "not supplied by the caller -- kernel channel "
                          "indeterminate; no false green"}
    if not ppr.get("ok"):
        return {**base, "result": "fail",
                "detail": "pp.all round-trip is not definitionally equal (D6): "
                          "silent-coercion / wrong-instance suspected"}

    return {**base, "result": "pass",
            "detail": ("L5 two-run: elaborated (run 1) + lean4checker-replayed "
                       f"(run 2); axioms={sorted(audited)}; pp.all round-trip "
                       "def-eq (D6)")}


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
        from generators import (protocol_model as _pm, protocol_gen as _pg,
                                ltlf_smt as _lt)
        m = _pm.parse_protocol_spec(contract["spec_text"])
        K = m.acyclic_bound()[0]
        obl = _pg.bmc_smtlib(m, K)
        z = _smt.run_z3(obl); z["backend"] = "z3-safety"; z["role"] = "smt-proof"
        c = _smt.run_cvc5(obl); c["backend"] = "cvc5-safety"; c["role"] = "smt-proof"
        channels = [z, c]
        # P1: per LTLf temporal demand, its OWN dual-solver query (unsat = the
        # demand holds on every complete session within the bound).  K is lifted
        # to cover any `within n` deadline (hazard 7).
        KT = _pg.temporal_bound(m, K)
        for o in m.obligations:
            try:
                tobl = _lt.protocol_temporal_smtlib(m, o, KT)
            except _lt.UnsupportedObligation as e:
                # honest non-verdict: this temporal kind has no protocol-side SMT
                # obligation yet (Phase-1 fragment is 'eventually').  "unknown"
                # blocks certification without crashing the check.
                channels.append({"backend": f"temporal-{o['id']}",
                                 "result": "unknown", "role": "smt-proof",
                                 "detail": str(e)[:400]})
                continue
            tz = _smt.run_z3(tobl); tz["backend"] = f"z3-temporal-{o['id']}"
            tz["role"] = "smt-proof"
            tc = _smt.run_cvc5(tobl); tc["backend"] = f"cvc5-temporal-{o['id']}"
            tc["role"] = "smt-proof"
            channels += [tz, tc]
        conf = _hyp.check_protocol_conformance(artifact["files"], m, K)
        channels.append(conf)
        return "protocol-admission", channels
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
    if ctype == "vpl-differential":
        # Recursive JSON-subset codec (the corrected P4b route).  Two
        # independent evidence channels over DISJOINT input classes -- no Dafny
        # (the .ksy/Dafny model cannot express recursion), tier emit-check:
        #   channel 1: cross-implementation differential on bounded-depth
        #              recursive JSON VALUES -- the tree-sitter-emitted codec,
        #              the independent recursive-descent codec, and stdlib json
        #              must agree byte-for-byte on encode and cross-decode
        #              (N-version evidence, no shared code with tree-sitter);
        #   channel 2: membership differential on structurally MUTATED inputs
        #              (bracket deletion/swap/truncation -> visibly-pushdown
        #              membership violations); the tree-sitter decider
        #              (has_error) and the recursive-descent decider must agree,
        #              rejecting the same illegal strings.
        # Both channels are z3-free sandbox work -> run them concurrently.  The
        # recursion depth is bounded and named on the certificate (claims), and
        # the tree-JSON driver caps nesting consistently so deep inputs do not
        # become opaque sandbox crashes.
        depth = contract.get("depth_bound", 4)
        mx = contract.get("max_examples", 100)
        channels = _par(
            lambda: _hyp.check_vpl_differential(
                artifact["files"], depth_bound=depth, max_examples=mx),
            lambda: _hyp.check_vpl_membership(
                artifact["files"], depth_bound=depth, max_examples=mx))
        return "vpl-differential-admission", channels
    if ctype == "macro-expansion-cert":
        # P5.2: certify that a macro-EXPANDED reading is identical to its
        # hand-INLINED form, so a recurring Reading pattern can be abbreviated
        # without weakening what gets certified.  Non-pooled direct-path contract
        # (like monitor-cert / tier-classification): NOT in POOL_SUPPORTED, no
        # channel_specs/run_channel, so the channel-parity tripwire is untouched.
        # Two independent evidence channels:
        #   channel 1 = COMPILE IDENTITY: the expanded reading and the inlined
        #               reading compile (compositional, deterministic) to the SAME
        #               meta-spec, byte-for-byte (equal compile-hash).  A macro
        #               that expands to a DIFFERENT spec is refuted here.
        #   channel 2 = ENTAILED-SCENARIO REPLAY: the expanded reading's emitted
        #               dispatcher reproduces the accept/reject of the scenarios
        #               the INLINED reading's demands SOLVER-ENTAIL -- behavioural
        #               N-version evidence, disjoint from the syntactic hash check.
        # A faithful macro passes both; a bad macro (different guard/spec) fails
        # BOTH (different bytes AND a violated entailed expectation).
        from generators import (reading as _rd, reading_compile as _rc,
                                service_model as _svm)
        req = contract["request"]
        try:
            r_in = _rd.parse_reading(contract["inlined_reading"], req)
            r_ex = _rd.parse_reading(contract["expanded_reading"], req,
                                     macro_table=contract["macro_table"])
            spec_in = _rc.compile_reading(r_in)[0]
            spec_ex = _rc.compile_reading(r_ex)[0]
        except Exception as e:
            # an unexpandable/uncompilable expansion is refuted, not a crash.
            det = f"expanded reading did not parse/compile: {str(e)[:400]}"
            return "macro-expansion-admission", [
                {"backend": "macro-compile-identity", "result": "fail",
                 "role": "cross-impl-differential", "detail": det},
                {"backend": "entailed-scenario-replay", "result": "fail",
                 "role": "behavioral-witness",
                 "detail": "not run: expansion failed"}]
        ch1 = _hyp.check_macro_compile_identity(spec_in, spec_ex)
        m_in = _svm.parse_service_spec(spec_in)
        scenarios = _rc.entailed_scenarios(m_in, r_in)
        ch2 = _hyp.check_macro_scenario_replay(
            artifact.get("files", {}), scenarios)
        return "macro-expansion-admission", [ch1, ch2]
    if ctype == "translation-cert":
        # W1: the generic per-emission translation contract.  Non-pooled direct
        # path (like macro-expansion-cert): NOT in POOL_SUPPORTED, no
        # channel_specs/run_channel, so the channel-parity tripwire is untouched.
        # Dispatch on the anchor (house rule 11 -- no cert without one).
        from generators import derivers as _dv
        anchor = contract["anchor"]
        if anchor == "reference-lowering":
            # Generalises macro-expansion-cert (fact 3): a TRUSTED lowering L
            # (keyed by high_language) lowers both the translator's output and a
            # trusted reference; channel 1 = compile identity of the two lowered
            # specs; channel 2 = the reference's solver-entailed scenarios
            # replayed on the emitted artifact.  The harness comes from the HIGH
            # spec via L, never via the translator under test.
            hl = contract["high_language"]
            spec = _dv.LOWERINGS.get(hl)
            if spec is None:
                return "translation-admission", [
                    {"backend": "translation-compile-identity", "result": "fail",
                     "role": "cross-impl-differential",
                     "detail": f"no reference lowering for {hl!r}"},
                    {"backend": "entailed-scenario-replay", "result": "fail",
                     "role": "behavioral-witness", "detail": "not run"}]
            ctx = {**(contract.get("expansion_context") or {}),
                   "request": contract.get("request", "")}
            try:
                lo = spec["lower"](contract["high_spec_text"], ctx)
                ref = spec["lower"](contract["reference_lowering"], ctx)
            except Exception as e:
                det = f"translation did not lower/compile: {str(e)[:400]}"
                return "translation-admission", [
                    {"backend": "translation-compile-identity", "result": "fail",
                     "role": "cross-impl-differential", "detail": det},
                    {"backend": "entailed-scenario-replay", "result": "fail",
                     "role": "behavioral-witness",
                     "detail": "not run: lowering failed"}]
            ch1 = _hyp.check_macro_compile_identity(ref["spec"], lo["spec"])
            ch1["backend"] = "translation-compile-identity"
            scenarios = spec["scenarios"](ref)
            # A2 (F3.3): channel-2 replay is PLUGGABLE per LOWERINGS entry.  The
            # default `check_macro_scenario_replay` emits a service dispatcher
            # (`from service import Service`) and is correct for the reading /
            # macro-reading lowerings; a math emission has no dispatcher, so its
            # entry supplies `replay` = entailed-instance replay via math_eval.
            # Absent a `replay` key the default keeps every existing lowering
            # byte-identical.
            replay = spec.get("replay", _hyp.check_macro_scenario_replay)
            ch2 = replay(artifact.get("files", {}), scenarios)
            ch2["backend"] = "translation-scenario-replay"
            return "translation-admission", [ch1, ch2]
        if anchor == "incumbent-differential":
            # W4.2 conversion: certify the LLM-authored REPLACEMENT is
            # behaviourally EQUIVALENT to the CAGED INCUMBENT up to the declared
            # state bound n.  The named anchor (house rule 11) is the incumbent-
            # as-oracle: oracle_ref = {incumbent_hash, cage_hash, sandbox_params}
            # is already folded into cdesc, so a trapdoor byte-identical up to n
            # cannot reproduce an honest cache key.  Two genuinely-independent
            # channels (different procedures, not sampling-vs-enumeration of one
            # predicate):
            #   channel 1 = the CAGE / W-suite differential -- the incumbent IS
            #       the oracle_ref cage: on the cage's OWN solver-generated LEGAL
            #       and VIOLATING sessions the emitted replacement dispatcher must
            #       reach the SAME accept/reject verdict as the caged incumbent
            #       (cage.run).  Real emitted artifacts on both sides (a cross-
            #       impl differential over the cage's certified input classes).
            #   channel 2 = a RANDOM-WALK / W-METHOD differential at the state
            #       bound n, CONTAINMENT respected: over a W-method test suite
            #       (state-cover of the replacement protocol . Sigma^<=k) the
            #       incumbent's CLASSIFIED output (buildloop.lstar._classify;
            #       'ok' == accept), queried CONTAINED inside the cage's sandbox
            #       batching oracle, must agree with the replacement's structural
            #       accept/reject.  A trapdoor DEEPER than the learned bound
            #       surfaces HERE as an honest divergence -> fail -> conversion
            #       refused; a NONDETERMINISTIC incumbent ABORTS the differential
            #       (first-class, never a silently-wrong verdict).
            # NON-pooled direct path (not in POOL_SUPPORTED, no channel_specs /
            # run_channel), like macro-expansion-cert / cage-conformance.  If the
            # replacement DIVERGES from the incumbent, honest FAIL channels are
            # returned and no certificate issues.
            from run import guarded as _guarded
            from generators import service_model as _svm2
            from buildloop import lstar as _lstar
            _KIND = "conversion-differential"
            cage = contract.get("cage")
            low_text = contract.get("low_spec_text", "")
            n = int(contract.get("n") or contract.get("state_bound_n") or 0)
            if cage is None:
                return _KIND, [
                    {"backend": "cage-differential", "result": "unknown",
                     "role": "cross-impl-differential",
                     "detail": "no oracle_ref cage supplied to the differential"},
                    {"backend": "walk-differential", "result": "unknown",
                     "role": "behavioral-witness", "detail": "not run"}]
            # emit the replacement through the normal service pipeline.  A benign
            # stub incumbent -- only the emitted dispatcher (run_dispatch) is ever
            # exercised on the replacement side; the stub never runs.
            _probe = (b"class Incumbent:\n"
                      b"    def __init__(self):\n        pass\n"
                      b"    def call(self, tool, args):\n        return None\n")
            try:
                rep_model = _svm2.parse_service_spec(low_text)
                rep_cage = _guarded.Cage(rep_model, _probe)
            except Exception as e:
                det = f"replacement spec did not parse/emit: {str(e)[:400]}"
                return _KIND, [
                    {"backend": "cage-differential", "result": "fail",
                     "role": "cross-impl-differential", "detail": det},
                    {"backend": "walk-differential", "result": "fail",
                     "role": "behavioral-witness",
                     "detail": "not run: replacement invalid"}]
            cmodel = cage.model

            def _cage_diff():
                # channel 1: replacement emitted dispatcher vs the CAGED incumbent
                # over the cage's own legal + violating sessions.
                try:
                    legal = _guarded.legal_sessions(cmodel)
                    viol = _guarded.violating_sessions(cage, cmodel)
                except Exception as ex:
                    return {"backend": "cage-differential", "result": "unknown",
                            "role": "cross-impl-differential",
                            "detail": f"session generation failed: {str(ex)[:400]}"}
                sessions = ([("legal", s) for s in legal]
                            + [("violating", s) for s in viol])
                if not sessions:
                    return {"backend": "cage-differential", "result": "fail",
                            "role": "cross-impl-differential",
                            "detail": "no cage sessions (differential vacuous)"}
                accepts = 0
                for label, s in sessions:
                    inc = cage.run(s["init"], s["seq"])
                    rep = rep_cage.run_dispatch(s["init"], s["seq"])
                    for i in range(len(s["seq"])):
                        iok = bool(inc[i].get("ok"))
                        rok = bool(rep[i].get("ok")) if i < len(rep) else False
                        if iok:
                            accepts += 1
                        if iok != rok:
                            return {"backend": "cage-differential",
                                    "result": "fail",
                                    "role": "cross-impl-differential",
                                    "detail": (
                                        f"replacement diverges from the caged "
                                        f"incumbent on a {label} session at step "
                                        f"{i} ({s['seq'][i][0]!r}): incumbent "
                                        f"{'accept' if iok else 'reject'} vs "
                                        f"replacement "
                                        f"{'accept' if rok else 'reject'}")}
                if accepts == 0:
                    return {"backend": "cage-differential", "result": "fail",
                            "role": "cross-impl-differential",
                            "detail": "vacuous: no accepted step across sessions"}
                return {"backend": "cage-differential", "result": "pass",
                        "role": "cross-impl-differential",
                        "detail": (
                            f"{len(sessions)} cage sessions (legal+violating): "
                            f"emitted replacement matches the caged incumbent's "
                            f"accept/reject on every step ({accepts} accepts)")}

            def _rep_step(model):
                # structural in-process stepper for the (data-free abstract)
                # replacement protocol: a symbol is legal iff a tool of that name
                # leaves the current state; an illegal call is refused and leaves
                # the state unchanged (a distinct procedure from channel 1's
                # sandboxed dispatcher).
                edge = {t.name: (t.frm, t.to) for t in model.tools}

                def step(state, sym):
                    e = edge.get(sym)
                    if e is None or e[0] != state:
                        return (False, state)
                    return (True, e[1])
                return step

            def _wmethod_tests(model, alphabet, bound):
                # state-cover of the replacement (BFS spanning tree over its
                # accept-edges) . Sigma^<=k, k = min(max(1, n - m + 1), 3): the
                # Chow W-method suite that reaches a state DEEPER than the
                # replacement's m states (where a trapdoor hides).
                step = _rep_step(model)
                cover, seen = [()], {model.initial}
                frontier = [((), model.initial)]
                while frontier:
                    nf = []
                    for acc, st in frontier:
                        for sym in alphabet:
                            ok, nx = step(st, sym)
                            if ok and nx not in seen:
                                seen.add(nx)
                                cover.append(acc + (sym,))
                                nf.append((acc + (sym,), nx))
                    frontier = nf
                m = max(1, len(model.states))
                # Chow's k = n - m + 1, floored at 2 so a trapdoor one state
                # deeper than the replacement (distinguished by a length>=2
                # suffix, e.g. the order_service void) is still reached, and
                # capped so the suite stays sandbox-feasible.
                k = min(max(2, bound - m + 1), 3)
                mids = _lstar._sigma_upto(alphabet, k)
                tests = {tuple(p) + tuple(mid) for p in cover for mid in mids}
                tests.discard(())
                return sorted(tests, key=lambda t: (len(t), t))

            def _walk_diff():
                # channel 2: W-method / random-walk differential up to n against
                # the incumbent queried CONTAINED in the cage's sandbox.  The
                # alphabet is the FULL learned input alphabet (contract-supplied),
                # NOT just the cage's ok-edge tool subset -- a trapdoor reached by
                # a symbol the replacement never accepts (e.g. the order_service
                # `refund` god-mode) is otherwise invisible.  The cage's incumbent
                # is the abstraction adapter, so identity abstract symbols reach it.
                alphabet = (contract.get("diff_alphabet")
                            or [t.name for t in cmodel.tools])
                if not alphabet:
                    return {"backend": "walk-differential", "result": "unknown",
                            "role": "behavioral-witness",
                            "detail": "cage model has no tool alphabet"}
                abstraction = {s: {"tool": s, "args": {}} for s in alphabet}
                oracle = _lstar.Oracle(cage._incumbent_src, alphabet, abstraction)
                tests = _wmethod_tests(rep_model, alphabet, n)
                if not tests:
                    return {"backend": "walk-differential", "result": "unknown",
                            "role": "behavioral-witness",
                            "detail": "no test sequences generated"}
                try:
                    oracle.prefill(tests)
                except _lstar.NondeterministicIncumbent as ex:
                    return {"backend": "walk-differential", "result": "fail",
                            "role": "behavioral-witness",
                            "detail": (f"nondeterministic incumbent: differential "
                                       f"aborted ({str(ex)[:280]})")}
                except Exception as ex:
                    return {"backend": "walk-differential", "result": "unknown",
                            "role": "behavioral-witness",
                            "detail": f"incumbent query failed: {str(ex)[:400]}"}
                step = _rep_step(rep_model)
                checked = 0
                for seq in tests:
                    out = oracle.outseq(seq)
                    st = rep_model.initial
                    for i, sym in enumerate(seq):
                        inc_accept = (out[i] == _lstar.ACCEPTING)
                        rok, st = step(st, sym)
                        checked += 1
                        if inc_accept != rok:
                            return {"backend": "walk-differential",
                                    "result": "fail",
                                    "role": "behavioral-witness",
                                    "detail": (
                                        f"replacement diverges from the incumbent "
                                        f"up to n={n} on {list(seq[:i + 1])}: "
                                        f"incumbent "
                                        f"{'accept' if inc_accept else 'reject'} "
                                        f"vs replacement "
                                        f"{'accept' if rok else 'reject'} -- the "
                                        f"honesty bound (a state or trapdoor "
                                        f"deeper than n refuses the conversion)")}
                return {"backend": "walk-differential", "result": "pass",
                        "role": "behavioral-witness",
                        "detail": (
                            f"W-method+walk differential to n={n}: {len(tests)} "
                            f"contained sequences, {checked} steps; replacement "
                            f"accept/reject == incumbent 'ok'-class on every step "
                            f"(containment respected)")}

            return _KIND, [_cage_diff(), _walk_diff()]
        if anchor == "fixed-deriver":
            # W1.3b: the abnf->ksy translation stage.  DAFNY-FREE (does NOT use
            # the Dafny check_codec_spec).  The named independent anchor (house
            # rule 11) is the fixed per-language deriver DERIVERS[high_language]:
            # an LLM-free obligation-deriver + harness-deriver, each with its own
            # TRUST.md 1.2x entry.  Two genuinely-independent channels, both
            # derived from the HIGH spec (never via the translator under test):
            #   channel 1 (cross-impl-differential): the REFERENCE ksy the fixed
            #       deriver builds from the high spec -- tokens_to_ksy(tokenize(
            #       high), sha256(high)) -- must be COMPILE-IDENTICAL to the
            #       translator's emitted low_spec_text (the macro-compile-identity
            #       pattern, over ksy).  A lossy translator that drops or renames
            #       a field emits a different ksy and is refuted here.
            #   channel 2 (behavioral-witness): a codec differential (Hypothesis
            #       round-trip + ksc, NO Dafny) between the emitted low_artifact_
            #       files codec (spec_model = parse_ksy(low_spec_text)) and the
            #       INDEPENDENT reference fields the deriver derives from the high
            #       spec (abnf_reference_fields).  A byte divergence refuses.
            # Non-pooled direct path (not in POOL_SUPPORTED).  On any divergence
            # or lowering error honest FAIL channels are returned -- never a cert.
            from generators import ksy_model as _ksy, abnf_chain as _abnf
            hl = contract["high_language"]
            entry = _dv.DERIVERS.get(hl)
            if entry is None:
                return "translation-admission", [
                    {"backend": "translation-abnf-compile-identity",
                     "result": "fail", "role": "cross-impl-differential",
                     "detail": f"no fixed deriver for {hl!r}"},
                    {"backend": "translation-abnf-codec-differential",
                     "result": "fail", "role": "behavioral-witness",
                     "detail": "not run"}]
            derive_obligations, derive_harness = entry
            high = contract["high_spec_text"]
            low_text = contract.get("low_spec_text", "")
            low_files = contract.get("low_artifact_files") or {}
            # channel 1: build the reference ksy from the HIGH spec via the fixed
            # deriver, then compile-identity against the translator's emitted ksy.
            try:
                toks = derive_obligations(high)   # reference token list
                ref_ksy = _abnf.tokens_to_ksy(
                    toks, common.sha256_bytes(high.encode()))
            except Exception as e:
                det = f"reference lowering failed: {str(e)[:400]}"
                return "translation-admission", [
                    {"backend": "translation-abnf-compile-identity",
                     "result": "fail", "role": "cross-impl-differential",
                     "detail": det},
                    {"backend": "translation-abnf-codec-differential",
                     "result": "fail", "role": "behavioral-witness",
                     "detail": "not run: lowering failed"}]
            ch1 = _hyp.check_macro_compile_identity(ref_ksy, low_text)
            ch1["backend"] = "translation-abnf-compile-identity"
            # channel 2: codec differential on the emitted artifact vs the
            # independent reference fields.  parse the LOW spec for the kaitai
            # side + value strategies; the reference side uses ref_fields.
            try:
                spec_model = _ksy.parse_ksy(low_text)
                ref_fields = derive_harness(high)["ref_fields"]
            except Exception as e:
                ch2 = {"backend": "translation-abnf-codec-differential",
                       "result": "fail", "role": "behavioral-witness",
                       "detail": (f"low spec did not parse / harness failed: "
                                  f"{str(e)[:400]}")}
                return "translation-admission", [ch1, ch2]
            ch2 = _hyp.check_differential(
                low_files, spec_model,
                max_examples=contract.get("max_examples", 100),
                ref_fields=ref_fields)
            ch2["backend"] = "translation-abnf-codec-differential"
            ch2["role"] = "behavioral-witness"
            return "translation-admission", [ch1, ch2]
        # any other anchor is not wired -> honest NON-certificate (never a false
        # green), so an unknown anchor cannot be served a stale pass.
        return "translation-admission", [
            {"backend": "translation-anchor", "result": "unknown",
             "role": "smt-proof",
             "detail": f"anchor {anchor!r} not wired in this build"},
            {"backend": "translation-anchor-2", "result": "unknown",
             "role": "behavioral-witness", "detail": "not run"}]
    if ctype == "universal-translation":
        # W5.1: promote a TRANSLATOR by a bounded-exhaustive check over N sampled
        # inputs.  Two genuinely different aggregate channels, both Dafny-free:
        #   channel 1 = every sampled translation lowers compile-IDENTICAL to its
        #               reference (cross-impl-differential, via the trusted
        #               lowering, never the translator under test);
        #   channel 2 = every sampled artifact reproduces the reference's
        #               solver-entailed scenarios (behavioural fuzz through the
        #               real pipeline).
        # An honest PASS yields tier `complete-to-size(N)` (cdesc) -- a bounded
        # result, never `universal`, so promote()'s tier routing keeps emit-check
        # duty.  A single unsound sample fails a channel -> no certificate -> the
        # promotion is refused (the tier lattice doing its job).
        from generators import derivers as _dv
        spec = _dv.LOWERINGS.get(contract["high_language"])
        samples = contract.get("samples", [])
        if spec is None or not samples:
            return "promotion-translation", [
                {"backend": "bounded-translation-compile-identity",
                 "result": "fail", "role": "cross-impl-differential",
                 "detail": "no reference lowering or no samples"},
                {"backend": "bounded-translation-scenario-fuzz",
                 "result": "fail", "role": "behavioral-witness",
                 "detail": "not run"}]
        compile_ok, scen_ok, details = True, True, []
        for i, s in enumerate(samples):
            ctx = {**(s.get("expansion_context") or {}),
                   "request": s.get("request", "")}
            try:
                lo = spec["lower"](s["high_spec_text"], ctx)
                ref = spec["lower"](s["reference_lowering"], ctx)
            except Exception as e:
                compile_ok = scen_ok = False
                details.append(f"sample {i}: lowering failed: {str(e)[:120]}")
                continue
            c1 = _hyp.check_macro_compile_identity(ref["spec"], lo["spec"])
            if c1["result"] != "pass":
                compile_ok = False
                details.append(f"sample {i} compile-identity fail")
            c2 = _hyp.check_macro_scenario_replay(
                s.get("files", {}), spec["scenarios"](ref))
            if c2["result"] != "pass":
                scen_ok = False
                details.append(f"sample {i} scenario-replay fail")
        n = len(samples)
        return "promotion-translation", [
            {"backend": "bounded-translation-compile-identity",
             "role": "cross-impl-differential",
             "result": "pass" if compile_ok else "fail",
             "detail": f"{n} sampled inputs"
                       + ("" if compile_ok else "; " + "; ".join(details[:3]))},
            {"backend": "bounded-translation-scenario-fuzz",
             "role": "behavioral-witness",
             "result": "pass" if scen_ok else "fail",
             "detail": f"{n} sampled inputs"
                       + ("" if scen_ok else "; " + "; ".join(details[:3]))}]
    if ctype == "monitor-cert":
        # Certify an emitted LTLf MONITOR DFA (generators.monitor_gen output).
        # Two independent decision procedures for the SAME action-atom LTLf
        # semantics, over every trace up to the length bound:
        #   channel 1 = the BAKED table (read from monitor.py, never executed)
        #               vs. the SMT LTLf semantics -- Z3 AND CVC5 both assert the
        #               two never disagree (unsat); a mutated table is refuted;
        #   channel 2 = the baked table walk vs. the INDEPENDENT live flloat
        #               stepper (ref_stepper.py), on every trace in the sandbox.
        # An ACCEPTANCE/transition mutation in the shipped monitor.py is caught by
        # BOTH channels (acceptance is dual-checked, SMT + flloat).  A pending-only
        # mutation (the _PERMANENT/_LIVE reachability sets) is caught by the flloat
        # channel alone -- the SMT channel encodes bounded-trace acceptance, not the
        # reachability property `pending` is (see kernel/backends.check_monitor_
        # crosscheck).  This is an action-atom-only contract (flloat and SMT are
        # truly independent here); context-predicate temporal demands are SMT-only.
        from generators import monitor_gen as _mg, ltlf_smt as _lt
        files = artifact.get("files", {})
        parsed = _mg.parse_monitor_module(files["monitor.py"])
        max_len = int(contract.get("max_len", 4))
        obl = _lt.monitor_agreement_smtlib(
            parsed["TABLE"], parsed["INITIAL"], parsed["ACCEPTING"],
            contract["kind"], contract["params"], contract["alphabet"], max_len)
        z = _smt.run_z3(obl); z["backend"] = "z3-ltlf-agreement"
        z["role"] = "smt-proof"
        c = _smt.run_cvc5(obl); c["backend"] = "cvc5-ltlf-agreement"
        c["role"] = "smt-proof"
        cross = _hyp.check_monitor_crosscheck(
            files, contract["alphabet"], max_len)
        return "monitor-admission", [z, c, cross]
    if ctype == "cage-conformance":
        # A certified CAGE: arbitrary incumbent (third-party, never LLM-authored)
        # code runs behind an ingress dispatcher + egress output-contracts + the
        # OS sandbox.  Two independent evidence channels over DISJOINT input
        # classes:
        #   channel 1 = CONTAINMENT: on solver-generated violating inputs the
        #               caged system REJECTS at the exact ingress layer where the
        #               BARE (still sandboxed) incumbent would ACT.  The
        #               adjudication is EXTERNAL (trusted code in run.guarded); the
        #               incumbent never shares a process with the dispatcher, so it
        #               cannot fake the verdict.
        #   channel 2 = TRANSPARENCY: on legal runs the caged results are byte-
        #               identical to the bare incumbent (common.canonical_json), so
        #               the cage adds enforcement without altering legal behaviour.
        # The certificate names tier "monitored" and machine-readably DECLINES to
        # praise the cargo (non-empty non_claims); it certifies the cage, not the
        # incumbent.
        from generators import service_model as _svm
        cage = contract["cage"]
        m = _svm.parse_service_spec(contract["spec_text"])
        channels = [_hyp.check_cage_containment(cage, m),
                    _hyp.check_cage_transparency(cage, m)]
        return "cage-admission", channels
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
    if ctype == "tier-classification":
        # P5.1: classify a protocol's CONTROL SKELETON (control states + action-
        # labelled transitions, IGNORING guards / integer context / stack) as
        # star-free or not, via generators.monoid's DUAL, genuinely-independent
        # channels -- channel 1 = transition-monoid aperiodicity (m^k==m^(k+1)),
        # channel 2 = a counter-free r-cycle search on the minimal DFA (a
        # different algorithm for the same property, the z3-vs-cvc5 independence
        # grade).  Both are pure/z3-free, so they run in-process (no sandbox, no
        # solver).  This is a NON-pooled direct-path contract (like monitor-cert /
        # vpl-differential): not in POOL_SUPPORTED, no channel_specs/run_channel.
        #
        # The obligation is "classify", so map to the kernel result vocab by
        # AGREEMENT, not by the answer: both channels concurring (both star-free,
        # OR both not-star-free) => pass => Certificate whose claim names the tag;
        # a channel SPLIT (never on correct code) => pass/fail so adjudicate emits
        # the dual-checker 'disagreement' verdict (+ event_sink); a pushdown
        # skeleton or the |Q|>8 / cap cliff => 'unknown' on both, an honest non-
        # certificate (protocol-cert's temporal-unknown pattern) -- NOT a failure,
        # NOT a false star-free claim.  role='monoid-proof' marks the two as the
        # SAME obligation.
        res = _tier_classify(contract["spec_text"])
        ch1, ch2 = res["channels"][0], res["channels"][1]
        r1, r2 = ch1["result"], ch2["result"]
        if "unclassified" in (r1, r2):
            chans = [{"backend": c["backend"], "result": "unknown",
                      "role": "monoid-proof",
                      "detail": f"tier-unclassified: {str(c.get('detail', ''))[:400]}"}
                     for c in (ch1, ch2)]
        else:
            # agreement -> both pass (the tag rides on the cert's claims/tier);
            # split -> pass/fail so the generic dual-checker disagreement fires.
            results = ["pass", "pass"] if r1 == r2 else ["pass", "fail"]
            chans = [{"backend": c["backend"], "result": rr, "role": "monoid-proof",
                      "detail": str(c.get("detail", ""))[:400]}
                     for c, rr in zip((ch1, ch2), results)]
        return "tier-classification-admission", chans
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
    if ctype == "statement-cert":
        # FORMALIZATION F0.2 -- certify a COMPILED Lean statement (from F1) with
        # `:= sorry` as its placeholder proof.  NON-POOLED, direct-path (like
        # monitor-cert / tier-classification): not in POOL_SUPPORTED, no
        # channel_specs/run_channel.
        #   channel 1 (run 1 + run 2 per L5): sandboxed elaboration succeeds AND
        #     the run-2 trusted audit shows `sorryAx` present with every other
        #     axiom in the standard three, PLUS the pp-roundtrip sub-check (⚠D6).
        #     Labeled `kernel-family` (L4) -- NOT an independent channel from
        #     lean4checker replay (⚠T3), so it is only channel 1.
        #   channels 2+ = the tool-independent FIDELITY gates (F2.1 non-vacuity +
        #     F2.2 entailed instances), computed by the pipeline (WP-H).  Their
        #     passage is what makes the dual-checker rule genuinely met by
        #     DISJOINT evidence (⚠T3), not two kernel-family passes.
        # With Lean absent channel 1 is `unknown` -> NO certificate (honest),
        # even when every fidelity channel passes: no false green without the
        # kernel.
        ch1 = _lean_kernel_channel(contract["lean_text"], expect_sorry=True,
                                   forbid_sorry=False, contract=contract)
        fidelity = list(contract.get("fidelity_channels", []))
        return "statement-cert-admission", [ch1] + fidelity
    if ctype == "proof-cert":
        # FORMALIZATION F0.3 -- certify a statement + PROOF artifact (tactic
        # script or term).  NON-POOLED, direct-path.  channel 1 = sandboxed
        # `lake` build accepts (run 1, expect_sorry=False) + the run-2 trusted
        # audit shows NO `sorryAx` and axioms subset of the standard three (⚠T2:
        # this catches an axiom smuggled via Lean.addDecl with no `axiom` token --
        # the environment audit is the axiom defense, NOT the escape gate); plus
        # the pp-roundtrip sub-check (⚠D6).  channels 2+ = the fidelity gates.
        # lean4lean, when pinned, participates as an additional run-2 channel and
        # upgrades independence to `kernel-independent` (L4).  tier kernel-checked.
        ch1 = _lean_kernel_channel(contract["lean_text"], expect_sorry=False,
                                   forbid_sorry=True, contract=contract)
        fidelity = list(contract.get("fidelity_channels", []))
        return "proof-cert-admission", [ch1] + fidelity
    raise ValueError(f"unknown contract type {ctype}")

"""Kernel evidence backends.  Each wraps one outsourced checker.

  * HypothesisBackend -- property-based testing of the *actual emitted
    artifact*, executed only inside the OS sandbox.
  * DafnyBackend -- Dafny/Z3 verification of generated proof obligations.
  * SmtBackend -- the same SMT-LIB obligation given independently to Z3 and
    CVC5 (used for pure-logic contracts and for engineering/detecting
    solver disagreements).

Backends return plain dicts {backend, result, detail, ...}; the kernel
adjudicates.  result is one of "pass", "fail", "unknown", "error".
"""
from __future__ import annotations

import json
import pathlib
import re
import tempfile

import common
from sandbox import Sandbox
from generators import harness_gen, dafny_gen, refcodec, toolgen


class HypothesisBackend:
    name = "hypothesis"

    def check_codec(self, files: dict, spec_model, max_examples=100) -> dict:
        harness = harness_gen.build_harness(spec_model, max_examples=max_examples)
        with Sandbox() as sb:
            for name, data in files.items():
                sb.add_file(name, data)
            sb.add_file("harness.py", harness)
            res = sb.run(["python3", "harness.py"], timeout=180, cpu_seconds=120)
            out = {}
            try:
                out = json.loads(res.stdout.decode().strip().splitlines()[-1])
            except Exception:
                pass
            if res.ok and out.get("status") == "pass":
                return {"backend": self.name, "result": "pass",
                        "role": "behavioral-witness",
                        "detail": f"{out.get('examples')} derandomized examples,"
                                  " roundtrip+truncation+corruption properties"}
            return {"backend": self.name, "result": "fail",
                    "role": "behavioral-witness",
                    "detail": out.get("error", "")[:1500] or
                              res.stderr[-1500:].decode(errors="replace"),
                    "transcript": out,
                    "harness_stderr": res.stderr[-2000:].decode(errors="replace")}

    def check_differential(self, files: dict, spec_model, max_examples=100,
                           ref_fields=None) -> dict:
        """Path (i): diff the Kaitai-emitted codec against the independent
        reference codec on spec-generated inputs, inside the sandbox.  Catches
        jointly-consistent-but-wrong errors that self-round-trip misses.  When
        ref_fields is given, the reference side uses an independently-derived
        field list (the rung differential), catching mapper/codec-generation
        divergence, not just codec bugs."""
        harness = refcodec.build_differential_harness(
            spec_model, max_examples=max_examples, ref_fields=ref_fields)
        with Sandbox() as sb:
            for name, data in files.items():
                sb.add_file(name, data)
            sb.add_file("ref.py", refcodec.ref_module_source())
            sb.add_file("diff_harness.py", harness)
            res = sb.run(["python3", "diff_harness.py"], timeout=180,
                         cpu_seconds=120)
            out = {}
            try:
                out = json.loads(res.stdout.decode().strip().splitlines()[-1])
            except Exception:
                pass
            if res.ok and out.get("status") == "pass":
                return {"backend": "kaitai-vs-reference", "result": "pass",
                        "role": "cross-impl-differential",
                        "detail": f"{out.get('examples')} inputs; two independent "
                                  "codec implementations agree byte-for-byte "
                                  "and cross-decode"}
            return {"backend": "kaitai-vs-reference", "result": "fail",
                    "role": "cross-impl-differential",
                    "detail": out.get("error", "")[:1500] or
                              res.stderr[-1500:].decode(errors="replace"),
                    "transcript": out}

    def check_vpl_differential(self, files: dict, depth_bound=4,
                               max_examples=100) -> dict:
        """vpl-differential channel 1: diff, on bounded-depth recursive JSON
        values inside the sandbox, THREE genuinely-independent DECODERS -- the
        tree-sitter parser tree-walk, the from-scratch recursive-descent decoder,
        and stdlib json -- requiring decode + cross-decode agreement.  Encode
        agreement is anchored by stdlib json (the two hand-written serializers
        share the one canonical output form, so the independent encode witness is
        stdlib, not a third implementation).  Depth is capped (named on the
        certificate) so deep inputs cannot become opaque sandbox crashes."""
        from generators import json_codec
        harness = json_codec.build_vpl_differential_harness(depth_bound, max_examples)
        with Sandbox() as sb:
            for name, data in files.items():
                sb.add_file(name, data)
            sb.add_file("tswalk.py", json_codec.ts_walk_source())
            sb.add_file("rd.py", json_codec.rd_source())
            sb.add_file("diff_harness.py", harness)
            res = sb.run(["python3", "diff_harness.py"], timeout=180,
                         cpu_seconds=120)
            out = {}
            try:
                out = json.loads(res.stdout.decode().strip().splitlines()[-1])
            except Exception:
                pass
            if res.ok and out.get("status") == "pass":
                return {"backend": "tree-sitter-vs-recursive-descent",
                        "result": "pass", "role": "cross-impl-differential",
                        "detail": f"depth<={depth_bound}; {out.get('examples')} "
                                  "recursive JSON values; three independent "
                                  "decoders (tree-sitter walk, recursive-descent, "
                                  "stdlib) agree on decode + cross-decode; encode "
                                  "agreement is stdlib-anchored"}
            return {"backend": "tree-sitter-vs-recursive-descent",
                    "result": "fail", "role": "cross-impl-differential",
                    "detail": out.get("error", "")[:1500] or
                              res.stderr[-1500:].decode(errors="replace"),
                    "transcript": out}

    def check_vpl_membership(self, files: dict, depth_bound=4,
                             max_examples=100) -> dict:
        """vpl-differential channel 2: membership differential on structurally
        MUTATED inputs (bracket deletion/swap/truncation -> visibly-pushdown
        membership violations).  The tree-sitter decider (has_error) and the
        independent recursive-descent decider must agree on every mutation, and
        malformed inputs must be rejected by both.  Independent of channel 1: it
        exercises the NEGATIVE/illegal input class, not round-trip."""
        from generators import json_codec
        harness = json_codec.build_vpl_membership_harness(depth_bound, max_examples)
        with Sandbox() as sb:
            for name, data in files.items():
                sb.add_file(name, data)
            sb.add_file("tswalk.py", json_codec.ts_walk_source())
            sb.add_file("rd.py", json_codec.rd_source())
            sb.add_file("mutate.py", json_codec.mutate_source())
            sb.add_file("mem_harness.py", harness)
            res = sb.run(["python3", "mem_harness.py"], timeout=180,
                         cpu_seconds=120)
            out = {}
            try:
                out = json.loads(res.stdout.decode().strip().splitlines()[-1])
            except Exception:
                pass
            if res.ok and out.get("status") == "pass":
                return {"backend": "membership-ts-vs-recursive-descent",
                        "result": "pass", "role": "cross-impl-differential",
                        "detail": f"depth<={depth_bound}; {out.get('examples')} "
                                  "values x structural mutations; tree-sitter "
                                  "(has_error) and recursive-descent agree on "
                                  "membership; malformed inputs rejected by both"}
            return {"backend": "membership-ts-vs-recursive-descent",
                    "result": "fail", "role": "cross-impl-differential",
                    "detail": out.get("error", "")[:1500] or
                              res.stderr[-1500:].decode(errors="replace"),
                    "transcript": out}

    def check_tool(self, files: dict, schema_text, max_examples=100) -> dict:
        """Tool contract, channel 1: the emitted Pydantic validator satisfies
        round-trip + rejection on hypothesis-jsonschema instances (sandboxed)."""
        harness = toolgen.build_tool_harness(schema_text, max_examples=max_examples)
        return self._run_tool_harness(files, {"harness.py": harness}, "harness.py",
                                      "pydantic-validator")

    def check_tool_differential(self, files: dict, schema_text,
                                max_examples=100) -> dict:
        """Tool contract, channel (i): the Pydantic validator and the
        independent jsonschema-library validator accept iff each other, on the
        same generated + mutated instances (sandboxed)."""
        harness = toolgen.build_tool_differential_harness(
            schema_text, max_examples=max_examples)
        ref = toolgen.emit_reference_validator(schema_text)
        extra = dict(ref)
        extra["diff_harness.py"] = harness
        return self._run_tool_harness(files, extra, "diff_harness.py",
                                      "pydantic-vs-jsonschema",
                                      role="cross-impl-differential")

    def check_protocol_conformance(self, files, model, K) -> dict:
        """Protocol validator-conformance: the emitted session validator agrees
        with an independent reference simulator on solver-generated legal traces
        and guard-violating / wrong-state illegal ones (N-version on traces)."""
        from generators import protocol_gen as pg
        cases = pg.conformance_traces(model, K)
        extra = pg.build_conformance_harness(model, cases)
        return self._run_tool_harness(files, extra, "conf_harness.py",
                                      "validator-vs-refsim",
                                      role="cross-impl-differential")

    def check_constraint_boundary(self, files, inputs) -> dict:
        """Solver-as-adversary channel: run the emitted validator (sandboxed)
        on Z3-generated boundary inputs -- one satisfying model plus the
        tightest per-constraint violation -- and require accept/reject to match
        the solver's verdict.  Also enforces non-vacuity: at least one valid
        input must exist (constraints not UNSAT)."""
        from generators import constraint_gen as cg
        if not any(exp for _, exp in inputs):
            return {"backend": "solver-boundary", "result": "fail",
                    "role": "cross-impl-differential",
                    "detail": "vacuous contract: constraints are UNSAT, no "
                              "valid input exists"}
        harness = cg.build_boundary_harness(inputs)
        return self._run_tool_harness(files, {"boundary_harness.py": harness},
                                      "boundary_harness.py", "solver-boundary",
                                      role="cross-impl-differential")

    def check_service_conformance(self, files, model) -> dict:
        """Composition channel (i): the composed dispatcher agrees, accept for
        accept and reject for reject, with an INDEPENDENT jsonschema-based
        reference service (separately authored, no shared code) on generated
        call sequences that exercise every layer -- so a dispatcher that drops
        or misorders a certified layer is caught."""
        from generators import service_gen as sg
        extra = sg.build_service_conformance(model)
        return self._run_tool_harness(files, extra, "conf_harness.py",
                                      "dispatcher-vs-refservice",
                                      role="cross-impl-differential")

    def check_service_liveness(self, files, model) -> dict:
        """Composition channel (ii), non-vacuity: the composed dispatcher must
        ACCEPT a full legal run (the golden path).  Without this a dispatcher
        that rejects everything would trivially agree with a reference on the
        negative cases; liveness forces the composition to admit real work."""
        from generators import service_gen as sg
        extra = sg.build_service_liveness(model)
        return self._run_tool_harness(files, extra, "live_harness.py",
                                      "service-liveness",
                                      role="behavioral-witness")

    def check_intent_dispatcher(self, files, scenarios) -> dict:
        """Intent channel 1: the certified dispatcher replays the independently-
        authored scenario traces (LLM-derived from the REQUEST, not the spec's
        semantics) and must reproduce their accept/reject expectations."""
        from generators import service_gen as sg
        extra = sg.build_scenario_dispatcher_harness(scenarios)
        return self._run_tool_harness(files, extra, "scn_harness.py",
                                      "dispatcher-vs-scenarios",
                                      role="behavioral-witness")

    def check_intent_reference(self, files, model, scenarios) -> dict:
        """Intent channel 2: the INDEPENDENT reference service (a second
        interpreter of the same spec, no shared code) replays the same
        scenarios; both implementations must match the same expectations, so a
        spec whose semantics diverge from the request's is caught by two
        independent artifacts, not one."""
        from generators import service_gen as sg
        extra = sg.build_scenario_reference_harness(model, scenarios)
        return self._run_tool_harness(files, extra, "scn_ref_harness.py",
                                      "reference-vs-scenarios",
                                      role="cross-impl-differential")

    def check_monitor_crosscheck(self, files, alphabet, max_len) -> dict:
        """monitor-cert channel 2: run the BAKED monitor table (monitor.py) and
        the INDEPENDENT live flloat stepper (ref_stepper.py) on every action
        trace up to max_len inside the sandbox; they must agree on BOTH
        `accepting` and `pending`.  This is a cross-implementation differential
        -- table walk vs. flloat automaton -- so a mutation in either
        implementation is caught here.

        CHANNEL DIVISION OF LABOUR (honest scope): `accepting` is DUAL-checked --
        both this flloat crosscheck AND the SMT LTLf-agreement channel
        (ltlf_smt.monitor_agreement_smtlib, Z3 & CVC5) verify it, the latter
        against the LTLf formula semantics.  `pending` (the reachability-derived
        _LIVE/_PERMANENT bit driving the dispatcher's refuse-terminal-while-
        pending) is encoded ONLY in the flloat channel; the SMT channel asserts
        acceptance agreement only.  So a mutation touching ONLY the pending sets
        is caught by THIS channel alone, not by both -- pending is
        cross-checked (table vs. flloat), while acceptance is dual-checked."""
        from generators import monitor_gen as mg
        harness = mg.build_crosscheck_harness(alphabet, max_len)
        return self._run_tool_harness(files, {"crosscheck_harness.py": harness},
                                      "crosscheck_harness.py",
                                      "monitor-vs-flloat",
                                      role="cross-impl-differential")

    def check_macro_compile_identity(self, inlined_spec, expanded_spec) -> dict:
        """macro-expansion-cert channel 1: the macro-EXPANDED reading and the
        hand-INLINED reading must compile to the SAME service meta-spec, byte for
        byte.  A pure, deterministic, z3-free / sandbox-free comparison of the two
        compositional-compiler outputs (compile is trusted like the reference
        codec, see TRUST 1.2e); a macro that expands to a DIFFERENT spec is
        refuted here.  A cross-implementation differential in spirit -- two
        independently-authored readings, one compiler, equal artifact."""
        h_in = common.sha256_bytes(inlined_spec.encode())
        h_ex = common.sha256_bytes(expanded_spec.encode())
        if h_in == h_ex:
            return {"backend": "macro-compile-identity", "result": "pass",
                    "role": "cross-impl-differential",
                    "detail": f"expanded compile-hash == inlined compile-hash "
                              f"({h_ex[:16]}...)"}
        return {"backend": "macro-compile-identity", "result": "fail",
                "role": "cross-impl-differential",
                "detail": f"expanded spec differs from the hand-inlined spec: "
                          f"expanded={h_ex[:16]}... inlined={h_in[:16]}...",
                "transcript": {"error": "macro expansion is not identical to the "
                                        "hand-inlined reading",
                               "observed": expanded_spec[:1000],
                               "expected": inlined_spec[:1000]}}

    def check_macro_scenario_replay(self, files, scenarios) -> dict:
        """macro-expansion-cert channel 2: replay, inside the sandbox, the
        scenarios the INLINED reading's demands solver-ENTAIL against the
        EXPANDED reading's emitted dispatcher; it must reproduce every accept/
        reject expectation.  Behavioural N-version evidence, disjoint from
        channel 1's syntactic hash check: a bad macro whose dispatcher drops a
        guard accepts a call the inlined demand entailed as a rejection, and is
        caught here even though it also fails channel 1."""
        from generators import service_gen as sg
        extra = sg.build_scenario_dispatcher_harness(scenarios)
        return self._run_tool_harness(files, extra, "scn_harness.py",
                                      "expanded-dispatcher-vs-inlined-scenarios",
                                      role="behavioral-witness")

    def check_cage_containment(self, cage, model) -> dict:
        """cage-conformance channel 1 (containment): the cage REJECTS contract-
        violating calls exactly where the bare-but-sandboxed incumbent would ACT,
        on solver-generated violating inputs.  The comparison happens in TRUSTED
        code (run.guarded, outside every sandbox) -- the incumbent never shares a
        process with the dispatcher, so it cannot fake the containment verdict.
        A behavioral witness: it observes the real caged pipeline rejecting."""
        from run import guarded
        rep = guarded.containment_report(cage, model)
        return {"backend": "cage-containment", "role": "behavioral-witness",
                "result": "pass" if rep["pass"] else "fail",
                "detail": rep["detail"][:1500]}

    def check_cage_transparency(self, cage, model) -> dict:
        """cage-conformance channel 2 (transparency): on legal runs the caged
        results equal the bare incumbent's, compared via common.canonical_json
        (never raw json.dumps -- dict order/floats would spuriously diverge).  A
        cross-implementation differential -- caged pipeline vs. bare incumbent --
        over the LEGAL input class, disjoint from channel 1's violating class."""
        from run import guarded
        rep = guarded.transparency_report(cage, model)
        return {"backend": "cage-transparency", "role": "cross-impl-differential",
                "result": "pass" if rep["pass"] else "fail",
                "detail": rep["detail"][:1500]}

    def check_incumbent_differential(self, files, schema_text, incumbent_files,
                                     max_examples=100) -> dict:
        """Schema-lift channel (i): the inferred-schema validator agrees with
        the INCUMBENT validator (the ground-truth anchor) on accept/reject."""
        harness = toolgen.build_incumbent_differential_harness(
            schema_text, max_examples=max_examples)
        extra = dict(incumbent_files)
        extra["inc_harness.py"] = harness
        return self._run_tool_harness(files, extra, "inc_harness.py",
                                      "inferred-vs-incumbent",
                                      role="cross-impl-differential")

    def _run_tool_harness(self, files, extra, entry, backend, role=None):
        with Sandbox() as sb:
            for name, data in files.items():
                sb.add_file(name, data)
            for name, data in extra.items():
                sb.add_file(name, data if isinstance(data, bytes) else data.encode())
            res = sb.run(["python3", entry], timeout=180, cpu_seconds=120)
            out = {}
            try:
                out = json.loads(res.stdout.decode().strip().splitlines()[-1])
            except Exception:
                pass
            r = {"backend": backend}
            if role:
                r["role"] = role
            if res.ok and out.get("status") == "pass":
                r.update(result="pass",
                         detail=f"{out.get('examples')} schema-generated instances")
                return r
            r.update(result="fail",
                     detail=out.get("error", "")[:1500] or
                            res.stderr[-1500:].decode(errors="replace"),
                     transcript=out)
            return r

    def replay_corpus(self, files: dict, spec_model, inputs_hex: list) -> dict:
        """Deterministically replay stored counterexample inputs (no fresh
        generation).  Contract: decode must reject, or roundtrip canonically."""
        cls = harness_gen._class_name(spec_model.id)
        replay = f"""
import io, json, sys
from kaitaistruct import KaitaiStream
from {spec_model.id} import {cls}
inputs = {inputs_hex!r}
for hx in inputs:
    raw = bytes.fromhex(hx)
    try:
        obj = {cls}.from_bytes(raw)
        obj._read()
    except Exception:
        continue
    try:
        obj._check()
        ks = KaitaiStream(io.BytesIO(bytearray(1 << 20)))
        obj._write(ks)
        enc = ks.to_byte_array()[:ks.pos()]
    except Exception as e:
        print(json.dumps({{"status": "fail", "failing_input": hx,
                          "error": "decoded object cannot re-encode: " + repr(e)[:500]}}))
        sys.exit(1)
    if enc != raw:
        print(json.dumps({{"status": "fail", "failing_input": hx,
                          "error": "non-canonical decode: re-encode differs",
                          "observed": enc.hex(), "expected": hx}}))
        sys.exit(1)
print(json.dumps({{"status": "pass", "examples": len(inputs)}}))
"""
        with Sandbox() as sb:
            for name, data in files.items():
                sb.add_file(name, data)
            sb.add_file("replay.py", replay)
            res = sb.run(["python3", "replay.py"], timeout=120)
            try:
                out = json.loads(res.stdout.decode().strip().splitlines()[-1])
            except Exception:
                out = {}
            if res.ok and out.get("status") == "pass":
                return {"backend": "corpus-replay", "result": "pass",
                        "detail": f"replayed {len(inputs_hex)} stored counterexamples"}
            return {"backend": "corpus-replay", "result": "fail",
                    "detail": out.get("error", res.stderr[-800:].decode(errors='replace')),
                    "transcript": out}


class DafnyBackend:
    name = "dafny"

    def __init__(self):
        self.version = "4.11.0"

    def verify_text(self, dfy_text: str, time_limit=90) -> dict:
        with tempfile.TemporaryDirectory(prefix="cgb-dfy-") as td:
            p = pathlib.Path(td) / "obligation.dfy"
            p.write_text(dfy_text)
            proc = common.run_cmd(
                [common.DAFNY, "verify", "--cores", "4",
                 f"--verification-time-limit", str(time_limit), str(p)],
                timeout=time_limit * 10 + 120)
            out = (proc.stdout or b"").decode(errors="replace")
            if proc.returncode == 0 and "0 errors" in out and " verified" in out:
                return {"backend": self.name, "result": "pass",
                        "detail": out.strip().splitlines()[-1]}
            result = "unknown" if ("time out" in out or "timed out" in out) else "fail"
            return {"backend": self.name, "result": result,
                    "detail": out[-2000:]}

    def check_codec_spec(self, spec_model) -> dict:
        """Channel #2 of an emission check: prove the contract model (round
        trip + truncation rejection) for this concrete task spec."""
        return self.verify_text(dafny_gen.per_spec_obligation(spec_model))

    def check_universal(self, grammar_atoms: frozenset) -> dict:
        try:
            text = dafny_gen.universal_obligation(grammar_atoms)
        except ValueError as e:
            return {"backend": self.name, "result": "fail", "detail": str(e)}
        return self.verify_text(text, time_limit=120)


class SmtBackend:
    """Feeds the same SMT-LIB obligation to Z3 and CVC5 independently.

    An obligation is a proof goal: we assert its negation and expect *unsat*
    from both solvers.  sat => refuted, unknown/timeout => no verdict.

    The z3 and cvc5 Python bindings use process-global solver state that is not
    thread-safe, so a module lock serializes SMT calls.  This costs effectively
    nothing -- these obligations are decidable QF_LIA / bounded and settle in
    milliseconds -- while the expensive, process-isolated sandbox (Hypothesis)
    and Dafny channels still run fully in parallel when the orchestrator fans
    layers out across threads.
    """
    name = "smt"
    _lock = common.SMT_LOCK

    @staticmethod
    def _verdict(r: str, expect: str) -> str:
        """expect='unsat': a proof goal (negation refuted).  expect='sat': a
        consistency goal (a model must exist).  unknown never passes."""
        if r == "unknown":
            return "unknown"
        return "pass" if r == expect else "fail"

    def run_z3(self, smtlib: str, timeout_ms=15000, expect="unsat") -> dict:
        import z3
        with self._lock:
            try:
                s = z3.Solver()
                s.set("timeout", timeout_ms)
                s.add(z3.parse_smt2_string(smtlib))
                r = str(s.check())
                return {"backend": "z3", "result": self._verdict(r, expect),
                        "detail": f"z3 says {r} (expected {expect})",
                        "solver_version": z3.get_version_string()}
            except Exception as e:
                return {"backend": "z3", "result": "error",
                        "detail": repr(e)[:800]}

    def run_cvc5(self, smtlib: str, timeout_ms=15000, expect="unsat") -> dict:
        import cvc5
        with self._lock:
            try:
                slv = cvc5.Solver()
                slv.setOption("tlimit-per", str(timeout_ms))
                parser = cvc5.InputParser(slv)
                parser.setStringInput(
                    cvc5.InputLanguage.SMT_LIB_2_6, smtlib, "obligation.smt2")
                sm = parser.getSymbolManager()
                r = None
                while True:
                    cmd = parser.nextCommand()
                    if cmd.isNull():
                        break
                    out = cmd.invoke(slv, sm)
                    if out.strip():
                        r = out.strip()
                head = (r or "").split()[0] if r else ""
                result = self._verdict(head, expect) \
                    if head in ("sat", "unsat", "unknown") else "error"
                ver = slv.getVersion()
                if isinstance(ver, bytes):
                    ver = ver.decode(errors="replace")
                return {"backend": "cvc5", "result": result,
                        "detail": f"cvc5 says {r} (expected {expect})",
                        "solver_version": ver}
            except Exception as e:
                return {"backend": "cvc5", "result": "error",
                        "detail": repr(e)[:800]}


class LeanBackend:
    """F0.5 runner -- Lean 4 + pinned Mathlib as an outsourced checker binary.

    API frozen as F-H.  Three methods, each honoring the two-run adjudication
    rule L5:

      * elaborate(lean_text, *, expect_sorry) -> {ok, olean_path,
        transcript_path, unavailable}  -- RUN 1 (UNTRUSTED).  Sandboxed
        `lake build`; its outputs (.olean, transcripts) are *artifacts, not
        evidence*, and its exit code is a liveness signal only, because
        elaboration-time code can write any file in the scratch dir including a
        forged driver result (sandbox/__init__.py -- the payload owns the only
        writable path).
      * recheck(olean_path) -> {ok, axioms:[str], transcript, unavailable}
        -- RUN 2 (TRUSTED, the ONLY source of verdict-bearing facts, L5).
        lean4checker replays the exported environment as DATA; the axiom audit
        is enumerated by this trusted pass via `Lean.collectAxioms` emitting
        canonical JSON -- `#print axioms` text is never parsed (⚠D5).
      * eval_props(header, props) -> [{prop, closed_by, value, unavailable}]
        -- the F2.2/F2.3 discharge ladder decide -> omega -> norm_num -> simp
        (-> exact? for the tripwire), each under a pinned maxHeartbeats,
        two-run, with the sandbox wall-clock/rlimit as the authoritative bound
        (⚠D7).

    L1 containment: NO Lean text is LLM-authored -- the compiler emits it, this
    gate re-checks it (defense in depth), the sandbox runs it, and no
    verdict-bearing fact leaves a process where untrusted bytes executed.  ALL
    subject-byte execution goes through the OS sandbox (network off via
    `unshare --net`).  Every network-touching lake/elan operation is
    setup-time-only (⚠T9); cert-time is sandbox-only.

    Availability: this container has no Lean toolchain, so every method
    degrades to an honest `unavailable` result (never a crash).  The code is
    written to run correctly WHEN a real toolchain is present; the honest
    degradation is the guard at the top of each method.

    Content-addressed caching (L2): an optional `cache` handle (get/put) keys
    verdicts by (statement bytes, proof bytes, import set, toolchain hash,
    Mathlib commit, escape-gate source hash, runner/driver source hash,
    contract).  A changed gate, driver, or pin is a clean miss, never a stale
    false-green.
    """
    name = "lean"

    def __init__(self, cache=None):
        # cache: optional object with `.get(key) -> dict|None` and
        # `.put(key, dict)`.  None disables caching (the default now, since
        # every method is unavailable).
        self._cache = cache

    # ---------------------------------------------------------- L2 identity
    @staticmethod
    def _driver_hash() -> str:
        """sha256 over this runner's own source -- the runner/driver +
        adjudication source hash L2 folds into cache identity (⚠T6)."""
        try:
            return common.sha256_bytes(pathlib.Path(__file__).read_bytes())
        except OSError:
            return common.sha256_bytes(b"")

    def _cache_key(self, contract: str, statement_bytes: bytes,
                   proof_bytes: bytes = b"") -> str:
        ident = {
            "contract": contract,
            "statement_sha": common.sha256_bytes(statement_bytes),
            "proof_sha": common.sha256_bytes(proof_bytes),
            "imports": list(common.MATHLIB_IMPORTS),
            "toolchain_hash": common.lean_toolchain_hash(),
            "mathlib_commit": common.MATHLIB_COMMIT,
            "gate_hash": common.validate_lean_hash(),
            "driver_hash": self._driver_hash(),
        }
        return "lean:" + common.sha256_json(ident)

    def _cache_get(self, key):
        if self._cache is None:
            return None
        try:
            return self._cache.get(key)
        except Exception:
            return None

    def _cache_put(self, key, value):
        if self._cache is None:
            return
        try:
            self._cache.put(key, value)
        except Exception:
            pass

    @staticmethod
    def _unavailable(extra: dict) -> dict:
        base = {"ok": False, "unavailable": True, "reason": "lean toolchain absent"}
        base.update(extra)
        return base

    # ------------------------------------------------------------- scratch pkg
    # Jail paths for the read-only mounts (sandbox.Sandbox(ro_mounts=...)): the
    # Mathlib checkout, the RESOLVED toolchain (bypassing elan's writable-home
    # proxies), and the lean4checker build.  The lakefile references the JAIL
    # path, never the host path, so the package is position-independent.
    _RO_MATHLIB = "/ro/mathlib"
    _RO_TOOLCHAIN = "/ro/toolchain"
    _RO_CHECKER = "/ro/lean4checker"

    def _lean_mounts(self, *, checker: bool = False):
        """The ro_mounts dict for a Lean sandbox, or None (with a reason) when a
        required setup-time directory is missing -- an honest degradation, never
        a crash inside the jail."""
        mounts = {"mathlib": common.LEAN_MATHLIB_DIR,
                  "toolchain": common.LEAN_TOOLCHAIN_DIR}
        if checker:
            mounts["lean4checker"] = common.LEAN4CHECKER_DIR
        missing = [p for p in mounts.values() if not pathlib.Path(p).exists()]
        if missing:
            return None, f"setup-time checkout(s) missing: {missing}"
        return mounts, ""

    def _lean_run_kw(self) -> dict:
        """run() kwargs common to every in-jail Lean invocation: the toolchain
        bin on PATH, Mathlib's build lib on LEAN_PATH (import resolution for
        direct `lean`/lean4checker invocations; `lake` sets its own), and the
        EXPLICIT sysroot/home overrides so lake/lean never fall back to the
        /proc/self/exe path heuristic to locate their installation."""
        return {"extra_path": (self._RO_TOOLCHAIN + "/bin",),
                "extra_env": {"LEAN_PATH": self._RO_MATHLIB + "/.lake/build/lib",
                              "LEAN_SYSROOT": self._RO_TOOLCHAIN,
                              "LAKE_HOME": self._RO_TOOLCHAIN}}

    def _scratch_package(self, sb, lean_text: str) -> None:
        """Materialize a one-file scratch Lake package inside the sandbox scratch
        dir (F0.5): pinned `lean-toolchain`, a committed `lake-manifest.json`,
        a `require`-Mathlib-by-LOCAL-PATH lakefile with NO-UPDATE semantics, and
        the subject `.lean` (narrow imports + body).  No lake invocation may
        resolve dependencies or touch the network (⚠D3) -- the manifest is
        committed, the require points at the READ-ONLY jail mount
        (/ro/mathlib, sandbox ro_mounts), and `unshare --net` makes any fetch
        attempt fail at the OS level anyway."""
        imports = "\n".join(f"import {m}" for m in common.MATHLIB_IMPORTS)
        sb.add_file("lean-toolchain", common.LEAN_TOOLCHAIN + "\n")
        # NB: `package «x» where` / `lean_lib «x» where` with ZERO fields is a
        # Lean parse error -- the field-less declarations take no `where`.
        sb.add_file("lakefile.lean",
                    'import Lake\nopen Lake DSL\n'
                    'package «cgb_scratch»\n'
                    f'require mathlib from "{self._RO_MATHLIB}"\n'
                    '@[default_target] lean_lib «CgbScratch»\n')
        # A committed manifest keeps `lake build` offline; the real bytes are
        # copied from the setup-time checkout at cert time.
        sb.add_file("lake-manifest.json",
                    common.canonical_json({"version": "1.1.0", "packages": []}))
        sb.add_file("CgbScratch.lean", imports + "\n" + lean_text + "\n")

    # ---------------------------------------------------- run 1: elaborate
    def elaborate(self, lean_text: str, *, expect_sorry: bool) -> dict:
        """RUN 1 (UNTRUSTED).  Returns artifacts only -- {ok, olean_path,
        transcript_path, unavailable}.  Verdict-bearing facts come from
        recheck() (run 2), never from here (L5)."""
        if not common.lean_available():
            return self._unavailable({"olean_path": None, "transcript_path": None})

        # defense in depth: re-check even the compiler's own output (F0.4).
        from buildloop import validate_lean
        ok, reason = validate_lean.validate_lean(lean_text)
        if not ok:
            return {"ok": False, "unavailable": False, "olean_path": None,
                    "transcript_path": None,
                    "reason": f"escape-gate refusal: {reason}"}

        key = self._cache_key(f"elaborate:sorry={bool(expect_sorry)}",
                              lean_text.encode())
        hit = self._cache_get(key)
        if hit is not None:
            return hit

        mounts, why = self._lean_mounts()
        if mounts is None:
            return {"ok": False, "unavailable": False, "olean_path": None,
                    "transcript_path": None, "reason": why}

        # rlimits sized for a NARROW-import elaboration (⚠D4/D15): full-Mathlib
        # would need ~4--6 GB; the narrow set is far cheaper but we keep headroom.
        with Sandbox(ro_mounts=mounts) as sb:
            self._scratch_package(sb, lean_text)
            res = sb.run(["lake", "build", "CgbScratch"],
                         timeout=1800, cpu_seconds=1200, mem_mb=6144,
                         fsize_mb=512, **self._lean_run_kw())
            transcript = (res.stdout + b"\n" + res.stderr).decode(errors="replace")
            sb.add_file("elaborate.transcript.txt", transcript)
            # lake's build layout moved build/ -> .lake/build/ across versions;
            # accept either so a layout change is a visible miss, not a false ok.
            olean_rel = next(
                (rel for rel in (".lake/build/lib/CgbScratch.olean",
                                 "build/lib/CgbScratch.olean") if sb.exists(rel)),
                ".lake/build/lib/CgbScratch.olean")
            built = sb.exists(olean_rel)
            # exit code is a LIVENESS signal only (⚠T1); the verdict is run 2's.
            result = {"ok": bool(res.ok and built),
                      "unavailable": False,
                      "olean_path": str(sb.root / olean_rel) if built else None,
                      "transcript_path": str(sb.root / "elaborate.transcript.txt"),
                      "expect_sorry": bool(expect_sorry),
                      "detail": transcript[-1500:]}
        self._cache_put(key, result)
        return result

    # ------------------------------------------------------ run 2: recheck
    def recheck(self, olean_path: str) -> dict:
        """RUN 2 (TRUSTED).  lean4checker replays the exported environment as
        DATA in a fresh sandbox where no untrusted bytes load as code; the
        axiom set is enumerated by this trusted pass (`Lean.collectAxioms` ->
        canonical JSON), never parsed from `#print axioms` text (⚠D5).  This is
        the ONLY source of verdict-bearing facts (L5)."""
        if not common.lean_available():
            return self._unavailable({"axioms": [], "transcript": None})

        key = self._cache_key("recheck", str(olean_path).encode())
        hit = self._cache_get(key)
        if hit is not None:
            return hit

        mounts, why = self._lean_mounts(checker=True)
        if mounts is None:
            return {"ok": False, "unavailable": False, "axioms": [],
                    "transcript": None, "reason": why}

        with Sandbox(ro_mounts=mounts) as sb:
            # The subject's exported .olean is copied in and replayed AS DATA;
            # lean4checker (Lean's kernel linked as a library, L4) re-typechecks
            # it and the trusted driver enumerates axioms canonically.
            try:
                sb.add_file("CgbScratch.olean", pathlib.Path(olean_path).read_bytes())
            except OSError as e:
                return {"ok": False, "unavailable": False, "axioms": [],
                        "transcript": None, "reason": f"olean unreadable: {e!r}"}
            kw = self._lean_run_kw()
            # the scratch dir joins LEAN_PATH so the checker resolves the
            # subject module alongside the read-only Mathlib oleans.
            kw["extra_env"]["LEAN_PATH"] = ("/work:" +
                                            kw["extra_env"]["LEAN_PATH"])
            res = sb.run([self._RO_CHECKER + "/.lake/build/bin/lean4checker",
                          "CgbScratch"],
                         timeout=1800, cpu_seconds=1200, mem_mb=6144, **kw)
            transcript = (res.stdout + b"\n" + res.stderr).decode(errors="replace")
            # The axiom audit is emitted by the trusted driver as canonical JSON
            # on its own channel; parse it here in TRUSTED code outside the
            # sandbox.  Absent that channel we report no verified axioms.
            axioms = []
            try:
                for line in res.stdout.decode(errors="replace").splitlines():
                    line = line.strip()
                    if line.startswith("{") and '"axioms"' in line:
                        axioms = sorted(str(a) for a in json.loads(line)["axioms"])
                        break
            except Exception:
                axioms = []
            result = {"ok": bool(res.ok), "unavailable": False,
                      "axioms": axioms, "transcript": transcript[-1500:]}
        self._cache_put(key, result)
        return result

    # ------------------------------------------- discharge / tripwire ladder
    def eval_props(self, header: str, props: list) -> list:
        """The F2.2/F2.3 ladder decide -> omega -> norm_num -> simp (-> exact?),
        each under a pinned maxHeartbeats with the sandbox wall-clock/rlimit as
        the authoritative bound (⚠D7).  Two-run: props are evaluated over the
        NARROW header via `lake env lean` (no olean needed, ⚠D15) and results
        extracted by trusted code per L5.  Returns
        [{prop, closed_by, value, unavailable}] in input order."""
        props = list(props)
        if not common.lean_available():
            return [{"prop": p, "closed_by": None, "value": "unavailable",
                     "unavailable": True} for p in props]

        # defense in depth on the header (compiler output).
        from buildloop import validate_lean
        ok, reason = validate_lean.validate_lean(header)
        if not ok:
            return [{"prop": p, "closed_by": None,
                     "value": "refused", "unavailable": False,
                     "reason": f"escape-gate refusal on header: {reason}"}
                    for p in props]

        key = self._cache_key("eval_props", header.encode(),
                              common.canonical_json(props).encode())
        hit = self._cache_get(key)
        if hit is not None:
            return hit

        mounts, why = self._lean_mounts()
        if mounts is None:
            return [{"prop": p, "closed_by": None, "value": "error",
                     "unavailable": False, "reason": why} for p in props]

        ladder = ("decide", "omega", "norm_num", "simp")
        results = []
        with Sandbox(ro_mounts=mounts) as sb:
            self._scratch_package(sb, header)
            for i, prop in enumerate(props):
                closed_by, value = None, "open"
                for rung in ladder:
                    probe = (f"set_option maxHeartbeats {common.LEAN_MAXHEARTBEATS} in\n"
                             f"example : {prop} := by {rung}\n")
                    # the probe body reuses the (gate-checked) header's imports.
                    sb.add_file(f"Probe_{i}.lean",
                                "\n".join(f"import {m}" for m in common.MATHLIB_IMPORTS)
                                + "\n" + probe)
                    res = sb.run(["lake", "env", "lean", f"Probe_{i}.lean"],
                                 timeout=300, cpu_seconds=120, mem_mb=6144,
                                 **self._lean_run_kw())
                    if res.ok:
                        closed_by, value = rung, "closed"
                        break
                results.append({"prop": prop, "closed_by": closed_by,
                                "value": value, "unavailable": False})
        self._cache_put(key, results)
        return results

    # ------------------------------------------------- pp.all round-trip (⚠D6)
    _THEOREM_NAME = re.compile(r"\btheorem\s+([A-Za-z_][A-Za-z0-9_.']*)")

    def pp_roundtrip(self, lean_text: str) -> dict:
        """⚠D6: the elaborated statement pretty-printed under `pp.all` must
        re-elaborate to a definitionally-equal term -- the silent-coercion /
        wrong-instance catcher, this plan's whole mission.  The kernel channel
        (`kernel._lean_kernel_channel`) prefers this method when present.

        NO metaprogramming and NO isDefEq driver: def-eq is confirmed by Lean's
        own type-checker.  Three in-jail steps over the built scratch package:

          1. `lake build` the subject (as in elaborate);
          2. a trusted driver file prints the theorem's type under
             `set_option pp.all true` (`#check @<name>` -- a TRUSTED driver we
             author, so the subject-facing escape gate's `#check` blocklist
             does not apply to it);
          3. a second driver file `example : <printed type> := @<name>` --
             this ELABORATES the printed text and type-checks the original
             constant against it, which succeeds IFF the two are
             definitionally equal.  The def-eq verdict is therefore
             kernel-checked, not text-compared.

        Honesty note (kernel-family, not L5-clean): unlike build/axioms there
        is no replay-as-data run-2 equivalent -- printing inherently
        elaborates subject bytes.  The subject on this path is compiler-emitted
        and escape-gated (defense in depth), the jail contains escape, and the
        result feeds channel 1, which is already labeled
        independence="kernel-family".
        """
        if not common.lean_available():
            return {"ok": False, "unavailable": True,
                    "reason": "lean toolchain absent"}

        from buildloop import validate_lean
        ok, reason = validate_lean.validate_lean(lean_text)
        if not ok:
            return {"ok": False, "unavailable": False,
                    "reason": f"escape-gate refusal: {reason}"}
        m = self._THEOREM_NAME.search(lean_text)
        if not m:
            return {"ok": False, "unavailable": False,
                    "reason": "no `theorem <name>` in subject"}
        name = m.group(1)

        key = self._cache_key("pp_roundtrip", lean_text.encode())
        hit = self._cache_get(key)
        if hit is not None:
            return hit

        mounts, why = self._lean_mounts()
        if mounts is None:
            return {"ok": False, "unavailable": False, "reason": why}

        imports = "\n".join(f"import {m_}" for m_ in common.MATHLIB_IMPORTS)
        with Sandbox(ro_mounts=mounts) as sb:
            self._scratch_package(sb, lean_text)
            kw = self._lean_run_kw()
            build = sb.run(["lake", "build", "CgbScratch"],
                           timeout=1800, cpu_seconds=1200, mem_mb=6144,
                           fsize_mb=512, **kw)
            if not build.ok:
                result = {"ok": False, "unavailable": False,
                          "reason": "subject did not build",
                          "detail": (build.stdout + build.stderr
                                     ).decode(errors="replace")[-800:]}
                self._cache_put(key, result)
                return result
            # step 2: print the type under pp.all (trusted driver).
            sb.add_file("PpPrint.lean",
                        "import CgbScratch\n"
                        "set_option pp.all true in\n"
                        f"#check @{name}\n")
            pr = sb.run(["lake", "env", "lean", "PpPrint.lean"],
                        timeout=600, cpu_seconds=300, mem_mb=6144, **kw)
            out = pr.stdout.decode(errors="replace")
            sep = out.find(" : ")
            if not pr.ok or sep < 0:
                result = {"ok": False, "unavailable": False,
                          "reason": "pp.all print failed",
                          "detail": out[-800:]}
                self._cache_put(key, result)
                return result
            printed = " ".join(out[sep + 3:].split())
            # step 3: re-elaborate the printed type; type-checking the original
            # constant against it IS the def-eq check (kernel-confirmed).
            sb.add_file("PpRoundtrip.lean",
                        "import CgbScratch\n"
                        f"example : ({printed}) := @{name}\n")
            rt = sb.run(["lake", "env", "lean", "PpRoundtrip.lean"],
                        timeout=600, cpu_seconds=300, mem_mb=6144, **kw)
            result = {"ok": bool(rt.ok), "unavailable": False,
                      "printed": printed[:2000],
                      "detail": ("" if rt.ok else (rt.stdout + rt.stderr
                                                   ).decode(errors="replace")[-800:])}
        self._cache_put(key, result)
        return result

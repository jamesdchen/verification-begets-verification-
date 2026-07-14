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

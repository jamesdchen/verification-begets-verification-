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
from generators import harness_gen, dafny_gen


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
    """
    name = "smt"

    def run_z3(self, smtlib: str, timeout_ms=15000) -> dict:
        import z3
        try:
            s = z3.Solver()
            s.set("timeout", timeout_ms)
            s.add(z3.parse_smt2_string(smtlib))
            r = str(s.check())
            result = {"unsat": "pass", "sat": "fail", "unknown": "unknown"}[r]
            return {"backend": "z3", "result": result, "detail": f"z3 says {r}",
                    "solver_version": z3.get_version_string()}
        except Exception as e:
            return {"backend": "z3", "result": "error", "detail": repr(e)[:800]}

    def run_cvc5(self, smtlib: str, timeout_ms=15000) -> dict:
        import cvc5
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
            result = {"unsat": "pass", "sat": "fail",
                      "unknown": "unknown"}.get(head, "error")
            ver = slv.getVersion()
            if isinstance(ver, bytes):
                ver = ver.decode(errors="replace")
            return {"backend": "cvc5", "result": result, "detail": f"cvc5 says {r}",
                    "solver_version": ver}
        except Exception as e:
            return {"backend": "cvc5", "result": "error", "detail": repr(e)[:800]}

#!/usr/bin/env python3
"""Unsat proof-artifact production (certifying-algorithms sweep, item 1).

THE GAP THIS ADDRESSES.  A ``sat`` verdict carries a model -- a witness
anyone can re-check by substitution -- but an ``unsat`` is witness-less,
which is exactly why the repo runs the direction-split discipline (dual
solver + enumeration corroboration before an unsat may refuse).  The
certifying-algorithms lesson (Mehlhorn; proof-carrying code) says: make the
computation EMIT a checkable witness.  Both installed solvers can:

  * z3 produces a proof term when ``proof=True`` precedes context creation
    (which is why the z3 leg runs in a SUBPROCESS here -- setting it
    in-process would mutate global solver config under the kernel's feet);
  * cvc5 produces proof components under ``produce-proofs``.

WHAT THIS TOOL DOES: for each obligation it obtains the unsat verdict AND
records both solvers' proof artifacts, content-bound to the obligation hash.

WHAT IT HONESTLY DOES NOT DO: check them.  No independent proof checker
(carcara for Alethe, or a bound z3-proof replayer) is installed here, so
every artifact is recorded at tier ``proof-produced-unchecked`` -- strictly
more auditable than a bare unsat (the reasoning is on disk), but NOT yet a
certified verdict.  The upgrade path is one tool install + one tier string:
``proof-checked``.  The kernel and TRUST.md are untouched; this is the
evidence layer probing what the trust layer could later adopt.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common

TIER = "proof-produced-unchecked"

# Fragment-shaped demo obligations (self-contained SMT-LIB, QF_NIA): each is
# an UNSAT assertion of the negation of a fragment truth.
DEMO_OBLIGATIONS = (
    ("square-nonneg", """(set-logic QF_NIA)
(declare-const n Int)
(assert (< (* n n) 0))
(check-sat)
"""),
    ("even-plus-even-not-odd", """(set-logic QF_NIA)
(declare-const a Int)
(declare-const b Int)
(declare-const j Int)
(declare-const k Int)
(assert (= a (* 2 j)))
(assert (= b (* 2 k)))
(assert (exists ((m Int)) (= (+ a b) (+ (* 2 m) 1))))
(check-sat)
"""),
)

_Z3_SUBPROCESS = r"""
import json, sys
import z3
z3.set_param(proof=True)                # BEFORE first context use
s = z3.Solver()
s.set("timeout", 15000)
s.add(z3.parse_smt2_string(sys.stdin.read()))
r = str(s.check())
out = {"verdict": r, "proof_sexpr": None}
if r == "unsat":
    out["proof_sexpr"] = s.proof().sexpr()
print(json.dumps(out))
"""


def z3_unsat_proof(smt: str) -> dict:
    """z3 leg, subprocess-isolated (see module docstring).  Honest error
    shape on any failure, never a crash."""
    try:
        r = subprocess.run([sys.executable, "-c", _Z3_SUBPROCESS],
                           input=smt, capture_output=True, text=True,
                           timeout=60)
        if r.returncode != 0:
            return {"verdict": "error", "detail": r.stderr[-400:]}
        return json.loads(r.stdout)
    except Exception as ex:
        return {"verdict": "error", "detail": repr(ex)[:400]}


def cvc5_unsat_proof(smt: str) -> dict:
    """cvc5 leg (per-instance options, safe in-process).  Proof extraction is
    accessor-tolerant across binding versions; absence degrades honestly."""
    try:
        import cvc5
    except ImportError:
        return {"verdict": "absent", "detail": "cvc5 binding not installed"}
    try:
        slv = cvc5.Solver()
        slv.setOption("produce-proofs", "true")
        slv.setOption("tlimit-per", "15000")
        parser = cvc5.InputParser(slv)
        parser.setStringInput(cvc5.InputLanguage.SMT_LIB_2_6, smt, "ob.smt2")
        sm = parser.getSymbolManager()
        verdict = None
        while True:
            cmd = parser.nextCommand()
            if cmd.isNull():
                break
            out = cmd.invoke(slv, sm)
            if out.strip():
                verdict = out.strip().split()[0]
        rec = {"verdict": verdict or "error", "proof_text": None}
        if verdict == "unsat":
            proofs = slv.getProof()
            texts = []
            for p in proofs:
                for accessor in (lambda x: slv.proofToString(x),
                                 lambda x: str(x)):
                    try:
                        t = accessor(p)
                        if isinstance(t, bytes):
                            t = t.decode(errors="replace")
                        if t:
                            texts.append(t)
                            break
                    except Exception:
                        continue
            rec["proof_text"] = "\n".join(texts) if texts else None
            rec["n_components"] = len(proofs)
        return rec
    except Exception as ex:
        return {"verdict": "error", "detail": repr(ex)[:400]}


def probe(obligations) -> dict:
    rows = []
    for name, smt in obligations:
        ob_hash = common.sha256_bytes(smt.encode())
        z = z3_unsat_proof(smt)
        c = cvc5_unsat_proof(smt)
        rows.append({
            "name": name,
            "obligation_sha": ob_hash,
            "tier": TIER,
            "z3": {"verdict": z.get("verdict"),
                   "proof_bytes": len(z.get("proof_sexpr") or "")},
            "cvc5": {"verdict": c.get("verdict"),
                     "proof_bytes": len(c.get("proof_text") or "")},
            "artifacts": {"z3_proof_sexpr": z.get("proof_sexpr"),
                          "cvc5_proof_text": c.get("proof_text")},
        })
    return {
        "tool": "smt_proof_probe",
        "honesty": ("proof artifacts RECORDED, not checked -- no independent "
                    "proof checker is installed; tier stays "
                    f"'{TIER}' until one is.  Kernel and TRUST.md untouched."),
        "rows": rows,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="results/smt_proof_probe.json")
    args = ap.parse_args(argv)
    rep = probe(DEMO_OBLIGATIONS)
    with open(args.out, "w") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True)
    for r in rep["rows"]:
        print(f"{r['name']}: z3={r['z3']['verdict']}"
              f"({r['z3']['proof_bytes']}B proof) "
              f"cvc5={r['cvc5']['verdict']}"
              f"({r['cvc5']['proof_bytes']}B proof) tier={r['tier']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

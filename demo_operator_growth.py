#!/usr/bin/env python3
"""R2 demo: autonomous operator-table growth under a gate-correctness certificate.

REQUIRES_LLM = False   # first line after the docstring (the --full glob reads it)

Five LLM-free, Lean-free teeth over the "semantics in, never code in"
architecture (``generators/operator_growth.py``).  A new operator WORD is a row
of pure data -- a definitional extension over the frozen kernel fragment -- and
is EXPANDED at the reading layer before compile / eval / smt ever see it, so the
three backends' semantics DERIVE from one definition and the certificate is
their differential agreement.

  [1] ADMIT   propose multiple_of(a,b) := dvd(b,a); the admission battery
              (well-formedness + differential instance battery + compile
              round-trip + nonvacuity) is GREEN, and a planted MathReading using
              the word certifies end-to-end through run.formalize.certify_statement
              via expansion (the engines only ever saw `dvd`).
  [2] VACUOUS propose always_geq(a,b) := (a <= b) or (b <= a); always TRUE on the
              battery domain -> REFUSED as vacuous vocabulary (nonvacuity).
  [3] UNKNOWN propose weird(a) := frobnicate(a); an operator neither kernel nor
              already-admitted -> REFUSED at well-formedness (no forward refs).
  [4] TAMPER  corrupt an admitted row's definition after admission; the per-use
              expansion recomputes the row hash and REFUSES (cert-id mismatch),
              so a stale/tampered row can never silently lower.
  [5] ZERO    with NO admitted operators, a full certify_statement run is
              byte-identical to the pre-change golden captured before any edit.

Deterministic: no LLM, no Lean, no clocks in any verdict.  cvc5 may be wholly
absent in a thin environment; the battery tolerates that honestly (the verdict
records ``cvc5=absent`` and admission is decided by z3 + decidable enumeration).
"""
REQUIRES_LLM = False

import dataclasses
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common
from generators import operator_growth as og
from generators.math_reading import split_envelope
from run.formalize import certify_statement


def _rule(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# multiple_of(a,b) := dvd(b,a).  "a is a multiple of b" iff b divides a.
MULTIPLE_OF = {"word": "multiple_of", "arity": 2, "params": ["a", "b"],
               "definition": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}

# A planted reading that USES the derived word in its demanded conclusion; its
# single hypothesis is the kernel form, so a faithful expansion makes the k
# smallest satisfying instances all hold (stage-4 replay passes).
PLANTED_SOURCE = "For a and b, if b divides a then a is a multiple of b."
PLANTED_READING = {
    "theorem": "dvd_gives_mult",
    "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "presupposition", "quote": "a and b",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "presupposition", "quote": "a and b",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h", "force": "presupposition", "quote": "b divides a",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}},
        {"id": "c", "force": "demand", "quote": "a is a multiple of b",
         "lf": {"kind": "conclusion",
                "pred": {"op": "multiple_of",
                         "args": [{"ref": "a"}, {"ref": "b"}]}}},
    ],
}

# A definition that is TRUE at every assignment (a <= b or b <= a is a total
# order tautology) -> vacuous vocabulary.
VACUOUS = {"word": "always_geq", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "or", "args": [
               {"op": "<=", "args": [{"ref": "a"}, {"ref": "b"}]},
               {"op": "<=", "args": [{"ref": "b"}, {"ref": "a"}]}]}}

# A definition naming an operator that is neither kernel nor admitted.
UNKNOWN = {"word": "weird", "arity": 1, "params": ["a"],
           "definition": {"op": "frobnicate", "args": [{"ref": "a"}]}}


def _serial(res):
    d = dataclasses.asdict(res)
    d["statement_cert"] = None if res.statement_cert is None else "CERT"
    return d


def main():
    # Isolated, empty operator registry so the demo is deterministic and never
    # depends on (or writes) the committed admitted.json.
    op_dir = tempfile.mkdtemp(prefix="op-growth-demo-")
    os.environ["CGB_OPERATORS_DIR"] = op_dir
    os.environ.pop("CGB_DB", None)          # in-process fidelity cache
    og.reload()
    failures = []

    # -------------------------------------------------------------- [1] ADMIT
    _rule("[1] ADMIT  multiple_of(a,b) := dvd(b,a)  ->  battery green, certifies")
    res = og.admit_operator(MULTIPLE_OF)
    print("  battery admitted :", res["admitted"])
    if res["admitted"]:
        cert = res["cert"]
        b = cert["battery"]
        print("  cert id          :", cert["id"][:16], "...")
        print("  battery          : %d instances, satisfiable=%s refutable=%s"
              % (b["n_instances"], b["satisfiable"], b["refutable"]))
        print("  channels         : z3 confirmations=%d  cvc5_present=%s  "
              "(enum always)" % (b["smt_confirmations"], b["cvc5_present"]))
        og.save_admitted({"multiple_of": {"row": res["row"], "cert": cert}})
        og.reload()
    else:
        failures.append("multiple_of should have admitted")

    r = certify_statement(PLANTED_SOURCE, json.dumps(PLANTED_READING))
    print("  planted certify  : ok=%s stage=%r" % (r.ok, r.stage))
    print("  compiled (engines saw only kernel `dvd`):")
    print("     ", r.lean_text)
    # The word never reaches the engine: the compiled Lean carries the kernel
    # divides atom (U+2223), not the derived word.
    if not (r.ok and "multiple_of" not in r.lean_text
            and "∣" in r.lean_text):
        failures.append("planted reading should certify via expansion to dvd")

    # ------------------------------------------------------------ [2] VACUOUS
    _rule("[2] VACUOUS  always_geq(a,b) := (a<=b) or (b<=a)  ->  refused")
    res = og.admit_operator(VACUOUS)
    print("  admitted :", res["admitted"])
    print("  refusal  :", res.get("refusal"))
    if res["admitted"] or res["refusal"]["stage"] != "nonvacuity":
        failures.append("vacuous word should refuse at nonvacuity")

    # ------------------------------------------------------------ [3] UNKNOWN
    _rule("[3] UNKNOWN  weird(a) := frobnicate(a)  ->  refused at well-formedness")
    res = og.admit_operator(UNKNOWN)
    print("  admitted :", res["admitted"])
    print("  refusal  :", res.get("refusal"))
    if res["admitted"] or res["refusal"]["stage"] != "well-formedness":
        failures.append("unknown-operator word should refuse at well-formedness")

    # ------------------------------------------------------------- [4] TAMPER
    _rule("[4] TAMPER  edit an admitted row after admission  ->  refuses to lower")
    path = os.path.join(op_dir, "admitted.json")
    with open(path) as fh:
        disk = json.load(fh)
    # swap the args: multiple_of now (wrongly) expands to dvd(a,b), a different
    # relation.  The row hash no longer matches the certificate id.
    disk["multiple_of"]["row"]["definition"] = {
        "op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}
    with open(path, "w") as fh:
        json.dump(disk, fh)
    og.reload()
    r = certify_statement(PLANTED_SOURCE, json.dumps(PLANTED_READING))
    print("  after tamper : ok=%s stage=%r" % (r.ok, r.stage))
    print("  reason       :", r.error[:88])
    if r.ok or "cert" not in r.error.lower():
        failures.append("tampered row should refuse with a cert-id mismatch")

    # --------------------------------------------------------------- [5] ZERO
    _rule("[5] ZERO-ROWS  empty registry  ->  certify_statement byte-identical")
    empty_dir = tempfile.mkdtemp(prefix="op-growth-empty-")
    os.environ["CGB_OPERATORS_DIR"] = empty_dir
    og.reload()
    here = os.path.dirname(os.path.abspath(__file__))
    golden = json.load(open(os.path.join(
        here, "tests", "golden", "operator_growth_zero_rows.json")))
    all_identical = True
    for name in sorted(golden):
        rj, src = split_envelope(open(os.path.join(
            here, "specs", "mathsources", "readings", name)).read())
        res = certify_statement(src, rj)
        got = common.canonical_json(_serial(res))
        want = common.canonical_json(golden[name])
        same = got == want
        all_identical = all_identical and same
        print("  %-26s byte-identical=%s" % (name, same))
    if not all_identical:
        failures.append("zero-rows run diverged from the pre-change golden")

    # ------------------------------------------------------------------- done
    _rule("SUMMARY")
    if failures:
        for f in failures:
            print("  FAIL:", f)
        print("\nDEMO FAILED")
        return 1
    print("  All five teeth green: admit / vacuous-refuse / unknown-refuse / "
          "tamper-refuse / zero-rows byte-identity.")
    print("\nDEMO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""R2 demo: autonomous operator-table growth under a gate-correctness certificate.

REQUIRES_LLM = False   # first line after the docstring (the --full glob reads it)

Six LLM-free, Lean-free teeth over the "semantics in, never code in"
architecture (``generators/operator_growth.py``).  A new operator WORD is a row
of pure data -- a definitional extension over the frozen kernel fragment -- and
is EXPANDED at the reading layer before compile / eval / smt ever see it, so the
three backends' semantics DERIVE from one definition and the certificate is
their differential agreement.  Since WP-T4a, admission is also PRICED: a row
must strictly lower corpus DL over a supplied pricing corpus (model bits paid,
savings counted, >= 2 witness readings), and pure renames of kernel atoms are
refused before the battery ever runs.

  [1] ADMIT   propose congm(a,b,m) := (a mod m) = (b mod m); priced against the
              REAL committed corpus (results/formalize_bench_state.jsonl) the
              row pays (saving > model_bits over >= 2 witnesses), the admission
              battery is GREEN, and a planted MathReading using the word
              certifies end-to-end via expansion (the engines only ever saw
              kernel `mod`/`=`).
  [2] ALIAS   propose multiple_of(a,b) := dvd(b,a); a pure rename of a kernel
              atom -> REFUSED at trivial-alias, before the battery.
  [3] VACUOUS propose always_geq(a,b) := (a <= b) or (b <= a); always TRUE on the
              battery domain -> REFUSED as vacuous vocabulary (nonvacuity).
  [4] UNKNOWN propose weird(a) := frobnicate(a); an operator neither kernel nor
              already-admitted -> REFUSED at well-formedness (no forward refs).
  [5] TAMPER  corrupt an admitted row's definition after admission; the per-use
              expansion recomputes the row hash and REFUSES (cert-id mismatch),
              so a stale/tampered row can never silently lower.
  [6] ZERO    with NO admitted operators, a full certify_statement run is
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


# congm(a,b,m) := (a mod m) = (b mod m).  A genuine derived operator (not a
# rename): the congruence shape recurs across the committed corpus, so it PAYS
# under the WP-T4a pricing gate.
CONGM = {"word": "congm", "arity": 3, "params": ["a", "b", "m"],
         "definition": {"op": "=", "args": [
             {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
             {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}}

# multiple_of(a,b) := dvd(b,a): a single kernel atom over distinct param refs --
# a pure rename, semantically empty vocabulary.  The pricing-era gate refuses it
# before the battery ever runs.
MULTIPLE_OF = {"word": "multiple_of", "arity": 2, "params": ["a", "b"],
               "definition": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}

# A planted reading that USES the derived word in its demanded conclusion; its
# single hypothesis is the kernel form, so a faithful expansion makes the k
# smallest satisfying instances all hold (stage-4 replay passes).
PLANTED_SOURCE = ("For a, b and m, if a and b leave the same remainder on "
                  "division by m then a is congruent to b modulo m.")
PLANTED_READING = {
    "theorem": "same_rem_gives_cong",
    "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "om", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "m", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "a, b and m",
         "lf": {"kind": "quantifier", "binder": "forall",
                "objects": ["a", "b", "m"]}},
        {"id": "h", "force": "presupposition",
         "quote": "same remainder on division by m",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "=", "args": [
                    {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
                    {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}}},
        {"id": "c", "force": "demand", "quote": "congruent to b modulo m",
         "lf": {"kind": "conclusion",
                "pred": {"op": "congm",
                         "args": [{"ref": "a"}, {"ref": "b"},
                                  {"ref": "m"}]}}},
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


def _real_corpus():
    """The real pricing corpus: the certified governed exogenous readings from
    the committed bench checkpoint (same set the subtree census runs over)."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "results", "formalize_bench_state.jsonl")
    out = []
    with open(path) as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("arm") != "governed" or not rec.get("certified"):
                continue
            rj = rec.get("reading_json") or ""
            if not rj:
                continue
            doc = json.loads(rj)
            if isinstance(doc, dict) and isinstance(doc.get("statements"), list):
                out.append(doc)
    return out


def main():
    # Isolated, empty operator registry so the demo is deterministic and never
    # depends on (or writes) the committed admitted.json.
    op_dir = tempfile.mkdtemp(prefix="op-growth-demo-")
    os.environ["CGB_OPERATORS_DIR"] = op_dir
    os.environ.pop("CGB_DB", None)          # in-process fidelity cache
    og.reload()
    failures = []
    corpus = _real_corpus()

    # -------------------------------------------------------------- [1] ADMIT
    _rule("[1] ADMIT  congm(a,b,m) := (a mod m)=(b mod m)  ->  pays, certifies")
    res = og.admit_operator(CONGM, pricing_corpus=corpus)
    print("  battery admitted :", res["admitted"])
    if res["admitted"]:
        cert = res["cert"]
        b = cert["battery"]
        p = cert["pricing"]
        print("  cert id          :", cert["id"][:16], "...")
        print("  battery          : %d instances, satisfiable=%s refutable=%s"
              % (b["n_instances"], b["satisfiable"], b["refutable"]))
        print("  channels         : z3 confirmations=%d  cvc5_present=%s  "
              "(enum always)" % (b["smt_confirmations"], b["cvc5_present"]))
        print("  pricing          : model_bits=%s saving=%s uses=%s "
              "witnesses=%s  dl %s -> %s"
              % (p["model_bits"], p["saving"], p["uses"], p["witnesses"],
                 p["dl_before"], p["dl_after"]))
        og.save_admitted({"congm": {"row": res["row"], "cert": cert}},
                         pricing_corpus=corpus)
        og.reload()
    else:
        failures.append("congm should have admitted (it pays on the real "
                        "corpus): %r" % (res.get("refusal"),))

    r = certify_statement(PLANTED_SOURCE, json.dumps(PLANTED_READING))
    print("  planted certify  : ok=%s stage=%r" % (r.ok, r.stage))
    print("  compiled (engines saw only kernel `mod`/`=`):")
    print("     ", r.lean_text)
    # The word never reaches the engine: the compiled Lean carries the kernel
    # `%` notation, not the derived word.
    if not (r.ok and "congm" not in r.lean_text and "%" in r.lean_text):
        failures.append("planted reading should certify via expansion to mod")

    # -------------------------------------------------------------- [2] ALIAS
    _rule("[2] ALIAS  multiple_of(a,b) := dvd(b,a)  ->  refused pre-battery")
    res = og.admit_operator(MULTIPLE_OF, pricing_corpus=corpus)
    print("  admitted :", res["admitted"])
    print("  refusal  :", res.get("refusal"))
    if res["admitted"] or res["refusal"]["stage"] != "trivial-alias":
        failures.append("alias word should refuse at trivial-alias")

    # ------------------------------------------------------------ [3] VACUOUS
    _rule("[3] VACUOUS  always_geq(a,b) := (a<=b) or (b<=a)  ->  refused")
    res = og.admit_operator(VACUOUS, pricing_corpus=corpus)
    print("  admitted :", res["admitted"])
    print("  refusal  :", res.get("refusal"))
    if res["admitted"] or res["refusal"]["stage"] != "nonvacuity":
        failures.append("vacuous word should refuse at nonvacuity")

    # ------------------------------------------------------------ [4] UNKNOWN
    _rule("[4] UNKNOWN  weird(a) := frobnicate(a)  ->  refused at well-formedness")
    res = og.admit_operator(UNKNOWN, pricing_corpus=corpus)
    print("  admitted :", res["admitted"])
    print("  refusal  :", res.get("refusal"))
    if res["admitted"] or res["refusal"]["stage"] != "well-formedness":
        failures.append("unknown-operator word should refuse at well-formedness")

    # ------------------------------------------------------------- [5] TAMPER
    _rule("[5] TAMPER  edit an admitted row after admission  ->  refuses to lower")
    path = os.path.join(op_dir, "admitted.json")
    with open(path) as fh:
        disk = json.load(fh)
    # swap the first mod's args: congm now (wrongly) expands to
    # (m mod a) = (b mod m), a different relation.  The row hash no longer
    # matches the certificate id.
    disk["congm"]["row"]["definition"] = {
        "op": "=", "args": [
            {"op": "mod", "args": [{"ref": "m"}, {"ref": "a"}]},
            {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}
    with open(path, "w") as fh:
        json.dump(disk, fh)
    og.reload()
    r = certify_statement(PLANTED_SOURCE, json.dumps(PLANTED_READING))
    print("  after tamper : ok=%s stage=%r" % (r.ok, r.stage))
    print("  reason       :", r.error[:88])
    if r.ok or "cert" not in r.error.lower():
        failures.append("tampered row should refuse with a cert-id mismatch")

    # --------------------------------------------------------------- [6] ZERO
    _rule("[6] ZERO-ROWS  empty registry  ->  certify_statement byte-identical")
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
    print("  All six teeth green: priced-admit / alias-refuse / vacuous-refuse "
          "/ unknown-refuse / tamper-refuse / zero-rows byte-identity.")
    print("\nDEMO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""S4a -- reflection as a SHADOW channel beside the anchor ladder.

THE PROPER ROUTE (growth lane 2, the repo's own rule for new trust roots):
a new verdict source never wires into certs directly -- it runs in shadow,
PERMANENTLY PAIRED with the incumbent, accumulating differential agreement;
promotion into the cert vocabulary is a later, evidence-gated ceremony
(PLAN_REFLECT.md S4b).  ``ANCHOR_CERT_CHANNELS`` and
``ANCHOR_DISCHARGE_RUNGS`` are PINNED (kernel/certs.py, FI-KA-1/4); nothing
here touches them, the kernel, or any cert byte.

WHAT THE SHADOW CHANNEL DOES.  For a reading whose witness emitter produced
a template, build a self-contained Lean probe: the FgReflect module source
(content-hashed into the record) plus ONE theorem instantiating
``checkAll_witness`` -- template substituted, box environments listed -- with
``rfl`` as the entire discharge.  The probe's subject is EXACTLY the bounded
shadow's own claim (every hypothesis-admitted outer point in the box has a
witness); elaboration is RUN-1 evidence (the import_rt honesty note
verbatim: an elaboration typecheck inside the jail; the two-run L5
adjudication belongs to cert minting, which this deliberately is not).

THE DIFFERENTIAL.  The emitter's full-check guarantees the bounded claim
holds wherever it emits, so reflection MUST close; a probe that fails to
elaborate where the ladder closed is a first-class disagreement -- recorded,
never discarded (the disagreement-logging discipline).  Agreement rows are
the evidence S4b's ceremony will be gated on.

Frozen skip vocabulary (a skip is never a failure):
  ``not-emitted:<emitter reason>``, ``multi-exists-out-of-scope-v0``,
  ``op-out-of-reflect-slice:<op>``, ``nat-sub-out-of-reflect-slice``.
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from generators.math_reading import parse_math_reading
from generators.math_witness import emit_witness_proofs, _collect_witnesses
from generators.math_eval import exists_shadow_shape
from buildloop.validate_lean import validate_lean

_REFLECT_SRC = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "FgReflect.lean")

# F-G op -> FgReflect constructor (the v0.1 slice).  Anything absent is an
# op-out-of-reflect-slice skip -- gcd/coprime/^ arrive with later slices.
_TERM_OPS = {"+": "Tm.add", "-": "Tm.sub", "*": "Tm.mul",
             "%": "Tm.tmod", "mod": "Tm.tmod"}
_ATOM_OPS = {"=": "Pd.peq", "<=": "Pd.ple", "<": "Pd.plt", "!=": "Pd.pne",
             "dvd": "Pd.pdvd"}
_UNARY_OPS = {"even": "Pd.peven", "odd": "Pd.podd"}
_CONN_OPS = {"and": "Pd.pand", "or": "Pd.por", "implies": "Pd.pimp"}


class SliceMiss(Exception):
    """An AST node outside the reflect slice -- becomes a named skip."""


def quote_term(term: dict, index_of: dict) -> str:
    if "ref" in term:
        return f"(Tm.tvar {index_of[term['ref']]})"
    if "lit" in term:
        v = term["lit"]
        return f"(Tm.lit {v})" if v >= 0 else f"(Tm.lit ({v}))"
    op = term.get("op")
    ctor = _TERM_OPS.get(op)
    if ctor is None:
        raise SliceMiss(f"op-out-of-reflect-slice:{op}")
    args = term["args"]
    # n-ary + and * fold left, mirroring the compiler's association.
    out = quote_term(args[0], index_of)
    for a in args[1:]:
        out = f"({ctor} {out} {quote_term(a, index_of)})"
    return out


def quote_pred(pred: dict, index_of: dict) -> str:
    op = pred.get("op")
    if op in _CONN_OPS:
        args = pred["args"]
        out = quote_pred(args[0], index_of)
        for a in args[1:]:
            out = f"({_CONN_OPS[op]} {out} {quote_pred(a, index_of)})"
        return out
    if op in _UNARY_OPS:
        return f"({_UNARY_OPS[op]} {quote_term(pred['args'][0], index_of)})"
    if op in _ATOM_OPS:
        a, b = pred["args"]
        return (f"({_ATOM_OPS[op]} {quote_term(a, index_of)} "
                f"{quote_term(b, index_of)})")
    raise SliceMiss(f"op-out-of-reflect-slice:{op}")


def _env_text(assignment: dict, index_of: dict) -> str:
    branches = "".join(
        f"if i = {index_of[n]} then "
        + (f"({v})" if v < 0 else str(v)) + " else "
        for n, v in sorted(assignment.items(), key=lambda kv: index_of[kv[0]]))
    return f"(fun i => {branches}(0 : Int))"


def _uses_sub(node) -> bool:
    if isinstance(node, dict):
        if node.get("op") == "-":
            return True
        return any(_uses_sub(a) for a in node.get("args", []))
    return False


def shadow_probe(reading, *, bound=8) -> dict:
    """Build the paired reflection probe for one reading, or a named skip.
    Deterministic; never touches Lean itself (the caller elaborates)."""
    res = emit_witness_proofs(reading, bound=bound)
    if res["status"] != "emitted":
        return {"status": "skip", "reason": f"not-emitted:{res['reason']}"}
    shape = exists_shadow_shape(reading, bound=None)
    outer, exists = shape["outer"], shape["exists"]
    if len(exists) != 1:
        return {"status": "skip", "reason": "multi-exists-out-of-scope-v0"}
    carriers = reading.objects()
    from generators.math_eval import conclusions_of
    concl = conclusions_of(reading)
    if any(c == "Nat" for c in carriers.values()) and (
            _uses_sub(concl) or _uses_sub(res["template"][exists[0]])):
        return {"status": "skip", "reason": "nat-sub-out-of-reflect-slice"}

    names = sorted(carriers)
    index_of = {n: i for i, n in enumerate(names)}
    k = index_of[exists[0]]
    try:
        tau = quote_term(res["template"][exists[0]], index_of)
        pd = quote_pred(concl, index_of)
    except SliceMiss as ex:
        return {"status": "skip", "reason": str(ex)}

    admitted, _ = _collect_witnesses(reading, outer, exists, bound)
    if not admitted:
        return {"status": "skip", "reason": "not-emitted:no-admitted-outers"}
    envs = ",\n      ".join(_env_text(a, index_of) for a in admitted)

    module = open(_REFLECT_SRC).read()
    module_sha = common.sha256_bytes(module.encode())
    probe = (module + "\n\n"
             "-- reflect-shadow probe (S4a): the bounded shadow's own claim,\n"
             "-- discharged by checkAll_witness with rfl as the computation.\n"
             "example :\n"
             "    forall env, env ∈ ([" + envs + "] : List (Nat -> Int)) ->\n"
             f"      Exists (fun v => FgReflect.denote "
             f"(FgReflect.update env {k} v)\n"
             f"        {pd}) :=\n"
             f"  FgReflect.checkAll_witness _ {k}\n"
             f"    {tau} _ rfl\n")
    ok, why = validate_lean(probe)
    if not ok:
        # invariant violation, not a skip (the math_witness convention).
        raise RuntimeError(f"reflect-shadow probe failed the escape gate: "
                           f"{why}")
    return {"status": "probe", "probe": probe, "module_sha": module_sha,
            "k": k, "template": tau, "n_envs": len(admitted),
            "statement_hash": res["statement_hash"]}


def run_shadow(root=None, *, bound=8) -> dict:
    """The shadow sweep over the committed reading corpus.  Lean present:
    each probe elaborates (RUN-1) and agreement/disagreement is recorded;
    absent: probes are built and honestly deferred."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows = []
    for p in sorted(glob.glob(os.path.join(
            root, "specs", "mathsources", "readings", "*.json"))):
        d = json.load(open(p))
        reading = parse_math_reading(json.dumps(d["reading"]), d["source"])
        r = shadow_probe(reading, bound=bound)
        r["source"] = os.path.basename(p)
        rows.append(r)
    report = {"tool": "reflect_shadow", "channel": "shadow (paired, non-cert)",
              "honesty": ("RUN-1 elaboration evidence beside the pinned "
                          "ladder; cert channels and discharge vocabulary "
                          "untouched.  Disagreement rows are first-class; "
                          "S4b's ceremony is gated on accumulated agreement."),
              "rows": rows}
    if not common.lean_available():
        report["verdicts"] = "deferred: lean toolchain absent"
        return report
    from kernel.backends import LeanBackend
    be = LeanBackend()
    agree = disagree = 0
    for r in rows:
        if r["status"] != "probe":
            continue
        res = be.elaborate(r["probe"], expect_sorry=False)
        r["elaborated"] = bool(res.get("ok"))
        if r["elaborated"]:
            agree += 1
        else:
            disagree += 1
            r["disagreement"] = {"transcript": str(res)[:1500]}
    report["verdicts"] = {"agree": agree, "disagree": disagree}
    return report


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="results/reflect_shadow.json")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("reflect-shadow"):
        rep = run_shadow()
    with open(args.out, "w") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True)
    print(f"reflect_shadow: {sum(1 for r in rep['rows'] if r['status'] == 'probe')} "
          f"probes, verdicts={rep.get('verdicts')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
  ``op-out-of-reflect-slice:<op>``, ``mixed-carriers-out-of-reflect-slice``.
(``nat-sub-out-of-reflect-slice`` RETIRED with the S6-carrier Nat layer:
truncated subtraction is now proven in FgReflect (evalTmN/denoteN/
checkAllN_witness), so Nat readings probe through the Nat mirror instead
of skipping -- the retirement the plan requires to happen only on proof.)
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


def _env_text(assignment: dict, index_of: dict, carrier: str = "Int") -> str:
    branches = "".join(
        f"if i = {index_of[n]} then "
        + (f"({v})" if v < 0 else str(v)) + " else "
        for n, v in sorted(assignment.items(), key=lambda kv: index_of[kv[0]]))
    return f"(fun i => {branches}(0 : {carrier}))"


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
    cvals = set(carriers.values())
    if len(cvals) > 1:
        return {"status": "skip", "reason": "mixed-carriers-out-of-reflect-slice"}
    # single-carrier readings pick their proven layer: the Int slice or the
    # S6-carrier Nat mirror (truncated sub included -- the retired skip).
    nat = cvals == {"Nat"}

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

    module = open(_REFLECT_SRC).read()
    module_sha = common.sha256_bytes(module.encode())
    # the examples re-enter the namespace: the quoter emits UNQUALIFIED
    # constructor names (Tm.add, Pd.plt), which resolve only inside it --
    # the first lane run refused exactly this, from outside (S1 ledger).
    #
    # ONE example PER box point (singleton checkAll_witness), because Lean's
    # elaboration budget is PER DECLARATION: the single full-box example
    # deterministically timed out at whnf on the 289-env box even at the
    # gate's whitelisted cap (lane runs 30032983482/30033836721), while the
    # conjunction of the pointwise claims IS the box claim -- same subject,
    # per-point cost.  The whitelisted cap rides each example, belt+braces.
    carrier = "Nat" if nat else "Int"
    den = "denoteN" if nat else "denote"
    upd = "updateN" if nat else "update"
    thm = "checkAllN_witness" if nat else "checkAll_witness"
    example_blocks = "\n\n".join(
        f"set_option maxHeartbeats {common.LEAN_MAXHEARTBEATS} in\n"
        "example :\n"
        "    forall env, env ∈ ([" + _env_text(a, index_of, carrier)
        + f"] : List (Nat -> {carrier})) ->\n"
        f"      Exists (fun v => {den} ({upd} env {k} v)\n"
        f"        {pd}) :=\n"
        f"  {thm} _ {k}\n"
        f"    {tau} _ rfl"
        for a in admitted)
    probe = (module + "\n\n"
             "namespace FgReflect\n\n"
             "-- reflect-shadow probe (S4a): the bounded shadow's own claim,\n"
             "-- discharged pointwise by checkAll_witness, rfl per point.\n"
             + example_blocks + "\n\n"
             "end FgReflect\n")
    ok, why = validate_lean(probe)
    if not ok:
        # invariant violation, not a skip (the math_witness convention).
        raise RuntimeError(f"reflect-shadow probe failed the escape gate: "
                           f"{why}")
    return {"status": "probe", "probe": probe, "module_sha": module_sha,
            "k": k, "template": tau, "n_envs": len(admitted),
            "statement_hash": res["statement_hash"]}


def _statement_hash(reading) -> str:
    from generators.math_compile import compile_math_reading
    return compile_math_reading(reading)["statement_hash"]


def search_probe(reading, *, bound=8) -> dict:
    """ROUTE 2 -- template-free exhaustive search
    (``checkStmtBox_sound_exOnly``): at every box point that HAS an in-box
    witness, the ∃-statement is discharged by sweeping the witness box, no
    template involved.  Edge points whose only witnesses escape the box are
    honestly OUTSIDE this route's reach (that is the search route's
    semantics, not a failure), so they are simply not probed here -- the
    template route covers them."""
    shape = exists_shadow_shape(reading, bound=None)
    if shape.get("mode") != "supported":
        return {"status": "skip",
                "reason": f"route-not-applicable:{shape.get('mode')}"}
    outer, exists = shape["outer"], shape["exists"]
    if len(exists) != 1:
        return {"status": "skip", "reason": "multi-exists-out-of-scope-v0"}
    carriers = reading.objects()
    if set(carriers.values()) != {"Int"}:
        # the box layer (denoteStmtBox/checkStmtBox) is Int-only today; the
        # Nat mirror covers the Pd chain, not the Stmt layer.
        return {"status": "skip", "reason": "route-not-applicable:non-int-carrier"}
    from generators.math_eval import conclusions_of
    concl = conclusions_of(reading)
    names = sorted(carriers)
    index_of = {n: i for i, n in enumerate(names)}
    k = index_of[exists[0]]
    try:
        pd = quote_pred(concl, index_of)
    except SliceMiss as ex:
        return {"status": "skip", "reason": str(ex)}
    _, witnessed = _collect_witnesses(reading, outer, exists, bound)
    if not witnessed:
        return {"status": "skip", "reason": "no-inbox-witness-envs"}
    box = "[" + ", ".join((f"({v})" if v < 0 else str(v))
                          for v in range(-bound, bound + 1)) + "]"
    module = open(_REFLECT_SRC).read()
    module_sha = common.sha256_bytes(module.encode())
    example_blocks = "\n\n".join(
        f"set_option maxHeartbeats {common.LEAN_MAXHEARTBEATS} in\n"
        "example :\n"
        "    denoteStmt " + _env_text(a, index_of) + "\n"
        f"      (Stmt.sex {k} (Stmt.base\n"
        f"        {pd})) :=\n"
        f"  checkStmtBox_sound_exOnly {box}\n"
        f"    {_env_text(a, index_of)} _ rfl rfl"
        for a, _tuples in witnessed)
    probe = (module + "\n\n"
             "namespace FgReflect\n\n"
             "-- reflect-shadow probe (route 2): the ∃-statement by exhaustive\n"
             "-- box search, one example per in-box-witnessed point.\n"
             + example_blocks + "\n\n"
             "end FgReflect\n")
    ok, why = validate_lean(probe)
    if not ok:
        raise RuntimeError(f"route-2 probe failed the escape gate: {why}")
    return {"status": "probe", "probe": probe, "module_sha": module_sha,
            "k": k, "n_envs": len(witnessed),
            "statement_hash": _statement_hash(reading)}


def guard_probe(reading, *, bound=8) -> dict:
    """ROUTE 3 -- the guard shape (``sall_guard_of_check``): for a ∀-only
    single-variable Int reading, each true box point c yields the typed
    rendering's emitted form ``forall v, v = c -> body`` (hypotheses folded
    into the body as implications), discharged by one checker run through
    the shape-1 preservation theorem."""
    shape = exists_shadow_shape(reading, bound=None)
    if shape != {"mode": "forall-only"}:
        return {"status": "skip", "reason": "route-not-applicable:not-forall-only"}
    carriers = reading.objects()
    if set(carriers.values()) != {"Int"}:
        return {"status": "skip", "reason": "route-not-applicable:non-int-carrier"}
    if len(carriers) != 1:
        return {"status": "skip", "reason": "route-not-applicable:multi-var-guard-v1"}
    from generators.math_eval import conclusions_of, hypotheses_of, eval_pred
    body = conclusions_of(reading)
    for h in reversed(hypotheses_of(reading)):
        body = {"op": "implies", "args": [h, body]}
    name = sorted(carriers)[0]
    index_of = {name: 0}
    try:
        q = quote_pred(body, index_of)
    except SliceMiss as ex:
        return {"status": "skip", "reason": str(ex)}
    ambient = reading.ambient_carrier()
    points = [c for c in range(-bound, bound + 1)
              if eval_pred(body, {name: c}, carriers, ambient)]
    if not points:
        return {"status": "skip", "reason": "no-true-box-points"}
    module = open(_REFLECT_SRC).read()
    module_sha = common.sha256_bytes(module.encode())
    env = _env_text({}, index_of)
    example_blocks = "\n\n".join(
        f"set_option maxHeartbeats {common.LEAN_MAXHEARTBEATS} in\n"
        "example :\n"
        "    denoteStmt " + env + "\n"
        "      (Stmt.sall 0 (Stmt.base\n"
        f"        (Pd.pimp (Pd.peq (Tm.tvar 0) (Tm.lit "
        + (f"({c})" if c < 0 else str(c)) + f")) {q}))) :=\n"
        f"  sall_guard_of_check _ 0 "
        + (f"({c})" if c < 0 else str(c)) + " _ rfl"
        for c in points)
    probe = (module + "\n\n"
             "namespace FgReflect\n\n"
             "-- reflect-shadow probe (route 3): the typed rendering's guard\n"
             "-- shape at every true box point, via compile_guard_shape's\n"
             "-- discharge.\n"
             + example_blocks + "\n\n"
             "end FgReflect\n")
    ok, why = validate_lean(probe)
    if not ok:
        raise RuntimeError(f"route-3 probe failed the escape gate: {why}")
    return {"status": "probe", "probe": probe, "module_sha": module_sha,
            "n_envs": len(points),
            "statement_hash": _statement_hash(reading)}


# The three discharge routes S4b would promote, each with its own probe
# builder -- ledger rows carry the route, so per-route evidence is
# ledger-measurable (route-qualified claims are what the ceremony pins).
ROUTES = (
    ("checkAll_witness", shadow_probe),
    ("checkStmtBox_sound_exOnly", search_probe),
    ("sall_guard_of_check", guard_probe),
)


def run_shadow(root=None, *, bound=8) -> dict:
    """The shadow sweep over the committed reading corpus, one probe per
    (reading, route).  Lean present: each probe elaborates (RUN-1) and
    agreement/disagreement is recorded; absent: probes are built and
    honestly deferred."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows = []
    for p in sorted(glob.glob(os.path.join(
            root, "specs", "mathsources", "readings", "*.json"))):
        d = json.load(open(p))
        reading = parse_math_reading(json.dumps(d["reading"]), d["source"])
        for route, build in ROUTES:
            r = build(reading, bound=bound)
            r["source"] = os.path.basename(p)
            r["route"] = route
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
            # classify from the TRANSCRIPT (data-derived, no tuned constant):
            # a deterministic budget timeout is an explained refusal, not a
            # semantic reflection/ladder divergence -- S4b's entrance
            # predicate needs every disagreement row to carry a root cause.
            detail = str(res.get("detail", "")) + str(res)
            reason = ("deterministic-timeout-at-heartbeat-cap"
                      if "maximum number of heartbeats" in detail
                      else "unexplained")
            r["disagreement"] = {"reason": reason,
                                 "transcript": str(res)[:1500]}
    report["verdicts"] = {"agree": agree, "disagree": disagree}
    return report


def append_ledger(report, path, lane_run_id) -> list:
    """S4a'(i): append one agreement/disagreement row per ELABORATED probe to
    the durable JSONL ledger -- the evidence store S4b's entrance predicate is
    measured from.  APPEND-ONLY, the import_driver._Ledger convention: rows
    are only ever appended (canonical JSON, one line each), so any prior
    ledger content remains a byte-prefix of the new file; there is NO
    truncate or rewrite path.  Returns the rows appended."""
    rows = []
    for r in report["rows"]:
        if r.get("status") != "probe" or "elaborated" not in r:
            continue
        row = {
            "lane_run_id": str(lane_run_id),
            "module_sha": r["module_sha"],
            "route": r.get("route", "checkAll_witness"),
            "source": r["source"],
            "statement_hash": r["statement_hash"],
            "verdict": "agree" if r["elaborated"] else "disagree",
        }
        if not r["elaborated"]:
            # the root-cause rides the ledger row itself (the `reason`
            # field), so S4b's zero-unexplained-disagreements predicate is
            # ledger-measurable.
            row["reason"] = r.get("disagreement", {}).get(
                "reason", "unexplained")
        rows.append(row)
    if rows:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(common.canonical_json(row) + "\n")
    return rows


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="results/reflect_shadow.json")
    ap.add_argument("--ledger", default=None,
                    help="append agreement rows to this JSONL (S4a' durable "
                         "ledger); only written when Lean verdicts were "
                         "actually computed, never on deferred sweeps")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("reflect-shadow"):
        rep = run_shadow()
    with open(args.out, "w") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True)
    print(f"reflect_shadow: {sum(1 for r in rep['rows'] if r['status'] == 'probe')} "
          f"probes, verdicts={rep.get('verdicts')}")
    if args.ledger and isinstance(rep.get("verdicts"), dict):
        appended = append_ledger(
            rep, args.ledger, os.environ.get("GITHUB_RUN_ID", "local"))
        print(f"reflect_shadow: ledger +{len(appended)} rows -> {args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

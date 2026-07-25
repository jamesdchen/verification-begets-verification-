"""The AUTHORING kind of the `[lean-hammer]` batch ride (PLAN_HAMMER.md H1.3).

WHY THIS EXISTS.  The hammer batch is proof-SEARCH shaped: each entry carries a
compiled statement plus candidate scripts, and the lane asks the frozen ladder
to close it.  That shape cannot carry the other thing the loop needs a
toolchain for -- AUTHORING a slice extension, i.e. proposing new `FgReflect`
definitions and theorems and finding out whether they elaborate.  PLAN_FRAGMENT
§3.1 rule 3 makes tower-class work conditional on
`tools/lean_env_probe.py` reading `lean-local`; where it reads
`lean-absent:policy-denied` the container CANNOT iterate on Lean text at all,
and the rule binds -- unless there is some OTHER channel that elaborates
arbitrary Lean bytes under the same kernel primitives.  There is: this lane
already does exactly that.  The authoring kind is that channel made explicit,
and it rides the EXISTING trigger and the EXISTING entrypoint -- no workflow
change, therefore no ceremony (`.github/` is trust-surface PROTECTED).

THE HONEST BOUND, stated up front so no reader mistakes what it buys.  This
iterates at a SESSION BOUNDARY per ride -- one round-trip per push, not per
minute -- so it is a strictly slower authoring loop than a local toolchain and
it never becomes one.  It does not soften rule 3's capability condition either:
a candidate verdict is LANE EVIDENCE, the lane's own verdict remains FINAL, and
"it elaborated in the batch ride" is a reason to keep authoring, never a
done-predicate.

THE SPLICE.  A candidate is composed exactly the way `run/reflect_shadow.py`
composes its probes: the committed `tools/FgReflect.lean` source verbatim, then
the candidate text re-entering `namespace FgReflect` -- because the slice's own
names (`Tm.add`, `denote`, `checkAll_witness`) are UNQUALIFIED and resolve only
inside it (the first lane run refused exactly this, from outside; S1 ledger).
The committed slice is never modified: a candidate is a PROPOSAL appended to it,
and it becomes part of it only through an ordinary authored edit later.

THE VERDICT, in the ride's existing idiom (study `run/hammer_ride.py`):

  0. ESCAPE GATE FIRST (`buildloop/validate_lean.py`) over the COMPOSED bytes --
     the exact text the backend would see.  A refusal is terminal and the
     backend is NEVER reached; the gate is defense-in-depth, never the trust
     boundary (⚠T7), but a candidate that cannot pass it is not proof demand.
  1. `LeanBackend.elaborate(..., expect_sorry=False)` -- RUN 1, UNTRUSTED,
     artifacts only, mirroring `_verify_goal`'s statement/proof split (the
     statement leg is the one that may carry `sorry`; a candidate is the PROOF
     leg and may not).
  2. `LeanBackend.recheck` -- RUN 2, TRUSTED, the only verdict-bearing pass.
  3. FAIL CLOSED ON AUDIT SILENCE: a run-2 that reported no axiom audit
     (`audited` False) is NOT "no axioms" -- it yields no pass, exactly as
     `kernel.__init__._lean_kernel_channel` returns `unknown`.
  4. THE NEGATIVE CONTROL THAT MATTERS: `sorryAx` in the audited axiom set is
     never a pass.  A candidate that merely ELABORATES with a `sorry` in it is
     a well-formed hole, not a proof, and reporting it proved would be the one
     failure mode that poisons every downstream reading.  Axioms outside the
     measured whitelist are likewise not a pass.
  5. THE CLAIMED DECLARATIONS MUST APPEAR IN THE CANDIDATE'S OWN TEXT.  A
     proof that renames its own theorem -- or that claims `checkAll_witness`,
     which the slice ALREADY has -- must not pass on the strength of a name it
     did not introduce, so the search is over the candidate text, never over
     the composed module.

LANE PROTOCOL (PLAN_HAMMER.md H1, binding; reproduced because this module's
verdicts ride it).  The lane commits verdicts back with `GITHUB_TOKEN`, which
FIRES NO WORKFLOWS: that tip carries ZERO check runs and MUST NEVER be merged
(the self-merge rule's missing-trust-surface refusal enforces it mechanically).
The next driver session CONSUMES the verdicts, commits under its OWN
credentials -- which re-arms the checks -- and only then merges.

Lean-free, deterministic, clock-free: every function here is a pure function of
(candidate, backend).  Local tests cover the gate/refusal/deferral paths only;
elaboration itself is CI-lane work per the network policy.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:                       # repo-root exec shim (lane runs
    sys.path.insert(0, str(_ROOT))                   # this file directly)

from buildloop.validate_lean import validate_lean
from run.reflect_shadow import _REFLECT_SRC          # single-sourced slice path

# The axiom whitelist a spliced FgReflect probe may land on.  NOT invented here:
# it is Lean's benign core set (`kernel.__init__._STANDARD_AXIOMS`) plus the ONE
# extra the reflect lane has actually MEASURED -- `lcProof`, the compiler-erasure
# artifact any olean with compiled defs carries, never part of a proof term
# (baseline lane run 30049627938, pinned at tests/test_reflect_shadow.py:522).
# The equality against `_STANDARD_AXIOMS` is a tooth, so this can never drift
# into a private, quietly-widened list.
AUTHORING_AXIOM_WHITELIST = ("Classical.choice", "Quot.sound", "lcProof",
                             "propext")

# Declaration heads a candidate may introduce.  `example` is deliberately
# ABSENT: an `example` introduces no name, so it can never satisfy a claim.
_DECL_HEADS = ("theorem", "lemma", "def", "abbrev", "instance", "structure",
               "inductive")

_AUTHORING_NOTE = (
    "candidate FgReflect module text spliced inside `namespace FgReflect` the "
    "way run/reflect_shadow.py composes its probes; a row is lane evidence "
    "about ELABORATION, never a certificate and never a slice edit -- adopting "
    "a passed candidate is an ordinary authored edit in a later session")


def reflect_source(path=None) -> str:
    """The committed slice bytes a candidate is appended to (read, never
    written -- this module has no write path into `tools/FgReflect.lean`)."""
    return pathlib.Path(path or _REFLECT_SRC).read_text(encoding="utf-8")


def compose_candidate_module(module_text: str, *, candidate_id: str = "",
                             source: str = None) -> str:
    """Splice one candidate into the slice: the committed source verbatim, then
    the candidate RE-ENTERING `namespace FgReflect` (the quoter's unqualified
    names resolve only inside it).  Deterministic in its inputs alone -- no
    clock, no environment, so two rides over one candidate compose byte-identical
    text and the elaboration cache (L2) sees one key."""
    header = "-- authoring candidate (PLAN_HAMMER H1.3)"
    if candidate_id:
        header += f": {candidate_id}"
    return (reflect_source(source) + "\n\n"
            "namespace FgReflect\n\n"
            + header + "\n"
            "-- PROPOSAL ONLY: elaborated appended to the committed slice, never\n"
            "-- written into it; adoption is a separate authored edit.\n"
            + module_text.rstrip("\n") + "\n\n"
            "end FgReflect\n")


def declares_missing(module_text: str, declares) -> list:
    """The claimed names that the CANDIDATE'S OWN TEXT does not introduce.

    Searched over the candidate text and NEVER over the composed module: a
    candidate must not pass on the strength of a name the committed slice
    already carries, and a proof that renames its own theorem must FAIL rather
    than quietly close something else."""
    heads = "|".join(_DECL_HEADS)
    missing = []
    for name in declares:
        pat = (r"(?<![\w.'])(?:" + heads + r")\s+" + re.escape(str(name))
               + r"(?![\w.'])")
        if re.search(pat, module_text) is None:
            missing.append(str(name))
    return missing


def not_run_row(candidate_id: str) -> dict:
    """A candidate that never ran (Lean absent, or past the ride's deadline):
    every verdict-bearing field is honestly ``null``, NEVER ``false`` -- the
    `run/hammer_ride.py::_not_run_row` idiom, one kind over."""
    return {"candidate_id": candidate_id, "gate_ok": None, "elaborated": None,
            "replayed": None, "declared_missing": None, "axioms": None,
            "passed": None, "detail": None}


def _row(cid, *, gate_ok=None, elaborated=None, replayed=None,
         declared_missing=None, axioms=None, passed=None, detail=None) -> dict:
    return {"candidate_id": cid, "gate_ok": gate_ok, "elaborated": elaborated,
            "replayed": replayed, "declared_missing": declared_missing,
            "axioms": axioms, "passed": passed, "detail": detail}


def verify_candidate(entry: dict, backend, *, source: str = None):
    """Verify one authoring candidate.  Returns ``(row, deferred)``: ``deferred``
    True iff the toolchain went ``unavailable`` mid-candidate (the caller stops
    and defers the rest, exactly as `_verify_goal` does).  ``row`` carries the
    frozen 8-key authoring verdict schema."""
    cid = entry.get("candidate_id", "")
    module_text = entry.get("module_text") or ""
    declares = list(entry.get("declares") or [])
    composed = compose_candidate_module(module_text, candidate_id=cid,
                                        source=source)

    # --- 0. escape gate, BEFORE anything else -- the backend is not reached. --
    ok, why = validate_lean(composed)
    if not ok:
        return _row(cid, gate_ok=False, passed=False,
                    detail=f"escape-gate refusal: {why}"), False

    # A candidate that claims NOTHING can never be checked against anything, so
    # it is a malformed proposal rather than proof demand: refused pre-flight,
    # named, and never spent on a lane elaboration.
    if not declares:
        return _row(cid, gate_ok=True, declared_missing=[], passed=False,
                    detail="candidate declares no names -- nothing to verify"), False

    missing = declares_missing(module_text, declares)

    # --- 1. RUN 1 (UNTRUSTED): elaborate the composed bytes. -----------------
    el = backend.elaborate(composed, expect_sorry=False)
    if el.get("unavailable"):
        return not_run_row(cid), True
    if not el.get("ok"):
        return _row(cid, gate_ok=True, elaborated=False, replayed=False,
                    declared_missing=missing, axioms=[], passed=False,
                    detail=(el.get("detail") or el.get("reason")
                            or "elaboration failed (no transcript)")), False

    # --- 2. RUN 2 (TRUSTED): kernel replay + axiom audit. --------------------
    rc = backend.recheck(el.get("olean_path"))
    if rc.get("unavailable"):
        return not_run_row(cid), True
    if not rc.get("ok"):
        return _row(cid, gate_ok=True, elaborated=True, replayed=False,
                    declared_missing=missing, axioms=[], passed=False,
                    detail=(rc.get("transcript") or rc.get("reason")
                            or "kernel replay refused (no transcript)")), False
    if not rc.get("audited"):
        # FAIL CLOSED on auditor silence: no audit -> no verdict.  Never read
        # as "no axioms" (⚠ _lean_kernel_channel).
        return _row(cid, gate_ok=True, elaborated=True, replayed=False,
                    declared_missing=missing, axioms=[], passed=False,
                    detail="axiom audit silent -- fail closed, no verdict"), False

    axioms = sorted(rc.get("axioms", []))

    # --- 3. the two things elaboration alone does NOT establish. -------------
    reasons = []
    if "sorryAx" in axioms:
        reasons.append("sorryAx in the audited axiom set -- the candidate "
                       "elaborates with a hole, which is not a proof")
    outside = [a for a in axioms if a not in AUTHORING_AXIOM_WHITELIST
               and a != "sorryAx"]
    if outside:
        reasons.append("axioms outside the measured whitelist: "
                       + ", ".join(outside))
    if missing:
        reasons.append("claimed declarations absent from the candidate text: "
                       + ", ".join(missing))
    return _row(cid, gate_ok=True, elaborated=True, replayed=True,
                declared_missing=missing, axioms=axioms,
                passed=not reasons,
                detail=("; ".join(reasons) if reasons else None)), False


def run_authoring(entries, backend, *, source: str = None,
                  budget_spent=lambda: False):
    """Verify the authoring entries in order.  Returns ``(rows, status)`` where
    status is ``complete`` / ``deferred`` / ``partial`` -- the ride's own
    vocabulary.  ``budget_spent`` is the caller's deadline predicate (the clock
    drives CONTROL FLOW ONLY; it never enters a report byte)."""
    entries = list(entries)
    rows = []
    for i, entry in enumerate(entries):
        if budget_spent():
            rows.extend(not_run_row(e.get("candidate_id", ""))
                        for e in entries[i:])
            return rows, "partial"
        row, deferred = verify_candidate(entry, backend, source=source)
        if deferred:
            rows.extend(not_run_row(e.get("candidate_id", ""))
                        for e in entries[i:])
            return rows, "deferred"
        rows.append(row)
    return rows, "complete"


# ===========================================================================
# CONSUMPTION (session-side): committed verdicts -> a mechanical next move.
# ===========================================================================
PASSED = "PASSED"
FAILED = "FAILED-WITH-TRANSCRIPT"
NOT_RUN = "NOT-RUN"


def classify(row: dict) -> str:
    """One row -> the three-way readout the next session iterates on.  A row
    that never ran is NOT-RUN (honestly null), never a failure; anything that
    ran and did not pass is FAILED-WITH-TRANSCRIPT and carries the `detail`
    that says why, so the next round is a mechanical edit rather than a guess."""
    if row.get("passed") is True:
        return PASSED
    if row.get("passed") is None:
        return NOT_RUN
    return FAILED


def report(verdicts: dict, batch: dict = None) -> dict:
    """Per-candidate PASSED / FAILED-WITH-TRANSCRIPT / NOT-RUN from the
    COMMITTED verdicts, plus the batch's claimed declarations for context.
    Pure and clock-free; a batch/verdicts pair with no authoring entries yields
    the honest empty report rather than an error."""
    declared = {e.get("candidate_id"): list(e.get("declares") or [])
                for e in (batch or {}).get("authoring", [])}
    rows = verdicts.get("authoring_rows") or []
    out = []
    for row in rows:
        cid = row.get("candidate_id")
        out.append({"candidate_id": cid,
                    "status": classify(row),
                    "declares": declared.get(cid, []),
                    "declared_missing": row.get("declared_missing"),
                    "axioms": row.get("axioms"),
                    "detail": row.get("detail")})
    totals = {"n_candidates": len(out),
              "n_passed": sum(1 for r in out if r["status"] == PASSED),
              "n_failed": sum(1 for r in out if r["status"] == FAILED),
              "n_not_run": sum(1 for r in out if r["status"] == NOT_RUN)}
    return {"verdicts_status": verdicts.get("status"),
            "lean_available": verdicts.get("lean_available"),
            "totals": totals,
            "candidates": out,
            "note": _AUTHORING_NOTE}


def render_report_text(rep: dict) -> str:
    t = rep["totals"]
    L = [f"reflect_ride report: verdicts={rep['verdicts_status']} "
         f"lean_available={rep['lean_available']}",
         f"  candidates={t['n_candidates']}  passed={t['n_passed']}  "
         f"failed={t['n_failed']}  not-run={t['n_not_run']}"]
    for r in rep["candidates"]:
        L.append(f"  [{r['status']}] {r['candidate_id']}"
                 + (f"  declares={','.join(r['declares'])}" if r["declares"]
                    else ""))
        if r.get("declared_missing"):
            L.append(f"      missing: {', '.join(r['declared_missing'])}")
        if r.get("detail"):
            for line in str(r["detail"]).strip().splitlines()[-12:]:
                L.append("      | " + line)
    if not rep["candidates"]:
        L.append("  (no authoring entries in the committed verdicts)")
    return "\n".join(L) + "\n"


def main(argv=None):
    """Session-side readout of the committed lane verdicts.

    LANE PROTOCOL (binding, PLAN_HAMMER.md H1): the tip this reads was pushed by
    the lane with `GITHUB_TOKEN`, so it fired no workflows and carries ZERO
    check runs -- it MUST NEVER be merged.  The session that runs this command
    consumes the verdicts, commits under its own credentials (re-arming the
    checks), and only then merges."""
    ap = argparse.ArgumentParser(description=main.__doc__.splitlines()[0])
    ap.add_argument("--verdicts", default=None,
                    help="path to results/hammer_verdicts.json")
    ap.add_argument("--batch", default=None,
                    help="path to results/hammer_batch.json (declares context)")
    ap.add_argument("--json", action="store_true",
                    help="emit the report as canonical json")
    args = ap.parse_args(argv)

    from bench import bench_hammer
    import common
    vp = pathlib.Path(args.verdicts) if args.verdicts else bench_hammer.VERDICTS_PATH
    bp = pathlib.Path(args.batch) if args.batch else bench_hammer.BATCH_PATH
    verdicts = (json.loads(vp.read_text(encoding="utf-8")) if vp.exists()
                else {"status": "not-run", "lean_available": False})
    batch = json.loads(bp.read_text(encoding="utf-8")) if bp.exists() else None
    rep = report(verdicts, batch)
    print(common.canonical_json(rep) if args.json else render_report_text(rep),
          end="" if not args.json else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""S4a -- the abstract-algebra discharge route as a SHADOW channel beside
the anchor ladder.

THE PROPER ROUTE (PLAN_FRAGMENT §4 P5: "abstract algebra discharge route:
TRUST ROOT, NOT A PURCHASE").  A new rung is not a purchase and no census
price may shortcut it -- the only path is the PLAN_REFLECT
S4a -> S4a' -> S4b pattern verbatim: a shadow channel PERMANENTLY PAIRED
with the incumbent ladder, a durable differential-agreement ledger, a
NUMERIC entrance predicate measured from that ledger, and then ONE ceremony
commit with explicit maintainer sign-off.  ``ANCHOR_CERT_CHANNELS`` and
``ANCHOR_DISCHARGE_RUNGS`` are PINNED (kernel/certs.py, FI-KA-1/4);
``ANCHOR_LIVE_DISCHARGES`` is derived from them.  Nothing in this module
reads, imports or writes any of the three, the kernel, or any cert byte --
they are named HERE, in prose, and nowhere else in this file (a tooth greps
for exactly that).

WHAT THE SHADOW CHANNEL DOES.  The tap point is ``results/proof_queue.json``
-- the committed, subject-hash-keyed worklist, the only stream in the repo
that actually reaches goals -- read STRICTLY read-only.  For each queued
goal whose family is ring-shaped, the channel rebuilds the goal's own
proposition from the committed reading behind its ``subject`` and wraps it
as a self-contained probe::

    example : <the goal's own proposition> := by ring_nf

The subject hash is RECOMPUTED and compared against the queue's committed
``subject.sha256`` before a probe is built, so a probe can never assert
something other than the goal the ladder is being measured on; a mismatch
is recorded staleness (a named skip), never a silent re-aim.

THE DIFFERENTIAL.  The incumbent ladder already closes (or refuses) these
goals; the candidate route runs BESIDE it and every elaboration verdict is
recorded -- agreements are the evidence S4b's ceremony is gated on,
disagreements are first-class rows carrying their own root cause.  Two
refusal classes are classified from the TRANSCRIPT rather than guessed: a
deterministic budget timeout, and the candidate tactic simply not being
reachable under the pinned narrow import set (``common.MATHLIB_IMPORTS``,
D15 -- widening that set is its own decision and is NOT part of this
cycle).  An unreachable tactic is therefore a MEASURED, named refusal that
the first lane run reports, never a quiet import widening.

WHAT IS DELIBERATELY ABSENT.  No CI sweep step is wired (``.github/`` is
ceremony scope), so the ledger stays unseeded until a maintainer wires the
lane step; the ledger-measured teeth skip honestly until then.  Elaboration
itself is CI-lane-only (no local Lean in remote containers): here the
probes are BUILT and gate-validated, and the sweep defers verbatim.

Frozen skip vocabulary (a skip is never a failure):
  ``family-not-algebra:<family>`` -- the queue row's family is not one a
    ring/group-normalization route is even a candidate for.
  ``no-lean-prop:unresolved-subject`` -- the queue row's subject resolves to
    no committed reading (the row records demand, not a proposition).
  ``no-lean-prop:subject-hash-mismatch`` -- recorded STALENESS: the reading
    behind the subject no longer compiles to the pinned subject hash.
  ``route-not-applicable:status-<status>`` -- the row is not ``queued``
    (infrastructure refusal / shadow-refuted demand); never proof demand.
  ``route-not-applicable:unrenderable`` -- the compiler itself refuses the
    reading, so there is no proposition to probe.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop.validate_lean import validate_lean
from generators.math_compile import compile_math_reading, CompileError
from run.anchor import _load_reading

# The committed artifacts this channel reads.  BOTH are read-only here: the
# queue is the demand stream, the bench state is where the queue's own
# reconciler took the readings from (tools/proof_queue.py), so joining back
# through it reproduces the queue's derivation instead of inventing one.
QUEUE = "results/proof_queue.json"
BENCH = "results/formalize_bench_state.jsonl"

# The durable evidence store.  NOT created here and NOT seeded by a local
# run: rows only ever come from a real lane sweep (see the module docstring).
LEDGER = "results/algebra_agreement.jsonl"

# ONE candidate route, named honestly.  Not a family of tactics, not an
# alias set: the thing S4b would eventually be asked to pin is a single
# route name, so the shadow measures exactly that one and nothing else.
TACTIC = "ring_nf"
ROUTE = f"algebra/{TACTIC}"

# The families a ring/group-normalization route is even a candidate for.
# `linear` is the queue's name for purely arithmetic/relational goals -- the
# ring-shaped class.  Everything else (dvd / parity / gcd / exists) is a
# NAMED skip, never a probe that would measure the wrong thing.
ALGEBRA_FAMILIES = ("linear",)

# The frozen skip vocabulary (prefix form), single-sourced for the teeth.
SKIP_PREFIXES = ("family-not-algebra:", "no-lean-prop",
                 "route-not-applicable:")

# The compiler pins its emitted shape as `theorem <thm> : <prop> := sorry`
# (generators/math_compile.py module docstring); slicing at that shape is
# reading the compiler's own contract, and `_prop_of` re-composes and
# byte-compares before returning, so a drifted shape is loud, never silent.
_STATEMENT_RE = re.compile(
    r"\Atheorem\s+(?P<thm>\S+)\s+:\s+(?P<prop>.*)\s+:=\s+sorry\Z", re.S)

# Transcript markers for the two EXPLAINED refusal classes.  Data-derived
# classification, no tuned constants: anything else stays `unexplained`, so
# the entrance predicate can never be met by an unread failure.
_TIMEOUT_MARK = "maximum number of heartbeats"
_MISSING_MARKS = ("unknown tactic", "unknown identifier", "unknown constant")


def _root(root=None) -> str:
    return root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def builder_sha() -> str:
    """sha256 of THIS builder's source -- folded into every ledger row so a
    row always names the exact code that produced it (the emitter_hash
    discipline; a changed builder is a visible change, never a silent one)."""
    with open(os.path.abspath(__file__), "rb") as fh:
        return common.sha256_bytes(fh.read())


def load_queue(root=None) -> dict:
    """The committed goal worklist, verbatim (read-only)."""
    with open(os.path.join(_root(root), *QUEUE.split("/"))) as fh:
        return json.load(fh)


def bench_readings(root=None) -> dict:
    """``source_id -> reading_json`` over the governed arm's certified bench
    rows -- the same selection tools/proof_queue.py made when it built the
    queue.  FIRST occurrence wins, so the map is order-deterministic even if
    the append-only bench state ever repeats a source_id."""
    out: dict = {}
    with open(os.path.join(_root(root), *BENCH.split("/"))) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("arm") == "governed" and r.get("certified") is True:
                out.setdefault(r["source_id"], r["reading_json"])
    return out


def _prop_of(reading):
    """``(prop_text, statement_hash)`` for one reading, sliced out of the
    COMPILER'S OWN emitted statement -- never re-rendered here, so the probe
    can never drift from what the statement compiles to."""
    out = compile_math_reading(reading)
    m = _STATEMENT_RE.match(out["lean_text"])
    if m is None:
        raise RuntimeError("compiled statement no longer matches the pinned "
                           "`theorem <thm> : <prop> := sorry` shape: "
                           f"{out['lean_text'][:120]!r}")
    prop, thm = m.group("prop"), m.group("thm")
    if f"theorem {thm} : {prop} := sorry" != out["lean_text"]:
        raise RuntimeError("proposition slice does not re-compose to the "
                           "compiled statement (byte check)")
    return prop, out["statement_hash"]


def algebra_probe(goal: dict, *, readings=None, root=None) -> dict:
    """Build the paired algebra probe for one committed queue goal, or a
    named skip.  Deterministic (same goal -> byte-identical probe) and never
    touches Lean itself; the caller elaborates."""
    ref = goal["subject"]["ref"]
    base = {"route": ROUTE, "source": ref}
    status = goal.get("status")
    if status != "queued":
        return dict(base, status="skip",
                    reason=f"route-not-applicable:status-{status}")
    family = goal.get("family")
    if family not in ALGEBRA_FAMILIES:
        return dict(base, status="skip",
                    reason=f"family-not-algebra:{family}")
    readings = bench_readings(root) if readings is None else readings
    doc = readings.get(ref)
    if doc is None:
        return dict(base, status="skip",
                    reason="no-lean-prop:unresolved-subject")
    reading = _load_reading(json.loads(doc), ref)
    try:
        prop, statement_hash = _prop_of(reading)
    except CompileError:
        return dict(base, status="skip",
                    reason="route-not-applicable:unrenderable")
    if statement_hash != goal["subject"]["sha256"]:
        # the queue pins the subject by hash; a drift is recorded staleness
        # (regenerate the queue), NEVER a probe re-aimed at a different goal.
        return dict(base, status="skip",
                    reason="no-lean-prop:subject-hash-mismatch")
    lean = (f"-- algebra-shadow probe (S4a, route {ROUTE}): the committed\n"
            "-- queue goal's OWN proposition, discharged by the candidate\n"
            "-- normalization route alone.  Nothing here enters a cert path.\n"
            f"set_option maxHeartbeats {common.LEAN_MAXHEARTBEATS} in\n"
            f"example : {prop} := by {TACTIC}\n")
    ok, why = validate_lean(lean)
    if not ok:
        # invariant violation, not a skip (the math_witness convention).
        raise RuntimeError(f"algebra-shadow probe failed the escape gate: "
                           f"{why}")
    return dict(base, status="probe", lean=lean, prop=prop, family=family,
                probe_sha=common.sha256_bytes(lean.encode()),
                statement_hash=statement_hash)


def _classify(detail: str) -> str:
    """Root-cause a refusal from the TRANSCRIPT (never guessed).  The two
    explained classes are a deterministic budget timeout and the candidate
    tactic being unreachable under the pinned narrow import set -- the
    latter is a decision for a later cycle, recorded here, not papered over
    by widening ``common.MATHLIB_IMPORTS``."""
    if _TIMEOUT_MARK in detail:
        return "deterministic-timeout-at-heartbeat-cap"
    if TACTIC in detail and any(m in detail for m in _MISSING_MARKS):
        return "tactic-unavailable-under-pinned-imports"
    return "unexplained"


def run_shadow(root=None) -> dict:
    """The shadow sweep over the committed proof queue, one row per (goal,
    route).  Lean present: each probe elaborates (RUN-1) and
    agreement/disagreement is recorded; absent: probes are built and the
    verdicts are honestly deferred (and NOTHING is written to the ledger)."""
    root = _root(root)
    queue = load_queue(root)
    readings = bench_readings(root)
    rows = [algebra_probe(g, readings=readings, root=root)
            for g in queue["goals"]]
    report = {
        "tool": "algebra_shadow",
        "channel": "shadow (paired, non-cert)",
        "route": ROUTE,
        "module_sha": builder_sha(),
        "queue_derived_from": queue.get("derived_from", {}),
        "honesty": ("RUN-1 elaboration evidence beside the pinned ladder; "
                    "cert channels and discharge vocabulary untouched.  "
                    "Disagreement rows are first-class; S4b's ceremony is "
                    "gated on accumulated agreement plus explicit maintainer "
                    "sign-off, never on this report."),
        "rows": rows,
    }
    if not common.lean_available():
        report["verdicts"] = "deferred: lean toolchain absent"
        return report
    from kernel.backends import LeanBackend
    be = LeanBackend()
    agree = disagree = 0
    for r in rows:
        if r["status"] != "probe":
            continue
        res = be.elaborate(r["lean"], expect_sorry=False)
        r["elaborated"] = bool(res.get("ok"))
        if r["elaborated"]:
            agree += 1
        else:
            disagree += 1
            detail = str(res.get("detail", "")) + str(res)
            r["disagreement"] = {"reason": _classify(detail),
                                 "transcript": str(res)[:1500]}
    report["verdicts"] = {"agree": agree, "disagree": disagree}
    return report


def append_ledger(path, rows, lane_run_id, module_sha=None) -> list:
    """S4a'(i): append one agreement/disagreement row per ELABORATED probe to
    the durable JSONL ledger -- the evidence store S4b's entrance predicate is
    measured from.  APPEND-ONLY, the import_driver._Ledger convention: rows
    are only ever appended (canonical JSON, one line each), so any prior
    ledger content remains a byte-prefix of the new file; there is NO
    truncate or rewrite path.  Skips never reach the ledger (a skip is not a
    verdict).  Returns the rows appended."""
    module_sha = module_sha or builder_sha()
    out = []
    for r in rows:
        if r.get("status") != "probe" or "elaborated" not in r:
            continue
        row = {
            "lane_run_id": str(lane_run_id),
            "module_sha": module_sha,
            "probe_sha": r["probe_sha"],
            "route": r.get("route", ROUTE),
            # a workflow RE-RUN re-appends under the same lane_run_id; the
            # attempt number keeps such duplicates distinguishable in the
            # append-only log instead of silently inflating row counts.
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
            "source": r["source"],
            "statement_hash": r["statement_hash"],
            "verdict": "agree" if r["elaborated"] else "disagree",
        }
        if not r["elaborated"]:
            # the root cause rides the ledger row itself, so S4b's
            # zero-unexplained-disagreements axis is ledger-measurable.
            row["reason"] = r.get("disagreement", {}).get(
                "reason", "unexplained")
        out.append(row)
    if out:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            for row in out:
                fh.write(common.canonical_json(row) + "\n")
    return out


def discharge_algebra(goal, *, readings=None, root=None) -> dict:
    """SHADOW-MODE discharge: mint the exact record shape a promoted runner
    path would emit -- route-qualified claim naming included -- WITHOUT
    entering the cert vocabulary (nothing here is a certificate; the pinned
    surfaces stay untouched).  Pre-building this lets a future ceremony
    commit flip already-lane-tested machinery live instead of shipping new
    code and its first evidence in the same diff."""
    r = algebra_probe(goal, readings=readings, root=root)
    if r["status"] != "probe":
        return {"status": "skip", "reason": r["reason"], "route": ROUTE,
                "source": r["source"]}
    return {"status": "proposed",
            "route": ROUTE,
            "source": r["source"],
            "statement_hash": r["statement_hash"],
            "module_sha": builder_sha(),
            "probe_sha": r["probe_sha"],
            "lean": r["lean"]}


def replay_algebra(goal, record, *, readings=None, root=None) -> dict:
    """Deterministic replay of a shadow discharge record: rebuild the probe
    from the COMMITTED queue row and re-derive every hash; byte-identity of
    probe_sha / module_sha / statement_hash is the replay gate (a record can
    never mean something the queue does not rebuild to)."""
    rebuilt = discharge_algebra(goal, readings=readings, root=root)
    ok = (rebuilt.get("status") == "proposed"
          and rebuilt.get("probe_sha") == record.get("probe_sha")
          and rebuilt.get("module_sha") == record.get("module_sha")
          and rebuilt.get("statement_hash") == record.get("statement_hash"))
    return {"ok": ok, "rebuilt_status": rebuilt.get("status")}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="results/algebra_shadow.json")
    ap.add_argument("--ledger", default=None,
                    help="append agreement rows to this JSONL (S4a' durable "
                         "ledger); only written when Lean verdicts were "
                         "actually computed, never on deferred sweeps")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("algebra-shadow"):
        rep = run_shadow()
    with open(args.out, "w") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True)
    print(f"algebra_shadow: "
          f"{sum(1 for r in rep['rows'] if r['status'] == 'probe')} probes, "
          f"verdicts={rep.get('verdicts')}")
    if args.ledger and isinstance(rep.get("verdicts"), dict):
        appended = append_ledger(
            args.ledger, rep["rows"], os.environ.get("GITHUB_RUN_ID", "local"))
        print(f"algebra_shadow: ledger +{len(appended)} rows -> {args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

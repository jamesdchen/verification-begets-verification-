#!/usr/bin/env python3
"""WS-R -- the UNBOUNDED-statement hammer bench (assemble + consume).

WHAT THIS IS, AND ITS DELTA FROM THE PROBE.  ``tools/flywheel_probe.py`` is the
repo's "hammer close-rate meter, v0": it renders GROUNDED INSTANCES of corpus
conclusions (``∀ (n : Int), n = 3 -> <body>`` -- a value pinned per prop) and
discharges them through ``LeanBackend.eval_props``, measuring what fraction of a
fixed prop set the frozen ladder closes.  THIS bench renders the UNBOUNDED
statements themselves -- the full compiled theorem ``∀ binders, hyps → concl``
(``∀``/``∃`` and all) -- and asks the ladder to close the WHOLE statement, not a
numeral instance.  Both share the ONE rendering path: the compiler's own
``generators/math_compile`` (``compile_math_reading`` for the statement,
``_render_pred`` transitively) so bench text can never drift from what statements
compile to, and both route discharge through the same ``kernel.backends``
``LeanBackend`` code path the kernel channel uses.

REUSE, NEVER DUPLICATE.  The rung vocabulary is IMPORTED from
``generators.math_witness.RUNGS`` -- never redeclared (equality tooth vs
``kernel.certs.ANCHOR_DISCHARGE_RUNGS``, the ``tests/test_import_rt.py`` RUNGS
precedent).  ∃-shaped goals route their proof scripts through the anchor
kernel-leg template machinery (``math_witness.emit_witness_proofs`` -- the same
emitter ``run/anchor.py`` drives), NOT raw rungs.  ∀-shaped goals get an intro
prelude built from the EXISTING closed discharge vocabulary only (``intro`` +
the four ladder rungs -- byte-for-byte the ``math_witness._emit_proofs`` /
``kernel/certs.py`` anchor-discharge surface); no new tactic surface whatsoever.

LANE-ADJACENT, LEAN-LAST.  ``assemble`` and ``consume`` are pure, deterministic,
Lean-free.  ``assemble`` emits ``results/hammer_batch.json`` carrying the EXACT
rendered Lean bytes the CI lane elaborates (``run/hammer_ride.py``); the verdicts
pin those bytes.  ``consume`` turns the lane's ``results/hammer_verdicts.json``
into the per-rung / per-family closure readout.  Like ``run/anchor.py`` and
``run/import_rt.py`` this is NOT in the ``regen_downstream`` DAG -- it rides the
Lean lane, not the offline regen.

Honesty (the ``import_rt`` precedent): a verdict row is LANE EVIDENCE toward a
future kernel statement-cert / proof-cert mint, NEVER a certificate.  A statement
that fails to elaborate is STATEMENT-CERT demand; a statement that elaborates but
whose ladder closes nothing is TACTIC (H3) demand -- reported separately.  The
upgrade path is nothing -> statement-cert -> proof-cert (two lane steps).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:                       # repo-root exec shim (bench/)
    sys.path.insert(0, str(_ROOT))

import common
from generators.math_reading import parse_math_reading
from generators.math_compile import compile_math_reading, _pred_refs
from generators import math_witness

# Single-sourced rung vocabulary (NEVER redeclared -- the import_rt precedent).
RUNGS = math_witness.RUNGS

# The bounded-shadow search bound the ∃ emitter runs under (mirrors
# run/anchor.py::BOUND; the bound rides the SEARCH + provenance, never the proof
# bytes -- FI-KA-1, so emitting at any bound yields byte-identical proofs).
DEFAULT_BOUND = 8

# Deterministic per-ride cap (the 120-min lane budget / worst-case 3-10 min per
# goal -- PLAN_HAMMER batch-cap rationale).  Flag-overridable.
DEFAULT_CAP = 24

BATCH_SCHEMA = "hammer-batch/v1"
VERDICTS_SCHEMA = "hammer-verdicts/v1"
READOUT_SCHEMA = "hammer-readout/v1"

BATCH_PATH = _ROOT / "results" / "hammer_batch.json"
VERDICTS_PATH = _ROOT / "results" / "hammer_verdicts.json"
READOUT_JSON_PATH = _ROOT / "results" / "hammer_readout.json"
READOUT_MD_PATH = _ROOT / "results" / "hammer_readout.md"

_BATCH_NOTE = ("UNBOUNDED compiled statements (∀/∃ and all), NOT the flywheel "
               "probe's grounded numeral instances; rendered through the "
               "compiler's own math_compile, discharged through the "
               "math_witness ladder / anchor kernel-leg emitter")
_EVIDENCE_NOTE = ("rows are lane evidence toward a future kernel statement-cert "
                  "/ proof-cert mint, NEVER certificates (the run/import_rt.py "
                  "precedent); no per-row wall time -- byte-stability law")


# ===========================================================================
# reading resolution (ref -> MathReading).  Injectable; the default reads the
# committed corpus.  Tests inject a synthetic resolver (the import_rt fake
# pattern), so assemble is a pure function of (queue, resolver).
# ===========================================================================
def _synthetic_source(doc: dict) -> str:
    """A groundedness-satisfying source for ``doc`` (the run/anchor.py pattern):
    the compiled statement is independent of the source, so the rendered bytes
    are byte-identical to the real pipeline's; only the quote gate consumes it."""
    return "  ".join(s.get("quote", "") for s in doc.get("statements", [])
                     if s.get("quote"))


def _reading_from_doc(doc: dict):
    return parse_math_reading(json.dumps(doc), _synthetic_source(doc))


def default_resolver(goal: dict, *, root: pathlib.Path = _ROOT):
    """Map one queue goal to its authored ``MathReading`` from the committed
    corpus, or ``None`` (honest unresolved -- never a crash).

      * ``anchor-exists`` -> ``wp_auth_readings.READINGS[ref]`` (the 41-44 ∃
        corpus run/anchor.py drives).
      * ``bench-certified`` -> the governed-arm certified row of
        ``results/formalize_bench_state.jsonl`` whose ``source_id`` == ref.

    ``rt-failed`` never reaches assemble (those rows are ``infra-refused`` in the
    queue, never ``queued``), so it has no resolver branch."""
    ref = goal.get("subject", {}).get("ref")
    source = goal.get("source")
    if source == "anchor-exists":
        try:
            import wp_auth_readings
        except Exception:
            return None
        doc = wp_auth_readings.READINGS.get(ref)
        return _reading_from_doc(doc) if doc else None
    if source == "bench-certified":
        path = pathlib.Path(root) / "results" / "formalize_bench_state.jsonl"
        if not path.exists():
            return None
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if (row.get("source_id") == ref and row.get("certified")
                    and row.get("arm") == "governed"):
                return _reading_from_doc(json.loads(row["reading_json"]))
        return None
    return None


# ===========================================================================
# rendering: statement + proof scripts (the EXACT lean bytes the lane runs).
# ===========================================================================
def _has_exists(reading) -> bool:
    return any(s["lf"].get("binder") == "exists"
               for s in reading.by_kind("quantifier"))


def _forall_intro_order(reading) -> list:
    """The ``intro`` binder order for a ∀-only reading, MIRRORING the compiler's
    binder emission (``generators/math_compile.compile_math_reading``): leading
    referenced-but-unbound objects (sorted) then the ∀-quantifier objects in
    id/listed order.  Pure structural -- no term rendering, no new vocabulary."""
    q_stmts = sorted(reading.by_kind("quantifier"), key=lambda s: s["id"])
    forall_objs = []
    bound_q = set()
    for s in q_stmts:
        objs = s["lf"]["objects"]
        bound_q.update(objs)
        if s["lf"]["binder"] == "forall":
            forall_objs.extend(objs)
    referenced = set()
    for s in reading.by_kind("hypothesis") + reading.by_kind("conclusion"):
        referenced.update(_pred_refs(s["lf"]["pred"]))
    leading = sorted(referenced - bound_q)
    return leading + forall_objs


def _forall_scripts(reading, statement_lean_text: str) -> list:
    """One proof script per rung for a ∀-only goal: the compiled statement with
    ``:= sorry`` replaced by ``:= by intro <binders>; intro <hyps>; <rung>``.
    The ONLY tactics are ``intro`` and the four ladder rungs -- exactly the
    ``math_witness._emit_proofs`` surface minus the ∃ ``refine`` (no new tactic
    surface, ⚠ house law)."""
    assert statement_lean_text.endswith(" := sorry")
    head = statement_lean_text[:-len(" := sorry")]
    intro_order = _forall_intro_order(reading)
    hyp_ids = [s["id"] for s in
               sorted(reading.by_kind("hypothesis"), key=lambda s: s["id"])]
    scripts = []
    for rung in RUNGS:
        lines = [" := by"]
        if intro_order:
            lines.append("  intro " + " ".join(intro_order))
        if hyp_ids:
            lines.append("  intro " + " ".join("hyp_" + h for h in hyp_ids))
        lines.append("  " + rung)
        scripts.append({"discharge": rung, "lean_text": head + "\n".join(lines)})
    return scripts


def render_goal(goal: dict, reading, *, bound: int = DEFAULT_BOUND) -> dict:
    """Render one queued goal into a batch entry: the compiled statement (``:=
    sorry`` form, for the lane's statement-stage elaborate) plus the ordered
    proof scripts (first-success ladder order).  ∃ goals route through the anchor
    kernel-leg emitter; ∀ goals through the intro-prelude builder."""
    compiled = compile_math_reading(reading)
    statement_lean_text = compiled["lean_text"]
    statement_hash = compiled["statement_hash"]
    skip_reason = None
    if _has_exists(reading):
        shape = "exists"
        emit = math_witness.emit_witness_proofs(reading, bound=bound)
        if emit["status"] == "emitted":
            scripts = [{"discharge": p["discharge"], "lean_text": p["lean_text"]}
                       for p in emit["proofs"]]
        else:
            scripts = []               # honest: no witness template found/searchable
            skip_reason = "emitter-skip:" + emit.get("reason", "unknown")
    else:
        shape = "forall"
        scripts = _forall_scripts(reading, statement_lean_text)
    return {"goal_id": goal["goal_id"],
            "family": goal.get("family", "other"),
            "shape": shape,
            "subject_ref": goal.get("subject", {}).get("ref"),
            "statement_hash": statement_hash,
            "statement_lean_text": statement_lean_text,
            "scripts": scripts,
            "skip_reason": skip_reason}


# ===========================================================================
# ASSEMBLE: queue -> results/hammer_batch.json (deterministic, byte-stable).
# ===========================================================================
def assemble(queue_path=None, *, resolver=None, cap: int = DEFAULT_CAP,
             bound: int = DEFAULT_BOUND) -> dict:
    """Build the hammer batch from the ``queued``-status goals of the proof queue
    (the PROOF_QUEUE.JSON SCHEMA CONTRACT).  Deterministic: goals are taken in
    the queue's own order up to ``cap``; a missing queue file yields the honest
    empty bootstrap batch (no exception).  ``resolver`` maps a goal to its
    ``MathReading`` (default: the committed corpus)."""
    resolver = resolver or default_resolver
    queue_sha = None
    goals_in = []
    if queue_path is not None:
        qp = pathlib.Path(queue_path)
        if qp.exists():
            raw = qp.read_bytes()
            queue_sha = common.sha256_bytes(raw)
            goals_in = json.loads(raw.decode("utf-8")).get("goals", [])

    queued = [g for g in goals_in if g.get("status") == "queued"]
    capped = queued[:cap]

    goals_out = []
    unresolved = []
    for g in capped:
        reading = resolver(g)
        if reading is None:
            unresolved.append(g["goal_id"])
            continue
        goals_out.append(render_goal(g, reading, bound=bound))

    return {"schema": BATCH_SCHEMA,
            "cap": cap,
            "bound": bound,
            "queue_sha256": queue_sha,
            "n_queued": len(queued),
            "note": _BATCH_NOTE,
            "goals": goals_out,
            "unresolved": sorted(unresolved)}


def render_batch_json(batch: dict) -> str:
    return common.canonical_json(batch) + "\n"


def write_batch(batch: dict, path=None) -> pathlib.Path:
    path = pathlib.Path(path) if path else BATCH_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_batch_json(batch), encoding="utf-8")
    return path


# ===========================================================================
# CONSUME: verdicts (+ batch context) -> results/hammer_readout.{json,md}.
# ===========================================================================
def _rung_of(script, batch_goal) -> str:
    """The discharge rung whose script the lane closed, by matching the verdict
    row's ``script`` bytes against the batch goal's rendered scripts."""
    if script is None or batch_goal is None:
        return "unknown"
    for s in batch_goal.get("scripts", []):
        if s["lean_text"] == script:
            return s["discharge"]
    return "unknown"


def build_readout(verdicts: dict, batch: dict = None) -> dict:
    """Classify every verdict row into the honest demand buckets and build the
    per-rung / per-family closure tables.  ``batch`` supplies each goal's family
    and the rung that closed it (the verdict row is minimal by contract).

    Buckets (⚠ the H3 distinction): ``elaborated is None`` -> NOT-RUN;
    ``elaborated is False`` -> STATEMENT-CERT demand (the statement itself did not
    elaborate); ``elaborated & replayed`` -> CLOSED; ``elaborated & not replayed``
    -> TACTIC (hammer/H3) refusal.  Token columns are present and zero (LLM off)."""
    by_goal = {g["goal_id"]: g for g in (batch or {}).get("goals", [])}
    per_rung = {r: {"closed": 0} for r in RUNGS}
    per_rung["unknown"] = {"closed": 0}
    per_family = {}
    closed, stmt_demand, tactic_refused, not_run = [], [], [], []

    for row in verdicts.get("rows", []):
        gid = row["goal_id"]
        bg = by_goal.get(gid)
        family = bg.get("family", "other") if bg else "other"
        fam = per_family.setdefault(
            family, {"closed": 0, "statement_cert_demand": 0,
                     "tactic_refused": 0, "not_run": 0, "total": 0})
        fam["total"] += 1
        elaborated = row.get("elaborated")
        replayed = row.get("replayed")
        if elaborated is None:
            not_run.append(gid)
            fam["not_run"] += 1
        elif elaborated is False:
            stmt_demand.append(gid)
            fam["statement_cert_demand"] += 1
        elif replayed:
            rung = _rung_of(row.get("script"), bg)
            closed.append({"goal_id": gid, "rung": rung, "family": family})
            per_rung.setdefault(rung, {"closed": 0})["closed"] += 1
            fam["closed"] += 1
        else:
            tactic_refused.append(gid)
            fam["tactic_refused"] += 1

    return {"schema": READOUT_SCHEMA,
            "verdicts_status": verdicts.get("status"),
            "lean_available": verdicts.get("lean_available"),
            "totals": {"n_goals": len(verdicts.get("rows", [])),
                       "n_closed": len(closed),
                       "n_statement_cert_demand": len(stmt_demand),
                       "n_tactic_refused": len(tactic_refused),
                       "n_not_run": len(not_run)},
            "per_rung": per_rung,
            "per_family": dict(sorted(per_family.items())),
            "closed": sorted(closed, key=lambda c: c["goal_id"]),
            "statement_cert_demand": sorted(stmt_demand),
            "tactic_refusals": sorted(tactic_refused),
            "not_run": sorted(not_run),
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "note": _EVIDENCE_NOTE}


def render_readout_md(readout: dict) -> str:
    t = readout["totals"]
    L = ["# Hammer readout (UNBOUNDED-statement close-rate)",
         "",
         f"- verdicts status: **{readout['verdicts_status']}**  "
         f"(lean_available={readout['lean_available']})",
         f"- goals: {t['n_goals']}  |  closed: {t['n_closed']}  |  "
         f"statement-cert demand: {t['n_statement_cert_demand']}  |  "
         f"tactic (H3) refused: {t['n_tactic_refused']}  |  "
         f"not-run: {t['n_not_run']}",
         "",
         "## Per-rung closure",
         "",
         "| rung | closed |",
         "|---|---|"]
    for rung in list(RUNGS) + ["unknown"]:
        L.append(f"| {rung} | {readout['per_rung'].get(rung, {}).get('closed', 0)} |")
    L += ["",
          "## Per-family closure",
          "",
          "| family | closed | stmt-cert demand | tactic refused | not-run | total |",
          "|---|---|---|---|---|---|"]
    for fam, d in readout["per_family"].items():
        L.append(f"| {fam} | {d['closed']} | {d['statement_cert_demand']} | "
                 f"{d['tactic_refused']} | {d['not_run']} | {d['total']} |")
    L += ["",
          "## Statement-cert demand (elaborated=false -- statement stage)",
          "",
          ("- " + ", ".join(readout["statement_cert_demand"]))
          if readout["statement_cert_demand"] else "- (none)",
          "",
          "## Tactic / H3 refusals (elaborated, ladder closed nothing)",
          "",
          ("- " + ", ".join(readout["tactic_refusals"]))
          if readout["tactic_refusals"] else "- (none)",
          "",
          "## Tokens (LLM off)",
          "",
          "| prompt | completion | total |",
          "|---|---|---|",
          f"| {readout['tokens']['prompt']} | {readout['tokens']['completion']} "
          f"| {readout['tokens']['total']} |",
          "",
          f"> {readout['note']}",
          ""]
    return "\n".join(L)


def consume(verdicts_path=None, batch_path=None):
    """Read the lane's verdicts (+ the batch for family/rung context) and write
    the readout json + md.  A missing verdicts file yields the honest not-yet-run
    bootstrap readout (the import_rt Lean-absent deferral precedent)."""
    vp = pathlib.Path(verdicts_path) if verdicts_path else VERDICTS_PATH
    bp = pathlib.Path(batch_path) if batch_path else BATCH_PATH
    if vp.exists():
        verdicts = json.loads(vp.read_text(encoding="utf-8"))
    else:
        verdicts = {"schema": VERDICTS_SCHEMA, "status": "not-run",
                    "lean_available": bool(common.lean_available()), "rows": []}
    batch = json.loads(bp.read_text(encoding="utf-8")) if bp.exists() else None
    return build_readout(verdicts, batch)


def write_readout(readout: dict, json_path=None, md_path=None):
    jp = pathlib.Path(json_path) if json_path else READOUT_JSON_PATH
    mp = pathlib.Path(md_path) if md_path else READOUT_MD_PATH
    jp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(common.canonical_json(readout) + "\n", encoding="utf-8")
    mp.write_text(render_readout_md(readout), encoding="utf-8")
    return jp, mp


# ===========================================================================
# CLI
# ===========================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("assemble", help="queue -> results/hammer_batch.json")
    a.add_argument("--queue", default=None,
                   help="path to the proof queue json (absent -> empty bootstrap)")
    a.add_argument("--cap", type=int, default=DEFAULT_CAP)
    a.add_argument("--bound", type=int, default=DEFAULT_BOUND)
    a.add_argument("--out", default=None)

    c = sub.add_parser("consume", help="verdicts -> results/hammer_readout.{json,md}")
    c.add_argument("--verdicts", default=None)
    c.add_argument("--batch", default=None)
    c.add_argument("--out-json", default=None)
    c.add_argument("--out-md", default=None)

    args = ap.parse_args(argv)
    if args.cmd == "assemble":
        batch = assemble(args.queue, cap=args.cap, bound=args.bound)
        p = write_batch(batch, args.out)
        print(f"bench_hammer assemble: {len(batch['goals'])} goals "
              f"(queued={batch['n_queued']}, unresolved={len(batch['unresolved'])})"
              f" -> {p}")
    else:
        readout = consume(args.verdicts, args.batch)
        jp, mp = write_readout(readout, args.out_json, args.out_md)
        t = readout["totals"]
        print(f"bench_hammer consume: closed={t['n_closed']} "
              f"stmt-demand={t['n_statement_cert_demand']} "
              f"tactic-refused={t['n_tactic_refused']} not-run={t['n_not_run']} "
              f"-> {jp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

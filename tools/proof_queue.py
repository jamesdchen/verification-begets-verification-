#!/usr/bin/env python3
"""Proof queue: the committed, subject-hash-keyed worklist the in-lane hammer
(WS-R, ``bench/bench_hammer.py``) consumes to decide which statements to try to
elaborate next.

It reconciles THREE lane/bench-written demand sources into one deterministic,
prose-free table of goals (refs + hashes only):

- ``results/anchor_report.json`` -- the ∃-anchor lattice.  Its
  ``shadow-certified`` rows carry bounded-shadow fidelity evidence and enter
  ``queued`` (source ``anchor-exists``).  The one ``shadow-edge-refused`` row
  (43) enters ``shadow-refuted-excluded`` -- the shadow REFUTED it, so it is
  recorded as demand but MUST NEVER be queued as provable.
- ``results/import_rt_report.json`` -- the import round-trip differential.  Its
  ``failed`` rows are ALL infrastructure refusals (a defeq field-notation
  rendering bug + escape-gate U+2115 refusals on every iff rung; the math never
  ran).  They enter ``infra-refused`` -- gate/probe-surface demand, NEVER proof
  demand, NEVER batched.  (The ASCII-render repair of the probes is a separate
  deferred package, not this build.)
- ``results/formalize_bench_state.jsonl`` -- the dual-arm formalization bench.
  Its governed-arm certified rows enter ``queued`` (source ``bench-certified``)
  labelled with the honest fidelity string -- "dual-arm bench-certified
  (Lean-free fidelity evidence; kernel statement-cert deferred)", NEVER
  "certified TRUE".

DEDUPE is by ``subject.sha256`` (the compiled-reading ``statement_hash``, which
is byte-identical between the anchor pipeline and the bench readings -- see
``generators.math_compile.compile_math_reading``).  Sources 41/42/44 appear in
BOTH the anchor report and the bench state; each becomes ONE row whose
provenance merges both arms.

FAMILY (linear/dvd/parity/exists/gcd/other) is classified from the reading's
operator tokens (the ``op`` fields plus the ∃-binder), mirroring the demand
sweep's method; for the infra-refused rows -- which carry no reading, the math
never ran -- the tokens are lifted best-effort from the refused Lean surface.

DERIVED_FROM pins the sha256 of every input file.  The reconciliation tooth
compares those pins against the live files, so "an input moved" reads as
recorded STALENESS demand (regenerate the queue), distinct from "the derivation
is wrong" (a red byte-compare).

REGEN-DAG MEMBER (originally lane-adjacent; overruled by measured evidence).
The queue's INPUTS stay lane/bench-written and regen never touches them --
but the queue itself is a committed DERIVATIVE with pin/byte teeth, and the
first live cycle merge after this tool landed moved
``formalize_bench_state.jsonl`` and redded those teeth on an unrelated PR.
Cycles must regenerate the queue mechanically, so it now rides
``tools/regen_downstream.py`` (chain: proof_queue -> hammer_batch, after
frontier) -- recompute beats recollection.

Deterministic, LLM-free, Lean-free, network-free.  Same canonical-JSON
discipline as the other ``results/`` writers (``common.canonical_json``, sorted
keys, trailing newline); only refs and hashes are written -- statement prose is
never duplicated into ``results/``.

OUTPUT: ``results/proof_queue.json`` (schema: ``derived_from``, ``goals``,
``honesty``).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from run.anchor import _load_reading
from generators.math_compile import compile_math_reading

# --------------------------------------------------------------------------- #
# Input artifacts (lane/bench-written; pinned into ``derived_from``).
# --------------------------------------------------------------------------- #
ANCHOR = "results/anchor_report.json"
IMPORT_RT = "results/import_rt_report.json"
BENCH = "results/formalize_bench_state.jsonl"
INPUTS = (ANCHOR, IMPORT_RT, BENCH)

_BENCH_LABEL = ("dual-arm bench-certified (Lean-free fidelity evidence; "
                "kernel statement-cert deferred)")
_EXCLUDED_LABEL = ("shadow refuted the bounded exists-edge witness; recorded "
                   "as demand, excluded from the provable queue")
_INFRA_LABEL = ("infrastructure refusal (escape-gate / field-notation "
                "rendering); gate/probe-surface demand, the math never ran")

_HONESTY = (
    "statements carry fidelity evidence (dual-arm bench certification / shadow "
    "evidence), never truth verdicts; kernel statement-cert is deferred, so the "
    "upgrade path is nothing -> statement-cert -> proof-cert (two lane steps); "
    "infra-refused rows are gate/rendering demand, never proof demand")

# Family classification vocabulary (operator tokens -> family).  Precedence is
# fixed and checked in this order; a token set matches the FIRST family whose
# trigger it hits.
_LINEAR_OPS = {"+", "-", "*", "=", "<", "<=", ">", ">=", "!=", "^", "mod"}


# --------------------------------------------------------------------------- #
# Family classification (operator tokens, deterministic precedence).
# --------------------------------------------------------------------------- #
def _reading_tokens(reading_doc: dict) -> set:
    """Operator/binder tokens for a WP-AUTH reading dict: every ``op`` value plus
    the sentinel ``exists`` when an ∃-quantifier binder is present."""
    toks: set = set()

    def walk(o):
        if isinstance(o, dict):
            if "op" in o and isinstance(o["op"], str):
                toks.add(o["op"].lower())
            if o.get("kind") == "quantifier" and o.get("binder") == "exists":
                toks.add("exists")
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(reading_doc)
    return toks


def _lean_surface_tokens(lean_text: str) -> set:
    """Best-effort operator tokens lifted from a refused Lean surface (the
    infra-refused rows carry no reading -- the math never ran).  Keyword/symbol
    membership only, deterministic."""
    toks: set = set()
    if "Even" in lean_text:
        toks.add("even")
    if "Odd" in lean_text:
        toks.add("odd")
    if "gcd" in lean_text or "Gcd" in lean_text:
        toks.add("gcd")
    if "∣" in lean_text or " dvd " in lean_text:   # U+2223 DIVIDES
        toks.add("dvd")
    if "∃" in lean_text:                            # U+2203 THERE EXISTS
        toks.add("exists")
    return toks


def classify_family(tokens: set) -> str:
    """Map operator tokens to a family.  Fixed precedence: gcd > parity > dvd >
    exists > linear > other (a gcd statement over a dvd sub-term is a gcd
    statement; a parity statement mentioning dvd is parity; an ∃-shaped goal
    with none of those is exists; a purely arithmetic/relational goal is
    linear)."""
    if "gcd" in tokens:
        return "gcd"
    if tokens & {"even", "odd"}:
        return "parity"
    if "dvd" in tokens:
        return "dvd"
    if "exists" in tokens:
        return "exists"
    if tokens & _LINEAR_OPS:
        return "linear"
    return "other"


def _rung_hint(status: str, has_exists: bool) -> str:
    """The hammer's routing hint for a goal (never a proof claim)."""
    if status == "infra-refused":
        return "none: infrastructure refusal (gate/rendering); no proof attempt"
    if status == "shadow-refuted-excluded":
        return "none: shadow refuted the bounded exists-edge; not queued"
    if has_exists:
        return ("exists-route: anchor kernel-leg template machinery "
                "(run/anchor.py); discharge vocabulary kernel/certs.py "
                "ANCHOR_DISCHARGE_RUNGS")
    return ("forall-route: intro prelude then first-success over the pinned "
            "discharge rungs (decide, omega, norm_num, simp)")


# --------------------------------------------------------------------------- #
# Input loaders.
# --------------------------------------------------------------------------- #
def _load_bench(path: str) -> list:
    """Governed-arm certified bench rows, sorted by ``source_id``."""
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("arm") == "governed" and r.get("certified") is True:
                out.append(r)
    out.sort(key=lambda r: r["source_id"])
    return out


def _subject_sha(reading_doc: dict, source_id: str) -> str:
    """The compiled-reading ``statement_hash`` -- byte-identical to the anchor
    pipeline's ``subject_hash`` for the same reading (verified for 41/42/44)."""
    reading = _load_reading(reading_doc, source_id)
    return compile_math_reading(reading)["statement_hash"]


# --------------------------------------------------------------------------- #
# The reconciler.
# --------------------------------------------------------------------------- #
def build_proof_queue(results_dir: str) -> dict:
    anchor = json.load(open(os.path.join(results_dir, "anchor_report.json")))
    import_rt = json.load(
        open(os.path.join(results_dir, "import_rt_report.json")))
    bench_path = os.path.join(results_dir, "formalize_bench_state.jsonl")
    bench_rows = _load_bench(bench_path)

    # A source_id -> governed reading doc map (any certified state) so anchor
    # rows -- including the excluded 43, governed but not certified -- can be
    # classified by their reading operator tokens.
    reading_by_source: dict = {}
    with open(bench_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rj = r.get("reading_json")
            if r.get("arm") == "governed" and isinstance(rj, str) and rj.strip():
                reading_by_source.setdefault(r["source_id"], json.loads(rj))

    by_subject: dict = {}       # subject sha256 -> goal dict

    # (a) anchor-exists: shadow-certified -> queued; shadow-edge-refused ->
    #     excluded.  subject.sha256 is the anchor row's own subject_hash.
    for row in anchor["readings"]:
        sid = row["source_id"]
        subj = row["subject_hash"]
        doc = reading_by_source.get(sid)
        tokens = _reading_tokens(doc) if doc is not None else set()
        has_exists = "exists" in tokens
        if row["lattice_point"] == "shadow-certified":
            status = "queued"
            prov = {
                "sources": ["anchor-exists"],
                "anchor": {
                    "lattice_point": row["lattice_point"],
                    "shadow_verdict": row["shadow"]["verdict"],
                    "n_outer_admitted": row["shadow"]["n_outer_admitted"],
                    "bound": row["shadow"]["bound"],
                },
                "label": ("bounded-shadow certified (Lean-free fidelity "
                          "evidence; kernel statement-cert deferred)"),
            }
        elif row["lattice_point"] == "shadow-edge-refused":
            status = "shadow-refuted-excluded"
            prov = {
                "sources": ["anchor-exists"],
                "anchor": {
                    "lattice_point": row["lattice_point"],
                    "shadow_verdict": row["shadow"]["verdict"],
                    "refuting_outer": row["shadow"]["refuting_outer"],
                    "n_outer_admitted": row["shadow"]["n_outer_admitted"],
                    "bound": row["shadow"]["bound"],
                },
                "label": _EXCLUDED_LABEL,
            }
        else:
            continue   # only certified / edge-refused rows are demand
        by_subject[subj] = {
            "goal_id": sid,
            "source": "anchor-exists",
            "subject": {"ref": sid, "sha256": subj},
            "status": status,
            "family": classify_family(tokens),
            "rung_hint": _rung_hint(status, has_exists),
            "provenance": prov,
        }

    # (c) bench-certified: governed-arm certified -> queued.  If the subject is
    #     already present (an anchor-exists row), MERGE provenance; else add.
    for r in bench_rows:
        sid = r["source_id"]
        doc = json.loads(r["reading_json"])
        subj = _subject_sha(doc, sid)
        tokens = _reading_tokens(doc)
        has_exists = "exists" in tokens
        bench_prov = {
            "arm": "governed",
            "certified": True,
            "table_hash": r.get("table_hash"),
            "wave": r.get("wave"),
        }
        if subj in by_subject:                      # dedupe: merge into anchor
            g = by_subject[subj]
            g["provenance"]["sources"].append("bench-certified")
            g["provenance"]["bench"] = bench_prov
            g["provenance"]["label"] = _BENCH_LABEL
            continue
        by_subject[subj] = {
            "goal_id": sid,
            "source": "bench-certified",
            "subject": {"ref": sid, "sha256": subj},
            "status": "queued",
            "family": classify_family(tokens),
            "rung_hint": _rung_hint("queued", has_exists),
            "provenance": {
                "sources": ["bench-certified"],
                "bench": bench_prov,
                "label": _BENCH_LABEL,
            },
        }

    # (b) rt-failed: import round-trip failures -> infra-refused (never batched).
    for row in import_rt["rows"]:
        if row.get("verdict") != "failed":
            continue
        decl = row["decl_name"]
        subj = row["statement_hash_original"]
        surfaces = " ".join(t.get("lean_text", "")
                            for t in row.get("probe_transcripts", []))
        tokens = _lean_surface_tokens(surfaces)
        by_subject[subj] = {
            "goal_id": decl,
            "source": "rt-failed",
            "subject": {"ref": decl, "sha256": subj},
            "status": "infra-refused",
            "family": classify_family(tokens),
            "rung_hint": _rung_hint("infra-refused", "exists" in tokens),
            "provenance": {
                "sources": ["rt-failed"],
                "rt": {
                    "decl_name": decl,
                    "channel": row.get("channel"),
                    "verdict": "failed",
                    "statement_hash_compiled": row.get("statement_hash_compiled"),
                },
                "label": _INFRA_LABEL,
            },
        }

    goals = sorted(by_subject.values(), key=lambda g: g["goal_id"])

    derived_from = {p: common.sha256_bytes(open(p, "rb").read()) for p in INPUTS}

    return {
        "derived_from": derived_from,
        "goals": goals,
        "honesty": _HONESTY,
    }


def _write(queue: dict, out_path: str) -> None:
    with open(out_path, "w") as fh:
        fh.write(common.canonical_json(queue) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", default="results",
                    help="dir holding the input reports; proof_queue.json is "
                         "written here")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("proof_queue"):
        queue = build_proof_queue(args.results)
    out_path = os.path.join(args.results, "proof_queue.json")
    _write(queue, out_path)
    by_status: dict = {}
    for g in queue["goals"]:
        by_status[g["status"]] = by_status.get(g["status"], 0) + 1
    print(f"proof_queue: {len(queue['goals'])} goals "
          f"({by_status}) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

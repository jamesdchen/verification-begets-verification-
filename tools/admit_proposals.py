#!/usr/bin/env python3
"""WP-T4-WIRE: the ADMISSION RUNNER -- the miner -> gate -> registry seam.

The producer half of auto-R2 (``tools/subtree_mine.py``) STAGES proposed
operator rows under ``specs/mathsources/operators/proposed/`` as inert data; the
R2 battery + pricing gate (``generators.operator_growth.admit_operator``) is the
SOLE honest judge.  Between them sat an unbridged gap: nothing ran the staged
proposals THROUGH the gate and into the registry.  This runner is that bridge.

It is a DETERMINISTIC batch:

  1. ``load_proposed`` every staged row (sorted by filename -> stable order).
  2. For each row, run ``admit_operator(row, pricing_corpus=<the real certified
     governed corpus from the committed checkpoint>)`` -- the same corpus the
     WP-T4 subtree census is built over.
  3. ``save_admitted`` every PASSER through the sole-admitter path (which itself
     re-runs the battery and requires cert-id equality, so this runner cannot
     launder a row past the gate).  Refusals STAY in ``proposed/`` untouched --
     staging is the record of what did not pay.
  4. Emit a per-row verdict table (word, stage, arithmetic) to stdout and to the
     deterministic sibling artifacts ``results/proposal_admissions.{json,md}``.

APPEND-ONLY / IDEMPOTENT.  ``save_admitted`` refuses to overwrite a word with a
different row digest and is a no-op for a same-digest re-save, so re-running this
runner is a NO-OP: the registry and the artifacts come out byte-identical.  The
grandfathered ``multiple_of`` row (admitted pre-pricing, now alias-refused) is
NEVER evicted -- append-only means the runner only ever ADDS.

Nothing here is on the live parse/expand path; it is an offline registry-growth
step, run explicitly by a human/operator, never by the governor loop.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from generators import operator_growth as og

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_OP_DIR = os.path.join(_ROOT, "specs", "mathsources", "operators")
_DEFAULT_CORPUS = os.path.join(_ROOT, "results", "formalize_bench_state.jsonl")
_DEFAULT_RESULTS = os.path.join(_ROOT, "results")


def load_pricing_corpus(path):
    """The real pricing corpus: the certified governed exogenous readings from
    the committed bench checkpoint (the same readings the WP-T4 subtree census in
    ``results/tower_census.json`` is built over)."""
    out = []
    with open(path, "r", encoding="utf-8") as fh:
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


def _best_effort_pricing(row, corpus):
    """The pricing arithmetic for a row, computed for REPORTING even when the
    gate refuses it earlier (evidence, never a verdict).  Returns None if the
    row cannot even be expanded to a kernel pred (a term-valued definition that
    fails well-formedness)."""
    try:
        kernel_def = og._expand_definition_to_kernel(row, {})
        return og.price_operator(row, kernel_def, corpus)
    except Exception:
        return None


def run(op_dir, corpus_path, results_dir, *, execute=True):
    """Run the batch.  Returns the verdict list (also the JSON artifact body)."""
    corpus = load_pricing_corpus(corpus_path)
    corpus_digest = common.sha256_json(corpus)[:16]
    proposed = og.load_proposed(op_dir=op_dir)
    proposed = sorted(proposed, key=lambda r: r.get("word", ""))

    verdicts = []
    for row in proposed:
        word = row.get("word", "?")
        res = og.admit_operator(row, op_dir=op_dir, pricing_corpus=corpus)
        pricing = _best_effort_pricing(row, corpus)
        admitted = bool(res.get("admitted"))
        if admitted:
            stage, reason = "admitted", ""
            cert_id = res["cert"]["id"]
            # the cert's own priced pricing block is authoritative for a passer.
            pricing = res["cert"]["pricing"]
        else:
            ref = res.get("refusal", {})
            stage, reason = ref.get("stage", "?"), ref.get("reason", "")
            cert_id = None

        saved = False
        if admitted and execute:
            og.save_admitted({word: {"row": res["row"], "cert": res["cert"]}},
                             op_dir=op_dir, pricing_corpus=corpus)
            og.reload()
            saved = True

        verdicts.append({
            "word": word,
            "arity": row.get("arity"),
            "admitted": admitted,
            "stage": stage,
            "reason": reason,
            "cert_id": cert_id,
            "saved": saved,
            "pricing": _pricing_view(pricing),
        })
    return {"corpus_digest": corpus_digest, "corpus_readings": len(corpus),
            "n_proposed": len(proposed),
            "n_admitted": sum(v["admitted"] for v in verdicts),
            "verdicts": verdicts}


def _pricing_view(pricing):
    """The reportable slice of a pricing block (drops the corpus digest, which is
    reported once at top level)."""
    if not isinstance(pricing, dict):
        return None
    keys = ("model_bits", "saving", "uses", "witnesses",
            "dl_before", "dl_after", "delta")
    return {k: pricing.get(k) for k in keys if k in pricing}


def _arith_str(p):
    if not p:
        return "(no pricing -- not a well-formed pred)"
    return (f"model_bits={p.get('model_bits')}, saving={p.get('saving')} over "
            f"{p.get('uses')} uses in {p.get('witnesses')} witnesses "
            f"(dl {p.get('dl_before')} -> {p.get('dl_after')}, "
            f"delta={p.get('delta')})")


def render_md(report):
    lines = []
    lines.append("# Proposal admissions (WP-T4-WIRE)")
    lines.append("")
    lines.append("The staged `proposed/` operator rows run through the R2 "
                 "battery + pricing gate (`admit_operator`), priced against the "
                 "real certified governed corpus from the committed checkpoint. "
                 "Passers are persisted via the sole-admitter `save_admitted` "
                 "path (append-only); refusals stay in `proposed/`.")
    lines.append("")
    lines.append(f"- pricing corpus: {report['corpus_readings']} readings "
                 f"(digest `{report['corpus_digest']}`)")
    lines.append(f"- proposed rows: {report['n_proposed']}")
    lines.append(f"- admitted: {report['n_admitted']}")
    lines.append("")
    lines.append("| word | arity | verdict | stage | arithmetic |")
    lines.append("|------|------:|---------|-------|------------|")
    for v in report["verdicts"]:
        verdict = "ADMIT" if v["admitted"] else "refuse"
        lines.append(f"| `{v['word']}` | {v['arity']} | {verdict} | "
                     f"{v['stage']} | {_arith_str(v['pricing'])} |")
    lines.append("")
    lines.append("## Refusal reasons")
    lines.append("")
    for v in report["verdicts"]:
        if not v["admitted"]:
            lines.append(f"- `{v['word']}` ({v['stage']}): {v['reason']}")
    lines.append("")
    lines.append("## E1 note (prompt-side pricing)")
    lines.append("")
    lines.append("The admitted rows carry a `pricing` cert block and therefore "
                 "surface in the math authoring prompt's ADMITTED OPERATORS "
                 "section (`buildloop/math_prompt.render_operator_table`), which "
                 "adds prompt bytes -- the priced §11.4 mechanism (i). The "
                 "grandfathered `multiple_of` row (no pricing block, alias-"
                 "refused under the current gate) is NOT surfaced, so the "
                 "committed-registry prompt stays byte-identical to the pre-seam "
                 "prompt. The frozen bench artifacts are untouched (read-only); "
                 "the committed sidecar's `prompt_scaffold_sha256` intentionally "
                 "records the pre-seam scaffold that produced that frozen run.")
    return "\n".join(lines) + "\n"


def write_artifacts(report, results_dir):
    os.makedirs(results_dir, exist_ok=True)
    jpath = os.path.join(results_dir, "proposal_admissions.json")
    mpath = os.path.join(results_dir, "proposal_admissions.md")
    with open(jpath, "w", encoding="utf-8") as fh:
        fh.write(common.canonical_json(report))
        fh.write("\n")
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write(render_md(report))
    return jpath, mpath


def print_table(report):
    print(f"pricing corpus: {report['corpus_readings']} readings "
          f"(digest {report['corpus_digest']})")
    print(f"proposed: {report['n_proposed']}   admitted: {report['n_admitted']}")
    print()
    print(f"{'word':16} {'verdict':8} {'stage':16} arithmetic")
    print("-" * 100)
    for v in report["verdicts"]:
        verdict = "ADMIT" if v["admitted"] else "refuse"
        print(f"{v['word']:16} {verdict:8} {v['stage']:16} "
              f"{_arith_str(v['pricing'])}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--op-dir", default=_DEFAULT_OP_DIR,
                    help="operators dir (default: specs/mathsources/operators)")
    ap.add_argument("--corpus", default=_DEFAULT_CORPUS,
                    help="pricing corpus jsonl (default: the committed checkpoint)")
    ap.add_argument("--results-dir", default=_DEFAULT_RESULTS,
                    help="artifact output dir (default: results/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="measure + write artifacts, but do NOT save_admitted")
    args = ap.parse_args(argv)

    og.reload()
    report = run(args.op_dir, args.corpus, args.results_dir,
                 execute=not args.dry_run)
    print_table(report)
    jpath, mpath = write_artifacts(report, args.results_dir)
    print()
    print("wrote", jpath)
    print("wrote", mpath)
    if args.dry_run:
        print("(dry run -- registry NOT mutated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

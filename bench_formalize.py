#!/usr/bin/env python3
"""F5.2: the governed-vs-ungoverned formalization benchmark (LLM-requiring).

Two arms over an IDENTICAL corpus, model, prompt scaffold and spend cap --
implemented as the SAME code path over different READING SETS, never a miner
fork (⚠E4: `mine` refuses DL-raising candidates inline, so "admit everything" is
not a flag; and origin-blind witnessing is today's default, so it is the
GOVERNED arm that needs the exogenous witness filter):

  * governed   -- mining / admission over EXOGENOUS-origin readings only,
                  per-use translation-cert on;
  * ungoverned -- the identical calls over ALL readings including dreams (the
                  literature's default), per-use certs off.

Reported DL for BOTH arms = `mdl_macros.corpus_dl` over the EXOGENOUS sub-corpus
(⚠E4/E7b): a dream-witnessed macro admitted by the ungoverned arm raises the
*reported* exogenous DL by exactly its `dl_macro` -- real junk, same code path.

Cost accounting NEVER sums tokens with seconds (⚠E6).  The FH7 anti-gaming
denominator (⚠E3): `cost_per_certified_statement` divides by the exogenous
entries whose statement-cert is green AND `trivially_closed == false`.

Skippable with an honest note (⚠H43 / X15): the teeth live in the LLM-FREE
demos (demo_formalize.py and demo_formalize_governor.py part (v), both green).
When this bench is SKIPPED, F5's `>= 30/40 certified` headline is explicitly
DEFERRED -- an honest tie is an admissible, publishable finding (the H24
lesson); the asserted, certificate-backed win lives in the planted tooth.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys

REQUIRES_LLM = True

_CORPUS = pathlib.Path(__file__).resolve().parent / "specs" / "mathsources"


def _llm_available() -> bool:
    import common
    return bool(shutil.which(os.path.basename(common.CLAUDE_CLI))
                or os.path.exists(common.CLAUDE_CLI)
                or os.environ.get("ANTHROPIC_API_KEY"))


def _author_reading(source: str, macro_table: dict, model=None) -> str | None:
    """Prompt the model to author a MathReading for one source sentence.  The
    prompt renders the live macro table (buildloop.math_prompt) -- the E1
    mechanism by which admitted vocabulary changes prompt bytes and thus cost."""
    from buildloop import llm, math_prompt
    prompt = math_prompt.render_math_reading_prompt(source, macro_table)
    try:
        out = llm.call_llm(prompt, model=model)
    except llm.LLMError:
        return None
    return llm.strip_fences(out["text"] if isinstance(out, dict) else out)


def _arm(sources, readings_by_origin, *, governed):
    """One arm: certify each authored reading, then price the corpus over the
    EXOGENOUS sub-corpus with the arm's witness discipline.  Same code path for
    both arms -- only the witness filter (and per-use certs) differ."""
    from run.formalize import certify_statement
    from buildloop import recurrence, mdl_macros
    exo = [r for r in readings_by_origin if r.get("origin") == "exogenous"]
    corpus = exo if governed else list(readings_by_origin)
    wfilter = (lambda r: r.get("origin") == "exogenous") if governed else None

    # greedy admission over the arm's corpus (mine refuses DL-raising inline).
    table = {}
    while True:
        cands = recurrence.mine(corpus, table, witness_filter=wfilter)
        chosen = next(
            (c["candidate"] for c in cands
             if c["candidate"]["name"] not in table
             and mdl_macros.macro_admission_decision(
                 corpus, c["candidate"], table, witness_filter=wfilter)["admit"]),
            None)
        if chosen is None:
            break
        table[chosen["name"]] = chosen

    # BOTH arms report corpus_dl over the EXOGENOUS sub-corpus (E4).
    reported_dl = mdl_macros.corpus_dl(exo, table)["total"]
    covered = sum(1 for r in exo if r.get("_certified"))
    return {"reported_exogenous_dl": round(reported_dl, 3),
            "live_macros": len(table),
            "certified_exogenous_statements": covered,
            "per_use_certs": bool(governed)}


def run_bench(model=None) -> int:
    from run.formalize import certify_statement
    sources = [(p.stem, p.read_text().strip())
               for p in sorted(_CORPUS.glob("*.txt"))]
    readings = []
    for stem, src in sources:
        rj = _author_reading(src, {}, model=model)
        if rj is None:
            continue
        try:
            res = certify_statement(src, rj)
        except Exception:
            continue
        try:
            doc = json.loads(rj)
        except ValueError:
            continue
        readings.append({**doc, "origin": "exogenous", "_certified": res.ok})
    governed = _arm(sources, readings, governed=True)
    ungoverned = _arm(sources, readings, governed=False)
    out = _CORPUS.parent.parent / "results" / "formalize_governed.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        fh.write("arm,reported_exogenous_dl,live_macros,"
                 "certified_exogenous_statements\n")
        for name, a in (("governed", governed), ("ungoverned", ungoverned)):
            fh.write(f"{name},{a['reported_exogenous_dl']},{a['live_macros']},"
                     f"{a['certified_exogenous_statements']}\n")
    print(json.dumps({"governed": governed, "ungoverned": ungoverned}, indent=2))
    # relational assert only (E5): equal coverage, governed DL no worse.
    assert (governed["certified_exogenous_statements"]
            == ungoverned["certified_exogenous_statements"])
    assert governed["reported_exogenous_dl"] <= ungoverned["reported_exogenous_dl"]
    print(f"wrote {out}")
    return 0


def main() -> int:
    if not _llm_available():
        print("SKIP bench_formalize: no LLM endpoint (REQUIRES_LLM).")
        print("  The governed-vs-ungoverned MECHANISM is proven LLM-free in "
              "demo_formalize_governor.py part (v): equal exogenous coverage AND "
              "strictly lower governed exogenous corpus_dl, certificate-backed.")
        print("  Per X15, F5's '>= 30/40 certified' headline is DEFERRED to a "
              "run with a model + Lean toolchain; an honest tie is admissible.")
        return 0
    return run_bench()


if __name__ == "__main__":
    sys.exit(main())

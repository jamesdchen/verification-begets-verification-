#!/usr/bin/env python3
"""WP-MET (§12.5): the METERED holdout run harness -- a thin metered layer over
``bench_formalize.py`` that discharges the X15-deferred COST headline on the
committed held-out set (``specs/mathsources/holdout/``, §11.13 / §11.7).

THIS module ships the machinery + teeth ONLY.  The actual metered run is a
SEPARATE, user-gated execution (real spend), run after adversarial review and
after WP-FLIP merges.  On the committed branch it is inert: ``main`` SKIPS
without an LLM endpoint, and every protocol requirement is toothed LLM-free in
``tests/test_bench_metered.py`` with a fake transport.

Why a NEW harness and not the committed bench: the §12.5 sweep found protocol
errors that the committed ``bench_formalize`` predates (it shares ONE state file
across arms and ASSERTS in the run path).  This layer REUSES that bench's
machinery -- ``_run_arm`` (the wave engine), ``_timed_certify`` (which calls
``run.formalize.certify_statement`` -- the fidelity pipeline is NEVER forked),
``_author_dreams``, ``_arm_row``, ``_Checkpoint`` -- and re-orchestrates it under
the seven binding corrections:

  1. BOTH ARMS METERED.  Governed and ungoverned run the SAME code path
     (``bench._run_arm``) over the SAME sources under the SAME author; token
     counts (in AND out) are the author's returned ``tokens_in``/``tokens_out``
     from the real LLM call metadata (``bench._llm_author`` reads
     ``call_llm``'s usage), never estimated post hoc.  A fake transport with the
     identical signature replays canned token counts for the LLM-free teeth.
  2. SEPARATE ``out_dir`` PER ARM.  ``out_dir/governed/`` and
     ``out_dir/ungoverned/`` -- separate checkpoint state files, separate CSV /
     meta / frozen-table sidecars, separate in-memory macro tables (each arm's
     ``_run_arm`` owns its own ``table = {}``).  Nothing mutable is shared, so
     cross-arm leakage cannot occur.  The ungoverned arm authors its OWN dream
     corpus into its OWN dir (governed never mines dreams).
  3. FH7-EXCLUSIVE COST DENOMINATOR.  The headline
     ``cost_per_certified_statement`` divides tokens by certified exogenous
     statements NET of trivially-closed ones (``bench._arm_row`` already emits
     both the exclusive and ``_inclusive`` figures); this harness NAMES the
     exclusive one the headline and records both.
  4. ASSERTS DEMOTED TO RECORDED VERDICTS.  The run path runs every in-run
     invariant as a ``{name, expected, observed, pass}`` verdict row written to
     ``verdicts.json``; it NEVER dies on a failing invariant -- the run
     completes and reports.  The teeth stay ``assert``s in the TESTS, never on
     the run path.
  5. MODEL-QUALIFIED CLAIMS.  EVERY output artifact (each per-arm meta AND the
     combined run manifest) records the model id, the prompt-vocabulary digest
     (the admitted-operator registry digest -- the E1 seam by which vocabulary
     changes prompt bytes and thus cost), the corpus digest (over the holdout
     source bytes in canonical order), and the harness version.  The results are
     properties of the model+prompt+corpus triple, stamped as such.
  6. HOLDOUT AS THE SOURCE SET.  ``_holdout_sources`` reads the manifest's
     ``holdout`` array in canonical (file-sorted) order and reads the ``.txt``
     bytes READ-ONLY; the harness snapshots the holdout tree's bytes before and
     after and records a ``holdout_byte_inert`` verdict.  Writing to ``holdout/``
     is forbidden and structurally impossible here (all writes go to ``out_dir``,
     which a verdict pins to be OUTSIDE the holdout tree).
  7. NO WALL-CLOCK IN DL (E6).  Token costs live in their own kilotoken columns;
     ``smt_seconds`` / ``lean_seconds_total`` are REPORTED beside, never summed
     into the cost numerator or into any DL.  The ledger law holds: this harness
     REPORTS cost, it prices cost into NO admission gate.

REAL RUN (user-gated, real spend, run separately after review + WP-FLIP):

    python3 bench_metered.py --confirm-spend    # resumes; --fresh ignores state

The ``--confirm-spend`` flag (or ``CGB_METERED_CONFIRM_SPEND=1``) is a mandatory
SPEND-SAFETY INTERLOCK: an endpoint merely EXISTING is not consent, so ``main``
SKIPS without the explicit opt-in even when the ``claude`` CLI is present -- an
accidental invocation can never spend.

writes, under ``results/metered_holdout/``:
    governed/formalize_bench_state.jsonl   ungoverned/formalize_bench_state.jsonl
    governed/formalize_governed.csv        ungoverned/formalize_governed.csv
    governed/meta.json                     ungoverned/meta.json
    governed/formalize_frozen_tables.json  ungoverned/formalize_frozen_tables.json
    metered_run.json    -- the combined, model-qualified run manifest (headline)
    verdicts.json       -- the recorded in-run invariant verdicts (never asserts)

``cvc5`` may be absent -- the bench degrades honestly (a certify exception counts
the reading uncertified).  Lean absent -> ``trivially_closed`` is false for all,
so the exclusive and inclusive cost figures coincide (recorded honestly).
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import bench_formalize as bench

REQUIRES_LLM = True

# SPEND-SAFETY INTERLOCK (§12.5).  ``_llm_available()`` is true whenever the
# ``claude`` CLI merely EXISTS (or an API key is set) -- that is NOT a deliberate
# user gate.  A metered run is REAL SPEND, so the run path additionally requires
# an EXPLICIT opt-in: the ``--confirm-spend`` flag OR ``CGB_METERED_CONFIRM_SPEND=1``
# in the environment.  Without it, ``main`` SKIPS (exit 0) even when an endpoint
# is present, so an accidental ``python3 bench_metered.py`` (a future demo sweep,
# a curious dev, CI drift) can NEVER spend.  A deliberate run is one flag away.
_CONFIRM_SPEND_FLAG = "--confirm-spend"
_CONFIRM_SPEND_ENV = "CGB_METERED_CONFIRM_SPEND"


def _spend_confirmed(argv) -> bool:
    return (_CONFIRM_SPEND_FLAG in argv
            or os.environ.get(_CONFIRM_SPEND_ENV) == "1")


# The harness identity stamped into every model-qualified artifact.  Bump on any
# change to the metered protocol so a stored result names the machinery that
# produced it (model+prompt+corpus+HARNESS triple).
HARNESS_VERSION = "wp-met/1"

_ROOT = pathlib.Path(__file__).resolve().parent
_HOLDOUT = _ROOT / "specs" / "mathsources" / "holdout"
_MANIFEST = _ROOT / "specs" / "mathsources" / "manifest.json"
_DEFAULT_OUT = _ROOT / "results" / "metered_holdout"

ARMS = ("governed", "ungoverned")


# =========================================================== holdout (read-only)
def _holdout_sources():
    """The holdout source set in CANONICAL order: the manifest's ``holdout``
    array sorted by ``file`` (== the h01..h20 walk order), each ``.txt`` read
    READ-ONLY.  Returns ``[(stem, source_text)]``.

    Read from the manifest (not a bare glob) so the canonical walk and the
    manifest/disk bijection are honoured; a top-level ``holdout/*.txt`` glob --
    NEVER ``rglob``/``**`` -- so the inertness guarantee (the set stays out of
    every corpus/ledger enumeration) is preserved."""
    with open(_MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    entries = sorted(manifest.get("holdout", []), key=lambda e: e["file"])
    out = []
    for e in entries:
        p = _HOLDOUT / e["file"]
        out.append((p.stem, p.read_text(encoding="utf-8").strip()))
    return out


def _holdout_byte_snapshot():
    """A content snapshot of the holdout tree: ``{filename: sha256(bytes)}`` over
    EVERY file (not only ``.txt`` -- README/manifest-adjacent files too), so any
    write, truncate, or new file is detected.  Used by the inertness verdict."""
    import common
    snap = {}
    # Non-recursive (``glob`` not ``rglob``): the holdout tree is flat (the
    # ``.txt`` sources + a README), so a top-level walk captures every file
    # without a recursive glob that a future guard could mistake for corpus
    # enumeration.  Read-only.
    for p in sorted(_HOLDOUT.glob("*")):
        if p.is_file():
            snap[p.name] = common.sha256_bytes(p.read_bytes())
    return snap


# =================================================== model-qualification stamp
def _operator_registry_digest():
    """The prompt-VOCABULARY digest: the admitted-operator registry (the E1 seam
    the prompt renders) content-hashed.  Empty registry -> the digest of ``{}``,
    stable and honest."""
    import common
    from generators import operator_growth as _og
    return common.sha256_json(_og.load_admitted())


def _corpus_digest(sources):
    """The holdout corpus digest: a hash over ``[(source_id, sha256(bytes))]`` in
    the given (canonical) order.  Ties every result to the exact source bytes it
    was measured on."""
    import common
    return common.sha256_json(
        [[sid, common.sha256_bytes(txt.encode("utf-8"))] for sid, txt in sources])


def _model_qualification(model, sources):
    """The four §12.5 req-5 fields every artifact carries, PLUS the pins that make
    the model+prompt+corpus triple reproducible.  The results are a property of
    THIS triple, stamped as such -- never of the machinery alone."""
    import common
    from buildloop import llm
    scaffold_src = (_ROOT / "buildloop" / "math_prompt.py").read_bytes()
    return {
        # --- the four binding req-5 fields --------------------------------
        "model_id": model or llm.DEFAULT_MODEL,
        "prompt_vocabulary_digest": _operator_registry_digest(),
        "corpus_digest": _corpus_digest(sources),
        "harness_version": HARNESS_VERSION,
        # --- reproducibility pins beside them -----------------------------
        "prompt_scaffold_sha256": common.sha256_bytes(scaffold_src),
        "corpus_source_ids": [sid for sid, _ in sources],
        "corpus_size": len(sources),
        "mathlib_commit": common.MATHLIB_COMMIT,
        "lean_toolchain": common.LEAN_TOOLCHAIN,
        "lean_available": bool(
            getattr(common, "lean_available", lambda: False)()),
    }


# ===================================================== one arm -> its own out_dir
def _prompt_bytes_of(text, table):
    from buildloop import math_prompt
    return len(math_prompt.render_math_reading_prompt(text, table))


def _run_one_arm(arm, sources, author, *, governed, dream_sources, arm_dir,
                 model, fresh, event_sink, modelq):
    """Run ONE arm into its OWN ``arm_dir`` with its OWN checkpoint state file.

    Reuses ``bench._author_dreams`` + ``bench._run_arm`` (never a fork).  The
    ungoverned arm authors its OWN dreams into ITS OWN checkpoint (governed
    passes ``dream_sources=[]`` -- it never mines dreams).  Returns
    ``(rows, wave_tables, dream_row)``."""
    arm_dir = pathlib.Path(arm_dir)
    arm_dir.mkdir(parents=True, exist_ok=True)
    state_path = arm_dir / "formalize_bench_state.jsonl"
    checkpoint = bench._Checkpoint(state_path, fresh=fresh)

    # dreams: only the ungoverned arm mines them; authored into ITS checkpoint so
    # no dream state is shared with the governed arm (arm isolation).
    if dream_sources:
        dream_readings, dream_row = bench._author_dreams(
            dream_sources, author, checkpoint, model, event_sink,
            _prompt_bytes_of)
    else:
        dream_readings, dream_row = [], {c: 0 for c in bench.CSV_COLUMNS}
        dream_row.update({"arm": "dream", "wave": 0})

    rows, wave_tables = bench._run_arm(
        arm, sources, author, governed=governed,
        dream_readings=dream_readings, checkpoint=checkpoint, model=model,
        event_sink=event_sink, prompt_bytes_of=_prompt_bytes_of)
    checkpoint.close()

    # per-arm artifacts, each model-qualified.
    all_rows = ([dream_row] if dream_sources else []) + rows
    bench._write_csv(all_rows, arm_dir / "formalize_governed.csv")
    bench._write_frozen_tables({arm: wave_tables},
                               arm_dir / "formalize_frozen_tables.json")
    _write_arm_meta(arm_dir / "meta.json", arm=arm, governed=governed,
                    dream_sources=dream_sources, modelq=modelq)
    return rows, wave_tables, dream_row


def _write_arm_meta(path, *, arm, governed, dream_sources, modelq):
    import common
    meta = {
        "arm": arm,
        # every artifact carries the model-qualification stamp (§12.5 req 5).
        "model_qualification": modelq,
        "arm_config": {
            "mining_corpus": "exogenous-only" if governed
            else "exogenous+dreams",
            "witness_filter": "exogenous" if governed else None,
            "per_use_certs": bool(governed),
            "dream_count": len(dream_sources),
            "isolated_state_file": "formalize_bench_state.jsonl (this dir only)",
        },
        "cost_law": {
            "numerator": "(cumulative_ktokens_in + cumulative_ktokens_out) -- "
                         "kilotokens ONLY; seconds NEVER summed in (E6).",
            "headline_denominator": "FH7-EXCLUSIVE: certified exogenous "
                                    "statements with trivially_closed == false.",
            "inclusive_denominator": "certified exogenous statements (green "
                                     "regardless of triviality) -- recorded "
                                     "beside the headline.",
            "lean_absent_note": "trivially_closed is false for ALL entries with "
                                "no Lean toolchain, so the two cost figures "
                                "coincide -- recorded honestly.",
            "reported_first": "this harness REPORTS cost; it prices cost into NO "
                              "admission gate (the ledger law).",
        },
        "deferred_f52_fields": list(bench.DEFERRED_F52_FIELDS),
    }
    with open(path, "w") as fh:
        fh.write(common.canonical_json(meta))
    return path


# ======================================================= verdicts (not asserts)
def _verdict(name, expected, observed):
    """One recorded verdict row.  ``pass`` is ``expected == observed``; a mismatch
    is DATA (a recorded row), NEVER an exception -- the run always completes."""
    return {"name": name, "expected": expected, "observed": observed,
            "pass": expected == observed}


def _run_verdicts(gov_rows, ung_rows, *, gov_state, ung_state, out_dir,
                  holdout_before, holdout_after, inject_failure=False):
    """Every in-run invariant, DEMOTED to a recorded verdict row.  Returns the
    verdict list; the run reports it and NEVER raises on a failing verdict."""
    verdicts = []
    gov, ung = gov_rows[-1], ung_rows[-1]

    # (1) both arms metered: each arm recorded real (in AND out) token columns.
    for arm, r in (("governed", gov), ("ungoverned", ung)):
        metered = (r["cumulative_ktokens_in"] > 0
                   or r["cumulative_ktokens_out"] > 0)
        verdicts.append(_verdict(
            f"{arm}_arm_metered", True, bool(metered)))

    # (2) arm isolation: distinct state files, and out_dir is OUTSIDE holdout.
    verdicts.append(_verdict("arm_state_files_distinct", True,
                             str(gov_state) != str(ung_state)))
    try:
        pathlib.Path(out_dir).resolve().relative_to(_HOLDOUT.resolve())
        out_inside_holdout = True
    except ValueError:
        out_inside_holdout = False
    verdicts.append(_verdict("out_dir_outside_holdout", True,
                             not out_inside_holdout))

    # (3) FH7-exclusive denominator is the headline, and the cost arithmetic is
    #     tokens-only (E6): recompute numerator/denominator and compare.
    for arm, r in (("governed", gov), ("ungoverned", ung)):
        denom_excl = (r["certified_exogenous_statements"]
                      - r["trivially_closed_count"])
        ktin, ktout = r["cumulative_ktokens_in"], r["cumulative_ktokens_out"]
        expect_cps = round((ktin + ktout) / denom_excl, 6) if denom_excl else 0.0
        verdicts.append(_verdict(
            f"{arm}_cost_is_fh7_exclusive_tokens_only",
            expect_cps, r["cost_per_certified_statement"]))
        # E6: the seconds columns are present but never in the numerator.
        verdicts.append(_verdict(
            f"{arm}_wall_clock_not_in_cost", True,
            r["cost_per_certified_statement"]
            == (round((ktin + ktout) / denom_excl, 6) if denom_excl else 0.0)))

    # (4) relational F5.2 pair (REPORTED here, asserted only in tests): equal
    #     exogenous coverage, governed reported DL no worse than ungoverned.
    verdicts.append(_verdict(
        "equal_exogenous_coverage",
        gov["certified_exogenous_statements"],
        ung["certified_exogenous_statements"]))
    verdicts.append({
        "name": "governed_dl_le_ungoverned",
        "expected": "governed <= ungoverned",
        "observed": {"governed": gov["reported_exogenous_dl"],
                     "ungoverned": ung["reported_exogenous_dl"]},
        "pass": float(gov["reported_exogenous_dl"])
        <= float(ung["reported_exogenous_dl"])})

    # (5) holdout byte-inertness across the whole run (read-only source set).
    verdicts.append(_verdict("holdout_byte_inert",
                             holdout_before, holdout_after))

    # A test-only injected invariant failure -- proves the run RECORDS a failing
    # verdict and COMPLETES rather than dying (verdict-demotion tooth).  Never
    # set on the real run path.
    if inject_failure:
        verdicts.append({"name": "injected_test_invariant",
                         "expected": "pass", "observed": "fail", "pass": False})
    return verdicts


# =================================================================== the run
def run_metered(model=None, *, author=None, author_by_arm=None, sources=None,
                dream_sources=None, out_dir=None, fresh=False, event_sink=None,
                inject_invariant_failure=False):
    """Run the two-arm METERED holdout bench with per-arm isolation and recorded
    verdicts.  Returns the combined summary dict.

    ``author`` -- the shared author for BOTH arms (default the real LLM author,
    ``bench._llm_author``); a fake transport with the same signature is injected
    by the LLM-free teeth.  ``author_by_arm`` -- optional ``{arm: author}`` to
    give the arms DIVERGENT canned responses (used by the verdict-demotion tooth
    to make an invariant observably fail); overrides ``author`` per arm.

    ``sources`` defaults to the committed holdout (canonical order);
    ``dream_sources`` defaults to the committed dream corpus (only the ungoverned
    arm mines it -- the governance contrast).  ``out_dir`` defaults to
    ``results/metered_holdout``; each arm writes under ``out_dir/<arm>/``."""
    if sources is None:
        sources = _holdout_sources()
    if dream_sources is None:
        dream_sources = bench._dream_sources()
    out_dir = pathlib.Path(out_dir) if out_dir else _DEFAULT_OUT
    out_dir.mkdir(parents=True, exist_ok=True)

    def _author_for(arm):
        if author_by_arm and arm in author_by_arm:
            return author_by_arm[arm]
        if author is not None:
            return author
        return lambda sid, txt, mt, th, _m=model: bench._llm_author(
            sid, txt, mt, th, model=_m)

    modelq = _model_qualification(model, sources)
    holdout_before = _holdout_byte_snapshot()

    # --- governed arm: exogenous-only mining, per-use certs, NO dreams --------
    gov_dir = out_dir / "governed"
    gov_rows, gov_tables, _gov_dream = _run_one_arm(
        "governed", sources, _author_for("governed"), governed=True,
        dream_sources=[], arm_dir=gov_dir, model=model, fresh=fresh,
        event_sink=event_sink, modelq=modelq)

    # --- ungoverned arm: exogenous+dreams mining, no certs, OWN dream state ----
    ung_dir = out_dir / "ungoverned"
    ung_rows, ung_tables, ung_dream = _run_one_arm(
        "ungoverned", sources, _author_for("ungoverned"), governed=False,
        dream_sources=dream_sources, arm_dir=ung_dir, model=model, fresh=fresh,
        event_sink=event_sink, modelq=modelq)

    holdout_after = _holdout_byte_snapshot()

    # --- verdicts (recorded, never asserted) ----------------------------------
    verdicts = _run_verdicts(
        gov_rows, ung_rows,
        gov_state=gov_dir / "formalize_bench_state.jsonl",
        ung_state=ung_dir / "formalize_bench_state.jsonl",
        out_dir=out_dir, holdout_before=holdout_before,
        holdout_after=holdout_after, inject_failure=inject_invariant_failure)
    _write_verdicts(out_dir / "verdicts.json", verdicts, modelq=modelq)

    # --- combined, model-qualified run manifest (the headline) ----------------
    gov, ung = gov_rows[-1], ung_rows[-1]
    summary = {
        "model_qualification": modelq,
        "out_dir": str(out_dir),
        "arm_dirs": {"governed": str(gov_dir), "ungoverned": str(ung_dir)},
        "headline": {
            "metric": "cost_per_certified_statement (FH7-EXCLUSIVE)",
            "governed": gov["cost_per_certified_statement"],
            "ungoverned": ung["cost_per_certified_statement"],
            "governed_inclusive": gov["cost_per_certified_statement_inclusive"],
            "ungoverned_inclusive":
                ung["cost_per_certified_statement_inclusive"],
            "denominator_law": "certified exogenous statements NET of "
                               "trivially-closed (FH7-exclusive).",
        },
        "governed": gov, "ungoverned": ung,
        "dream": ung_dream,
        "covered_governed": gov["certified_exogenous_statements"],
        "covered_ungoverned": ung["certified_exogenous_statements"],
        "dl_governed": gov["reported_exogenous_dl"],
        "dl_ungoverned": ung["reported_exogenous_dl"],
        "verdicts": verdicts,
        "verdicts_all_pass": all(v["pass"] for v in verdicts),
    }
    _write_manifest(out_dir / "metered_run.json", summary)
    return summary


def _write_verdicts(path, verdicts, *, modelq):
    import common
    doc = {"model_qualification": modelq,
           "note": "In-run invariants DEMOTED to recorded verdicts (§12.5 req "
                   "4): the metered run NEVER dies on a failing invariant -- it "
                   "records the row and completes.  The teeth stay asserts in "
                   "tests/test_bench_metered.py, never on this run path.",
           "verdicts": verdicts,
           "all_pass": all(v["pass"] for v in verdicts)}
    with open(path, "w") as fh:
        fh.write(common.canonical_json(doc))
    return path


def _write_manifest(path, summary):
    import common
    with open(path, "w") as fh:
        fh.write(common.canonical_json(summary))
    return path


# ====================================================================== main
def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    fresh = "--fresh" in argv
    if not bench._llm_available():
        print("SKIP bench_metered: no LLM endpoint (REQUIRES_LLM).")
        print("  WP-MET ships the metered-run MACHINERY + TEETH only; the real "
              "run is a SEPARATE, user-gated execution (real spend) after "
              "adversarial review and after WP-FLIP merges.")
        print("  Every §12.5 protocol requirement (both arms metered, per-arm "
              "out_dir isolation, FH7-exclusive denominator, verdict-demotion, "
              "model-qualification, holdout byte-inertness, no wall-clock in DL) "
              "is proven LLM-free in tests/test_bench_metered.py with a fake "
              "transport (canned responses + canned token counts).")
        print("  Real run:  python3 bench_metered.py --confirm-spend [--fresh]  "
              "-> writes results/metered_holdout/{governed,ungoverned}/... + "
              "metered_run.json + verdicts.json")
        return 0
    if not _spend_confirmed(argv):
        # SPEND-SAFETY INTERLOCK: an endpoint is present, but a metered run is
        # REAL SPEND and must be a DELIBERATE act.  Refuse to spend without the
        # explicit opt-in, so an accidental `python3 bench_metered.py` is inert.
        print("SKIP bench_metered: LLM endpoint present but spend NOT confirmed.")
        print(f"  A metered run is REAL SPEND.  Re-run with {_CONFIRM_SPEND_FLAG} "
              f"(or {_CONFIRM_SPEND_ENV}=1) to authorise it deliberately:")
        print(f"    python3 bench_metered.py {_CONFIRM_SPEND_FLAG} [--fresh]")
        print("  Without this interlock a stray invocation (CI drift, a demo "
              "sweep, a curious run) would spend; the machinery + every §12.5 "
              "tooth already ran LLM-free in tests/test_bench_metered.py.")
        return 0
    summary = run_metered(fresh=fresh)
    # The run REPORTS; it does NOT assert (§12.5 req 4).  Print the headline and
    # the verdict ledger; a failing verdict is DATA, not a crash.
    print(json.dumps({
        "headline": summary["headline"],
        "covered_governed": summary["covered_governed"],
        "covered_ungoverned": summary["covered_ungoverned"],
        "dl_governed": summary["dl_governed"],
        "dl_ungoverned": summary["dl_ungoverned"],
        "verdicts_all_pass": summary["verdicts_all_pass"],
    }, indent=2))
    print("\nverdict ledger:")
    for v in summary["verdicts"]:
        print(f"  [{'PASS' if v['pass'] else 'FAIL'}] {v['name']}")
    print(f"\nartifacts under {summary['out_dir']} "
          "(metered_run.json = headline; verdicts.json = recorded invariants).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

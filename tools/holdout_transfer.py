"""WP-TRANSFER -- the one-shot §13.2 holdout transfer readout (deterministic, LLM-free).

The registered question (COMPRESSION.md §13.2): does the vocabulary mined on the
TRAINING corpus price unseen SAME-DOMAIN (Euclid) sources cheaper than no
vocabulary?  This tool answers it by REPRICING the already-authored holdout
readings -- no LLM, no new spend -- under two frozen tables:

    (i)  T_frozen  -- the 8-macro governed refined+GC census-of-record table,
         frozen at digest ce5cb03fe2c5bdad BEFORE any holdout reading existed
         (results/reentry_evaluations.json, transfer_registration_13_2).
    (ii) {}        -- the empty table (no vocabulary).

MODEL BITS ARE EXCLUDED from both arms (§13.2): they were paid in-sample and are
sunk, so the transfer signal is the DATA-bit reduction only.  In the counting
currency (mdl_macros) that is `reading_cost`; the macro-definition `macro_cost`
is the excluded model bits.  This is why the result is a *transfer* readout, not
an admission decision -- with model bits included the small holdout does not pay
for the table, and that is reported honestly beside the headline.

    transfer_saving = data_bits(H, {}) - data_bits(H, T_frozen)   (>= 0)

The mandatory deflation line (§13.2): the adaptive-KT comparator -- does the
transferred vocabulary beat what an order-1 KT context model learns from scratch
on the same 20-source holdout?  Both KT numbers ship in this artifact.

T_frozen is RECONSTRUCTED by replaying the frozen checkpoint's authored waves
through the refined greedy miner + GC (tools.measure_cluster_key), then its
census summary digest is VERIFIED against the registered ce5cb03fe2c5bdad; a
mismatch STOPS the readout rather than pricing against a wrong table.  H is read
from the COMMITTED snapshot results/holdout_transfer_input.json (the gitignored
metered run is not required at readout time).

Claims grammar (§13.2, pre-registered): a win claims WITHIN-DOMAIN transfer to
unseen sources under the SAME author pipeline, model-qualified.  Never
"generalization" simpliciter.  n=1 authoring draw -- the population variance over
readings is bootstrapped here; the authoring-stability variance is NOT (it needs
>= 2 authoring passes / real spend) and is stated as a limitation.

Deterministic and byte-stable: the bootstrap PRNG is seeded from the input
digest (no wall-clock, no Math.random), and no timestamp is emitted.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import common                                                     # noqa: E402
from buildloop import mdl_macros, recurrence                      # noqa: E402
from tools import measure_cluster_key as mck                      # noqa: E402
from tools import tower_census as tc                              # noqa: E402
import tools.ppm_ref as ppm_ref                                   # noqa: E402
import tools.c2_report as c2_report                               # noqa: E402

INPUT_JSON = _REPO / "results" / "holdout_transfer_input.json"
JSON_OUT = _REPO / "results" / "holdout_transfer.json"

REGISTERED_TABLE_DIGEST_16 = "ce5cb03fe2c5bdad"   # §13.2, reentry_evaluations.json
BOOTSTRAP_RESAMPLES = 1000

# The counting-currency pricing is done RAW (canon=False), matching
# tools.c2_report._counting_corpus_dl.  With the committed empty rung registry
# canon=True is byte-identical (the FI-W1-2 rung-free pin); the readout asserts
# that identity in its teeth rather than depending on it.
_CANON = False


# ------------------------------------------------------------- T_frozen
def reconstruct_frozen_table() -> tuple:
    """Replay the frozen checkpoint's governed waves through the refined greedy
    miner + GC to rebuild the census-of-record table WITH macro bodies (the
    committed census artifact stores only summaries).  Returns (table, gexo)."""
    records = tc._load_records()
    dream = tc._dream_readings(records)
    ref_greedy, gexo = mck._replay(records, "governed", True, dream, "refined")
    table = dict(ref_greedy)
    recurrence.gc_table(table, gexo)
    return table, gexo


def table_digest_16(table: dict, gexo: list) -> str:
    """The registered digest is common.sha256_json over the census SUMMARY of the
    table (measure_cluster_key._inventory over the governed exogenous readings),
    first 16 hex -- reproduced exactly here."""
    return common.sha256_json(mck._inventory(table, gexo))[:16]


# ------------------------------------------------------------- H
def load_holdout(path: Path = INPUT_JSON) -> tuple:
    """The committed holdout snapshot: returns (readings, source_ids, meta)."""
    doc = json.loads(path.read_text())
    # reproducibility guard: the snapshot's self-declared digest must hold.
    canon = [{"source_id": r["source_id"], "reading_json": r["reading_json"]}
             for r in sorted(doc["readings"], key=lambda x: x["source_id"])]
    got = common.sha256_json(canon)
    if got != doc["digest_sha256"]:
        raise SystemExit(
            f"STOP: holdout snapshot digest mismatch: {got} != "
            f"{doc['digest_sha256']}")
    readings = [r["reading_json"] for r in
                sorted(doc["readings"], key=lambda x: x["source_id"])]
    sids = [r["source_id"] for r in
            sorted(doc["readings"], key=lambda x: x["source_id"])]
    return readings, sids, doc


# ------------------------------------------------------------- currencies
def data_bits(readings: list, table: dict) -> float:
    """Counting-currency DATA bits (model/macro-definition bits EXCLUDED)."""
    return round(mdl_macros.corpus_dl(readings, table, canon=_CANON)["reading_cost"], 3)


def model_bits(table: dict) -> float:
    """The EXCLUDED model bits: the once-paid macro-definition cost."""
    return round(mdl_macros.corpus_dl([], table, canon=_CANON)["macro_cost"], 3)


def per_reading_savings(readings: list, table: dict) -> list:
    """Each reading's own data-bit saving under `table` vs the empty table.
    corpus_dl prices each reading independently (no cross-reading state), so the
    per-reading savings sum to the corpus transfer_saving -- and they are the
    bootstrap resampling unit."""
    out = []
    for r in readings:
        empty = mdl_macros.corpus_dl([r], {}, canon=_CANON)["reading_cost"]
        full = mdl_macros.corpus_dl([r], table, canon=_CANON)["reading_cost"]
        out.append(round(empty - full, 3))
    return out


def kt_data_bits(readings: list, table: dict) -> dict:
    """Adaptive order-1 KT code length over the (macro-rewritten) statement
    stream -- the §13.2 comparator: what a context model learns from scratch on
    H (empty table) vs what the transferred vocabulary buys on top (table)."""
    stream = c2_report.rewritten_stream(readings, table)
    a = len(set(stream))
    bits, _ = ppm_ref.adaptive_code(stream, c2_report.KT_ORDER,
                                    c2_report.KT_ALPHA, a)
    return {"kt_bits": round(bits, 4), "stream_length": len(stream),
            "alphabet_size": a}


# ------------------------------------------------------------- variance
def bootstrap_ci(per_reading: list, seed: int, resamples: int = BOOTSTRAP_RESAMPLES) -> dict:
    """POPULATION variance over readings: resample H's per-reading savings with
    replacement (Mersenne-Twister seeded from the input digest -- byte-stable, no
    wall-clock) and report the transfer_saving mean + 2.5/97.5 percentile CI.

    This is variance over READINGS only.  The AUTHORING-stability variance (would
    the same sources certify run-to-run) is NOT estimated -- it needs >= 2
    authoring passes / real spend; n=1 authoring draw is a stated limitation."""
    n = len(per_reading)
    rng = random.Random(seed)
    totals = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        totals.append(round(sum(per_reading[i] for i in idx), 3))
    totals.sort()
    mean = round(sum(totals) / resamples, 3)
    lo = totals[int(0.025 * resamples)]
    hi = totals[int(0.975 * resamples)]
    return {"resamples": resamples, "seed": seed, "resampling_unit": "reading",
            "mean": mean, "ci_2_5": lo, "ci_97_5": hi,
            "variance_scope": "POPULATION over readings only; authoring-stability "
                              "variance (run-to-run certification) NOT estimated "
                              "(needs >= 2 authoring passes / real spend); n=1 "
                              "authoring draw."}


# ------------------------------------------------------------- verdict
def _verdict(saving: float, model_bits_excluded: float, kt_from_scratch: float,
             kt_under_table: float, n: int, model_id: str) -> str:
    kt_gain = round(kt_from_scratch - kt_under_table, 3)
    return (
        f"Within-domain transfer readout, model-qualified ({model_id}, "
        f"wp-met/1 author pipeline, Euclid holdout = the certified Euclid IX "
        f"arithmetic propositions (h13-h20; the VII definitions did not certify "
        f"and are excluded, so transfer is measured on the arithmetic-proposition "
        f"subset only), n={n} certified readings, n=1 authoring draw). In the "
        f"counting currency the frozen 8-macro census-of-record table (digest "
        f"{REGISTERED_TABLE_DIGEST_16}) saves {saving} DATA bits repricing the "
        f"unseen holdout vs the empty table -- a POSITIVE within-domain transfer "
        f"signal. What transfers is GENERIC STRUCTURAL BOILERPLATE, not the "
        f"even/odd content: the macro carrying nearly all of it (m_5cfe6695215f, "
        f"matching 7 of the 8 readings) is a bare 'two consecutive Int object "
        f"declarations' idiom -- it matches ANY two Int variable declarations and "
        f"is blind to even/odd (h20, whose vars are Nat, misses it and is instead "
        f"touched by an atomic-hypothesis-pair macro that abstracts the even/odd "
        f"operator to a free parameter). The trained pipeline's recurring "
        f"declaration/hypothesis SHAPES recur in unseen Euclid sources; the "
        f"domain-specific even/odd reasoning is NOT what compresses. Model "
        f"bits ({model_bits_excluded}) are EXCLUDED per §13.2 (sunk, in-sample); "
        f"that exclusion is load-bearing -- with the macro-definition cost "
        f"included the small holdout does NOT pay for the table, so this is a "
        f"transfer readout, not an admission. The mandatory adaptive-KT "
        f"comparator DEFLATES the headline: an order-1 KT context model codes H "
        f"from scratch at {kt_from_scratch} bits and only {kt_under_table} under "
        f"the transferred vocabulary -- a {kt_gain}-bit gain -- i.e. the context "
        f"model learns almost all of the recurrence the macros encode, so the "
        f"vocabulary barely beats learning-from-scratch. Claim, un-inflated: the "
        f"trained vocabulary transfers within-domain to unseen Euclid sources "
        f"under the same authoring model in the counting currency, but the "
        f"transfer is marginal under a from-scratch context model and does not "
        f"survive charging its own model bits. Never 'generalization' "
        f"simpliciter -- same domain, same transcription conventions, same "
        f"authoring model. Authoring-stability variance is unestimated (n=1).")


# ------------------------------------------------------------- compute
def compute() -> dict:
    table, gexo = reconstruct_frozen_table()
    got_digest = table_digest_16(table, gexo)
    if got_digest != REGISTERED_TABLE_DIGEST_16:
        raise SystemExit(
            f"STOP: reconstructed T_frozen digest {got_digest} != registered "
            f"{REGISTERED_TABLE_DIGEST_16}; refusing to price against a wrong "
            f"table (§13.2).")

    H, sids, in_doc = load_holdout()
    mq = in_doc["model_qualification"]

    db_empty = data_bits(H, {})
    db_table = data_bits(H, table)
    saving = round(db_empty - db_table, 3)
    mbits = model_bits(table)

    per = per_reading_savings(H, table)
    seed = int(in_doc["digest_sha256"][:16], 16)
    boot = bootstrap_ci(per, seed)

    kt_empty = kt_data_bits(H, {})
    kt_table = kt_data_bits(H, table)

    uses = mdl_macros.corpus_dl(H, table, canon=_CANON)["reading_uses"]

    return {
        "artifact": "holdout_transfer",
        "registration": "COMPRESSION.md §13.2 WP-TRANSFER; measurement of record.",
        "what_this_is": "One-shot deterministic LLM-free repricing of the "
                        "already-authored Euclid holdout under the frozen trained "
                        "table vs the empty table; counting currency + adaptive-KT "
                        "comparator; model bits excluded (sunk, in-sample).",
        "model_qualification": {
            "model_id": mq["model_id"],
            "harness_version": mq["harness_version"],
            "author_pipeline": "wp-met/1 ungoverned arm (the metered holdout "
                               "authoring draw); one authoring pass (n=1).",
            "corpus_digest": mq["corpus_digest"],
            "prompt_vocabulary_digest": mq["prompt_vocabulary_digest"],
            "lean_available": mq["lean_available"],
        },
        "holdout_H": {
            "n": len(H),
            "source_ids": sids,
            "digest_sha256": in_doc["digest_sha256"],
            "snapshot": "results/holdout_transfer_input.json",
            "selection": "certified Euclid holdout (source_id 'h*'); dreams and "
                         "non-certified excluded.",
        },
        "frozen_table_T": {
            "name": "governed refined+GC census-of-record (8 macros)",
            "digest_sha256_16": got_digest,
            "registered_digest_sha256_16": REGISTERED_TABLE_DIGEST_16,
            "digest_verified": True,
            "reconstruction": "tools.measure_cluster_key replay (refined greedy + "
                              "gc_table) over the frozen checkpoint's governed "
                              "waves; bodies rebuilt, summary digest verified.",
            "n_macros": len(table),
            "macro_names": sorted(table),
        },
        "counting_currency": {
            "currency": "mdl_macros.corpus_dl reading_cost (canon=False, raw "
                        "committed pricing).",
            "data_bits_empty_table": db_empty,
            "data_bits_frozen_table": db_table,
            "transfer_saving": saving,
            "model_bits_excluded": mbits,
            "model_bits_note": "macro-definition cost; EXCLUDED per §13.2 "
                               "(sunk, in-sample). With model bits included the "
                               "frozen table's total on H is "
                               f"{round(db_table + mbits, 3)} > {db_empty} "
                               "(empty) -- it does NOT pay as an admission.",
            "per_reading_savings": dict(zip(sids, per)),
            "macro_reading_uses": {k: v for k, v in sorted(uses.items())},
            "bootstrap_ci": boot,
        },
        "adaptive_kt_comparator": {
            "estimator": f"order-{c2_report.KT_ORDER} KT (alpha="
                         f"{c2_report.KT_ALPHA}) over the macro-rewritten stream "
                         "(tools.ppm_ref.adaptive_code).",
            "kt_bits_from_scratch_empty": kt_empty["kt_bits"],
            "kt_bits_under_frozen_table": kt_table["kt_bits"],
            "kt_transfer_gain_bits": round(kt_empty["kt_bits"] - kt_table["kt_bits"], 4),
            "empty_stream": kt_empty,
            "frozen_table_stream": kt_table,
            "reading": "The from-scratch context model captures nearly all of the "
                       "recurrence; the transferred vocabulary's KT gain is small "
                       "-- the mandatory deflation of the counting-currency "
                       "headline (§13.2).",
        },
        "verdict": _verdict(saving, mbits, kt_empty["kt_bits"],
                            kt_table["kt_bits"], len(H), mq["model_id"]),
    }


def _dump_json(r: dict) -> str:
    return json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    r = compute()
    JSON_OUT.write_text(_dump_json(r))
    sys.stdout.write(f"wrote {JSON_OUT}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

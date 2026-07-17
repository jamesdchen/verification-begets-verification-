"""Teeth for WP-TRANSFER -- the §13.2 one-shot holdout transfer readout
(tools.holdout_transfer).  Deterministic, LLM-free.

The teeth pin the properties that make the readout an honest measurement rather
than a structural artifact:

  (a) BYTE-STABLE across two builds (no wall-clock, deterministic bootstrap).
  (b) MODEL BITS EXCLUDED -- the reported transfer_saving is DATA bits only; a
      version that charged the macro-definition bits would report a different
      (negative) number, and that difference is asserted.
  (c) NOT STRUCTURALLY ZERO -- a PLANTED reading whose statements instantiate a
      T_frozen macro body yields a POSITIVE saving, proving the foreign-table
      application actually matches and prices foreign readings (so the real
      holdout's saving is a measurement, whatever its sign).
  (d) BOOTSTRAP is deterministic (fixed seed -> identical CI) and resamples
      READINGS.
  (e) T_frozen's census digest == the registered ce5cb03fe2c5bdad.
  (f) H excludes dreams and non-certified readings.
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import common                                                     # noqa: E402
from buildloop import mdl_macros                                  # noqa: E402
from tools import holdout_transfer as ht                          # noqa: E402


# --------------------------------------------------------------- (e) T digest
def test_frozen_table_digest_matches_registration():
    table, gexo = ht.reconstruct_frozen_table()
    assert ht.table_digest_16(table, gexo) == ht.REGISTERED_TABLE_DIGEST_16
    assert ht.REGISTERED_TABLE_DIGEST_16 == "ce5cb03fe2c5bdad"
    assert len(table) == 8
    # bodies were rebuilt (the census artifact stores only summaries)
    assert all(m.get("body") for m in table.values())


# --------------------------------------------------------------- (f) H hygiene
def test_holdout_excludes_dreams_and_noncertified():
    doc = json.loads(ht.INPUT_JSON.read_text())
    assert doc["n"] == len(doc["readings"]) == 8
    for r in doc["readings"]:
        assert r["certified"] is True
        assert r["source_id"].startswith("h")
        assert not r["source_id"].startswith("d")   # no dream/system readings
    # snapshot digest self-consistency (the reproducibility guard)
    H, sids, loaded = ht.load_holdout()
    assert loaded["digest_sha256"] == doc["digest_sha256"]
    assert len(H) == 8


# --------------------------------------------------------------- (b) model bits out
def test_model_bits_excluded_from_transfer_saving():
    r = ht.compute()
    cc = r["counting_currency"]
    table, _ = ht.reconstruct_frozen_table()
    H, _, _ = ht.load_holdout()

    # the reported saving is DATA bits only: empty reading_cost - frozen reading_cost
    db_empty = mdl_macros.corpus_dl(H, {}, canon=ht._CANON)["reading_cost"]
    db_table = mdl_macros.corpus_dl(H, table, canon=ht._CANON)["reading_cost"]
    assert cc["transfer_saving"] == round(db_empty - db_table, 3)

    # a version that INCLUDED model bits would differ: the frozen table charges a
    # non-zero macro_cost, so the with-model-bits saving is strictly smaller.
    mbits = cc["model_bits_excluded"]
    assert mbits > 0
    saving_with_model_bits = round((db_empty) - (db_table + mbits), 3)
    assert saving_with_model_bits != cc["transfer_saving"]
    assert saving_with_model_bits < cc["transfer_saving"]


# --------------------------------------------------------- (c) not structurally zero
def _instantiate_body(macro):
    """Build a concrete reading whose statement stream IS one instantiation of a
    macro body (placeholders bound to concrete scalars), so the foreign-table
    rewrite must match it."""
    subst = {"$p0": "even", "$p1": "odd", "$p2": "prime", "$p3": "square"}

    def fill(node):
        if isinstance(node, str):
            return subst.get(node, node)
        if isinstance(node, dict):
            return {k: fill(v) for k, v in node.items()}
        if isinstance(node, list):
            return [fill(v) for v in node]
        return node

    stmts = [{"id": f"s{i}", "force": "presupposition", "quote": "",
              "lf": fill(tmpl)} for i, tmpl in enumerate(macro["body"])]
    return {"theorem": "planted", "statements": stmts}


def test_planted_matching_reading_yields_positive_saving():
    table, _ = ht.reconstruct_frozen_table()
    # pick the macro the real holdout leans on, and prove the machinery matches a
    # foreign (not-mined-from-H) planted instantiation of its body.
    macro = table["m_5cfe6695215f"]
    planted = _instantiate_body(macro)

    # sanity: the empty-table rewrite does NOT collapse it, the frozen table does
    db_empty = mdl_macros.corpus_dl([planted], {}, canon=ht._CANON)["reading_cost"]
    priced = mdl_macros.corpus_dl([planted], table, canon=ht._CANON)
    db_table = priced["reading_cost"]
    assert db_empty - db_table > 0                       # positive saving
    assert priced["reading_uses"].get("m_5cfe6695215f", 0) == 1   # it matched

    # and it flows through the tool's per-reading pricing identically
    per = ht.per_reading_savings([planted], table)
    assert per[0] > 0


# --------------------------------------------------------- (d) deterministic bootstrap
def test_bootstrap_deterministic_and_resamples_readings():
    per = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 16.0]
    seed = 12345
    a = ht.bootstrap_ci(per, seed, resamples=500)
    b = ht.bootstrap_ci(per, seed, resamples=500)
    assert a == b                                        # fixed seed -> identical
    assert a["resampling_unit"] == "reading"
    # a different seed gives a (generally) different draw -> not a constant
    c = ht.bootstrap_ci(per, seed + 1, resamples=500)
    assert (c["ci_2_5"], c["ci_97_5"]) != (a["ci_2_5"], a["ci_97_5"]) \
        or c["mean"] != a["mean"]
    # resamples of a constant vector are the constant total (resampling readings)
    const = ht.bootstrap_ci([5.0, 5.0, 5.0, 5.0], seed, resamples=50)
    assert const["mean"] == 20.0 and const["ci_2_5"] == 20.0


# --------------------------------------------------------------- (a) byte-stable
def test_output_byte_stable_across_two_builds():
    one = ht._dump_json(ht.compute())
    two = ht._dump_json(ht.compute())
    assert one == two
    # no wall-clock leaked into the artifact
    for banned in ("now_iso", "timestamp", "Z\","):
        assert banned not in one


# --------------------------------------------------- headline sanity (measurement)
def test_headline_numbers_present_and_consistent():
    r = ht.compute()
    cc = r["counting_currency"]
    assert cc["transfer_saving"] == round(
        cc["data_bits_empty_table"] - cc["data_bits_frozen_table"], 3)
    assert cc["transfer_saving"] >= 0
    # the mandatory KT deflation line ships in the same artifact
    kt = r["adaptive_kt_comparator"]
    assert "kt_bits_from_scratch_empty" in kt
    assert "kt_bits_under_frozen_table" in kt
    assert r["frozen_table_T"]["digest_verified"] is True

"""WP-I2: certify-at-seed for MathReadings (F3.2).

Committed MathReadings under specs/mathsources/readings/ are certified at seed
time and persisted into the readings table keyed by their math-source demand_id,
covering the corpus row.  Coverage here is the FIDELITY tier (non-vacuity +
entailed instances); the F0 kernel statement-cert is deferred without a Lean
toolchain.
"""
import os
import tempfile

import common
from library import Registry
import cgb
from buildloop import dl as dl_mod


def _reg():
    return Registry(db_path=os.path.join(tempfile.mkdtemp(), "t.sqlite"))


def _did(relpath):
    return common.sha256_bytes(("math-source:" + relpath).encode())


def test_seed_covers_corpus_rows():
    reg = _reg()
    cgb._ledger_sync(reg)                 # ingest math-source rows
    m = cgb._seed_math_readings(reg)      # certify + persist the committed readings
    # S4a' (PLAN_REFLECT) grew the corpus with ∃-class readings.  Two of them
    # (64, 65) pass the fidelity tier (in-box witnesses everywhere); THREE are
    # the DESIGNED edge-refusal class (43, 63, 66: a box-edge outer world has
    # its only witnesses outside the bounded shadow -- the exact class the
    # witness-template channel exists to certify; math_witness.py docstring,
    # source 43).  Their seed-time refusal is the honest measured fact, pinned
    # exactly so a silently-passing gate or a new refusal stays loud.
    assert m["covered"] >= 5 and m["failed"] == 3
    # each fidelity-covered reading covers its corpus row.
    for stem in ("01_dvd_reflexive", "02_one_divides_all", "04_even_plus_even",
                 "64_pos_pred_witness", "65_double_witness"):
        did = _did(f"specs/mathsources/{stem}.txt")
        row = reg.demand_get(did)
        assert row is not None and row["status"] == "covered", stem
        assert reg.reading_get(did) is not None, stem
    # the edge-refusal three stay honestly uncovered at the fidelity tier.
    for stem in ("43_larger_integer_exists", "63_gap_witness", "66_sum_exists"):
        did = _did(f"specs/mathsources/{stem}.txt")
        row = reg.demand_get(did)
        assert row is not None and row["status"] != "covered", stem


def test_ledger_counts_covered_math():
    reg = _reg()
    cgb._ledger_sync(reg)
    cgb._seed_math_readings(reg)
    tot = dl_mod.ledger_dl(reg)
    assert tot["covered_math"] >= 3
    # a covered exogenous math-source row prices below the uncovered penalty.
    assert tot["covered_math"] <= tot["total_math"]


def test_byte_match_is_enforced(tmp_path):
    # a reading whose source does not byte-match a committed corpus .txt is a
    # hard error (H44) -- construct an isolated root to prove the guard fires.
    import json
    import pytest
    root = tmp_path
    rdir = root / "specs" / "mathsources" / "readings"
    rdir.mkdir(parents=True)
    (root / "specs" / "mathsources" / "99_x.txt").write_text("A real statement.")
    (rdir / "99_x.json").write_text(json.dumps(
        {"source": "A DIFFERENT statement.",
         "reading": {"theorem": "t", "statements": [
             {"id": "c", "force": "demand", "quote": "A DIFFERENT statement.",
              "lf": {"kind": "conclusion",
                     "pred": {"op": "=", "args": [{"lit": 1}, {"lit": 1}]}}}]}}))
    with pytest.raises(SystemExit):
        cgb._seed_math_readings(_reg(), root=root)

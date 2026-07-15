"""Teeth for `cgb ledger seed-readings` (Zone 3 S0.2) provenance + enforcement.

Fast and LLM-free: certify_reading is monkeypatched with a canned success so the
test exercises the SEED LOGIC (byte-match classification, origin tagging, the
H44 hard-error) without running the SMT/service kernel.  A separate manual/demo
path exercises real certification end-to-end.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
import cgb
from library import Registry
from run import semantic as semantic_mod


def _fake_certify(request, reading_text, *, event_sink=None, cache_get=None,
                  cache_put=None, write_output=True, macro_table=None,
                  on_certified=None):
    res = semantic_mod.SemanticResult(ok=True,
                                      layers=[("reading-gate", True, [])])
    if on_certified is not None:
        on_certified(res, "fake-cert-" + common.sha256_json(reading_text)[:8])
    return res


def _reg():
    return Registry(db_path=os.path.join(tempfile.mkdtemp(), "r.sqlite"))


def test_seed_classifies_real_and_dream_by_origin(monkeypatch):
    monkeypatch.setattr(semantic_mod, "certify_reading", _fake_certify)
    reg = _reg()
    counts = cgb._seed_readings(reg)
    # 6 committed-request readings (exogenous) + 3 dream anchors (system)
    assert counts["certified"] == counts["seen"]
    assert counts["real"] >= 6 and counts["dream"] >= 3
    rows = reg.readings_all()
    dem = {r["demand_id"]: r for r in reg.demand_all()}
    real = sum(1 for r in rows
               if dem.get(r["demand_id"], {}).get("origin") == "exogenous")
    dream = sum(1 for r in rows
                if dem.get(r["demand_id"], {}).get("origin") == "system")
    assert real == counts["real"] and dream == counts["dream"]
    assert real >= 6 and dream >= 3


def test_real_reading_without_byte_match_hard_errors(monkeypatch, tmp_path):
    """A top-level (real-classified) reading whose request matches no committed
    specs/requests file must hard-error at seed time (H44)."""
    monkeypatch.setattr(semantic_mod, "certify_reading", _fake_certify)
    (tmp_path / "specs" / "readings").mkdir(parents=True)
    (tmp_path / "specs" / "requests").mkdir(parents=True)
    # a grounded-enough reading, but its request is NOT a committed request file
    bad = {"request": "an uncommitted request that matches nothing",
           "reading": {"service": "svc", "statements": [
               {"id": "s1", "force": "choice", "quote": "",
                "lf": {"kind": "action", "name": "go"}},
               {"id": "s2", "force": "choice", "quote": "",
                "lf": {"kind": "lifecycle", "states": ["open", "closed"],
                       "initial": "open"}}]}}
    (tmp_path / "specs" / "readings" / "orphan.json").write_text(json.dumps(bad))
    reg = _reg()
    try:
        cgb._seed_readings(reg, root=str(tmp_path))
        assert False, "expected a hard error for a real reading with no byte-match"
    except SystemExit:
        pass


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))

"""Tooth for the S4.0 fill-path fix (H46): a served request grows the corpus.

Before the fix, buildloop.loop._dispatch_request passed the request PATH where
the request TEXT belongs and called synthesize_service (which never returns a
`reading` key), so registry.reading_add was unreachable and the live loop never
grew the corpus recurrence mines.  This test drives the dispatcher on a fresh DB
with a canned synthesize_semantic and asserts a readings row appears.

LLM-free: synthesize_semantic is monkeypatched; no LLM/kernel is invoked.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop import loop, service_loop
from library import Registry


def _reg():
    return Registry(db_path=os.path.join(tempfile.mkdtemp(), "r.sqlite"))


_CANNED_READING = {"service": "svc", "statements": [
    {"id": "s1", "force": "demand", "quote": "never oversell",
     "lf": {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}}]}


def test_dispatch_request_persists_a_reading(monkeypatch):
    def fake_semantic(request, **kw):
        return {"status": "certified", "reading": _CANNED_READING,
                "layers": [("reading-gate", True, []), ("compile", True, [])]}
    monkeypatch.setattr(service_loop, "synthesize_semantic", fake_semantic)

    reg = _reg()
    did = "req-fill-1"
    move = {"demand_id": did,
            "row": {"payload_ref": "specs/requests/01_ticketing_oversell.txt"}}
    assert reg.reading_get(did) is None
    out = loop._dispatch_request(move, None, reg, [], "frequency", False,
                                 model="stub-model")
    assert out["status"] == "request-certified"
    row = reg.reading_get(did)
    assert row is not None
    assert common.canonical_json(_CANNED_READING) == row["reading_json"]
    # the persisted cert_id is the composed layer-hash, not a placeholder
    assert row["cert_id"] and row["cert_id"] != "reading-cert"


def test_dispatch_request_llm_free_is_a_scheduled_marker():
    reg = _reg()
    out = loop._dispatch_request({"demand_id": "x", "row": {}}, None, reg, [],
                                 "frequency", False, model=None)
    assert out["status"] == "request-scheduled"
    assert reg.reading_get("x") is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))

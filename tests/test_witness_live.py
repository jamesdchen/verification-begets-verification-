"""The S5 witness discipline is enforced on the LIVE scheduler path, not only in
tagged-dict unit tests.

Two live wirings make it real (both added after an adversarial review found the
discipline was unenforceable live):
  * `dl.snapshot` joins each reading to its demand row's `origin`, so a reading
    dict carries `origin` ("exogenous" == real, "system" == dream) even though
    the readings table has no origin column;
  * `loop._recurrence_moves` / `loop._dispatch_recurrence` pass an exogenous-only
    `witness_filter` whenever any system-origin reading is present.

So a pattern that recurs only across dreams is mined-but-refused until real
requests witness it -- and a dream-free corpus stays byte-identical.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from buildloop import dl, loop
from library import Registry


def _reg():
    return Registry(db_path=os.path.join(tempfile.mkdtemp(), "r.sqlite"))


def _stmt(sid):
    return {"id": sid, "force": "demand", "quote": "s",
            "lf": {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}}


def _stmt2(sid):
    return {"id": sid, "force": "demand", "quote": "s",
            "lf": {"kind": "bound", "action": "a", "left": "n",
                   "cmp": "<=", "right": "q"}}


def _add_reading(reg, did, origin, i):
    reg.demand_upsert({"demand_id": did, "kind": "nl-request", "origin": origin,
                       "status": "open", "language": None, "features": None,
                       "payload_ref": did, "size_bytes": 10})
    reg.reading_add(did, json.dumps({"service": "s",
                    "statements": [_stmt(f"{i}a"), _stmt2(f"{i}b")]}), f"c{i}")


def test_snapshot_attaches_origin():
    reg = _reg()
    _add_reading(reg, "real-0", "exogenous", 0)
    _add_reading(reg, "dream-0", "system", 1)
    snap = dl.snapshot(reg)
    assert snap.readings["real-0"]["origin"] == "exogenous"
    assert snap.readings["dream-0"]["origin"] == "system"


def test_dreams_alone_do_not_witness_but_reals_flip_it():
    reg = _reg()
    for i in range(3):                              # 3 dreams share the cluster
        _add_reading(reg, f"dream-{i}", "system", i)
    assert loop._recurrence_moves(dl.snapshot(reg)) == [], \
        "a dream-only pattern must not be mineable (no real witnesses)"
    for i in range(2):                              # + 2 real witnesses
        _add_reading(reg, f"real-{i}", "exogenous", 100 + i)
    assert len(loop._recurrence_moves(dl.snapshot(reg))) >= 1, \
        "adding real witnesses must flip the pattern to mineable"


def test_dream_free_corpus_is_unfiltered():
    # No system-origin readings -> witness_filter is None -> byte-identical to
    # the pre-S5 behavior: the real cluster mines normally.
    reg = _reg()
    for i in range(2):
        _add_reading(reg, f"real-{i}", "exogenous", i)
    assert loop._exogenous_witness_filter(
        list(dl.snapshot(reg).readings.values())) is None
    assert len(loop._recurrence_moves(dl.snapshot(reg))) >= 1


if __name__ == "__main__":
    test_snapshot_attaches_origin()
    test_dreams_alone_do_not_witness_but_reals_flip_it()
    test_dream_free_corpus_is_unfiltered()
    print("all live-witness teeth pass")

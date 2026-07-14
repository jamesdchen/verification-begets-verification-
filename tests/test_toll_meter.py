#!/usr/bin/env python3
"""W4.1 toll meter -- the cage-emitter teeth.

The cage is a task-time component and the ledger's DB is written ONLY by the loop
(house rule 9).  The single task-time -> ledger bridge is an append-only JSONL
file the cage writes per call: `common.ARTIFACTS / "toll.jsonl"`, one record
`{incumbent_hash, tool, verdict_layer, wall_ms}` per step, ingested at epoch start
by `library.Registry.ingest_toll_jsonl` into `toll:{incumbent_hash}:calls`.

This proves both halves meet:
  * EMIT: `Cage.run` appends exactly one line per step, with the tool, the verdict
    layer ("ok" on accept else the reject layer), and the SAME incumbent_hash the
    scheduler prices under (`Cage.incumbent_hash`, which the caller sets to
    `buildloop.dl.incumbent_hash_of(row)` for wrapped/adapter incumbents).
  * INGEST: `ingest_toll_jsonl` counts one per record into
    `toll:{incumbent_hash}:calls`; re-ingest is idempotent (the `.pos` offset);
    `wall_ms` (reporting-only, house rule 13) never enters any counter.

Runnable under pytest AND as `python3 tests/test_toll_meter.py`.
"""
from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

import common
import library
from generators import service_model
from run import guarded
from demo_guarded import STORE, HONEST_SRC

# init={"stock":3}: reserve qty=1 accepts (state shop->held, guard 1<=3, qty>=1,
# egress-valid output); a SECOND reserve is out of sequence (reserve is from
# "shop", state is now "held") -> rejected at the "sequencing" layer.  One accept,
# one reject -- both layers present in one run.
_INIT = {"stock": 3}
_SEQ = [["reserve", {"qty": 1}], ["reserve", {"qty": 1}]]
_EXPECTED_LAYERS = ["ok", "sequencing"]


def _model():
    return service_model.parse_service_spec(json.dumps(STORE))


def _run_meter(tmp):
    """Point the toll file + a fresh registry at `tmp`, run one caged session, and
    return (cage, toll_path, jsonl_lines, verdicts)."""
    common.ARTIFACTS = tmp                                     # redirect toll.jsonl
    m = _model()
    cage = guarded.Cage(m, HONEST_SRC)
    verdicts = cage.run(_INIT, _SEQ)
    toll_path = tmp / "toll.jsonl"
    lines = [json.loads(x) for x in
             toll_path.read_text().splitlines() if x.strip()]
    return cage, toll_path, lines, verdicts


def _do(tmp_path, monkeypatch=None):
    orig = common.ARTIFACTS
    try:
        cage, toll_path, lines, verdicts = _run_meter(tmp_path)

        # the caged session itself behaves as designed (one accept, one reject)
        assert [v.get("ok") for v in verdicts] == [True, False], verdicts

        # EMIT: one JSONL line per step, right {incumbent_hash, tool, verdict_layer}
        assert len(lines) == len(_SEQ), (
            "expected one toll line per step", len(lines), lines)
        for i, rec in enumerate(lines):
            assert rec["incumbent_hash"] == cage.incumbent_hash, (
                "toll incumbent_hash must be the priced identity", rec)
            assert rec["tool"] == _SEQ[i][0], ("tool per step", i, rec)
            assert rec["verdict_layer"] == _EXPECTED_LAYERS[i], (
                "verdict layer per step", i, rec)
            assert "wall_ms" in rec, ("wall_ms is written (reporting-only)", rec)

        ih = cage.incumbent_hash
        reg = library.Registry(db_path=str(tmp_path / "registry.sqlite"))

        # INGEST: one increment per record -> counter == number of steps
        n = reg.ingest_toll_jsonl(toll_path)
        assert n == len(_SEQ), ("ingested count", n)
        assert reg.counter_get(f"toll:{ih}:calls") == float(len(_SEQ)), (
            "toll counter must equal the number of steps",
            reg.counter_get(f"toll:{ih}:calls"))

        # IDEMPOTENT: a second ingest of the same append-only file adds nothing
        n2 = reg.ingest_toll_jsonl(toll_path)
        assert n2 == 0, ("re-ingest must add nothing (.pos offset)", n2)
        assert reg.counter_get(f"toll:{ih}:calls") == float(len(_SEQ)), (
            "re-ingest changed the counter", reg.counter_get(f"toll:{ih}:calls"))

        # wall_ms NEVER enters the counter: the only counter is the calls key, and
        # no key mentions wall_ms.
        rows = reg.db.execute("SELECT key, value FROM counters").fetchall()
        keys = [k for k, _ in rows]
        assert keys == [f"toll:{ih}:calls"], ("unexpected counters", rows)
        assert not any("wall_ms" in k for k in keys), ("wall_ms leaked", rows)
        return ih
    finally:
        common.ARTIFACTS = orig


def test_toll_emit_and_ingest(tmp_path):
    _do(tmp_path)


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        ih = _do(pathlib.Path(d))
    print("PASS toll-meter  emit 1 line/step, ingest -> toll:%s:calls == %d, "
          "re-ingest idempotent, wall_ms never counted" % (ih[:12], len(_SEQ)))

#!/usr/bin/env python3
"""W4.2 conversion -- the LLM/Dafny-FREE teeth.

Two guarantees are checkable without an LLM or a solver, so they live here (the
full five-teeth arc is `demos/demo_conversion.py`, REQUIRES_LLM=True):

  (a) W4.2b SWAP -- the status transition.  A caged-incumbent demand row goes
      status -> 'converted' with `payload_ref` pointing at the replacement and
      `covered_via` the replacement cert id; the cage is never mutated; a second
      call is idempotent.

  (b) ORACLE_REF CACHE-IDENTITY -- two `translation-cert` /
      `incumbent-differential` contracts identical EXCEPT their `oracle_ref`
      (e.g. a different incumbent_hash) must produce DISTINCT `kernel.cache_key`
      values (a clean miss).  This guards the trapdoor cache-collision hazard:
      an incumbent byte-identical up to bound n must NOT reproduce the honest
      incumbent's key and be served its PASS.  Identical oracle_ref -> identical
      key (a clean hit).

Runnable under pytest AND as `python3 tests/test_conversion.py`.
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

import common
import kernel
import library
from buildloop import convert


# --------------------------------------------------------------------------- #
#  (a) W4.2b swap: the status transition + idempotency.                        #
# --------------------------------------------------------------------------- #
_INCUMBENT_REF = "specs/incumbent/order_service.py"
_DEMAND_ID = common.sha256_bytes(("caged-incumbent:" + _INCUMBENT_REF).encode())
_REP_CERT = "cert-replacement-deadbeef"
_REP_PAYLOAD = common.canonical_json(
    {"replacement_cert_id": _REP_CERT, "replacement_artifact_hash": "aa" * 4})


def _caged_row(reg):
    reg.demand_upsert({
        "demand_id": _DEMAND_ID, "kind": "caged-incumbent",
        "origin": "exogenous", "status": "open",
        "payload_ref": _INCUMBENT_REF, "size_bytes": 100})
    return reg.demand_get(_DEMAND_ID)


def _do_swap(tmp_path):
    reg = library.Registry(db_path=str(tmp_path / "registry.sqlite"))
    row = _caged_row(reg)
    assert row["status"] == "open", row
    assert row["kind"] == "caged-incumbent", row

    out = convert.swap_converted(reg, _DEMAND_ID,
                                 replacement_cert_id=_REP_CERT,
                                 replacement_payload_ref=_REP_PAYLOAD)
    # status -> converted (a status transition, NOT a kind mutation)
    assert out["status"] == "converted", out
    assert out["kind"] == "caged-incumbent", ("kind must never mutate", out)
    # payload_ref points at the replacement; covered_via is the replacement cert
    assert out["payload_ref"] == _REP_PAYLOAD, ("payload_ref updated", out)
    assert out["covered_via"] == _REP_CERT, ("covered_via = replacement cert", out)

    # re-read from the DB confirms it persisted
    reread = reg.demand_get(_DEMAND_ID)
    assert reread["status"] == "converted" and reread["payload_ref"] == _REP_PAYLOAD

    # IDEMPOTENT: a second call with the same cert id is a no-op
    again = convert.swap_converted(reg, _DEMAND_ID,
                                   replacement_cert_id=_REP_CERT,
                                   replacement_payload_ref=_REP_PAYLOAD)
    assert again["status"] == "converted" and again["payload_ref"] == _REP_PAYLOAD

    # a converted row is priced as the retention right-hand side (never the toll
    # stock): with no ingested calls it is 0, strictly below an open incumbent's
    # capped toll -- the conversion can only lower ledger_dl.
    from buildloop import dl
    snap = dl.snapshot(reg)
    conv_cost = dl._demand_cost(reg.demand_get(_DEMAND_ID), snap)
    assert conv_cost == 0.0, ("converted retention cost with no calls", conv_cost)
    return reg


def test_swap_status_transition(tmp_path):
    _do_swap(tmp_path)


def test_swap_rejects_non_incumbent(tmp_path):
    reg = library.Registry(db_path=str(tmp_path / "r2.sqlite"))
    did = common.sha256_bytes(b"spec-file:x")
    reg.demand_upsert({"demand_id": did, "kind": "spec-file",
                       "origin": "exogenous", "status": "open",
                       "payload_ref": "specs/backlog/x.ksy", "size_bytes": 10})
    try:
        convert.swap_converted(reg, did, replacement_cert_id="c",
                               replacement_payload_ref="p")
        assert False, "swap must refuse a non-caged-incumbent row"
    except ValueError:
        pass


# --------------------------------------------------------------------------- #
#  (b) oracle_ref cache-identity: a clean miss on a different incumbent.       #
# --------------------------------------------------------------------------- #
_REP_SPEC = common.canonical_json({
    "name": "rep", "context": {"ok": {"init_min": 0, "init_max": 0}},
    "states": ["q0", "q1"], "initial": "q0",
    "tools": [{"name": "go", "from": "q0", "to": "q1",
               "input_schema": {"type": "object", "properties": {},
                                "required": [], "additionalProperties": False}}],
    "safety": {"when": "*", "invariant": {"op": "==", "left": "ok", "right": 0}}})


def _contract(incumbent_hash, *, cage_hash="CAGE", low=_REP_SPEC):
    return {
        "type": "translation-cert", "anchor": "incumbent-differential",
        "high_language": "mealy-lift", "high_spec_text": "{}",
        "low_spec_text": low,
        "oracle_ref": {"incumbent_hash": incumbent_hash, "cage_hash": cage_hash,
                       "sandbox_params": {"timeout": 60}},
        "n": 7}


def _key(contract):
    return kernel.cache_key({"kind": "service", "files": {}}, contract)


def test_oracle_ref_cache_identity():
    honest = _contract("incumbent-HONEST")
    # a trapdoor incumbent byte-identical up to bound n: same replacement spec,
    # same cage_hash, but a DIFFERENT incumbent_hash -> must NOT collide.
    trapdoor = _contract("incumbent-TRAPDOOR")

    k_honest = _key(honest)
    k_trapdoor = _key(trapdoor)
    assert k_honest != k_trapdoor, (
        "oracle_ref MUST enter the cache key -- a different incumbent_hash is a "
        "clean miss, never a served PASS", k_honest, k_trapdoor)

    # a byte-identical contract reproduces the SAME key (a clean hit)
    assert _key(_contract("incumbent-HONEST")) == k_honest, "identity must be stable"

    # a different cage_hash is also a clean miss (the whole oracle_ref folds in)
    assert _key(_contract("incumbent-HONEST", cage_hash="OTHER")) != k_honest, (
        "cage_hash is part of oracle_ref and must flip the key")

    # a different replacement (low_spec_text) is a clean miss too
    other_low = _REP_SPEC.replace('"go"', '"other"')
    assert _key(_contract("incumbent-HONEST", low=other_low)) != k_honest, (
        "the replacement spec is part of the identity")

    # the tier the cdesc names for this anchor is conformance-relative(n)
    _subj, cdesc = kernel._subject_and_cdesc({"kind": "service", "files": {}},
                                             honest)
    assert cdesc["tier"] == "conformance-relative(n)", cdesc
    assert cdesc["anchor"] == "incumbent-differential", cdesc


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _do_swap(pathlib.Path(d))
    test_oracle_ref_cache_identity()
    print("PASS conversion  (a) W4.2b swap status->converted + idempotent; "
          "(b) oracle_ref cache-identity clean miss on incumbent_hash / cage_hash "
          "/ replacement")

#!/usr/bin/env python3
"""P0.5.3 parity tripwire: the pooled channel path MUST equal the direct path.

certify_service fans each layer's channels across a process pool via
kernel.channel_specs()+kernel.run_channel(); the standalone check() path runs
kernel._dispatch().  If those two ever drift (a renamed backend, a dropped role,
a re-ordered obligation) the pool would silently issue a different verdict than
check().  This test pins them together: for EVERY kernel.POOL_SUPPORTED type it
builds a real (artifact, contract) fixture -- mirroring the demos -- and asserts

  1. channel_specs' kind == _dispatch's kind,
  2. the MULTISET of (backend, role, result) triples matches (sorted), and
  3. kernel.adjudicate() over each channel list yields the same verdict CLASS
     (both Certificate, or both ErrorTranscript with equal .verdict).

Plus coverage: every contract type run.service._build_jobs emits is pool-safe,
and channel_specs refuses a non-pool type yet accepts every pool type.

Runnable under pytest AND as `python3 tests/test_channel_parity.py` (prints
PASS/<type>).  run_channel may run z3/cvc5 in-process here -- fine, one process.
"""
from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

import common
import kernel
from kernel.certs import Certificate


def _read(rel):
    return (_ROOT / rel).read_text()


# --- one real (artifact, contract) fixture per POOL_SUPPORTED type -----------
# Each is a canonical, well-formed artifact (as in demo_tool / demo_constraint /
# demo_protocol / demo_service / demo_tower), so both paths certify.  PARITY is
# the property under test, not the verdict: a shared-but-broken artifact would
# still have to fail IDENTICALLY on both paths.  Built once and cached.
_FX = None


def _fixtures():
    global _FX
    if _FX is not None:
        return _FX
    from generators import (toolgen, constraint_model as cm,
                            constraint_gen as cg, protocol_model as pm,
                            protocol_gen as pg, service_model, service_gen)
    fx = {}
    # (i) tool-differential: pydantic tool validator vs jsonschema reference
    ts = _read("specs/tools/create_calendar_event.json")
    fx["tool-differential"] = (
        {"kind": "tool", "files": toolgen.emit_pydantic_tool(ts)},
        {"type": "tool-differential", "schema_text": ts, "max_examples": 30})
    # (ii) constraint-cert: dual-SMT proof (z3+cvc5) + solver-boundary channel
    cs = _read("specs/constraints/book_meeting.json")
    cmod = cm.parse_constraint_spec(cs)          # has an invariant -> provable
    fx["constraint-cert"] = (
        {"kind": "constraint-validator", "files": cg.emit_validator(cmod)},
        {"type": "constraint-cert", "spec_text": cs})
    # (iii) protocol-cert: dual BMC safety (z3+cvc5) + conformance differential
    ps = _read("specs/protocols/order.json")
    pmod = pm.parse_protocol_spec(ps)
    fx["protocol-cert"] = (
        {"kind": "protocol-validator", "files": pg.emit_validator(pmod)},
        {"type": "protocol-cert", "spec_text": ps})
    # (iv) service-conformance: composed dispatcher vs reference + liveness
    ss = _read("specs/services/orders.json")
    smod = service_model.parse_service_spec(ss)
    svc_files = service_gen.emit_service(smod)   # reused by (v)
    fx["service-conformance"] = (
        {"kind": "service", "files": svc_files},
        {"type": "service-conformance", "spec_text": ss})
    # (v) intent-scenarios: reuse the orders dispatcher; hand-built scenarios in
    # the buildloop.validate.validate_scenarios shape -- {name, init(=exactly the
    # context vars), seq=[[tool,args]..], expect=[bool per step]} -- with one
    # fully-accepting run (golden path) and one refused step (underpayment at the
    # pay guard).  Both channels replay the SAME traces, so parity is structural.
    scn = {"scenarios": [
        {"name": "golden-run", "init": {"due": 10, "auth": 0},
         "seq": [["login", {"user": "u", "token": "t"}],
                 ["pay", {"amount": 10, "currency": "usd"}],
                 ["ship", {"address": "a"}], ["close", {}]],
         "expect": [True, True, True, True]},
        {"name": "underpay-refused", "init": {"due": 10, "auth": 0},
         "seq": [["login", {"user": "u", "token": "t"}],
                 ["pay", {"amount": 5, "currency": "usd"}]],
         "expect": [True, False]}]}
    fx["intent-scenarios"] = (
        {"kind": "service", "files": svc_files},
        {"type": "intent-scenarios", "spec_text": ss,
         "scenarios_text": json.dumps(scn)})
    _FX = fx
    return fx


def _triples(channels):
    """A channel list reduced to the comparable multiset the two paths must share:
    sorted (backend, role, result).  role is normalised so a channel with no role
    key ('' by default) and one with an explicit '' compare equal."""
    return sorted((c["backend"], c.get("role", "") or "", c["result"])
                  for c in channels)


def _verdict_class(kind, artifact, contract, channels):
    """adjudicate() over one channel list, collapsed to its verdict CLASS:
    ('cert',) for a Certificate else ('transcript', <verdict>).  Pure in the
    channels, so equal channel multisets => equal class (the contract_hash is
    cosmetic to the classification -- computed properly anyway)."""
    subject, cdesc = kernel._subject_and_cdesc(artifact, contract)
    v = kernel.adjudicate(kind, subject, common.sha256_json(cdesc), cdesc,
                          channels)
    return ("cert",) if isinstance(v, Certificate) else ("transcript", v.verdict)


def _assert_parity(ctype):
    """For one type: channel_specs()+run_channel() (the path certify_service fans
    across processes) reproduces _dispatch()'s kind, channel multiset, and
    adjudicated verdict class exactly."""
    artifact, contract = _fixtures()[ctype]
    d_kind, d_ch = kernel._dispatch(artifact, contract, None)   # direct path
    p_kind, specs = kernel.channel_specs(artifact, contract)    # pooled path
    p_ch = [kernel.run_channel(s) for s in specs]               # z3/cvc5 in-proc
    assert p_kind == d_kind, (ctype, "kind", p_kind, "!=", d_kind)
    assert _triples(p_ch) == _triples(d_ch), (
        ctype, "channel multiset", _triples(p_ch), "!=", _triples(d_ch))
    dv = _verdict_class(d_kind, artifact, contract, d_ch)
    pv = _verdict_class(p_kind, artifact, contract, p_ch)
    assert dv == pv, (ctype, "verdict class", pv, "!=", dv)


# --- pytest entry points (parametrized per pool type) ------------------------
try:
    import pytest
    _param = pytest.mark.parametrize("ctype", list(kernel.POOL_SUPPORTED))
except ImportError:                       # script mode without pytest installed
    def _param(fn):
        return fn


@_param
def test_channel_parity(ctype):
    """Pooled path == direct path for every POOL_SUPPORTED contract type."""
    _assert_parity(ctype)


def test_build_jobs_types_are_pool_safe():
    """Coverage: every contract type the pooling orchestrator (_build_jobs)
    emits is in POOL_SUPPORTED -- else certify_service would hit channel_specs'
    ValueError at fan-out time."""
    from generators import service_model
    from run import service as svc
    ss = _read("specs/services/orders.json")
    m = service_model.parse_service_spec(ss)
    jobs, _svc = svc._build_jobs(m, ss)
    types = {con["type"] for _n, _a, con in jobs}
    assert types, "no jobs emitted"
    assert types <= set(kernel.POOL_SUPPORTED), (
        "build_jobs emits a non-pool type", types - set(kernel.POOL_SUPPORTED))


def test_channel_specs_rejects_non_pool_accepts_pool():
    """Coverage: channel_specs refuses a non-pool type (smt-obligation stays on
    the direct check() path) and yields a non-empty spec list for every pool
    type."""
    try:
        kernel.channel_specs({"kind": "logic", "files": {}},
                             {"type": "smt-obligation", "smtlib": "(check-sat)"})
        assert False, "channel_specs accepted a non-pool type"
    except ValueError:
        pass
    fx = _fixtures()
    for ctype in kernel.POOL_SUPPORTED:
        artifact, contract = fx[ctype]
        kind, specs = kernel.channel_specs(artifact, contract)
        assert kind and specs, (ctype, "channel_specs returned nothing")


if __name__ == "__main__":
    for _ctype in kernel.POOL_SUPPORTED:         # the parity tripwire, per type
        _assert_parity(_ctype)
        print("PASS", _ctype)
    for _name, _fn in sorted(globals().items()):  # the coverage assertions
        if _name.startswith("test_") and _name != "test_channel_parity":
            _fn()
            print("PASS", _name)
    print("channel parity holds for all POOL_SUPPORTED types")

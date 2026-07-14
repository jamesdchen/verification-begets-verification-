#!/usr/bin/env python3
"""P1.5 monitor-factory invariants, runnable under pytest AND as a bare script
(`python3 tests/test_monitor_gen.py` -> PASS lines, exit 0).

Three properties pin generators.monitor_gen:

  1. DETERMINISM -- building the SAME monitor under different PYTHONHASHSEED (0
     and 1, in subprocesses) yields BYTE-IDENTICAL monitor.py.  pythomata state
     numbering varies with the seed (proven); canonicalization must erase it.
  2. SEMANTICS  -- "eventually ship" pends on ''/[pay], accepts on [pay,ship],
     and an unknown symbol lands in a non-accepting sink; "ship within 2"
     rejects a trace that misses the deadline.
  3. CROSS-CHECK -- the baked table (monitor.py) and the independent live
     stepper (ref_stepper.py) agree on (accepting, pending) for EVERY trace up
     to length 4, plus unknown-symbol traces.  This is channel 2 of the future
     monitor-cert: a mutation in either implementation diverges here.
"""
from __future__ import annotations

import ast
import itertools
import os
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from generators import monitor_gen as mg

ALPHABET = ["pay", "ship", "close"]

# (label, kind, params) -- one per kind, over the shared alphabet.
MONITORS = [
    ("eventually-ship", "eventually", {"action": "ship"}),
    ("within-2-ship", "within", {"action": "ship", "steps": 2}),
    ("until-pay-ship", "until", {"pre": "pay", "post": "ship"}),
    ("before-pay-ship", "before", {"first": "pay", "second": "ship"}),
]


# ------------------------------------------------------------------- helpers
def _load(src: bytes) -> dict:
    """exec emitted module bytes into a fresh namespace."""
    ns: dict = {}
    exec(compile(src, "<emitted>", "exec"), ns)
    return ns


def _drive(mon: dict, trace) -> tuple:
    """Walk a trace through monitor.py from INITIAL; return (accepting, pending)
    of the final state."""
    st = mon["INITIAL"]
    for sym in trace:
        st = mon["step"](st, sym)
    return bool(mon["accepting"](st)), bool(mon["pending"](st))


def _all_traces(alphabet, maxlen):
    for n in range(maxlen + 1):
        for t in itertools.product(alphabet, repeat=n):
            yield list(t)


# --- DETERMINISM: rebuild under a fixed hashseed in a subprocess -------------
_SUBPROC = r"""
import sys
sys.path.insert(0, sys.argv[1])
from generators import monitor_gen as mg
SPECS = [
    ("eventually-ship", "eventually", {"action": "ship"}),
    ("within-2-ship", "within", {"action": "ship", "steps": 2}),
    ("until-pay-ship", "until", {"pre": "pay", "post": "ship"}),
    ("before-pay-ship", "before", {"first": "pay", "second": "ship"}),
]
ALPHA = ["pay", "ship", "close"]
out = {label: mg.build_monitor(k, p, ALPHA)["monitor.py"].hex()
       for label, k, p in SPECS}
print(repr(out))
"""


def _build_under_seed(seed: str) -> dict:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    env["PYTHONPATH"] = str(_ROOT)
    r = subprocess.run([sys.executable, "-c", _SUBPROC, str(_ROOT)],
                       capture_output=True, env=env)
    assert r.returncode == 0, ("subprocess (seed %s) failed: %s"
                               % (seed, r.stderr.decode()[-2000:]))
    return ast.literal_eval(r.stdout.decode().strip().splitlines()[-1])


def test_determinism_across_hashseeds():
    """monitor.py is byte-identical when built under PYTHONHASHSEED 0 vs 1."""
    a = _build_under_seed("0")
    b = _build_under_seed("1")
    assert set(a) == set(b) == {label for label, _k, _p in MONITORS}
    for label in a:
        assert a[label] == b[label], (
            "monitor.py NOT byte-identical across seeds for %r" % (label,))


# --- SEMANTICS ---------------------------------------------------------------
def test_semantics_eventually():
    """'eventually ship': ''/[pay] pending & not accepting; [pay,ship] accepting
    & not pending; unknown symbol -> non-accepting sink."""
    r = mg.build_monitor("eventually", {"action": "ship"}, ALPHABET)
    mon = _load(r["monitor.py"])
    assert _drive(mon, []) == (False, True), "empty trace should pend"
    assert _drive(mon, ["pay"]) == (False, True), "[pay] should pend"
    assert _drive(mon, ["pay", "ship"]) == (True, False), "[pay,ship] accepts"
    # unknown symbol -> dead sink, non-accepting
    sink = mon["step"](mon["INITIAL"], "no_such_action")
    assert sink == mon["SINK"], "unknown symbol did not route to SINK"
    assert mon["accepting"](sink) is False, "sink must be non-accepting"
    # sink is a trap on every alphabet action
    for a in ALPHABET:
        assert mon["step"](sink, a) == sink, "sink not a trap"


def test_semantics_within_deadline():
    """'ship within 2': [pay,ship] meets the deadline (accepting); [pay,close,
    ship] misses it (rejected -- non-accepting)."""
    r = mg.build_monitor("within", {"action": "ship", "steps": 2}, ALPHABET)
    mon = _load(r["monitor.py"])
    assert r["meta"]["formula"] == "act_ship | X(act_ship)"
    assert _drive(mon, ["ship"]) == (True, False), "[ship] within 2"
    assert _drive(mon, ["pay", "ship"]) == (True, False), "[pay,ship] within 2"
    acc, _pend = _drive(mon, ["pay", "close", "ship"])
    assert acc is False, "[pay,close,ship] MISSED deadline, must be rejected"


def test_semantics_before_accepts_yet_pends():
    """'pay before ship' accepts the empty trace yet still PENDS (a ship could
    still violate) -- the case where pending != not accepting."""
    r = mg.build_monitor("before", {"first": "pay", "second": "ship"}, ALPHABET)
    mon = _load(r["monitor.py"])
    assert _drive(mon, []) == (True, True), "before: empty accepts but pends"
    assert _drive(mon, ["pay"]) == (True, False), "before: pay locks safety"
    assert _drive(mon, ["ship"]) == (False, True), "before: ship-first violates"


# --- CROSS-CHECK: baked table vs independent live stepper --------------------
def test_crosscheck_table_vs_ref():
    """monitor.py and ref_stepper.py agree on (accepting, pending) for every
    trace up to length 4, plus unknown-symbol traces."""
    extra = [["nope"], ["pay", "nope"], ["nope", "ship"]]   # unknown symbols
    for label, kind, params in MONITORS:
        r = mg.build_monitor(kind, params, ALPHABET)
        mon = _load(r["monitor.py"])
        ref = _load(r["ref_stepper.py"])
        for trace in list(_all_traces(ALPHABET, 4)) + extra:
            m = _drive(mon, trace)
            f = (bool(ref["accepting"](trace)), bool(ref["pending"](trace)))
            assert m == f, ("table vs ref divergence", label, trace,
                            "monitor", m, "ref", f)


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_"):
            _fn()
            print("PASS", _name)
    print("monitor-factory invariants hold "
          "(determinism + semantics + table/ref cross-check)")

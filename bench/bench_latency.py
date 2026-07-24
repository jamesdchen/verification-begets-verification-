#!/usr/bin/env python3
"""Latency of the service-certification path -- the three levers, measured.

  1. certificate cache: unchanged layers never re-run (instant re-certification,
     e.g. across the synthesis loop's refinement rounds);
  2. cross-layer parallelism: the independent layers are checked concurrently in
     separate PROCESSES (the z3/cvc5 bindings are not thread-safe -- their
     process-global context is corrupted by concurrent use AND by cross-thread
     finalization -- so layers fan out across processes, not threads);
  3. intra-contract channel parallelism: a single contract's z3-free channels
     (pure sandbox / Dafny) overlap; this is auto-disabled inside the process
     pool so process x thread nesting never oversubscribes the cores.

Startup was measured NOT to be the bottleneck: a fresh sandbox + interpreter is
~0.03s and importing Hypothesis ~0.3s; the real per-channel cost is the
property-based *testing* (~2s), which the parallelism overlaps and the cache
elides.  Run: python3 bench_latency.py
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 bench/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import pathlib
import tempfile
import time

import common  # noqa: F401  (import side effects: ensure dirs)
from library import Registry
from run import service

SPECS = ["specs/services/orders.json", "specs/services/tickets.json"]


def _time(fn):
    t0 = time.time()
    r = fn()
    return time.time() - t0, r


def main():
    for spec_path in SPECS:
        spec = pathlib.Path(spec_path).read_text()
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tf:
            reg = Registry(db_path=tf.name)
            hooks = dict(event_sink=reg.log_event, cache_get=reg.cache_get,
                         cache_put=reg.cache_put, write_output=False)
            cold, r1 = _time(lambda: service.certify_service(spec, **hooks))
            warm, r2 = _time(lambda: service.certify_service(spec, **hooks))
        # fully-serial baseline (layers serial, channels serial) = the original
        os.environ["CGB_KERNEL_SERIAL"] = "1"
        try:
            base, r0 = _time(lambda: service.certify_service(
                spec, write_output=False, max_workers=1))
        finally:
            os.environ.pop("CGB_KERNEL_SERIAL", None)
        name = pathlib.Path(spec_path).stem
        print(f"{name:9s} layers={len(r1.layers):2d}  "
              f"serial={base:5.2f}s  parallel(cold)={cold:5.2f}s  "
              f"cached(warm)={warm:5.2f}s  "
              f"speedup={base / cold:4.1f}x  ok={r1.ok and r2.ok and r0.ok}")


if __name__ == "__main__":
    main()

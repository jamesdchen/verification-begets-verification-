#!/usr/bin/env python3
"""regen-DAG shim: assemble the hammer batch from the committed proof queue.

Thin exec of ``bench/bench_hammer.py assemble`` so the batch joins
``tools/regen_downstream.py`` under the uniform tools/<name>.py step
convention (chain: proof_queue -> hammer_batch, strictly after frontier).
Being IN the DAG is load-bearing: the queue/batch reproduction teeth
byte-compare committed artifacts against a fresh derivation, and every
corpus cycle moves the inputs -- outside the DAG they red the gate one
merge later (measured on PR #39: the first live cycle merge after the
queue landed did exactly that).
"""
import subprocess
import sys

sys.exit(subprocess.run(
    [sys.executable, "bench/bench_hammer.py", "assemble",
     "--queue", "results/proof_queue.json"]).returncode)

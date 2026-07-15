"""Metrics experiment driver (milestones 5 and 8).

For each steering policy (and each --corpus setting), start from a FRESH
registry, seed the opening library through the kernel, then run build-loop
iterations until coverage saturates or a cap is hit -- snapshotting reach,
cost, tier mix, description length, and corpus effectiveness after every
admission.  Emits one CSV per configuration and a combined reach-vs-cost
plot with one curve per configuration.

By default the experiment measures against the ksy families of the backlog
(the ABNF tree-sitter chain is exercised in the milestone-4 demo, which is
slower and separate); pass include_abnf=True to include it.
"""
from __future__ import annotations

import pathlib

import common
from library import Registry
from buildloop import admission, loop
from buildloop.loop import backlog_index
from metrics import snapshot, export_csv


def _seed(reg, backlog, use_corpus):
    cand = {
        "name": "kaitai-fixed-uint-be", "spec_language": "ksy",
        "output_language": "python-codec",
        "spec_grammar": {"atoms": ["endian:be", "uint:1", "uint:2",
                                   "uint:4", "uint:8"]},
        "emit_entrypoint": {"kind": "ksc-python-rw"},
        "contract": {"type": "codec-roundtrip"},
        "provenance": {"author": "human-seed",
                       "parents": ["kaitai-struct-compiler"], "depth": 1},
    }
    admission.admit(reg, cand, backlog, use_corpus=use_corpus)


def run_config(db_path, csv_path, *, policy, use_corpus, backlog,
               max_iterations=14, model=None):
    if pathlib.Path(db_path).exists():
        pathlib.Path(db_path).unlink()
    reg = Registry(db_path)
    _seed(reg, backlog, use_corpus)
    snapshot(reg, backlog, event="seed", policy=policy, corpus=use_corpus)
    admitted = 0
    for i in range(max_iterations):
        res = loop.run_iteration(reg, backlog, policy=policy,
                                 use_corpus=use_corpus, model=model)
        if res["status"] == "converged":
            break
        if res["status"] == "admitted":
            admitted += 1
            snapshot(reg, backlog, event=f"admission:{res['generator']}",
                     policy=policy, corpus=use_corpus)
        else:
            # exhausted refinement on this miss; snapshot cost and continue
            snapshot(reg, backlog, event=f"miss-exhausted",
                     policy=policy, corpus=use_corpus)
    export_csv(reg, csv_path)
    return {"policy": policy, "corpus": use_corpus, "admitted": admitted,
            "csv": csv_path}


def ksy_backlog():
    bl = backlog_index(common.REPO_ROOT / "specs" / "backlog")
    return [s for s in bl if s["language"] == "ksy"]

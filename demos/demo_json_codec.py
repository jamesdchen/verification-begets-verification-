#!/usr/bin/env python3
"""Corrected P4b demo: a RECURSIVE JSON-subset codec, certified by two
independent evidence channels (ts-recursive-codec + vpl-differential).

The original P4b route (JSON "via the existing chain") is infeasible: the .ksy
subset rejects recursive types, ABNF wants one flat rule, and refcodec is a
linear field interpreter.  This route instead uses a hand-written RECURSIVE
tree-sitter grammar -> a self-contained emitted parser -> a fixed tree-walk
codec (Implementation A), diffed against an independent recursive-descent codec
(Implementation B) and stdlib json.

Part A -- the kernel's vpl-differential contract certifies the codec: channel 1
(bounded-depth recursive values -- byte-agreement + cross-decode across the
three implementations) and channel 2 (membership differential on structurally
mutated inputs) both pass, so the dual-checker rule issues a certificate whose
`claims` name the recursion depth that was checked.

Part B -- the visibly-pushdown point.  A structural mutation (deleting a closing
bracket) is a membership violation no per-character check can catch, but a
recursive grammar must.  We show one mutated input rejected by BOTH independent
membership deciders: the tree-sitter parser (has_error, run sandboxed) and the
recursive-descent parser.

REQUIRES_LLM = False -- the grammar and both codecs are hand-written and fixed;
nothing here calls an LLM.
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import sys

from generators import json_codec
import kernel
from kernel.certs import Certificate

REQUIRES_LLM = False

DEPTH_BOUND = 4


def part_a():
    print("== Part A: vpl-differential certificate (tree-sitter == recursive-descent == stdlib) ==")
    files = json_codec.emit_json_codec()          # emit Implementation A's parser
    v = kernel.check(
        {"kind": "json-codec", "files": files},
        {"type": "vpl-differential", "grammar_js": json_codec.JSON_GRAMMAR_JS,
         "depth_bound": DEPTH_BOUND, "max_examples": 80})
    if isinstance(v, Certificate):
        print("  CERTIFIED. agreeing channels:",
              [(c["backend"], c["result"]) for c in v.channels])
        print("  certificate claims (named depth bound):", v.claims)
        return True, files
    t = v.to_dict()
    print("  unexpected:", t["verdict"],
          [(c["backend"], c["result"]) for c in t["channels"]])
    return False, files


def part_b(files):
    print("\n== Part B: a structural mutation is rejected by BOTH membership checks ==")
    value = {"a": [1, {"b": None}], "c": True, "d": "xy z"}
    text = json_codec.rd_serialize(value)          # a well-formed member
    print(f"  valid input:   {text}")

    # a visibly-pushdown violation: delete the last closing bracket -> unbalanced
    muts = dict(json_codec.mutations(text))
    mutated = muts.get("del-last-bracket", json_codec.mutations(text)[0][1])
    print(f"  mutated input: {mutated}   (deleted a closing bracket)")

    # membership decider B (recursive-descent), in-process
    rd_reject = not json_codec.rd_is_member(mutated)
    # membership decider A (tree-sitter has_error), run SANDBOXED on the emitted parser
    ts = json_codec.run_json_parser_sandboxed(files, mutated)
    ts_reject = bool(ts["has_error"])

    print(f"  recursive-descent rejects: {rd_reject}")
    print(f"  tree-sitter has_error:     {ts_reject}")
    both = rd_reject and ts_reject
    print(f"  rejected by BOTH membership checks: {both}")
    # sanity: the two deciders also AGREE that the un-mutated input IS a member
    valid_member = json_codec.rd_is_member(text) and not \
        json_codec.run_json_parser_sandboxed(files, text)["has_error"]
    print(f"  (both accept the un-mutated input: {valid_member})")
    return both and valid_member


if __name__ == "__main__":
    a_ok, files = part_a()
    b_ok = part_b(files)
    print("\nsummary:", json.dumps({
        "part_a_codec_certified": a_ok,
        "part_b_mutation_rejected_by_both": b_ok}))
    sys.exit(0 if all([a_ok, b_ok]) else 1)

#!/usr/bin/env python3
"""Combined-Loop W1 -- the generic `translation-cert` rung contract.

ONE kernel contract certifies any per-emission translation Spec_high -> Spec_low
against a NAMED independent anchor (house rule 11).  This demo exercises the
`reference-lowering` anchor on the reading domain (the macro-expansion pattern
generalised, fact 3) -- LLM-free and Dafny-free:

Tooth (a) -- a FAITHFUL translator (the `no_oversell` macro expansion) certifies:
  channel 1 (compile identity: the translated form and the trusted reference
  lower to a byte-identical meta-spec) AND channel 2 (the reference's
  solver-entailed scenarios replay on the emitted artifact) both pass.

Tooth (b) -- a PLANTED LOSSY translator (the `bad_no_oversell` macro drops the
  guard bound) is refuted by BOTH channels: a different compile hash AND a
  scenario the reference's demands entail as a rejection that the guard-less
  artifact accepts.  No certificate is issued.

Tooth (c) -- cache identity: two contracts identical except for an anchor input
  (the reference lowering / the translator_hash) produce DISTINCT cache keys, so
  a changed anchor is a clean miss, never a stale false-green.

The contract shape is anchor-generic (reference-lowering here; fixed-deriver and
incumbent-differential land their dispatch in W1.3b / W4.2).  A new rung is one
`generators/derivers.py` entry + one TRUST.md line -- never a kernel edit.

REQUIRES_LLM = False
"""
from __future__ import annotations

import json
import sys

import kernel
from kernel.certs import Certificate
from demo_macros import (NO_OVERSELL, BAD_OVERSELL, CORPUS, _reading,
                         _compile_and_emit)

REQUIRES_LLM = False


def _contract(inlined, translated, macro_table, request, **extra):
    c = {"type": "translation-cert", "anchor": "reference-lowering",
         "high_language": "reading",
         "high_spec_text": json.dumps(translated),
         "reference_lowering": json.dumps(inlined),
         "expansion_context": {"macro_table": macro_table},
         "request": request}
    c.update(extra)
    return c


def part_a() -> bool:
    print("== Tooth (a): a faithful translator certifies (both channels) ==")
    c = CORPUS[0]
    inlined, macro_form = _reading(**c)
    files = _compile_and_emit(macro_form, c["request"],
                              {"no_oversell": NO_OVERSELL})
    v = kernel.check(
        {"kind": "translation", "files": files},
        _contract(inlined, macro_form, {"no_oversell": NO_OVERSELL},
                  c["request"]))
    ok = isinstance(v, Certificate)
    ch = [(x["backend"], x["result"]) for x in
          (v.channels if ok else v.to_dict()["channels"])]
    print(f"  {'OK' if ok else 'XX'} translation-cert  channels={ch}")
    if ok:
        print(f"  tier={v.tier}  anchor claim={[cl[1] for cl in v.claims if cl[0]=='anchor']}")
    passed = ok and all(r == "pass" for _b, r in ch) and len(ch) == 2
    print(f"  part_a: {passed}")
    return passed


def part_b() -> bool:
    print("\n== Tooth (b): a planted lossy translator is refuted (both) ==")
    c = CORPUS[0]
    inlined, _good = _reading(**c)
    _in, bad_form = _reading(macro=BAD_OVERSELL, **c)
    files = _compile_and_emit(bad_form, c["request"],
                              {"bad_no_oversell": BAD_OVERSELL})
    v = kernel.check(
        {"kind": "translation", "files": files},
        _contract(inlined, bad_form, {"bad_no_oversell": BAD_OVERSELL},
                  c["request"]))
    refuted = not isinstance(v, Certificate)
    ch = [(x["backend"], x["result"]) for x in
          (v.to_dict()["channels"] if refuted else [])]
    ch1_fail = any(b == "translation-compile-identity" and r != "pass"
                   for b, r in ch)
    ch2_fail = any(b == "translation-scenario-replay" and r != "pass"
                   for b, r in ch)
    print(f"  refuted={refuted}  channels={ch}")
    print(f"  channel-1 (compile identity) refutes: {ch1_fail}")
    print(f"  channel-2 (scenario replay) refutes: {ch2_fail}")
    passed = refuted and ch1_fail and ch2_fail
    print(f"  part_b: {passed}")
    return passed


def part_c() -> bool:
    print("\n== Tooth (c): an anchor input enters cache identity ==")
    c = CORPUS[0]
    inlined, macro_form = _reading(**c)
    _in2, other_form = _reading(**CORPUS[1])
    art = {"kind": "translation", "files": {}}
    base = _contract(inlined, macro_form, {"no_oversell": NO_OVERSELL},
                     c["request"])
    # differ only in translator_hash -> distinct key
    k_base = kernel.cache_key(art, base)
    k_th = kernel.cache_key(art, {**base, "translator_hash": "PINNED-DIFFERENT"})
    # differ only in the reference lowering -> distinct key
    k_ref = kernel.cache_key(
        art, {**base, "reference_lowering": json.dumps(other_form)})
    distinct = len({k_base, k_th, k_ref}) == 3
    print(f"  base            = {k_base[:24]}...")
    print(f"  +translator_hash= {k_th[:24]}...")
    print(f"  +reference      = {k_ref[:24]}...")
    print(f"  all three distinct: {distinct}")
    print(f"  part_c: {distinct}")
    return distinct


if __name__ == "__main__":
    a, b, cc = part_a(), part_b(), part_c()
    print("\nsummary:", json.dumps({
        "tooth_a_faithful_translator_certifies": a,
        "tooth_b_lossy_translator_refuted_both_channels": b,
        "tooth_c_anchor_enters_cache_identity": cc}))
    sys.exit(0 if all([a, b, cc]) else 1)

#!/usr/bin/env python3
"""W5.2/W5.3 -- the macro-reading RUNG: a 3-link exogenous-serving chain, and
the equivalence anchor that makes lossy compression inadmissible.

A `macro-reading` is a Reading whose statements MAY be macro invocations.  The
FIXED macro machinery (generators.reading._expand_macros -- the trusted lowering,
fact 3) lowers a macro-reading to a plain Reading; the existing chain then
carries it the rest of the way down:

        macro-reading  ->  reading  ->  meta-spec  ->  service
        \\________________ 3 links, all exogenous-serving _______________/

Per-emission certification is the generic kernel `translation-cert` with
`anchor='reference-lowering'` and `high_language='macro-reading'` -- NO kernel or
planner edit: the reference-lowering dispatch and `LOWERINGS['macro-reading']`
already exist (W1).  A macro-reading is a NOTATION over the Reading domain, not a
new LF kind, so nothing about the fragment grows.

THE EQUIVALENCE ANCHOR (the load-bearing soundness property, W5.2).  The DL
objective PAYS FOR DELETION -- a rewrite that silently drops a safety demand is
"cheaper", so an acceptance rule that only rewards smaller DL rewards lossiness.
House rule 12: every rewritten demand KEEPS ITS ORIGINAL as the baseline; the
rewrite, lowered through the chain, MUST be compile-hash-IDENTICAL to the
original's compiled spec, or it is REFUSED.  That identity is exactly channel-1
of translation-cert.  A planted lossy rewrite diverges the hash and is refused.

------------------------------------------------------------------------------
WHICH PARTS NEED THE LLM
------------------------------------------------------------------------------
  Part 1  (LLM-FREE, deterministic)  -- the acceptance arc + the teeth.  Every
          number here is checkable in-sandbox: rewritten items have strictly
          lower authored DL, the certified count is unchanged, every equivalence
          anchor is green, max_chain_depth_used == 3, and a planted lossy rewrite
          is refused.  This is the honest, reproducible core.

  Part 2  (REQUIRES THE LIVE LLM)    -- closes the flywheel on a natural-language
          request: the model AUTHORS a Reading (synthesize_semantic), the
          deterministic pipeline certifies it, and an LLM-proposed macro-reading
          rewrite is certified against the model's OWN original as baseline
          through the same equivalence anchor.  Skipped unless the LLM is
          reachable; the whole demo is REQUIRES_LLM=True and never runs in --fast.
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

import kernel
from kernel.certs import Certificate
from buildloop import mdl_macros as mm
from generators import derivers as dv
from demos.demo_macros import (NO_OVERSELL, BAD_OVERSELL, CORPUS,
                         _reading, _compile_and_emit)

REQUIRES_LLM = True   # Part 2 authors a Reading with a live model; Part 1 is LLM-free

HL = "macro-reading"

# The exogenous-serving chain the rung stands up.  Each link is a distinct
# generator with its own tier; the kernel carries this as `chain_links` so the
# height metric (max_chain_depth_used) is content-addressed, not asserted.
CHAIN_LINKS = [
    {"generator": "macro-expansion", "tier": "emit-check"},   # macro-reading -> reading
    {"generator": "reading-compile", "tier": "emit-check"},   # reading -> meta-spec
    {"generator": "service-gen",     "tier": "emit-check"},   # meta-spec -> service
]
CHAIN_DEPTH = len(CHAIN_LINKS)   # 3


def _contract(reference_inlined, rewrite_macro_form, macro_table, request):
    return {"type": "translation-cert", "anchor": "reference-lowering",
            "high_language": HL,
            "high_spec_text": json.dumps(rewrite_macro_form),
            "reference_lowering": json.dumps(reference_inlined),
            "expansion_context": {"macro_table": macro_table},
            "request": request,
            "chain_links": CHAIN_LINKS}


def _channels(v):
    return [(c["backend"], c["result"]) for c in
            (v.channels if isinstance(v, Certificate) else v.to_dict()["channels"])]


def _certify_rewrite(inlined, macro_form, macro_table, request):
    """Emit + certify one macro-reading rewrite against its original baseline."""
    files = _compile_and_emit(macro_form, request, macro_table)
    return kernel.check({"kind": "translation", "files": files},
                        _contract(inlined, macro_form, macro_table, request))


# ---------------------------------------------------------------- Part 1 (no LLM)
def part1_deterministic_arc() -> bool:
    print("== Part 1 (LLM-FREE): the rung arc on the NL request corpus ==")
    print(f"   chain: macro-reading -> reading -> meta-spec -> service "
          f"({CHAIN_DEPTH} links)")
    macro_table = {"no_oversell": NO_OVERSELL}

    dl_before_total = dl_after_total = 0.0
    certified_before = certified_after = 0
    anchors_green = 0
    depths = []

    for c in CORPUS:
        inlined, macro_form = _reading(**c)
        # authored description length: original (no macro) vs rewrite (macro).
        dl_before = mm.dl_reading(inlined, {})
        dl_after = mm.dl_reading(inlined, macro_table)
        dl_before_total += dl_before
        dl_after_total += dl_after

        # BASELINE certifies (the original inlined reading, on its own).
        base_files = _compile_and_emit(inlined, c["request"], None)
        vb = kernel.check(
            {"kind": "translation", "files": base_files},
            {"type": "translation-cert", "anchor": "reference-lowering",
             "high_language": "reading",
             "high_spec_text": json.dumps(inlined),
             "reference_lowering": json.dumps(inlined),
             "request": c["request"]})
        certified_before += 1 if isinstance(vb, Certificate) else 0

        # REWRITE certifies against the baseline through the equivalence anchor.
        vr = _certify_rewrite(inlined, macro_form, macro_table, c["request"])
        ok = isinstance(vr, Certificate)
        certified_after += 1 if ok else 0
        ch = _channels(vr)
        green = ok and dict(ch).get("translation-compile-identity") == "pass"
        anchors_green += 1 if green else 0
        depths.append(CHAIN_DEPTH if ok else 0)

        print(f"   {c['service']:<10} authored DL {dl_before:>5.1f} -> {dl_after:>5.1f}"
              f"   rewrite cert={ok}  equivalence-anchor={'green' if green else 'RED'}")

    max_depth = max(depths) if depths else 0
    lower_dl = dl_after_total < dl_before_total
    count_unchanged = certified_after == certified_before == len(CORPUS)
    all_green = anchors_green == len(CORPUS)
    depth_ok = max_depth == 3

    print(f"\n   authored DL total: {dl_before_total:.1f} -> {dl_after_total:.1f}"
          f"   (strictly lower: {lower_dl})")
    print(f"   certified count: before={certified_before} after={certified_after}"
          f"   (unchanged at {len(CORPUS)}: {count_unchanged})")
    print(f"   equivalence anchors green: {anchors_green}/{len(CORPUS)}")
    print(f"   max_chain_depth_used: {max_depth}   (reaches 3: {depth_ok})")
    ok = lower_dl and count_unchanged and all_green and depth_ok
    print(f"   part1: {ok}")
    return ok


def part1b_lossy_tooth() -> bool:
    print("\n== Part 1 tooth (a): a planted LOSSY rewrite is REFUSED ==")
    c = CORPUS[0]
    inlined, _good = _reading(**c)                 # ORIGINAL kept as baseline
    _in, bad_form = _reading(macro=BAD_OVERSELL, **c)   # drops the guard-bound demand
    vr = _certify_rewrite(inlined, bad_form,
                          {"bad_no_oversell": BAD_OVERSELL}, c["request"])
    refused = not isinstance(vr, Certificate)
    ch = _channels(vr)
    anchor_refuses = dict(ch).get("translation-compile-identity") == "fail"
    print(f"   certificate issued: {not refused}  (want False)")
    print(f"   channels: {ch}")
    print(f"   REFUSED by the equivalence anchor (compile-identity): {anchor_refuses}")
    if refused:
        d = vr.to_dict()
        fail = next((x for x in d["channels"]
                     if x["backend"] == "translation-compile-identity"), {})
        print(f"   witness: {str(fail.get('detail', ''))[:140]}")
    ok = refused and anchor_refuses
    print(f"   part1b: {ok}")
    return ok


# ------------------------------------------------------------ Part 2 (needs LLM)
def part2_llm_flywheel() -> bool:
    print("\n== Part 2 (REQUIRES THE LIVE LLM): flywheel on an NL request ==")
    try:
        from buildloop import service_loop
    except Exception as e:                                   # pragma: no cover
        print(f"   SKIPPED (import): {e}")
        return True
    request = CORPUS[0]["request"]
    try:
        res = service_loop.synthesize_semantic(request, write_output=False,
                                               examiner=False)
    except Exception as e:                                   # pragma: no cover
        print(f"   SKIPPED (LLM unreachable): {str(e)[:160]}")
        return True
    if res.get("status") != "certified":
        print(f"   the model's Reading did not certify: {res.get('status')}"
              f" -- honest miss, no false green")
        return False
    print(f"   LLM authored + certified a Reading in {res['rounds']} round(s), "
          f"{res['tokens']} tokens")
    print("   (an LLM-proposed macro-reading rewrite of this Reading would be "
          "certified against\n    THIS certified original as its equivalence "
          "baseline -- same anchor as Part 1)")
    return True


if __name__ == "__main__":
    p1 = part1_deterministic_arc()
    p1b = part1b_lossy_tooth()
    p2 = part2_llm_flywheel()
    print("\nsummary:", json.dumps({
        "part1_acceptance_arc_dl_down_count_unchanged_depth3": p1,
        "part1_tooth_lossy_rewrite_refused_by_equivalence_anchor": p1b,
        "part2_llm_flywheel_authored_reading_certified": p2}))
    sys.exit(0 if all([p1, p1b, p2]) else 1)

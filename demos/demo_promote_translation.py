#!/usr/bin/env python3
"""Combined-Loop W5.1 -- promoting a TRANSLATOR (universal-translation).

The second pinned Combined-Loop contract type.  A translator is promoted by a
bounded-exhaustive check over N sampled inputs (two genuinely different
aggregate channels: compile-identity vs the trusted reference lowering, and
solver-entailed-scenario replay through the real pipeline).  Because we have NO
unbounded proof for the reading compiler, the honest outcome is
`complete-to-size(N)` -- a real, hash-bound BOUNDED adjudication that does NOT
flip the tier (the promotion is honestly REFUSED, keeping emit-check duty).  A
translator with even ONE unsound sample is refused outright.  Mislabelling a
bounded result as `universal` never happens.

REQUIRES_LLM = False -- every reading/macro here is hand-written (Dafny-free).
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
import tempfile

import kernel
from kernel.certs import Certificate
from library import Registry
from buildloop import promote as promote_mod
from demos.demo_macros import (NO_OVERSELL, BAD_OVERSELL, CORPUS, _reading,
                         _compile_and_emit)

REQUIRES_LLM = False


def _sample(c, macro):
    inlined, macro_form = _reading(macro=macro, **c) if macro else _reading(**c)
    name = (macro or NO_OVERSELL)["name"]
    files = _compile_and_emit(macro_form, c["request"], {name: macro or NO_OVERSELL})
    return {"high_spec_text": json.dumps(macro_form),
            "reference_lowering": json.dumps(inlined),
            "expansion_context": {"macro_table": {name: macro or NO_OVERSELL}},
            "request": c["request"], "files": files}


def _register_translator(reg):
    return reg.register(
        name="macro-reading-lowering", tier="emit-check",
        spec_language="macro-reading", output_language="reading",
        spec_grammar={"atoms": ["macro"]},
        emit_entrypoint={"kind": "macro-expand"}, contract={},
        provenance={"note": "the fixed macro-reading -> reading lowering"},
        kind="translator")


def part_a() -> bool:
    print("== Tooth (a): honest translator -> complete-to-size(N), tier NOT flipped ==")
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    gh = _register_translator(reg)
    samples = [_sample(c, None) for c in CORPUS]        # 3 faithful samples
    res = promote_mod.promote(reg, gh, translator_samples=samples)
    tier_after = reg.get(gh)["tier"]
    ok = (res["status"] == "refused-bounded"
          and res["tier"] == "complete-to-size(N)"
          and tier_after == "emit-check")              # NOT flipped to universal
    print(f"  promotion status={res['status']} cert_tier={res.get('tier')} "
          f"channels={[c['backend'] for c in res.get('channels', [])]}")
    print(f"  translator tier after = {tier_after} (honest bounded refusal)")
    print(f"  part_a: {ok}")
    return ok


def part_b() -> bool:
    print("\n== Tooth (b): an UNSOUND translator sample refuses the promotion ==")
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    gh = _register_translator(reg)
    # two faithful samples + one PLANTED LOSSY sample (drops the guard bound):
    samples = [_sample(CORPUS[0], None), _sample(CORPUS[1], None),
               _sample(CORPUS[2], BAD_OVERSELL)]
    res = promote_mod.promote(reg, gh, translator_samples=samples)
    tier_after = reg.get(gh)["tier"]
    ok = (res["status"] == "rejected" and tier_after == "emit-check")
    v = res.get("transcript", {})
    print(f"  promotion status={res['status']} verdict={v.get('verdict')}")
    print(f"  translator tier after = {tier_after} (unsound -> refused)")
    print(f"  part_b: {ok}")
    return ok


def part_c() -> bool:
    print("\n== Tooth (c): the bounded certificate is real (kept as evidence) ==")
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    gh = _register_translator(reg)
    samples = [_sample(c, None) for c in CORPUS]
    promote_mod.promote(reg, gh, translator_samples=samples)
    certs = reg.certs_for(gh)
    ut = [c for c in certs if c["kind"] == "promotion-translation"]
    ok = (len(ut) == 1 and ut[0]["tier"] == "complete-to-size(N)")
    print(f"  stored certs for translator: {[c['kind'] for c in certs]}")
    print(f"  universal-translation cert tier: {ut[0]['tier'] if ut else None}")
    print(f"  part_c: {ok}")
    return ok


if __name__ == "__main__":
    a, b, c = part_a(), part_b(), part_c()
    print("\nsummary:", json.dumps({
        "tooth_a_honest_translator_bounded_not_flipped": a,
        "tooth_b_unsound_translator_refused": b,
        "tooth_c_bounded_certificate_is_real_evidence": c}))
    sys.exit(0 if all([a, b, c]) else 1)

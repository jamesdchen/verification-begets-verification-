"""W5.2 -- the macro-reading rung: teeth (LLM-free, Dafny-free, in-sandbox).

A `macro-reading` is a Reading whose statements MAY be macro invocations; the
fixed macro machinery (generators.reading._expand_macros) lowers it to a plain
Reading, which the existing chain then carries down `reading -> meta-spec ->
service`.  Per-emission certification is the generic kernel `translation-cert`
with `anchor='reference-lowering'` and `high_language='macro-reading'` -- NO
kernel or planner edit is involved: the reference-lowering dispatch and the
`LOWERINGS['macro-reading']` registry entry already exist (W1).  These tests
only demonstrate the rung and its load-bearing soundness property.

The EQUIVALENCE ANCHOR (the reason a lossy rewrite cannot be admitted): every
rewritten demand keeps its ORIGINAL as the baseline `reference_lowering`; the
rewrite, lowered through the fixed chain, must be compile-hash-IDENTICAL to the
baseline's compiled spec, or the certificate is refused.  That identity IS
channel-1 of translation-cert.  Because the DL objective pays for deletion, this
anchor is the only thing standing between "cheaper" and "lossy".

  (a) a FAITHFUL macro-reading rewrite (the demo_macros `no_oversell` macro over
      one CORPUS request) certifies -- both channels pass.
  (b) a PLANTED LOSSY rewrite (the `bad_no_oversell` macro drops the guard-bound
      demand) is REFUSED by the equivalence anchor -- the compile-identity
      channel fails and NO certificate is issued.

Reuses demo_macros._reading / _compile_and_emit and kernel.check verbatim, so the
tooth exercises the real emission path, not a bespoke stub.
"""
import json

import kernel
from kernel.certs import Certificate
from buildloop import mdl_macros as mm
from generators import derivers as dv
from demos.demo_macros import (NO_OVERSELL, BAD_OVERSELL, CORPUS,
                         _reading, _compile_and_emit)

HL = "macro-reading"          # the rung's high language (a NOTATION over Reading)


def _contract(reference_inlined, rewrite_macro_form, macro_table, request):
    """A per-emission translation-cert for the macro-reading rung.  The baseline
    ORIGINAL is the reference_lowering (house rule 12: every rewrite keeps its
    original); the macro-form rewrite is the high spec under test."""
    return {"type": "translation-cert", "anchor": "reference-lowering",
            "high_language": HL,
            "high_spec_text": json.dumps(rewrite_macro_form),
            "reference_lowering": json.dumps(reference_inlined),
            "expansion_context": {"macro_table": macro_table},
            "request": request}


def _channels(v):
    return [(c["backend"], c["result"]) for c in
            (v.channels if isinstance(v, Certificate) else v.to_dict()["channels"])]


def test_faithful_macro_reading_rewrite_certifies():
    """(a) A faithful macro-reading rewrite certifies via translation-cert with
    BOTH channels green: channel 1 = the rewrite and its original baseline lower
    to a byte-identical meta-spec (the equivalence anchor); channel 2 = the
    baseline's solver-entailed scenarios replay on the emitted artifact."""
    c = CORPUS[0]
    inlined, macro_form = _reading(**c)
    files = _compile_and_emit(macro_form, c["request"],
                              {"no_oversell": NO_OVERSELL})
    v = kernel.check({"kind": "translation", "files": files},
                     _contract(inlined, macro_form,
                               {"no_oversell": NO_OVERSELL}, c["request"]))
    assert isinstance(v, Certificate), _channels(v)
    ch = _channels(v)
    assert len(ch) == 2, ch
    assert all(r == "pass" for _b, r in ch), ch
    # it is exactly the emit-check rung on the macro-reading high language.
    assert v.tier == "emit-check", v.tier
    claims = dict(v.claims)
    assert claims.get("anchor") == "reference-lowering", v.claims


def test_equivalence_anchor_is_compile_identity_for_faithful_rewrite():
    """The equivalence anchor spelled out: the faithful rewrite, lowered through
    the fixed chain, is compile-hash-IDENTICAL to the original baseline's
    compiled spec.  This is what channel-1 certifies."""
    c = CORPUS[0]
    inlined, macro_form = _reading(**c)
    ctx = {"macro_table": {"no_oversell": NO_OVERSELL}, "request": c["request"]}
    low = dv.LOWERINGS[HL]["lower"]
    rewrite_spec = low(json.dumps(macro_form), ctx)["spec"]
    baseline_spec = low(json.dumps(inlined), ctx)["spec"]
    assert rewrite_spec == baseline_spec, "faithful rewrite must preserve the compiled spec"


def test_lossy_macro_reading_rewrite_is_refused_by_equivalence_anchor():
    """(b) A planted LOSSY rewrite -- the `bad_no_oversell` macro DROPS the
    guard-bound demand -- diverges the compile hash, so the equivalence anchor
    (channel 1, compile identity) REFUSES it and NO certificate is issued.  The
    DL objective would happily pay for that deletion; this anchor is the only
    thing that refuses it."""
    c = CORPUS[0]
    inlined, _good = _reading(**c)                 # the ORIGINAL, kept as baseline
    _in, bad_form = _reading(macro=BAD_OVERSELL, **c)
    files = _compile_and_emit(bad_form, c["request"],
                              {"bad_no_oversell": BAD_OVERSELL})
    v = kernel.check({"kind": "translation", "files": files},
                     _contract(inlined, bad_form,
                               {"bad_no_oversell": BAD_OVERSELL}, c["request"]))
    # no certificate: the lossy rewrite is refused.
    assert not isinstance(v, Certificate), "a lossy rewrite MUST NOT certify"
    ch = _channels(v)
    # the REFUSING channel is the equivalence anchor: compile identity.
    ch1 = dict((b, r) for b, r in ch)
    assert ch1.get("translation-compile-identity") == "fail", ch
    # and the dropped safety statement really did change the compiled spec.
    ctx = {"macro_table": {"bad_no_oversell": BAD_OVERSELL}, "request": c["request"]}
    low = dv.LOWERINGS[HL]["lower"]
    assert low(json.dumps(bad_form), ctx)["spec"] != low(json.dumps(inlined), ctx)["spec"]


def test_faithful_rewrite_has_strictly_lower_authored_dl():
    """The economic reason to mint the rung (LLM-free slice of the acceptance
    property): with the macro available the authored description length of the
    demand drops strictly, while the equivalence anchor keeps what is certified
    identical -- cheaper notation, same proof."""
    c = CORPUS[0]
    inlined, _macro_form = _reading(**c)
    dl_baseline = mm.dl_reading(inlined, {})
    dl_rewritten = mm.dl_reading(inlined, {"no_oversell": NO_OVERSELL})
    assert dl_rewritten < dl_baseline, (dl_rewritten, dl_baseline)


def test_macro_reading_lowering_registered():
    """The rung is a NOTATION over the existing Reading domain: `macro-reading`
    reuses the SAME trusted lowering as `reading` (a macro is an abbreviation,
    not a new LF kind), so no new domain and no kernel edit were needed."""
    assert HL in dv.LOWERINGS
    assert dv.LOWERINGS[HL]["lower"] is dv.LOWERINGS["reading"]["lower"]
    assert dv.LOWERINGS[HL]["scenarios"] is dv.LOWERINGS["reading"]["scenarios"]

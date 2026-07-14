#!/usr/bin/env python3
"""P5.2/P5.3 -- Reading macros under MDL, with a macro-expansion certificate.

A recurring READING pattern (generators/reading.py) can be captured as a MACRO
that expands to concrete statements before the groundedness gate, inheriting the
invocation's force+quote.  The vocabulary is only allowed to grow when it PAYS:

Part A -- MDL admission.  A hand-written corpus of readings shares the "never let
  a quantity go negative, and never let an action exceed it" cluster.  The MDL
  gate (buildloop/mdl_macros.py, mirroring buildloop.mdl.admission_decision's
  dl_before/dl_after shape) admits the `no_oversell` macro IFF it strictly
  reduces the corpus description length AND is used by >= 2 readings.

Part B -- the macro-expansion-cert (a new NON-pooled kernel contract, five
  touchpoints + a TRUST entry, direct-path like monitor-cert).  Two independent
  channels certify that the macro-EXPANDED reading is identical to the hand-
  INLINED one: channel 1 = the two compile to a byte-identical meta-spec (equal
  compile-hash); channel 2 = the expanded reading's emitted dispatcher reproduces
  every accept/reject the inlined reading's demands solver-ENTAIL.

Part C -- teeth.  A PLANTED BAD macro drops the guard bound, so it expands to a
  DIFFERENT spec.  BOTH channels refute it: channel 1 sees a different compile-
  hash; channel 2 sees the guard-less dispatcher accept a call the inlined demand
  entailed as a rejection.  No certificate is issued.

Part D -- measurement (P5.3, results/macro_compression.csv).  The macro reduces
  the mean statements/reading and the token proxy across the corpus while the
  CERTIFIED COUNT is UNCHANGED -- expansion compresses without weakening what is
  certified (the certs come from IDENTICAL compiled specs, so they cache-hit).

REQUIRES_LLM = False -- every Reading and macro here is hand-written; nothing
calls the LLM (live `synthesize --semantic` is flaky at the frontier and is not
on this deterministic path).
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import kernel
from kernel.certs import Certificate
from generators import (reading as rd, reading_compile as rc,
                        service_model as svm, service_gen as sg)
from buildloop import mdl_macros as mm
from run import semantic

REQUIRES_LLM = False

# --- the macro under test, and a planted BAD twin ----------------------------
# no_oversell(q, act, arg): the recurring safety cluster -- a global floor on q
# AND a live guard that an action's argument may not exceed q.
NO_OVERSELL = {
    "name": "no_oversell", "params": ["q", "act", "arg"],
    "body": [
        {"kind": "always", "pred": {"op": ">=", "left": "$q", "right": 0}},
        {"kind": "bound", "action": "$act", "left": "$arg",
         "cmp": "<=", "right": "$q"}]}
# the bad twin DROPS the guard bound: it expands to a strictly weaker, DIFFERENT
# spec (the action may exceed the quantity), so both cert channels must refute it.
BAD_OVERSELL = {
    "name": "bad_no_oversell", "params": ["q", "act", "arg"],
    "body": [
        {"kind": "always", "pred": {"op": ">=", "left": "$q", "right": 0}}]}


def _reading(service, request, qty, qty_q, act, act_q, arg, safety_q, macro=None):
    """Build (inlined_dict, macro_form_dict).  The macro form replaces the two
    safety-cluster statements with ONE invocation; the inlined form spells them
    out.  Everything else is identical, so both compile to the same spec."""
    base = [
        {"id": "s1", "force": "presupposition", "quote": qty_q,
         "lf": {"kind": "quantity", "name": qty, "min": 0, "max": 100}},
        {"id": "s2", "force": "presupposition", "quote": act_q,
         "lf": {"kind": "action", "name": act, "arg": arg}},
        {"id": "s3", "force": "presupposition", "quote": act_q,
         "lf": {"kind": "effect", "action": act, "quantity": qty,
                "op": "dec", "amount": {"arg": arg}}}]
    cluster = [
        {"id": "s4", "force": "demand", "quote": safety_q,
         "lf": {"kind": "always", "pred": {"op": ">=", "left": qty, "right": 0}}},
        {"id": "s5", "force": "demand", "quote": safety_q,
         "lf": {"kind": "bound", "action": act, "left": arg,
                "cmp": "<=", "right": qty}}]
    tail = [
        {"id": "s6", "force": "choice", "quote": "",
         "lf": {"kind": "action", "name": "close_out"}},
        {"id": "s7", "force": "choice", "quote": "",
         "lf": {"kind": "lifecycle", "states": ["open", "closed"],
                "initial": "open"}},
        {"id": "s8", "force": "choice", "quote": "",
         "lf": {"kind": "transition", "action": act, "from": "open", "to": "open"}},
        {"id": "s9", "force": "choice", "quote": "",
         "lf": {"kind": "transition", "action": "close_out", "from": "open",
                "to": "closed"}}]
    inlined = {"service": service, "statements": base + cluster + tail}
    invoke_name = macro["name"] if macro else NO_OVERSELL["name"]
    macro_form = {"service": service, "statements": base + [
        {"id": "m1", "force": "demand", "quote": safety_q,
         "lf": {"kind": "macro", "name": invoke_name,
                "args": {"q": qty, "act": act, "arg": arg}}}] + tail}
    return inlined, macro_form


# The corpus: three domains, one shared safety pattern.  Quotes occur verbatim in
# each request (the groundedness gate checks that mechanically).
CORPUS = [
    dict(service="tickets",
         request="Please make sure we never oversell tickets beyond the "
                 "seats we have left.",
         qty="tickets_left", qty_q="tickets", act="sell", act_q="oversell",
         arg="count", safety_q="never oversell tickets"),
    dict(service="inventory",
         request="Our inventory keeps going negative; guarantee we never "
                 "allocate more parts than we have on hand.",
         qty="parts_on_hand", qty_q="parts", act="allocate", act_q="allocate",
         arg="qty", safety_q="never allocate more parts than we have"),
    dict(service="booking",
         request="In our booking system we must never reserve more seats "
                 "than remain available in the room.",
         qty="seats_left", qty_q="seats", act="reserve", act_q="reserve",
         arg="n", safety_q="never reserve more seats than remain"),
]


class _R:
    """Lightweight reading holder for the MDL arithmetic (statements only)."""
    def __init__(self, stmts):
        self.statements = stmts


def _compile_and_emit(reading_dict, request, macro_table):
    r = rd.parse_reading(json.dumps(reading_dict), request, macro_table=macro_table)
    spec, _ = rc.compile_reading(r)
    return sg.emit_service(svm.parse_service_spec(spec))


def part_a():
    print("== Part A: MDL admission -- a macro is minted only if it pays ==")
    inlined_corpus = [_R(_reading(**c)[0]["statements"]) for c in CORPUS]
    dec = mm.macro_admission_decision(inlined_corpus, NO_OVERSELL)
    print(f"  candidate macro: {NO_OVERSELL['name']}"
          f"({', '.join(NO_OVERSELL['params'])})  body={len(NO_OVERSELL['body'])} stmts")
    print(f"  dl_before={dec['dl_before']}  dl_after={dec['dl_after']}  "
          f"delta={dec['delta']}")
    print(f"  used by {dec['uses']} readings (>=2: {dec['used_by_ge_2']})")
    print(f"  mean statements/reading: {dec['mean_statements_before']} -> "
          f"{dec['mean_statements_after']}")
    print(f"  ADMIT: {dec['admit']}")
    # a one-off macro (used by a single reading) must be REFUSED even if it would
    # shave a token -- the two-witness discipline.
    single = mm.macro_admission_decision([inlined_corpus[0]], NO_OVERSELL)
    print(f"  control: same macro over a 1-reading corpus -> admit="
          f"{single['admit']} (uses={single['uses']}; needs >=2)")
    return dec["admit"] and dec["dl_after"] < dec["dl_before"] \
        and dec["uses"] >= 2 and not single["admit"]


def part_b():
    print("\n== Part B: macro-expansion-cert -- expanded == hand-inlined ==")
    c = CORPUS[0]
    inlined, macro_form = _reading(**c)
    files = _compile_and_emit(macro_form, c["request"], {"no_oversell": NO_OVERSELL})
    v = kernel.check(
        {"kind": "reading-macro", "files": files},
        {"type": "macro-expansion-cert", "request": c["request"],
         "inlined_reading": json.dumps(inlined),
         "expanded_reading": json.dumps(macro_form),
         "macro_table": {"no_oversell": NO_OVERSELL}})
    ok = isinstance(v, Certificate)
    ch = [(x["backend"], x["result"]) for x in
          (v.channels if ok else v.to_dict()["channels"])]
    print(f"  {'OK' if ok else 'XX'} macro-expansion-cert  channels={ch}")
    if ok:
        print(f"  tier: {v.tier}")
        for cl in v.claims:
            print(f"    claim: {cl[0]} = {cl[1][:70]}")
        for nc in v.non_claims:
            print(f"    non-claim: {nc[0]}")
    return ok and all(r == "pass" for _b, r in ch) and len(ch) == 2


def part_c():
    print("\n== Part C: a PLANTED BAD macro (drops the guard) is REFUTED ==")
    c = CORPUS[0]
    inlined, _good = _reading(**c)
    _in, bad_form = _reading(macro=BAD_OVERSELL, **c)
    files = _compile_and_emit(bad_form, c["request"],
                              {"bad_no_oversell": BAD_OVERSELL})
    v = kernel.check(
        {"kind": "reading-macro", "files": files},
        {"type": "macro-expansion-cert", "request": c["request"],
         "inlined_reading": json.dumps(inlined),
         "expanded_reading": json.dumps(bad_form),
         "macro_table": {"bad_no_oversell": BAD_OVERSELL}})
    refuted = not isinstance(v, Certificate)
    d = v.to_dict() if refuted else {}
    ch = [(x["backend"], x["result"]) for x in d.get("channels", [])]
    print(f"  issued a certificate: {not refuted}  (want False)")
    print(f"  verdict={d.get('verdict')}  channels={ch}")
    ch1_fail = any(b == "macro-compile-identity" and r != "pass" for b, r in ch)
    ch2_fail = any(b.startswith("expanded-dispatcher") and r != "pass"
                   for b, r in ch)
    print(f"  channel 1 (compile-hash) refutes: {ch1_fail}")
    print(f"  channel 2 (entailed replay) refutes: {ch2_fail}")
    return refuted and ch1_fail and ch2_fail


def part_d():
    print("\n== Part D: measurement -- results/macro_compression.csv ==")
    inlined_corpus = [_R(_reading(**c)[0]["statements"]) for c in CORPUS]
    before = mm.corpus_dl(inlined_corpus, {})
    after = mm.corpus_dl(inlined_corpus, {"no_oversell": NO_OVERSELL})

    # certified count: certify each reading BEFORE (inlined) and AFTER (macro
    # form).  A shared cache makes the AFTER certifications cache-hit -- they
    # compile to IDENTICAL specs (the macro-expansion-cert's channel 1), so the
    # same obligations are served, which is exactly why the count is unchanged.
    store: dict = {}
    cg = lambda k: store.get(k)
    cp = lambda k, val: store.__setitem__(k, val)
    cert_before = cert_after = 0
    for c in CORPUS:
        inlined, macro_form = _reading(**c)
        rb = semantic.certify_reading(c["request"], json.dumps(inlined),
                                      cache_get=cg, cache_put=cp,
                                      write_output=False)
        cert_before += 1 if rb.ok else 0
        ra = semantic.certify_reading(c["request"], json.dumps(macro_form),
                                      cache_get=cg, cache_put=cp,
                                      write_output=False,
                                      macro_table={"no_oversell": NO_OVERSELL})
        cert_after += 1 if ra.ok else 0

    rows = [
        ("readings", before["n"], after["n"]),
        ("mean_statements_per_reading",
         round(before["mean_statements"], 3), round(after["mean_statements"], 3)),
        ("total_statements", before["total_statements"], after["total_statements"]),
        ("corpus_token_proxy_dl",
         round(before["total"], 3), round(after["total"], 3)),
        ("certified_count", cert_before, cert_after),
    ]
    out = pathlib.Path("results") / "macro_compression.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "before", "after"])
        for r in rows:
            w.writerow(r)
    for metric, b, a in rows:
        print(f"  {metric:<30} before={b}  after={a}")
    print(f"  wrote {out}")
    compressed = (after["mean_statements"] < before["mean_statements"]
                  and after["total"] < before["total"])
    unchanged = (cert_before == cert_after == len(CORPUS))
    print(f"  compressed (fewer statements + lower DL): {compressed}")
    print(f"  certified count UNCHANGED at {cert_after}/{len(CORPUS)}: {unchanged}")
    return compressed and unchanged


if __name__ == "__main__":
    a = part_a()
    b = part_b()
    c = part_c()
    d = part_d()
    print("\nsummary:", json.dumps({
        "part_a_macro_admitted_under_mdl": a,
        "part_b_macro_expansion_certified": b,
        "part_c_bad_macro_refuted": c,
        "part_d_compression_unchanged_certified": d}))
    sys.exit(0 if all([a, b, c, d]) else 1)

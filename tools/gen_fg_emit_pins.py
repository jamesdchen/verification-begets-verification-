#!/usr/bin/env python3
"""Level B pin generator: corpus readings -> tools/fg_emit_pins.lean.

Each committed reading inside the binary-argument reflect slice is
transcribed ONCE into an FgReflect `EReading` datum together with the
EXACT proposition bytes the shipped compiler emits for it
(generators/math_compile.compile_math_reading, theorem wrapper
stripped).  The generated file carries, per reading:

  * a kernel `rfl` pin  `emitProp <datum> = "<bytes>"`  -- the Lean
    reference emitter agrees with the shipped compiler byte-for-byte;
  * a pairing instance through `toReading` -- the SAME datum names the
    statement `compile_preserves` (level A) speaks about.

Deterministic and LLM-free.  Skips are NAMED, never silent:

  * slice-miss:<...>   -- an op outside the reflect slice (gcd, ...);
  * pow-surface-form   -- powTm unrolls to a product, but the compiler
    renders `^`, so the surface bytes cannot match in this slice;
  * nary-flattening    -- the compiler renders n-ary + / * / and / or
    flat; the binarized Tm/Pd fold cannot reproduce those bytes.

GENERATION-TIME CROSS-CHECK: the transcribed datum is rendered by a
Python SIMULATION of the Lean emitter's rules -- from the quoted
constructor text parsed BACK (the parity-test discipline), so the check
covers the datum actually written, not the source AST -- and must equal
the compiler bytes before anything is emitted.  A transcription bug
dies here, not in the Lean lane.
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.math_compile import _pred_refs, compile_math_reading
from generators.math_reading import parse_math_reading
from run.reflect_shadow import SliceMiss, quote_pred

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READINGS = os.path.join(ROOT, "specs", "mathsources", "readings")
OUT = os.path.join(ROOT, "tools", "fg_emit_pins.lean")


class Skip(Exception):
    """A named per-reading skip (reason in args[0])."""


# ------------------------------------------------- quoted text -> AST parser
# (the parity-test discipline, generator-local: the cross-check must read the
# BYTES being committed, not re-walk the source AST it came from)
def _parse_sexpr(text):
    toks = text.replace("(", " ( ").replace(")", " ) ").split()

    def parse(i):
        assert toks[i] == "(", toks[i:]
        i += 1
        head = toks[i]
        i += 1
        args = []
        while toks[i] != ")":
            if toks[i] == "(":
                node, i = parse(i)
                args.append(node)
            else:
                args.append(toks[i])
                i += 1
        return (head, args), i + 1

    node, i = parse(0)
    assert i == len(toks), "trailing tokens"
    return node


_TM = {"Tm.add": "+", "Tm.sub": "-", "Tm.mul": "*", "Tm.tmod": "%"}
_PD = {"Pd.peq": "=", "Pd.ple": "<=", "Pd.plt": "<", "Pd.pne": "!=",
       "Pd.pdvd": "dvd", "Pd.peven": "even", "Pd.podd": "odd",
       "Pd.pand": "and", "Pd.por": "or", "Pd.pimp": "implies"}


def _unquote(text):
    def conv(node):
        head, args = node
        if head == "Tm.lit":
            a = args[0]
            return {"lit": int(a if isinstance(a, str) else a[0])}
        if head == "Tm.tvar":
            return {"var": int(args[0])}
        op = _TM.get(head) or _PD.get(head)
        assert op is not None, head
        return {"op": op, "args": [conv(a) for a in args]}
    return conv(_parse_sexpr(text))


# ----------------------------------- Lean-emitter rules, simulated in Python
_SYM_ATOM = {"=": "=", "<=": "≤", "<": "<", "!=": "≠"}
_SYM_CONN = {"and": "∧", "or": "∨"}


def _sim_term(t, names):
    if "var" in t:
        return names[t["var"]]
    if "lit" in t:
        v = t["lit"]
        return str(v) if v >= 0 else f"({v})"
    a, b = t["args"]
    return f"({_sim_term(a, names)} {t['op']} {_sim_term(b, names)})"


def _sim_pred(p, names):
    op = p["op"]
    if op in _SYM_ATOM:
        a, b = p["args"]
        return f"({_sim_term(a, names)} {_SYM_ATOM[op]} {_sim_term(b, names)})"
    if op == "dvd":
        a, b = p["args"]
        return f"({_sim_term(a, names)} ∣ {_sim_term(b, names)})"
    if op == "even":
        return f"(Even {_sim_term(p['args'][0], names)})"
    if op == "odd":
        return f"(Odd {_sim_term(p['args'][0], names)})"
    if op in _SYM_CONN:
        a, b = p["args"]
        return f"({_sim_pred(a, names)} {_SYM_CONN[op]} {_sim_pred(b, names)})"
    if op == "implies":
        a, b = p["args"]
        return f"({_sim_pred(a, names)} → {_sim_pred(b, names)})"
    raise AssertionError(op)


def _sim_prop(segs, names, hyps_q, concl_q, concls_q):
    prefix = ""
    for ex, cols in segs:
        sym = "∃" if ex else "∀"
        prefix += (sym + " "
                   + " ".join(f"({n} : {c})" for n, c in cols) + ", ")
    strs = [_sim_pred(_unquote(q), names) for q in [concl_q] + concls_q]
    conclusion = strs[0] if len(strs) == 1 else "(" + " ∧ ".join(strs) + ")"
    body = " → ".join([_sim_pred(_unquote(q), names) for q in hyps_q]
                           + [conclusion])
    return prefix + body


# ------------------------------------------------------------- transcription
def _nary(node) -> bool:
    args = node.get("args", [])
    if node.get("op") in ("+", "*", "and", "or") and len(args) > 2:
        return True
    return any(_nary(a) for a in args if isinstance(a, dict))


def _transcribe(stem: str, reading) -> dict:
    objects = reading.objects()
    names = sorted(objects)
    idx = {n: i for i, n in enumerate(names)}
    by_id = lambda s: s["id"]
    hyp_stmts = sorted(reading.by_kind("hypothesis"), key=by_id)
    concl_stmts = sorted(reading.by_kind("conclusion"), key=by_id)
    preds = [s["lf"]["pred"] for s in hyp_stmts + concl_stmts]

    for p in preds:
        if _nary(p):
            raise Skip("nary-flattening")
    try:
        hyps_q = [quote_pred(s["lf"]["pred"], idx) for s in hyp_stmts]
        concl_qs = [quote_pred(s["lf"]["pred"], idx) for s in concl_stmts]
    except SliceMiss as e:
        raise Skip(f"slice-miss:{e}") from e
    if any("powTm" in q for q in hyps_q + concl_qs):
        raise Skip("pow-surface-form")

    # binder segments, exactly the compiler's build: quantifier statements in
    # id order (objects in listed order), preceded by a leading forall over
    # referenced-but-unbound objects in sorted-name order.
    bound: set = set()
    q_segs = []
    for s in sorted(reading.by_kind("quantifier"), key=by_id):
        lf = s["lf"]
        q_segs.append((lf["binder"] != "forall",
                       [(o, objects[o]) for o in lf["objects"]]))
        bound.update(lf["objects"])
    referenced: set = set()
    for p in preds:
        referenced.update(_pred_refs(p))
    leading = sorted(referenced - bound)
    segs = ([(False, [(o, objects[o]) for o in leading])] if leading else [])
    segs += q_segs

    art = compile_math_reading(reading)
    lt = art["lean_text"]
    prefix = f"theorem {reading.theorem} : "
    suffix = " := " + "sorry"
    assert lt.startswith(prefix) and lt.endswith(suffix), stem
    prop = lt[len(prefix):-len(suffix)]
    assert '"' not in prop and "\\" not in prop, stem

    sim = _sim_prop(segs, names, hyps_q, concl_qs[0], concl_qs[1:])
    assert sim == prop, (stem, sim, prop)

    return {"stem": stem, "name": "pin_" + stem, "theorem": reading.theorem,
            "prop": prop, "segs": segs, "names": names, "hyps_q": hyps_q,
            "concl_q": concl_qs[0], "concls_q": concl_qs[1:]}


def collect():
    """(pins, skips): every corpus reading lands in exactly one list."""
    pins, skips = [], []
    for path in sorted(glob.glob(os.path.join(READINGS, "*.json"))):
        stem = os.path.basename(path)[:-len(".json")]
        d = json.load(open(path))
        reading = parse_math_reading(json.dumps(d["reading"]), d["source"])
        try:
            pins.append(_transcribe(stem, reading))
        except Skip as e:
            skips.append((stem, e.args[0]))
    return pins, skips


# ------------------------------------------------------------------ emission
def _lean_seg(ex, cols) -> str:
    body = ", ".join(f'("{n}", "{c}")' for n, c in cols)
    flag = "true" if ex else "false"
    return "{ ex := " + flag + ", vars := [" + body + "] }"


def _entry(rec) -> str:
    segs = ",\n      ".join(_lean_seg(e, v) for e, v in rec["segs"])
    names = ", ".join(f'"{n}"' for n in rec["names"])
    hyps = ", ".join(rec["hyps_q"])
    concls = ", ".join(rec["concls_q"])
    return (
        f"/-- specs/mathsources/readings/{rec['stem']}.json "
        f"(theorem {rec['theorem']}). -/\n"
        f"def {rec['name']} : EReading :=\n"
        "  { segs := [\n"
        f"      {segs}],\n"
        f"    names := [{names}],\n"
        f"    hyps := [{hyps}],\n"
        f"    concl := {rec['concl_q']},\n"
        f"    concls := [{concls}] }}\n"
        "\n"
        f"example : emitProp {rec['name']} =\n"
        f"    \"{rec['prop']}\" := rfl\n"
        "\n"
        "example (env : Nat -> Int) :\n"
        f"    readingDenote (toReading {rec['name']}) env <->\n"
        f"    denoteStmt env (compileR (toReading {rec['name']})) :=\n"
        "  compile_preserves _ _\n")


_HEADER = """/-
tools/fg_emit_pins.lean -- GENERATED by tools/gen_fg_emit_pins.py.
Do not edit by hand; regenerate and let the teeth compare bytes.

Level B pins: each entry transcribes one corpus reading ONCE as an
EReading datum; `emitProp` (the in-module reference emitter) must
render it to EXACTLY the proposition bytes the shipped Python compiler
emitted for the same reading (theorem wrapper stripped) -- discharged
by kernel rfl when this file elaborates appended to
tools/FgReflect.lean.  The Python tooth (tests/test_fg_emit_pins.py)
pins the same strings against a live compiler run, closing the loop:
emitter bytes == pin bytes == compiler bytes.  The second example per
entry routes the SAME datum through toReading into compile_preserves,
so the pinned surface and the level-A statement share one source.
-/

namespace FgReflect

set_option maxHeartbeats 400000

"""


def build_text() -> str:
    pins, skips = collect()
    skip_lines = "".join(f"     {stem}: {reason}\n" for stem, reason in skips)
    skip_block = ("/- skipped (named, generator-verified):\n"
                  + skip_lines + "-/\n\n") if skips else ""
    return (_HEADER + skip_block + "\n".join(_entry(rec) for rec in pins)
            + "\nend FgReflect\n")


def main() -> None:
    text = build_text()
    with open(OUT, "w") as fh:
        fh.write(text)
    pins, skips = collect()
    print(f"wrote {OUT}: {len(pins)} pins, {len(skips)} skips")
    for stem, reason in skips:
        print(f"  skip {stem}: {reason}")


if __name__ == "__main__":
    main()

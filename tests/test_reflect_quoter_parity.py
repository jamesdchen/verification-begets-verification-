"""Quoter parity teeth (the S4b-readiness gap: agreement must mean "the
probe asserts the RIGHT proposition", not merely "the probe elaborated").

The shadow differential records agreement when a probe elaborates -- but a
mistranslating quoter (F-G AST -> FgReflect constructors) could build a
probe that asserts a DIFFERENT true statement and still elaborate.  These
teeth close that hole from two sides:

  * ROUND-TRIP: a test-local parser reads the quoted constructor text back
    into an AST and asserts equality with an independently computed normal
    form of the source AST (n-ary + and * fold left, `mod` -> `%`, refs ->
    indices) -- for every committed reading's conclusion, hypothesis fold,
    and emitted template.
  * PLANTED MIS-QUOTE: perturbing the quoter's atom table must make the
    round-trip fail -- proving the parity check has teeth, not just luck.

LLM-free, Lean-free, deterministic.
"""
import glob
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.math_reading import parse_math_reading
from generators.math_eval import conclusions_of, hypotheses_of
from generators.math_witness import emit_witness_proofs
from run import reflect_shadow

READINGS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "specs", "mathsources", "readings")


# ------------------------------------------------ quoted-text -> AST parser
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


def unquote(text):
    """Quoted FgReflect constructor text -> binarized AST."""
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


# --------------------------------- source AST -> expected binarized normal form
def norm_term(t, idx):
    if "ref" in t:
        return {"var": idx[t["ref"]]}
    if "lit" in t:
        return {"lit": t["lit"]}
    op = "%" if t["op"] == "mod" else t["op"]
    out = norm_term(t["args"][0], idx)
    for a in t["args"][1:]:
        out = {"op": op, "args": [out, norm_term(a, idx)]}
    return out


def norm_pred(p, idx):
    op = p["op"]
    if op in ("and", "or", "implies"):
        out = norm_pred(p["args"][0], idx)
        for a in p["args"][1:]:
            out = {"op": op, "args": [out, norm_pred(a, idx)]}
        return out
    if op in ("even", "odd"):
        return {"op": op, "args": [norm_term(p["args"][0], idx)]}
    return {"op": op, "args": [norm_term(a, idx) for a in p["args"]]}


def _corpus():
    for path in sorted(glob.glob(os.path.join(READINGS, "*.json"))):
        d = json.load(open(path))
        yield (os.path.basename(path),
               parse_math_reading(json.dumps(d["reading"]), d["source"]))


def test_conclusions_round_trip():
    checked = 0
    for name, reading in _corpus():
        idx = {n: i for i, n in enumerate(sorted(reading.objects()))}
        concl = conclusions_of(reading)
        try:
            quoted = reflect_shadow.quote_pred(concl, idx)
        except reflect_shadow.SliceMiss:
            continue                       # named-skip class, not parity's job
        assert unquote(quoted) == norm_pred(concl, idx), name
        checked += 1
    assert checked >= 8, checked


def test_hypothesis_folds_round_trip():
    checked = 0
    for name, reading in _corpus():
        hyps = hypotheses_of(reading)
        if not hyps:
            continue
        idx = {n: i for i, n in enumerate(sorted(reading.objects()))}
        body = conclusions_of(reading)
        for h in reversed(hyps):
            body = {"op": "implies", "args": [h, body]}
        try:
            quoted = reflect_shadow.quote_pred(body, idx)
        except reflect_shadow.SliceMiss:
            continue
        assert unquote(quoted) == norm_pred(body, idx), name
        checked += 1
    assert checked >= 2, checked


def test_templates_round_trip():
    checked = 0
    for name, reading in _corpus():
        res = emit_witness_proofs(reading, bound=8)
        if res["status"] != "emitted":
            continue
        idx = {n: i for i, n in enumerate(sorted(reading.objects()))}
        for var, tmpl in res["template"].items():
            quoted = reflect_shadow.quote_term(tmpl, idx)
            assert unquote(quoted) == norm_term(tmpl, idx), (name, var)
            checked += 1
    assert checked >= 5, checked


def test_planted_misquote_is_caught(monkeypatch):
    # perturb the quoter's atom table (<= emitted as Pd.plt): the round-trip
    # must FAIL -- otherwise this parity file is decoration, not a tooth.
    idx = {"a": 0, "b": 1}
    pred = {"op": "<=", "args": [{"ref": "a"}, {"ref": "b"}]}
    good = reflect_shadow.quote_pred(pred, idx)
    assert unquote(good) == norm_pred(pred, idx)
    bad_atoms = dict(reflect_shadow._ATOM_OPS)
    bad_atoms["<="] = "Pd.plt"
    monkeypatch.setattr(reflect_shadow, "_ATOM_OPS", bad_atoms)
    bad = reflect_shadow.quote_pred(pred, idx)
    assert unquote(bad) != norm_pred(pred, idx)


def test_planted_arg_swap_is_caught(monkeypatch):
    # a subtler plant: swapped atom arguments must also fail the round-trip.
    idx = {"a": 0, "b": 1}
    pred = {"op": "<", "args": [{"ref": "a"}, {"ref": "b"}]}
    orig = reflect_shadow.quote_pred

    def swapped(p, index_of):
        if p.get("op") in reflect_shadow._ATOM_OPS and len(p["args"]) == 2:
            x, y = p["args"]
            p = {"op": p["op"], "args": [y, x]}
        return orig(p, index_of)

    monkeypatch.setattr(reflect_shadow, "quote_pred", swapped)
    assert unquote(reflect_shadow.quote_pred(pred, idx)) != norm_pred(pred, idx)
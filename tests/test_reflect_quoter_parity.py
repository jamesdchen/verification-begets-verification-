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

P4's congruence image raises the stakes on both: a residue `=` atom is quoted
as an Int divisibility statement, so the quoted text no longer LOOKS like the
source atom and the round-trip is the only thing that says it means it.  The
image is unquoted to `n | (a - b)` and compared against an INDEPENDENTLY built
image, and the modulus is perturbed twice -- once passed in, once resolved
from the reading -- because a wrong modulus is a mis-quote that still
elaborates.

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


def _pow_unroll(base, k):
    """The powTm shape: left-nested k-fold product from (lit 1)."""
    out = {"lit": 1}
    for _ in range(k):
        out = {"op": "*", "args": [out, base]}
    return out


def unquote(text):
    """Quoted FgReflect constructor text -> binarized AST."""
    def conv(node):
        head, args = node
        if head == "zmodEq":
            # P4: the congruence image unquotes to what it MEANS, not to the
            # residue atom it came from -- `n | (a - b)`.  Parity is then
            # checked against an INDEPENDENTLY built image (`zmod_image`
            # below), so a quoter that emitted the wrong modulus cannot
            # round-trip through its own mistake.
            n = args[0] if isinstance(args[0], str) else args[0][0]
            return {"op": "dvd", "args": [
                {"lit": int(n)},
                {"op": "-", "args": [conv(args[1]), conv(args[2])]}]}
        if head == "Tm.lit":
            a = args[0]
            return {"lit": int(a if isinstance(a, str) else a[0])}
        if head == "Tm.tvar":
            return {"var": int(args[0])}
        if head == "powTm":
            return _pow_unroll(conv(args[0]), int(args[1]))
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
    if t["op"] == "^":
        # D10: literal exponent unrolls exactly like powTm -- the parity
        # holds at the UNROLLED normal form on both sides.
        return _pow_unroll(norm_term(t["args"][0], idx), t["args"][1]["lit"])
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


def test_pow_round_trips():
    idx = {"n": 0, "m": 1}
    pred = {"op": "=", "args": [
        {"ref": "m"}, {"op": "^", "args": [{"ref": "n"}, {"lit": 2}]}]}
    quoted = reflect_shadow.quote_pred(pred, idx)
    assert "powTm" in quoted
    assert unquote(quoted) == norm_pred(pred, idx)


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


# ------------------------------------------ P4: the congruence image's parity
# The round-trip's whole point is that agreement means "the probe asserts the
# RIGHT proposition".  For the residue image that means TWO things and the
# teeth below say both: the image is the right SHAPE (n divides a - b), and it
# carries the right MODULUS.  The second is what the plants prove, and it is
# the half elaboration can NEVER supply -- see the comment on
# `test_planted_modulus_perturbation_is_caught`.
def zmod_image(pred, idx, n):
    """The congruence image of an `=` atom, built WITHOUT the quoter -- parity
    needs an independent other side, or it is only checking the quoter against
    itself."""
    a, b = (norm_term(t, idx) for t in pred["args"])
    return {"op": "dvd", "args": [{"lit": n},
                                  {"op": "-", "args": [a, b]}]}


def _zmod_exists_reading(carrier="ZMod 5"):
    """`for every n there exists m with n + m = n` on one carrier -- the
    forall-outer / exists-inner shape route 1 accepts, with a CONSTANT witness
    so the emitter's integer-shaped candidate family lands a template."""
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": carrier}},
        {"id": "on", "force": "demand", "quote": "the residue n",
         "lf": {"kind": "object", "name": "n", "type": carrier}},
        {"id": "om", "force": "demand", "quote": "the residue m",
         "lf": {"kind": "object", "name": "m", "type": carrier}},
        {"id": "qf", "force": "demand", "quote": "for every",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "qx", "force": "demand", "quote": "there exists",
         "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
        {"id": "c", "force": "demand", "quote": "n plus m is n",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [{"ref": "n"}, {"ref": "m"}]},
             {"ref": "n"}]}}},
    ]
    src = " ".join(s["quote"] for s in stmts if s["quote"])
    return parse_math_reading(
        json.dumps({"theorem": "zmod_parity", "statements": stmts}), src)


def test_zmod_congruence_image_round_trips():
    idx = {"x": 0, "y": 1}
    pred = {"op": "=", "args": [
        {"op": "*", "args": [{"ref": "x"}, {"ref": "y"}]}, {"lit": 3}]}
    quoted = reflect_shadow.quote_pred(pred, idx, "Int", 5)
    assert "(zmodEq 5 " in quoted
    assert unquote(quoted) == zmod_image(pred, idx, 5)
    # the SAME atom with no modulus stays the ordinary Int equality: the image
    # is spent on residue readings only, never leaked into the Int slice.
    assert unquote(reflect_shadow.quote_pred(pred, idx)) == norm_pred(pred, idx)


def test_planted_modulus_perturbation_is_caught():
    # THE image's parity tooth, in the shape test_planted_misquote_is_caught
    # uses for the atom table.  A wrong modulus is the mis-quote ELABORATION
    # cannot catch: `7 | ((x + 5) - x)` is false, but the perturbed probe would
    # be built from the perturbed reading, and plenty of congruences are true
    # at BOTH moduli -- so a mis-quoted image can still hand the lane a green.
    # Only the round-trip against an independently built image sees it.
    # Agreement must mean the RIGHT congruence, not merely a congruence.
    idx = {"x": 0}
    pred = {"op": "=", "args": [{"ref": "x"},
                                {"op": "+", "args": [{"ref": "x"},
                                                     {"lit": 5}]}]}
    good = reflect_shadow.quote_pred(pred, idx, "Int", 5)
    assert unquote(good) == zmod_image(pred, idx, 5)

    bad = reflect_shadow.quote_pred(pred, idx, "Int", 7)      # perturbed 5 -> 7
    assert "(zmodEq 7 " in bad
    assert unquote(bad) != zmod_image(pred, idx, 5)


def test_planted_modulus_perturbation_is_caught_end_to_end(monkeypatch):
    # The same plant one layer UP, where the modulus is RESOLVED from the
    # reading rather than passed in: perturbing the carrier-family predicate
    # must reach the emitted probe text.  That is what proves the modulus is
    # not hard-coded anywhere between the reading and the quoted atom -- and
    # it is the reason `_zmod_modulus` is imported into reflect_shadow rather
    # than re-matched there (one definition of what a residue carrier is).
    reading = _zmod_exists_reading()
    honest = reflect_shadow.shadow_probe(reading)
    assert honest["status"] == "probe", honest
    body = honest["probe"].split("namespace FgReflect")[-1]
    assert "(zmodEq 5 " in body

    orig = reflect_shadow._zmod_modulus
    monkeypatch.setattr(reflect_shadow, "_zmod_modulus",
                        lambda ty: None if orig(ty) is None else orig(ty) + 2)
    planted = reflect_shadow.shadow_probe(reading)
    assert planted["status"] == "probe", planted
    assert "(zmodEq 7 " in planted["probe"].split("namespace FgReflect")[-1]
    assert planted["probe"] != honest["probe"]
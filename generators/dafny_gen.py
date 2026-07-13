"""Deterministic derivation of Dafny proof obligations.

Two kinds of obligation are generated on top of the fixed, pre-verified
library generators/codec_model.dfy:

  * per-emission obligation: instantiate SPEC with one task spec's concrete
    field list and re-check round-trip + truncation-rejection for it
    (kernel evidence channel #2 for emit-check-tier emissions);

  * promotion obligation ("universal"): for a *grammar* restricted to
    fixed-width unsigned integers, prove that the static-offset
    implementation shape (the shape ksc emits for such layouts) decodes
    every spec-model encoding correctly for ALL field lists in the grammar.

Both are pure text generation; Dafny (Z3-backed) does all the judging.
"""
from __future__ import annotations

import pathlib

from .ksy_model import SpecModel, Field

LIB = (pathlib.Path(__file__).parent / "codec_model.dfy").read_text()


def _f_ctor(f: Field) -> str:
    e = "BE" if f.endian == "be" else "LE"
    if f.kind == "uint":
        return f"FUint({f.width}, {e})"
    if f.kind == "sint":
        return f"FSint({f.width}, {e})"
    if f.kind == "magic":
        return f"FMagic([{', '.join(str(b) for b in f.magic)}])"
    if f.kind == "str_fixed":
        return f"FStrFixed({f.size})"
    if f.kind == "str_lenprefix":
        return f"FStrLP({f.lenwidth}, {e})"
    if f.kind == "strz":
        return "FStrZ"
    if f.kind == "repeat_lit":
        return f"FRepLit({f.size}, {f.width}, {e})"
    if f.kind == "repeat_ref":
        return f"FRepRef({f.lenwidth}, {f.width}, {e})"
    raise ValueError(f.kind)


def per_spec_obligation(spec: SpecModel) -> str:
    ctors = ", ".join(_f_ctor(f) for f in spec.fields)
    return LIB + f"""
// ---- per-emission obligation for task spec '{spec.id}' -------------------
const SPEC: seq<F> := [{ctors}]

lemma SpecWellFormed()
  ensures WfSpec(SPEC)
{{
}}

lemma SpecRoundTrip(vs: seq<V>, rest: seq<byte>)
  requires ValidVals(SPEC, vs)
  ensures DecAll(SPEC, EncAll(SPEC, vs) + rest) == Some(vs, rest)
{{
  RecordRT(SPEC, vs, rest);
}}

lemma SpecTruncationRejected(vs: seq<V>, pre: seq<byte>)
  requires ValidVals(SPEC, vs)
  requires pre <= EncAll(SPEC, vs) && |pre| < |EncAll(SPEC, vs)|
  ensures DecAll(SPEC, pre) == None
{{
  RecordTrunc(SPEC, vs, pre);
}}
"""


UNIVERSAL_FIXED_UINT = LIB + """
// ---- promotion obligation: universal correctness over the whole grammar --
//
// Grammar: records whose fields are all fixed-width unsigned integers of a
// single endianness (the narrow generator's spec grammar).  ksc emits, for
// such layouts, straight-line code that reads each field at a *static
// offset*.  ImplDecode models that code shape.  The theorem quantifies over
// EVERY field list in the grammar -- not one emission -- which is what
// distinguishes the universal tier from per-emission checking.

ghost predicate GrammarOK(ws: seq<nat>) {
  forall i :: 0 <= i < |ws| ==> ws[i] in {1, 2, 4, 8}
}

function Offset(ws: seq<nat>, i: nat): nat
  requires i <= |ws|
{
  if i == 0 then 0 else ws[0] + Offset(ws[1..], i - 1)
}

lemma OffsetBound(ws: seq<nat>, i: nat)
  requires i <= |ws|
  ensures i < |ws| ==> Offset(ws, i) + ws[i] <= Offset(ws, |ws|)
{
  if i > 0 {
    OffsetBound(ws[1..], i - 1);
  } else if |ws| > 0 {
    OffsetNonNeg(ws[1..], |ws| - 1);
  }
}

lemma OffsetNonNeg(ws: seq<nat>, i: nat)
  requires i <= |ws|
  ensures Offset(ws, i) >= 0
{
}

function ImplDecode(ws: seq<nat>, e: End, bs: seq<byte>): seq<nat>
  requires |bs| == Offset(ws, |ws|)
{
  if |ws| == 0 then []
  else
    OffsetBound(ws, 0);
    [DecNat(bs[..ws[0]], e)] + ImplDecode(ws[1..], e, bs[ws[0]..])
}

function SpecOf(ws: seq<nat>, e: End): seq<F> {
  seq(|ws|, i requires 0 <= i < |ws| => FUint(ws[i], e))
}

function ValsOf(vs: seq<nat>): seq<V> {
  seq(|vs|, i requires 0 <= i < |vs| => VInt(vs[i]))
}

lemma EncAllLen(ws: seq<nat>, e: End, vs: seq<nat>)
  requires GrammarOK(ws) && |vs| == |ws|
  requires forall i :: 0 <= i < |vs| ==> vs[i] < Pow256(ws[i])
  ensures WfSpec(SpecOf(ws, e)) && ValidVals(SpecOf(ws, e), ValsOf(vs))
  ensures |EncAll(SpecOf(ws, e), ValsOf(vs))| == Offset(ws, |ws|)
{
  if |ws| != 0 {
    EncAllLen(ws[1..], e, vs[1..]);
    assert SpecOf(ws, e)[1..] == SpecOf(ws[1..], e);
    assert ValsOf(vs)[1..] == ValsOf(vs[1..]);
  }
}

// The universal theorem: for every spec in the grammar and every valid value
// assignment, the static-offset implementation decode inverts the spec-model
// encode.
lemma UniversalFixedUint(ws: seq<nat>, e: End, vs: seq<nat>)
  requires GrammarOK(ws) && |vs| == |ws|
  requires forall i :: 0 <= i < |vs| ==> vs[i] < Pow256(ws[i])
  ensures WfSpec(SpecOf(ws, e)) && ValidVals(SpecOf(ws, e), ValsOf(vs))
  ensures |EncAll(SpecOf(ws, e), ValsOf(vs))| == Offset(ws, |ws|)
  ensures ImplDecode(ws, e, EncAll(SpecOf(ws, e), ValsOf(vs))) == vs
{
  EncAllLen(ws, e, vs);
  if |ws| == 0 {
  } else {
    var fs := SpecOf(ws, e);
    var vv := ValsOf(vs);
    var enc0 := EncF(fs[0], vv[0]);
    var encT := EncAll(fs[1..], vv[1..]);
    var whole := EncAll(fs, vv);
    assert whole == enc0 + encT;
    assert |enc0| == ws[0];
    assert whole[..ws[0]] == enc0;
    assert whole[ws[0]..] == encT;
    EncDecNat(vs[0], ws[0], e);
    assert fs[1..] == SpecOf(ws[1..], e);
    assert vv[1..] == ValsOf(vs[1..]);
    UniversalFixedUint(ws[1..], e, vs[1..]);
    assert [vs[0]] + vs[1..] == vs;
  }
}
"""


def universal_obligation(atoms: frozenset) -> str:
    """Return the promotion .dfy for a grammar, or raise if out of scope.

    Only grammars consisting purely of fixed-width unsigned integers (plus an
    endianness atom) have a universal proof in this MVP.
    """
    allowed = {"endian:be", "endian:le", "uint:1", "uint:2", "uint:4", "uint:8"}
    extra = set(atoms) - allowed
    if extra:
        raise ValueError(
            f"no universal proof template covers atoms {sorted(extra)}; "
            "generator must stay at emit-check tier")
    return UNIVERSAL_FIXED_UINT

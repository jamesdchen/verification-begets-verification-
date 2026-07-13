// Generic codec contract model for the ksy subset used by the seed domain.
//
// This file is a fixed, machine-checked library: it defines an ideal
// encoder/decoder pair over field descriptors and proves the round-trip
// contract  Dec(Enc(vals) + rest) == Some((vals, rest))  for every
// well-formed field list, plus rejection of truncated inputs.
//
// Per-emission obligations instantiate SPEC with the concrete field list of
// one task spec (appended by generators/dafny_gen.py); Dafny re-verifies the
// instantiation.  Verified with Dafny 4.11 / Z3.

type byte = x: int | 0 <= x < 256

datatype End = BE | LE

datatype F =
    FUint(w: nat, e: End)
  | FSint(sw: nat, se: End)
  | FMagic(m: seq<byte>)
  | FStrFixed(n: nat)
  | FStrLP(lw: nat, le: End)
  | FStrZ
  | FRepLit(cnt: nat, ew: nat, ee: End)
  | FRepRef(rlw: nat, rew: nat, re: End)

datatype V =
    VInt(i: int)
  | VBytes(bs: seq<byte>)
  | VList(l: seq<nat>)

datatype Res = None | Some(v: seq<V>, rest: seq<byte>)
datatype FRes = FNone | FSome(fv: V, frest: seq<byte>)
datatype LRes = LNone | LSome(lv: seq<nat>, lrest: seq<byte>)

function Pow256(n: nat): nat
  ensures Pow256(n) >= 1
{
  if n == 0 then 1 else 256 * Pow256(n - 1)
}

ghost predicate WfF(f: F) {
  match f
  case FUint(w, _) => w in {1, 2, 4, 8}
  case FSint(w, _) => w in {1, 2, 4, 8}
  case FMagic(m) => |m| >= 1
  case FStrFixed(n) => n >= 1
  case FStrLP(lw, _) => lw in {1, 2}
  case FStrZ => true
  case FRepLit(c, ew, _) => c >= 1 && ew in {1, 2, 4, 8}
  case FRepRef(lw, ew, _) => lw in {1, 2} && ew in {1, 2, 4, 8}
}

ghost predicate ValidV(f: F, v: V) {
  match f
  case FUint(w, _) => v.VInt? && 0 <= v.i < Pow256(w)
  case FSint(w, _) => v.VInt? && -(Pow256(w) / 2) <= v.i < Pow256(w) / 2
  case FMagic(m) => v == VBytes(m)
  case FStrFixed(n) => v.VBytes? && |v.bs| == n
  case FStrLP(lw, _) => v.VBytes? && |v.bs| < Pow256(lw)
  case FStrZ => v.VBytes? && (forall k :: 0 <= k < |v.bs| ==> v.bs[k] != 0)
  case FRepLit(c, ew, _) =>
    v.VList? && |v.l| == c && forall k :: 0 <= k < |v.l| ==> v.l[k] < Pow256(ew)
  case FRepRef(lw, ew, _) =>
    v.VList? && |v.l| < Pow256(lw) && forall k :: 0 <= k < |v.l| ==> v.l[k] < Pow256(ew)
}

// ---------------------------------------------------------------- integers

function EncNat(v: nat, w: nat, e: End): seq<byte>
  requires v < Pow256(w)
  ensures |EncNat(v, w, e)| == w
{
  if w == 0 then [] else
    match e
    case BE => EncNat(v / 256, w - 1, BE) + [v % 256]
    case LE => [v % 256] + EncNat(v / 256, w - 1, LE)
}

function DecNat(bs: seq<byte>, e: End): nat
{
  if |bs| == 0 then 0 else
    match e
    case BE => DecNat(bs[..|bs| - 1], BE) * 256 + bs[|bs| - 1]
    case LE => bs[0] + 256 * DecNat(bs[1..], LE)
}

lemma EncDecNat(v: nat, w: nat, e: End)
  requires v < Pow256(w)
  ensures DecNat(EncNat(v, w, e), e) == v
{
  if w == 0 {
  } else {
    match e
    case BE => {
      var pre := EncNat(v / 256, w - 1, BE);
      var whole := pre + [v % 256];
      assert whole[..|whole| - 1] == pre;
      EncDecNat(v / 256, w - 1, BE);
    }
    case LE => {
      var tail := EncNat(v / 256, w - 1, LE);
      var whole := [v % 256] + tail;
      assert whole[1..] == tail;
      EncDecNat(v / 256, w - 1, LE);
    }
  }
}

lemma DecNatBound(bs: seq<byte>, e: End)
  ensures DecNat(bs, e) < Pow256(|bs|)
{
  if |bs| == 0 {
  } else {
    match e
    case BE => DecNatBound(bs[..|bs| - 1], BE);
    case LE => DecNatBound(bs[1..], LE);
  }
}

// two's complement on top of EncNat/DecNat
function EncSint(v: int, w: nat, e: End): seq<byte>
  requires w >= 1 && -(Pow256(w) / 2) <= v < Pow256(w) / 2
  ensures |EncSint(v, w, e)| == w
{
  EncNat(if v >= 0 then v else v + Pow256(w), w, e)
}

function DecSint(bs: seq<byte>, e: End): int
  requires |bs| >= 1
{
  var u := DecNat(bs, e);
  if u < Pow256(|bs|) / 2 then u else u - Pow256(|bs|)
}

lemma EncDecSint(v: int, w: nat, e: End)
  requires w >= 1 && -(Pow256(w) / 2) <= v < Pow256(w) / 2
  ensures DecSint(EncSint(v, w, e), e) == v
{
  EncDecNat(if v >= 0 then v else v + Pow256(w), w, e);
}

// ------------------------------------------------------------------- lists

function EncList(l: seq<nat>, ew: nat, e: End): seq<byte>
  requires forall k :: 0 <= k < |l| ==> l[k] < Pow256(ew)
  ensures |EncList(l, ew, e)| == |l| * ew
{
  if |l| == 0 then [] else EncNat(l[0], ew, e) + EncList(l[1..], ew, e)
}

function DecList(bs: seq<byte>, c: nat, ew: nat, e: End): LRes
  requires ew >= 1
  decreases c
{
  if c == 0 then LSome([], bs)
  else if |bs| < ew then LNone
  else
    var hd := DecNat(bs[..ew], e);
    match DecList(bs[ew..], c - 1, ew, e)
    case LNone => LNone
    case LSome(tl, rest) => LSome([hd] + tl, rest)
}

lemma EncDecList(l: seq<nat>, ew: nat, e: End, rest: seq<byte>)
  requires ew >= 1 && forall k :: 0 <= k < |l| ==> l[k] < Pow256(ew)
  ensures DecList(EncList(l, ew, e) + rest, |l|, ew, e) == LSome(l, rest)
{
  if |l| == 0 {
    assert EncList(l, ew, e) + rest == rest;
  } else {
    var h := EncNat(l[0], ew, e);
    var t := EncList(l[1..], ew, e);
    var whole := h + t + rest;
    assert EncList(l, ew, e) + rest == whole;
    assert whole[..ew] == h;
    assert whole[ew..] == t + rest;
    EncDecNat(l[0], ew, e);
    EncDecList(l[1..], ew, e, rest);
    assert [l[0]] + l[1..] == l;
  }
}

// ------------------------------------------------------------- one field

function FindZero(bs: seq<byte>): int
  ensures -1 <= FindZero(bs) < |bs|
  ensures FindZero(bs) >= 0 ==> bs[FindZero(bs)] == 0
  ensures FindZero(bs) >= 0 ==> forall k :: 0 <= k < FindZero(bs) ==> bs[k] != 0
  ensures FindZero(bs) == -1 ==> forall k :: 0 <= k < |bs| ==> bs[k] != 0
{
  if |bs| == 0 then -1
  else if bs[0] == 0 then 0
  else
    var r := FindZero(bs[1..]);
    if r == -1 then -1 else r + 1
}

function EncF(f: F, v: V): seq<byte>
  requires WfF(f) && ValidV(f, v)
{
  match f
  case FUint(w, e) => EncNat(v.i, w, e)
  case FSint(w, e) => EncSint(v.i, w, e)
  case FMagic(m) => m
  case FStrFixed(n) => v.bs
  case FStrLP(lw, e) => EncNat(|v.bs|, lw, e) + v.bs
  case FStrZ => v.bs + [0]
  case FRepLit(c, ew, e) => EncList(v.l, ew, e)
  case FRepRef(lw, ew, e) => EncNat(|v.l|, lw, e) + EncList(v.l, ew, e)
}

function DecF(f: F, bs: seq<byte>): FRes
  requires WfF(f)
{
  match f
  case FUint(w, e) =>
    if |bs| < w then FNone else FSome(VInt(DecNat(bs[..w], e)), bs[w..])
  case FSint(w, e) =>
    if |bs| < w then FNone else FSome(VInt(DecSint(bs[..w], e)), bs[w..])
  case FMagic(m) =>
    if |bs| < |m| || bs[..|m|] != m then FNone else FSome(VBytes(m), bs[|m|..])
  case FStrFixed(n) =>
    if |bs| < n then FNone else FSome(VBytes(bs[..n]), bs[n..])
  case FStrLP(lw, e) =>
    if |bs| < lw then FNone else
      var len := DecNat(bs[..lw], e);
      if |bs| - lw < len then FNone
      else FSome(VBytes(bs[lw..lw + len]), bs[lw + len..])
  case FStrZ =>
    var z := FindZero(bs);
    if z < 0 then FNone else FSome(VBytes(bs[..z]), bs[z + 1..])
  case FRepLit(c, ew, e) =>
    (match DecList(bs, c, ew, e)
     case LNone => FNone
     case LSome(l, rest) => FSome(VList(l), rest))
  case FRepRef(lw, ew, e) =>
    if |bs| < lw then FNone else
      var c := DecNat(bs[..lw], e);
      match DecList(bs[lw..], c, ew, e)
      case LNone => FNone
      case LSome(l, rest) => FSome(VList(l), rest)
}

lemma FindZeroAppend(bs: seq<byte>, rest: seq<byte>)
  requires forall k :: 0 <= k < |bs| ==> bs[k] != 0
  ensures FindZero(bs + [0] + rest) == |bs|
{
  var whole := bs + [0] + rest;
  assert whole[|bs|] == 0;
  var z := FindZero(whole);
  if z < |bs| {
    assert whole[z] == bs[z];
  }
}

lemma FieldRT(f: F, v: V, rest: seq<byte>)
  requires WfF(f) && ValidV(f, v)
  ensures DecF(f, EncF(f, v) + rest) == FSome(v, rest)
{
  var enc := EncF(f, v);
  var whole := enc + rest;
  match f
  case FUint(w, e) => {
    assert whole[..w] == enc;
    assert whole[w..] == rest;
    EncDecNat(v.i, w, e);
  }
  case FSint(w, e) => {
    assert whole[..w] == enc;
    assert whole[w..] == rest;
    EncDecSint(v.i, w, e);
  }
  case FMagic(m) => {
    assert whole[..|m|] == m;
    assert whole[|m|..] == rest;
  }
  case FStrFixed(n) => {
    assert whole[..n] == v.bs;
    assert whole[n..] == rest;
  }
  case FStrLP(lw, e) => {
    var hdr := EncNat(|v.bs|, lw, e);
    assert whole == hdr + v.bs + rest;
    assert whole[..lw] == hdr;
    EncDecNat(|v.bs|, lw, e);
    assert whole[lw..lw + |v.bs|] == v.bs;
    assert whole[lw + |v.bs|..] == rest;
  }
  case FStrZ => {
    FindZeroAppend(v.bs, rest);
    assert whole == v.bs + [0] + rest;
    assert whole[..|v.bs|] == v.bs;
    assert whole[|v.bs| + 1..] == rest;
  }
  case FRepLit(c, ew, e) => {
    EncDecList(v.l, ew, e, rest);
  }
  case FRepRef(lw, ew, e) => {
    var hdr := EncNat(|v.l|, lw, e);
    var body := EncList(v.l, ew, e);
    assert whole == hdr + body + rest;
    assert whole[..lw] == hdr;
    EncDecNat(|v.l|, lw, e);
    assert whole[lw..] == body + rest;
    EncDecList(v.l, ew, e, rest);
  }
}

// ------------------------------------------------------------ full record

ghost predicate WfSpec(fs: seq<F>) {
  forall i :: 0 <= i < |fs| ==> WfF(fs[i])
}

ghost predicate ValidVals(fs: seq<F>, vs: seq<V>) {
  |vs| == |fs| && forall i :: 0 <= i < |fs| ==> ValidV(fs[i], vs[i])
}

function EncAll(fs: seq<F>, vs: seq<V>): seq<byte>
  requires WfSpec(fs) && ValidVals(fs, vs)
{
  if |fs| == 0 then [] else EncF(fs[0], vs[0]) + EncAll(fs[1..], vs[1..])
}

function DecAll(fs: seq<F>, bs: seq<byte>): Res
  requires WfSpec(fs)
{
  if |fs| == 0 then Some([], bs)
  else
    match DecF(fs[0], bs)
    case FNone => None
    case FSome(v, rest) =>
      match DecAll(fs[1..], rest)
      case None => None
      case Some(vs, rest') => Some([v] + vs, rest')
}

lemma RecordRT(fs: seq<F>, vs: seq<V>, rest: seq<byte>)
  requires WfSpec(fs) && ValidVals(fs, vs)
  ensures DecAll(fs, EncAll(fs, vs) + rest) == Some(vs, rest)
{
  if |fs| == 0 {
    assert EncAll(fs, vs) + rest == rest;
  } else {
    var enc0 := EncF(fs[0], vs[0]);
    var encT := EncAll(fs[1..], vs[1..]);
    assert EncAll(fs, vs) + rest == enc0 + (encT + rest);
    FieldRT(fs[0], vs[0], encT + rest);
    RecordRT(fs[1..], vs[1..], rest);
    assert [vs[0]] + vs[1..] == vs;
  }
}

// Truncation rejection: decoding any strict prefix of an encoding fails.
lemma FieldTrunc(f: F, v: V, pre: seq<byte>)
  requires WfF(f) && ValidV(f, v)
  requires pre <= EncF(f, v) && |pre| < |EncF(f, v)|
  ensures DecF(f, pre) == FNone
{
  var enc := EncF(f, v);
  match f
  case FUint(w, e) => {}
  case FSint(w, e) => {}
  case FMagic(m) => {
    if |pre| >= |m| {
      assert |enc| == |m|;
      assert false;
    }
  }
  case FStrFixed(n) => {}
  case FStrLP(lw, e) => {
    if |pre| >= lw {
      var hdr := EncNat(|v.bs|, lw, e);
      assert pre[..lw] == enc[..lw] == hdr;
      EncDecNat(|v.bs|, lw, e);
      assert |pre| - lw < |v.bs|;
    }
  }
  case FStrZ => {
    assert enc == v.bs + [0];
    assert forall k :: 0 <= k < |pre| ==> pre[k] == enc[k];
    assert forall k :: 0 <= k < |pre| ==> pre[k] != 0;
    assert FindZero(pre) == -1;
  }
  case FRepLit(c, ew, e) => {
    TruncList(v.l, ew, e, pre, c);
  }
  case FRepRef(lw, ew, e) => {
    if |pre| >= lw {
      var hdr := EncNat(|v.l|, lw, e);
      assert pre[..lw] == enc[..lw] == hdr;
      EncDecNat(|v.l|, lw, e);
      assert pre[lw..] <= EncList(v.l, ew, e);
      TruncList(v.l, ew, e, pre[lw..], |v.l|);
    }
  }
}

lemma TruncList(l: seq<nat>, ew: nat, e: End, pre: seq<byte>, c: nat)
  requires ew >= 1 && forall k :: 0 <= k < |l| ==> l[k] < Pow256(ew)
  requires c == |l|
  requires pre <= EncList(l, ew, e) && |pre| < |EncList(l, ew, e)|
  ensures DecList(pre, c, ew, e) == LNone
{
  if c == 0 {
  } else if |pre| < ew {
  } else {
    var h := EncNat(l[0], ew, e);
    var t := EncList(l[1..], ew, e);
    assert EncList(l, ew, e) == h + t;
    assert pre[..ew] == h;
    assert pre[ew..] <= t;
    TruncList(l[1..], ew, e, pre[ew..], c - 1);
  }
}

lemma RecordTrunc(fs: seq<F>, vs: seq<V>, pre: seq<byte>)
  requires WfSpec(fs) && ValidVals(fs, vs)
  requires pre <= EncAll(fs, vs) && |pre| < |EncAll(fs, vs)|
  ensures DecAll(fs, pre) == None
{
  if |fs| == 0 {
  } else {
    var enc0 := EncF(fs[0], vs[0]);
    var encT := EncAll(fs[1..], vs[1..]);
    assert EncAll(fs, vs) == enc0 + encT;
    if |pre| < |enc0| {
      FieldTrunc(fs[0], vs[0], pre);
      assert DecF(fs[0], pre) == FNone;
    } else {
      var tail := pre[|enc0|..];
      assert pre[..|enc0|] == enc0;
      assert pre == pre[..|enc0|] + tail;
      assert pre == enc0 + tail;
      FieldRT(fs[0], vs[0], tail);
      assert DecF(fs[0], pre) == FSome(vs[0], tail);
      assert tail <= encT;
      assert |tail| < |encT|;
      RecordTrunc(fs[1..], vs[1..], tail);
      assert DecAll(fs[1..], tail) == None;
    }
  }
}

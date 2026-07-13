"""An independent reference codec generator -- path (i).

This is a second, from-scratch Spec->Code derivation that shares NO code with
Kaitai Struct.  Given the same SpecModel it produces a codec with the same
wire format, implemented directly over Python byte operations.  Because its
implementation is independent of Kaitai's compiler, its bugs are
uncorrelated with Kaitai's -- so a behavioral differential between the two
codecs catches "jointly-consistent-but-wrong" errors that the round-trip
oracle (encode/decode of a single codec) structurally cannot: a codec can be
internally round-trip-consistent yet wrong about the wire format, and only a
comparison against an independent implementation exposes it.

The reference codec is a fixed, trusted interpreter parametrized by the field
descriptors -- it is not emitted by the LLM and not derived from Kaitai.  The
differential harness drives both codecs from the same spec-generated logical
values (Hypothesis, never the LLM) inside the sandbox.
"""
from __future__ import annotations

from .ksy_model import SpecModel, Field
from . import harness_gen


def serialize_fields(spec: SpecModel) -> list:
    out = []
    for f in spec.fields:
        out.append({
            "kind": f.kind, "id": f.id, "width": f.width, "endian": f.endian,
            "magic": list(f.magic), "size": f.size, "lenwidth": f.lenwidth,
            "enum_values": f.enum_values,
        })
    return out


# --- the reference interpreter (also shipped into the sandbox as ref.py) ---
_REF_RUNTIME = r'''
"""Independent reference codec interpreter (no Kaitai)."""

def _end(e):
    return "big" if e == "be" else "little"

def _take(raw, pos, n):
    if n < 0 or pos + n > len(raw):
        raise ValueError("short read")
    return raw[pos:pos + n], pos + n

def encode_ref(fields, vals):
    out = bytearray()
    for f in fields:
        k = f["kind"]; fid = f["id"]
        if k == "uint":
            v = int(vals[fid])
            if not 0 <= v < 256 ** f["width"]:
                raise ValueError("uint out of range")
            out += v.to_bytes(f["width"], _end(f["endian"]))
        elif k == "sint":
            v = int(vals[fid]); w = f["width"]
            if not -(256 ** w // 2) <= v < 256 ** w // 2:
                raise ValueError("sint out of range")
            if v < 0:
                v += 256 ** w
            out += v.to_bytes(w, _end(f["endian"]))
        elif k == "magic":
            out += bytes(f["magic"])
        elif k == "str_fixed":
            b = vals[fid].encode("ascii")
            if len(b) != f["size"]:
                raise ValueError("str_fixed wrong size")
            out += b
        elif k == "str_lenprefix":
            b = vals[fid].encode("ascii")
            if len(b) >= 256 ** f["lenwidth"]:
                raise ValueError("str too long for length prefix")
            out += len(b).to_bytes(f["lenwidth"], _end(f["endian"])) + b
        elif k == "strz":
            b = vals[fid].encode("ascii")
            if 0 in b:
                raise ValueError("embedded NUL in strz")
            out += b + b"\x00"
        elif k == "repeat_lit":
            lst = vals[fid]
            if len(lst) != f["size"]:
                raise ValueError("repeat_lit wrong count")
            for e in lst:
                out += int(e).to_bytes(f["width"], _end(f["endian"]))
        elif k == "repeat_ref":
            lst = vals[fid]
            if len(lst) >= 256 ** f["lenwidth"]:
                raise ValueError("repeat too long for count prefix")
            out += len(lst).to_bytes(f["lenwidth"], _end(f["endian"]))
            for e in lst:
                out += int(e).to_bytes(f["width"], _end(f["endian"]))
        else:
            raise ValueError("unknown kind " + k)
    return bytes(out)

def decode_ref(fields, raw):
    pos = 0; vals = {}
    for f in fields:
        k = f["kind"]; fid = f["id"]
        if k == "uint":
            b, pos = _take(raw, pos, f["width"])
            vals[fid] = int.from_bytes(b, _end(f["endian"]))
        elif k == "sint":
            w = f["width"]; b, pos = _take(raw, pos, w)
            u = int.from_bytes(b, _end(f["endian"]))
            vals[fid] = u - 256 ** w if u >= 256 ** w // 2 else u
        elif k == "magic":
            m = bytes(f["magic"]); b, pos = _take(raw, pos, len(m))
            if b != m:
                raise ValueError("magic mismatch")
            # magic carries no value
        elif k == "str_fixed":
            b, pos = _take(raw, pos, f["size"])
            vals[fid] = b.decode("ascii")
        elif k == "str_lenprefix":
            lb, pos = _take(raw, pos, f["lenwidth"])
            n = int.from_bytes(lb, _end(f["endian"]))
            b, pos = _take(raw, pos, n)
            vals[fid] = b.decode("ascii")
        elif k == "strz":
            z = raw.find(0, pos)
            if z < 0:
                raise ValueError("no NUL terminator")
            vals[fid] = raw[pos:z].decode("ascii"); pos = z + 1
        elif k == "repeat_lit":
            lst = []
            for _ in range(f["size"]):
                b, pos = _take(raw, pos, f["width"])
                lst.append(int.from_bytes(b, _end(f["endian"])))
            vals[fid] = lst
        elif k == "repeat_ref":
            cb, pos = _take(raw, pos, f["lenwidth"])
            c = int.from_bytes(cb, _end(f["endian"])); lst = []
            for _ in range(c):
                b, pos = _take(raw, pos, f["width"])
                lst.append(int.from_bytes(b, _end(f["endian"])))
            vals[fid] = lst
        else:
            raise ValueError("unknown kind " + k)
    return vals
'''


def ref_module_source() -> str:
    return _REF_RUNTIME


# expose for in-process demos/tests
_ns = {}
exec(_REF_RUNTIME, _ns)
encode_ref = _ns["encode_ref"]
decode_ref = _ns["decode_ref"]


def _val_expr(f: Field) -> str:
    """How to read a field's logical value out of the kaitai-decoded object,
    normalized to the same Python type the reference codec uses."""
    if f.kind == "uint" and f.enum_values is not None:
        return f"int(dec.{f.id})"
    return f"dec.{f.id}"


def build_differential_harness(spec: SpecModel, max_examples: int = 100,
                               ref_fields: list = None) -> str:
    """Differential harness.  The Kaitai side and the Hypothesis value
    strategies come from `spec`; the reference-codec side uses `ref_fields`
    when supplied (an *independently derived* field list, e.g. the ABNF
    reference route) instead of serialize_fields(spec).  A divergence between
    the two independently-derived field lists surfaces as a byte mismatch."""
    cls = harness_gen._class_name(spec.id)
    args = [f"v_{f.id}={harness_gen._strategy(f)}" for f in spec.fields]
    # non-magic fields carry values; magic fields are implicit
    valued = [f for f in spec.fields if f.kind != "magic"]
    fields_literal = ref_fields if ref_fields is not None else serialize_fields(spec)

    lines = [
        "import io, json, sys, traceback",
        "from hypothesis import given, settings, strategies as st, HealthCheck",
        "from kaitaistruct import KaitaiStream",
        f"from {spec.id} import {cls}",
        "from ref import encode_ref, decode_ref",
        f"PRINTABLE = {harness_gen.PRINTABLE!r}",
        f"FIELDS = {fields_literal!r}",
        "",
        "def kai_encode(vals):",
        f"    obj = {cls}()",
    ]
    for f in spec.fields:
        if f.kind == "magic":
            # Kaitai read-write _check() reads the contents attribute, so it
            # must be set (to its fixed bytes) even though it carries no value.
            lines.append(f"    obj.{f.id} = {bytes(f.magic)!r}")
            continue
        val = f"vals[{f.id!r}]"
        if f.kind in ("str_lenprefix", "repeat_ref"):
            lines.append(f"    obj.{f.lenfield} = len({val})")
            lines.append(f"    obj.{f.id} = {val}")
        elif f.kind == "uint" and f.enum_values is not None:
            ecls = cls + "." + harness_gen._class_name(f.enum_name)
            lines.append(f"    obj.{f.id} = {ecls}({val})")
        else:
            lines.append(f"    obj.{f.id} = {val}")
    lines += [
        "    obj._check()",
        "    ks = KaitaiStream(io.BytesIO(bytearray(1 << 20)))",
        "    obj._write(ks)",
        "    return ks.to_byte_array()[:ks.pos()]",
        "",
        "def kai_decode(raw):",
        f"    dec = {cls}.from_bytes(raw); dec._read()",
        "    return {" + ", ".join(
            f"{f.id!r}: {_val_expr(f)}" for f in valued) + "}",
        "",
        f"@settings(max_examples={max_examples}, derandomize=True, database=None,"
        " deadline=None, suppress_health_check=list(HealthCheck))",
        f"@given({', '.join(args)})",
        f"def prop({', '.join('v_' + f.id for f in spec.fields)}):",
        "    vals = {" + ", ".join(
            f"{f.id!r}: v_{f.id}" for f in valued) + "}",
        "    enc_ref = encode_ref(FIELDS, vals)",
        "    enc_kai = kai_encode(vals)",
        "    # CHANNEL (i): two independent implementations must agree on bytes",
        "    assert enc_ref == enc_kai, ('encoder-divergence', enc_ref.hex(),"
        " enc_kai.hex(), repr(vals)[:200])",
        "    # cross-decode: each implementation decodes the other's bytes",
        "    assert kai_decode(enc_ref) == vals, ('kaitai-cannot-decode-ref',"
        " enc_ref.hex())",
        "    assert decode_ref(FIELDS, enc_kai) == vals, ('ref-cannot-decode-kaitai',"
        " enc_kai.hex())",
        "",
        "def main():",
        "    try:",
        "        prop()",
        f"        print(json.dumps({{'status': 'pass', 'examples': {max_examples}}}))",
        "    except BaseException as e:",
        "        print(json.dumps({'status': 'fail', 'error': repr(e)[:2000],",
        "                          'traceback': traceback.format_exc()[-2500:]}))",
        "        sys.exit(1)",
        "",
        "main()",
    ]
    return "\n".join(lines) + "\n"

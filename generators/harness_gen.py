"""Deterministic derivation of a Hypothesis test harness from a SpecModel.

The harness is *derived from the task spec by fixed code* -- the LLM never
authors test inputs (anti-goal #1).  Hypothesis runs derandomized with a
fixed seed, so the whole task-time path stays deterministic.

The harness checks, against the actual emitted codec, executed only inside
the sandbox:

  P1 round-trip     : decode(encode(vals)) == vals, and re-encode is
                      byte-identical (canonicality);
  P2 truncation     : every strict prefix of a valid encoding is rejected
                      (the generic model proves this must hold: RecordTrunc);
  P3 magic corruption: flipping a magic byte is rejected;
  P4 length overrun : inflating a length prefix is rejected.

Protocol: prints one JSON line {"status": "pass", "examples": N} or
{"status": "fail", "property": ..., "transcript": {...}} and exits 0/1.
"""
from __future__ import annotations

from .ksy_model import SpecModel, Field

PRINTABLE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.:"


def _strategy(f: Field) -> str:
    if f.kind == "uint":
        if f.enum_values is not None:
            return f"st.sampled_from({f.enum_values!r})"
        return f"st.integers(0, {256 ** f.width - 1})"
    if f.kind == "sint":
        half = 256 ** f.width // 2
        return f"st.integers({-half}, {half - 1})"
    if f.kind == "magic":
        return f"st.just({f.magic!r})"
    if f.kind == "str_fixed":
        return f"st.text(alphabet=PRINTABLE, min_size={f.size}, max_size={f.size})"
    if f.kind == "str_lenprefix":
        mx = min(256 ** f.lenwidth - 1, 64)
        return f"st.text(alphabet=PRINTABLE, min_size=0, max_size={mx})"
    if f.kind == "strz":
        return "st.text(alphabet=PRINTABLE, min_size=0, max_size=64)"
    if f.kind == "repeat_lit":
        return (f"st.lists(st.integers(0, {256 ** f.width - 1}), "
                f"min_size={f.size}, max_size={f.size})")
    if f.kind == "repeat_ref":
        mx = min(256 ** f.lenwidth - 1, 32)
        return (f"st.lists(st.integers(0, {256 ** f.width - 1}), "
                f"min_size=0, max_size={mx})")
    raise ValueError(f.kind)


def _class_name(sid: str) -> str:
    return "".join(p.capitalize() for p in sid.split("_"))


def build_harness(spec: SpecModel, max_examples: int = 100) -> str:
    cls = _class_name(spec.id)
    sets, gets, args = [], [], []
    for f in spec.fields:
        argn = f"v_{f.id}"
        val = f"vals[{argn!r}]"
        args.append(f"{argn}={_strategy(f)}")
        if f.kind in ("str_lenprefix", "repeat_ref"):
            sets.append(f"    obj.{f.lenfield} = len({val})")
            sets.append(f"    obj.{f.id} = {val}")
        elif f.kind == "uint" and f.enum_values is not None:
            ecls = _class_name(spec.id) + "." + _class_name(f.enum_name)
            sets.append(f"    obj.{f.id} = {ecls}({val})")
        else:
            sets.append(f"    obj.{f.id} = {val}")
        if f.kind == "uint" and f.enum_values is not None:
            gets.append(f"    got_{f.id} = int(dec.{f.id})")
        else:
            gets.append(f"    got_{f.id} = dec.{f.id}")
        gets.append(
            f"    assert got_{f.id} == {argn}, "
            f"('field {f.id}', got_{f.id}, {argn})")

    magic_fields = [f for f in spec.fields if f.kind == "magic"]
    has_lenprefix = any(f.kind in ("str_lenprefix", "repeat_ref")
                        for f in spec.fields)

    lines = [
        "import io, json, sys, traceback",
        "from hypothesis import given, settings, strategies as st, HealthCheck",
        "from kaitaistruct import KaitaiStream",
        f"from {spec.id} import {cls}",
        f"PRINTABLE = {PRINTABLE!r}",
        "",
        "def encode(**vals):",
        f"    obj = {cls}()",
    ]
    lines += [s.replace("    obj", "    obj", 1) for s in sets]
    lines += [
        "    obj._check()",
        "    ks = KaitaiStream(io.BytesIO(bytearray(1 << 20)))",
        "    obj._write(ks)",
        "    return ks.to_byte_array()[:ks.pos()]",
        "",
        "def decode(raw):",
        f"    obj = {cls}.from_bytes(raw)",
        "    obj._read()",
        "    return obj",
        "",
        "FAIL = {}",
        "",
        f"@settings(max_examples={max_examples}, derandomize=True, database=None,"
        " deadline=None, suppress_health_check=list(HealthCheck))",
        f"@given({', '.join(args)})",
        f"def prop_all({', '.join('v_' + f.id for f in spec.fields)}):",
        "    kw = dict(" + ", ".join(f"{'v_'+f.id}={'v_'+f.id}" for f in spec.fields) + ")",
        "    enc = encode(**kw)",
        "    # P1: round-trip",
        "    dec = decode(enc)",
    ]
    lines += gets
    lines += [
        "    # P1b: canonical re-encode of the decoded object",
        "    kw2 = {}",
    ]
    for f in spec.fields:
        if f.kind == "uint" and f.enum_values is not None:
            lines.append(f"    kw2['v_{f.id}'] = int(dec.{f.id})")
        else:
            lines.append(f"    kw2['v_{f.id}'] = dec.{f.id}")
    lines += [
        "    enc2 = encode(**kw2)",
        "    assert enc2 == enc, ('non-canonical re-encode', enc.hex(), enc2.hex())",
        "    # P2: every strict prefix must be rejected",
        "    cuts = range(len(enc)) if len(enc) <= 48 else "
        "list(range(0, len(enc), max(1, len(enc)//32))) + [len(enc)-1]",
        "    for k in cuts:",
        "        try:",
        "            decode(enc[:k])",
        "        except Exception:",
        "            pass",
        "        else:",
        "            raise AssertionError(('truncated input accepted', k, enc[:k].hex()))",
    ]
    if magic_fields:
        lines += [
            "    # P3: corrupt magic must be rejected",
            "    b = bytearray(enc)",
        ]
        # magic offset is well-defined only if no variable-length field precedes it;
        # compute at generation time when possible, else corrupt first byte only
        # when the first field is magic.
        off = 0
        fixed_so_far = True
        for f in spec.fields:
            if f.kind == "magic" and fixed_so_far:
                lines += [
                    f"    b[{off}] ^= 0xFF",
                    "    try:",
                    "        decode(bytes(b))",
                    "    except Exception:",
                    "        pass",
                    "    else:",
                    "        raise AssertionError(('corrupt magic accepted', bytes(b).hex()))",
                    f"    b[{off}] ^= 0xFF",
                ]
            if f.kind == "uint" or f.kind == "sint":
                off += f.width
            elif f.kind == "magic":
                off += len(f.magic)
            elif f.kind == "str_fixed":
                off += f.size
            elif f.kind == "repeat_lit":
                off += f.size * f.width
            else:
                fixed_so_far = False
    if has_lenprefix:
        lines += [
            "    # P4: inflated length prefix must be rejected",
            "    b = bytearray(enc)",
        ]
        off_expr = "0"
        fixed = True
        for f in spec.fields:
            if f.kind in ("str_lenprefix", "repeat_ref") and fixed:
                # bump the last byte of the length prefix if not at max
                pos = f"({off_expr}) + {f.lenwidth - 1 if f.endian == 'be' else 0}"
                lines += [
                    f"    if b[{pos}] != 0xFF:",
                    f"        b[{pos}] += 1",
                    "        try:",
                    "            decode(bytes(b))",
                    "        except Exception:",
                    "            pass",
                    "        else:",
                    "            raise AssertionError(('inflated length accepted',"
                    " bytes(b).hex()))",
                    f"        b[{pos}] -= 1",
                ]
                break  # only the first variable-length field has a static offset
            if f.kind in ("uint", "sint"):
                off_expr += f" + {f.width}"
            elif f.kind == "magic":
                off_expr += f" + {len(f.magic)}"
            elif f.kind == "str_fixed":
                off_expr += f" + {f.size}"
            elif f.kind == "repeat_lit":
                off_expr += f" + {f.size * f.width}"
            else:
                fixed = False
    lines += [
        "",
        "def main():",
        "    try:",
        "        prop_all()",
        f"        print(json.dumps({{'status': 'pass', 'examples': {max_examples}}}))",
        "    except BaseException as e:",
        "        tb = traceback.format_exc()",
        "        print(json.dumps({'status': 'fail', 'property': 'codec-roundtrip',",
        "                          'error': repr(e)[:2000], 'traceback': tb[-3000:]}))",
        "        sys.exit(1)",
        "",
        "main()",
    ]
    return "\n".join(lines) + "\n"

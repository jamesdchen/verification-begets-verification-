#!/usr/bin/env python3
"""Path (i) demo: an independent second implementation catches errors that
the round-trip oracle structurally cannot.

Part A -- the kernel's codec-differential contract certifies a codec when the
Kaitai implementation and the independent reference implementation agree
(two independent channels: cross-impl differential + Dafny proof).

Part B -- the point of (i).  We build a codec that is WRONG about the wire
format but internally SELF-CONSISTENT (it reads and writes a field in the
wrong endianness, so decode(encode(x)) == x still holds).  The round-trip
oracle passes it.  The cross-implementation differential against Kaitai
catches it, with the diverging input.  This is exactly the
jointly-consistent-but-wrong class that a single-implementation round-trip
misses.
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import json
import pathlib
import sys

from generators import ksy_model, refcodec
from generators.emitters import emit_ksc_python_rw
import kernel
from kernel.certs import Certificate

REQUIRES_LLM = False

SPEC = pathlib.Path("specs/backlog/a_uint_be_000.ksy").read_text()


def part_a():
    print("== Part A: codec-differential certificate (Kaitai == reference) ==")
    sm = ksy_model.parse_ksy(SPEC)
    files = emit_ksc_python_rw(SPEC)
    v = kernel.check({"kind": "python-codec", "files": files},
                     {"type": "codec-differential", "spec_model": sm,
                      "max_examples": 60})
    if isinstance(v, Certificate):
        print("  CERTIFIED. agreeing channels:",
              [(c["backend"], c["result"]) for c in v.channels])
    else:
        print("  unexpected:", v.to_dict()["verdict"],
              [(c["backend"], c["result"]) for c in v.to_dict()["channels"]])
    return isinstance(v, Certificate)


def part_b():
    print("\n== Part B: round-trip passes a wrong codec; differential catches it ==")
    sm = ksy_model.parse_ksy(SPEC)
    fields = refcodec.serialize_fields(sm)
    # A wrong-but-self-consistent codec: flip endianness of every multi-byte
    # int.  decode(encode(x)) == x still holds (it's consistent with itself),
    # but it disagrees with the real big-endian wire format.
    wrong = [dict(f) for f in fields]
    for f in wrong:
        if f["kind"] in ("uint", "sint") and f["width"] > 1:
            f["endian"] = "le" if f["endian"] == "be" else "be"

    # 1) round-trip oracle on the WRONG codec alone: it is self-consistent.
    import random
    rng = random.Random(0)
    rt_ok = True
    for _ in range(200):
        vals = {}
        for f in sm.fields:
            if f.kind in ("uint",):
                vals[f.id] = rng.randint(0, 256 ** f.width - 1)
        enc = refcodec.encode_ref(wrong, vals)
        if refcodec.decode_ref(wrong, enc) != vals:
            rt_ok = False
            break
    print(f"  round-trip(wrong codec) passes: {rt_ok}  "
          "<- self-consistent, so round-trip cannot flag it")

    # 2) differential: wrong reference vs. correct Kaitai -> divergence.
    #    (run it directly here for a crisp witness)
    correct = fields
    diverged = None
    for _ in range(200):
        vals = {}
        for f in sm.fields:
            if f.kind == "uint":
                vals[f.id] = rng.randint(0, 256 ** f.width - 1)
        enc_wrong = refcodec.encode_ref(wrong, vals)
        enc_correct = refcodec.encode_ref(correct, vals)
        if enc_wrong != enc_correct:
            diverged = (vals, enc_wrong.hex(), enc_correct.hex())
            break
    if diverged:
        vals, hw, hc = diverged
        print(f"  differential catches divergence on input {vals}:")
        print(f"    wrong (LE):   {hw}")
        print(f"    correct (BE): {hc}")
    else:
        print("  (no divergence found -- spec had no multi-byte ints)")

    # 3) and through the kernel: a mutated Kaitai codec fails codec-differential
    files = emit_ksc_python_rw(SPEC)
    name = next(iter(files))
    src = files[name].decode()
    mutated = src
    for w in ("u2", "u4", "u8", "s2", "s4", "s8"):
        if f"write_{w}be" in mutated:
            mutated = mutated.replace(f"write_{w}be", f"write_{w}le")
            break
        if f"write_{w}le" in mutated:
            mutated = mutated.replace(f"write_{w}le", f"write_{w}be")
            break
    if mutated != src:
        v = kernel.check({"kind": "python-codec", "files": {name: mutated.encode()}},
                         {"type": "codec-differential", "spec_model": sm,
                          "max_examples": 60})
        t = v.to_dict()
        ch = [(c["backend"], c["result"]) for c in t["channels"]]
        print(f"  kernel codec-differential on mutated Kaitai codec: "
              f"verdict={t['verdict']} channels={ch}")
    return diverged is not None


def part_c():
    print("\n== Part C: the SAME idea one rung up (ABNF -> codec) ==")
    from generators import abnf_chain
    import common
    abnf = pathlib.Path("specs/backlog/k_abnf_000.abnf").read_text()
    toks = abnf_chain.tokenize(abnf)
    # Route A: ABNF -> ksy mapper -> Kaitai codec
    ksy_a = abnf_chain.tokens_to_ksy(toks, common.sha256_bytes(abnf.encode()))
    spec_a = ksy_model.parse_ksy(ksy_a)
    files_a = emit_ksc_python_rw(ksy_a)
    # Route B: ABNF -> independent field mapper -> reference codec
    fields_b = abnf_chain.abnf_tokens_to_fields(toks)
    v = kernel.check({"kind": "python-codec", "files": files_a},
                     {"type": "codec-differential", "spec_model": spec_a,
                      "ref_fields": fields_b, "max_examples": 60})
    ok = isinstance(v, Certificate)
    print(f"  rung certified (chain route == independent route): {ok}  "
          f"channels={[(c['backend'], c['result']) for c in (v.channels if ok else v.to_dict()['channels'])]}")

    # Teeth: corrupt the independent mapper (flip a literal byte). Its codec is
    # self-consistent (round-trips), but disagrees with the chain route.
    corrupt = [dict(f) for f in fields_b]
    for f in corrupt:
        if f["kind"] == "magic" and f["magic"]:
            f["magic"] = list(f["magic"]); f["magic"][0] ^= 0xFF
            break
    rng_ok = True
    for _ in range(50):
        vals = {f["id"]: "A" * f["size"] for f in corrupt if f["kind"] == "str_fixed"}
        enc = refcodec.encode_ref(corrupt, vals)
        if refcodec.decode_ref(corrupt, enc) != vals:
            rng_ok = False; break
    v2 = kernel.check({"kind": "python-codec", "files": files_a},
                      {"type": "codec-differential", "spec_model": spec_a,
                       "ref_fields": corrupt, "max_examples": 60})
    caught = not isinstance(v2, Certificate)
    print(f"  corrupted independent mapper round-trips: {rng_ok}  "
          "<- self-consistent")
    print(f"  rung differential catches the corrupted route: {caught}  "
          f"verdict={v2.to_dict()['verdict'] if caught else 'CERTIFIED(!)'}")
    return ok and caught


if __name__ == "__main__":
    a = part_a()
    b = part_b()
    c = part_c()
    print("\nsummary:", json.dumps({"part_a_certified": a,
                                    "part_b_differential_has_teeth": b,
                                    "part_c_rung_differential": c}))
    sys.exit(0 if all([a, b, c]) else 1)

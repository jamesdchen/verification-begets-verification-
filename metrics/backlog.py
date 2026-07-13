"""Fixed backlog of ~200 programmatically varied codec/format task specs.

All specs are written in existing spec languages (.ksy, ABNF).  Generation
is seeded and deterministic; the spec files are committed under
specs/backlog/ so every run measures against the same backlog.
"""
from __future__ import annotations

import pathlib
import random

import common

SEED = 20260713
FAMILIES = [
    ("a_uint_be", 30), ("b_uint_le", 25), ("c_magic", 25),
    ("d_strfixed", 20), ("e_lenprefix", 25), ("f_repeat", 25),
    ("g_enum", 20), ("h_sint", 15), ("k_abnf", 15),
]  # = 200

_WIDTHS = [1, 2, 4, 8]


def _uints(rng, n, signed_ok=False):
    lines = []
    for i in range(n):
        w = rng.choice(_WIDTHS)
        t = ("s" if signed_ok and rng.random() < 0.5 else "u") + str(w)
        lines += [f"  - id: f{i}", f"    type: {t}"]
    return lines


def _ksy(sid, endian, body_lines, enums=None):
    lines = ["meta:", f"  id: {sid}", f"  endian: {endian}", "seq:"] + body_lines
    if enums:
        lines += enums
    return "\n".join(lines) + "\n"


def _gen_family(fam, idx, rng):
    sid = f"{fam}_{idx:03d}"
    if fam == "a_uint_be":
        return sid + ".ksy", _ksy(sid, "be", _uints(rng, rng.randint(1, 6)))
    if fam == "b_uint_le":
        return sid + ".ksy", _ksy(sid, "le", _uints(rng, rng.randint(1, 6)))
    if fam == "c_magic":
        magic = "".join(rng.choice("ABCDEFGHKLMPQRSTVWXZ")
                        for _ in range(rng.randint(2, 4)))
        body = ["  - id: magic", f"    contents: {magic}"] + \
            _uints(rng, rng.randint(1, 4))
        return sid + ".ksy", _ksy(sid, "be", body)
    if fam == "d_strfixed":
        body = _uints(rng, rng.randint(0, 2)) if rng.random() < 0.7 else []
        for j in range(rng.randint(1, 3)):
            body += [f"  - id: s{j}", "    type: str",
                     f"    size: {rng.randint(1, 16)}",
                     "    encoding: ASCII"]
        if not body:
            body = _uints(rng, 1)
        return sid + ".ksy", _ksy(sid, "be", body)
    if fam == "e_lenprefix":
        endian = rng.choice(["be", "le"])
        lw = rng.choice([1, 2])
        body = _uints(rng, rng.randint(0, 2))
        body += [f"  - id: len_data", f"    type: u{lw}",
                 "  - id: data", "    type: str", "    size: len_data",
                 "    encoding: ASCII"]
        return sid + ".ksy", _ksy(sid, endian, body)
    if fam == "f_repeat":
        endian = rng.choice(["be", "le"])
        ew = rng.choice(_WIDTHS)
        if rng.random() < 0.5:
            body = [f"  - id: items", f"    type: u{ew}",
                    "    repeat: expr",
                    f"    repeat-expr: {rng.randint(1, 8)}"]
        else:
            lw = rng.choice([1, 2])
            body = [f"  - id: num_items", f"    type: u{lw}",
                    f"  - id: items", f"    type: u{ew}",
                    "    repeat: expr", "    repeat-expr: num_items"]
        body = _uints(rng, rng.randint(0, 2)) + body
        return sid + ".ksy", _ksy(sid, endian, body)
    if fam == "g_enum":
        vals = sorted(rng.sample(range(1, 200), rng.randint(2, 5)))
        enums = ["enums:", "  kind:"]
        for v in vals:
            enums.append(f"    {v}: v{v}")
        body = ["  - id: kind_field", "    type: u1", "    enum: kind"] + \
            _uints(rng, rng.randint(1, 3))
        return sid + ".ksy", _ksy(sid, "be", body, enums)
    if fam == "h_sint":
        return sid + ".ksy", _ksy(sid, "be",
                                  _uints(rng, rng.randint(1, 5), signed_ok=True))
    if fam == "k_abnf":
        parts = []
        lit = "".join(rng.choice("ABCDEFGHKLMNPRSTVWXZ")
                      for _ in range(rng.randint(2, 4)))
        parts.append(f'"{lit}"')
        for _ in range(rng.randint(1, 4)):
            kind = rng.choice(["DIGIT", "HEXDIG", "ALPHA"])
            parts.append(f"{rng.randint(1, 8)}{kind}")
            if rng.random() < 0.5:
                parts.append("SP")
        parts.append("CRLF")
        return sid + ".abnf", f"record = {' '.join(parts)}\n"
    raise ValueError(fam)


def generate(out_dir=None) -> pathlib.Path:
    out = pathlib.Path(out_dir or common.REPO_ROOT / "specs" / "backlog")
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    n = 0
    for fam, count in FAMILIES:
        for i in range(count):
            name, text = _gen_family(fam, i, rng)
            (out / name).write_text(text)
            n += 1
    return out

"""Model of the .ksy subset used by the codec seed domain.

A task spec is a Kaitai Struct .ksy file (an *existing*, documented spec
language -- we did not design it).  This module:

  * parses a .ksy into an ordered list of field descriptors,
  * extracts the spec's *feature atoms* (the vocabulary that generator
    spec-grammars are written in),
  * rejects anything outside the modeled subset (such specs simply become
    permanent coverage misses).

Feature atoms (the complete vocabulary):

  endian:be endian:le
  uint:1 uint:2 uint:4 uint:8
  sint:1 sint:2 sint:4 sint:8
  magic                str-fixed          strz
  str-lenprefix:1 str-lenprefix:2
  repeat:lit           repeat:ref
  enum

A generator's spec grammar is a set of atoms; it covers a spec iff the
spec's atoms are a subset of the grammar's atoms.
"""
from __future__ import annotations

import dataclasses
import re
from typing import Optional

import yaml

UINT_TYPES = {"u1": 1, "u2": 2, "u4": 4, "u8": 8}
SINT_TYPES = {"s1": 1, "s2": 2, "s4": 4, "s8": 8}

ALL_ATOMS = (
    ["endian:be", "endian:le", "magic", "str-fixed", "strz",
     "str-lenprefix:1", "str-lenprefix:2", "repeat:lit", "repeat:ref", "enum"]
    + [f"uint:{w}" for w in (1, 2, 4, 8)]
    + [f"sint:{w}" for w in (1, 2, 4, 8)]
)


class UnsupportedSpec(Exception):
    """Spec uses constructs outside the modeled subset."""


@dataclasses.dataclass
class Field:
    kind: str            # uint sint magic str_fixed str_lenprefix strz repeat_lit repeat_ref
    id: str
    width: int = 0       # int width for uint/sint/enum elements
    endian: str = "be"
    magic: bytes = b""
    size: int = 0        # str_fixed size / repeat_lit count
    lenwidth: int = 0    # str_lenprefix / repeat_ref length-field width
    lenfield: str = ""   # id of the folded length field (harness must set it)
    enum_values: Optional[list] = None  # sorted allowed values when enum-typed
    enum_name: str = ""  # ksy enum name (for the generated Python enum class)


@dataclasses.dataclass
class SpecModel:
    id: str
    endian: str
    fields: list          # list[Field]
    atoms: frozenset
    source: str           # raw ksy text
    spec_hash: str = ""


def _int_type(t: str):
    if t in UINT_TYPES:
        return "uint", UINT_TYPES[t]
    if t in SINT_TYPES:
        return "sint", SINT_TYPES[t]
    return None, 0


def parse_ksy(text: str) -> SpecModel:
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise UnsupportedSpec(f"not valid YAML: {e}")
    if not isinstance(doc, dict) or "meta" not in doc or "seq" not in doc:
        raise UnsupportedSpec("ksy must have meta and seq sections")
    meta = doc["meta"]
    forbidden = {"process", "imports", "ks-opaque-types"}
    if forbidden & set(meta):
        raise UnsupportedSpec(f"forbidden meta keys: {forbidden & set(meta)}")
    if set(doc) - {"meta", "seq", "enums", "doc"}:
        raise UnsupportedSpec(f"unsupported top-level keys: {set(doc) - {'meta','seq','enums','doc'}}")
    sid = meta.get("id")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", sid or ""):
        raise UnsupportedSpec("meta.id missing or malformed")
    endian = meta.get("endian", "be")
    if endian not in ("be", "le"):
        raise UnsupportedSpec(f"unsupported endian {endian}")
    enums = doc.get("enums", {}) or {}

    atoms = set()
    fields: list[Field] = []
    seq = doc["seq"]
    if not isinstance(seq, list) or not seq:
        raise UnsupportedSpec("seq must be a non-empty list")
    ids = [e.get("id") for e in seq if isinstance(e, dict)]
    by_id = {e.get("id"): e for e in seq if isinstance(e, dict)}
    consumed_len_fields = set()

    # first pass: find pure length fields (referenced by a later size:/repeat-expr:)
    for e in seq:
        if not isinstance(e, dict):
            raise UnsupportedSpec("seq entries must be maps")
        ref = None
        if isinstance(e.get("size"), str):
            ref = e["size"].strip()
        if e.get("repeat") == "expr" and isinstance(e.get("repeat-expr"), str):
            ref = e["repeat-expr"].strip()
        if ref:
            if ref not in by_id:
                raise UnsupportedSpec(f"size/repeat-expr references unknown field {ref!r}")
            k, w = _int_type(by_id[ref].get("type", ""))
            if k != "uint":
                raise UnsupportedSpec(f"length field {ref!r} must be an unsigned int")
            consumed_len_fields.add(ref)

    for e in seq:
        fid = e.get("id")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", fid or ""):
            raise UnsupportedSpec(f"bad field id {fid!r}")
        keys = set(e) - {"id", "type", "contents", "size", "encoding", "enum",
                         "repeat", "repeat-expr", "terminator", "doc"}
        if keys:
            raise UnsupportedSpec(f"field {fid}: unsupported keys {keys}")
        if fid in consumed_len_fields:
            continue  # folded into the variable-length field that references it

        if "contents" in e:
            c = e["contents"]
            if isinstance(c, str):
                mb = c.encode("ascii")
            elif isinstance(c, list) and all(isinstance(x, int) and 0 <= x < 256 for x in c):
                mb = bytes(c)
            else:
                raise UnsupportedSpec(f"field {fid}: unsupported contents form")
            if not mb:
                raise UnsupportedSpec(f"field {fid}: empty contents")
            fields.append(Field(kind="magic", id=fid, magic=mb))
            atoms.add("magic")
            continue

        t = e.get("type")
        if e.get("repeat") == "expr":
            k, w = _int_type(t or "")
            if k != "uint":
                raise UnsupportedSpec(f"field {fid}: only unsigned-int repeats supported")
            if w > 1:
                atoms.add(f"endian:{endian}")
            rex = e["repeat-expr"]
            if isinstance(rex, int):
                if not 1 <= rex <= 64:
                    raise UnsupportedSpec(f"field {fid}: repeat count out of range")
                fields.append(Field(kind="repeat_lit", id=fid, width=w,
                                    endian=endian, size=rex))
                atoms.update({"repeat:lit", f"uint:{w}"})
            elif isinstance(rex, str) and rex.strip() in consumed_len_fields:
                lf = by_id[rex.strip()]
                lw = UINT_TYPES[lf["type"]]
                if lw > 1:
                    atoms.add(f"endian:{endian}")
                fields.append(Field(kind="repeat_ref", id=fid, width=w,
                                    endian=endian, lenwidth=lw,
                                    lenfield=rex.strip()))
                atoms.update({"repeat:ref", f"uint:{w}", f"uint:{lw}"})
            else:
                raise UnsupportedSpec(f"field {fid}: unsupported repeat-expr")
            continue

        if t == "str":
            if e.get("encoding", "ASCII").upper() not in ("ASCII", "UTF-8"):
                raise UnsupportedSpec(f"field {fid}: unsupported encoding")
            sz = e.get("size")
            if isinstance(sz, int):
                if not 1 <= sz <= 256:
                    raise UnsupportedSpec(f"field {fid}: str size out of range")
                fields.append(Field(kind="str_fixed", id=fid, size=sz))
                atoms.add("str-fixed")
            elif isinstance(sz, str) and sz.strip() in consumed_len_fields:
                lf = by_id[sz.strip()]
                lw = UINT_TYPES[lf["type"]]
                if lw > 1:
                    atoms.add(f"endian:{endian}")
                fields.append(Field(kind="str_lenprefix", id=fid, lenwidth=lw,
                                    endian=endian, lenfield=sz.strip()))
                atoms.update({f"str-lenprefix:{lw}", f"uint:{lw}"})
            else:
                raise UnsupportedSpec(f"field {fid}: str needs a size")
            continue

        if t == "strz":
            if e.get("encoding", "ASCII").upper() not in ("ASCII", "UTF-8"):
                raise UnsupportedSpec(f"field {fid}: unsupported encoding")
            fields.append(Field(kind="strz", id=fid))
            atoms.add("strz")
            continue

        k, w = _int_type(t or "")
        if k:
            enum_vals = None
            if "enum" in e:
                if k != "uint":
                    raise UnsupportedSpec(f"field {fid}: enum on non-uint")
                en = enums.get(e["enum"])
                if not isinstance(en, dict) or not en:
                    raise UnsupportedSpec(f"field {fid}: unknown enum {e['enum']!r}")
                enum_vals = sorted(int(v) for v in en.keys())
                if any(not 0 <= v < 256 ** w for v in enum_vals):
                    raise UnsupportedSpec(f"field {fid}: enum value out of range")
                atoms.add("enum")
            if w > 1:
                atoms.add(f"endian:{endian}")
            fields.append(Field(kind=k, id=fid, width=w, endian=endian,
                                enum_values=enum_vals,
                                enum_name=e.get("enum", "") if enum_vals else ""))
            atoms.add(f"{k}:{w}")
            continue

        raise UnsupportedSpec(f"field {fid}: unsupported type {t!r}")

    if len(set(f.id for f in fields)) != len(fields):
        raise UnsupportedSpec("duplicate field ids")
    return SpecModel(id=sid, endian=endian, fields=fields,
                     atoms=frozenset(atoms), source=text)


def atoms_of_ksy(text: str) -> frozenset:
    return parse_ksy(text).atoms

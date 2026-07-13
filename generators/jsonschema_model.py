"""Model of the JSON Schema subset used for agent tool contracts.

A tool contract is a message schema: the tool's ``input_schema`` (JSON Schema)
plus a name/description.  This is the *same shape* as the codec domain -- a
declarative record spec -- with a different, existing, documented spec
language (JSON Schema) that the LLM already knows.  This module:

  * parses a JSON Schema (a bounded subset) into an ordered property list,
  * extracts the spec's *feature atoms* (the vocabulary generator grammars
    are written in),
  * rejects anything outside the modeled subset (permanent coverage miss).

Feature-atom vocabulary (a generator covers a schema iff the schema's atoms
are a subset of the generator's atoms):

  type:string type:integer type:number type:boolean
  enum  array  object-nested  optional  format:<name>

The seed domain intentionally forbids ``additionalProperties`` and forces
strict validation, so an independent JSON Schema validator and a strict
Pydantic model accept exactly the same set of instances (the differential).
"""
from __future__ import annotations

import dataclasses
import json
import re
from typing import Optional

SCALARS = {"string", "integer", "number", "boolean"}
ALLOWED_FORMATS = {"email", "uri", "date", "date-time", "uuid", "ipv4"}

ALL_ATOMS = (
    [f"type:{t}" for t in SCALARS]
    + ["enum", "array", "object-nested", "optional"]
    + [f"format:{f}" for f in sorted(ALLOWED_FORMATS)]
)


class UnsupportedSchema(Exception):
    """Schema uses constructs outside the modeled subset."""


@dataclasses.dataclass
class Prop:
    name: str
    jtype: str                       # string integer number boolean array object
    required: bool
    enum: Optional[list] = None      # allowed scalar values, sorted
    item_type: str = ""              # for arrays: scalar element type
    fmt: str = ""                    # string format
    nested: Optional["SchemaModel"] = None  # for object properties


@dataclasses.dataclass
class SchemaModel:
    name: str
    props: list          # list[Prop]
    atoms: frozenset
    source: str          # raw JSON text (canonical for hashing)
    required: list


_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _tool_name(doc: dict, default: str) -> str:
    t = doc.get("title") or doc.get("$id") or default
    t = re.sub(r"[^A-Za-z0-9_]", "_", str(t)).strip("_")
    if not t or not t[0].isalpha():
        t = "tool_" + (t or "x")
    return t


def _parse_object(doc: dict, atoms: set, name: str, depth: int) -> "SchemaModel":
    if depth > 3:
        raise UnsupportedSchema("nesting too deep (>3)")
    if doc.get("type") != "object":
        raise UnsupportedSchema("top-level schema must be type: object")
    if doc.get("additionalProperties", False) not in (False,):
        raise UnsupportedSchema("additionalProperties must be false (strict)")
    props_doc = doc.get("properties", {})
    if not isinstance(props_doc, dict):
        raise UnsupportedSchema("properties must be an object")
    # An object with no properties and additionalProperties:false is the
    # legitimate "accepts exactly {}" contract of a no-argument tool; only a
    # top-level (depth 0) schema may be empty, so nested {} objects still must
    # declare shape.
    if not props_doc and depth > 0:
        raise UnsupportedSchema("nested object must have non-empty properties")
    required = list(doc.get("required", []))
    if not all(isinstance(r, str) for r in required):
        raise UnsupportedSchema("required must be a list of names")
    props = []
    for pname, pschema in props_doc.items():
        if not _NAME_RE.fullmatch(pname):
            raise UnsupportedSchema(f"bad property name {pname!r}")
        if not isinstance(pschema, dict):
            raise UnsupportedSchema(f"property {pname} must be a schema object")
        req = pname in required
        if not req:
            atoms.add("optional")
        prop = _parse_prop(pname, pschema, atoms, req, depth)
        props.append(prop)
    return SchemaModel(name=name, props=props, atoms=frozenset(atoms),
                       source="", required=sorted(required))


def _parse_prop(pname, pschema, atoms, req, depth) -> Prop:
    if "enum" in pschema:
        vals = pschema["enum"]
        if not isinstance(vals, list) or not vals:
            raise UnsupportedSchema(f"property {pname}: empty/invalid enum")
        if not all(isinstance(v, (str, int)) and not isinstance(v, bool)
                   for v in vals):
            raise UnsupportedSchema(f"property {pname}: enum values must be "
                                    "strings or integers")
        jt = pschema.get("type", "string")
        if jt not in ("string", "integer"):
            raise UnsupportedSchema(f"property {pname}: enum type must be "
                                    "string or integer")
        atoms.add("enum")
        atoms.add(f"type:{jt}")
        return Prop(name=pname, jtype=jt, required=req,
                    enum=sorted(vals, key=lambda x: (str(type(x)), x)))
    jt = pschema.get("type")
    if jt in SCALARS:
        atoms.add(f"type:{jt}")
        fmt = pschema.get("format", "")
        if fmt:
            if fmt not in ALLOWED_FORMATS:
                raise UnsupportedSchema(f"property {pname}: unsupported "
                                        f"format {fmt!r}")
            if jt != "string":
                raise UnsupportedSchema(f"property {pname}: format on "
                                        "non-string")
            atoms.add(f"format:{fmt}")
        return Prop(name=pname, jtype=jt, required=req, fmt=fmt)
    if jt == "array":
        items = pschema.get("items")
        if not isinstance(items, dict) or items.get("type") not in SCALARS:
            raise UnsupportedSchema(f"property {pname}: array items must be a "
                                    "scalar type")
        atoms.add("array")
        atoms.add(f"type:{items['type']}")
        return Prop(name=pname, jtype="array", required=req,
                    item_type=items["type"])
    if jt == "object":
        atoms.add("object-nested")
        nested = _parse_object(pschema, atoms, pname, depth + 1)
        return Prop(name=pname, jtype="object", required=req, nested=nested)
    raise UnsupportedSchema(f"property {pname}: unsupported type {jt!r}")


def parse_schema(text: str, default_name: str = "tool") -> SchemaModel:
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise UnsupportedSchema(f"not valid JSON: {e}")
    if not isinstance(doc, dict):
        raise UnsupportedSchema("schema must be a JSON object")
    name = _tool_name(doc, default_name)
    atoms: set = set()
    model = _parse_object(doc, atoms, name, 0)
    model.source = text
    return model


def atoms_of_schema(text: str) -> frozenset:
    return parse_schema(text).atoms

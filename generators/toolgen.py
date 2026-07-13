"""Tool-contract generator: JSON Schema -> a certified tool boundary.

Emits, from a tool's ``input_schema``:

  * a strict Pydantic model + ``decode``/``encode`` + a ``TOOL_DEF`` descriptor
    (the MCP / function-calling tool definition) -- the *outsourced* validator
    (Pydantic is the vendored tool, like Kaitai for codecs);
  * an INDEPENDENT reference validator built on the ``jsonschema`` library --
    a separately-authored implementation, for the N-version differential
    (like refcodec for codecs, but here the independence is free: two
    vendored libraries).

Oracles (reuse the codec kernel machinery):
  * round-trip:  encode(decode(x)) == x for schema-valid x (Hypothesis
    instances from hypothesis-jsonschema, never the LLM);
  * rejection:   extra keys / missing-required are rejected;
  * differential: Pydantic accepts iff the jsonschema reference accepts, on
    the same generated + mutated instances.

The seed forbids ``additionalProperties`` and enforces strict typing so the
two independent validators accept exactly the same instance set.
"""
from __future__ import annotations

import copy
import json

from .jsonschema_model import SchemaModel, Prop, parse_schema


def _cls(name: str) -> str:
    return "".join(p.capitalize() or "_" for p in name.split("_")) or "T"


def inject_strict(schema: dict) -> dict:
    """Recursively set additionalProperties:false on every object (jsonschema
    defaults it to *true*; Pydantic's extra='forbid' is strict -- align them)."""
    s = copy.deepcopy(schema)

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                node.setdefault("additionalProperties", False)
                for v in node["properties"].values():
                    walk(v)
            if node.get("type") == "array" and isinstance(node.get("items"), dict):
                walk(node["items"])
        return node

    walk(s)
    return s


_SCALAR_PY = {"string": "str", "integer": "int", "number": "float",
              "boolean": "bool"}


def _involves_number(p: Prop) -> bool:
    return p.jtype == "number" or (p.jtype == "array" and p.item_type == "number")


def _ann(p: Prop, tool_cls: str) -> str:
    if p.enum is not None:
        return "Literal[" + ", ".join(repr(v) for v in p.enum) + "]"
    if p.jtype in _SCALAR_PY:
        return _SCALAR_PY[p.jtype]
    if p.jtype == "array":
        return f"List[{_SCALAR_PY[p.item_type]}]"
    if p.jtype == "object":
        return f"{tool_cls}_{_cls(p.name)}"
    raise ValueError(p.jtype)


def _emit_class(model: SchemaModel, tool_cls: str, prefix: str, out: list):
    # emit nested classes first (dependency order)
    for p in model.props:
        if p.jtype == "object" and p.nested is not None:
            _emit_class(p.nested, tool_cls, f"{prefix}_{_cls(p.name)}", out)
    cls_name = prefix
    lines = [f"class {cls_name}(BaseModel):",
             "    model_config = ConfigDict(strict=True, extra='forbid')"]
    for p in model.props:
        ann = _ann(p, tool_cls)
        relax = _involves_number(p)
        if p.required:
            if relax:
                lines.append(f"    {p.name}: {ann} = Field(strict=False)")
            else:
                lines.append(f"    {p.name}: {ann}")
        else:
            if relax:
                lines.append(f"    {p.name}: Optional[{ann}] = "
                             "Field(default=None, strict=False)")
            else:
                lines.append(f"    {p.name}: Optional[{ann}] = None")
    out.append("\n".join(lines))


def emit_pydantic_tool(schema_text: str) -> dict:
    model = parse_schema(schema_text)
    tool_cls = _cls(model.name)
    strict_schema = inject_strict(json.loads(schema_text))
    classes: list = []
    _emit_class(model, tool_cls, tool_cls, classes)
    src = [
        "import json",
        "from typing import Optional, List, Literal",
        "from pydantic import BaseModel, ConfigDict, Field",
        "",
        "# NOTE: JSON Schema 'format' (email/uri/...) is ADVISORY here -- an",
        "# annotation, not enforced -- matching JSON Schema Draft-7 default",
        "# behavior and the jsonschema reference validator. The certificate",
        "# covers structural validation (types/enums/required/extra), not",
        "# format-string semantics, on which independent validators disagree.",
        "",
        "\n\n".join(classes),
        "",
        f"TOOL_DEF = {{'name': {model.name!r}, 'description': "
        f"'certified tool contract', 'input_schema': "
        f"json.loads(r'''{json.dumps(strict_schema)}''')}}",
        "",
        "def decode(data):",
        f"    return {tool_cls}.model_validate(data)",
        "",
        "def encode(obj):",
        "    return obj.model_dump(exclude_none=True)",
        "",
    ]
    return {"tool_model.py": "\n".join(src).encode()}


_REF_VALIDATOR = r'''
import json
import jsonschema
from tool_model import TOOL_DEF
SCHEMA = TOOL_DEF["input_schema"]
_validator = jsonschema.Draft7Validator(SCHEMA)

def decode(data):
    _validator.validate(data)   # raises jsonschema.ValidationError if invalid
    return data

def encode(data):
    return data
'''


def emit_reference_validator(schema_text: str) -> dict:
    return {"ref_validator.py": _REF_VALIDATOR.encode()}


_SETTINGS = ("@settings(max_examples=%d, derandomize=True, database=None, "
             "deadline=None, suppress_health_check=list(HealthCheck))")


def build_tool_harness(schema_text: str, max_examples: int = 100) -> str:
    return f'''
import json, sys, traceback
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis_jsonschema import from_schema
from tool_model import decode, encode, TOOL_DEF
SCHEMA = TOOL_DEF["input_schema"]

def _accepts(fn, x):
    try:
        fn(x); return True
    except Exception:
        return False

{_SETTINGS % max_examples}
@given(from_schema(SCHEMA))
def prop_roundtrip(data):
    obj = decode(data)
    out = encode(obj)
    assert out == data, ("roundtrip", out, data)

{_SETTINGS % max_examples}
@given(from_schema(SCHEMA))
def prop_reject(data):
    # extra key must be rejected (additionalProperties:false / extra=forbid)
    bad = dict(data); bad["__unexpected_key__"] = 1
    assert not _accepts(decode, bad), ("accepted extra key", bad)
    # missing required must be rejected
    req = SCHEMA.get("required", [])
    if req and req[0] in data:
        b2 = {{k: v for k, v in data.items() if k != req[0]}}
        assert not _accepts(decode, b2), ("accepted missing required", b2)

def main():
    try:
        prop_roundtrip(); prop_reject()
        print(json.dumps({{"status": "pass", "examples": {max_examples}}}))
    except BaseException as e:
        print(json.dumps({{"status": "fail", "error": repr(e)[:2000],
                          "traceback": traceback.format_exc()[-2500:]}}))
        sys.exit(1)

main()
'''


def build_incumbent_differential_harness(schema_text: str,
                                         max_examples: int = 100) -> str:
    """Differential of the inferred-schema validator against the INCUMBENT
    validator (shipped as incumbent.py, run sandboxed).  Certifies that the
    inferred schema faithfully captures the incumbent's accept/reject
    contract: the incumbent is the ground-truth anchor."""
    return f'''
import json, sys, traceback
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis_jsonschema import from_schema
from tool_model import decode as p_decode, TOOL_DEF
from incumbent import accepts as inc_accepts
SCHEMA = TOOL_DEF["input_schema"]

def _accepts(fn, x):
    try:
        fn(x); return True
    except Exception:
        return False

def _inc(x):
    try:
        return bool(inc_accepts(x))
    except Exception:
        return False

def _mutations(data):
    out = []
    b = dict(data); b["__unexpected_key__"] = 1; out.append(b)
    for k in list(data):
        out.append({{kk: vv for kk, vv in data.items() if kk != k}})
        b3 = dict(data); b3[k] = {{"__wrong__": True}}; out.append(b3)
    return out

{_SETTINGS % max_examples}
@given(from_schema(SCHEMA))
def prop(data):
    # every schema-valid instance must be accepted by the incumbent (else the
    # inferred schema is too loose), and vice-versa on mutations
    assert _inc(data), ("incumbent rejects a schema-valid instance", data)
    assert _accepts(p_decode, data), ("inferred validator rejects a valid "
                                      "instance", data)
    for bad in _mutations(data):
        p, i = _accepts(p_decode, bad), _inc(bad)
        assert p == i, ("inferred schema disagrees with incumbent", bad,
                        "inferred", p, "incumbent", i)

def main():
    try:
        prop()
        print(json.dumps({{"status": "pass", "examples": {max_examples}}}))
    except BaseException as e:
        print(json.dumps({{"status": "fail", "error": repr(e)[:2000],
                          "traceback": traceback.format_exc()[-2500:]}}))
        sys.exit(1)

main()
'''


def build_tool_differential_harness(schema_text: str, max_examples: int = 100) -> str:
    return f'''
import json, sys, traceback
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis_jsonschema import from_schema
from tool_model import decode as p_decode, encode as p_encode, TOOL_DEF
from ref_validator import decode as j_decode
SCHEMA = TOOL_DEF["input_schema"]

def _accepts(fn, x):
    try:
        fn(x); return True
    except Exception:
        return False

def _mutations(data):
    out = []
    b = dict(data); b["__unexpected_key__"] = 1; out.append(b)
    for k in list(data):
        b2 = {{kk: vv for kk, vv in data.items() if kk != k}}; out.append(b2)
        b3 = dict(data); b3[k] = {{"__wrong__": True}}; out.append(b3)
    return out

{_SETTINGS % max_examples}
@given(from_schema(SCHEMA))
def prop_agree(data):
    # CHANNEL (i): two independent validators must agree on accept/reject
    assert _accepts(p_decode, data) and _accepts(j_decode, data), \\
        ("both should accept a schema-valid instance", data)
    out = p_encode(p_decode(data))
    assert out == data, ("pydantic roundtrip differs from input", out, data)
    for bad in _mutations(data):
        pj, jj = _accepts(p_decode, bad), _accepts(j_decode, bad)
        assert pj == jj, ("validators disagree", bad, "pydantic", pj,
                          "jsonschema", jj)

def main():
    try:
        prop_agree()
        print(json.dumps({{"status": "pass", "examples": {max_examples}}}))
    except BaseException as e:
        print(json.dumps({{"status": "fail", "error": repr(e)[:2000],
                          "traceback": traceback.format_exc()[-2500:]}}))
        sys.exit(1)

main()
'''

"""Cross-field constraint specs -- the semantic layer JSON Schema cannot express.

A constraint spec has integer and enum fields plus a list of predicates that
relate fields to each other (e.g. ``start_hour < end_hour``,
``priority == "high"  =>  attendees >= 2``) and an optional ``invariant`` the
constraints are claimed to guarantee.  This is the contract layer that plain
structural validation (types/enums/required) provably cannot reach, and the
schema-lift loop correctly refuses.

Predicates are declarative JSON (the LLM authors logic, not code):

  {"op": "<",  "left": "start_hour", "right": "end_hour"}
  {"op": ">=", "left": "attendees",  "right": 1}
  {"op": "implies",
   "if":   {"op": "==", "left": "priority", "right": "high"},
   "then": {"op": ">=", "left": "attendees", "right": 2}}

Fields are Int (SMT theory of linear integer arithmetic) or enums encoded as
bounded integers, so obligations land in the decidable QF_LIA fragment that
both Z3 and CVC5 settle -- the dual-checker agrees on a *load-bearing* proof.
"""
from __future__ import annotations

import dataclasses
import json
import re
from typing import Optional

CMP = {"<", "<=", ">", ">=", "==", "!="}
_NAME = re.compile(r"[a-z][a-z0-9_]*")


class UnsupportedConstraint(Exception):
    pass


@dataclasses.dataclass
class Field:
    name: str
    kind: str                 # "integer" | "enum"
    values: Optional[list] = None   # enum value strings, in index order


@dataclasses.dataclass
class ConstraintModel:
    name: str
    fields: dict              # name -> Field
    constraints: list         # list[pred dict]
    invariant: Optional[dict]
    source: str


def _check_pred(pred, fields, top=True):
    if not isinstance(pred, dict) or "op" not in pred:
        raise UnsupportedConstraint(f"predicate must be an object with op: {pred!r}")
    op = pred["op"]
    if op == "implies":
        _check_pred(pred.get("if"), fields, top=False)
        _check_pred(pred.get("then"), fields, top=False)
        return
    if op not in CMP:
        raise UnsupportedConstraint(f"unsupported op {op!r}")
    left, right = pred.get("left"), pred.get("right")
    if left not in fields:
        raise UnsupportedConstraint(f"left operand must be a field: {left!r}")
    lf = fields[left]
    if lf.kind == "enum":
        if op not in ("==", "!="):
            raise UnsupportedConstraint(
                f"enum field {left!r} supports only ==/!=")
        if right not in (lf.values or []):
            raise UnsupportedConstraint(
                f"{left} {op} {right!r}: right must be one of {lf.values}")
    else:  # integer field
        if isinstance(right, str):
            if right not in fields or fields[right].kind != "integer":
                raise UnsupportedConstraint(
                    f"right operand {right!r} must be an integer field or int")
        elif not isinstance(right, int) or isinstance(right, bool):
            raise UnsupportedConstraint(
                f"right operand must be an int or integer field: {right!r}")


def parse_constraint_spec(text: str) -> ConstraintModel:
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise UnsupportedConstraint(f"not valid JSON: {e}")
    if not isinstance(doc, dict):
        raise UnsupportedConstraint("spec must be a JSON object")
    name = doc.get("name", "constrained")
    if not _NAME.fullmatch(name):
        raise UnsupportedConstraint("name must be lowercase identifier")
    fdoc = doc.get("fields")
    if not isinstance(fdoc, dict) or not fdoc:
        raise UnsupportedConstraint("fields must be a non-empty object")
    fields = {}
    for fn, fs in fdoc.items():
        if not _NAME.fullmatch(fn):
            raise UnsupportedConstraint(f"bad field name {fn!r}")
        t = fs.get("type")
        if t == "integer":
            fields[fn] = Field(fn, "integer")
        elif t == "enum":
            vals = fs.get("values")
            if not isinstance(vals, list) or not vals or \
                    not all(isinstance(v, str) for v in vals):
                raise UnsupportedConstraint(f"enum {fn} needs string values")
            if len(set(vals)) != len(vals):
                raise UnsupportedConstraint(f"enum {fn} has duplicate values")
            fields[fn] = Field(fn, "enum", list(vals))
        else:
            raise UnsupportedConstraint(f"field {fn}: type must be integer/enum")
    cons = doc.get("constraints", [])
    if not isinstance(cons, list) or not cons:
        raise UnsupportedConstraint("constraints must be a non-empty list")
    for c in cons:
        _check_pred(c, fields)
    inv = doc.get("invariant")
    if inv is not None:
        _check_pred(inv, fields)
    return ConstraintModel(name=name, fields=fields, constraints=cons,
                           invariant=inv, source=text)

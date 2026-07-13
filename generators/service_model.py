"""Service meta-spec: one declaration that fans out to all four certified
generator families.

A service is a set of tools; each tool is simultaneously
  * a tool contract  (its input JSON Schema  -> tool-differential),
  * optionally a per-call constraint          (cross-field logic -> constraint-cert),
  * a protocol transition                      (from/to state, guard, update).
The whole set is a protocol (states + safety invariant -> protocol-cert).

Certifying a service = certifying every tool's schema, every declared
constraint, and the protocol's sequencing safety, then binding those
certificates to a composed service dispatcher whose behaviour is checked to
faithfully AND them together.  This is where the certified library composes
into practical, whole-service code.
"""
from __future__ import annotations

import dataclasses
import json


class UnsupportedService(Exception):
    pass


@dataclasses.dataclass
class ServiceTool:
    name: str
    frm: str
    to: str
    input_schema: dict
    arg: str | None
    guard: dict | None
    update: dict
    constraints: dict | None   # a constraint-cert spec, or None

    @property
    def schema_text(self) -> str:
        return json.dumps(self.input_schema)


@dataclasses.dataclass
class ServiceModel:
    name: str
    context: dict
    states: list
    initial: str
    safety: dict
    tools: list        # list[ServiceTool]
    source: str

    def protocol_spec_text(self) -> str:
        """Project the tools to a pure protocol spec (protocol_model input)."""
        actions = []
        for t in self.tools:
            a = {"name": t.name, "from": t.frm, "to": t.to,
                 "update": t.update or {}}
            if t.arg:
                a["arg"] = t.arg
            if t.guard is not None:
                a["guard"] = t.guard
            actions.append(a)
        return json.dumps({
            "name": self.name, "context": {
                c: {"type": "integer", "init_min": lo, "init_max": hi}
                for c, (lo, hi) in self.context.items()},
            "states": self.states, "initial": self.initial,
            "actions": actions, "safety": self.safety})


def parse_service_spec(text: str) -> ServiceModel:
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise UnsupportedService(f"not valid JSON: {e}")
    states = doc.get("states")
    if not isinstance(states, list) or len(states) < 2:
        raise UnsupportedService("states must be a list of >=2 names")
    initial = doc.get("initial")
    if initial not in states:
        raise UnsupportedService("initial must be a state")
    context = {}
    for c, cs in doc.get("context", {}).items():
        lo, hi = cs.get("init_min", 0), cs.get("init_max", 0)
        if not (isinstance(lo, int) and isinstance(hi, int) and lo <= hi):
            raise UnsupportedService(f"context {c}: bad init range")
        context[c] = (lo, hi)
    tools = []
    seen = set()
    for t in doc.get("tools", []):
        name = t.get("name")
        if not name or name in seen:
            raise UnsupportedService(f"tool name missing or duplicate: {name!r}")
        seen.add(name)
        if t.get("from") not in states or t.get("to") not in states:
            raise UnsupportedService(f"tool {name}: from/to must be states")
        sch = t.get("input_schema")
        if not isinstance(sch, dict) or sch.get("type") != "object":
            raise UnsupportedService(f"tool {name}: input_schema must be object")
        sch.setdefault("title", name)
        tools.append(ServiceTool(
            name=name, frm=t["from"], to=t["to"], input_schema=sch,
            arg=t.get("arg"), guard=t.get("guard"), update=t.get("update", {}) or {},
            constraints=t.get("constraints")))
    if not tools:
        raise UnsupportedService("no tools")
    safety = doc.get("safety")
    if not isinstance(safety, dict) or safety.get("when") not in states:
        raise UnsupportedService("safety needs {when: state, invariant: pred}")
    m = ServiceModel(name=doc.get("name", "service"), context=context,
                     states=states, initial=initial, safety=safety,
                     tools=tools, source=text)
    # validate the projected protocol + each tool schema parse cleanly
    from generators import protocol_model, jsonschema_model
    protocol_model.parse_protocol_spec(m.protocol_spec_text())
    for t in tools:
        jsonschema_model.parse_schema(t.schema_text)
    return m

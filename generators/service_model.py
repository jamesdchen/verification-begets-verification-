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
    terminal: bool = False     # P1.2: a session-closing tool (monitor-guarded)
    output_schema: dict | None = None
    # P2.1: optional JSON-Schema-subset contract on the tool's RESULT value.  It
    # is a pure EGRESS concern: the emitted dispatcher (which never returns a
    # `result`) ignores it entirely, so a service that declares one stays byte-
    # identical.  Only the cage (run/guarded.py) validates an incumbent's output
    # against it, via the same dual-validator machinery as input schemas.

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
    obligations: list = dataclasses.field(default_factory=list)
    # P1: LTLf temporal demands over the tool alphabet; empty by default, so a
    # service that declares none is byte-identical to a pre-Phase-1 service.

    def interface_text(self) -> str:
        """The service's INTERFACE only: tool names, from/to states, input
        schemas, states, initial, context variable ranges.  Deliberately
        excludes guards, updates, per-call constraints and the safety invariant
        -- the semantic content.  This is what the independent scenario-author
        is shown, so its accept/reject expectations must be derived from the
        original request, not read off the spec.  Terminal flags ARE interface
        (which tool closes a session), so they are exposed."""
        return json.dumps({
            "name": self.name,
            "context": {c: {"init_min": lo, "init_max": hi}
                        for c, (lo, hi) in self.context.items()},
            "states": self.states, "initial": self.initial,
            "tools": [dict({"name": t.name, "from": t.frm, "to": t.to,
                            "input_schema": t.input_schema},
                           **({"terminal": True} if t.terminal else {}))
                      for t in self.tools]})

    def protocol_spec_text(self) -> str:
        """Project the tools to a pure protocol spec (protocol_model input).

        Threads the P1.2 `terminal` flag per action and the P1 temporal
        `obligations` (both DROPPED silently before -- protocol_model.Action now
        carries terminal, and parse_protocol_spec validates the obligations)."""
        actions = []
        for t in self.tools:
            a = {"name": t.name, "from": t.frm, "to": t.to,
                 "update": t.update or {}}
            if t.arg:
                a["arg"] = t.arg
            if t.guard is not None:
                a["guard"] = t.guard
            if t.terminal:
                a["terminal"] = True
            actions.append(a)
        doc = {
            "name": self.name, "context": {
                c: {"type": "integer", "init_min": lo, "init_max": hi}
                for c, (lo, hi) in self.context.items()},
            "states": self.states, "initial": self.initial,
            "actions": actions, "safety": self.safety}
        if self.obligations:
            doc["obligations"] = self.obligations
        return json.dumps(doc)


def _parse_obligations(obls, tool_names):
    """Validate the temporal-obligation list against the tool alphabet, reusing
    the protocol_model validator so the shape is single-sourced.  Returns the
    normalized list (empty when none declared)."""
    from generators import protocol_model
    try:
        return protocol_model._check_obligations(obls, tool_names)
    except protocol_model.UnsupportedProtocol as e:
        raise UnsupportedService(f"bad obligations: {e}")


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
        osch = t.get("output_schema")
        if osch is not None:
            if not isinstance(osch, dict) or osch.get("type") != "object":
                raise UnsupportedService(
                    f"tool {name}: output_schema must be an object schema")
            osch.setdefault("title", f"{name}_out")
        tools.append(ServiceTool(
            name=name, frm=t["from"], to=t["to"], input_schema=sch,
            arg=t.get("arg"), guard=t.get("guard"), update=t.get("update", {}) or {},
            constraints=t.get("constraints"), terminal=bool(t.get("terminal", False)),
            output_schema=osch))
    if not tools:
        raise UnsupportedService("no tools")
    safety = doc.get("safety")
    if not isinstance(safety, dict) or (safety.get("when") not in states
                                        and safety.get("when") != "*"):
        raise UnsupportedService(
            'safety needs {when: state | "*", invariant: pred}')
    tool_names = {t.name for t in tools}
    obligations = _parse_obligations(doc.get("obligations", []), tool_names)
    m = ServiceModel(name=doc.get("name", "service"), context=context,
                     states=states, initial=initial, safety=safety,
                     tools=tools, source=text, obligations=obligations)
    # validate the projected protocol + each tool schema parse cleanly
    from generators import protocol_model, jsonschema_model
    try:
        protocol_model.parse_protocol_spec(m.protocol_spec_text())
    except protocol_model.UnsupportedProtocol as e:
        raise UnsupportedService(f"protocol projection invalid: {e}")
    for t in tools:
        try:
            jsonschema_model.parse_schema(t.schema_text)
        except jsonschema_model.UnsupportedSchema as e:
            raise UnsupportedService(f"tool {t.name}: input_schema invalid: {e}")
        if t.output_schema is not None:
            try:
                jsonschema_model.parse_schema(json.dumps(t.output_schema))
            except jsonschema_model.UnsupportedSchema as e:
                raise UnsupportedService(
                    f"tool {t.name}: output_schema invalid: {e}")
    return m

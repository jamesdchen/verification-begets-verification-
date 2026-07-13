"""Stateful protocol / sequencing contracts -- the layer that per-message
validation cannot reach.

A protocol spec has finite control states, integer context variables,
actions (guarded transitions that read an optional integer argument and update
context), and a safety invariant that must hold in every reachable state.
This certifies *sequences* of calls -- "authenticate before you act", "never
ship an unpaid order" -- which no single-message schema can express.

Example (an order lifecycle):

  states: new -> paid -> shipped -> closed
  context: due (int)
  pay(amount): from new, guard amount >= due, sets due := 0, to paid
  ship():      from paid, to shipped
  safety:      in state 'shipped', due == 0   (never ship unpaid)

Safety is verified by bounded model checking over the transition relation
(SMT, dual-checked Z3 & CVC5).  When the control graph is acyclic the bound
equals the longest path and the result is *complete*, not merely bounded.
"""
from __future__ import annotations

import dataclasses
import json
import re
from typing import Optional

_NAME = re.compile(r"[a-z][a-z0-9_]*")
CMP = {"<", "<=", ">", ">=", "==", "!="}


class UnsupportedProtocol(Exception):
    pass


@dataclasses.dataclass
class Action:
    name: str
    frm: str
    to: str
    arg: Optional[str]
    guard: Optional[dict]
    update: dict          # context var -> expr


@dataclasses.dataclass
class ProtocolModel:
    name: str
    context: dict          # var -> (init_min, init_max)
    states: list
    initial: str
    actions: list
    safety: dict           # {"when": state, "invariant": pred}
    source: str

    def idx(self, state):
        return self.states.index(state)

    def acyclic_bound(self):
        """(bound K, complete: bool).  Complete = K covers the longest path
        because the control graph is a DAG."""
        adj = {}
        for a in self.actions:
            adj.setdefault(a.frm, set()).add(a.to)
        # cycle detection (DFS)
        WHITE, GREY, BLACK = 0, 1, 2
        color = {s: WHITE for s in self.states}
        cyclic = [False]

        def dfs(u):
            color[u] = GREY
            for v in adj.get(u, ()):
                if color[v] == GREY:
                    cyclic[0] = True
                elif color[v] == WHITE:
                    dfs(v)
            color[u] = BLACK
        for s in self.states:
            if color[s] == WHITE:
                dfs(s)
        if cyclic[0]:
            return 8, False
        return max(1, len(self.states) - 1), True


def _check_atom(o, names):
    if isinstance(o, int) and not isinstance(o, bool):
        return
    if isinstance(o, str) and o in names:
        return
    raise UnsupportedProtocol(f"operand must be an int or a known name: {o!r}")


def _check_pred(pred, names):
    if not isinstance(pred, dict) or "op" not in pred:
        raise UnsupportedProtocol(f"predicate must have op: {pred!r}")
    op = pred["op"]
    if op == "and":
        for p in pred.get("preds", []):
            _check_pred(p, names)
        return
    if op == "implies":
        _check_pred(pred["if"], names); _check_pred(pred["then"], names)
        return
    if op not in CMP:
        raise UnsupportedProtocol(f"unsupported op {op!r}")
    _check_atom(pred.get("left"), names)
    _check_atom(pred.get("right"), names)


def _check_expr(e, names):
    if isinstance(e, int) and not isinstance(e, bool):
        return
    if isinstance(e, str):
        if e not in names:
            raise UnsupportedProtocol(f"unknown name in expr: {e!r}")
        return
    if isinstance(e, dict):
        if "const" in e:
            return
        if "var" in e:
            if e["var"] not in names:
                raise UnsupportedProtocol(f"unknown var {e['var']!r}")
            return
        if e.get("op") in ("+", "-"):
            _check_expr(e["left"], names); _check_expr(e["right"], names)
            return
    raise UnsupportedProtocol(f"unsupported update expr: {e!r}")


def parse_protocol_spec(text: str) -> ProtocolModel:
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise UnsupportedProtocol(f"not valid JSON: {e}")
    name = doc.get("name", "protocol")
    if not _NAME.fullmatch(name):
        raise UnsupportedProtocol("bad name")
    states = doc.get("states")
    if not isinstance(states, list) or len(states) < 2 or \
            len(set(states)) != len(states):
        raise UnsupportedProtocol("states must be a list of >=2 unique names")
    initial = doc.get("initial")
    if initial not in states:
        raise UnsupportedProtocol("initial must be a state")
    ctx_doc = doc.get("context", {})
    context = {}
    for c, cs in ctx_doc.items():
        if not _NAME.fullmatch(c):
            raise UnsupportedProtocol(f"bad context var {c!r}")
        lo, hi = cs.get("init_min", 0), cs.get("init_max", 0)
        if not (isinstance(lo, int) and isinstance(hi, int) and lo <= hi):
            raise UnsupportedProtocol(f"context {c}: bad init range")
        context[c] = (lo, hi)
    ctx_names = set(context)
    actions = []
    for a in doc.get("actions", []):
        an = a.get("name")
        if not _NAME.fullmatch(an or ""):
            raise UnsupportedProtocol(f"bad action name {an!r}")
        if a.get("from") not in states or a.get("to") not in states:
            raise UnsupportedProtocol(f"action {an}: from/to must be states")
        arg = a.get("arg")
        names = ctx_names | ({arg} if arg else set())
        guard = a.get("guard")
        if guard is not None:
            _check_pred(guard, names)
        update = a.get("update", {}) or {}
        for uv, ue in update.items():
            if uv not in ctx_names:
                raise UnsupportedProtocol(f"action {an}: updates unknown {uv!r}")
            _check_expr(ue, names)
        actions.append(Action(an, a["from"], a["to"], arg, guard, update))
    if not actions:
        raise UnsupportedProtocol("no actions")
    safety = doc.get("safety")
    if not isinstance(safety, dict) or safety.get("when") not in states \
            or "invariant" not in safety:
        raise UnsupportedProtocol("safety needs {when: state, invariant: pred}")
    _check_pred(safety["invariant"], ctx_names)
    return ProtocolModel(name=name, context=context, states=states,
                         initial=initial, actions=actions, safety=safety,
                         source=text)

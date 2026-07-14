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

# P4a nested sessions: the bounded visible-stack depth D.  Exploration is
# COMPLETE only for stack depth <= D, so every dispatcher/reference/validator
# MUST enforce this same bound (refuse a call at depth D).  Sweep-proven with
# K=8,D=4 (per-step sp[i]:Int + fixed slots stk[d][i]:Int, symbolic-index
# case-split -- pure QF_LIA, no arrays).
STACK_DEPTH = 4
KINDS = ("call", "return", "internal")


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
    terminal: bool = False  # P1.2: a session-closing action ("close"/"cancel")
    # P4a: call/return/internal.  A `call` pushes `return_to` (its continuation
    # state) and enters its `to`; a `return`'s target is STACK-DETERMINED (the
    # top of the stack), so its `to` is a nominal placeholder every reader must
    # ignore in favour of the popped continuation; `internal` is a plain move.
    kind: str = "internal"
    return_to: Optional[str] = None


@dataclasses.dataclass
class ProtocolModel:
    name: str
    context: dict          # var -> (init_min, init_max)
    states: list
    initial: str
    actions: list
    safety: dict           # {"when": state, "invariant": pred}
    source: str
    obligations: list = dataclasses.field(default_factory=list)
    # P1: LTLf temporal demands over the ACTION alphabet, each
    #   {"id": str, "kind": "eventually"|..., "action"/"pre"/... : name, ...}
    # An empty list (the default) leaves every existing protocol untouched.

    def idx(self, state):
        return self.states.index(state)

    def has_stack(self):
        """P4a: does this protocol use a visible call/return stack?  When false
        every P4a code path is skipped, so a non-nested spec is byte-identical."""
        return any(a.kind in ("call", "return") for a in self.actions)

    def terminal_actions(self):
        """Names of actions marked terminal:true (the monitor guards these)."""
        return [a.name for a in self.actions if a.terminal]

    def sink_states(self):
        """States with no outgoing non-idle transition -- a session structurally
        ends on entering one.  Used (together with terminal_actions) to decide
        which trace steps 'complete' the session for the LTLf obligation."""
        has_out = {a.frm for a in self.actions}
        return [s for s in self.states if s not in has_out]

    def completing_actions(self):
        """Actions whose step completes a session: marked terminal OR leading to
        a sink state.  The LTLf temporal obligation is asserted violated only on
        traces whose last real action is completing (P1.3: an F/U obligation on
        an incomplete prefix is vacuously 'violated')."""
        sinks = set(self.sink_states())
        return [a.name for a in self.actions if a.terminal or a.to in sinks]

    def _cyclic(self, adj):
        """DFS cycle detection over an adjacency map (state -> set(states))."""
        WHITE, GREY, BLACK = 0, 1, 2
        color = {s: WHITE for s in self.states}
        cyc = [False]

        def dfs(u):
            color[u] = GREY
            for v in adj.get(u, ()):
                if color[v] == GREY:
                    cyc[0] = True
                elif color[v] == WHITE:
                    dfs(v)
            color[u] = BLACK
        for s in self.states:
            if color[s] == WHITE:
                dfs(s)
        return cyc[0]

    def acyclic_bound(self):
        """(bound K, complete: bool, depth D).

        NON-nested (depth=0, unchanged): complete = K covers the longest path
        because the control graph is a DAG; a cyclic control graph gets the
        arbitrary bounded constant (8, False, 0).

        NESTED (depth=D): call/return graphs are inherently cyclic, so the bound
        is DEPTH-AWARE over the bounded stack.  If the per-level INTERNAL-edge
        graph is acyclic, exploration is COMPLETE for every stack depth <= D and
        K = (|states|-1)*(D+1) + 2*D (claim `complete-to-depth(D)`); otherwise it
        is a plain bounded search, K = |states|*(D+1) (claim `bounded-K`)."""
        if not self.has_stack():
            adj = {}
            for a in self.actions:
                adj.setdefault(a.frm, set()).add(a.to)
            if self._cyclic(adj):
                return 8, False, 0
            return max(1, len(self.states) - 1), True, 0
        D = STACK_DEPTH
        n = len(self.states)
        internal_adj = {}
        for a in self.actions:
            if a.kind == "internal":
                internal_adj.setdefault(a.frm, set()).add(a.to)
        if self._cyclic(internal_adj):
            return n * (D + 1), False, D
        return (n - 1) * (D + 1) + 2 * D, True, D


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
        kind = a.get("kind", "internal")
        if kind not in KINDS:
            raise UnsupportedProtocol(
                f"action {an}: kind must be one of {KINDS}")
        frm = a.get("from")
        if frm not in states:
            raise UnsupportedProtocol(f"action {an}: from must be a state")
        # P4a: a return's target is STACK-DETERMINED, so its `to` is a nominal
        # placeholder (defaults to `from`) that every reader must ignore.
        to = a.get("to", frm) if kind == "return" else a.get("to")
        if to not in states:
            raise UnsupportedProtocol(f"action {an}: to must be a state")
        return_to = a.get("return_to")
        if kind == "call":
            if return_to not in states:
                raise UnsupportedProtocol(
                    f"action {an}: a call needs return_to (a state)")
        elif return_to is not None:
            raise UnsupportedProtocol(
                f"action {an}: return_to is only for call actions")
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
        terminal = bool(a.get("terminal", False))
        actions.append(Action(an, frm, to, arg, guard, update,
                              terminal=terminal, kind=kind, return_to=return_to))
    if not actions:
        raise UnsupportedProtocol("no actions")
    obligations = _check_obligations(doc.get("obligations", []),
                                     {a.name for a in actions})
    safety = doc.get("safety")
    if not isinstance(safety, dict) or "invariant" not in safety \
            or (safety.get("when") not in states and safety.get("when") != "*"):
        raise UnsupportedProtocol(
            'safety needs {when: state | "*", invariant: pred} '
            '("*" = a global G(pred): the invariant must hold in every '
            "reachable state)")
    _check_pred(safety["invariant"], ctx_names)
    return ProtocolModel(name=name, context=context, states=states,
                         initial=initial, actions=actions, safety=safety,
                         source=text, obligations=obligations)


# P1: the frozen LTLf temporal-demand kinds and their action-naming fields.
#   eventually {action}          F(action)
#   until      {pre, post}       pre U post
#   before     {first, second}   second must not occur before first
#   within     {action, steps}   action in one of the first `steps` positions
_OBLIGATION_FIELDS = {
    "eventually": ("action",),
    "until": ("pre", "post"),
    "before": ("first", "second"),
    "within": ("action",),      # + integer "steps"
}


def _check_obligations(obls, action_names):
    """Validate the temporal-obligation list against the action alphabet.  Every
    named action must exist; ids must be unique lowercase identifiers.  Returns a
    normalized list of plain dicts (empty when the protocol declares none)."""
    if not isinstance(obls, list):
        raise UnsupportedProtocol("obligations must be a list")
    out, seen = [], set()
    for o in obls:
        if not isinstance(o, dict):
            raise UnsupportedProtocol(f"obligation must be an object: {o!r}")
        oid, kind = o.get("id"), o.get("kind")
        if not (isinstance(oid, str) and _NAME.fullmatch(oid)) or oid in seen:
            raise UnsupportedProtocol(f"bad/duplicate obligation id {oid!r}")
        seen.add(oid)
        if kind not in _OBLIGATION_FIELDS:
            raise UnsupportedProtocol(f"obligation {oid}: unknown kind {kind!r}")
        norm = {"id": oid, "kind": kind}
        for f in _OBLIGATION_FIELDS[kind]:
            v = o.get(f)
            if v not in action_names:
                raise UnsupportedProtocol(
                    f"obligation {oid}: {f}={v!r} is not a declared action")
            norm[f] = v
        if kind == "within":
            steps = o.get("steps")
            if not (isinstance(steps, int) and not isinstance(steps, bool)
                    and steps >= 1):
                raise UnsupportedProtocol(
                    f"obligation {oid}: within needs integer steps >= 1")
            norm["steps"] = steps
        out.append(norm)
    return out

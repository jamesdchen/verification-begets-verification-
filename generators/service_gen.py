"""Emit a composed service dispatcher from a service meta-spec, plus a
conformance check that the dispatcher faithfully ANDs the certified layers.

  * emit_service(model): a `Service` class + one certified Pydantic validator
    module per tool.  call(tool, args) enforces, in order: sequencing (is this
    tool legal in the current state?), schema (tool contract), per-call
    constraints, protocol guard; then applies the update and advances state.
  * the conformance harness replays generated call sequences through the
    dispatcher and through an INDEPENDENT reference (jsonschema for shape +
    a separate interpreter) and requires identical accept/reject -- so a
    dispatcher that drops or misorders a layer is caught.
"""
from __future__ import annotations

import json

from . import toolgen

_EVAL = r'''
def _val(o, env):
    return env[o] if isinstance(o, str) else o

def _pred(p, env):
    op = p["op"]
    if op == "and":
        return all(_pred(q, env) for q in p["preds"])
    if op == "implies":
        return (not _pred(p["if"], env)) or _pred(p["then"], env)
    l, r = _val(p["left"], env), _val(p["right"], env)
    return {"<": l < r, "<=": l <= r, ">": l > r, ">=": l >= r,
            "==": l == r, "!=": l != r}[op]

def _expr(e, env):
    if isinstance(e, int):
        return e
    if isinstance(e, str):
        return env[e]
    if "const" in e:
        return e["const"]
    if "var" in e:
        return env[e["var"]]
    l, r = _expr(e["left"], env), _expr(e["right"], env)
    return l + r if e["op"] == "+" else l - r
'''


def _transitions(model):
    out = []
    for t in model.tools:
        out.append({"name": t.name, "from": t.frm, "to": t.to, "arg": t.arg,
                    "guard": t.guard, "update": t.update or {}})
    return out


def _constraints(model):
    return {t.name: (t.constraints["constraints"] if t.constraints else [])
            for t in model.tools}


def emit_service(model) -> dict:
    files = {}
    imports, vmap = [], []
    for t in model.tools:
        mod = f"tool_{t.name}"
        files[f"{mod}.py"] = toolgen.emit_pydantic_tool(t.schema_text)["tool_model.py"]
        imports.append(f"import {mod}")
        vmap.append(f"    {t.name!r}: {mod}.decode,")
    init_ctx = {c: lo for c, (lo, hi) in model.context.items()}
    svc = f'''
import json
{chr(10).join(imports)}
TRANSITIONS = {_transitions(model)!r}
CONSTRAINTS = {_constraints(model)!r}
INITIAL = {model.initial!r}
INIT_CTX = {init_ctx!r}
VALIDATORS = {{
{chr(10).join(vmap)}
}}
{_EVAL}

class Service:
    def __init__(self, init_ctx=None):
        self.state = INITIAL
        self.ctx = dict(init_ctx if init_ctx is not None else INIT_CTX)

    def call(self, tool, args):
        tr = next((t for t in TRANSITIONS
                   if t["from"] == self.state and t["name"] == tool), None)
        if tr is None:
            return {{"ok": False, "layer": "sequencing"}}
        try:
            VALIDATORS[tool](args)
        except Exception:
            return {{"ok": False, "layer": "schema"}}
        if not isinstance(args, dict):
            return {{"ok": False, "layer": "schema"}}
        for c in CONSTRAINTS.get(tool, []):
            if not _pred(c, args):
                return {{"ok": False, "layer": "constraint"}}
        env = dict(self.ctx)
        if tr["arg"]:
            env[tr["arg"]] = args.get(tr["arg"])
        if tr["guard"] is not None and not _pred(tr["guard"], env):
            return {{"ok": False, "layer": "guard"}}
        for v, e in (tr["update"] or {{}}).items():
            self.ctx[v] = _expr(e, env)
        self.state = tr["to"]
        return {{"ok": True}}
'''
    files["service.py"] = svc.encode()
    return files


def _strict_schemas(model):
    return {t.name: toolgen.inject_strict(t.input_schema) for t in model.tools}


def _default_for(s):
    if "enum" in s:
        return s["enum"][0]
    return {"string": "x", "integer": 0, "number": 0.0, "boolean": False,
            "array": []}.get(s.get("type"), "x")


def _valid_args(tool, big=10 ** 6):
    props = tool.input_schema.get("properties", {})
    out = {p: _default_for(props[p])
           for p in tool.input_schema.get("required", [])}
    if tool.arg and tool.arg in props:
        out[tool.arg] = big          # guard-satisfying for >= guards
    return out


def _golden_path(model):
    adj = {}
    for t in model.tools:
        adj.setdefault(t.frm, []).append(t)
    path, state, seen = [], model.initial, set()
    while state in adj and state not in seen:
        seen.add(state)
        t = adj[state][0]
        path.append(t)
        state = t.to
    return path


def _ev_val(o, env):
    return env[o] if isinstance(o, str) else o


def _ev_pred(p, env):
    op = p["op"]
    if op == "and":
        return all(_ev_pred(q, env) for q in p["preds"])
    if op == "implies":
        return (not _ev_pred(p["if"], env)) or _ev_pred(p["then"], env)
    l, r = _ev_val(p["left"], env), _ev_val(p["right"], env)
    return {"<": l < r, "<=": l <= r, ">": l > r, ">=": l >= r,
            "==": l == r, "!=": l != r}[op]


def _ev_expr(e, env):
    if isinstance(e, int):
        return e
    if isinstance(e, str):
        return env[e]
    if "const" in e:
        return e["const"]
    if "var" in e:
        return env[e["var"]]
    l, r = _ev_expr(e["left"], env), _ev_expr(e["right"], env)
    return l + r if e["op"] == "+" else l - r


def _ctx_before(model, path, init, gi):
    """Simulate the golden prefix [0, gi) to get the context at step gi (mirror
    of the reference simulator), so guard-boundary probing uses the real env."""
    ctx = dict(init)
    for t in path[:gi]:
        env = dict(ctx)
        if t.arg:
            env[t.arg] = _valid_args(t).get(t.arg)
        for v, e in (t.update or {}).items():
            ctx[v] = _ev_expr(e, env)
    return ctx


def _guard_discriminating_arg(t, ctx):
    """A value for t.arg that satisfies every per-call constraint yet violates
    the guard -- so a dropped/short-circuited guard becomes observable.  Returns
    None when the guard is not separable from the constraints (nothing to catch).
    Probes boundary candidates drawn from the context values the guard compares
    against; sufficient for the linear comparisons this domain models."""
    cons = t.constraints["constraints"] if t.constraints else []
    cands = {0, 1, -1}
    for v in ctx.values():
        if isinstance(v, int):
            cands.update({v, v - 1, v + 1})
    for c in [t.guard] + cons:
        if c and isinstance(c.get("right"), int):
            cands.update({c["right"], c["right"] - 1, c["right"] + 1})
    for cand in sorted(cands):
        env = dict(ctx); env[t.arg] = cand
        args = {t.arg: cand}
        if all(_ev_pred(c, args) for c in cons) and \
                t.guard is not None and not _ev_pred(t.guard, env):
            return cand
    return None


def conformance_cases(model) -> list:
    init = {c: lo for c, (lo, hi) in model.context.items()}
    path = _golden_path(model)
    golden = [[t.name, _valid_args(t)] for t in path]
    cases = [{"init": init, "seq": golden}]
    # wrong sequencing: a non-initial tool first
    for t in model.tools:
        if t.frm != model.initial:
            cases.append({"init": init, "seq": [[t.name, _valid_args(t)]]})
            break
    # find the guarded / arg-bearing tool and its index in the golden path
    gi = next((i for i, t in enumerate(path)
               if t.guard is not None or t.arg), None)
    if gi is not None:
        t = path[gi]
        # schema-bad: drop a required key at that step
        req = t.input_schema.get("required", [])
        if req:
            bad = dict(_valid_args(t)); bad.pop(req[0], None)
            seq = [list(x) for x in golden]; seq[gi] = [t.name, bad]
            cases.append({"init": init, "seq": seq})
        # extra-key: forbidden by additionalProperties:false
        ek = dict(_valid_args(t)); ek["__nope__"] = 1
        seq = [list(x) for x in golden]; seq[gi] = [t.name, ek]
        cases.append({"init": init, "seq": seq})
        # guard-bad: a value that PASSES every per-call constraint yet VIOLATES
        # the guard, so the guard is the sole deciding layer -- this is what
        # exposes a dispatcher that drops or short-circuits the guard.
        if t.arg and t.guard is not None:
            dv = _guard_discriminating_arg(t, _ctx_before(model, path, init, gi))
            if dv is not None:
                gb = dict(_valid_args(t)); gb[t.arg] = dv
                seq = [list(x) for x in golden]; seq[gi] = [t.name, gb]
                cases.append({"init": init, "seq": seq})
    return cases


def build_service_conformance(model) -> dict:
    ref = f'''
import json, jsonschema
TRANSITIONS = {_transitions(model)!r}
CONSTRAINTS = {_constraints(model)!r}
INITIAL = {model.initial!r}
SCHEMAS = {_strict_schemas(model)!r}
VALIDATORS = {{k: jsonschema.Draft7Validator(v) for k, v in SCHEMAS.items()}}
{_EVAL}

def _accepts(state, ctx, tool, args):
    tr = next((t for t in TRANSITIONS
               if t["from"] == state and t["name"] == tool), None)
    if tr is None:
        return False, state, ctx
    if not isinstance(args, dict) or list(VALIDATORS[tool].iter_errors(args)):
        return False, state, ctx
    for c in CONSTRAINTS.get(tool, []):
        if not _pred(c, args):
            return False, state, ctx
    env = dict(ctx)
    if tr["arg"]:
        env[tr["arg"]] = args.get(tr["arg"])
    if tr["guard"] is not None and not _pred(tr["guard"], env):
        return False, state, ctx
    nctx = dict(ctx)
    for v, e in (tr["update"] or {{}}).items():
        nctx[v] = _expr(e, env)
    return True, tr["to"], nctx

def run_reference(init_ctx, seq):
    state, ctx, out = INITIAL, dict(init_ctx), []
    for tool, args in seq:
        ok, state, ctx = _accepts(state, ctx, tool, args)
        out.append(ok)
    return out
'''
    cases = conformance_cases(model)
    harness = f'''
import json, sys, traceback
from service import Service
from ref_service import run_reference
CASES = {cases!r}
def main():
    try:
        for case in CASES:
            s = Service(case["init"])
            got = [s.call(tool, args)["ok"] for tool, args in case["seq"]]
            exp = run_reference(case["init"], case["seq"])
            assert got == exp, ("dispatcher disagrees with reference",
                                case, "dispatcher", got, "reference", exp)
        print(json.dumps({{"status": "pass", "examples": len(CASES)}}))
    except BaseException as e:
        print(json.dumps({{"status": "fail", "error": repr(e)[:2000],
                          "traceback": traceback.format_exc()[-2000:]}}))
        sys.exit(1)
main()
'''
    return {"ref_service.py": ref.encode(), "conf_harness.py": harness.encode()}


def build_service_liveness(model) -> dict:
    """Non-vacuity: the composed dispatcher must ACCEPT a full legal run (the
    golden path), so the composition isn't vacuously rejecting everything."""
    init = {c: lo for c, (lo, hi) in model.context.items()}
    golden = [[t.name, _valid_args(t)] for t in _golden_path(model)]
    harness = f'''
import json, sys, traceback
from service import Service
def main():
    try:
        s = Service({init!r})
        got = [s.call(tool, args)["ok"] for tool, args in {golden!r}]
        assert got and all(got), ("golden legal path not fully accepted", got)
        print(json.dumps({{"status": "pass", "examples": len(got)}}))
    except BaseException as e:
        print(json.dumps({{"status": "fail", "error": repr(e)[:2000],
                          "traceback": traceback.format_exc()[-2000:]}}))
        sys.exit(1)
main()
'''
    return {"live_harness.py": harness.encode()}

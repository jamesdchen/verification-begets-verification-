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


def _obligations(model):
    return list(getattr(model, "obligations", []) or [])


def _terminal_tools(model):
    return sorted(t.name for t in model.tools if getattr(t, "terminal", False))


def _monitor_data(model):
    """Per-obligation certified monitor: its canonical table, initial state and
    permanent (non-pending) state set, read from generators.monitor_gen.  Only
    called when the service HAS obligations, so it never runs (nor imports
    flloat) for a plain service -- keeping emitted sources byte-identical."""
    from generators import monitor_gen
    alphabet = [t.name for t in model.tools]
    tables, initial, perm = {}, {}, {}
    for o in _obligations(model):
        params = {k: v for k, v in o.items() if k not in ("id", "kind")}
        r = monitor_gen.build_monitor(o["kind"], params, alphabet)
        parsed = monitor_gen.parse_monitor_module(r["monitor.py"])
        tables[o["id"]] = parsed["TABLE"]
        initial[o["id"]] = parsed["INITIAL"]
        perm[o["id"]] = r["meta"]["permanent"]
    return tables, initial, perm


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
    # CONDITIONAL EMISSION (house rule 8): the monitor machinery appears ONLY
    # when the service declares temporal obligations.  For a plain service every
    # `{...}` below is the empty string, so the bytes are IDENTICAL to pre-P1.
    mon_consts = mon_init = obl_check = mon_adv = ""
    if _obligations(model):
        tables, minitial, perm = _monitor_data(model)
        mon_consts = (f"\nMON_TABLES = {tables!r}\nMON_INITIAL = {minitial!r}\n"
                      f"MON_PERM = {perm!r}\nTERMINAL_TOOLS = "
                      f"{_terminal_tools(model)!r}")
        mon_init = "\n        self.mon = dict(MON_INITIAL)"
        # obligation layer: a terminal tool is refused while ANY monitor pends
        # (a state not in its permanent/non-pending set).  Checked AFTER the
        # guard, using the PRE-advance monitor states.
        obl_check = (
            '\n        if tool in TERMINAL_TOOLS and any('
            '\n                self.mon[o] not in MON_PERM[o] for o in MON_INITIAL):'
            '\n            return {"ok": False, "layer": "obligation"}')
        # monitors advance on the ACCEPTED call (this tool)
        mon_adv = ("\n        for o in MON_INITIAL:"
                   "\n            self.mon[o] = MON_TABLES[o][self.mon[o]][tool]")
    svc = f'''
import json
{chr(10).join(imports)}
TRANSITIONS = {_transitions(model)!r}
CONSTRAINTS = {_constraints(model)!r}
INITIAL = {model.initial!r}
INIT_CTX = {init_ctx!r}
VALIDATORS = {{
{chr(10).join(vmap)}
}}{mon_consts}
{_EVAL}

class Service:
    def __init__(self, init_ctx=None):
        self.state = INITIAL
        self.ctx = dict(init_ctx if init_ctx is not None else INIT_CTX){mon_init}

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
            return {{"ok": False, "layer": "guard"}}{obl_check}
        for v, e in (tr["update"] or {{}}).items():
            self.ctx[v] = _expr(e, env)
        self.state = tr["to"]{mon_adv}
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


def _required_defaults(tool):
    """Required NON-solved fields with type defaults; the guard/constraint-
    relevant integer fields are filled in by the solver, not guessed."""
    props = tool.input_schema.get("properties", {})
    return {p: _default_for(props[p])
            for p in tool.input_schema.get("required", [])}


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


def _adj(model):
    adj = {}
    for t in model.tools:
        adj.setdefault(t.frm, []).append(t)
    return adj


def _golden_path_oblig(model):
    """P1.7 obligation-aware golden run: BFS over (control-state, monitor-states)
    configurations for a path that reaches a TERMINAL tool with EVERY obligation
    DISCHARGED (all monitors non-pending), honouring the dispatcher rule that a
    terminal tool is refused while any monitor pends.

    The greedy _golden_path builds a run a CORRECT service (with refusal-at-close)
    refuses, so liveness would fail on green services -- this search finds a run
    the service actually admits and completes.  Returns the tool path or None."""
    from collections import deque
    tables, minitial, perm = _monitor_data(model)
    oids = [o["id"] for o in _obligations(model)]
    permset = {o: set(perm[o]) for o in oids}
    term = set(_terminal_tools(model))
    adj = _adj(model)
    start = (model.initial, tuple(minitial[o] for o in oids))
    q = deque([(start, [])])
    seen = {start}
    while q:
        (state, mons), path = q.popleft()
        pending = [mons[i] not in permset[oids[i]] for i in range(len(oids))]
        for t in adj.get(state, []):
            if t.name in term and any(pending):
                continue                    # dispatcher refuses; not a valid step
            npath = path + [t]
            if t.name in term:              # a discharged terminal: session done
                return npath
            nmons = tuple(tables[oids[i]][mons[i]][t.name]
                          for i in range(len(oids)))
            cfg = (t.to, nmons)
            if cfg not in seen:
                seen.add(cfg)
                q.append((cfg, npath))
    return None


def _run_path(model):
    """The path the golden-run solver follows: obligation-aware when the service
    has temporal demands, else the greedy first-outgoing walk (unchanged, so
    plain services stay byte-identical)."""
    return _golden_path_oblig(model) if _obligations(model) \
        else _golden_path(model)


def _stranding_attempts(model):
    """B2 tooth: for each terminal tool, a trace that reaches its from-state with
    an obligation STILL PENDING and then attempts the terminal.  A correct
    dispatcher (and the reference) refuse that terminal at the obligation layer;
    a dispatcher with the monitor wiring dropped accepts it -- so the
    conformance differential catches the dropped wiring on exactly this trace."""
    from collections import deque
    if not _obligations(model):
        return []
    tables, minitial, perm = _monitor_data(model)
    oids = [o["id"] for o in _obligations(model)]
    permset = {o: set(perm[o]) for o in oids}
    term = set(_terminal_tools(model))
    adj = _adj(model)
    lo_init = {c: lo for c, (lo, hi) in model.context.items()}
    cases = []
    for T in model.tools:
        if not getattr(T, "terminal", False):
            continue
        start = (model.initial, tuple(minitial[o] for o in oids))
        q = deque([(start, [])])
        seen = {start}
        found = None
        while q:
            (state, mons), path = q.popleft()
            pending = any(mons[i] not in permset[oids[i]]
                          for i in range(len(oids)))
            if state == T.frm and pending:
                found = path
                break
            for t in adj.get(state, []):
                if t.name in term:          # don't discharge via a terminal en route
                    continue
                nmons = tuple(tables[oids[i]][mons[i]][t.name]
                              for i in range(len(oids)))
                cfg = (t.to, nmons)
                if cfg not in seen:
                    seen.add(cfg)
                    q.append((cfg, path + [t]))
        if found is not None:
            seq = [[t.name, _required_defaults(t)] for t in found]
            seq.append([T.name, _required_defaults(T)])
            cases.append({"init": lo_init, "seq": seq})
    return cases


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


def _z3_expr(e, zvars):
    if isinstance(e, bool):
        return 1 if e else 0
    if isinstance(e, int):
        return e
    if isinstance(e, str):
        return zvars[e]
    if "const" in e:
        return e["const"]
    if "var" in e:
        return zvars[e["var"]]
    l, r = _z3_expr(e["left"], zvars), _z3_expr(e["right"], zvars)
    return l + r if e["op"] == "+" else l - r


def _pred_names(p, out):
    op = p.get("op")
    if op == "and":
        for q in p["preds"]:
            _pred_names(q, out)
        return
    if op == "implies":
        _pred_names(p["if"], out); _pred_names(p["then"], out)
        return
    for side in ("left", "right"):
        if isinstance(p.get(side), str):
            out.add(p[side])


def _z3_pred(p, zvars):
    import z3
    op = p["op"]
    if op == "and":
        return z3.And([_z3_pred(q, zvars) for q in p["preds"]])
    if op == "implies":
        return z3.Implies(_z3_pred(p["if"], zvars), _z3_pred(p["then"], zvars))
    l = zvars[p["left"]] if isinstance(p["left"], str) else p["left"]
    r = zvars[p["right"]] if isinstance(p["right"], str) else p["right"]
    return {"<": l < r, "<=": l <= r, ">": l > r, ">=": l >= r,
            "==": l == r, "!=": l != r}[op]


def _solver_guard_input(t, ctx):
    """Solver-as-adversary for the COMPOSITION, mirroring the constraint/protocol
    layers.  Ask Z3 for an assignment of the tool's integer input fields that
    satisfies EVERY per-call constraint yet FALSIFIES the guard, with the context
    fixed to its golden-prefix value.  That input is legal at the schema and
    constraint layers and illegal only at the guard, so a dispatcher that drops
    or short-circuits the guard is provably observable.  Returns {field: int} for
    the freed fields, or None when the guard is not separable from the
    constraints (UNSAT -> nothing to catch) or the fields fall outside the
    integer fragment this generator models (skip honestly)."""
    if t.guard is None:
        return None
    import z3
    import common
    cons = t.constraints["constraints"] if t.constraints else []
    names = set()
    _pred_names(t.guard, names)
    for c in cons:
        _pred_names(c, names)
    props = t.input_schema.get("properties", {})
    with common.SMT_LOCK:                 # z3 default context is not thread-safe
        zvars, free = {}, []
        for n in names:
            if n in ctx:                                   # context: concrete
                zvars[n] = z3.IntVal(ctx[n])
            elif props.get(n, {}).get("type") == "integer":  # free int field
                zvars[n] = z3.Int(n); free.append(n)
            else:
                return None                            # non-integer -> unsupported
        s = z3.Solver()
        s.add([_z3_pred(c, zvars) for c in cons])
        s.add(z3.Not(_z3_pred(t.guard, zvars)))
        if s.check() != z3.sat:
            return None
        m = s.model()
        return {n: m.eval(zvars[n], model_completion=True).as_long()
                for n in free}


def _legal_golden_run(model):
    """Solve (Z3) for a FULLY LEGAL run of the canonical first-outgoing path:
    initial context values within their declared ranges PLUS per-step integer
    arguments, such that every step satisfies its per-call constraints AND its
    guard under the symbolic running context.  Unlike a guessed 'valid args',
    this handles upper-bound guards (count <= seats_left), guards coupled to
    context, and contexts whose *minimum* admits no legal move -- the solver
    picks initial values that make a legal run exist.

    Returns (init_ctx, seq, prefix_ctx) with concrete values -- seq is
    [[tool, args], ...], prefix_ctx[i] the context before step i -- or None when
    no legal run exists along that path (an honest liveness failure: the
    composition would be vacuous), or when a field is outside the integer
    fragment this generator models."""
    import z3
    import common
    path = _run_path(model)
    if not path:
        return None
    with common.SMT_LOCK:                 # z3 default context is not thread-safe
        s = z3.Solver()
        env = {}
        for c, (lo, hi) in model.context.items():
            v = z3.Int(f"c0_{c}")
            s.add(v >= lo, v <= hi)
            env[c] = v
        steps = []
        for i, t in enumerate(path):
            cons = t.constraints["constraints"] if t.constraints else []
            names = set()
            if t.guard is not None:
                _pred_names(t.guard, names)
            for c in cons:
                _pred_names(c, names)
            if t.arg:
                names.add(t.arg)
            props = t.input_schema.get("properties", {})
            local, free = dict(env), {}
            for n in names:
                if n in env:
                    continue                   # context var: already symbolic
                if props.get(n, {}).get("type") == "integer":
                    fv = z3.Int(f"s{i}_{n}"); free[n] = fv; local[n] = fv
                else:
                    return None                # non-integer field -> unsupported
            for c in cons:
                s.add(_z3_pred(c, local))
            if t.guard is not None:
                s.add(_z3_pred(t.guard, local))
            steps.append((t, free))
            nenv = dict(env)
            for var, expr in (t.update or {}).items():
                nenv[var] = _z3_expr(expr, local)
            env = nenv
        if not steps or s.check() != z3.sat:
            return None
        m = s.model()
        init = {c: m.eval(z3.Int(f"c0_{c}"), model_completion=True).as_long()
                for c in model.context}
        seq, prefix_ctx, ctx = [], [], dict(init)
        for t, free in steps:
            args = _required_defaults(t)
            for n, fv in free.items():
                args[n] = m.eval(fv, model_completion=True).as_long()
            prefix_ctx.append(dict(ctx))
            seq.append([t.name, args])
            cenv = dict(ctx); cenv.update({n: args[n] for n in free})
            for var, expr in (t.update or {}).items():
                ctx[var] = _ev_expr(expr, cenv)
        return init, seq, prefix_ctx


def conformance_cases(model) -> list:
    lo_init = {c: lo for c, (lo, hi) in model.context.items()}
    run = _legal_golden_run(model)

    def wrong_seq(init):
        for t in model.tools:
            if t.frm != model.initial:
                return [{"init": init, "seq": [[t.name, _required_defaults(t)]]}]
        return []

    if run is None:
        # no legal golden run: liveness fails honestly; still emit the negative
        # wrong-sequencing case so the differential is non-empty.
        return wrong_seq(lo_init) + _stranding_attempts(model)
    init, golden, prefix_ctx = run
    path = _run_path(model)
    cases = [{"init": init, "seq": [list(x) for x in golden]}]
    cases += wrong_seq(init)
    # P1.6/B2: obligation-layer cases -- reach a terminal while pending; the
    # correct dispatcher and reference refuse, a dropped-wiring dispatcher does
    # not (caught by the differential).
    cases += _stranding_attempts(model)
    gi = next((i for i, t in enumerate(path)
               if t.guard is not None or t.arg), None)
    if gi is not None:
        t = path[gi]
        # schema-bad: drop a required key at that step
        req = t.input_schema.get("required", [])
        if req:
            bad = dict(golden[gi][1]); bad.pop(req[0], None)
            seq = [list(x) for x in golden]; seq[gi] = [t.name, bad]
            cases.append({"init": init, "seq": seq})
        # extra-key: forbidden by additionalProperties:false
        ek = dict(golden[gi][1]); ek["__nope__"] = 1
        seq = [list(x) for x in golden]; seq[gi] = [t.name, ek]
        cases.append({"init": init, "seq": seq})
        # guard-bad: a value that PASSES every per-call constraint yet VIOLATES
        # the guard, so the guard is the sole deciding layer -- exposes a
        # dispatcher that drops or short-circuits the guard.  Uses the solved
        # concrete context reached just before the guarded step.
        if t.arg and t.guard is not None:
            sol = _solver_guard_input(t, prefix_ctx[gi])
            if sol is not None:
                gb = dict(golden[gi][1]); gb.update(sol)
                seq = [list(x) for x in golden]; seq[gi] = [t.name, gb]
                cases.append({"init": init, "seq": seq})
    return cases


def ref_service_source(model) -> str:
    """Source of the INDEPENDENT jsonschema-based reference service -- a
    separate interpreter of the meta-spec sharing no code with the emitted
    dispatcher.  Used by the conformance differential and by the intent-scenario
    check (both implementations must match the independently-derived
    expectations).

    SYMMETRIC-IMPLEMENTATION rule (house rule 7): the monitor wiring the
    dispatcher adds (advance-on-accept, refuse-terminal-while-pending) is
    re-implemented HERE independently -- a different control structure over the
    SAME certified monitor tables -- so a dropped/misordered monitor in the
    dispatcher is caught by the differential.  CONDITIONAL EMISSION: a plain
    service (no obligations) emits byte-identical bytes to pre-P1."""
    mon_consts = ""
    if _obligations(model):
        tables, minitial, perm = _monitor_data(model)
        mon_consts = (f"\nMON_TABLES = {tables!r}\nMON_INITIAL = {minitial!r}\n"
                      f"MON_PERM = {perm!r}\nTERMINAL_TOOLS = "
                      f"{_terminal_tools(model)!r}")
    if _obligations(model):
        run_ref_body = (
            "    state, ctx, mon, out = INITIAL, dict(init_ctx), "
            "dict(MON_INITIAL), []\n"
            "    for tool, args in seq:\n"
            "        ok, nstate, nctx = _accepts(state, ctx, tool, args)\n"
            "        if ok and tool in TERMINAL_TOOLS and any(\n"
            "                mon[o] not in MON_PERM[o] for o in MON_INITIAL):\n"
            "            ok = False\n"
            "        if ok:\n"
            "            state, ctx = nstate, nctx\n"
            "            for o in MON_INITIAL:\n"
            "                mon[o] = MON_TABLES[o][mon[o]][tool]\n"
            "        out.append(ok)\n"
            "    return out")
    else:
        run_ref_body = (
            "    state, ctx, out = INITIAL, dict(init_ctx), []\n"
            "    for tool, args in seq:\n"
            "        ok, state, ctx = _accepts(state, ctx, tool, args)\n"
            "        out.append(ok)\n"
            "    return out")
    return f'''
import json, jsonschema
TRANSITIONS = {_transitions(model)!r}
CONSTRAINTS = {_constraints(model)!r}
INITIAL = {model.initial!r}
SCHEMAS = {_strict_schemas(model)!r}
VALIDATORS = {{k: jsonschema.Draft7Validator(v) for k, v in SCHEMAS.items()}}{mon_consts}
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
{run_ref_body}
'''


def build_service_conformance(model) -> dict:
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
    return {"ref_service.py": ref_service_source(model).encode(),
            "conf_harness.py": harness.encode()}


def build_service_liveness(model) -> dict:
    """Non-vacuity: the composed dispatcher must ACCEPT a full legal run (a
    solver-certified legal golden path), so the composition isn't vacuously
    rejecting everything.  If no legal run exists the golden path is empty and
    this witness fails -- the honest verdict that the composition is vacuous."""
    run = _legal_golden_run(model)
    init, golden = ({c: lo for c, (lo, hi) in model.context.items()}, []) \
        if run is None else (run[0], run[1])
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


def _scenario_replay(runner_setup, scenarios) -> str:
    """A harness replaying scenario traces through `run(sc)` (defined by
    runner_setup) and asserting the accept/reject list equals the scenario's
    independently-authored expectations."""
    return f'''
import json, sys, traceback
{runner_setup}
SCENARIOS = {scenarios!r}
def main():
    try:
        for sc in SCENARIOS:
            got = run(sc)
            assert got == sc["expect"], (
                "scenario expectation violated", sc["name"],
                "trace", sc["seq"], "expected", sc["expect"], "got", got)
        print(json.dumps({{"status": "pass", "examples": len(SCENARIOS)}}))
    except BaseException as e:
        print(json.dumps({{"status": "fail", "error": repr(e)[:2000],
                          "traceback": traceback.format_exc()[-2000:]}}))
        sys.exit(1)
main()
'''


def build_scenario_dispatcher_harness(scenarios: list) -> dict:
    """Intent channel 1: the certified dispatcher replays the independently-
    authored scenarios and must reproduce their accept/reject expectations."""
    setup = ('from service import Service\n'
             'def run(sc):\n'
             '    s = Service(sc["init"])\n'
             '    return [s.call(t, a)["ok"] for t, a in sc["seq"]]')
    return {"scn_harness.py": _scenario_replay(setup, scenarios).encode()}


def build_scenario_reference_harness(model, scenarios: list) -> dict:
    """Intent channel 2: the INDEPENDENT reference service replays the same
    scenarios; both implementations must match the same expectations."""
    setup = ('from ref_service import run_reference\n'
             'def run(sc):\n'
             '    return run_reference(sc["init"], sc["seq"])')
    return {"ref_service.py": ref_service_source(model).encode(),
            "scn_ref_harness.py": _scenario_replay(setup, scenarios).encode()}

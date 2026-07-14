"""Emit, from a protocol spec:

  * a bounded-model-checking SMT obligation (built in Z3, exported as SMT-LIB
    so BOTH Z3 and CVC5 check the same thing) -- safety: no state violating the
    invariant is reachable via legal transitions within the bound;
  * a counterexample trace when the protocol is unsafe (the solver's shortest
    illegal call sequence -- solver-as-adversary, lifted from single inputs to
    *traces*);
  * a Python session validator (does this call sequence obey the protocol?),
    executed sandboxed;
  * conformance test traces (legal + illegal) so the emitted validator can be
    differentialled against an independent reference simulator.
"""
from __future__ import annotations

import json

from .protocol_model import ProtocolModel, Action


# --------------------------------------------------------------- z3 / BMC
def _atom_z3(o, ctx_i, argname, argvar):
    if isinstance(o, int):
        return o
    if argname is not None and o == argname:
        return argvar
    return ctx_i[o]


def _expr_z3(e, ctx_i, argname, argvar):
    if isinstance(e, int):
        return e
    if isinstance(e, str):
        return _atom_z3(e, ctx_i, argname, argvar)
    if "const" in e:
        return e["const"]
    if "var" in e:
        return _atom_z3(e["var"], ctx_i, argname, argvar)
    l = _expr_z3(e["left"], ctx_i, argname, argvar)
    r = _expr_z3(e["right"], ctx_i, argname, argvar)
    return l + r if e["op"] == "+" else l - r


def _pred_z3(pred, ctx_i, argname, argvar):
    import z3
    op = pred["op"]
    if op == "and":
        return z3.And([_pred_z3(p, ctx_i, argname, argvar)
                       for p in pred["preds"]])
    if op == "implies":
        return z3.Implies(_pred_z3(pred["if"], ctx_i, argname, argvar),
                          _pred_z3(pred["then"], ctx_i, argname, argvar))
    l = _atom_z3(pred["left"], ctx_i, argname, argvar)
    r = _atom_z3(pred["right"], ctx_i, argname, argvar)
    return {"<": l < r, "<=": l <= r, ">": l > r, ">=": l >= r,
            "==": l == r, "!=": l != r}[op]


def build_bmc(model: ProtocolModel, K: int):
    """Returns (z3 Solver asserting: init AND legal-transitions AND a safety
    violation is reachable within K steps, vars)."""
    import z3
    s = z3.Solver()
    S = len(model.states)
    IDLE = len(model.actions)
    ctrl = [z3.Int(f"ctrl_{i}") for i in range(K + 1)]
    ctx = {c: [z3.Int(f"{c}_{i}") for i in range(K + 1)] for c in model.context}
    act = [z3.Int(f"act_{i}") for i in range(K)]
    arg = [z3.Int(f"arg_{i}") for i in range(K)]

    s.add(ctrl[0] == model.idx(model.initial))
    for c, (lo, hi) in model.context.items():
        s.add(ctx[c][0] >= lo, ctx[c][0] <= hi)

    for i in range(K):
        ci = {c: ctx[c][i] for c in model.context}
        disj = []
        for aidx, a in enumerate(model.actions):
            conj = [act[i] == aidx, ctrl[i] == model.idx(a.frm),
                    ctrl[i + 1] == model.idx(a.to)]
            if a.guard is not None:
                conj.append(_pred_z3(a.guard, ci, a.arg, arg[i]))
            for c in model.context:
                if c in a.update:
                    conj.append(ctx[c][i + 1] ==
                                _expr_z3(a.update[c], ci, a.arg, arg[i]))
                else:
                    conj.append(ctx[c][i + 1] == ctx[c][i])
            disj.append(z3.And(conj))
        idle = [act[i] == IDLE, ctrl[i + 1] == ctrl[i]] + \
            [ctx[c][i + 1] == ctx[c][i] for c in model.context]
        disj.append(z3.And(idle))
        s.add(z3.Or(disj))
        s.add(act[i] >= 0, act[i] <= IDLE)

    glob = model.safety["when"] == "*"   # G(inv): every reachable state
    when = None if glob else model.idx(model.safety["when"])
    inv = model.safety["invariant"]
    viol = []
    for i in range(K + 1):
        ci = {c: ctx[c][i] for c in model.context}
        bad = z3.Not(_pred_z3(inv, ci, None, None))
        viol.append(bad if glob else z3.And(ctrl[i] == when, bad))
    s.add(z3.Or(viol))
    return s, {"ctrl": ctrl, "ctx": ctx, "act": act, "arg": arg, "IDLE": IDLE}


def bmc_smtlib(model: ProtocolModel, K: int) -> str:
    s, _ = build_bmc(model, K)
    text = "(set-logic QF_LIA)\n" + s.to_smt2()
    if "(check-sat)" not in text:
        text += "\n(check-sat)\n"
    return text


def counterexample(model: ProtocolModel, K: int):
    """If unsafe, return the solver's shortest illegal trace: (init, steps)."""
    import z3
    s, v = build_bmc(model, K)
    if s.check() != z3.sat:
        return None
    m = s.model()
    init = {c: m[v["ctx"][c][0]].as_long() for c in model.context}
    steps = []
    for i in range(K):
        a = m[v["act"][i]]
        a = a.as_long() if a is not None else v["IDLE"]
        if a >= len(model.actions):
            break
        act = model.actions[a]
        av = m[v["arg"][i]]
        steps.append([act.name, (av.as_long() if av is not None else 0)
                      if act.arg else None])
    return {"init": init, "trace": steps}


# ------------------------------------------------------------ Python emit
def _atom_py(o, argname):
    if isinstance(o, int):
        return str(o)
    if argname is not None and o == argname:
        return "arg"
    return f"ctx[{o!r}]"


def _expr_py(e, argname):
    if isinstance(e, int):
        return str(e)
    if isinstance(e, str):
        return _atom_py(e, argname)
    if "const" in e:
        return str(e["const"])
    if "var" in e:
        return _atom_py(e["var"], argname)
    return f"({_expr_py(e['left'], argname)} {e['op']} {_expr_py(e['right'], argname)})"


def _pred_py(pred, argname):
    op = pred["op"]
    if op == "and":
        return "(" + " and ".join(_pred_py(p, argname)
                                  for p in pred["preds"]) + ")"
    if op == "implies":
        return (f"((not {_pred_py(pred['if'], argname)}) or "
                f"{_pred_py(pred['then'], argname)})")
    pyop = {"==": "==", "!=": "!="}.get(op, op)
    return f"({_atom_py(pred['left'], argname)} {pyop} {_atom_py(pred['right'], argname)})"


def emit_validator(model: ProtocolModel) -> dict:
    ctx_keys = set(model.context)
    lines = [
        "def accepts(data):",
        "    if not isinstance(data, dict) or set(data.keys()) != {'init', 'trace'}:",
        "        return False",
        "    init, trace = data['init'], data['trace']",
        f"    if not isinstance(init, dict) or set(init.keys()) != {ctx_keys!r}:",
        "        return False",
        "    if not isinstance(trace, list):",
        "        return False",
    ]
    for c, (lo, hi) in model.context.items():
        lines.append(f"    if type(init[{c!r}]) is not int or not "
                     f"({lo} <= init[{c!r}] <= {hi}):")
        lines.append("        return False")
    lines += [
        "    ctx = dict(init)",
        f"    state = {model.initial!r}",
        "    for step in trace:",
        "        if not (isinstance(step, list) and len(step) == 2):",
        "            return False",
        "        name, arg = step",
    ]
    first = True
    for a in model.actions:
        kw = "if" if first else "elif"
        first = False
        cond = f"state == {a.frm!r} and name == {a.name!r}"
        lines.append(f"        {kw} {cond}:")
        if a.arg:
            lines.append("            if type(arg) is not int:")
            lines.append("                return False")
        else:
            lines.append("            if arg is not None:")
            lines.append("                return False")
        if a.guard is not None:
            lines.append(f"            if not {_pred_py(a.guard, a.arg)}:")
            lines.append("                return False")
        for c, e in a.update.items():
            lines.append(f"            ctx[{c!r}] = {_expr_py(e, a.arg)}")
        lines.append(f"            state = {a.to!r}")
    lines += [
        "        else:",
        "            return False",
        "    return True",
    ]
    return {"validator.py": ("\n".join(lines) + "\n").encode()}


# ------------------------------------------ conformance: traces + reference
def _table(model: ProtocolModel) -> dict:
    return {
        "initial": model.initial,
        "context": {c: list(v) for c, v in model.context.items()},
        "actions": [{"name": a.name, "from": a.frm, "to": a.to, "arg": a.arg,
                     "guard": a.guard, "update": a.update}
                    for a in model.actions],
    }


def conformance_traces(model: ProtocolModel, K: int) -> list:
    """Legal traces (control paths with solver-satisfied guards) plus illegal
    ones (wrong-state action; guard-violating argument)."""
    import z3
    cases = []
    # empty trace: always legal, ends in initial
    lo0 = {c: v[0] for c, v in model.context.items()}
    cases.append({"init": lo0, "trace": []})
    # BFS legal control paths, solve for a concrete init+args
    from collections import deque
    dq = deque([(model.initial, [])])
    paths = []
    while dq:
        st, path = dq.popleft()
        if len(path) >= K:
            continue
        for a in model.actions:
            if a.frm == st:
                np = path + [a]
                paths.append(np)
                dq.append((a.to, np))
    def _solve(path, negate_last):
        s = z3.Solver()
        ctx = {c: z3.Int(f"c_{c}") for c in model.context}
        for c, (lo, hi) in model.context.items():
            s.add(ctx[c] >= lo, ctx[c] <= hi)
        args = []
        cur = dict(ctx)
        for j, a in enumerate(path):
            av = z3.Int(f"a_{j}")
            args.append(av if a.arg else None)
            last = (j == len(path) - 1)
            if a.guard is not None:
                g = _pred_z3(a.guard, cur, a.arg, av)
                s.add(z3.Not(g) if (last and negate_last) else g)
            nxt = dict(cur)
            for c in model.context:
                if c in a.update:
                    nxt[c] = _expr_z3(a.update[c], cur, a.arg, av)
            cur = nxt
        if s.check() != z3.sat:
            return None
        m = s.model()
        # model_completion: an arg that appears in no guard along the path is
        # unconstrained, and m[var] would be None for it
        def val(v):
            return m.eval(v, model_completion=True).as_long()
        return {"init": {c: val(ctx[c]) for c in model.context},
                "trace": [[a.name,
                           (val(args[j]) if args[j] is not None else 0)
                           if a.arg else None] for j, a in enumerate(path)]}

    for path in paths[:24]:
        legal = _solve(path, negate_last=False)
        if legal is not None:
            cases.append(legal)
        # a trace that violates exactly the last action's guard (illegal) --
        # this is what catches a validator that drops a guard check
        if path and path[-1].guard is not None:
            bad = _solve(path, negate_last=True)
            if bad is not None:
                cases.append(bad)
    # illegal: an action from the wrong state (not enabled initially)
    for a in model.actions:
        if a.frm != model.initial:
            cases.append({"init": lo0,
                          "trace": [[a.name, 0 if a.arg else None]]})
            break
    return cases


_REF_SIM = r'''
import json
TABLE = json.loads(r"""%s""")

def _atom(o, ctx, arg):
    if isinstance(o, int):
        return o
    return arg if o == "__arg__" else ctx[o]

def _resolve(o, argname):
    return "__arg__" if (isinstance(o, str) and o == argname) else o

def _expr(e, ctx, argname, arg):
    if isinstance(e, int):
        return e
    if isinstance(e, str):
        return _atom(_resolve(e, argname), ctx, arg)
    if "const" in e:
        return e["const"]
    if "var" in e:
        return _atom(_resolve(e["var"], argname), ctx, arg)
    l = _expr(e["left"], ctx, argname, arg); r = _expr(e["right"], ctx, argname, arg)
    return l + r if e["op"] == "+" else l - r

def _pred(p, ctx, argname, arg):
    op = p["op"]
    if op == "and":
        return all(_pred(q, ctx, argname, arg) for q in p["preds"])
    if op == "implies":
        return (not _pred(p["if"], ctx, argname, arg)) or _pred(p["then"], ctx, argname, arg)
    l = _atom(_resolve(p["left"], argname), ctx, arg)
    r = _atom(_resolve(p["right"], argname), ctx, arg)
    return {"<": l < r, "<=": l <= r, ">": l > r, ">=": l >= r,
            "==": l == r, "!=": l != r}[op]

def legal(data):
    if not isinstance(data, dict) or set(data.keys()) != {"init", "trace"}:
        return False
    init, trace = data["init"], data["trace"]
    ctxkeys = set(TABLE["context"])
    if not isinstance(init, dict) or set(init.keys()) != ctxkeys:
        return False
    for c, (lo, hi) in TABLE["context"].items():
        if type(init[c]) is not int or not (lo <= init[c] <= hi):
            return False
    if not isinstance(trace, list):
        return False
    ctx = dict(init); state = TABLE["initial"]
    for step in trace:
        if not (isinstance(step, list) and len(step) == 2):
            return False
        name, arg = step
        act = next((a for a in TABLE["actions"]
                    if a["from"] == state and a["name"] == name), None)
        if act is None:
            return False
        if act["arg"]:
            if type(arg) is not int:
                return False
        elif arg is not None:
            return False
        if act["guard"] is not None and not _pred(act["guard"], ctx, act["arg"], arg):
            return False
        newctx = dict(ctx)
        for c, e in (act["update"] or {}).items():
            newctx[c] = _expr(e, ctx, act["arg"], arg)
        ctx = newctx; state = act["to"]
    return True
'''


def build_conformance_harness(model: ProtocolModel, cases: list) -> dict:
    ref = _REF_SIM % json.dumps(_table(model))
    harness = f'''
import json, sys, traceback
from validator import accepts
from refsim import legal
CASES = {cases!r}
def main():
    try:
        for data in CASES:
            a, b = bool(accepts(data)), bool(legal(data))
            assert a == b, ("validator disagrees with reference simulator",
                            data, "emitted", a, "reference", b)
        print(json.dumps({{"status": "pass", "examples": len(CASES)}}))
    except BaseException as e:
        print(json.dumps({{"status": "fail", "error": repr(e)[:2000],
                          "traceback": traceback.format_exc()[-2000:]}}))
        sys.exit(1)
main()
'''
    return {"refsim.py": ref.encode(), "conf_harness.py": harness.encode()}

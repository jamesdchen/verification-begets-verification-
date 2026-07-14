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

from .protocol_model import ProtocolModel, Action, STACK_DEPTH


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


def _unrolled(model: ProtocolModel, K: int):
    """Build the shared BMC skeleton: init + legal transitions over K steps, with
    the IDLE action as an ABSORBING SUFFIX.

    P1.3 idle discipline (proven blocker): the old encoding let IDLE fire at any
    step, so a spurious interior-idle model like ['IDLE','pay','IDLE','ship']
    satisfied the transition relation.  We now assert `act[i]==IDLE ->
    act[i+1]==IDLE`, making IDLE an absorbing suffix: a trace's real length is
    its first idle index and every real action forms a contiguous prefix.  Idle
    is a stutter (ctrl/ctx unchanged), so this removes only spurious models and
    never changes which states are reachable -- the safety verdict is identical,
    while counterexamples and the per-step LTLf truth (over the non-idle prefix
    only) become well-defined.

    Returns (z3 Solver with init+transitions+idle-discipline asserted, vars).
    Callers add their own goal (safety violation, or a temporal violation)."""
    import z3
    s = z3.Solver()
    IDLE = len(model.actions)
    ctrl = [z3.Int(f"ctrl_{i}") for i in range(K + 1)]
    ctx = {c: [z3.Int(f"{c}_{i}") for i in range(K + 1)] for c in model.context}
    act = [z3.Int(f"act_{i}") for i in range(K)]
    arg = [z3.Int(f"arg_{i}") for i in range(K)]

    s.add(ctrl[0] == model.idx(model.initial))
    for c, (lo, hi) in model.context.items():
        s.add(ctx[c][0] >= lo, ctx[c][0] <= hi)

    # P4a: the bounded visible stack.  Emitted ONLY for a nested (call/return)
    # protocol, so a non-nested spec declares no sp/stk vars and its SMT-LIB is
    # byte-identical to pre-P4a.  Encoding: a per-step pointer sp[i] plus D fixed
    # integer slots stk[d][i] (continuation-state indices), pushed/popped by a
    # symbolic-index case split over the D slots -- pure QF_LIA, no arrays.
    stack = model.has_stack()
    if stack:
        D = STACK_DEPTH
        sp = [z3.Int(f"sp_{i}") for i in range(K + 1)]
        stk = [[z3.Int(f"stk_{d}_{i}") for i in range(K + 1)] for d in range(D)]
        s.add(sp[0] == 0)
        for i in range(K + 1):
            s.add(sp[i] >= 0, sp[i] <= D)

    for i in range(K):
        ci = {c: ctx[c][i] for c in model.context}
        disj = []
        for aidx, a in enumerate(model.actions):
            conj = [act[i] == aidx, ctrl[i] == model.idx(a.frm)]
            if not stack:                   # static target (byte-identical path)
                conj.append(ctrl[i + 1] == model.idx(a.to))
            if a.guard is not None:
                conj.append(_pred_z3(a.guard, ci, a.arg, arg[i]))
            for c in model.context:
                if c in a.update:
                    conj.append(ctx[c][i + 1] ==
                                _expr_z3(a.update[c], ci, a.arg, arg[i]))
                else:
                    conj.append(ctx[c][i + 1] == ctx[c][i])
            if stack:                       # stack-determined target + sp/slots
                conj += _stack_step(model, a, i, ctrl, sp, stk, D)
            disj.append(z3.And(conj))
        idle = [act[i] == IDLE, ctrl[i + 1] == ctrl[i]] + \
            [ctx[c][i + 1] == ctx[c][i] for c in model.context]
        if stack:                           # idle stutters the whole stack too
            idle.append(sp[i + 1] == sp[i])
            for d in range(D):
                idle.append(stk[d][i + 1] == stk[d][i])
        disj.append(z3.And(idle))
        s.add(z3.Or(disj))
        s.add(act[i] >= 0, act[i] <= IDLE)
        if i + 1 < K:                       # idle is an ABSORBING suffix
            s.add(z3.Implies(act[i] == IDLE, act[i + 1] == IDLE))
    v = {"ctrl": ctrl, "ctx": ctx, "act": act, "arg": arg, "IDLE": IDLE}
    if stack:
        v.update(sp=sp, stk=stk, D=D)
    return s, v


def _stack_step(model, a, i, ctrl, sp, stk, D):
    """P4a per-action stack constraints for step i (nested protocols only).

      internal : ctrl' = to ; sp' = sp ; every slot unchanged.
      call     : sp < D (depth bound) ; ctrl' = to ; sp' = sp+1 ; the NEW top
                 slot (index sp) := idx(return_to) ; other slots unchanged --
                 a symbolic-index case split over the D possible values of sp.
      return   : sp > 0 (no over-pop) ; sp' = sp-1 ; ctrl' = stk[sp-1] (the
                 popped continuation, again a case split) ; slots unchanged.
    """
    import z3
    out = []
    if a.kind == "call":
        out.append(sp[i] < D)
        out.append(ctrl[i + 1] == model.idx(a.to))
        out.append(sp[i + 1] == sp[i] + 1)
        rt = model.idx(a.return_to)
        for d0 in range(D):
            out.append(z3.Implies(sp[i] == d0, stk[d0][i + 1] == rt))
            for d in range(D):
                if d != d0:
                    out.append(z3.Implies(sp[i] == d0,
                                          stk[d][i + 1] == stk[d][i]))
    elif a.kind == "return":
        out.append(sp[i] > 0)
        out.append(sp[i + 1] == sp[i] - 1)
        for d1 in range(D):
            out.append(z3.Implies(sp[i] == d1 + 1,
                                  ctrl[i + 1] == stk[d1][i]))
        for d in range(D):
            out.append(stk[d][i + 1] == stk[d][i])
    else:                                   # internal
        out.append(ctrl[i + 1] == model.idx(a.to))
        out.append(sp[i + 1] == sp[i])
        for d in range(D):
            out.append(stk[d][i + 1] == stk[d][i])
    return out


def build_bmc(model: ProtocolModel, K: int):
    """Returns (z3 Solver asserting: init AND legal-transitions AND a safety
    violation is reachable within K steps, vars)."""
    import z3
    s, v = _unrolled(model, K)
    ctrl, ctx = v["ctrl"], v["ctx"]
    glob = model.safety["when"] == "*"   # G(inv): every reachable state
    when = None if glob else model.idx(model.safety["when"])
    inv = model.safety["invariant"]
    viol = []
    for i in range(K + 1):
        ci = {c: ctx[c][i] for c in model.context}
        bad = z3.Not(_pred_z3(inv, ci, None, None))
        viol.append(bad if glob else z3.And(ctrl[i] == when, bad))
    s.add(z3.Or(viol))
    return s, v


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
    return _extract_trace(model, m, v, K)


def _extract_trace(model, m, v, K):
    """Read a concrete trace out of a sat model, stopping at the first IDLE.

    With the P1.3 idle discipline IDLE is an absorbing suffix, so the first idle
    index is exactly the real trace length: everything before it is the
    contiguous prefix of real actions and everything after is idle padding.  (The
    old code broke at the first act>=len(actions) too, but WITHOUT the discipline
    an interior idle could truncate a real suffix -- now that cannot happen.)"""
    init = {c: m[v["ctx"][c][0]].as_long() for c in model.context}
    steps = []
    for i in range(K):
        a = m[v["act"][i]]
        a = a.as_long() if a is not None else v["IDLE"]
        if a >= len(model.actions):        # first IDLE == end of the real trace
            break
        act = model.actions[a]
        av = m[v["arg"][i]]
        steps.append([act.name, (av.as_long() if av is not None else 0)
                      if act.arg else None])
    return {"init": init, "trace": steps}


def temporal_bound(model: ProtocolModel, base_K: int) -> int:
    """K for the temporal obligations = max(structural safety bound, max within-n
    deadline) (hazard 7).  For an acyclic control graph the structural bound is
    already the longest path; `within n` needs K >= n to witness a missed
    deadline."""
    within = [int(o.get("steps", 0)) for o in model.obligations
              if o.get("kind") == "within"]
    return max([base_K] + within)


def temporal_counterexample(model: ProtocolModel, obligation: dict, K: int):
    """The SHORTEST stranded trace for a temporal `obligation` (a complete legal
    session that violates the LTLf demand), or None if it holds within K.

    z3 does not minimise, so we search increasing length bounds L=1..K and return
    the first sat model's trace -- the shortest stranding witness (the B1 tooth's
    'shortest stranded trace')."""
    import z3
    from generators import ltlf_smt
    for L in range(1, K + 1):
        s, v = ltlf_smt.protocol_temporal_solver(model, obligation, L)
        if s.check() == z3.sat:
            return _extract_trace(model, s.model(), v, L)
    return None


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
    if model.has_stack():
        return _emit_validator_stack(model)
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


def _emit_validator_stack(model: ProtocolModel) -> dict:
    """P4a session validator over a visible call/return stack.  A call pushes its
    continuation (refusing at depth D), a return pops (refusing an over-pop of the
    empty stack), and every other reader of `to` is bypassed for returns (the
    target is the popped continuation)."""
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
        "    stack = []",
        f"    D = {STACK_DEPTH}",
        "    for step in trace:",
        "        if not (isinstance(step, list) and len(step) == 2):",
        "            return False",
        "        name, arg = step",
    ]
    first = True
    for a in model.actions:
        kw = "if" if first else "elif"
        first = False
        lines.append(f"        {kw} state == {a.frm!r} and name == {a.name!r}:")
        if a.arg:
            lines.append("            if type(arg) is not int:")
            lines.append("                return False")
        else:
            lines.append("            if arg is not None:")
            lines.append("                return False")
        if a.guard is not None:
            lines.append(f"            if not {_pred_py(a.guard, a.arg)}:")
            lines.append("                return False")
        if a.kind == "call":
            lines.append("            if len(stack) >= D:")
            lines.append("                return False")
            lines.append(f"            stack.append({a.return_to!r})")
        elif a.kind == "return":
            lines.append("            if not stack:")
            lines.append("                return False")
        for c, e in a.update.items():
            lines.append(f"            ctx[{c!r}] = {_expr_py(e, a.arg)}")
        if a.kind == "return":
            lines.append("            state = stack.pop()")
        else:
            lines.append(f"            state = {a.to!r}")
    lines += [
        "        else:",
        "            return False",
        "    return True",
    ]
    return {"validator.py": ("\n".join(lines) + "\n").encode()}


# ------------------------------------------ conformance: traces + reference
def _table(model: ProtocolModel) -> dict:
    acts = []
    for a in model.actions:
        d = {"name": a.name, "from": a.frm, "to": a.to, "arg": a.arg,
             "guard": a.guard, "update": a.update}
        if model.has_stack():             # P4a keys only when nested (byte-id)
            d["kind"] = a.kind
            d["return_to"] = a.return_to
        acts.append(d)
    return {
        "initial": model.initial,
        "context": {c: list(v) for c, v in model.context.items()},
        "actions": acts,
    }


def _solve_trace(model, path, negate_last):
    """Solve (Z3) for init+args making `path` legal (guards satisfied); with
    negate_last, the LAST action's guard is instead FALSIFIED (an illegal trace
    that a guard-dropping validator would wrongly accept).  Returns {init, trace}
    or None (UNSAT)."""
    import z3
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

    def val(v):                             # unconstrained args model-complete
        return m.eval(v, model_completion=True).as_long()
    return {"init": {c: val(ctx[c]) for c in model.context},
            "trace": [[a.name,
                       (val(args[j]) if args[j] is not None else 0)
                       if a.arg else None] for j, a in enumerate(path)]}


def conformance_traces(model: ProtocolModel, K: int) -> list:
    """Legal traces (control paths with solver-satisfied guards) plus illegal
    ones (wrong-state action; guard-violating argument).  For a nested protocol
    the walk is over (state, stack) CONFIGURATIONS and adds unmatched-return and
    over-pop-after-legal-prefix cases."""
    if model.has_stack():
        return _conformance_traces_stack(model, K)
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
    for path in paths[:24]:
        legal = _solve_trace(model, path, negate_last=False)
        if legal is not None:
            cases.append(legal)
        # a trace that violates exactly the last action's guard (illegal) --
        # this is what catches a validator that drops a guard check
        if path and path[-1].guard is not None:
            bad = _solve_trace(model, path, negate_last=True)
            if bad is not None:
                cases.append(bad)
    # illegal: an action from the wrong state (not enabled initially)
    for a in model.actions:
        if a.frm != model.initial:
            cases.append({"init": lo0,
                          "trace": [[a.name, 0 if a.arg else None]]})
            break
    return cases


def _conformance_traces_stack(model: ProtocolModel, K: int) -> list:
    """P4a conformance cases: a BFS over (state, stack) CONFIGURATIONS, capped so
    it PRIORITIZES configuration-diverse paths (the first path reaching each
    distinct config), then explicit stack-integrity negatives -- an
    over-pop-after-legal-prefix (a return once the stack is empty) and a
    depth-overflow (D+1 self-recursive calls).  Every case must be judged
    identically by the emitted validator and the reference (both track the same
    stack), so a validator that drops the depth bound or the over-pop check is
    caught by the differential."""
    from collections import deque
    D = STACK_DEPTH
    cases = []
    lo0 = {c: v[0] for c, v in model.context.items()}
    cases.append({"init": lo0, "trace": []})
    # config-diverse BFS: keep the first (shortest) path reaching each new
    # (state, stack-tuple) config.
    start = (model.initial, ())
    dq = deque([(start, [])])
    seen = {start}
    diverse = []
    while dq and len(diverse) < 24:
        (st, stk), path = dq.popleft()
        if len(path) >= K:
            continue
        for a in model.actions:
            if a.frm != st:
                continue
            if a.kind == "call":
                if len(stk) >= D:
                    continue
                ncfg = (a.to, stk + (a.return_to,))
            elif a.kind == "return":
                if not stk:
                    continue
                ncfg = (stk[-1], stk[:-1])
            else:
                ncfg = (a.to, stk)
            npath = path + [a]
            if ncfg not in seen:
                seen.add(ncfg)
                diverse.append(npath)
                dq.append((ncfg, npath))
    for path in diverse:
        legal = _solve_trace(model, path, negate_last=False)
        if legal is not None:
            cases.append(legal)
        if path and path[-1].guard is not None:
            bad = _solve_trace(model, path, negate_last=True)
            if bad is not None:
                cases.append(bad)
    # wrong-state negative (an action not enabled initially)
    for a in model.actions:
        if a.frm != model.initial:
            cases.append({"init": lo0,
                          "trace": [[a.name, 0 if a.arg else None]]})
            break
    # over-pop after a legal prefix: reach a return's from-state at empty stack
    # via internal moves, then invoke the return (both impls reject -- over-pop).
    op = _overpop_case(model, lo0)
    if op is not None:
        cases.append(op)
    # depth-overflow: a self-recursive call from the initial state, D+1 times
    for c in model.actions:
        if c.kind == "call" and c.frm == c.to and c.frm == model.initial:
            cases.append({"init": lo0,
                          "trace": [[c.name, None if not c.arg else 0]
                                    for _ in range(D + 1)]})
            break
    return cases


def _overpop_case(model, lo0):
    """A legal internal prefix reaching some return action's from-state at empty
    stack, followed by that return (which over-pops).  Solved for concrete args
    so the prefix is genuinely accepted; None if unreachable / UNSAT."""
    from collections import deque
    R = next((a for a in model.actions if a.kind == "return"), None)
    if R is None:
        return None
    dq = deque([(model.initial, [])])
    seen = {model.initial}
    prefix = None
    while dq:
        st, path = dq.popleft()
        if st == R.frm:
            prefix = path
            break
        for a in model.actions:
            if a.frm == st and a.kind == "internal" and a.to not in seen:
                seen.add(a.to)
                dq.append((a.to, path + [a]))
    if prefix is None:
        return None
    solved = _solve_trace(model, prefix, negate_last=False)
    if solved is None:
        return None
    solved["trace"].append([R.name, 0 if R.arg else None])   # the over-pop
    return solved


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


_REF_SIM_STACK = r'''
import json
TABLE = json.loads(r"""%s""")
D = %d

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
    # INDEPENDENT reference simulator carrying a visible call/return stack; a
    # return's target is the popped continuation, NOT the static act["to"].
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
    ctx = dict(init); state = TABLE["initial"]; stack = []
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
        kind = act.get("kind", "internal")
        if kind == "call":
            if len(stack) >= D:
                return False
            stack.append(act["return_to"])
        elif kind == "return":
            if not stack:
                return False
        newctx = dict(ctx)
        for c, e in (act["update"] or {}).items():
            newctx[c] = _expr(e, ctx, act["arg"], arg)
        ctx = newctx
        state = stack.pop() if kind == "return" else act["to"]
    return True
'''


def build_conformance_harness(model: ProtocolModel, cases: list) -> dict:
    if model.has_stack():
        ref = _REF_SIM_STACK % (json.dumps(_table(model)), STACK_DEPTH)
    else:
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

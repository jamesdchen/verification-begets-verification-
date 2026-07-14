"""Compositional compilation: Reading -> service meta-spec, deterministically.

This is the Montague move mechanized for our fragment: each statement's logical
form contributes its meaning to the whole compositionally --

    quantity            -> context variable (init range)
    action + transition -> tool (one guarded transition)
    effect              -> the tool's update expression
    bound (vs const)    -> per-call constraint (cross-field layer)
    bound (vs quantity) -> guard (protocol layer)
    always              -> global safety invariant  G(pred)  (when: "*")
    order               -> a temporal obligation the CHOSEN lifecycle must
                           entail -- checked against the transition graph, so a
                           design choice can never silently override a demand
    input               -> extra (optional) schema fields

Every compiled element records PROVENANCE: the statement ids (and hence the
quoted request spans and speech-act forces) that produced it.  The certificate
chain for the finished service therefore reads:

    quoted span  ->  logical form  ->  spec element  ->  kernel proof

Also here:
  * demands_smt(reading): the satisfiability obligation for the demand set
    (dual-checked; contradictory demands are refused before any code exists);
  * entailed_scenarios(model, reading): behavioural expectations DERIVED from
    the demands by the solver -- each bound/guard/order demand generates the
    concrete trace that would violate it, with expectation "rejected".  No LLM
    guesses expectations on this path; they are entailed by the semantics.
"""
from __future__ import annotations

import json

from .reading import Reading, BadReading


class CompileError(Exception):
    """A choice contradicts a demand, or the reading is not compilable."""


# --------------------------------------------------------------- compile
def _pred_smt(pred, names) -> str:
    op = pred["op"]
    if op == "and":
        return "(and " + " ".join(_pred_smt(p, names)
                                  for p in pred["preds"]) + ")"
    if op == "implies":
        return (f"(=> {_pred_smt(pred['if'], names)} "
                f"{_pred_smt(pred['then'], names)})")
    smt = {"==": "=", "!=": "distinct"}.get(op, op)
    def side(o):
        return o if isinstance(o, str) else str(o)
    return f"({smt} {side(pred['left'])} {side(pred['right'])})"


def compile_reading(reading: Reading):
    """-> (spec_text, provenance).  Raises CompileError when the chosen
    structure fails to entail a demanded ordering."""
    prov = {}

    def add(key, sid):
        prov.setdefault(key, []).append(sid)

    quantities, actions, trans, effects = {}, {}, {}, {}
    bounds, always, orders, inputs = [], [], [], {}
    for s in reading.statements:
        lf, sid = s["lf"], s["id"]
        k = lf["kind"]
        if k == "quantity":
            quantities[lf["name"]] = (lf["min"], lf["max"])
            add(f"context.{lf['name']}", sid)
        elif k == "action":
            actions[lf["name"]] = lf.get("arg")
            add(f"tool.{lf['name']}", sid)
        elif k == "transition":
            trans[lf["action"]] = lf
            add(f"tool.{lf['action']}.transition", sid)
        elif k == "effect":
            effects.setdefault(lf["action"], []).append(lf)
            add(f"tool.{lf['action']}.update.{lf['quantity']}", sid)
        elif k == "bound":
            bounds.append((s, lf))
        elif k == "always":
            always.append((s, lf))
            add("safety", sid)
        elif k == "order":
            orders.append((s, lf))
        elif k == "lifecycle":
            lifecycle = lf
            add("lifecycle", sid)
        elif k == "input":
            inputs.setdefault(lf["action"], {}).update(lf["fields"])
            add(f"tool.{lf['action']}.input", sid)

    # a demanded ordering must be ENTAILED by the chosen transition graph:
    # with all `first`-edges removed, no reachable state may enable `then`.
    edges = [(t["from"], t["to"], a) for a, t in trans.items()]
    initial = lifecycle["initial"]
    for s, lf in orders:
        first, then = lf["first"], lf["then"]
        add(f"order.{first}->{then}", s["id"])
        reach, frontier = {initial}, [initial]
        while frontier:
            u = frontier.pop()
            for frm, to, a in edges:
                if frm == u and a != first and to not in reach:
                    reach.add(to)
                    frontier.append(to)
        offenders = [a for frm, to, a in edges if frm in reach and a == then]
        if offenders:
            raise CompileError(
                f"the chosen lifecycle contradicts demanded order "
                f"{s['id']} ({first!r} before {then!r}): {then!r} is "
                f"reachable from {initial!r} without ever performing "
                f"{first!r} (via states {sorted(reach)})")

    tools = []
    for name, arg in actions.items():
        t = trans[name]
        props, required = {}, []
        if arg:
            props[arg] = {"type": "integer"}
            required.append(arg)
        for fn, ft in inputs.get(name, {}).items():
            props[fn] = {"type": ft}
        tool = {"name": name, "from": t["from"], "to": t["to"],
                "input_schema": {"title": name, "type": "object",
                                 "properties": props, "required": required,
                                 "additionalProperties": False}}
        if arg:
            tool["arg"] = arg
        guards, cons = [], []
        for s, lf in bounds:
            if lf["action"] != name:
                continue
            pred = {"op": lf["cmp"], "left": lf["left"], "right": lf["right"]}
            if isinstance(lf["right"], int):
                cons.append(pred)
                add(f"tool.{name}.constraints", s["id"])
            else:
                guards.append(pred)
                add(f"tool.{name}.guard", s["id"])
        if guards:
            tool["guard"] = guards[0] if len(guards) == 1 else \
                {"op": "and", "preds": guards}
        if cons:
            tool["constraints"] = {
                "name": f"{name}_c",
                "fields": {arg: {"type": "integer"}},
                "constraints": cons, "invariant": cons[0]}
        update = {}
        for lf in effects.get(name, []):
            amt = lf["amount"]
            operand = amt["arg"] if "arg" in amt else {"const": amt["const"]}
            q = lf["quantity"]
            if lf["op"] == "set":
                update[q] = operand
            else:
                op = "-" if lf["op"] == "dec" else "+"
                update[q] = {"op": op, "left": {"var": q},
                             "right": ({"var": operand} if isinstance(operand, str)
                                       else operand)}
        if update:
            tool["update"] = update
        tools.append(tool)

    inv_preds = [lf["pred"] for _, lf in always]
    safety = {"when": "*",
              "invariant": inv_preds[0] if len(inv_preds) == 1 else
              {"op": "and", "preds": inv_preds}}
    spec = {"name": reading.service,
            "context": {q: {"type": "integer", "init_min": lo, "init_max": hi}
                        for q, (lo, hi) in quantities.items()},
            "states": lifecycle["states"], "initial": initial,
            "tools": tools, "safety": safety}
    return json.dumps(spec), prov


# ------------------------------------------------- demand-set consistency
def demands_smt(reading: Reading) -> str:
    """Satisfiability of the demand set: quantities within their declared
    ranges, action arguments free, all demanded always-preds and const-bounds
    asserted.  Expected verdict: sat (a world satisfying every demand exists).
    unsat = the request's demands contradict each other -- refuse before any
    code exists."""
    lines = ["(set-logic QF_LIA)"]
    qs = {lf["name"]: (lf["min"], lf["max"])
          for s in reading.statements
          if (lf := s["lf"])["kind"] == "quantity"}
    args = {lf["name"]: lf.get("arg")
            for s in reading.statements
            if (lf := s["lf"])["kind"] == "action"}
    for q, (lo, hi) in qs.items():
        lines.append(f"(declare-const {q} Int)")
        lines.append(f"(assert (and (>= {q} {lo}) (<= {q} {hi})))")
    declared = set(qs)
    for s in reading.demands():
        lf = s["lf"]
        if lf["kind"] == "always":
            lines.append(f"(assert {_pred_smt(lf['pred'], declared)})")
        elif lf["kind"] == "bound":
            arg = args.get(lf["action"])
            if arg and arg not in declared:
                lines.append(f"(declare-const {arg} Int)")
                declared.add(arg)
            pred = {"op": lf["cmp"], "left": lf["left"], "right": lf["right"]}
            lines.append(f"(assert {_pred_smt(pred, declared)})")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------ entailed scenarios
def entailed_scenarios(model, reading: Reading) -> list:
    """Behavioural expectations DERIVED from the demands, not guessed.

      * one full legal run (solver-constructed)          -> all accepted;
      * per demanded const-bound:  the solver picks an argument violating
        exactly that bound at its step of the legal run  -> rejected there;
      * per demanded guard-bound:  the solver picks an argument satisfying
        every constraint yet falsifying the guard        -> rejected there;
      * per demanded order:        attempt `then` before any `first`
        (the compiler proved the graph forbids it)       -> rejected.

    Each scenario names the demand statement(s) that entail it."""
    import z3
    import common
    from generators import service_gen as sg
    run = sg._legal_golden_run(model)
    if run is None:
        return []
    init, golden, prefix_ctx = run
    path = sg._golden_path(model)
    idx_of = {t.name: i for i, t in enumerate(path)}
    scenarios = [{"name": "entailed_legal_run", "init": init,
                  "seq": [list(x) for x in golden],
                  "expect": [True] * len(golden),
                  "why": "a full legal run must be admitted (non-vacuity)"}]

    tools = {t.name: t for t in model.tools}
    for s in reading.demands():
        lf = s["lf"]
        if lf["kind"] == "bound" and isinstance(lf["right"], int):
            name = lf["action"]
            if name not in idx_of:
                continue
            i, t = idx_of[name], tools[name]
            others = [c for c in (t.constraints["constraints"]
                                  if t.constraints else [])
                      if c != {"op": lf["cmp"], "left": lf["left"],
                               "right": lf["right"]}]
            with common.SMT_LOCK:
                v = z3.Int(lf["left"])
                sol = z3.Solver()
                sol.add(z3.Not(sg._z3_pred(
                    {"op": lf["cmp"], "left": lf["left"],
                     "right": lf["right"]}, {lf["left"]: v})))
                for c in others:
                    sol.add(sg._z3_pred(c, {lf["left"]: v}))
                if sol.check() != z3.sat:
                    continue
                bad = sol.model().eval(v, model_completion=True).as_long()
            args = dict(golden[i][1]); args[lf["left"]] = bad
            seq = [list(x) for x in golden][:i + 1]
            seq[i] = [name, args]
            scenarios.append({
                "name": f"entailed_violates_{s['id']}", "init": init,
                "seq": seq, "expect": [True] * i + [False],
                "why": f"entailed by {s['id']}: {s['quote']!r}"})
        elif lf["kind"] == "bound":     # vs quantity -> guard
            name = lf["action"]
            if name not in idx_of:
                continue
            i, t = idx_of[name], tools[name]
            sol = sg._solver_guard_input(t, prefix_ctx[i])
            if sol is None:
                continue
            args = dict(golden[i][1]); args.update(sol)
            seq = [list(x) for x in golden][:i + 1]
            seq[i] = [name, args]
            scenarios.append({
                "name": f"entailed_violates_{s['id']}", "init": init,
                "seq": seq, "expect": [True] * i + [False],
                "why": f"entailed by {s['id']}: {s['quote']!r}"})
        elif lf["kind"] == "order":
            then = lf["then"]
            t = tools[then]
            if t.frm == model.initial:
                continue        # compiler would have refused already
            args = sg._required_defaults(t)
            if t.arg:
                args.setdefault(t.arg, 1)
            scenarios.append({
                "name": f"entailed_violates_{s['id']}", "init": init,
                "seq": [[then, args]], "expect": [False],
                "why": f"entailed by {s['id']}: {s['quote']!r} "
                       f"({then!r} before {lf['first']!r})"})
    return scenarios

"""Emit, from a cross-field constraint spec:

  * a Python validator (structure + predicate evaluation), executed sandboxed;
  * an SMT-LIB proof obligation for  constraints => invariant  (fed to BOTH
    Z3 and CVC5 -- the dual-checker on a load-bearing theorem);
  * solver-generated boundary inputs: Z3 produces a satisfying model (a valid
    record) and, per constraint, a model that violates exactly that constraint
    (the tightest counterexample).  These drive the emitted validator so that
    "code matches spec" is checked at the exact constraint edges the solver
    finds -- far stronger than blind fuzzing, which almost never lands on
    boundaries like start == end or (priority == high AND attendees == 1).

The SMT proof is the trusted verdict (dual-checked); Z3-as-input-generator is
just a trusted tool producing test cases the untrusted validator runs on.
"""
from __future__ import annotations

from .constraint_model import ConstraintModel, Field, parse_constraint_spec


# ----------------------------------------------------------------- SMT-LIB
def _enum_idx(fld: Field, val: str) -> int:
    return fld.values.index(val)


def _smt_operand(operand, model: ConstraintModel) -> str:
    if isinstance(operand, str) and operand in model.fields:
        return operand
    return str(operand)


def _smt_pred(pred, model: ConstraintModel) -> str:
    op = pred["op"]
    if op == "implies":
        return f"(=> {_smt_pred(pred['if'], model)} {_smt_pred(pred['then'], model)})"
    left = pred["left"]
    lf = model.fields[left]
    if lf.kind == "enum":
        idx = _enum_idx(lf, pred["right"])
        return ("(= " if op == "==" else "(distinct ") + f"{left} {idx})"
    smt_op = {"==": "=", "!=": "distinct"}.get(op, op)
    return f"({smt_op} {left} {_smt_operand(pred['right'], model)})"


def smt_decls(model: ConstraintModel) -> str:
    lines = ["(set-logic QF_LIA)"]
    for f in model.fields.values():
        lines.append(f"(declare-const {f.name} Int)")
        if f.kind == "enum":
            lines.append(f"(assert (and (>= {f.name} 0) "
                         f"(< {f.name} {len(f.values)})))")
    return "\n".join(lines)


def obligation_smt(model: ConstraintModel) -> str:
    """constraints => invariant  is valid  iff  constraints AND (not invariant)
    is UNSAT.  Both solvers must return unsat."""
    if model.invariant is None:
        raise ValueError("no invariant to prove")
    parts = [smt_decls(model)]
    for c in model.constraints:
        parts.append(f"(assert {_smt_pred(c, model)})")
    parts.append(f"(assert (not {_smt_pred(model.invariant, model)}))")
    parts.append("(check-sat)")
    return "\n".join(parts) + "\n"


def nonvacuity_smt(model: ConstraintModel) -> str:
    """constraints is SAT (a valid input exists -- the contract is not
    vacuously unsatisfiable)."""
    parts = [smt_decls(model)]
    for c in model.constraints:
        parts.append(f"(assert {_smt_pred(c, model)})")
    parts.append("(check-sat)")
    return "\n".join(parts) + "\n"


# ------------------------------------------------------------- Python emit
def _py_operand(operand, model: ConstraintModel) -> str:
    if isinstance(operand, str) and operand in model.fields:
        return f"data[{operand!r}]"
    return repr(operand)


def _py_pred(pred, model: ConstraintModel) -> str:
    op = pred["op"]
    if op == "implies":
        return (f"((not ({_py_pred(pred['if'], model)})) or "
                f"({_py_pred(pred['then'], model)}))")
    left = pred["left"]
    lf = model.fields[left]
    if lf.kind == "enum":
        pyop = "==" if op == "==" else "!="
        return f"(data[{left!r}] {pyop} {pred['right']!r})"
    return f"(data[{left!r}] {op} {_py_operand(pred['right'], model)})"


def emit_validator(model: ConstraintModel) -> dict:
    ints = [f.name for f in model.fields.values() if f.kind == "integer"]
    enums = {f.name: f.values for f in model.fields.values() if f.kind == "enum"}
    names = list(model.fields)
    lines = [
        "def accepts(data):",
        "    if not isinstance(data, dict):",
        "        return False",
        f"    if set(data.keys()) != {set(names)!r}:",
        "        return False",
    ]
    for n in ints:
        lines.append(f"    if type(data[{n!r}]) is not int:")
        lines.append("        return False")
    for n, vals in enums.items():
        lines.append(f"    if data[{n!r}] not in {vals!r}:")
        lines.append("        return False")
    for c in model.constraints:
        lines.append(f"    if not ({_py_pred(c, model)}):")
        lines.append("        return False")
    lines.append("    return True")
    return {"validator.py": ("\n".join(lines) + "\n").encode()}


# ----------------------------------------- solver-generated boundary inputs
def _z3_operand(operand, zvars):
    if isinstance(operand, str) and operand in zvars:
        return zvars[operand]
    return operand


def _z3_pred(pred, model, zvars):
    import z3
    op = pred["op"]
    if op == "implies":
        return z3.Implies(_z3_pred(pred["if"], model, zvars),
                          _z3_pred(pred["then"], model, zvars))
    left = pred["left"]
    lf = model.fields[left]
    v = zvars[left]
    if lf.kind == "enum":
        idx = _enum_idx(lf, pred["right"])
        return v == idx if op == "==" else v != idx
    r = _z3_operand(pred["right"], zvars)
    return {"<": v < r, "<=": v <= r, ">": v > r, ">=": v >= r,
            "==": v == r, "!=": v != r}[op]


def _model_to_record(m, model, zvars):
    rec = {}
    for name, f in model.fields.items():
        val = m.eval(zvars[name], model_completion=True)
        iv = val.as_long()
        rec[name] = f.values[iv] if f.kind == "enum" else iv
    return rec


def boundary_inputs(model: ConstraintModel) -> list:
    """Returns [(record, expected_accept), ...] with solver-chosen inputs:
    one satisfying model (accept), and per constraint a model violating exactly
    that constraint while satisfying the rest (reject at the tightest edge)."""
    import z3
    import common
    with common.SMT_LOCK:                 # z3 default context is not thread-safe
        zvars = {}
        base = []
        for name, f in model.fields.items():
            zvars[name] = z3.Int(name)
            if f.kind == "enum":
                base.append(z3.And(zvars[name] >= 0, zvars[name] < len(f.values)))
        cons = [_z3_pred(c, model, zvars) for c in model.constraints]
        out = []
        # a valid record
        s = z3.Solver(); s.add(base + cons)
        if s.check() == z3.sat:
            out.append((_model_to_record(s.model(), model, zvars), True))
        # per-constraint tightest violation
        for i, c in enumerate(cons):
            s = z3.Solver()
            s.add(base + [cj for j, cj in enumerate(cons) if j != i])
            s.add(z3.Not(c))
            if s.check() == z3.sat:
                out.append((_model_to_record(s.model(), model, zvars), False))
        return out


def build_boundary_harness(inputs: list) -> str:
    return f'''
import json, sys, traceback
from validator import accepts
CASES = {inputs!r}
def main():
    try:
        for rec, expected in CASES:
            got = bool(accepts(rec))
            assert got == expected, ("validator disagrees with solver model",
                                     rec, "expected", expected, "got", got)
        print(json.dumps({{"status": "pass", "examples": len(CASES)}}))
    except BaseException as e:
        print(json.dumps({{"status": "fail", "error": repr(e)[:2000],
                          "traceback": traceback.format_exc()[-2000:]}}))
        sys.exit(1)
main()
'''

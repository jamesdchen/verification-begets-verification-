"""The seven certified compiler passes of the service pipeline (W6.2).

`generators/service_gen.py` historically emitted a service dispatcher from a
single monolithic function.  This module decomposes that emission into seven
PURE passes over a canonical-JSON **bundle** dict (W6.1).  Each pass takes the
bundle, produces one or more bundle keys, and returns the bundle; their
COMPOSITION reproduces exactly what `service_gen.emit_service(model)` produced
before the decomposition -- this is the BYTE-PRESERVING core of W6.  The
byte-CHANGING parts (golden regeneration, per-pass translation-certs, the
`_EVAL` interpreter split, kernel/backends repointing) are deferred to a later
serialized window and are NOT done here.

Bundle keys (W6.1):
    spec_text, model, files, validators, constraints_table, transitions,
    initial, init_ctx, stack, monitor, golden_run, cases, order_contract
plus internal carriers `imports` (the emitted `import tool_*` lines).

The seven passes:
    1. parse_normalize   -> initial, init_ctx, order_contract
    2. tool_schema       -> files (tool_*.py), validators, imports
    3. constraint        -> constraints_table
    4. protocol_stack    -> transitions, stack  (empty stack frags when flat)
    5. obligation_monitor-> monitor            (empty + NO flloat import when
                                                obligations == [])
    6. adversary_golden  -> golden_run, cases
    7. assemble          -> files["service.py"]

Passes 4/5 emit EMPTY fragments (byte-parity with the pre-decomposition
conditional-emission discipline) when the service has no stack / no
obligations; pass 5 never imports flloat in that case (the lazy import lives
behind `_monitor_data`, only reached for a service that declares obligations).

The order_contract produced by pass 1 is, for THIS byte-preserving window, a
plain DATA record (the frozen runtime enforcement order).  Its certificate
obligation (consumed by pass 7) is deferred; no cert is added here.
"""
from __future__ import annotations

from . import toolgen
from . import service_gen

# The frozen runtime layer-ordering semantics that the emitted `call()` enacts
# by interpolation position (service_gen template lines 177-199).  Produced by
# pass 1, consumed (as a data record only, for now) by pass 7.  See W6.2 pass 7.
ORDER_CONTRACT = [
    "sequencing",
    "stack-pre",
    "schema",
    "constraint",
    "guard",
    "obligation",
    "update",
    "state-advance",
    "monitor-advance",
]


# --- Pass 1 -----------------------------------------------------------------
def parse_normalize(bundle: dict) -> dict:
    """Spec well-formedness + the normalized scalars every later pass reads.

    The model is already parsed (`service_model.parse_service_spec`); this pass
    records the initial state, the low-end initial context, and the frozen
    order contract.  Byte-affecting outputs: `initial`, `init_ctx`."""
    model = bundle["model"]
    bundle["initial"] = model.initial
    bundle["init_ctx"] = {c: lo for c, (lo, hi) in model.context.items()}
    bundle["order_contract"] = list(ORDER_CONTRACT)
    return bundle


# --- Pass 2 -----------------------------------------------------------------
def tool_schema(bundle: dict) -> dict:
    """Per-tool schema modules (delegated to `toolgen`) and the validator map.

    Emits `tool_<name>.py` for each tool (in tool order) and records the
    `import tool_<name>` lines and the `VALIDATORS` map entries."""
    model = bundle["model"]
    files = bundle.setdefault("files", {})
    imports, vmap = [], []
    for t in model.tools:
        mod = f"tool_{t.name}"
        files[f"{mod}.py"] = toolgen.emit_pydantic_tool(t.schema_text)["tool_model.py"]
        imports.append(f"import {mod}")
        vmap.append(f"    {t.name!r}: {mod}.decode,")
    bundle["imports"] = imports
    bundle["validators"] = vmap
    return bundle


# --- Pass 3 -----------------------------------------------------------------
def constraint(bundle: dict) -> dict:
    """The per-call constraint table (delegated to the model's constraints)."""
    bundle["constraints_table"] = service_gen._constraints(bundle["model"])
    return bundle


# --- Pass 4 -----------------------------------------------------------------
def protocol_stack(bundle: dict) -> dict:
    """The `TRANSITIONS` table plus the P4a stack fragments.

    The stack fragments are the EMPTY strings (and the plain state-advance
    line) for a non-nested service, so a flat service is byte-identical to
    pre-P4a; the call/return machinery appears only when `_has_stack`."""
    model = bundle["model"]
    bundle["transitions"] = service_gen._transitions(model)
    from .protocol_model import STACK_DEPTH
    consts = init = pre = ""
    state = '        self.state = tr["to"]'
    if service_gen._has_stack(model):
        consts = (f"\nSTACK_D = {STACK_DEPTH}\nSTACK_TERMINALS = "
                  f"{service_gen._stack_terminals(model)!r}")
        init = "\n        self.stack = []"
        pre = (
            '\n        if tr["kind"] == "call" and len(self.stack) >= STACK_D:'
            '\n            return {"ok": False, "layer": "sequencing"}'
            '\n        if tr["kind"] == "return" and not self.stack:'
            '\n            return {"ok": False, "layer": "sequencing"}'
            '\n        if tr["name"] in STACK_TERMINALS and self.stack:'
            '\n            return {"ok": False, "layer": "sequencing"}')
        state = (
            '        if tr["kind"] == "return":\n'
            '            self.state = self.stack.pop()\n'
            '        elif tr["kind"] == "call":\n'
            '            self.stack.append(tr["return_to"])\n'
            '            self.state = tr["to"]\n'
            '        else:\n'
            '            self.state = tr["to"]')
    bundle["stack"] = {"consts": consts, "init": init, "pre": pre, "state": state}
    return bundle


# --- Pass 5 -----------------------------------------------------------------
def obligation_monitor(bundle: dict) -> dict:
    """The temporal-obligation monitor fragments.

    GENUINE no-op for a service with `obligations == []`: every fragment is the
    empty string and `_monitor_data` (which lazily imports monitor_gen/flloat)
    is never called -- keeping emitted bytes identical AND importing no flloat,
    exactly the pre-decomposition conditional-emission gate."""
    model = bundle["model"]
    consts = init = check = adv = ""
    if service_gen._obligations(model):
        tables, minitial, perm = service_gen._monitor_data(model)
        consts = (f"\nMON_TABLES = {tables!r}\nMON_INITIAL = {minitial!r}\n"
                  f"MON_PERM = {perm!r}\nTERMINAL_TOOLS = "
                  f"{service_gen._terminal_tools(model)!r}")
        init = "\n        self.mon = dict(MON_INITIAL)"
        check = (
            '\n        if tool in TERMINAL_TOOLS and any('
            '\n                self.mon[o] not in MON_PERM[o] for o in MON_INITIAL):'
            '\n            return {"ok": False, "layer": "obligation"}')
        adv = ("\n        for o in MON_INITIAL:"
               "\n            self.mon[o] = MON_TABLES[o][self.mon[o]][tool]")
    bundle["monitor"] = {"consts": consts, "init": init, "check": check, "adv": adv}
    return bundle


# --- Pass 6 -----------------------------------------------------------------
def adversary_golden(bundle: dict) -> dict:
    """The solver-witnessed golden run and the conformance case set.

    These bundle keys feed the conformance/liveness/scenario builders; they do
    NOT affect the emitted `service.py` bytes, so a pipeline that includes this
    pass produces the same `files` as one that stops at assemble."""
    model = bundle["model"]
    bundle["golden_run"] = service_gen._legal_golden_run(model)
    bundle["cases"] = service_gen.conformance_cases(model)
    return bundle


# --- Pass 7 -----------------------------------------------------------------
def assemble(bundle: dict) -> dict:
    """Interpolate the dispatcher template from the accumulated bundle.

    Reproduces the exact f-string of the pre-decomposition `emit_service`
    (service_gen lines 160-200); the interpolation ORDER is the frozen runtime
    enforcement order recorded in `order_contract`."""
    files = bundle.setdefault("files", {})
    imports = bundle["imports"]
    vmap = bundle["validators"]
    transitions = bundle["transitions"]
    constraints = bundle["constraints_table"]
    initial = bundle["initial"]
    init_ctx = bundle["init_ctx"]
    mon = bundle["monitor"]
    stk = bundle["stack"]
    mon_consts, mon_init, obl_check, mon_adv = (
        mon["consts"], mon["init"], mon["check"], mon["adv"])
    stk_consts, stk_init, stk_pre, stk_state = (
        stk["consts"], stk["init"], stk["pre"], stk["state"])
    _EVAL = service_gen._EVAL
    svc = f'''
import json
{chr(10).join(imports)}
TRANSITIONS = {transitions!r}
CONSTRAINTS = {constraints!r}
INITIAL = {initial!r}
INIT_CTX = {init_ctx!r}
VALIDATORS = {{
{chr(10).join(vmap)}
}}{mon_consts}{stk_consts}
{_EVAL}

class Service:
    def __init__(self, init_ctx=None):
        self.state = INITIAL
        self.ctx = dict(init_ctx if init_ctx is not None else INIT_CTX){mon_init}{stk_init}

    def call(self, tool, args):
        tr = next((t for t in TRANSITIONS
                   if t["from"] == self.state and t["name"] == tool), None)
        if tr is None:
            return {{"ok": False, "layer": "sequencing"}}{stk_pre}
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
{stk_state}{mon_adv}
        return {{"ok": True}}
'''
    files["service.py"] = svc.encode()
    return bundle


# The pipeline that produces the emitted `service.py` (used by emit_service).
EMIT_PASSES = [parse_normalize, tool_schema, constraint, protocol_stack,
               obligation_monitor, assemble]

# The full seven-pass pipeline (adds the solver-witnessed golden_run/cases).
ALL_PASSES = [parse_normalize, tool_schema, constraint, protocol_stack,
              obligation_monitor, adversary_golden, assemble]


def run_passes(model, passes=EMIT_PASSES) -> dict:
    """Run `passes` over a fresh bundle seeded with `model`; return the bundle.
    The composition reproduces `service_gen.emit_service(model)`'s files."""
    bundle = {"model": model}
    for p in passes:
        bundle = p(bundle)
    return bundle


def compose(passes):
    """Return a function model -> bundle running `passes` in order."""
    def _run(model):
        return run_passes(model, passes)
    return _run

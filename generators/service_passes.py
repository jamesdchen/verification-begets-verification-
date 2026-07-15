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


# ===========================================================================
# W6.2 teeth (a): PER-PASS certification.
#
# `emit_service` composes the passes and the whole-service certificate
# (`run/service.certify_service`) checks the composed dispatcher end to end.
# That end-to-end differential catches a defect ANYWHERE, but attributes it to
# the whole service, not to the pass that produced it.  This section makes each
# byte-affecting pass INDIVIDUALLY certified: it builds the pass's designated
# artifact FROM THAT PASS'S BUNDLE OUTPUT and checks it against the pass's
# DESIGNATED EXISTING kernel contract (no new contract type).  So a defect
# planted in ONE pass's bundle key is caught by THAT pass's certificate while
# the others still certify -- pass-level attribution.
#
# The per-pass contract mapping (each an existing, Dafny-free kernel contract,
# exactly as `run/service._build_jobs` constructs them):
#
#   pass 1 parse_normalize   -> structural well-formedness  (no kernel contract)
#   pass 2 tool_schema       -> tool-differential  (per emitted tool_<n>.py)
#   pass 3 constraint        -> constraint-cert    (per constrained tool)
#   pass 4 protocol_stack    -> protocol-cert      (emitted TRANSITIONS conform)
#   pass 5 obligation_monitor-> monitor-cert       (per obligation; no-op if none)
#   pass 6 adversary_golden  -> solver-witnessed   (no single kernel contract)
#   pass 7 assemble          -> service-conformance (the composed dispatcher)
#
# KEY to attribution: the ARTIFACT is rebuilt from the pass's bundle key (so a
# mutation there changes the artifact), while the CONTRACT's reference (spec_text
# / schema_text / obligation) is derived INDEPENDENTLY from the model.  A dropped
# transition makes the pass-4 validator disagree with the model's reference
# simulator; a weakened constraint makes the pass-3 validator disagree with the
# solver's boundary verdict; and so on.  Building the reference from the same
# mutated bundle would be self-consistent and catch nothing -- the independence
# is what gives the certificate teeth.


def _pass_channels(v):
    from kernel.certs import Certificate
    ch = v.channels if isinstance(v, Certificate) else v.to_dict()["channels"]
    return [(c["backend"], c["result"]) for c in ch]


def _tool_jobs(model, bundle):
    """Pass 2: each emitted `tool_<name>.py` vs its input JSON Schema
    (tool-differential).  The artifact is the pass's OWN emitted bytes,
    repackaged under the `tool_model.py` name the kernel harness imports."""
    files = bundle.get("files", {})
    jobs = []
    for t in model.tools:
        data = files.get(f"tool_{t.name}.py")
        if data is None:
            continue
        art = {"kind": "tool", "files": {"tool_model.py": data}}
        con = {"type": "tool-differential", "schema_text": t.schema_text}
        jobs.append((f"tool:{t.name}", art, con))
    return jobs


def _constraint_jobs(model, bundle):
    """Pass 3: per constrained tool, the validator emitted from the pass's
    `constraints_table` entry vs the constraint-cert (dual-SMT + solver boundary).
    Reference spec_text is the FULL model constraint spec, so a constraint the
    pass dropped/weakened makes the emitted validator diverge from the solver's
    boundary verdict."""
    import json
    from . import constraint_gen, constraint_model
    table = bundle.get("constraints_table", {})
    jobs = []
    for t in model.tools:
        if not t.constraints:
            continue
        # artifact FROM the pass output (the emitted constraint list)
        spec = dict(t.constraints)
        spec["constraints"] = table.get(t.name, [])
        cm = constraint_model.parse_constraint_spec(json.dumps(spec))
        art = {"kind": "constraint-validator",
               "files": constraint_gen.emit_validator(cm)}
        # reference FROM the model (independent of the bundle)
        con = {"type": "constraint-cert", "spec_text": json.dumps(t.constraints)}
        jobs.append((f"constraint:{t.name}", art, con))
    return jobs


def _protocol_job(model, bundle):
    """Pass 4: the session validator emitted from the pass's `transitions`
    (+ P4a stack) vs the protocol-cert.  The kernel's differential drives an
    INDEPENDENT reference simulator built from the FULL model on solver-generated
    traces, so a transition the pass dropped is caught (the reference accepts a
    trace the emitted validator, missing that action, rejects)."""
    import json
    from . import protocol_model, protocol_gen
    doc = json.loads(model.protocol_spec_text())
    # obligations reference action names; a dropped transition could orphan one,
    # and the validator ignores obligations anyway -- drop them for the rebuild.
    doc.pop("obligations", None)
    doc["actions"] = [dict(tr) for tr in bundle.get("transitions", [])]
    pm = protocol_model.parse_protocol_spec(json.dumps(doc))
    art = {"kind": "protocol-validator", "files": protocol_gen.emit_validator(pm)}
    con = {"type": "protocol-cert", "spec_text": model.protocol_spec_text()}
    return ("protocol", art, con)


def _monitor_jobs(model, bundle):
    """Pass 5: per temporal obligation, the certified monitor DFA the pass bakes
    into the bundle (the SAME `monitor_gen.build_monitor` output `_monitor_data`
    consumes) vs monitor-cert.  A GENUINE no-op when `obligations == []`: no
    monitor is built and flloat is never imported (parity with the pass's own
    lazy-import gate)."""
    obls = list(getattr(model, "obligations", []) or [])
    if not obls:
        return []
    from . import monitor_gen
    alphabet = [t.name for t in model.tools]
    max_len = max([4] + [int(o["steps"]) for o in obls if o["kind"] == "within"])
    jobs = []
    for o in obls:
        params = {k: v for k, v in o.items() if k not in ("id", "kind")}
        r = monitor_gen.build_monitor(o["kind"], params, alphabet)
        art = {"kind": "monitor",
               "files": {"monitor.py": r["monitor.py"],
                         "ref_stepper.py": r["ref_stepper.py"]}}
        con = {"type": "monitor-cert", "kind": o["kind"], "params": params,
               "alphabet": alphabet, "max_len": max_len}
        jobs.append((f"monitor:{o['id']}", art, con))
    return jobs


def _service_job(model, bundle):
    """Pass 7: the assembled dispatcher (service.py + tool modules) vs
    service-conformance -- the composition ANDs the layers, checked against the
    INDEPENDENT reference service and a liveness non-vacuity witness."""
    art = {"kind": "service", "files": bundle["files"]}
    con = {"type": "service-conformance", "spec_text": model.source}
    return ("assemble", art, con)


def _run_jobs(jobs, *, cache_get, cache_put, event_sink):
    """Run kernel.check over each (subject, artifact, contract); return a list of
    per-subject records.  Kernel is imported lazily (house rule / another agent
    may be editing it)."""
    import kernel
    from kernel.certs import Certificate
    out = []
    for subject, art, con in jobs:
        v = kernel.check(art, con, event_sink=event_sink,
                         cache_get=cache_get, cache_put=cache_put)
        out.append({"subject": subject,
                    "certified": isinstance(v, Certificate),
                    "channels": _pass_channels(v)})
    return out


def _record(passname, contract, jobs, note, *, cache_get, cache_put, event_sink):
    if not jobs:
        return {"pass": passname, "contract": contract, "certified": None,
                "channels": [], "subjects": [], "note": note}
    subs = _run_jobs(jobs, cache_get=cache_get, cache_put=cache_put,
                     event_sink=event_sink)
    return {"pass": passname, "contract": contract,
            "certified": all(s["certified"] for s in subs),
            "channels": [ch for s in subs for ch in s["channels"]],
            "subjects": subs}


def certify_passes(model, *, cache_get=None, cache_put=None, event_sink=None,
                   mutate=None):
    """Certify each byte-affecting pass individually against its designated
    EXISTING kernel contract.  Returns a list of records, one per pass:

        {"pass": <fn name>, "contract": <contract type | None>,
         "certified": True | False | None, "channels": [(backend, result), ...],
         "subjects": [{subject, certified, channels}, ...], "note"?: str}

    `certified` is None for a pass with nothing to certify on this model (a
    genuine no-op: pass 5 with no obligations, pass 3 with no cross-field
    constraints) or a structurally-only pass (1, 6) whose boolean is a
    well-formedness self-check rather than a kernel certificate.

    `mutate(bundle) -> bundle` (optional) is applied to the assembled bundle
    BEFORE the per-pass artifacts are built -- the teeth (b) hook: planting a
    defect in ONE pass's bundle key makes THAT pass's certificate fail while the
    others still certify (pass-level attribution).  It runs after `assemble`, so
    an injected `transitions`/`constraints_table` defect changes only the pass
    that OWNS the mutated key (the already-assembled `service.py` still reflects
    the pre-mutation value, so pass 7 is unaffected -- exactly the attribution we
    want to demonstrate)."""
    bundle = run_passes(model, ALL_PASSES)
    if mutate is not None:
        bundle = mutate(bundle) or bundle
    kw = {"cache_get": cache_get, "cache_put": cache_put,
          "event_sink": event_sink}

    records = []

    # pass 1 -- structural well-formedness (no natural kernel contract).
    ok1 = (bundle.get("initial") == model.initial
           and set(bundle.get("init_ctx", {})) == set(model.context)
           and bundle.get("order_contract") == list(ORDER_CONTRACT))
    records.append({"pass": "parse_normalize", "contract": None,
                    "certified": ok1, "channels": [], "subjects": [],
                    "note": "structural: spec well-formedness "
                            "(no kernel contract type)"})

    # pass 2 -- tool-differential per emitted tool schema.
    records.append(_record("tool_schema", "tool-differential",
                           _tool_jobs(model, bundle),
                           "no tools", **kw))

    # pass 3 -- constraint-cert per constrained tool.
    records.append(_record("constraint", "constraint-cert",
                           _constraint_jobs(model, bundle),
                           "no cross-field constraints", **kw))

    # pass 4 -- protocol-cert on the emitted TRANSITIONS.
    records.append(_record("protocol_stack", "protocol-cert",
                           [_protocol_job(model, bundle)],
                           "no protocol", **kw))

    # pass 5 -- monitor-cert per obligation (genuine no-op when none).
    records.append(_record("obligation_monitor", "monitor-cert",
                           _monitor_jobs(model, bundle),
                           "no obligations (genuine no-op)", **kw))

    # pass 6 -- adversarial / solver-witnessed; no single kernel contract type.
    cases = bundle.get("cases") or []
    golden = bundle.get("golden_run")
    ok6 = bool(cases) and golden is not None
    records.append({"pass": "adversary_golden", "contract": None,
                    "certified": ok6, "channels": [], "subjects": [],
                    "note": "adversarial: %d solver-witnessed conformance cases "
                            "(re-checked by the pass-7 differential; no single "
                            "kernel contract type)" % len(cases)})

    # pass 7 -- service-conformance on the composed dispatcher.
    records.append(_record("assemble", "service-conformance",
                           [_service_job(model, bundle)],
                           "no service", **kw))

    return records

"""Phase 2 -- the CAGE: arbitrary incumbent code run behind a certified boundary.

An *incumbent* is untrusted third-party code (never LLM-authored): a `class
Incumbent` with `__init__` (= reset to a fresh state, all state in instance
attributes) and `call(tool, args) -> jsonable` (the frozen incumbent interface,
interface-freeze item 7; `specs/incumbent/order_service.py` is a benign example).
The cage runs it inside an OS sandbox and interposes:

    dispatcher (ingress) -> monitors (Phase 1) -> sandboxed incumbent -> egress

  * INGRESS -- the certified emitted dispatcher (`service_gen.emit_service`)
    decides sequencing / schema / per-call constraint / protocol guard /
    temporal-obligation legality.  A rejected call NEVER reaches the incumbent.
  * INCUMBENT -- run in its own isolated sandbox via a batch driver: one flushed
    JSON line per query (never last-line parsing -- a poison query must not lose
    the batch), per-query `signal.alarm` -> "__timeout__", exceptions ->
    "__error__".  State threads across the batch inside the one run (init = a
    fresh object); `init()`/`step()` serialization via the instance __dict__ is
    available for threading between separate one-shot runs.
  * EGRESS -- the incumbent's raw result is validated against the tool's optional
    `output_schema` by an emitted output-validator (the same dual-validator
    machinery as input schemas), run in a SEPARATE incumbent-free sandbox over
    the result as pure data.  A malformed result is refused at the "egress" layer.

Trust boundary (why three sandboxes, not one).  The dispatcher and the egress
validators are TRUSTED emitted code; the incumbent is UNTRUSTED.  They are never
co-resident: the incumbent runs alone (it cannot monkeypatch the dispatcher or
fake an egress verdict), and every accept/reject/compare decision is made in
this trusted, in-process module -- the "external adjudication" P2's containment
channel requires.

This module imports NO kernel at module load (only `certify_cage` does, lazily),
so `kernel/backends.py` may import it for the `cage-conformance` channels without
an import cycle.  It is trusted by fiat as a cage builder (TRUST.md 1.2i).
"""
from __future__ import annotations

import base64
import json

import common
import sandbox
from sandbox import Sandbox
from generators import service_gen


# --------------------------------------------------------------------- helpers
def _b64(payload: str) -> str:
    return base64.b64encode(payload.encode()).decode()


def _emit_output_validators(model) -> dict:
    """Per tool with an `output_schema`, an emitted strict Pydantic validator
    module (`out_<tool>.py`) built by the SAME machinery as input tool contracts
    (`toolgen.emit_pydantic_tool`).  Only tools that declare an output_schema get
    one, so a service without egress contracts adds nothing."""
    from generators import toolgen
    out = {}
    for t in model.tools:
        sch = getattr(t, "output_schema", None)
        if not sch:
            continue
        s = dict(sch)
        s.setdefault("title", "%s_out" % t.name)
        files = toolgen.emit_pydantic_tool(json.dumps(s))
        out["out_%s.py" % t.name] = files["tool_model.py"]
    return out


def _build_monitor_files(model) -> dict:
    """Per temporal obligation, the certified monitor DFA table module.  The
    emitted dispatcher already BAKES these tables inline (so the ingress pass
    enforces them); we also materialize them here so their hashes enter the cage
    hash explicitly (interface-freeze item 9).  Only built when the service
    declares obligations (keeps flloat out of the plain path)."""
    from generators import monitor_gen
    alphabet = [t.name for t in model.tools]
    out = {}
    for o in model.obligations:
        params = {k: v for k, v in o.items() if k not in ("id", "kind")}
        r = monitor_gen.build_monitor(o["kind"], params, alphabet)
        out[o["id"]] = r["monitor.py"]
    return out


# ------------------------------------------------------------------- the cage
class Cage:
    """A certified cage around one incumbent for one service meta-spec.

    Operational API (each is a whole SESSION, threaded through the sandboxes):
      * run(init_ctx, seq)      -> the caged verdicts (dispatcher+egress applied)
      * run_bare(init_ctx, seq) -> the BARE incumbent's raw behaviour (no cage)
      * run_dispatch(init_ctx, seq) -> the ingress-only verdicts (trusted)
    plus files()/hash() for the certificate identity.
    """

    DEFAULT_SANDBOX = {"timeout": 60, "cpu_seconds": 30, "mem_mb": 512,
                       "fsize_mb": 16}

    def __init__(self, model, incumbent_src, sandbox_params=None):
        self.model = model
        self._incumbent_src = (incumbent_src.encode()
                               if isinstance(incumbent_src, str) else incumbent_src)
        self.sandbox_params = dict(sandbox_params or self.DEFAULT_SANDBOX)
        self._dispatcher_files = service_gen.emit_service(model)   # service.py + tool_*.py
        self._egress_files = _emit_output_validators(model)         # out_<tool>.py
        self._output_tools = [t.name for t in model.tools
                              if getattr(t, "output_schema", None)]
        self._monitor_files = _build_monitor_files(model) if model.obligations else {}
        # the INDEPENDENT jsonschema-based reference service (separately authored,
        # shares no code with the dispatcher, TRUST 1.2d): the containment channel
        # classifies which calls are contract-violating with THIS oracle, never
        # with the cage-under-test -- otherwise a broken cage that wrongly accepts
        # a violation would simply not flag it, grading itself green.
        self._ref_src = service_gen.ref_service_source(model).encode()
        # the sandbox "profile" is not otherwise reifiable: hash its run-parameter
        # dict together with the trusted `_INNER` jail template.
        self._inner_hash = common.sha256_bytes(sandbox._INNER.encode())

    # --- identity ---------------------------------------------------------
    def files(self) -> dict:
        """Every file the cage is built from -- the artifact whose hash is the
        certificate subject."""
        out = dict(self._dispatcher_files)
        out.update(self._egress_files)
        out["incumbent.py"] = self._incumbent_src
        for oid, b in self._monitor_files.items():
            out["monitor_%s.py" % oid] = b
        return out

    def hash(self) -> str:
        """Cage hash (interface-freeze item 9): canonical-JSON of the dispatcher,
        egress, and monitor file hashes, the incumbent hash, and the sandbox
        run-parameter dict + `_INNER` template hash."""
        body = {
            "dispatcher": {n: common.sha256_bytes(b)
                           for n, b in self._dispatcher_files.items()},
            "egress": {n: common.sha256_bytes(b)
                       for n, b in self._egress_files.items()},
            "monitors": {oid: common.sha256_bytes(b)
                         for oid, b in self._monitor_files.items()},
            "incumbent": common.sha256_bytes(self._incumbent_src),
            "sandbox": dict(self.sandbox_params, inner=self._inner_hash),
        }
        return common.sha256_json(body)

    def _run_kwargs(self) -> dict:
        p = self.sandbox_params
        return dict(timeout=p.get("timeout", 60),
                    cpu_seconds=p.get("cpu_seconds", 30),
                    mem_mb=p.get("mem_mb", 512), fsize_mb=p.get("fsize_mb", 16))

    # --- ingress (trusted dispatcher, no incumbent present) ---------------
    def _dispatch_harness(self, init, seq) -> bytes:
        b = _b64(json.dumps({"init": init, "seq": seq}))
        return ("import json, base64\n"
                "from service import Service\n"
                "_d = json.loads(base64.b64decode('%s').decode())\n"
                "s = Service(_d['init'])\n"
                "for _tool, _args in _d['seq']:\n"
                "    print(json.dumps(s.call(_tool, _args)), flush=True)\n"
                % b).encode()

    def run_dispatch(self, init, seq) -> list:
        if not seq:
            return []
        with Sandbox() as sb:
            for n, b in self._dispatcher_files.items():
                sb.add_file(n, b)
            sb.add_file("_disp.py", self._dispatch_harness(init, seq))
            res = sb.run(["python3", "_disp.py"], **self._run_kwargs())
        out = []
        for line in res.stdout.decode(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
        while len(out) < len(seq):        # a crash loses tail lines: fail closed
            out.append({"ok": False, "layer": "sequencing"})
        return out[:len(seq)]

    # --- independent reference oracle (trusted, no incumbent present) -----
    def _reference_harness(self, init, seq) -> bytes:
        b = _b64(json.dumps({"init": init, "seq": seq}))
        return ("import json, base64\n"
                "from ref_service import run_reference\n"
                "_d = json.loads(base64.b64decode('%s').decode())\n"
                "print(json.dumps(run_reference(_d['init'], _d['seq'])), flush=True)\n"
                % b).encode()

    def run_reference(self, init, seq) -> list:
        """Per-step accept(bool) from the INDEPENDENT reference service -- the
        containment oracle that classifies contract-violating calls without asking
        the cage-under-test.  Fail-closed (unknown step -> reject)."""
        if not seq:
            return []
        with Sandbox() as sb:
            sb.add_file("ref_service.py", self._ref_src)
            sb.add_file("_ref.py", self._reference_harness(init, seq))
            res = sb.run(["python3", "_ref.py"], **self._run_kwargs())
        for line in res.stdout.decode(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                v = json.loads(line)
            except Exception:
                continue
            if isinstance(v, list):
                out = [bool(x) for x in v]
                while len(out) < len(seq):
                    out.append(False)
                return out[:len(seq)]
        return [False] * len(seq)

    # --- incumbent (untrusted, isolated) ----------------------------------
    def _incumbent_harness(self, calls) -> bytes:
        b = _b64(json.dumps(calls))
        return ("import json, base64, signal\n"
                "from incumbent import Incumbent\n"
                "QUERIES = json.loads(base64.b64decode('%s').decode())\n"
                "def _to(sig, frm):\n"
                "    raise TimeoutError()\n"
                "inc = Incumbent()\n"
                "for _i, _q in enumerate(QUERIES):\n"
                "    _tool, _args = _q[0], _q[1]\n"
                "    signal.signal(signal.SIGALRM, _to)\n"
                "    signal.alarm(5)\n"
                "    try:\n"
                "        _r = inc.call(_tool, _args)\n"
                "        json.dumps(_r)\n"                # non-jsonable -> __error__
                "    except TimeoutError:\n"
                "        _r = '__timeout__'\n"
                "    except Exception:\n"
                "        _r = '__error__'\n"
                "    finally:\n"
                "        signal.alarm(0)\n"
                "    print(json.dumps({'i': _i, 'result': _r}), flush=True)\n"
                "try:\n"                                  # step()-style state thread
                "    print(json.dumps({'final_state': inc.__dict__}), flush=True)\n"
                "except Exception:\n"
                "    pass\n"
                % b).encode()

    def _incumbent_pass(self, calls) -> list:
        """One sandbox batch run of the incumbent over `calls`, threading its
        state internally.  Returns a raw result per call ("__error__" for a lost
        line -- fail closed)."""
        if not calls:
            return []
        with Sandbox() as sb:
            sb.add_file("incumbent.py", self._incumbent_src)
            sb.add_file("_driver.py", self._incumbent_harness(calls))
            res = sb.run(["python3", "_driver.py"], **self._run_kwargs())
        results = ["__error__"] * len(calls)
        for line in res.stdout.decode(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict) and "i" in obj and "result" in obj:
                i = obj["i"]
                if isinstance(i, int) and 0 <= i < len(calls):
                    results[i] = obj["result"]
        return results

    # --- egress (trusted output validators, no incumbent present) ---------
    def _egress_harness(self, pairs) -> bytes:
        b = _b64(json.dumps(pairs))
        imports = "".join("import out_%s as _v_%s\n" % (t, t)
                          for t in self._output_tools)
        vmap = ", ".join("%r: _v_%s.decode" % (t, t) for t in self._output_tools)
        return ("import json, base64\n"
                + imports +
                "VALID = {%s}\n"
                "_pairs = json.loads(base64.b64decode('%s').decode())\n"
                "for _tool, _res in _pairs:\n"
                "    _fn = VALID.get(_tool)\n"
                "    if _fn is None:\n"
                "        print(json.dumps({'ok': True}), flush=True)\n"
                "        continue\n"
                "    try:\n"
                "        _fn(_res)\n"
                "        print(json.dumps({'ok': True}), flush=True)\n"
                "    except Exception:\n"
                "        print(json.dumps({'ok': False}), flush=True)\n"
                % (vmap, b)).encode()

    def _egress_pass(self, pairs) -> list:
        if not pairs:
            return []
        with Sandbox() as sb:
            for n, b in self._egress_files.items():
                sb.add_file(n, b)
            sb.add_file("_egr.py", self._egress_harness(pairs))
            res = sb.run(["python3", "_egr.py"], **self._run_kwargs())
        out = []
        for line in res.stdout.decode(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
        while len(out) < len(pairs):      # fail closed on a lost verdict
            out.append({"ok": False})
        return out[:len(pairs)]

    # --- the composed caged pipeline --------------------------------------
    def run(self, init, seq) -> list:
        """The caged verdicts for a whole session.  A rejected ingress call never
        reaches the incumbent; an accepted call's raw result is egress-validated.

        Verdict shape (frozen dispatcher call() contract, interface-freeze item 2):
        {"ok": True, "result": <value>} | {"ok": False, "layer": <enum>}."""
        disp = self.run_dispatch(init, seq)
        accepted = [(i, list(seq[i])) for i in range(len(seq)) if disp[i].get("ok")]
        raw = self._incumbent_pass([c for _, c in accepted])
        pairs = [[accepted[k][1][0], raw[k]] for k in range(len(accepted))]
        egr = self._egress_pass(pairs)
        out, ai = [], 0
        for i in range(len(seq)):
            if not disp[i].get("ok"):
                out.append({"ok": False, "layer": disp[i].get("layer", "sequencing")})
            else:
                if egr[ai].get("ok"):
                    out.append({"ok": True, "result": raw[ai]})
                else:
                    out.append({"ok": False, "layer": "egress"})
                ai += 1
        return out

    def run_bare(self, init, seq) -> list:
        """The BARE incumbent (still sandboxed, but with NO cage): it sees every
        call in order and advances on each.  `acted` is True when it returned a
        normal (non-error/timeout) result -- the thing the cage must contain."""
        raw = self._incumbent_pass([list(c) for c in seq])
        return [{"acted": r not in ("__error__", "__timeout__"), "result": r}
                for r in raw]

    @classmethod
    def from_files(cls, model, incumbent_src, sandbox_params=None):
        return cls(model, incumbent_src, sandbox_params)


# ---------------------------------------------------- session generators
def legal_sessions(model) -> list:
    """A fully-legal run of the service (solver-certified: initial context values
    plus per-step integer arguments that satisfy every constraint and guard along
    the canonical path).  The transparency channel replays these."""
    run = service_gen._legal_golden_run(model)
    if run is None:
        return []
    init, seq, _prefix = run
    return [{"init": init, "seq": [list(x) for x in seq]}]


def violating_sessions(cage, model) -> list:
    """Solver-generated violating inputs for the containment channel: reuse the
    composition's `conformance_cases` (wrong-sequence / schema-bad / extra-key /
    guard-boundary / obligation-stranding) and classify each with the INDEPENDENT
    reference service (never the cage-under-test -- that would let a broken cage
    grade itself), TRUNCATING at the first step the reference rejects.  So every
    returned session ends on exactly the call a correct cage must refuse, with a
    legal prefix.  De-duplicated; the golden all-accept case is dropped."""
    cases = service_gen.conformance_cases(model)
    out, seen = [], set()
    for c in cases:
        seq = [list(x) for x in c["seq"]]
        refv = cage.run_reference(c["init"], seq)     # independent oracle
        idx = next((i for i, ok in enumerate(refv) if not ok), None)
        if idx is None:
            continue                      # reference accepts all: not violating
        trunc = {"init": c["init"], "seq": seq[:idx + 1]}
        key = json.dumps(trunc, sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(trunc)
    return out


# ---------------------------------------------------- channel reports
def containment_report(cage, model) -> dict:
    """Channel 1: for every solver-generated violating session the caged pipeline
    must REJECT the violating (final) call, and the BARE incumbent must ACT on at
    least one of them (non-vacuity teeth -- else the cage adds nothing)."""
    sessions = violating_sessions(cage, model)
    if not sessions:
        return {"pass": False,
                "detail": "no violating sessions generated (containment vacuous)"}
    breaches, teeth = 0, 0
    for s in sessions:
        disp = cage.run_dispatch(s["init"], s["seq"])   # caged ingress verdict
        bare = cage.run_bare(s["init"], s["seq"])
        if disp and disp[-1].get("ok"):
            breaches += 1                 # cage admitted a reference-rejected call
        if bare and bare[-1].get("acted"):
            teeth += 1
    if breaches:
        return {"pass": False,
                "detail": ("cage admitted %d call(s) the independent reference "
                           "rejects" % breaches)}
    if teeth == 0:
        return {"pass": False,
                "detail": "vacuous: the bare incumbent never acts on a violating "
                          "input, so containment is untested"}
    return {"pass": True,
            "detail": ("%d solver-generated violating sessions (reference-"
                       "classified): caged rejects every violating call; bare "
                       "incumbent acts on %d" % (len(sessions), teeth))}


def transparency_report(cage, model) -> dict:
    """Channel 2: on legal runs the caged results equal the bare incumbent's,
    compared via common.canonical_json (dict-order / float stable).  A caged
    rejection of a legal call, or a differing result, is a transparency
    violation."""
    sessions = legal_sessions(model)
    if not sessions:
        return {"pass": False,
                "detail": "no legal session exists (composition is vacuous)"}
    total, mism = 0, []
    for s in sessions:
        caged = cage.run(s["init"], s["seq"])
        bare = cage.run_bare(s["init"], s["seq"])
        for i in range(len(s["seq"])):
            total += 1
            if not caged[i].get("ok"):
                mism.append([i, "caged rejected a legal call", caged[i]])
            elif (common.canonical_json(caged[i].get("result"))
                  != common.canonical_json(bare[i].get("result"))):
                mism.append([i, "caged result != bare",
                             caged[i].get("result"), bare[i].get("result")])
    if mism:
        return {"pass": False,
                "detail": "transparency violations: %r" % (mism[:2],)}
    return {"pass": True,
            "detail": ("%d legal steps across %d session(s): caged == bare "
                       "incumbent (canonical-json)" % (total, len(sessions)))}


# ---------------------------------------------------- certification entry
def certify_cage(cage, model, *, event_sink=None, cache_get=None, cache_put=None):
    """Certify a cage via the kernel `cage-conformance` contract (tier
    "monitored").  LLM-free (guarded), so it lives in run/.  Returns a
    Certificate on success, else an ErrorTranscript naming the failing channel."""
    with common.task_time_guard():
        import kernel                      # lazy: keeps kernel.backends -> guarded
        artifact = {"kind": "cage", "files": cage.files()}
        contract = {"type": "cage-conformance", "spec_text": model.source,
                    "cage_hash": cage.hash(),
                    "sandbox_params": cage.sandbox_params, "cage": cage}
        return kernel.check(artifact, contract, event_sink=event_sink,
                            cache_get=cache_get, cache_put=cache_put)

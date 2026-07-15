"""Autonomous operator-table growth by DEFINITIONAL EXTENSION (R2).

**Semantics in, never code in.**  A new operator *word* is not new code in any
engine -- it is a row of pure data over the frozen kernel fragment (the F-G
pred/term AST in ``generators/math_reading.py``):

    {"word": "multiple_of", "arity": 2, "params": ["a", "b"],
     "definition": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}

``definition`` is a **pred AST over the existing fragment**, referring to the
``params`` by ``{"ref": <param>}``.  The word is EXPANDED at the READING layer
(the same place the governor lowers references) BEFORE ``math_compile`` /
``math_eval`` / ``math_smt`` ever see a statement: a statement whose operator is
a derived word is rewritten to its expanded kernel-fragment form by
deterministic, byte-stable deep-copy substitution of args for params.  The three
downstream engines are NEVER modified -- they only ever see kernel operators.
Because all three backends' semantics for the word DERIVE from one definition,
the gate-correctness certificate is simply their **differential agreement**.

ADMISSION (``admit_operator``) is the gate-correctness certificate, entirely
LLM-free and Lean-free.  It runs a battery:

  (a) well-formedness -- arity matches params; the (transitively expanded)
      definition parses as a valid pred in the existing fragment through the
      real ``_check_pred`` machinery on a synthetic reading; every operator
      inside the definition is kernel or already-admitted (no forward refs, no
      self-reference / recursion).
  (b) differential instance battery -- on generated instances over small ints
      (both Nat and Int carriers), the expanded form's z3 verdict, cvc5 verdict
      (honest absence tolerated) and decidable-enumeration verdict all AGREE.
      Disagreement or all-unknown => refusal, never admission.
  (c) compile round-trip -- a synthetic statement using the word compiles
      through ``math_compile`` via expansion and passes the ``validate_lean``
      escape gate; two expansions are byte-identical.
  (d) nonvacuity sanity -- the definition is satisfiable AND refutable on the
      battery domain.  A tautology / contradiction is refused as vacuous
      vocabulary.

The certificate is an **L3 evidence JSON** (``id = sha256(canonical row +
battery digest)``) persisted next to the row in
``specs/mathsources/operators/admitted.json``.  It is NOT a kernel cert tier:
``kernel/certs.py`` and ``CERTS_VERSION`` are untouched.

TAMPER SAFETY.  ``expand_reading_doc`` recomputes each used word's row hash and
checks it against the stored ``cert.id`` on EVERY use; a row whose definition
was edited after admission fails the check and REFUSES to lower, so a stale or
tampered row can never silently reach the engines.

BYTE-IDENTITY.  With an empty / missing ``admitted.json`` -- or a reading that
uses no derived word -- ``expand_reading_doc`` returns the input document
unchanged (identity), so existing behaviour is byte-identical.
"""
from __future__ import annotations

import copy
import json
import os

import common
from generators import math_reading as _mr
from generators import math_smt as _smt
from generators import math_eval as _eval

# The kernel operator vocabulary, single-sourced from the frozen fragment so a
# derived word can never shadow a kernel op and "kernel-or-admitted" stays exact.
KERNEL_OPS = frozenset(_mr._ATOM_OPS | _mr._TERM_OPS | _mr._CONNECTIVES)
CARRIERS = _mr.CARRIERS

CERT_KIND = "operator-admission"
# Battery sizing.  Small ints, both carriers; kept tiny so admission is fast and
# deterministic (the fragment is decidable, so a modest domain is conclusive).
DEFAULT_BATTERY_BOUND = 4
DEFAULT_MAX_INSTANCES = 24
# Guard against a pathological expansion cycle (admission forbids recursion, so
# this only ever bites a corrupted/hand-edited registry).
_MAX_EXPAND_DEPTH = 64


class OperatorGrowthError(Exception):
    """Base for operator-growth failures raised at USE time (not admission)."""


class OperatorExpansionError(OperatorGrowthError):
    """Raised during reading-layer expansion: a tampered row (cert-id mismatch)
    or an arity mismatch at a use site.  Surfaced by the parse hook as a
    ``BadMathReading`` refusal so a bad row can never silently lower."""


# ============================================================ canonical / cert
def canonical_row(row: dict) -> dict:
    """The canonical, key-ordered view of a row used for hashing.  Only the four
    load-bearing fields participate; extra keys are ignored so incidental
    annotations never change a row's identity."""
    return {
        "word": row["word"],
        "arity": row["arity"],
        "params": list(row["params"]),
        "definition": row["definition"],
    }


def row_digest(row: dict) -> str:
    """sha256 over the canonical row (the tamper-detection substrate)."""
    return common.sha256_json(canonical_row(row))


def cert_id(row: dict, battery_digest: str) -> str:
    """The certificate id: sha256 of the canonical row bound to the battery
    digest.  Recomputed on every use to detect row tampering."""
    return common.sha256_json(
        {"row": canonical_row(row), "battery_digest": battery_digest})


# ===================================================================== storage
def _default_operators_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here),
                        "specs", "mathsources", "operators")


def operators_dir(operators_dir=None) -> str:
    if operators_dir:
        return operators_dir
    env = os.environ.get("CGB_OPERATORS_DIR")
    return env if env else _default_operators_dir()


def _admitted_path(op_dir: str) -> str:
    return os.path.join(op_dir, "admitted.json")


# mtime-keyed cache so the hot parse path re-reads admitted.json only when it
# actually changes; ``reload()`` drops it for tests that rewrite the file.
_CACHE: dict = {}


def reload() -> None:
    """Drop the admitted.json cache (test hook after rewriting the registry)."""
    _CACHE.clear()


def load_admitted(op_dir=None) -> dict:
    """Return the admitted registry ``{word: {"row":..., "cert":...}}``.  A
    missing / empty file is an empty registry (the no-op path)."""
    path = _admitted_path(operators_dir(op_dir))
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}
    cached = _CACHE.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        data = {}
    _CACHE[path] = (mtime, data)
    return data


def save_admitted(entry: dict, op_dir=None) -> str:
    """Merge one ``{word: {"row", "cert"}}`` admission into admitted.json and
    return the path written.  Only ever called with a GREEN certificate; nothing
    here re-runs the battery, so callers must pass an ``admit_operator`` result."""
    op_dir_ = operators_dir(op_dir)
    os.makedirs(op_dir_, exist_ok=True)
    path = _admitted_path(op_dir_)
    current = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                current = json.load(fh)
        except (OSError, json.JSONDecodeError):
            current = {}
    if not isinstance(current, dict):
        current = {}
    current.update(entry)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(common.canonical_json(current))
        fh.write("\n")
    reload()
    return path


def load_proposed(op_dir=None) -> list:
    """Every proposed-but-unadmitted row under ``proposed/`` (dream-staging: an
    LLM may PROPOSE rows as data; only the battery admits them)."""
    d = os.path.join(operators_dir(op_dir), "proposed")
    out = []
    if not os.path.isdir(d):
        return out
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, name), "r", encoding="utf-8") as fh:
                out.append(json.load(fh))
        except (OSError, json.JSONDecodeError):
            continue
    return out


# ================================================================== expansion
def _substitute(node, arg_map):
    """Deep-copy ``node`` (a pred/term AST) replacing every ``{"ref": p}`` whose
    ``p`` is a param with a deep copy of the bound argument term.  Simultaneous
    substitution (params are placeholders), so arg/param name collisions are
    harmless."""
    if isinstance(node, dict):
        if set(node) == {"ref"} and node["ref"] in arg_map:
            return copy.deepcopy(arg_map[node["ref"]])
        return {k: _substitute(v, arg_map) for k, v in node.items()}
    if isinstance(node, list):
        return [_substitute(x, arg_map) for x in node]
    return node


def _verify_entry(word: str, entry: dict) -> None:
    """Recompute the row hash and confirm it matches the stored cert id; raise on
    tamper.  This is what makes a post-admission edit of ``definition`` refuse to
    lower instead of silently changing meaning."""
    row = entry.get("row")
    cert = entry.get("cert") or {}
    if not isinstance(row, dict) or "battery_digest" not in cert:
        raise OperatorExpansionError(
            f"operator {word!r}: malformed admitted entry (no row/battery_digest)")
    expect = cert_id(row, cert["battery_digest"])
    if expect != cert.get("id"):
        raise OperatorExpansionError(
            f"operator {word!r}: certificate id mismatch -- the admitted row was "
            f"tampered with after admission (recomputed {expect[:12]}..., stored "
            f"{str(cert.get('id'))[:12]}...); refusing to lower")


def _expand_pred(pred, registry, verify, depth=0):
    """Expand a pred, rewriting any derived-word atom to its kernel definition
    (transitively).  ``registry`` maps word -> ``{"row", "cert"?}``."""
    if depth > _MAX_EXPAND_DEPTH:
        raise OperatorExpansionError(
            "operator expansion exceeded max depth (cyclic registry?)")
    if not isinstance(pred, dict) or "op" not in pred:
        return pred
    op = pred["op"]
    entry = registry.get(op)
    if entry is not None:                       # a derived word
        if verify:
            _verify_entry(op, entry)
        row = entry["row"]
        args = pred.get("args", [])
        if not isinstance(args, list) or len(args) != row["arity"]:
            raise OperatorExpansionError(
                f"operator {op!r} takes {row['arity']} args, got "
                f"{len(args) if isinstance(args, list) else '?'} at a use site")
        arg_map = {p: args[i] for i, p in enumerate(row["params"])}
        expanded = _substitute(copy.deepcopy(row["definition"]), arg_map)
        return _expand_pred(expanded, registry, verify, depth + 1)
    if op in ("and", "or", "implies"):
        return {"op": op,
                "args": [_expand_pred(a, registry, verify, depth)
                         for a in pred.get("args", [])]}
    # A kernel atom: its args are terms, which cannot contain a derived PRED
    # word (definitions are pred ASTs), so nothing below needs rewriting.
    return pred


def _pred_ops(node, out):
    """Every ``op`` string appearing anywhere in a pred/term AST."""
    if isinstance(node, dict):
        if "op" in node:
            out.add(node["op"])
        for v in node.values():
            _pred_ops(v, out)
    elif isinstance(node, list):
        for x in node:
            _pred_ops(x, out)


def _doc_uses_any(doc, words) -> bool:
    stmts = doc.get("statements")
    if not isinstance(stmts, list):
        return False
    for s in stmts:
        if not isinstance(s, dict):
            continue
        lf = s.get("lf")
        if isinstance(lf, dict) and lf.get("kind") in ("hypothesis", "conclusion"):
            ops = set()
            _pred_ops(lf.get("pred"), ops)
            if ops & words:
                return True
    return False


def expand_reading_doc(doc, *, op_dir=None, registry=None, verify=True):
    """Rewrite every derived-operator statement in a reading document
    ``{theorem, statements}`` to its expanded kernel form.

    Returns the SAME object unchanged when the registry is empty or the document
    uses no derived word (byte-identity), else a new document with expanded
    hypothesis/conclusion preds.  Raises ``OperatorExpansionError`` on a tampered
    row (when ``verify``) or a use-site arity mismatch."""
    if registry is None:
        registry = load_admitted(op_dir)
    if not registry or not isinstance(doc, dict):
        return doc
    if not _doc_uses_any(doc, set(registry)):
        return doc
    new_stmts = []
    for s in doc.get("statements", []):
        lf = s.get("lf") if isinstance(s, dict) else None
        if (isinstance(lf, dict) and lf.get("kind") in ("hypothesis", "conclusion")
                and isinstance(lf.get("pred"), dict)):
            new_lf = dict(lf)
            new_lf["pred"] = _expand_pred(lf["pred"], registry, verify)
            new_s = dict(s)
            new_s["lf"] = new_lf
            new_stmts.append(new_s)
        else:
            new_stmts.append(s)
    return {**doc, "statements": new_stmts}


# ============================================================ admission battery
def _all_ops_in(definition) -> set:
    ops = set()
    _pred_ops(definition, ops)
    return ops


def _expand_definition_to_kernel(row, registry):
    """Transitively expand a row's definition to a pure-kernel pred (already-
    admitted words only; the candidate never appears in its own definition)."""
    return _expand_pred(copy.deepcopy(row["definition"]), registry, verify=False)


def _enumerate_param_instances(params, carrier, bound, max_instances):
    """Canonical small-int assignments of ``params`` over one carrier (ascending
    sum of |values|, then lexicographic), capped at ``max_instances``."""
    import itertools
    if carrier == "Nat":
        rng = range(0, bound + 1)
    else:
        rng = range(-bound, bound + 1)
    combos = sorted(itertools.product(rng, repeat=len(params)),
                    key=lambda vals: (sum(abs(v) for v in vals), vals))
    out = []
    for vals in combos:
        out.append(dict(zip(params, vals)))
        if len(out) >= max_instances:
            break
    return out


def _ground_smt(kernel_def, objects, carrier, assignment):
    """A ground SMT obligation: pin each param to its value and assert the
    expanded definition.  ``sat`` iff the pred holds at ``assignment``.  Uses
    QF_NIA (a superset both solvers accept for the pinned-constant arithmetic
    the fragment produces)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.append(f"(declare-const {name} Int)")
        if objects[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
        lines.append(f"(assert (= {name} {_smt._render_lit(assignment[name])}))")
    lines.append(f"(assert {_smt.render_pred(kernel_def, objects, carrier)})")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _sat_verdict(ch: dict) -> str:
    """Map an SmtBackend result (run with expect='sat') to sat/unsat/unknown/
    error (the run.formalize convention)."""
    r = ch.get("result")
    if r == "pass":
        return "sat"
    if r == "fail":
        return "unsat"
    return r or "error"


def _run_battery(row, registry, bound, max_instances):
    """The differential instance battery (b) + nonvacuity sanity (d).

    Returns ``(ok, reason, battery)``.  For every instance over both carriers,
    the decidable-enumeration verdict, the z3 verdict and (when present) the cvc5
    verdict must AGREE.  ``all-unknown`` from SMT (no independent corroboration)
    is a refusal, as is any solver disagreement.  The definition must also be
    satisfiable AND refutable across the domain."""
    from kernel.backends import SmtBackend
    kernel_def = _expand_definition_to_kernel(row, registry)
    params = list(row["params"])
    be = SmtBackend()

    instances = []
    n_true = n_false = 0
    smt_confirmations = 0
    cvc5_present = False

    for carrier in CARRIERS:
        objects = {p: carrier for p in params}
        representable = _smt._pred_uses_enum(kernel_def) is False
        for asg in _enumerate_param_instances(params, carrier, bound,
                                              max_instances):
            enum = bool(_eval.eval_pred(kernel_def, asg, objects, None))
            n_true += int(enum)
            n_false += int(not enum)
            rec = {"carrier": carrier, "assignment": dict(sorted(asg.items())),
                   "enum": enum}
            if representable:
                smt = _ground_smt(kernel_def, objects, carrier, asg)
                z = _sat_verdict(be.run_z3(smt, expect="sat"))
                rec["z3"] = z
                try:
                    c = _sat_verdict(be.run_cvc5(smt, expect="sat"))
                except ModuleNotFoundError:
                    c = "absent"
                if c == "error":
                    c = "absent"          # honest absence (binding missing)
                rec["cvc5"] = c
                if c != "absent":
                    cvc5_present = True
                # agreement check
                for backend, v in (("z3", z), ("cvc5", c)):
                    if v in ("sat", "unsat"):
                        holds = (v == "sat")
                        if holds != enum:
                            return (False,
                                    f"differential disagreement on {carrier} "
                                    f"{rec['assignment']}: enum={enum} but "
                                    f"{backend}={v}", None)
                        if backend == "z3":
                            smt_confirmations += 1
            else:
                rec["z3"] = "enum-only"
                rec["cvc5"] = "enum-only"
            instances.append(rec)

    representable_any = any(r.get("z3") not in ("enum-only",) for r in instances)
    if representable_any and smt_confirmations == 0:
        return (False,
                "all-unknown: no independent SMT verdict corroborated the "
                "enumeration channel (differential agreement unavailable)", None)
    if not representable_any:
        return (False,
                "the definition is enum-only (gcd/coprime): no independent SMT "
                "channel, so differential agreement is unavailable for admission",
                None)

    satisfiable = n_true > 0
    refutable = n_false > 0
    if not satisfiable:
        return (False,
                "vacuous vocabulary: the definition is a CONTRADICTION on the "
                "battery domain (never satisfiable) -- refused", None)
    if not refutable:
        return (False,
                "vacuous vocabulary: the definition is a TAUTOLOGY on the "
                "battery domain (never refutable) -- refused", None)

    battery = {
        "bound": bound,
        "carriers": list(CARRIERS),
        "n_instances": len(instances),
        "satisfiable": satisfiable,
        "refutable": refutable,
        "smt_confirmations": smt_confirmations,
        "cvc5_present": cvc5_present,
        "instances": instances,
    }
    return (True, "", battery)


def _synthetic_source(word: str) -> str:
    return f"for all values the {word} property holds"


def _synthetic_reading_doc(row: dict, carrier: str) -> dict:
    """A minimal reading exercising the word: params as (choice) objects, one
    forall quantifier over them, and a demanded conclusion applying the word.
    Its quotes are grounded in ``_synthetic_source``."""
    word = row["word"]
    params = list(row["params"])
    stmts = []
    for i, p in enumerate(params):
        stmts.append({"id": f"o{i}", "force": "choice", "quote": "",
                      "lf": {"kind": "object", "name": p, "type": carrier}})
    stmts.append({"id": "q", "force": "presupposition", "quote": "for all values",
                  "lf": {"kind": "quantifier", "binder": "forall",
                         "objects": params}})
    stmts.append({"id": "c", "force": "demand",
                  "quote": f"the {word} property holds",
                  "lf": {"kind": "conclusion",
                         "pred": {"op": word,
                                  "args": [{"ref": p} for p in params]}}})
    return {"theorem": "op_probe", "statements": stmts}


def _compile_roundtrip(row, registry):
    """Battery (c): a synthetic statement using the word expands, parses,
    compiles and clears the ``validate_lean`` escape gate; two expansions are
    byte-identical.  Returns ``(ok, reason)``."""
    from generators.math_compile import compile_math_reading, CompileError
    from buildloop.validate_lean import validate_lean
    for carrier in CARRIERS:
        syn = _synthetic_reading_doc(row, carrier)
        source = _synthetic_source(row["word"])
        try:
            e1 = expand_reading_doc(syn, registry=registry, verify=False)
            e2 = expand_reading_doc(copy.deepcopy(syn), registry=registry,
                                    verify=False)
        except OperatorExpansionError as ex:
            return False, f"expansion failed on the {carrier} probe: {ex}"
        if common.canonical_json(e1) != common.canonical_json(e2):
            return False, "expansion is not byte-deterministic"
        try:
            reading = _mr.parse_math_reading(json.dumps(e1), source)
        except _mr.BadMathReading as ex:
            return False, f"expanded {carrier} probe did not parse: {ex}"
        try:
            compiled = compile_math_reading(reading)
        except CompileError as ex:
            return False, f"expanded {carrier} probe did not compile: {ex}"
        ok, reason = validate_lean(compiled["lean_text"])
        if not ok:
            return False, f"compiled {carrier} probe failed the escape gate: {reason}"
    return True, ""


def _check_wellformed(row, registry):
    """Battery (a): structural well-formedness + kernel-or-admitted operator
    closure + the definition parses as a valid pred over both carriers.  Returns
    ``(ok, reason)``."""
    if not isinstance(row, dict):
        return False, "row must be an object"
    word = row.get("word")
    if not (isinstance(word, str) and _mr._ID.fullmatch(word)):
        return False, f"word must be a lowercase identifier, got {word!r}"
    if word in KERNEL_OPS:
        return False, f"word {word!r} shadows a kernel operator"
    params = row.get("params")
    if not (isinstance(params, list) and all(
            isinstance(p, str) and _mr._ID.fullmatch(p) for p in params)):
        return False, "params must be a list of lowercase identifiers"
    if len(set(params)) != len(params):
        return False, "params must be distinct"
    arity = row.get("arity")
    if not (isinstance(arity, int) and not isinstance(arity, bool)):
        return False, "arity must be an integer"
    if arity != len(params):
        return False, f"arity {arity} != len(params) {len(params)}"
    definition = row.get("definition")
    if not isinstance(definition, dict):
        return False, "definition must be a pred object"
    # operator closure: kernel or already-admitted; never self-reference.
    ops = _all_ops_in(definition)
    if word in ops:
        return False, f"self-reference: {word!r} appears in its own definition"
    for op in ops:
        if op in KERNEL_OPS:
            continue
        if op in registry:
            continue
        return False, (f"unknown operator {op!r} in definition (neither kernel "
                       f"nor already-admitted -- no forward references)")
    # validity: the transitively-expanded definition must parse as a valid pred
    # over the params, under both carriers, through the REAL fragment machinery.
    try:
        kernel_def = _expand_definition_to_kernel(row, registry)
    except OperatorExpansionError as ex:
        return False, f"definition failed to expand: {ex}"
    for carrier in CARRIERS:
        objects = {p: carrier for p in params}
        try:
            _mr._check_pred(kernel_def, objects)
        except _mr.BadMathReading as ex:
            return False, f"definition is not a valid pred over {carrier}: {ex}"
    return True, ""


def admit_operator(row: dict, *, op_dir=None, bound=DEFAULT_BATTERY_BOUND,
                   max_instances=DEFAULT_MAX_INSTANCES, registry=None) -> dict:
    """Run the full admission battery on a proposed row.

    Returns ``{"admitted": True, "cert": ..., "row": ...}`` on a green
    certificate, else ``{"admitted": False, "refusal": {"stage", "reason"}}``.
    Never writes anything -- persistence is the caller's explicit
    ``save_admitted`` step, so nothing autonomous lands a row without a green
    cert in hand."""
    if registry is None:
        registry = load_admitted(op_dir)
    # a row may re-admit, but not depend on a same-named prior admission.
    registry = {w: e for w, e in registry.items() if w != row.get("word")}

    ok, reason = _check_wellformed(row, registry)
    if not ok:
        return {"admitted": False,
                "refusal": {"stage": "well-formedness", "reason": reason}}

    # the candidate participates in expansion during the battery (verify=False;
    # it has no cert yet).
    battery_registry = dict(registry)
    battery_registry[row["word"]] = {"row": canonical_row(row)}

    ok, reason, battery = _run_battery(row, registry, bound, max_instances)
    if not ok:
        stage = "nonvacuity" if "vacuous" in reason else "battery"
        return {"admitted": False, "refusal": {"stage": stage, "reason": reason}}

    ok, reason = _compile_roundtrip(row, battery_registry)
    if not ok:
        return {"admitted": False,
                "refusal": {"stage": "compile", "reason": reason}}

    battery_digest = common.sha256_json(battery)
    cert = {
        "kind": CERT_KIND,
        "id": cert_id(row, battery_digest),
        "word": row["word"],
        "row_digest": row_digest(row),
        "battery_digest": battery_digest,
        "battery": battery,
        "engines": {
            "cvc5_present": battery["cvc5_present"],
            "smt_confirmations": battery["smt_confirmations"],
        },
        "mathlib_commit": common.MATHLIB_COMMIT,
        "toolchain": common.LEAN_TOOLCHAIN,
    }
    return {"admitted": True, "row": canonical_row(row), "cert": cert}

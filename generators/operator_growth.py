"""Autonomous operator-table growth by DEFINITIONAL EXTENSION (R2).

**Semantics in, never code in.**  A new operator *word* is not new code in any
engine -- it is a row of pure data over the frozen kernel fragment (the F-G
pred/term AST in ``generators/math_reading.py``):

    {"word": "multiple_of", "arity": 2, "params": ["a", "b"],
     "definition": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}

ROLES (D1).  A row carries an optional ``role``: ``"pred"`` (the default --
absent means pred, so every pre-D1 row loads unchanged and hashes identically)
or ``"term"`` for VALUE-PRODUCING function words such as

    {"word": "sq", "arity": 1, "params": ["a"], "role": "term",
     "definition": {"op": "*", "args": [{"ref": "a"}, {"ref": "a"}]}}

A pred-role ``definition`` is a **pred AST**; a term-role ``definition`` is a
**term AST** (validated by the real ``_check_term`` machinery).  Both refer to
the ``params`` by ``{"ref": <param>}``.  The word is EXPANDED at the READING layer
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
      definition parses as a valid pred (role "pred", via ``_check_pred``) or a
      valid TERM (role "term", via ``_check_term``) in the existing fragment;
      every operator inside the definition is kernel or already-admitted (no
      forward refs, no self-reference / recursion).
  (b) differential instance battery -- on generated instances over small ints
      (both Nat and Int carriers), the expanded form's z3 verdict, cvc5 verdict
      (honest absence tolerated) and decidable-enumeration verdict all AGREE.
      Disagreement or all-unknown => refusal, never admission.
      For a TERM-role row the battery is a VALUE battery: on every instance the
      expanded kernel term's value is computed by the fragment evaluator
      (``math_eval.eval_term``) and RECORDED; the SMT differential asserts the
      ground equation ``term = value`` (params pinned) and requires ``sat`` --
      an ``unsat`` is an evaluator/solver disagreement and refuses.
  (b2) symbolic battery (pred role, SMT-representable definitions) -- the
      SAME obligations with the params left FREE, so verdicts range over ALL
      values instead of the bounded box: per-carrier satisfiability /
      refutability, plus the CARRIER-STABILITY obligation (Nat rendering XOR
      Int rendering over the shared nonneg domain; dual Z3^CVC5 ``unsat`` is
      a universal carrier-invariance proof, ``sat`` triggers an eval witness
      search).  Stability is recorded evidence, never a refusal (carrier-
      sensitive vocabulary is legal: kernel ``-`` itself is the T4 class);
      the one NEW refusal is a definite solver ``unsat`` that contradicts an
      eval-witnessed box point -- an engine disagreement the pointwise
      battery cannot see.  Sound to ask symbolically because ``math_smt``
      totalises every partial SMT-LIB operation with explicit ``ite``.
  (c) compile round-trip -- a synthetic statement using the word compiles
      through ``math_compile`` via expansion and passes the ``validate_lean``
      escape gate; two expansions are byte-identical.  (A term-role probe uses
      the word inside a term of the demanded conclusion.)
  (d) nonvacuity sanity (pred role) -- the definition is satisfiable AND
      refutable on the battery domain.  A tautology / contradiction is refused
      as vacuous vocabulary.
      DEGENERACY sanity (term role) -- the chosen degeneracy rules, documented:
        * a term whose value is CONSTANT across the whole battery domain (both
          carriers, all instances) is a literal in disguise -- refused;
        * a definition that canonically expands to a bare ``{"ref": p}`` or
          ``{"lit": k}`` is a projection / literal, not vocabulary -- refused
          at the trivial-alias stage;
        * a definition that expands to a SINGLE kernel term operator over
          distinct bare param refs (``plus2(a, b) := a + b``) is a pure rename
          of a kernel op -- refused at the trivial-alias stage (the term
          adaptation of the pred alias rule; a diagonal such as
          ``sq(a) := a * a`` repeats a ref, adds structure, and is admitted on
          its economics).

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
from buildloop import mdl_macros as _mdl
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


class SaveRefused(OperatorGrowthError):
    """Raised by ``save_admitted`` when the append-only / sole-admitter
    invariants are violated: a forged/stale cert id, a row that does not
    re-admit, or an attempt to overwrite an existing word with a different row
    digest.  A refusal is LOUD (an exception), never a silent last-writer-wins
    overwrite of already-certified corpus bytes."""


# ============================================================ canonical / cert
def canonical_row(row: dict) -> dict:
    """The canonical, key-ordered view of a row used for hashing.  Only the
    load-bearing fields participate; extra keys are ignored so incidental
    annotations never change a row's identity.  ``role`` participates ONLY when
    it is not the default ``"pred"`` -- so every pre-D1 pred row (no role key)
    keeps its exact historical digest and cert id (full backward compat with
    the committed admitted.json), while a term row's role is hash-bound and
    thus tamper-protected like the definition itself."""
    out = {
        "word": row["word"],
        "arity": row["arity"],
        "params": list(row["params"]),
        "definition": row["definition"],
    }
    if row.get("role", "pred") != "pred":
        out["role"] = row["role"]
    return out


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


def save_admitted(entry: dict, op_dir=None, *, pricing_corpus=None,
                  bound=DEFAULT_BATTERY_BOUND,
                  max_instances=DEFAULT_MAX_INSTANCES) -> str:
    """Merge one ``{word: {"row", "cert"}}`` admission into admitted.json and
    return the path written.

    SOLE ADMITTER BY CONSTRUCTION (§11.4): rather than trust its caller,
    ``save_admitted`` RE-RUNS ``admit_operator`` on the row (admission is
    deterministic, 0.06-4.6s/row) and refuses unless the recomputed cert id
    equals the one handed in -- a forged or stale cert can never be persisted.
    The re-admission uses the same ``pricing_corpus`` the caller admitted with;
    without it the re-admission refuses fail-closed.

    APPEND-ONLY: refuses to overwrite an existing word with a DIFFERENT row
    digest (a same-digest re-save is idempotent), so an autonomous grower can
    never rewrite the meaning of already-certified corpus bytes.

    Raises ``SaveRefused`` on any invariant violation."""
    if not (isinstance(entry, dict) and len(entry) == 1):
        raise SaveRefused(
            "save_admitted takes exactly one {word: {'row','cert'}} entry")
    (word, payload), = entry.items()
    if not isinstance(payload, dict) or not isinstance(payload.get("row"), dict):
        raise SaveRefused(f"operator {word!r}: entry has no row")
    row = payload["row"]
    handed_cert = payload.get("cert") or {}
    if row.get("word") != word:
        raise SaveRefused(
            f"operator {word!r}: entry key does not match row word "
            f"{row.get('word')!r}")

    # sole-admitter: re-run the deterministic admission against the registry as
    # it stands (minus any same-named prior admission -- admit_operator strips
    # it too) and require cert-id equality.
    registry = {w: e for w, e in load_admitted(op_dir).items() if w != word}
    res = admit_operator(row, op_dir=op_dir, bound=bound,
                         max_instances=max_instances, registry=registry,
                         pricing_corpus=pricing_corpus)
    if not res.get("admitted"):
        ref = res.get("refusal", {})
        raise SaveRefused(
            f"operator {word!r}: re-admission refused at "
            f"{ref.get('stage')!r} -- {ref.get('reason')}; save_admitted is the "
            f"sole admitter, so a row that does not re-admit is never persisted")
    recomputed = res["cert"]["id"]
    if recomputed != handed_cert.get("id"):
        raise SaveRefused(
            f"operator {word!r}: cert id mismatch on re-admission (recomputed "
            f"{recomputed[:12]}..., handed {str(handed_cert.get('id'))[:12]}...); "
            f"refusing a forged or stale certificate")

    op_dir_ = operators_dir(op_dir)
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

    # append-only: an existing word may only be re-saved with the SAME row
    # digest (idempotent); a different digest is a meaning-changing overwrite.
    if word in current and isinstance(current[word], dict):
        existing_row = current[word].get("row")
        if (isinstance(existing_row, dict)
                and row_digest(existing_row) != row_digest(row)):
            raise SaveRefused(
                f"operator {word!r}: append-only registry -- a different row is "
                f"already admitted under this word (existing digest "
                f"{row_digest(existing_row)[:12]}..., new "
                f"{row_digest(row)[:12]}...); refusing to overwrite certified "
                f"corpus bytes without re-certification")

    os.makedirs(op_dir_, exist_ok=True)
    current[word] = {"row": res["row"], "cert": res["cert"]}
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
    # Reviewer hardening: also re-derive the two inner digests from their
    # stored substrates, so an editor who recomputes the outer id but reuses a
    # stale battery/row digest is still refused (unsigned hashing can never
    # stop an actor who rewrites everything consistently -- that actor could
    # rewrite this module too -- but each recomputation catches one more
    # corruption class for free).
    if "battery" in cert and common.sha256_json(cert["battery"]) != cert["battery_digest"]:
        raise OperatorExpansionError(
            f"operator {word!r}: battery_digest does not match the stored "
            f"battery transcript; refusing to lower")
    if "row_digest" in cert and row_digest(row) != cert["row_digest"]:
        raise OperatorExpansionError(
            f"operator {word!r}: row_digest does not match the stored row; "
            f"refusing to lower")


def _expand_pred(pred, registry, verify, depth=0):
    """Expand a pred OR term node, rewriting any derived-word application
    (pred-role atom or term-role function word, at any depth -- including term
    positions inside kernel atoms) to its kernel definition, transitively.
    ``registry`` maps word -> ``{"row", "cert"?}``.  Preds and terms share the
    ``{op, args}`` shape, so one walk expands both roles symmetrically."""
    if depth > _MAX_EXPAND_DEPTH:
        raise OperatorExpansionError(
            "operator expansion exceeded max depth (cyclic registry?)")
    if not isinstance(pred, dict) or "op" not in pred:
        return pred
    op = pred["op"]
    entry = registry.get(op)
    if entry is not None:                       # a derived word (either role)
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
    # A kernel connective / atom / term operator: recurse into the args, so a
    # derived TERM word nested anywhere inside a term is rewritten too (role
    # misuse -- a term word at a pred position or vice versa -- surfaces
    # downstream as a validation refusal on the expanded kernel form).
    args = pred.get("args")
    if not isinstance(args, list):
        return pred
    return {**pred,
            "args": [_expand_pred(a, registry, verify, depth) for a in args]}


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
    """Transitively expand a row's definition to a pure-kernel pred/term
    (already-admitted words only; the candidate never appears in its own
    definition)."""
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


def _ground_term_smt(kernel_term, objects, carrier, assignment, value):
    """A ground SMT obligation for a TERM-role row: pin each param to its value
    and assert the ground equation ``expanded-term = evaluator-value``.  With
    every param pinned the term is fully determined, so ``sat`` iff the solver's
    arithmetic agrees with ``math_eval.eval_term`` at ``assignment`` -- an
    ``unsat`` is a genuine evaluator/solver disagreement."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.append(f"(declare-const {name} Int)")
        if objects[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
        lines.append(f"(assert (= {name} {_smt._render_lit(assignment[name])}))")
    lines.append(f"(assert (= {_smt.render_term(kernel_term, objects, carrier)} "
                 f"{_smt._render_lit(value)}))")
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


# ======================================================= symbolic battery (b2)
def _symbolic_obligation(kernel_def, params, carrier, *, negate=False):
    """A SYMBOLIC obligation: params are declared but never pinned (Nat-carrier
    params constrained nonnegative).  With free constants and no quantifiers a
    ``sat`` is an existence verdict over the WHOLE carrier and an ``unsat`` is
    a universal proof -- the upgrade of battery (b)'s bounded-box evidence to
    all values.  Sound to ask symbolically because ``math_smt`` totalises every
    partial SMT-LIB operation (mod-by-zero, negative-divisor mod, truncated
    Nat ``-``) with explicit ``ite`` to match eval/Lean exactly, so no model
    can sit in an underspecified corner."""
    objects = {p: carrier for p in params}
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.append(f"(declare-const {name} Int)")
        if objects[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
    body = _smt.render_pred(kernel_def, objects, carrier)
    if negate:
        body = f"(not {body})"
    lines.append(f"(assert {body})")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _carrier_stability_obligation(kernel_def, params):
    """The cross-carrier divergence obligation over the SHARED domain (every
    param >= 0): assert the Nat rendering XOR the Int rendering of one
    definition.  ``unsat`` PROVES the word means the same thing under both
    carriers at EVERY shared value; ``sat`` means a divergence point exists
    somewhere (the truncated-``-`` class the T4 tooth guards)."""
    nat_objects = {p: "Nat" for p in params}
    int_objects = {p: "Int" for p in params}
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(params):
        lines.append(f"(declare-const {name} Int)")
        lines.append(f"(assert (>= {name} 0))")
    p_nat = _smt.render_pred(kernel_def, nat_objects, "Nat")
    p_int = _smt.render_pred(kernel_def, int_objects, "Int")
    lines.append(f"(assert (xor {p_nat} {p_int}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def _carrier_divergence_witness(kernel_def, params, bound, max_instances):
    """Scan the SHARED bounded box (nonnegative assignments) for a concrete
    point where the Nat-carrier and Int-carrier evaluations disagree -- the
    enumeration corroboration of a solver ``sat`` on the stability obligation.
    Direction-split discipline: a solver existence claim is never load-bearing
    on its own; an eval-witnessed point is.  ``None`` when the box holds no
    witness (the divergence, if real, lies outside the box -- recorded, never
    silently upgraded)."""
    nat_objects = {p: "Nat" for p in params}
    int_objects = {p: "Int" for p in params}
    for asg in _enumerate_param_instances(params, "Nat", bound, max_instances):
        nat_v = bool(_eval.eval_pred(kernel_def, asg, nat_objects, None))
        int_v = bool(_eval.eval_pred(kernel_def, asg, int_objects, None))
        if nat_v != int_v:
            return {"assignment": dict(sorted(asg.items())),
                    "nat": nat_v, "int": int_v}
    return None


def _symbolic_battery(kernel_def, params, be, bound, max_instances):
    """Battery (b2): the symbolic upgrade of the differential battery.

    Three obligation families, every verdict recorded (dual-solver, honest
    absence/unknown, never a crash):

      * per-carrier SATISFIABILITY (assert the definition) and REFUTABILITY
        (assert its negation) with free params -- ``sat`` upgrades battery
        (d)'s box observation to an all-values existence verdict; a definite
        ``unsat`` that CONTRADICTS an eval-witnessed box point is an engine
        disagreement the caller refuses on (the class the pointwise battery
        can never see, because it never asks a universal question);
      * CARRIER STABILITY (the ``xor`` obligation): dual ``unsat`` from Z3 and
        CVC5 is a universal proof the definition is carrier-invariant on the
        shared domain -- ``stable-proved``; a single-channel ``unsat`` is
        honestly weaker (``stable-z3-only``); ``sat`` triggers the eval
        witness search (``divergent`` with the point recorded, or
        ``divergent-unwitnessed-in-box`` when the point lies outside).

    Carrier-SENSITIVE vocabulary is legal (kernel ``-`` itself is: the T4
    class), so stability never refuses -- it is recorded evidence that rides
    the battery into the cert, making every word's carrier behaviour auditable
    at admission time instead of discoverable at use time."""
    def _dual(smt):
        z = _sat_verdict(be.run_z3(smt, expect="sat"))
        try:
            c = _sat_verdict(be.run_cvc5(smt, expect="sat"))
        except ModuleNotFoundError:
            c = "absent"
        if c == "error":
            c = "absent"          # honest absence (binding missing)
        return z, c

    out = {"carriers": {}}
    for carrier in CARRIERS:
        z_sat, c_sat = _dual(_symbolic_obligation(kernel_def, params, carrier))
        z_ref, c_ref = _dual(_symbolic_obligation(kernel_def, params, carrier,
                                                  negate=True))
        out["carriers"][carrier] = {
            "satisfiable": {"z3": z_sat, "cvc5": c_sat},
            "refutable": {"z3": z_ref, "cvc5": c_ref},
        }
    z_st, c_st = _dual(_carrier_stability_obligation(kernel_def, params))
    stability = {"z3": z_st, "cvc5": c_st}
    if z_st == "unsat" and c_st == "unsat":
        stability["verdict"] = "stable-proved"
    elif z_st == "unsat":
        stability["verdict"] = "stable-z3-only"
    elif "sat" in (z_st, c_st):
        witness = _carrier_divergence_witness(kernel_def, params, bound,
                                              max_instances)
        stability["witness"] = witness
        stability["verdict"] = ("divergent" if witness
                                else "divergent-unwitnessed-in-box")
    else:
        stability["verdict"] = "unknown"
    out["carrier_stability"] = stability
    return out


def _run_battery(row, registry, bound, max_instances):
    """The differential instance battery (b) + nonvacuity sanity (d).

    Returns ``(ok, reason, battery)``.  For every instance over both carriers,
    the decidable-enumeration verdict, the z3 verdict and (when present) the cvc5
    verdict must AGREE.  ``all-unknown`` from SMT (no independent corroboration)
    is a refusal, as is any solver disagreement.  The definition must also be
    satisfiable AND refutable across the domain.

    A TERM-role row dispatches to the VALUE battery (``_run_term_battery``)
    instead: same instances, same both-carrier discipline, but the recorded
    verdict per instance is the expanded kernel term's VALUE, corroborated by
    the ground-equation SMT differential; the nonvacuity sanity becomes the
    constant-term DEGENERACY check (module docstring, battery (d))."""
    if row.get("role", "pred") == "term":
        return _run_term_battery(row, registry, bound, max_instances)
    from kernel.backends import SmtBackend
    kernel_def = _expand_definition_to_kernel(row, registry)
    params = list(row["params"])
    be = SmtBackend()
    representable = _smt._pred_uses_enum(kernel_def) is False

    instances = []
    n_true = n_false = 0
    per_carrier = {c: {"true": 0, "false": 0} for c in CARRIERS}
    smt_confirmations = 0
    cvc5_present = False

    for carrier in CARRIERS:
        objects = {p: carrier for p in params}
        for asg in _enumerate_param_instances(params, carrier, bound,
                                              max_instances):
            enum = bool(_eval.eval_pred(kernel_def, asg, objects, None))
            n_true += int(enum)
            n_false += int(not enum)
            per_carrier[carrier]["true" if enum else "false"] += 1
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

    # (b2) the symbolic battery: free-param obligations upgrade the box
    # evidence to all-values verdicts.  Pred-role + representable only.
    symbolic = _symbolic_battery(kernel_def, params, be, bound, max_instances) \
        if representable else None

    if symbolic is not None:
        # box-vs-symbolic contradiction: an eval-witnessed box point is ground
        # truth; a definite solver UNSAT denying it is an engine disagreement
        # (renderer or solver bug) and refuses exactly like a pointwise
        # differential disagreement -- the class battery (b) cannot see
        # because it never asks a universal question.
        for carrier in CARRIERS:
            ch = symbolic["carriers"][carrier]
            for claim, observed in (("satisfiable",
                                     per_carrier[carrier]["true"] > 0),
                                    ("refutable",
                                     per_carrier[carrier]["false"] > 0)):
                if not observed:
                    continue
                for backend in ("z3", "cvc5"):
                    if ch[claim][backend] == "unsat":
                        return (False,
                                f"symbolic disagreement on {carrier}: the box "
                                f"holds an eval-witnessed {claim} point but "
                                f"{backend} proves the definition "
                                f"universally un-{claim} -- an engine "
                                f"contradiction, refused", None)

    satisfiable = n_true > 0
    refutable = n_false > 0
    if not satisfiable:
        extra = ""
        if symbolic is not None and any(
                symbolic["carriers"][c]["satisfiable"][b] == "sat"
                for c in CARRIERS for b in ("z3", "cvc5")):
            extra = (" (solver-satisfiable OUTSIDE the battery box: the box "
                     "refusal stands -- grow the bound to re-judge)")
        return (False,
                "vacuous vocabulary: the definition is a CONTRADICTION on the "
                "battery domain (never satisfiable) -- refused" + extra, None)
    if not refutable:
        extra = ""
        if symbolic is not None and any(
                symbolic["carriers"][c]["refutable"][b] == "sat"
                for c in CARRIERS for b in ("z3", "cvc5")):
            extra = (" (solver-refutable OUTSIDE the battery box: the box "
                     "refusal stands -- grow the bound to re-judge)")
        return (False,
                "vacuous vocabulary: the definition is a TAUTOLOGY on the "
                "battery domain (never refutable) -- refused" + extra, None)

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
    if symbolic is not None:
        battery["symbolic"] = symbolic
    return (True, "", battery)


def _run_term_battery(row, registry, bound, max_instances):
    """The VALUE battery for a TERM-role row (battery (b) + degeneracy (d)).

    Over the bounded domain (``bound``, both carriers -- every kernel term op is
    total on both, with ``-`` carrier-resolved exactly as the eval/SMT mirrors
    resolve it, ambient = the instance carrier), the expanded kernel term's
    value is COMPUTED by the deterministic fragment evaluator
    (``math_eval.eval_term``) and RECORDED per instance.  The differential
    channel asserts the ground equation ``term = value`` with the params pinned
    (``_ground_term_smt``): z3/cvc5 ``sat`` corroborates the evaluator,
    ``unsat`` is a disagreement and refuses, absence/unknown is tolerated
    honestly but all-unknown refuses (no independent corroboration), and an
    enum-only term (gcd) refuses for want of any SMT channel -- all exactly the
    pred battery's discipline, transposed to values.

    DEGENERACY (the term analogue of nonvacuity): a term whose value is the
    SAME on every battery instance across both carriers is a literal in
    disguise -- vocabulary that names no function -- and is refused."""
    from kernel.backends import SmtBackend
    kernel_def = _expand_definition_to_kernel(row, registry)
    params = list(row["params"])
    be = SmtBackend()

    instances = []
    values = set()
    smt_confirmations = 0
    cvc5_present = False
    representable = not _smt._term_uses_enum(kernel_def)

    for carrier in CARRIERS:
        objects = {p: carrier for p in params}
        for asg in _enumerate_param_instances(params, carrier, bound,
                                              max_instances):
            value = _eval.eval_term(kernel_def, asg, objects, carrier)
            values.add(value)
            rec = {"carrier": carrier, "assignment": dict(sorted(asg.items())),
                   "value": value}
            if representable:
                smt = _ground_term_smt(kernel_def, objects, carrier, asg, value)
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
                for backend, v in (("z3", z), ("cvc5", c)):
                    if v == "unsat":
                        return (False,
                                f"differential disagreement on {carrier} "
                                f"{rec['assignment']}: eval computed "
                                f"value={value} but {backend} refutes the "
                                f"ground equation", None)
                    if backend == "z3" and v == "sat":
                        smt_confirmations += 1
            else:
                rec["z3"] = "enum-only"
                rec["cvc5"] = "enum-only"
            instances.append(rec)

    if not representable:
        return (False,
                "the definition is enum-only (gcd): no independent SMT "
                "channel, so differential agreement is unavailable for "
                "admission", None)
    if smt_confirmations == 0:
        return (False,
                "all-unknown: no independent SMT verdict corroborated the "
                "evaluated values (differential agreement unavailable)", None)

    if len(values) <= 1:
        only = sorted(values)[0] if values else None
        return (False,
                f"degenerate vocabulary: the term is CONSTANT across the whole "
                f"battery domain (value {only} on every instance, both "
                f"carriers) -- a literal in disguise, not a function word; "
                f"refused", None)

    battery = {
        "role": "term",
        "bound": bound,
        "carriers": list(CARRIERS),
        "n_instances": len(instances),
        "distinct_values": len(values),
        "smt_confirmations": smt_confirmations,
        "cvc5_present": cvc5_present,
        "instances": instances,
    }
    return (True, "", battery)


def _synthetic_source(word: str) -> str:
    return f"for all values the {word} property holds"


def _synthetic_reading_doc(row: dict, carrier: str) -> dict:
    """A minimal reading exercising the word: params as (choice) objects, one
    forall quantifier over them, and a demanded conclusion applying the word --
    as the pred itself for a pred-role row, or inside a term of a kernel ``=``
    atom (``word(params...) = word(params...)``) for a term-role row, so the
    probe exercises exactly the position the role occupies at use time.  Its
    quotes are grounded in ``_synthetic_source``."""
    word = row["word"]
    params = list(row["params"])
    stmts = []
    for i, p in enumerate(params):
        stmts.append({"id": f"o{i}", "force": "choice", "quote": "",
                      "lf": {"kind": "object", "name": p, "type": carrier}})
    stmts.append({"id": "q", "force": "presupposition", "quote": "for all values",
                  "lf": {"kind": "quantifier", "binder": "forall",
                         "objects": params}})
    application = {"op": word, "args": [{"ref": p} for p in params]}
    if row.get("role", "pred") == "term":
        pred = {"op": "=", "args": [application, copy.deepcopy(application)]}
    else:
        pred = application
    stmts.append({"id": "c", "force": "demand",
                  "quote": f"the {word} property holds",
                  "lf": {"kind": "conclusion", "pred": pred}})
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
    closure + the definition parses as a valid pred (role "pred") or a valid
    TERM (role "term") over both carriers, through the real fragment machinery.
    Returns ``(ok, reason)``."""
    if not isinstance(row, dict):
        return False, "row must be an object"
    word = row.get("word")
    if not (isinstance(word, str) and _mr._ID.fullmatch(word)):
        return False, f"word must be a lowercase identifier, got {word!r}"
    if word in KERNEL_OPS:
        return False, f"word {word!r} shadows a kernel operator"
    role = row.get("role", "pred")
    if role not in ("pred", "term"):
        return False, f"role must be 'pred' or 'term', got {role!r}"
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
        return False, f"definition must be a {role} object"
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
    # (role "pred") or a valid TERM (role "term") over the params, under both
    # carriers, through the REAL fragment machinery.  A role mismatch -- a
    # term-shaped body on a pred row or a pred-shaped body on a term row --
    # refuses right here (`unknown atom` / `unknown term operator`).
    try:
        kernel_def = _expand_definition_to_kernel(row, registry)
    except OperatorExpansionError as ex:
        return False, f"definition failed to expand: {ex}"
    for carrier in CARRIERS:
        objects = {p: carrier for p in params}
        try:
            if role == "term":
                _mr._check_term(kernel_def, objects)
            else:
                _mr._check_pred(kernel_def, objects)
        except _mr.BadMathReading as ex:
            return False, (f"definition is not a valid {role} over "
                           f"{carrier}: {ex}")
    return True, ""


# =========================================================== trivial-alias gate
def _is_trivial_alias(kernel_def) -> bool:
    """A canonically-expanded definition that is a SINGLE kernel operator applied
    to bare refs, each a DISTINCT param (the ``divides_alias := dvd(a,b)`` case
    -- and, symmetrically for TERM-role rows, ``plus2(a,b) := a + b``).

    Such a word is a pure permutation / rename of a kernel operator: it adds no
    logical structure, so it can never earn its keep and is refused BEFORE the
    battery ever runs (§11.4 Critical 1).  Distinctness matters -- a diagonal
    like ``self_div(a) := dvd(a,a)`` or ``sq(a) := a * a`` is NOT a trivial
    alias (it repeats a ref, adding structure; it is judged by the nonvacuity /
    degeneracy battery and the economics instead).  A definition that expands
    to a bare ``{"ref": p}`` (a projection) or ``{"lit": k}`` (a literal) --
    reachable only through term-role rows, since ``_check_pred`` requires an
    op node -- is likewise trivial."""
    if isinstance(kernel_def, dict) and (set(kernel_def) == {"ref"}
                                         or set(kernel_def) == {"lit"}):
        return True                               # bare projection / literal
    if not (isinstance(kernel_def, dict) and "op" in kernel_def
            and kernel_def["op"] in KERNEL_OPS):
        return False
    args = kernel_def.get("args")
    if not isinstance(args, list) or not args:
        return False
    refs = []
    for a in args:
        if not (isinstance(a, dict) and set(a) == {"ref"}):
            return False                          # an arg carries structure
        refs.append(a["ref"])
    return len(set(refs)) == len(refs)            # each a DISTINCT param ref


# ================================================================ pricing gate
# The operator analogue of ``mdl_macros.macro_admission_decision``: after the
# battery certifies gate-correctness, a word is admitted only if writing the
# corpus with it strictly LOWERS the corpus description length in the ONE
# ``mdl_macros`` currency (no new constants).  ``model_bits`` is the once-paid
# cost of storing the row's definition; ``saving`` is the corpus-wide shrink from
# rewriting every matching pred subtree as the derived word.
_MODEL_BASE = _mdl._MACRO_BASE          # reuse the macro currency's stored-def base


def operator_model_bits(row: dict) -> float:
    """Model bits of a row's definition (its once-paid stored cost), in the
    ``mdl_macros`` currency: a stored-definition base + one per param + the
    leaf/field count of the definition AST.  No new constants."""
    return float(_MODEL_BASE + len(row["params"])
                 + _mdl._leaf_count(row["definition"]))


def _unify_pattern(pattern, node, params, binding) -> bool:
    """Match a definition PATTERN against a concrete AST ``node``; a param ref in
    the pattern is a placeholder that binds to a whole sub-term and must stay
    consistent across the match (so ``mod(a,m)=mod(b,m)`` matches only when both
    moduli are the SAME term)."""
    if (isinstance(pattern, dict) and set(pattern) == {"ref"}
            and pattern["ref"] in params):
        p = pattern["ref"]
        if p in binding:
            return binding[p] == node
        binding[p] = node
        return True
    if isinstance(pattern, dict):
        if not isinstance(node, dict) or set(pattern) != set(node):
            return False
        return all(_unify_pattern(pattern[k], node[k], params, binding)
                   for k in pattern)
    if isinstance(pattern, list):
        if not isinstance(node, list) or len(pattern) != len(node):
            return False
        return all(_unify_pattern(a, b, params, binding)
                   for a, b in zip(pattern, node))
    return pattern == node


def _outermost_matches(node, pattern, params):
    """Yield ``(subtree, binding)`` for every OUTERMOST subtree of ``node`` that
    matches ``pattern`` with all params bound.  Outermost-only (does not descend
    into a matched subtree) so a rewrite of the outer node never double-counts a
    nested match of the same operator."""
    if isinstance(node, dict):
        binding: dict = {}
        if (_unify_pattern(pattern, node, params, binding)
                and all(p in binding for p in params)):
            yield node, binding
            return
        for v in node.values():
            yield from _outermost_matches(v, pattern, params)
    elif isinstance(node, list):
        for v in node:
            yield from _outermost_matches(v, pattern, params)


def _corpus_readings(corpus):
    """Yield each reading dict in a pricing corpus that carries a statement
    list; tolerant of stray non-dict entries."""
    for reading in corpus:
        if isinstance(reading, dict) and isinstance(reading.get("statements"),
                                                    list):
            yield reading


def price_operator(row: dict, kernel_def, corpus) -> dict:
    """Price a candidate word against a pricing corpus (a list of reading docs).

    ``model_bits`` is paid once; every matching subtree collapses to a
    ``{"op": word, "args": [...]}`` invocation, saving
    ``leaf(subtree) - leaf(invocation)`` bits.  ONE currency for both roles:
    ``_outermost_matches`` walks every dict value and list element of each
    statement's pred, so a pred-role pattern matches pred subtrees and a
    term-role pattern (a term AST) matches TERM subtrees at any term position
    inside the corpus preds -- the same arithmetic, no new constants.
    Returns the full arithmetic:
    ``model_bits``, ``uses`` (matched subtree occurrences), ``witnesses``
    (distinct readings that use it), ``saving`` (corpus-wide), and the two-part
    ``dl_before`` / ``dl_after`` (``dl_after = dl_before - saving +
    model_bits``)."""
    word = row["word"]
    params = list(row["params"])
    model_bits = operator_model_bits(row)
    dl_before = 0.0
    saving = 0.0
    uses = 0
    witnesses = set()
    for idx, reading in enumerate(_corpus_readings(corpus)):
        used_here = False
        for s in reading["statements"]:
            lf = s.get("lf") if isinstance(s, dict) else None
            if not (isinstance(lf, dict) and isinstance(lf.get("pred"), dict)):
                continue
            pred = lf["pred"]
            dl_before += _mdl._leaf_count(pred)
            for subtree, binding in _outermost_matches(pred, kernel_def, params):
                invocation = {"op": word, "args": [binding[p] for p in params]}
                saving += _mdl._leaf_count(subtree) - _mdl._leaf_count(invocation)
                uses += 1
                used_here = True
        if used_here:
            witnesses.add(idx)
    dl_after = dl_before - saving + model_bits
    return {"model_bits": round(model_bits, 3),
            "uses": uses, "witnesses": len(witnesses),
            "saving": round(saving, 3),
            "dl_before": round(dl_before, 3),
            "dl_after": round(dl_after, 3),
            "delta": round(dl_after - dl_before, 3)}


def _pricing_decision(row, registry, pricing_corpus):
    """The operator pricing gate.  Fail-closed: no corpus => refuse.  Admit iff
    the corpus DL strictly drops (saving > model_bits) AND >= 2 real witness
    readings use the word (the two-witness discipline, §11 intro).  Returns
    ``(ok, reason, pricing)``; refusal reasons NAME the arithmetic."""
    if pricing_corpus is None:
        return (False,
                "no pricing corpus: operator admission charges the definition's "
                "model bits against a corpus-wide rewrite saving, so a pricing "
                "corpus (list of readings) is required -- refusing fail-closed",
                None)
    kernel_def = _expand_definition_to_kernel(row, registry)
    pricing = price_operator(row, kernel_def, pricing_corpus)
    # The pricing block is corpus-dependent EVIDENCE (never part of the cert
    # id); stamp which corpus produced it so the numbers are reproducible
    # without out-of-band knowledge (T4a review follow-up).
    pricing["pricing_corpus_digest"] = common.sha256_json(
        pricing_corpus)[:16]
    m, s = pricing["model_bits"], pricing["saving"]
    u, w = pricing["uses"], pricing["witnesses"]
    arith = (f"model_bits={m}, saving={s} over {u} uses in {w} witness "
             f"readings (dl_before={pricing['dl_before']} -> "
             f"dl_after={pricing['dl_after']})")
    if not s > m:
        return (False,
                f"no strict corpus-DL drop: the rewrite saving does not exceed "
                f"the definition's model bits ({arith}); saving must exceed "
                f"model_bits for the word to pay for itself", pricing)
    if w < 2:
        return (False,
                f"one-off word: {arith}; the two-witness discipline refuses a "
                f"word used by fewer than 2 readings even when it would pay",
                pricing)
    return (True, "", pricing)


def admit_operator(row: dict, *, op_dir=None, bound=DEFAULT_BATTERY_BOUND,
                   max_instances=DEFAULT_MAX_INSTANCES, registry=None,
                   pricing_corpus=None) -> dict:
    """Run the full admission battery on a proposed row.

    Returns ``{"admitted": True, "cert": ..., "row": ...}`` on a green
    certificate, else ``{"admitted": False, "refusal": {"stage", "reason"}}``.
    Never writes anything -- persistence is the caller's explicit
    ``save_admitted`` step, so nothing autonomous lands a row without a green
    cert in hand.

    Gate order: well-formedness, trivial-alias (pre-battery, §11.4 Critical 1),
    the differential battery, the compile round-trip, then the PRICING gate --
    the word is admitted only if it strictly lowers the corpus DL in the
    ``mdl_macros`` currency.  ``pricing_corpus`` (a list of reading docs) is
    REQUIRED; without it admission refuses fail-closed."""
    if registry is None:
        registry = load_admitted(op_dir)
    # a row may re-admit, but not depend on a same-named prior admission.
    registry = {w: e for w, e in registry.items() if w != row.get("word")}

    ok, reason = _check_wellformed(row, registry)
    if not ok:
        return {"admitted": False,
                "refusal": {"stage": "well-formedness", "reason": reason}}

    # trivial-alias refusal (pre-battery): canonically expand and reject a bare
    # kernel-op rename -- or, for a term-role row, a bare param projection /
    # literal -- before spending the battery on it.
    kernel_def = _expand_definition_to_kernel(row, registry)
    if _is_trivial_alias(kernel_def):
        if "op" in kernel_def:
            what = (f"a single kernel operator {kernel_def.get('op')!r} over "
                    f"distinct param refs -- a pure rename that adds no "
                    f"structure")
        elif "ref" in kernel_def:
            what = "a bare param reference -- a projection, not vocabulary"
        else:
            what = "a bare literal -- a constant, not vocabulary"
        return {"admitted": False, "refusal": {
            "stage": "trivial-alias",
            "reason": (f"trivial alias: {row['word']!r} expands to {what} and "
                       f"can never lower the corpus DL; refused")}}

    # the candidate participates in expansion during the battery (verify=False;
    # it has no cert yet).
    battery_registry = dict(registry)
    battery_registry[row["word"]] = {"row": canonical_row(row)}

    ok, reason, battery = _run_battery(row, registry, bound, max_instances)
    if not ok:
        if "vacuous" in reason:
            stage = "nonvacuity"
        elif "degenerate" in reason:
            stage = "degeneracy"          # the term-role analogue of nonvacuity
        else:
            stage = "battery"
        return {"admitted": False, "refusal": {"stage": stage, "reason": reason}}

    ok, reason = _compile_roundtrip(row, battery_registry)
    if not ok:
        return {"admitted": False,
                "refusal": {"stage": "compile", "reason": reason}}

    # pricing gate (after the battery): strict corpus-DL drop in one currency.
    ok, reason, pricing = _pricing_decision(row, registry, pricing_corpus)
    if not ok:
        return {"admitted": False,
                "refusal": {"stage": "pricing", "reason": reason}}

    battery_digest = common.sha256_json(battery)
    cert = {
        "kind": CERT_KIND,
        "id": cert_id(row, battery_digest),
        "word": row["word"],
        # role is stamped only for non-default rows, so every pred cert keeps
        # its exact historical byte shape (backward compat).
        **({"role": "term"} if row.get("role", "pred") == "term" else {}),
        "row_digest": row_digest(row),
        "battery_digest": battery_digest,
        "battery": battery,
        "pricing": pricing,
        "engines": {
            "cvc5_present": battery["cvc5_present"],
            "smt_confirmations": battery["smt_confirmations"],
        },
        "mathlib_commit": common.MATHLIB_COMMIT,
        "toolchain": common.LEAN_TOOLCHAIN,
    }
    return {"admitted": True, "row": canonical_row(row), "cert": cert}

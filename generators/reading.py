"""A READING: the semantic analysis of a natural-language request.

This is the linguistically principled artifact the LLM authors on the semantic
path -- it never writes the spec.  The theory it operationalizes:

  * Discourse referents (DRT, Kamp/Heim): the entities a request talks about --
    quantities ("seats left") and actions ("sell") -- are introduced explicitly
    and everything else refers to them.  Anaphora is resolved by construction:
    every later statement names its referents.
  * Speech-act force (Austin/Searle): each statement is tagged with what the
    text is DOING --
      - "demand":         the directive's propositional content.  Must carry an
                          EXACT QUOTE of the request span that demands it; the
                          gate checks the quote occurs in the request verbatim
                          (groundedness is mechanical, not judgment).
      - "presupposition": licensed but unstated.  "not oversell" presupposes
                          selling, and selling presupposes stock that
                          decrements.  Quotes its trigger span.
      - "choice":         the pragmatic residue -- design freedom the text
                          leaves open (lifecycle states, extra fields).  MUST
                          have an empty quote: a choice is by definition not
                          grounded in the text, and pretending otherwise is the
                          failure mode this format exists to prevent.
  * Logical forms (Montague-style): each statement's content is a term of a
    small deontic-temporal fragment that compiles compositionally:
      quantity    q with init range              (discourse referent)
      action      a, optional integer argument   (discourse referent)
      effect      a changes q by arg/const       (verb lexical semantics)
      bound       arg-of-a  CMP  const|quantity  (comparatives/quantifiers;
                                                  const -> per-call constraint,
                                                  quantity -> guard)
      always      G(pred over quantities)        (deontic prohibition "never")
      order       first a1, only then a2         (temporal precedence)
      lifecycle / transition / input             (structural choices)

The compiler (reading_compile.py) turns a Reading into a service meta-spec
deterministically, recording per-element provenance (which statements produced
it), and every demand generates its own machine-checked obligation downstream.
"""
from __future__ import annotations

import dataclasses
import json
import re

CMP = {"<", "<=", ">", ">=", "==", "!="}
_ID = re.compile(r"[a-z][a-z0-9_]*")
FORCES = ("demand", "presupposition", "choice")
SCALARS = ("string", "integer", "number", "boolean")
# The obligation kinds: what the text DIRECTS as a duty (a demand or a
# presupposition), never a mere design choice.  The state invariants/precedence
# obligations (always/order/bound) and the P1 LTLf temporal obligations
# (eventually/until/before/within) share this force discipline and the gate rule
# below ("at least one demanded obligation of ANY kind").
OBLIGATION_KINDS = ("always", "order", "bound",
                    "eventually", "until", "before", "within")


# --- the ONE source of truth for the LF fragment -----------------------------
# LF_KINDS maps every accepted logical-form kind to (signature_line, force_rule):
#   signature_line -- a one-line, human-readable field signature, rendered
#                     verbatim into the Reading prompt's grammar block by
#                     buildloop.service_loop (so prompt grammar is generated,
#                     never hand-maintained);
#   force_rule     -- the speech-act force(s) the kind may carry, as enforced by
#                     parse_reading below: structural kinds are choices,
#                     obligations are never choices, referents take any force.
# The prompt's grammar block AND this validator's accepted-kind set are BOTH
# derived from LF_KINDS -- the two can never drift.  (P0.5.8 enumerates EXACTLY
# the kinds the gate accepts today; no new temporal kinds -- that is Phase 1.)
LF_KINDS = {
    "quantity": (
        '{"kind":"quantity","name":q,"min":<int>,"max":<int>} '
        '-- an integer state quantity with its initial range.',
        "any force"),
    "action": (
        '{"kind":"action","name":a} | {"kind":"action","name":a,"arg":x} '
        '-- an operation; arg is its one integer argument, if any.',
        "any force"),
    "effect": (
        '{"kind":"effect","action":a,"quantity":q,"op":"dec|inc|set",'
        '"amount":{"arg":x}|{"const":<int>}} '
        '-- the verb\'s effect on state (selling DECREASES stock BY amount).',
        "any force"),
    "bound": (
        '{"kind":"bound","action":a,"left":x,"cmp":"<=|<|>=|>|==|!=",'
        '"right":<int>|q} -- a comparative on the action\'s argument; '
        'right=<int> is a per-call limit, right=q compares live state (guard).',
        "demand or presupposition; never choice"),
    "always": (
        '{"kind":"always","pred":<pred over quantities>} -- a global '
        'prohibition/invariant G(pred) in every reachable state; <pred> is '
        '{"op":cmp,"left":q|<int>,"right":q|<int>} or {"op":"and","preds":[...]}.',
        "demand or presupposition; never choice"),
    "order": (
        '{"kind":"order","first":a1,"then":a2} '
        '-- a2 may only ever happen after a1 has happened.',
        "demand or presupposition; never choice"),
    "eventually": (
        '{"kind":"eventually","action":a} -- LTLf F(a): action a MUST '
        'eventually occur before the session ends (a liveness obligation; '
        'the session-closing action is refused while a is still owed).',
        "demand or presupposition; never choice"),
    "until": (
        '{"kind":"until","hold_pred":a1,"until_action":a2} -- LTLf a1 U a2: '
        'a1 keeps occurring until a2 finally occurs, and a2 must occur.',
        "demand or presupposition; never choice"),
    "before": (
        '{"kind":"before","first":a1,"deadline":a2} -- a2 may not occur '
        'before a1 has occurred (temporal precedence over two actions).',
        "demand or presupposition; never choice"),
    "within": (
        '{"kind":"within","action":a,"steps":<int>} -- action a must occur '
        'within the first <int> steps of the session (<int> >= 1).',
        "demand or presupposition; never choice"),
    "lifecycle": (
        '{"kind":"lifecycle","states":[...],"initial":s} '
        '-- the control-state set and its start (exactly one lifecycle).',
        "choice only"),
    "transition": (
        '{"kind":"transition","action":a,"from":s,"to":s2} -- exactly one per '
        'action; s2 may equal s for repeatable actions.',
        "choice only"),
    "input": (
        '{"kind":"input","action":a,'
        '"fields":{name:"string|integer|number|boolean"}} '
        '-- optional extra fields for the action\'s schema.',
        "choice only"),
}

# Per-kind allowed field-key sets (structural validation).  Keyed by EXACTLY
# set(LF_KINDS); the assert makes any divergence a hard import-time error, so
# the accepted-kind set below stays single-sourced from LF_KINDS.
_LF_FIELDS = {
    "quantity": {"kind", "name", "min", "max"},
    "action": {"kind", "name", "arg"},
    "effect": {"kind", "action", "quantity", "op", "amount"},
    "bound": {"kind", "action", "left", "cmp", "right"},
    "always": {"kind", "pred"},
    "order": {"kind", "first", "then"},
    "eventually": {"kind", "action"},
    "until": {"kind", "hold_pred", "until_action"},
    "before": {"kind", "first", "deadline"},
    "within": {"kind", "action", "steps"},
    "lifecycle": {"kind", "states", "initial"},
    "transition": {"kind", "action", "from", "to"},
    "input": {"kind", "action", "fields"},
}
assert set(_LF_FIELDS) == set(LF_KINDS), \
    "LF_KINDS and _LF_FIELDS disagree on the accepted LF kinds"


class BadReading(Exception):
    pass


# --- macro expansion (P5.2) --------------------------------------------------
# A macro is an ABBREVIATION, never a new logical-form kind: LF_KINDS stays the
# single source of truth for the fragment.  A macro invocation is an ordinary
# statement whose lf is {"kind":"macro","name":<macro>,"args":{param:value}}; a
# macro definition is {"name","params":[...],"body":[<lf template>,...]} where a
# template may carry "$param" placeholders.  Expansion happens INSIDE
# parse_reading, BEFORE the groundedness gate, and every expanded statement
# INHERITS the invocation's force and quote -- otherwise a macro-expanded demand
# would carry no quote and be rejected by the groundedness gate.  Expansion is
# purely deterministic and LLM-free (the macro table is a checker input, like the
# reference codec).
def _macro_subst(node, args):
    """Substitute a macro's arguments into a body template: a "$param" string
    becomes args[param]; everything else is copied structurally."""
    if isinstance(node, dict):
        return {k: _macro_subst(v, args) for k, v in node.items()}
    if isinstance(node, list):
        return [_macro_subst(v, args) for v in node]
    if isinstance(node, str) and node.startswith("$"):
        p = node[1:]
        if p not in args:
            raise BadReading(f"macro placeholder ${p} has no argument")
        return args[p]
    return node


def _expand_one(stmt, macro_table):
    """Expand a single macro-invocation statement to its concrete statements,
    each inheriting the invocation's force+quote (and a derived unique id)."""
    lf = stmt["lf"]
    if set(lf) - {"kind", "name", "args"}:
        raise BadReading(f"{stmt.get('id')}: a macro invocation lf takes only "
                         f"name/args, got {sorted(set(lf) - {'kind','name','args'})}")
    name = lf.get("name")
    macro = macro_table.get(name)
    if macro is None:
        raise BadReading(f"{stmt.get('id')}: unknown macro {name!r}")
    args = lf.get("args", {}) or {}
    if not isinstance(args, dict):
        raise BadReading(f"{stmt.get('id')}: macro args must be an object")
    missing = [p for p in macro.get("params", []) if p not in args]
    if missing:
        raise BadReading(f"{stmt.get('id')}: macro {name!r} missing args {missing}")
    sid, force, quote = stmt.get("id"), stmt.get("force"), stmt.get("quote", "")
    out = []
    for i, template in enumerate(macro["body"]):
        out.append({"id": f"{sid}~{name}#{i}", "force": force, "quote": quote,
                    "lf": _macro_subst(template, args)})
    return out


def _expand_macros(stmts, macro_table):
    """Replace every macro-invocation statement in `stmts` (in place, in order)
    with its expansion; leave every concrete statement untouched.  Runs before
    any gate, so the rest of parse_reading only ever sees concrete LF kinds."""
    out = []
    for s in stmts:
        lf = s.get("lf") if isinstance(s, dict) else None
        if isinstance(lf, dict) and lf.get("kind") == "macro":
            out.extend(_expand_one(s, macro_table))
        else:
            out.append(s)
    return out


@dataclasses.dataclass
class Reading:
    service: str
    statements: list        # list[dict], validated
    source: str

    def by_kind(self, kind):
        return [s for s in self.statements if s["lf"]["kind"] == kind]

    def demands(self):
        return [s for s in self.statements if s["force"] == "demand"]


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _check_pred(pred, quantities):
    if not isinstance(pred, dict) or "op" not in pred:
        raise BadReading(f"pred must have op: {pred!r}")
    op = pred["op"]
    if op == "and":
        preds = pred.get("preds")
        if not isinstance(preds, list) or not preds:
            raise BadReading("and needs non-empty preds")
        for p in preds:
            _check_pred(p, quantities)
        return
    if op == "implies":
        _check_pred(pred.get("if"), quantities)
        _check_pred(pred.get("then"), quantities)
        return
    if op not in CMP:
        raise BadReading(f"unsupported op {op!r}")
    for side in ("left", "right"):
        o = pred.get(side)
        if isinstance(o, bool) or not (
                (isinstance(o, int)) or (isinstance(o, str) and o in quantities)):
            raise BadReading(f"pred operand must be int or a declared "
                             f"quantity: {o!r}")


def parse_reading(text: str, request: str, macro_table: dict = None) -> Reading:
    """Validate a Reading against its request.  Groundedness is checked HERE,
    mechanically: every demand (and presupposition) must quote a span that
    literally occurs in the request; every choice must quote nothing.

    P5.2: if `macro_table` is given, macro invocations are expanded to their
    concrete statements FIRST (before any gate), each inheriting the invocation's
    force+quote.  With no macro_table (the LLM path, and every pre-P5.2 caller)
    nothing is expanded and the behaviour is byte-identical."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise BadReading(f"not valid JSON: {e}")
    if not isinstance(doc, dict) or set(doc) - {"service", "statements"}:
        raise BadReading("reading must be {service, statements}")
    service = doc.get("service", "service")
    if not _ID.fullmatch(service):
        raise BadReading("service must be a lowercase identifier")
    stmts = doc.get("statements")
    if not isinstance(stmts, list) or not (1 <= len(stmts) <= 60):
        raise BadReading("statements must be a list of 1..60")
    if macro_table:
        stmts = _expand_macros(stmts, macro_table)
        if not (1 <= len(stmts) <= 60):
            raise BadReading("expanded statements must number 1..60")
    req_norm = _norm(request)

    seen_ids = set()
    quantities, actions, args = {}, {}, {}
    lifecycle = None
    transitions = {}
    for s in stmts:
        if not isinstance(s, dict) or set(s) - {"id", "force", "quote", "lf"}:
            raise BadReading(f"statement keys must be id/force/quote/lf: "
                             f"{str(s)[:120]}")
        sid, force, quote, lf = (s.get("id"), s.get("force"),
                                 s.get("quote", ""), s.get("lf"))
        # Accept an int id and coerce to str (LLMs routinely emit "id": 1); the
        # only requirement is a non-empty, UNIQUE identifier.  The message names
        # the fix explicitly so a refinement round can self-correct.
        if isinstance(sid, int) and not isinstance(sid, bool):
            sid = str(sid)
        if not isinstance(sid, str) or not sid:
            raise BadReading(f"statement id must be a non-empty string (or int); "
                             f"got {s.get('id')!r}")
        if sid in seen_ids:
            raise BadReading(f"duplicate statement id {sid!r}; each statement "
                             f"needs a UNIQUE id")
        seen_ids.add(sid)
        s["id"] = sid  # normalize so downstream (compile, provenance) sees a str
        if force not in FORCES:
            raise BadReading(f"{sid}: force must be one of {FORCES}")
        if not isinstance(quote, str):
            raise BadReading(f"{sid}: quote must be a string")
        # --- groundedness: the speech-act trichotomy is enforced here ------
        if force in ("demand", "presupposition"):
            if not quote.strip():
                raise BadReading(
                    f"{sid}: a {force} must quote the request span that "
                    f"carries it")
            if _norm(quote) not in req_norm:
                raise BadReading(
                    f"{sid}: quote {quote!r} does not occur in the request "
                    f"-- a {force} may not be fabricated")
        else:  # choice
            if quote.strip():
                raise BadReading(
                    f"{sid}: a choice is design freedom, not something the "
                    f"text says -- its quote must be empty")
        if not isinstance(lf, dict) or "kind" not in lf:
            raise BadReading(f"{sid}: lf must be an object with kind")
        kind = lf["kind"]
        # accepted-kind set is derived from LF_KINDS (the single source of
        # truth); _LF_FIELDS carries the per-kind allowed keys.
        if kind not in LF_KINDS:
            raise BadReading(f"{sid}: unknown lf kind {kind!r}")
        if set(lf) - _LF_FIELDS[kind]:
            raise BadReading(f"{sid}: unexpected lf keys "
                             f"{sorted(set(lf) - _LF_FIELDS[kind])}")
        # first pass: declare referents
        if kind == "quantity":
            n, lo, hi = lf.get("name"), lf.get("min"), lf.get("max")
            if not (isinstance(n, str) and _ID.fullmatch(n)) or n in quantities:
                raise BadReading(f"{sid}: bad/duplicate quantity name {n!r}")
            if not (isinstance(lo, int) and isinstance(hi, int) and lo <= hi
                    and not isinstance(lo, bool) and not isinstance(hi, bool)):
                raise BadReading(f"{sid}: quantity needs int min <= max")
            quantities[n] = (lo, hi)
        elif kind == "action":
            n, arg = lf.get("name"), lf.get("arg")
            if not (isinstance(n, str) and _ID.fullmatch(n)) or n in actions:
                raise BadReading(f"{sid}: bad/duplicate action name {n!r}")
            if arg is not None and not (isinstance(arg, str)
                                        and _ID.fullmatch(arg)):
                raise BadReading(f"{sid}: action arg must be an identifier")
            actions[n] = s
            args[n] = arg
        elif kind == "lifecycle":
            if lifecycle is not None:
                raise BadReading(f"{sid}: more than one lifecycle")
            states, init = lf.get("states"), lf.get("initial")
            if not (isinstance(states, list) and len(states) >= 2
                    and all(isinstance(x, str) and _ID.fullmatch(x)
                            for x in states)
                    and len(set(states)) == len(states)):
                raise BadReading(f"{sid}: lifecycle needs >=2 distinct states")
            if init not in states:
                raise BadReading(f"{sid}: initial must be a lifecycle state")
            lifecycle = lf

    if lifecycle is None:
        raise BadReading("no lifecycle statement (a choice, typically)")
    if not actions:
        raise BadReading("no action referents declared")

    # second pass: referential integrity
    states = set(lifecycle["states"])
    for s in stmts:
        sid, lf = s["id"], s["lf"]
        kind = lf["kind"]
        if kind == "effect":
            a, q, op, amt = (lf.get("action"), lf.get("quantity"),
                             lf.get("op"), lf.get("amount"))
            if a not in actions:
                raise BadReading(f"{sid}: effect on undeclared action {a!r}")
            if q not in quantities:
                raise BadReading(f"{sid}: effect on undeclared quantity {q!r}")
            if op not in ("dec", "inc", "set"):
                raise BadReading(f"{sid}: effect op must be dec/inc/set")
            if not isinstance(amt, dict) or set(amt) not in ({"arg"}, {"const"}):
                raise BadReading(f"{sid}: amount must be {{arg}} or {{const}}")
            if "arg" in amt and amt["arg"] != args.get(a):
                raise BadReading(
                    f"{sid}: amount arg {amt.get('arg')!r} is not action "
                    f"{a!r}'s argument")
            if "const" in amt and (not isinstance(amt["const"], int)
                                   or isinstance(amt["const"], bool)):
                raise BadReading(f"{sid}: amount const must be an int")
        elif kind == "bound":
            a, left, cmp_, right = (lf.get("action"), lf.get("left"),
                                    lf.get("cmp"), lf.get("right"))
            if a not in actions:
                raise BadReading(f"{sid}: bound on undeclared action {a!r}")
            if left != args.get(a) or left is None:
                raise BadReading(
                    f"{sid}: bound left {left!r} must be action {a!r}'s "
                    f"argument")
            if cmp_ not in CMP:
                raise BadReading(f"{sid}: bad cmp {cmp_!r}")
            const = isinstance(right, int) and not isinstance(right, bool)
            if not (const or right in quantities):
                raise BadReading(
                    f"{sid}: bound right must be an int or a declared "
                    f"quantity: {right!r}")
        elif kind == "always":
            _check_pred(lf.get("pred"), quantities)
        elif kind == "order":
            f_, t_ = lf.get("first"), lf.get("then")
            if f_ not in actions or t_ not in actions or f_ == t_:
                raise BadReading(f"{sid}: order needs two distinct declared "
                                 f"actions")
        elif kind == "eventually":
            a = lf.get("action")
            if a not in actions:
                raise BadReading(f"{sid}: eventually names undeclared action "
                                 f"{a!r} (its argument must be a declared "
                                 f"action referent)")
        elif kind == "until":
            a1, a2 = lf.get("hold_pred"), lf.get("until_action")
            if a1 not in actions or a2 not in actions or a1 == a2:
                raise BadReading(f"{sid}: until needs two distinct declared "
                                 f"actions (hold_pred, until_action)")
        elif kind == "before":
            a1, a2 = lf.get("first"), lf.get("deadline")
            if a1 not in actions or a2 not in actions or a1 == a2:
                raise BadReading(f"{sid}: before needs two distinct declared "
                                 f"actions (first, deadline)")
        elif kind == "within":
            a, steps = lf.get("action"), lf.get("steps")
            if a not in actions:
                raise BadReading(f"{sid}: within names undeclared action {a!r}")
            if not (isinstance(steps, int) and not isinstance(steps, bool)
                    and steps >= 1):
                raise BadReading(f"{sid}: within needs integer steps >= 1")
        elif kind == "transition":
            a, frm, to = lf.get("action"), lf.get("from"), lf.get("to")
            if a not in actions:
                raise BadReading(f"{sid}: transition for undeclared action "
                                 f"{a!r}")
            if frm not in states or to not in states:
                raise BadReading(f"{sid}: transition states must be lifecycle "
                                 f"states")
            if a in transitions:
                raise BadReading(f"{sid}: action {a!r} already has a "
                                 f"transition (one per action)")
            transitions[a] = lf
        elif kind == "input":
            a, fields = lf.get("action"), lf.get("fields")
            if a not in actions:
                raise BadReading(f"{sid}: input for undeclared action {a!r}")
            if not isinstance(fields, dict) or not fields:
                raise BadReading(f"{sid}: input needs a fields object")
            for fn, ft in fields.items():
                if not (isinstance(fn, str) and _ID.fullmatch(fn)
                        and ft in SCALARS):
                    raise BadReading(f"{sid}: bad input field {fn!r}: {ft!r}")
                if fn == args.get(a):
                    raise BadReading(f"{sid}: field {fn!r} collides with the "
                                     f"action argument")
        # structural kinds must be choices; obligations must not be choices
        if kind in ("lifecycle", "transition", "input") \
                and s["force"] != "choice":
            raise BadReading(
                f"{sid}: {kind} is structural design freedom -- force must "
                f"be 'choice' (if the text demands an ordering, state an "
                f"'order' demand instead)")
        if kind in OBLIGATION_KINDS and s["force"] == "choice":
            raise BadReading(
                f"{sid}: an obligation ({kind}) cannot be a mere choice -- "
                f"tag it demand (quoted) or presupposition")

    for a in actions:
        if a not in transitions:
            raise BadReading(f"action {a!r} has no transition (add a choice)")
    if not any(s["lf"]["kind"] in OBLIGATION_KINDS and s["force"] == "demand"
               for s in stmts):
        raise BadReading(
            "no demanded obligation -- the request's central directive must "
            "appear as a quoted demand of an obligation kind (a state "
            "invariant/precedence 'always'/'order'/'bound', or a temporal "
            "'eventually'/'until'/'before'/'within')")
    return Reading(service=service, statements=stmts, source=text)

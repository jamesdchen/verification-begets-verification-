"""F1.3 -- the math Reading prompt, single-sourced from the F1 fragment.

The mathematical analogue of the Reading-prompt scaffold in
`buildloop/service_loop.py` (the P0.5.8 single-source discipline).  Two things
are GENERATED here, never hand-maintained, so they can never drift from the
things they describe:

  * the per-kind GRAMMAR BLOCK is rendered from `math_reading.MATH_LF_KINDS`
    (each value is `(signature_line, force_rule)`) and the frozen operator
    lexicon `math_reading.MATH_OPERATORS` -- exactly as
    `service_loop._reading_grammar_block` renders from `reading.LF_KINDS`;

  * the live DEFINITION TABLE is rendered from the admitted `macro_table`
    (`{name: {name, params, body}}`), one `name(params...) -- <gloss>` row per
    admitted macro, sorted by name.  THIS is the E1 causal mechanism: on this
    tree the macro table reaches NO LLM prompt, so an admitted "definition"
    cannot change prompt bytes and therefore cannot change LLM cost -- an
    accounting fiction.  Rendering the table into the prompt is exactly the
    seam by which admitting a macro changes the prompt string (and so the token
    count the F5 benchmark measures).  A macro-free table renders a stable
    "(none)" block so a definition-less prompt is byte-stable.

No LLM call is made here; this module builds the PROMPT STRING only, and does so
deterministically (sorted iteration, no clocks/random), so the same inputs
always yield identical bytes.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import math_reading


_PREAMBLE = """You are the untrusted SEMANTIC ANALYST of a certified
formalization bootstrap.  You do NOT write Lean and you do NOT write proofs.
You author a MATH READING: a quoted, force-tagged semantic analysis of the
source sentence below, statement by statement.  A deterministic, LLM-free
compiler turns your Reading into a Lean statement; solvers then check every
obligation you attribute to the text.  Misattribute nothing: every demand and
presupposition you write is checked to occur VERBATIM in the source."""

# The envelope the LLM must return (F-A).  Mentions the keys `theorem` and
# `statements` literally so a prompt test can assert the shape is advertised.
_ENVELOPE_NOTE = """Return ONLY one JSON object (no prose, no fences):
  {"theorem": <lowercase id>,
   "statements": [{"id": <id>, "force": <force>, "quote": <string>,
                   "lf": <logical form>}, ...]}"""

# The speech-act trichotomy + quote-groundedness rules (mirrors the Reading
# prompt's FORCE block).  These are the gate `parse_math_reading` enforces
# mechanically, so the prompt states them exactly.
_RULES = """FORCE (the speech-act trichotomy -- the heart of the format):
  "demand"         the theorem's asserted content.  quote MUST be an exact
                   substring of the source (case/whitespace-insensitive).
                   Carried ONLY by a "conclusion" statement.
  "presupposition" a side condition the text takes for granted (n > 0, a
                   nonzero divisor, a nonempty domain) -- the implicit
                   hypotheses autoformalization silently drops.  quote the
                   trigger span, also verbatim.
  "choice"         formalization freedom (which carrier, what generality).
                   quote MUST be "" -- a choice is yours, not the text's.

Requirements: declare every object before referring to it; every quantifier and
pred may reference only declared objects; bind each lexicon word with an
"operator" statement at a carrier before using it in a pred; and the theorem's
asserted content MUST appear as at least one demanded "conclusion" quoted
verbatim from the source (trichotomy: exactly demand/presupposition/choice, and
quote-groundedness as above).  Keep the Reading MINIMAL -- only what the source
demands or presupposes, plus the fewest choices that make it compile."""

_PRED_AST_NOTE = (
    "PRED / TERM AST (F-G):\n"
    '  pred := {"op": <connective|atom>, "args": [pred|term, ...]}\n'
    '  term := {"ref": <declared object name>} | {"lit": <int>}\n'
    '        | {"op": <"+"|"*"|"-"|"%"|"^">, "args": [term, ...]}\n'
    '        | {"op": <"bigsum"|"bigprod">, "args": [{"var": <index>}, '
    '{"lit": lo}, {"lit": hi}, term]}\n'
    '        | {"op": "card", "args": [{"op": "setbuild", "args": '
    '[{"var": <index>}, {"lit": lo}, {"lit": hi}, pred]}]}\n'
    "  connectives: and, or, implies    atoms: =, !=, <=, <, plus the lexicon "
    "words above.\n"
    "  Args keep written order (the compiler never reorders); ^ takes "
    "[base, literal-exponent].\n"
    "  bigsum/bigprod fold the body term over index = lo..hi (inclusive; "
    "lo > hi is 0/1): bounds are\n"
    "  NON-NEGATIVE LITERALS, the index is Nat, no nesting, no shadowing a "
    "declared object.\n"
    "  card counts the index values lo..hi where the setbuild filter pred "
    "holds (same bound rules;\n"
    "  the filter may use declared objects); a setbuild appears ONLY inside "
    "card."
)


def _render_lexicon() -> str:
    """The frozen operator lexicon, GENERATED from MATH_OPERATORS so every
    available word (and its carriers) is advertised exactly once and can never
    drift from the table the gate resolves against."""
    lines = ["LEXICON (the frozen MATH_OPERATORS words -- bind each with an "
             "'operator' statement at a carrier;",
             " a (word, carrier) pair outside this table is refused as a "
             "fragment-miss):"]
    for word in sorted(math_reading.MATH_OPERATORS):
        info = math_reading.MATH_OPERATORS[word]
        carriers = ", ".join(sorted(info["lean"]))
        lines.append(f"  {word}  (arity {info['arity']}, {info['role']}; "
                     f"carriers: {carriers})")
    return "\n".join(lines)


def render_grammar_block() -> str:
    """The per-kind LF grammar, GENERATED from MATH_LF_KINDS (each entry's
    signature line + its force rule), followed by the operator lexicon and a
    note on the pred/term AST.  Mirrors service_loop._reading_grammar_block: one
    single source of truth for both the prompt grammar and the validator's
    accepted-kind set, so the two can never drift."""
    out = ["LOGICAL FORMS (each entry is the field signature followed by the "
           "speech-act force it may carry):"]
    for _kind, (sig, force) in math_reading.MATH_LF_KINDS.items():
        out.append(f"  {sig}")
        out.append(f"      (force: {force})")
    out.append("")
    out.append(_render_lexicon())
    out.append("")
    out.append(_PRED_AST_NOTE)
    return "\n".join(out)


# --------------------------------------------------------------- macro gloss
def _lf_of(template):
    """A macro body element is a bare LF template (per mdl_macros: body items
    are the lf dicts directly); tolerate a full {id,force,quote,lf} statement
    too."""
    if isinstance(template, dict) and "lf" in template:
        return template["lf"]
    return template


def _collect_ops(node, acc):
    """Depth-first, written-order collection of every `op` word in a pred/term
    tree (deterministic: dicts are visited op-then-args, lists in order)."""
    if isinstance(node, dict):
        if "op" in node:
            acc.append(str(node["op"]))
        for a in node.get("args", []) or []:
            _collect_ops(a, acc)
    return acc


def _body_stmt_descr(template) -> str:
    """A short, deterministic descriptor of ONE macro body statement, derived
    purely from its logical form (its kind, plus the salient content of that
    kind).  For hypothesis/conclusion this is the sequence of operator/atom
    words in the pred; for the other kinds the defining field."""
    lf = _lf_of(template)
    if not isinstance(lf, dict):
        return "?"
    kind = lf.get("kind", "?")
    if kind in ("hypothesis", "conclusion"):
        ops = _collect_ops(lf.get("pred"), [])
        return f"{kind}({', '.join(ops)})" if ops else kind
    if kind == "operator":
        return f"operator {lf.get('word')}@{lf.get('carrier')}"
    if kind == "object":
        return f"object:{lf.get('type')}"
    if kind == "quantifier":
        objs = ",".join(lf.get("objects", []) or [])
        return f"{lf.get('binder')} {objs}".strip()
    if kind == "ambient":
        return f"ambient:{lf.get('carrier')}"
    return str(kind)


def _macro_gloss(macro: dict) -> str:
    """A deterministic one-line gloss for an admitted macro, derived from its
    body's LF-kind sequence (with the salient content of each statement).  An
    empty body glosses to "(empty body)" so every row is non-empty."""
    body = macro.get("body") or []
    parts = [_body_stmt_descr(t) for t in body]
    return "; ".join(parts) if parts else "(empty body)"


def render_definition_table(macro_table: dict = None) -> str:
    """The live DEFINITION TABLE (the E1 mechanism): one
    `name(params...) -- <gloss>` row per admitted macro, sorted by name so the
    output is order-independent.  An empty table renders a stable "(none)"
    block so a macro-free prompt is byte-stable -- and admitting a macro
    therefore CHANGES these bytes, which is precisely how admitted vocabulary
    changes the prompt (and the LLM cost the F5 benchmark measures)."""
    macro_table = macro_table or {}
    header = ("DEFINITIONS (the live vocabulary admitted so far; each name "
              "abbreviates the body sketched after the dash and MAY be invoked "
              "by name):")
    if not macro_table:
        return header + "\n  (none)"
    lines = [header]
    for name in sorted(macro_table):
        macro = macro_table[name]
        params = ", ".join(macro.get("params", []) or [])
        lines.append(f"  {name}({params}) -- {_macro_gloss(macro)}")
    return "\n".join(lines)


# --------------------------------------------------------- operator vocabulary
def _ast_gloss(node) -> str:
    """A deterministic, compact rendering of a pred/term AST as text: a `{ref}`
    is its name, a `{lit}` its integer, an `{op, args}` renders `op(a, b, ...)`
    in written order (the compiler never reorders).  This is the operator
    analogue of `_macro_gloss`, but rendered from the DEFINITION AST directly
    (an admitted operator's meaning IS its kernel definition)."""
    if isinstance(node, dict):
        if set(node) == {"ref"}:
            return str(node["ref"])
        if set(node) == {"lit"}:
            return str(node["lit"])
        if "op" in node:
            args = node.get("args", []) or []
            return f"{node['op']}({', '.join(_ast_gloss(a) for a in args)})"
    return "?"


def render_operator_table(operator_registry: dict = None) -> str:
    """The live ADMITTED-OPERATOR vocabulary section (§11.4 mechanism (i)): one
    `word(params...)  (arity n) -- <definition gloss>` row per admitted derived
    operator, sorted by word so the output is order-independent.  The gloss is
    rendered from the row's kernel-fragment definition AST.

    ONLY PRICED operators are advertised: a row is surfaced iff its certificate
    carries a `pricing` block, i.e. it was admitted through the WP-T4a pricing
    gate and therefore genuinely lowers the corpus DL.  A grandfathered pre-
    pricing row (e.g. the committed `multiple_of`, alias-refused under the
    current gate and carrying no `pricing` block) is NOT authoring vocabulary and
    is omitted.

    Returns "" when there is NO priced operator to advertise (empty registry, or
    only grandfathered rows).  An empty result means the caller OMITS the section
    entirely -- so a registry with no priced operator yields a prompt that is
    BYTE-IDENTICAL to the pre-seam prompt.  This is the concrete form of the
    inert-by-default pin: empty/unchanged registry => identical prompt bytes.  It
    is exactly when a priced operator IS admitted that these bytes change, which
    is how admitting an operator changes the prompt (and the cost the F5
    benchmark measures) -- the operator analogue of the macro E1 seam."""
    operator_registry = operator_registry or {}
    rows = []
    for word in sorted(operator_registry):
        entry = operator_registry[word]
        if not isinstance(entry, dict):
            continue
        row = entry.get("row")
        cert = entry.get("cert") or {}
        if not isinstance(row, dict) or "pricing" not in cert:
            continue                     # unpriced / grandfathered => not vocab
        params = ", ".join(row.get("params", []) or [])
        gloss = _ast_gloss(row.get("definition"))
        rows.append(f"  {word}({params})  (arity {row.get('arity')}) -- {gloss}")
    if not rows:
        return ""
    header = ("ADMITTED OPERATORS (derived words admitted through the R2 "
              "gate; each abbreviates the kernel-fragment definition after the "
              "dash and MAY be used in its stated role -- pred words as pred "
              "operators, term words inside terms; every use is expanded to "
              "its kernel form before compile / eval / smt ever see it):")
    return "\n".join([header] + rows)


# ------------------------------------------------------- import (WP-LI1) ----
# The DIRECTION FLIP (PLAN_LEAN_IMPORT.md §2): for a Mathlib import the source
# object is already FORMAL.  The LLM sees the pretty-printed Lean statement and
# authors a MathReading OF it in the same F-G fragment -- the identical
# envelope, grammar block, lexicon, definition table and force rules as the
# NL prompt (COMPOSED from the same single-source renderers above, never
# duplicated), plus one import-specific rule: an out-of-fragment statement is
# declared as a STRUCTURED fragment-miss, never forced into a wrong reading.

_IMPORT_PREAMBLE = """You are the untrusted SEMANTIC ANALYST of a certified
Mathlib IMPORT operation.  The source object is already FORMAL: a
pretty-printed Lean statement from Mathlib at a pinned commit.  You author a
MATH READING of that statement -- a quoted, force-tagged semantic analysis in
the fragment described below.  A deterministic, LLM-free compiler turns your
Reading back into a Lean statement, and the round-trip is later checked
against the original declaration, so translate FAITHFULLY: no strengthening,
no weakening, no dropped side conditions.  Every quote you write MUST be a
verbatim substring of the pretty-printed statement text below."""

_FRAGMENT_MISS_NOTE = """FRAGMENT MISS (first-class data, never forced):
If the statement needs constants, carriers, binders, or structure OUTSIDE the
fragment above (e.g. Prime, Real, sets, higher-order functions), do NOT force
an unfaithful reading.  Return INSTEAD exactly one JSON object of the shape:
  {"fragment_miss": {"missing": ["<constant-or-carrier>", ...]}}
listing every out-of-fragment constant or carrier the statement needs.  A
declared miss is demand data that prices fragment growth; a forced reading is
a mistranslation."""


def render_import_reading_prompt(decl_name: str, statement_pp: str,
                                 operator_registry: dict = None,
                                 macro_table: dict = None) -> str:
    """The formal->reading authoring prompt for the Mathlib import driver
    (WP-LI1).  Deterministic: the same (decl_name, statement_pp, macro_table,
    operator_registry) always yields identical bytes.  Composes the SAME
    single-source machinery as `render_math_reading_prompt` (grammar block,
    lexicon, definition table, operator table, envelope, force rules), so the
    two prompts can never drift on the fragment they describe; only the
    preamble (direction flip), the source section (a Lean statement, not NL)
    and the structured fragment-miss rule differ."""
    macro_table = macro_table or {}
    parts = [
        _IMPORT_PREAMBLE,
        "",
        "DECLARATION: " + decl_name,
        "LEAN STATEMENT (pretty-printed):",
        "  " + statement_pp,
        "",
        _ENVELOPE_NOTE,
        "",
        render_grammar_block(),
        "",
        render_definition_table(macro_table),
    ]
    op_section = render_operator_table(operator_registry)
    if op_section:
        parts += ["", op_section]
    parts += [
        "",
        _FRAGMENT_MISS_NOTE,
        "",
        _RULES,
    ]
    return "\n".join(parts)


def render_math_reading_prompt(source_text: str, macro_table: dict = None,
                               operator_registry: dict = None) -> str:
    """The full, self-contained math Reading instruction: the task, the source,
    the F-A envelope shape, the generated grammar block + lexicon, the live
    definition table, the admitted-operator vocabulary, and the force/quote-
    groundedness rules.  Deterministic: the same (source_text, macro_table,
    operator_registry) always yields identical bytes, and both tables' insertion
    order is irrelevant (the renderers sort).

    INERT BY DEFAULT: `operator_registry` defaults to None, and a None / empty /
    priced-operator-free registry adds NOTHING to the prompt -- the bytes are
    identical to the pre-seam prompt, so an existing caller that does not pass a
    registry (and any tree whose priced-operator registry is empty) is
    byte-unchanged."""
    macro_table = macro_table or {}
    parts = [
        _PREAMBLE,
        "",
        "SOURCE:",
        "  " + source_text,
        "",
        _ENVELOPE_NOTE,
        "",
        render_grammar_block(),
        "",
        render_definition_table(macro_table),
    ]
    op_section = render_operator_table(operator_registry)
    if op_section:
        parts += ["", op_section]
    parts += [
        "",
        _RULES,
    ]
    return "\n".join(parts)

"""Spec-only validation of LLM output (hard constraint #2).

The LLM may only author declarative specifications: generator specs (JSON),
.ksy documents, tree-sitter grammar.js files in a declarative subset, and
contract annotations.  Anything smelling of general-purpose code is
rejected before it gets anywhere near the kernel or the registry.
"""
from __future__ import annotations

import json
import re

from generators.ksy_model import ALL_ATOMS
from generators.abnf_chain import ABNF_ATOM_VOCAB
from generators.json_codec import JSON_ATOM_VOCAB


class SpecViolation(Exception):
    pass


def validate_generator_spec(text: str) -> dict:
    """Parse + validate a proposed generator spec (JSON document)."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise SpecViolation(f"not valid JSON: {e}")
    if not isinstance(doc, dict):
        raise SpecViolation("generator spec must be a JSON object")
    allowed_keys = {"name", "spec_language", "grammar_atoms", "emitter",
                    "contract", "grammar_js", "notes"}
    extra = set(doc) - allowed_keys
    if extra:
        raise SpecViolation(f"unexpected keys: {sorted(extra)}")
    for k in ("name", "spec_language", "grammar_atoms", "emitter"):
        if k not in doc:
            raise SpecViolation(f"missing required key {k!r}")
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", doc["name"]):
        raise SpecViolation("name must be lowercase-kebab, 3-64 chars")
    if doc["spec_language"] not in ("ksy", "abnf", "json-subset"):
        raise SpecViolation("spec_language must be 'ksy', 'abnf' or 'json-subset'")
    vocab = (set(ALL_ATOMS) if doc["spec_language"] == "ksy"
             else set(ABNF_ATOM_VOCAB) if doc["spec_language"] == "abnf"
             else set(JSON_ATOM_VOCAB))
    atoms = doc["grammar_atoms"]
    if not isinstance(atoms, list) or not atoms:
        raise SpecViolation("grammar_atoms must be a non-empty list")
    bad = set(atoms) - vocab
    if bad:
        raise SpecViolation(
            f"unknown atoms {sorted(bad)}; the vocabulary is {sorted(vocab)}")
    if doc["emitter"] not in ("ksc-python-rw", "abnf-to-ksy", "ts-recursive-codec"):
        raise SpecViolation(
            "emitter must be 'ksc-python-rw', 'abnf-to-ksy' or 'ts-recursive-codec'")
    if doc["spec_language"] == "abnf":
        if doc["emitter"] != "abnf-to-ksy":
            raise SpecViolation("abnf generators must use the abnf-to-ksy emitter")
        if "grammar_js" not in doc:
            raise SpecViolation(
                "abnf generators must include grammar_js (a tree-sitter grammar)")
        validate_grammar_js(doc["grammar_js"])
    elif doc["spec_language"] == "json-subset":
        # json-subset: a RECURSIVE tree-sitter grammar (choice/seq/repeat, mutual
        # recursion) emitted to a self-contained parser; certified by the kernel
        # vpl-differential contract.  No ksy/Kaitai intermediate.
        if doc["emitter"] != "ts-recursive-codec":
            raise SpecViolation(
                "json-subset generators must use the ts-recursive-codec emitter")
        if "grammar_js" not in doc:
            raise SpecViolation(
                "json-subset generators must include grammar_js (a recursive "
                "tree-sitter grammar)")
        validate_grammar_js(doc["grammar_js"])
    elif "grammar_js" in doc:
        raise SpecViolation(
            "grammar_js only belongs on abnf or json-subset generators")
    if doc["emitter"] == "ts-recursive-codec" \
            and doc["spec_language"] != "json-subset":
        raise SpecViolation(
            "the ts-recursive-codec emitter is only for json-subset generators")
    return doc


_FORBIDDEN_JS = [
    r"\brequire\s*\(", r"\bimport\b", r"\bprocess\b", r"\bfs\b\s*\.",
    r"\beval\b", r"\bFunction\b", r"\bfetch\b", r"\bchild_process\b",
    r"=>\s*\{", r"\bfunction\s*\w*\s*\(", r"\bwhile\b", r"\bfor\s*\(",
    r"`",
]


def validate_grammar_js(text: str):
    """Enforce the declarative subset of tree-sitter grammar.js.

    tree-sitter grammars are JS files, so we restrict them to the purely
    declarative idiom: one `module.exports = grammar({...})` whose rule
    bodies are single-expression arrow functions built from the tree-sitter
    combinators.  No statements, no imports, no side effects.
    """
    if not isinstance(text, str) or len(text) > 20000:
        raise SpecViolation("grammar_js missing or oversized")
    stripped = re.sub(r"//[^\n]*", "", text)
    if not re.search(r"module\.exports\s*=\s*grammar\s*\(\s*\{", stripped):
        raise SpecViolation("grammar_js must be 'module.exports = grammar({...})'")
    for pat in _FORBIDDEN_JS:
        if re.search(pat, stripped):
            raise SpecViolation(
                f"grammar_js contains non-declarative construct: /{pat}/")
    return True


def validate_inferred_schema(text: str):
    """The LLM authored a JSON Schema (a spec).  Reject anything that is not a
    pure JSON Schema in the modeled subset -- no general-purpose code, no YAML,
    just declarative JSON.  Returns the parsed SchemaModel."""
    import json as _json
    from generators.jsonschema_model import parse_schema, UnsupportedSchema
    try:
        doc = _json.loads(text)
    except Exception as e:
        raise SpecViolation(f"not valid JSON: {e}")
    if not isinstance(doc, dict):
        raise SpecViolation("schema must be a JSON object")
    try:
        return parse_schema(text)
    except UnsupportedSchema as e:
        raise SpecViolation(f"not a supported JSON Schema: {e}")


def validate_service_spec(text: str):
    """The LLM authored a SERVICE meta-spec (a declarative JSON document).
    Reject anything that is not a pure meta-spec in the modeled subset -- no
    general-purpose code, just JSON that parses into the fixed ServiceModel
    structure (states, tools with a JSON-Schema-subset input contract, a guard/
    update predicate DSL over integers, optional cross-field constraints, and a
    safety invariant).  Every embedded piece is re-parsed by its own modeled
    parser, so an out-of-subset construct is a structured rejection, never code.
    Returns the parsed ServiceModel."""
    import json as _json
    from generators.service_model import parse_service_spec, UnsupportedService
    from generators.constraint_model import (parse_constraint_spec,
                                             UnsupportedConstraint)
    try:
        doc = _json.loads(text)
    except Exception as e:
        raise SpecViolation(f"not valid JSON: {e}")
    if not isinstance(doc, dict):
        raise SpecViolation("service spec must be a JSON object")
    allowed = {"name", "context", "states", "initial", "tools", "safety",
               "notes", "obligations"}
    extra = set(doc) - allowed
    if extra:
        raise SpecViolation(f"unexpected top-level keys: {sorted(extra)}")
    # P1.2 per-tool key allowlist (terminal is new); parse_service_spec reads via
    # .get() so an unknown tool key would be silently dropped -- reject it here.
    tool_keys = {"name", "from", "to", "input_schema", "arg", "guard", "update",
                 "constraints", "terminal"}
    for t in doc.get("tools", []):
        if isinstance(t, dict) and set(t) - tool_keys:
            raise SpecViolation(
                f"tool {t.get('name')!r}: unexpected keys "
                f"{sorted(set(t) - tool_keys)}")
    try:
        # parse_service_spec validates the projected protocol (guards/updates)
        # and every tool's input schema in their modeled subsets.
        m = parse_service_spec(text)
    except UnsupportedService as e:
        raise SpecViolation(f"not a supported service meta-spec: {e}")
    # constraints are not checked by parse_service_spec -- validate each here so
    # a malformed constraint is rejected at the gate, not at certification time.
    for t in m.tools:
        if t.constraints is not None:
            try:
                parse_constraint_spec(_json.dumps(t.constraints))
            except UnsupportedConstraint as e:
                raise SpecViolation(
                    f"tool {t.name}: unsupported constraint spec: {e}")
    return m


def validate_scenarios(text: str, service_model):
    """The LLM authored INTENT SCENARIOS -- concrete call traces with expected
    accept/reject verdicts, derived from the request and the tool interface
    only.  Pure data: JSON traces of (tool, scalar args) plus booleans.  Rejects
    anything else.  Requires at least one fully-accepting scenario and at least
    one rejection, so the expectation set has teeth in both directions.
    Returns the parsed scenario list."""
    import json as _json
    try:
        doc = _json.loads(text)
    except Exception as e:
        raise SpecViolation(f"not valid JSON: {e}")
    if not isinstance(doc, dict) or set(doc) - {"scenarios", "notes"}:
        raise SpecViolation("scenario doc must be {scenarios: [...]}")
    scs = doc.get("scenarios")
    if not isinstance(scs, list) or not (1 <= len(scs) <= 20):
        raise SpecViolation("scenarios must be a list of 1..20 entries")
    tools = {t.name for t in service_model.tools}
    ctx = service_model.context
    scalar = (str, int, float, bool)
    seen_names = set()
    any_all_accept = any_reject = False
    for sc in scs:
        if not isinstance(sc, dict) or set(sc) - {"name", "init", "seq",
                                                  "expect", "why"}:
            raise SpecViolation(f"scenario keys must be name/init/seq/expect: "
                                f"{sc!r}"[:200])
        name = sc.get("name")
        if not isinstance(name, str) or not name or name in seen_names:
            raise SpecViolation(f"scenario name missing/duplicate: {name!r}")
        seen_names.add(name)
        init = sc.get("init")
        if not isinstance(init, dict) or set(init) != set(ctx):
            raise SpecViolation(
                f"scenario {name}: init must set exactly the context vars "
                f"{sorted(ctx)}")
        for v, val in init.items():
            lo, hi = ctx[v]
            if not isinstance(val, int) or isinstance(val, bool) \
                    or not (lo <= val <= hi):
                raise SpecViolation(
                    f"scenario {name}: init {v}={val!r} outside [{lo},{hi}]")
        seq, expect = sc.get("seq"), sc.get("expect")
        if not isinstance(seq, list) or not (1 <= len(seq) <= 20):
            raise SpecViolation(f"scenario {name}: seq must be 1..20 steps")
        if not isinstance(expect, list) or len(expect) != len(seq) \
                or not all(isinstance(e, bool) for e in expect):
            raise SpecViolation(
                f"scenario {name}: expect must be bools, one per step")
        for step in seq:
            if not (isinstance(step, list) and len(step) == 2):
                raise SpecViolation(f"scenario {name}: step must be [tool, args]")
            tool, args = step
            if tool not in tools:
                raise SpecViolation(f"scenario {name}: unknown tool {tool!r}")
            if not isinstance(args, dict):
                raise SpecViolation(f"scenario {name}: args must be an object")
            for k, v in args.items():
                ok = isinstance(v, scalar) or (
                    isinstance(v, list) and all(isinstance(x, scalar) for x in v))
                if not (isinstance(k, str) and ok):
                    raise SpecViolation(
                        f"scenario {name}: arg {k!r} must be scalar data")
        if all(expect):
            any_all_accept = True
        if not all(expect):
            any_reject = True
    if not any_all_accept:
        raise SpecViolation("need at least one fully-accepted scenario "
                            "(a legal run the service must admit)")
    if not any_reject:
        raise SpecViolation("need at least one rejected step "
                            "(a behaviour the service must refuse)")
    return scs


def validate_ksy_purity(text: str):
    """A ksy spec must be plain declarative YAML -- ksy_model.parse_ksy
    already rejects process/imports/opaque types; this is a cheap pre-check
    for text the LLM returns."""
    for needle in ("process:", "ks-opaque-types", "imports:", "!!python"):
        if needle in text:
            raise SpecViolation(f"ksy contains forbidden construct {needle!r}")
    return True

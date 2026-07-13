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
    if doc["spec_language"] not in ("ksy", "abnf"):
        raise SpecViolation("spec_language must be 'ksy' or 'abnf'")
    vocab = set(ALL_ATOMS) if doc["spec_language"] == "ksy" \
        else set(ABNF_ATOM_VOCAB)
    atoms = doc["grammar_atoms"]
    if not isinstance(atoms, list) or not atoms:
        raise SpecViolation("grammar_atoms must be a non-empty list")
    bad = set(atoms) - vocab
    if bad:
        raise SpecViolation(
            f"unknown atoms {sorted(bad)}; the vocabulary is {sorted(vocab)}")
    if doc["emitter"] not in ("ksc-python-rw", "abnf-to-ksy"):
        raise SpecViolation("emitter must be 'ksc-python-rw' or 'abnf-to-ksy'")
    if doc["spec_language"] == "abnf":
        if doc["emitter"] != "abnf-to-ksy":
            raise SpecViolation("abnf generators must use the abnf-to-ksy emitter")
        if "grammar_js" not in doc:
            raise SpecViolation(
                "abnf generators must include grammar_js (a tree-sitter grammar)")
        validate_grammar_js(doc["grammar_js"])
    elif "grammar_js" in doc:
        raise SpecViolation("grammar_js only belongs on abnf generators")
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


def validate_ksy_purity(text: str):
    """A ksy spec must be plain declarative YAML -- ksy_model.parse_ksy
    already rejects process/imports/opaque types; this is a cheap pre-check
    for text the LLM returns."""
    for needle in ("process:", "ks-opaque-types", "imports:", "!!python"):
        if needle in text:
            raise SpecViolation(f"ksy contains forbidden construct {needle!r}")
    return True

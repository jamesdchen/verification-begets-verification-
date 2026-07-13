"""ABNF text-record family: chain support (tree-sitter-emitted parser stage).

Task specs for text record formats are written in ABNF (RFC 5234) -- an
existing, standard spec notation.  Supported subset: a single rule

    record = element element ...

with elements: quoted literals ("LOG", ":"), repeated core rules (4DIGIT,
2HEXDIG, 3ALPHA), and bare core rules (SP, CRLF, DIGIT, HEXDIG, ALPHA).

At task time the chain is:

    .abnf --[stage 1: tree-sitter-emitted ABNF parser, runs SANDBOXED]--> AST
          --[fixed mapper]--> .ksy --[stage 2: Kaitai generator]--> codec

The tree-sitter parser is *emitted code* (generated from an LLM-authored
grammar.js at build time), so it executes only inside the sandbox.  The
fixed mapper cross-checks the parser's AST against an independent
tokenization of the spec text and refuses to proceed on any mismatch, so a
mis-parse cannot silently produce a wrong layout.

Planner-side feature atoms for ABNF specs: abnf:lit abnf:digit abnf:hexdig
abnf:alpha abnf:sp abnf:crlf.
"""
from __future__ import annotations

import re

import common

CORE_FIXED = {"SP": " ", "CRLF": "\r\n", "HTAB": "\t"}
CORE_CLASS = {"DIGIT", "HEXDIG", "ALPHA"}

ABNF_ATOM_VOCAB = ["abnf:lit", "abnf:digit", "abnf:hexdig", "abnf:alpha",
                   "abnf:sp", "abnf:crlf"]


class AbnfError(Exception):
    pass


def tokenize(text: str) -> list:
    """Independent (non-tree-sitter) tokenization; used for planning atoms
    and as the mapper's cross-check oracle."""
    lines = [l.split(";")[0].strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    if len(lines) != 1:
        raise AbnfError("expected exactly one ABNF rule")
    m = re.fullmatch(r"([A-Za-z][A-Za-z0-9-]*)\s*=\s*(.+)", lines[0])
    if not m:
        raise AbnfError("rule must have the form 'name = elements'")
    rest = m.group(2)
    toks = []
    pat = re.compile(r'"([^"]*)"|(\d*)(DIGIT|HEXDIG|ALPHA|SP|CRLF|HTAB)\b')
    pos = 0
    for mt in pat.finditer(rest):
        if rest[pos:mt.start()].strip():
            raise AbnfError(f"unsupported ABNF at: {rest[pos:mt.start()]!r}")
        if mt.group(1) is not None:
            if not mt.group(1):
                raise AbnfError("empty literal")
            toks.append(("lit", mt.group(1)))
        else:
            n = int(mt.group(2)) if mt.group(2) else 1
            name = mt.group(3)
            if name in CORE_FIXED:
                if mt.group(2):
                    raise AbnfError(f"repetition not supported on {name}")
                toks.append(("lit", CORE_FIXED[name]))
            else:
                if not 1 <= n <= 64:
                    raise AbnfError(f"repeat count {n} out of range")
                toks.append(("class", name, n))
        pos = mt.end()
    if rest[pos:].strip():
        raise AbnfError(f"unsupported ABNF at: {rest[pos:]!r}")
    if not toks:
        raise AbnfError("no elements")
    return toks


def abnf_atoms(text: str) -> frozenset:
    atoms = set()
    for t in tokenize(text):
        if t[0] == "lit":
            atoms.add("abnf:sp" if t[1] == " " else
                      "abnf:crlf" if t[1] == "\r\n" else "abnf:lit")
        else:
            atoms.add(f"abnf:{t[1].lower()}")
    return frozenset(atoms)


def ast_tokens(ast: dict) -> list:
    """Extract (kind, ...) tokens from the sandboxed tree-sitter parse.

    Expected named node types (documented to the build loop): rule with
    children including literal / repetition / core_rule nodes.
    """
    if ast["root"].get("error") or ast.get("has_error"):
        raise AbnfError("tree-sitter parser reported a parse error")
    toks = []

    def walk(node):
        t = node["type"]
        if t == "literal":
            txt = node["text"]
            if len(txt) >= 2 and txt[0] == '"' and txt[-1] == '"':
                toks.append(("lit", txt[1:-1]))
            else:
                raise AbnfError(f"literal node with odd text {txt!r}")
            return
        if t == "repetition":
            m = re.fullmatch(r"(\d*)([A-Z]+)", node["text"].strip())
            if not m:
                raise AbnfError(f"repetition node with odd text {node['text']!r}")
            n = int(m.group(1)) if m.group(1) else 1
            name = m.group(2)
            if name in CORE_FIXED:
                toks.append(("lit", CORE_FIXED[name]))
            else:
                toks.append(("class", name, n))
            return
        if t == "core_rule":
            name = node["text"].strip()
            if name in CORE_FIXED:
                toks.append(("lit", CORE_FIXED[name]))
            elif name in CORE_CLASS:
                toks.append(("class", name, 1))
            else:
                raise AbnfError(f"unknown core rule {name!r}")
            return
        for c in node["children"]:
            walk(c)

    walk(ast["root"])
    if not toks:
        raise AbnfError("parser produced no elements")
    return toks


def tokens_to_ksy(toks: list, spec_hash: str) -> str:
    """Fixed, deterministic mapper: ABNF tokens -> .ksy text."""
    sid = f"abnf_rec_{spec_hash[:8]}"
    lines = ["meta:", f"  id: {sid}", "  endian: be", "seq:"]
    for i, t in enumerate(toks):
        if t[0] == "lit":
            bs = t[1].encode("ascii")
            arr = ", ".join(f"0x{b:02x}" for b in bs)
            lines.append(f"  - id: lit{i}")
            lines.append(f"    contents: [{arr}]")
        else:
            _, name, n = t
            lines.append(f"  - id: f{i}_{name.lower()}")
            lines.append("    type: str")
            lines.append(f"    size: {n}")
            lines.append("    encoding: ASCII")
    return "\n".join(lines) + "\n"


def abnf_to_ksy_via_parser(parser_so: bytes, abnf_text: str,
                           grammar_json: bytes = None) -> str:
    """Stage 1 of the chain: run the emitted parser (sandboxed), map to ksy,
    cross-check against the independent tokenizer."""
    from generators.emitters import run_emitted_parser_sandboxed
    # Deterministic normalization on the trusted mapper side: the record rule
    # parses a single line, so strip surrounding whitespace/newlines before
    # handing the input to the (untrusted) emitted parser.
    ast = run_emitted_parser_sandboxed(parser_so, abnf_text.strip(), grammar_json)
    toks = ast_tokens(ast)
    reference = tokenize(abnf_text)
    if toks != reference:
        raise AbnfError(
            f"parser AST tokens {toks!r} disagree with reference tokenization "
            f"{reference!r} -- refusing to map")
    return tokens_to_ksy(toks, common.sha256_bytes(abnf_text.encode()))

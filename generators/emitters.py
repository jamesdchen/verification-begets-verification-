"""Emit adapters: the fixed interpreters behind each emit_entrypoint kind.

A library entry's emit_entrypoint is *data* (JSON); these functions are the
fixed machinery that runs the corresponding outsourced tool.  The tools
(ksc, tree-sitter, cc) are vendored binaries; their outputs are never trusted
-- every emission from an emit-check-tier entry is individually checked by
the kernel before use.

Emitted code (generated parsers/codecs) is only ever *executed* inside the
sandbox; the tool invocations themselves are ordinary trusted-tool runs.
"""
from __future__ import annotations

import pathlib
import tempfile

import common
from sandbox import Sandbox


class EmitError(Exception):
    pass


def emit_ksc_python_rw(ksy_text: str) -> dict:
    """Kaitai Struct: .ksy spec -> read-write Python codec module."""
    import yaml
    sid = yaml.safe_load(ksy_text)["meta"]["id"]
    with tempfile.TemporaryDirectory(prefix="cgb-ksc-") as td:
        tdp = pathlib.Path(td)
        (tdp / f"{sid}.ksy").write_text(ksy_text)
        proc = common.run_cmd(
            [common.JAVA, "-cp", common.KSC_CLASSPATH, common.KSC_MAIN,
             "-t", "python", "-w", "--outdir", str(tdp / "gen"),
             str(tdp / f"{sid}.ksy")],
            timeout=120)
        out = tdp / "gen" / f"{sid}.py"
        if proc.returncode != 0 or not out.exists():
            raise EmitError(
                f"ksc failed rc={proc.returncode}: "
                f"{(proc.stderr or proc.stdout)[:2000].decode(errors='replace')}")
        return {f"{sid}.py": out.read_bytes()}


def emit_tree_sitter_parser(grammar_js: str) -> dict:
    """tree-sitter: grammar.js spec -> generated C parser + compiled .so.

    The .so is emitted code; callers must only load/execute it inside the
    sandbox.
    """
    with tempfile.TemporaryDirectory(prefix="cgb-ts-") as td:
        tdp = pathlib.Path(td)
        (tdp / "grammar.js").write_text(grammar_js)
        (tdp / "package.json").write_text(
            '{"name": "cgb-grammar", "version": "0.0.1"}\n')
        proc = common.run_cmd([common.TREE_SITTER, "generate", "--abi", "14"],
                              cwd=tdp, timeout=300)
        if proc.returncode != 0:
            raise EmitError(
                f"tree-sitter generate failed: "
                f"{(proc.stderr or proc.stdout)[:2000].decode(errors='replace')}")
        src = tdp / "src" / "parser.c"
        proc = common.run_cmd(
            [common.CC, "-shared", "-fPIC", "-O1",
             "-I", str(tdp / "src"), str(src), "-o", str(tdp / "parser.so")],
            timeout=300)
        if proc.returncode != 0:
            raise EmitError(
                f"cc failed: {(proc.stderr or proc.stdout)[:2000].decode(errors='replace')}")
        return {
            "parser.c": src.read_bytes(),
            "parser.so": (tdp / "parser.so").read_bytes(),
            "grammar.json": (tdp / "src" / "grammar.json").read_bytes(),
        }


_TS_PARSE_DRIVER = r"""
import ctypes, json, sys
import tree_sitter
name = json.load(open("grammar.json"))["name"]
lib = ctypes.CDLL("./parser.so")
fn = getattr(lib, "tree_sitter_" + name)
fn.restype = ctypes.c_void_p
lang = tree_sitter.Language(fn())
parser = tree_sitter.Parser(lang)
data = open("input.txt", "rb").read()
tree = parser.parse(data)

def walk(node):
    return {
        "type": node.type,
        "text": node.text.decode("utf-8", errors="replace"),
        "named": node.is_named,
        "error": node.type == "ERROR" or node.is_missing,
        "children": [walk(c) for c in node.children],
    }

out = {"root": walk(tree.root_node), "has_error": tree.root_node.has_error}
print(json.dumps(out))
"""


def run_emitted_parser_sandboxed(parser_so: bytes, input_text: str,
                                 grammar_json: bytes = None) -> dict:
    """Execute a tree-sitter-emitted parser on an input, inside the sandbox."""
    import json
    if grammar_json is None:
        grammar_json = b'{"name": "abnf_rec"}'
    with Sandbox() as sb:
        sb.add_file("parser.so", parser_so)
        sb.add_file("grammar.json", grammar_json)
        sb.add_file("input.txt", input_text)
        sb.add_file("driver.py", _TS_PARSE_DRIVER)
        res = sb.run(["python3", "driver.py"], timeout=60)
        if not res.ok:
            raise EmitError(
                f"sandboxed parse failed rc={res.returncode}: "
                f"{res.stderr[:2000].decode(errors='replace')}")
        return json.loads(res.stdout)

"""JSON-subset recursive codec family -- the `ts-recursive-codec` species.

The ORIGINAL P4b route (JSON "via the existing chain": .ksy / ABNF / refcodec)
is infeasible -- the .ksy subset rejects recursive `types:`, ABNF wants one
flat rule, and refcodec is a *linear* field interpreter.  None of those can
express a recursively-nested value.  What DOES work is a recursive tree-sitter
grammar (choice/seq/repeat, mutual recursion) that passes validate_grammar_js
and compiles via the tree-sitter generator (ABI 14) into a real recursive
parser.

This module is the corrected route.  It defines a small, honest JSON subset --
objects, arrays, strings (no escapes), integers, booleans, null -- bounded to a
named recursion depth, and provides TWO independent codecs plus a stdlib anchor:

  A (emitted)     : a hand-written recursive grammar.js -> tree-sitter parser
                    (statically linked, driven via the C API) -> a FIXED,
                    trusted tree-WALK decoder + a FIXED serializer.
  B (independent) : a fixed, hand-audited recursive-DESCENT decoder + serializer
                    sharing NO code with tree-sitter (the refcodec pattern, made
                    recursive).
  C (anchor)      : stdlib `json`, restricted to the subset by canonical dumps.

The kernel `vpl-differential` contract diffs these on bounded-depth recursive
values (encode-side BYTE agreement + cross-decode) and, on structurally MUTATED
inputs, checks that the tree-sitter membership decider (has_error) and the
recursive-descent decider agree -- a visibly-pushdown membership differential.

Everything here is LLM-free and fixed; the grammar is hand-written.  The
sandbox-side implementations (tswalk.py, rd.py, mutate.py) are shipped as source
strings, exactly like refcodec ships ref.py.
"""
from __future__ import annotations

import json

from sandbox import Sandbox
from generators.emitters import emit_tree_sitter_parser_linked, EmitError

# --- atom vocabulary (the species' own) -----------------------------------
# The six content atoms plus a parametric depth-bound atom json:depth:<N>.  The
# depth bound is part of the vocabulary so it is named at planning time and,
# through the contract, on the certificate.
JSON_CONTENT_ATOMS = ["json:object", "json:array", "json:string",
                      "json:number", "json:bool", "json:null"]
JSON_MAX_DEPTH = 8
JSON_DEFAULT_DEPTH = 4
JSON_ATOM_VOCAB = JSON_CONTENT_ATOMS + [
    f"json:depth:{n}" for n in range(1, JSON_MAX_DEPTH + 1)]


def json_depth_bound(atoms, default=JSON_DEFAULT_DEPTH) -> int:
    """Extract the numeric depth bound from a json:depth:<N> atom, if present."""
    ds = [int(a.rsplit(":", 1)[1]) for a in atoms if a.startswith("json:depth:")]
    return ds[0] if ds else default


# --- Implementation A, stage 0: the hand-written recursive grammar ---------
# Declarative tree-sitter idiom only (single-expression arrows built from the
# combinators) so it passes buildloop.validate.validate_grammar_js.  Mutual
# recursion: _value -> object/array -> pair/_value.  Numbers are integers and
# strings carry no escapes -- a deliberately small, canonicalizable subset.
JSON_GRAMMAR_JS = r"""
module.exports = grammar({
  name: 'jsonsub',
  extras: $ => [/\s/],
  rules: {
    document: $ => $._value,
    _value: $ => choice($.object, $.array, $.string, $.number,
                        $.true, $.false, $.null),
    object: $ => seq('{', optional(seq($.pair, repeat(seq(',', $.pair)))), '}'),
    pair: $ => seq($.string, ':', $._value),
    array: $ => seq('[', optional(seq($._value, repeat(seq(',', $._value)))), ']'),
    string: $ => /"[^"\\]*"/,
    number: $ => /-?[0-9]+/,
    true: $ => 'true',
    false: $ => 'false',
    null: $ => 'null',
  }
});
"""


def emit_json_codec() -> dict:
    """Emit Implementation A's artifact: the runtime-linked tree-sitter parser.
    Returns {parser.c, parser.so, grammar.json}.  Raises EmitError on failure."""
    return emit_tree_sitter_parser_linked(JSON_GRAMMAR_JS)


# --- Implementation A, runtime: tree-walk decoder + serializer -------------
# Shipped into the sandbox as tswalk.py.  Loads the emitted parser.so via
# ctypes, drives the tree-sitter C API, and walks the concrete syntax tree back
# into a Python value.  ts_serialize is an independent canonical encoder.
_TS_WALK_SRC = r'''
"""Implementation A: tree-sitter parse + fixed tree-walk (decoder+serializer)."""
import ctypes, json as _json

_lib = ctypes.CDLL("./parser.so")
_name = _json.load(open("grammar.json"))["name"]


class _Node(ctypes.Structure):
    _fields_ = [("context", ctypes.c_uint32 * 4),
                ("id", ctypes.c_void_p), ("tree", ctypes.c_void_p)]


_langfn = getattr(_lib, "tree_sitter_" + _name); _langfn.restype = ctypes.c_void_p
_lib.ts_parser_new.restype = ctypes.c_void_p
_lib.ts_parser_set_language.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_lib.ts_parser_set_language.restype = ctypes.c_bool
_lib.ts_parser_parse_string.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_char_p, ctypes.c_uint32]
_lib.ts_parser_parse_string.restype = ctypes.c_void_p
_lib.ts_tree_root_node.argtypes = [ctypes.c_void_p]; _lib.ts_tree_root_node.restype = _Node
_lib.ts_tree_delete.argtypes = [ctypes.c_void_p]
_lib.ts_node_type.argtypes = [_Node]; _lib.ts_node_type.restype = ctypes.c_char_p
_lib.ts_node_named_child_count.argtypes = [_Node]
_lib.ts_node_named_child_count.restype = ctypes.c_uint32
_lib.ts_node_named_child.argtypes = [_Node, ctypes.c_uint32]
_lib.ts_node_named_child.restype = _Node
_lib.ts_node_start_byte.argtypes = [_Node]; _lib.ts_node_start_byte.restype = ctypes.c_uint32
_lib.ts_node_end_byte.argtypes = [_Node]; _lib.ts_node_end_byte.restype = ctypes.c_uint32
_lib.ts_node_has_error.argtypes = [_Node]; _lib.ts_node_has_error.restype = ctypes.c_bool

_parser = _lib.ts_parser_new()
_lib.ts_parser_set_language(_parser, _langfn())


def _parse(text):
    b = text.encode("utf-8")
    tree = _lib.ts_parser_parse_string(_parser, None, b, len(b))
    return tree, b


def ts_has_error(text):
    """Membership decider A: True == the tree-sitter parser rejects `text`
    (an ERROR/MISSING node anywhere, or no value at all -> not in the language)."""
    tree, _b = _parse(text)
    root = _lib.ts_tree_root_node(tree)
    err = _lib.ts_node_has_error(root) or _lib.ts_node_named_child_count(root) == 0
    _lib.ts_tree_delete(tree)
    return bool(err)


def _txt(node, b):
    return b[_lib.ts_node_start_byte(node):_lib.ts_node_end_byte(node)].decode("utf-8")


def _value(node, b):
    t = _lib.ts_node_type(node).decode()
    if t == "object":
        d = {}
        for i in range(_lib.ts_node_named_child_count(node)):
            pair = _lib.ts_node_named_child(node, i)          # pair
            k = _value(_lib.ts_node_named_child(pair, 0), b)  # string key
            v = _value(_lib.ts_node_named_child(pair, 1), b)  # value
            d[k] = v
        return d
    if t == "array":
        return [_value(_lib.ts_node_named_child(node, i), b)
                for i in range(_lib.ts_node_named_child_count(node))]
    if t == "string":
        return _txt(node, b)[1:-1]
    if t == "number":
        return int(_txt(node, b))
    if t == "true":
        return True
    if t == "false":
        return False
    if t == "null":
        return None
    raise ValueError("unexpected node type " + t)


def ts_decode(text):
    tree, b = _parse(text)
    root = _lib.ts_tree_root_node(tree)
    if _lib.ts_node_has_error(root) or _lib.ts_node_named_child_count(root) == 0:
        _lib.ts_tree_delete(tree)
        raise ValueError("parse error")
    top = _lib.ts_node_named_child(root, 0)   # document's single value node
    v = _value(top, b)
    _lib.ts_tree_delete(tree)
    return v


def ts_serialize(v):
    """Independent canonical encoder (tree-sitter side)."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, list):
        return "[" + ",".join(ts_serialize(e) for e in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join('"' + k + '":' + ts_serialize(v[k])
                              for k in sorted(v)) + "}"
    raise ValueError("unserializable value")
'''


# --- Implementation B: independent recursive-descent decoder + serializer --
# Shipped as rd.py.  Shares NO code with tree-sitter -- a plain hand-audited
# recursive-descent parser over the raw string.  Same JSON subset / same
# canonical format, derived independently, so a shared-misconception bug in the
# tree-walk (wrong child index, dropped field) diverges here and is caught.
_RD_SRC = r'''
"""Implementation B: independent recursive-descent codec (no tree-sitter)."""
_WS = " \t\n\r\f\v"


class _P:
    def __init__(self, s):
        self.s = s; self.i = 0; self.n = len(s)

    def ws(self):
        while self.i < self.n and self.s[self.i] in _WS:
            self.i += 1

    def value(self):
        self.ws()
        if self.i >= self.n:
            raise ValueError("unexpected end of input")
        c = self.s[self.i]
        if c == '{':
            return self.obj()
        if c == '[':
            return self.arr()
        if c == '"':
            return self.string()
        if c == 't':
            return self.lit("true", True)
        if c == 'f':
            return self.lit("false", False)
        if c == 'n':
            return self.lit("null", None)
        if c == '-' or c.isdigit():
            return self.number()
        raise ValueError("unexpected character " + repr(c))

    def lit(self, word, val):
        if self.s[self.i:self.i + len(word)] != word:
            raise ValueError("bad literal")
        self.i += len(word)
        return val

    def number(self):
        j = self.i
        if self.i < self.n and self.s[self.i] == '-':
            self.i += 1
        k = self.i
        while self.i < self.n and self.s[self.i].isdigit():
            self.i += 1
        if self.i == k:
            raise ValueError("bad number")
        return int(self.s[j:self.i])

    def string(self):
        # subset: "[^"\\]*"  -- no escapes, no embedded quote/backslash
        self.i += 1
        j = self.i
        while self.i < self.n and self.s[self.i] not in '"\\':
            self.i += 1
        if self.i >= self.n or self.s[self.i] != '"':
            raise ValueError("unterminated string")
        val = self.s[j:self.i]
        self.i += 1
        return val

    def obj(self):
        self.i += 1
        d = {}
        self.ws()
        if self.i < self.n and self.s[self.i] == '}':
            self.i += 1
            return d
        while True:
            self.ws()
            if self.i >= self.n or self.s[self.i] != '"':
                raise ValueError("expected string key")
            k = self.string()
            self.ws()
            if self.i >= self.n or self.s[self.i] != ':':
                raise ValueError("expected ':'")
            self.i += 1
            d[k] = self.value()
            self.ws()
            if self.i >= self.n:
                raise ValueError("unterminated object")
            c = self.s[self.i]
            if c == ',':
                self.i += 1
                continue
            if c == '}':
                self.i += 1
                return d
            raise ValueError("expected ',' or '}'")

    def arr(self):
        self.i += 1
        a = []
        self.ws()
        if self.i < self.n and self.s[self.i] == ']':
            self.i += 1
            return a
        while True:
            a.append(self.value())
            self.ws()
            if self.i >= self.n:
                raise ValueError("unterminated array")
            c = self.s[self.i]
            if c == ',':
                self.i += 1
                continue
            if c == ']':
                self.i += 1
                return a
            raise ValueError("expected ',' or ']'")


def rd_decode(text):
    p = _P(text)
    v = p.value()
    p.ws()
    if p.i != p.n:
        raise ValueError("trailing content")
    return v


def rd_is_member(text):
    """Membership decider B: True == `text` is in the JSON-subset language."""
    try:
        rd_decode(text)
        return True
    except Exception:
        return False


def rd_serialize(v):
    """Independent canonical encoder (recursive-descent side)."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, list):
        return "[" + ",".join(rd_serialize(e) for e in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join('"' + k + '":' + rd_serialize(v[k])
                              for k in sorted(v)) + "}"
    raise ValueError("unserializable value")
'''


# --- structural mutations: visibly-pushdown membership violations ----------
_MUTATE_SRC = r'''
"""Structural mutations that push a well-formed JSON string out of the
(visibly-pushdown) language: bracket deletion / swap / truncation / stray
token.  Bracket structure is the pushdown alphabet, so these are exactly the
membership violations a per-character regex cannot catch but a recursive
grammar must."""


def mutations(text):
    out = []
    brackets = "{}[]"
    # stray closing / opening bracket: guaranteed illegal for ANY value
    out.append(("append-bracket", text + "]"))
    out.append(("prepend-bracket", "[" + text))
    # delete the first / last bracket occurrence (unbalances the string)
    first = next((i for i, c in enumerate(text) if c in brackets), -1)
    last = next((i for i in range(len(text) - 1, -1, -1)
                 if text[i] in brackets), -1)
    if first >= 0:
        out.append(("del-first-bracket", text[:first] + text[first + 1:]))
    if last >= 0:
        out.append(("del-last-bracket", text[:last] + text[last + 1:]))
    # swap one bracket for its opposite kind (breaks the pairing discipline)
    swap = {"{": "[", "[": "{", "}": "]", "]": "}"}
    for i, c in enumerate(text):
        if c in swap:
            out.append(("swap-bracket", text[:i] + swap[c] + text[i + 1:]))
            break
    # truncate before the final character
    if len(text) > 1:
        out.append(("truncate", text[:-1]))
    return out
'''


def ts_walk_source() -> str:
    return _TS_WALK_SRC


def rd_source() -> str:
    return _RD_SRC


def mutate_source() -> str:
    return _MUTATE_SRC


# in-process handles for demos/tests (the sandbox re-imports from source)
_rd_ns = {}
exec(_RD_SRC, _rd_ns)
rd_decode = _rd_ns["rd_decode"]
rd_is_member = _rd_ns["rd_is_member"]
rd_serialize = _rd_ns["rd_serialize"]
_mut_ns = {}
exec(_MUTATE_SRC, _mut_ns)
mutations = _mut_ns["mutations"]


# --- Hypothesis strategy source (shared by both harnesses) -----------------
def _strategy_src(depth: int) -> str:
    """A HARD depth-bounded recursive JSON strategy.  The depth cap is the
    certificate's named claim -- it also caps the tree-JSON driver's nesting so
    deep inputs cannot become opaque sandbox crashes."""
    return (
        '_SAFE = "abcABC012 _-.xyz"\n'
        '_txt = st.text(alphabet=_SAFE, min_size=0, max_size=5)\n'
        'def jval(d):\n'
        '    leaf = st.one_of(st.none(), st.booleans(),\n'
        '                     st.integers(min_value=-1000, max_value=1000), _txt)\n'
        '    if d <= 0:\n'
        '        return leaf\n'
        '    c = jval(d - 1)\n'
        '    return st.one_of(leaf, st.lists(c, max_size=4),\n'
        '                     st.dictionaries(keys=_txt, values=c, max_size=4))\n'
        f'ROOT = jval({int(depth)})\n')


def build_vpl_differential_harness(depth_bound: int, max_examples: int) -> str:
    """Channel 1: cross-implementation differential on bounded-depth recursive
    JSON values -- encode-side BYTE agreement across A/B/stdlib plus cross-decode
    (each implementation decodes the others' bytes)."""
    return (
        "import json, sys, traceback\n"
        "from hypothesis import given, settings, strategies as st, HealthCheck\n"
        "from tswalk import ts_decode, ts_serialize\n"
        "from rd import rd_decode, rd_serialize\n"
        f"MAXEX = {int(max_examples)}\n"
        "def std_serialize(v):\n"
        "    return json.dumps(v, sort_keys=True, separators=(',', ':'),"
        " ensure_ascii=True)\n"
        + _strategy_src(depth_bound) +
        "@settings(max_examples=MAXEX, derandomize=True, database=None,"
        " deadline=None, suppress_health_check=list(HealthCheck))\n"
        "@given(ROOT)\n"
        "def prop(v):\n"
        "    ea = ts_serialize(v); eb = rd_serialize(v); ec = std_serialize(v)\n"
        "    # CHANNEL 1: three independent encoders must agree byte-for-byte\n"
        "    assert ea == eb == ec, ('encode-divergence', ea, eb, ec, repr(v)[:200])\n"
        "    # each implementation round-trips its own bytes ...\n"
        "    assert ts_decode(ea) == v, ('ts-roundtrip', ea)\n"
        "    assert rd_decode(eb) == v, ('rd-roundtrip', eb)\n"
        "    assert json.loads(ec) == v, ('std-roundtrip', ec)\n"
        "    # ... and cross-decodes the others' bytes\n"
        "    assert ts_decode(eb) == v, ('ts-cross-decode', eb)\n"
        "    assert rd_decode(ea) == v, ('rd-cross-decode', ea)\n"
        "def main():\n"
        "    try:\n"
        "        prop()\n"
        "        print(json.dumps({'status': 'pass', 'examples': MAXEX}))\n"
        "    except BaseException as e:\n"
        "        print(json.dumps({'status': 'fail', 'error': repr(e)[:2000],\n"
        "                          'traceback': traceback.format_exc()[-2500:]}))\n"
        "        sys.exit(1)\n"
        "main()\n")


def build_vpl_membership_harness(depth_bound: int, max_examples: int) -> str:
    """Channel 2: membership differential on structurally MUTATED inputs.  The
    tree-sitter decider (has_error) and the recursive-descent decider must agree
    on every mutation, and each value must yield at least one input both reject
    (teeth: the mutations actually exercise rejection)."""
    return (
        "import json, sys, traceback\n"
        "from hypothesis import given, settings, strategies as st, HealthCheck\n"
        "from tswalk import ts_has_error\n"
        "from rd import rd_is_member, rd_serialize\n"
        "from mutate import mutations\n"
        f"MAXEX = {int(max_examples)}\n"
        + _strategy_src(depth_bound) +
        "@settings(max_examples=MAXEX, derandomize=True, database=None,"
        " deadline=None, suppress_health_check=list(HealthCheck))\n"
        "@given(ROOT)\n"
        "def prop(v):\n"
        "    text = rd_serialize(v)                 # a well-formed member\n"
        "    assert not ts_has_error(text), ('valid-input-flagged', text)\n"
        "    assert rd_is_member(text), ('valid-input-rejected', text)\n"
        "    both_reject = 0\n"
        "    for lab, m in mutations(text):\n"
        "        tr = ts_has_error(m)               # tree-sitter: True == reject\n"
        "        rr = not rd_is_member(m)           # recursive-descent: reject\n"
        "        # CHANNEL 2: two independent membership deciders must agree\n"
        "        assert tr == rr, ('membership-divergence', lab, m, tr, rr)\n"
        "        if tr and rr:\n"
        "            both_reject += 1\n"
        "    assert both_reject >= 1, ('no-effective-mutation', text)\n"
        "def main():\n"
        "    try:\n"
        "        prop()\n"
        "        print(json.dumps({'status': 'pass', 'examples': MAXEX}))\n"
        "    except BaseException as e:\n"
        "        print(json.dumps({'status': 'fail', 'error': repr(e)[:2000],\n"
        "                          'traceback': traceback.format_exc()[-2500:]}))\n"
        "        sys.exit(1)\n"
        "main()\n")


def run_json_parser_sandboxed(files: dict, text: str) -> dict:
    """Run Implementation A's emitted parser on one input, inside the sandbox,
    and report membership.  Returns {"has_error": bool}."""
    driver = ("import json\n"
              "from tswalk import ts_has_error\n"
              "print(json.dumps({'has_error':"
              " ts_has_error(open('input.txt').read())}))\n")
    with Sandbox() as sb:
        for name, data in files.items():
            sb.add_file(name, data)
        sb.add_file("tswalk.py", _TS_WALK_SRC)
        sb.add_file("input.txt", text)
        sb.add_file("driver.py", driver)
        res = sb.run(["python3", "driver.py"], timeout=60)
        if not res.ok:
            raise EmitError(
                f"sandboxed json parse failed rc={res.returncode}: "
                f"{res.stderr[:1500].decode(errors='replace')}")
        return json.loads(res.stdout.decode().strip().splitlines()[-1])

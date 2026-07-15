"""F1.3 -- invariants for the math Reading prompt (buildloop.math_prompt).

The math analogue of tests/test_prompt.py.  Two disciplines are pinned:

  (a) SINGLE-SOURCING: the grammar block advertises EXACTLY the kinds in
      MATH_LF_KINDS (both directions) and names every MATH_OPERATORS word, so
      adding a kind or a lexicon word to generators.math_reading automatically
      reaches the prompt -- prompt grammar and validator can never drift.

  (b) THE E1 MECHANISM (the crux): the live definition table renders the
      admitted macros into the prompt, so admitting a macro CHANGES the prompt
      bytes.  Without this the macro table reaches no prompt, admitted
      "definitions" cannot change LLM cost, and the F5 benchmark measures a
      coin flip.  We assert an empty vs one-macro table differ, and that the
      full prompt contains a macro's name iff the macro is admitted.

Plus determinism (identical bytes on re-render; macro-table order-independence)
and that the full prompt carries the source text and the F-A envelope keys.

Runnable under pytest and as `python3 tests/test_math_prompt.py`.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import math_reading
from buildloop import math_prompt

# a kind is "advertised" wherever a JSON `"kind":"..."` token appears -- these
# come only from the generated grammar-block signatures.
_KIND_TOKEN = re.compile(r'"kind"\s*:\s*"([a-z_]+)"')

_MACRO = {"name": "m_abc", "params": ["p"],
          "body": [{"kind": "hypothesis",
                    "pred": {"op": "even", "args": [{"ref": "p"}]}}]}
_SRC = "For every natural number n, n divides n squared."


def _advertised_kinds(text):
    return set(_KIND_TOKEN.findall(text))


# ----------------------------------------------------------- single-sourcing
def test_grammar_block_single_sources_every_kind_both_directions():
    block = math_prompt.render_grammar_block()
    advertised = _advertised_kinds(block)
    # direction 1: every kind in the single source of truth reaches the prompt
    for k in math_reading.MATH_LF_KINDS:
        assert k in block, f"{k!r} missing from the rendered grammar block"
        assert k in advertised, f"{k!r} not advertised as a JSON kind token"
    # direction 2: every advertised kind token is a key of MATH_LF_KINDS
    for k in advertised:
        assert k in math_reading.MATH_LF_KINDS, \
            f"grammar block advertises unknown kind {k!r}"
    assert advertised == set(math_reading.MATH_LF_KINDS)


def test_grammar_block_names_every_lexicon_word():
    block = math_prompt.render_grammar_block()
    for word in math_reading.MATH_OPERATORS:
        assert word in block, f"lexicon word {word!r} missing from the block"


def test_force_rules_are_derived_from_the_dict():
    # the force_rule half of each MATH_LF_KINDS value must reach the prompt too,
    # so grammar and force column cannot drift.
    block = math_prompt.render_grammar_block()
    for _sig, force in math_reading.MATH_LF_KINDS.values():
        assert force in block, f"force rule {force!r} missing from the block"


# ------------------------------------------------------------- E1 mechanism
def test_definition_table_empty_vs_macro_differ():
    empty = math_prompt.render_definition_table({})
    withm = math_prompt.render_definition_table({"m_abc": _MACRO})
    assert empty != withm, \
        "admitting a macro did NOT change the definition table (E1 broken)"
    # the empty table is a stable, non-empty '(none)' block ...
    assert "(none)" in empty
    # ... and the macro table names the macro and glosses its body.
    assert "m_abc" in withm
    assert "p" in withm            # the param
    assert "even" in withm         # the gloss, derived from the body's pred op


def test_full_prompt_contains_macro_name_iff_admitted():
    without = math_prompt.render_math_reading_prompt(_SRC, {})
    withm = math_prompt.render_math_reading_prompt(_SRC, {"m_abc": _MACRO})
    assert "m_abc" not in without, \
        "macro name leaked into a macro-free prompt"
    assert "m_abc" in withm, \
        "admitted macro name absent from the prompt (E1 broken)"
    assert without != withm


def test_gloss_derives_from_body_content():
    # a different body -> a different gloss, so the bytes track the vocabulary,
    # not just the name.
    m1 = {"name": "m_x", "params": ["p"],
          "body": [{"kind": "hypothesis",
                    "pred": {"op": "even", "args": [{"ref": "p"}]}}]}
    m2 = {"name": "m_x", "params": ["p"],
          "body": [{"kind": "hypothesis",
                    "pred": {"op": "odd", "args": [{"ref": "p"}]}}]}
    t1 = math_prompt.render_definition_table({"m_x": m1})
    t2 = math_prompt.render_definition_table({"m_x": m2})
    assert t1 != t2, "gloss did not track the macro body content"
    assert "even" in t1 and "odd" in t2


# --------------------------------------------------------------- determinism
def test_rendering_is_byte_stable():
    a = math_prompt.render_math_reading_prompt(_SRC, {"m_abc": _MACRO})
    b = math_prompt.render_math_reading_prompt(_SRC, {"m_abc": _MACRO})
    assert a == b, "same inputs produced different prompt bytes"
    assert math_prompt.render_grammar_block() == \
        math_prompt.render_grammar_block()


def test_definition_table_is_order_independent():
    m_a = {"name": "m_a", "params": [], "body": [
        {"kind": "conclusion", "pred": {"op": "dvd",
                                        "args": [{"ref": "x"}, {"ref": "y"}]}}]}
    m_b = {"name": "m_b", "params": ["q"], "body": [
        {"kind": "hypothesis", "pred": {"op": "odd", "args": [{"ref": "q"}]}}]}
    # same macros, different dict INSERTION order -> identical rendering
    forward = {"m_a": m_a, "m_b": m_b}
    reverse = {}
    reverse["m_b"] = m_b
    reverse["m_a"] = m_a
    assert math_prompt.render_definition_table(forward) == \
        math_prompt.render_definition_table(reverse)
    # and the full prompt inherits the order-independence
    assert math_prompt.render_math_reading_prompt(_SRC, forward) == \
        math_prompt.render_math_reading_prompt(_SRC, reverse)


def test_empty_and_none_macro_table_agree():
    # None defaults to the empty table (a macro-free prompt is stable).
    assert math_prompt.render_definition_table(None) == \
        math_prompt.render_definition_table({})
    assert math_prompt.render_math_reading_prompt(_SRC) == \
        math_prompt.render_math_reading_prompt(_SRC, {})


# ---------------------------------------------------- envelope + source text
def test_full_prompt_contains_source_and_envelope_keys():
    prompt = math_prompt.render_math_reading_prompt(_SRC, {"m_abc": _MACRO})
    assert _SRC in prompt, "source text absent from the prompt"
    assert "theorem" in prompt, "envelope key 'theorem' absent"
    assert "statements" in prompt, "envelope key 'statements' absent"
    # the grammar block and definition table are both embedded in the whole
    assert math_prompt.render_grammar_block() in prompt
    assert math_prompt.render_definition_table({"m_abc": _MACRO}) in prompt


if __name__ == "__main__":
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_"):
            _fn()
            print("PASS", _name)
    print("all math-prompt invariants hold")

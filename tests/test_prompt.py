"""P0.5.8 -- the Reading prompt is single-sourced from generators.reading.

One source of truth (reading.LF_KINDS) feeds BOTH the prompt's grammar block and
the reading validator's accepted-kind set, so the two can never drift.  These
invariants pin that down:

  (a) the rendered grammar block advertises EXACTLY the kinds in LF_KINDS
      (both directions: nothing missing, nothing extra);
  (b) the reading validator accepts EXACTLY set(LF_KINDS);
  (c) the static prompt fits its 6000-char budget;
  (d) a representative per-call prompt (base + one request + two feedback
      transcripts, of which only the last two are ever kept) fits its
      12000-char budget.

Runnable under pytest and as `python3 tests/test_prompt.py`.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import reading
from buildloop import service_loop

STATIC_BUDGET = 6000
PERCALL_BUDGET = 12000

# a kind is "advertised" in the prompt wherever a JSON `"kind":"..."` token
# appears -- these come only from the generated grammar-block signatures.
_KIND_TOKEN = re.compile(r'"kind"\s*:\s*"([a-z_]+)"')


def _advertised_kinds(prompt):
    return set(_KIND_TOKEN.findall(prompt))


def _reading_with_kind(kind):
    return ('{"service":"s","statements":[{"id":"s1","force":"choice",'
            '"quote":"","lf":{"kind":"%s"}}]}' % kind)


def test_grammar_block_matches_lf_kinds_both_directions():
    static = service_loop.reading_static_prompt()
    advertised = _advertised_kinds(static)
    # direction 1: every kind in the single source of truth is advertised
    for k in reading.LF_KINDS:
        assert k in static, f"{k!r} missing from the rendered static prompt"
        assert k in advertised, f"{k!r} not advertised as a JSON kind token"
    # direction 2: every advertised kind token is a key of LF_KINDS
    for k in advertised:
        assert k in reading.LF_KINDS, f"prompt advertises unknown kind {k!r}"
    assert advertised == set(reading.LF_KINDS)


def test_validator_accepts_exactly_lf_kinds():
    # the validator's field-key map is keyed by exactly the single-source kinds
    # (also asserted at import time in generators.reading) -- re-affirm here.
    assert set(reading._LF_FIELDS) == set(reading.LF_KINDS)
    # behaviourally: a kind OUTSIDE LF_KINDS is rejected as unknown ...
    try:
        reading.parse_reading(_reading_with_kind("teleport"), "any request")
        unknown_msg = ""
    except reading.BadReading as e:
        unknown_msg = str(e)
    assert "unknown lf kind" in unknown_msg, unknown_msg
    # ... and no kind IN LF_KINDS is ever reported unknown (it is recognised;
    # it may still fail later structural checks, which is fine here).
    for k in reading.LF_KINDS:
        try:
            reading.parse_reading(_reading_with_kind(k), "any request")
            msg = ""
        except reading.BadReading as e:
            msg = str(e)
        assert "unknown lf kind" not in msg, (k, msg)


def test_static_prompt_budget():
    n = len(service_loop.reading_static_prompt())
    assert n <= STATIC_BUDGET, \
        f"static reading prompt is {n} chars (budget {STATIC_BUDGET})"


def test_sample_percall_prompt_budget():
    request = ("I run a small venue. Help me not oversell tickets. "
               "Nobody may take more than 8 tickets in one order.")
    # two representative, near-cap refinement transcripts (worst realistic case)
    t1 = ("stage 'reading-gate': s4: quote 'guarantee same-day refunds' does "
          "not occur in the request -- a demand may not be fabricated. ") * 8
    t2 = ("stage 'consistency': the demand set is contradictory: const bounds "
          "count<=8 and count>=10 cannot both hold in any world. ") * 10
    prompt = service_loop.reading_prompt(request, [t1, t2])
    n = len(prompt)
    assert n <= PERCALL_BUDGET, \
        f"per-call reading prompt is {n} chars (budget {PERCALL_BUDGET})"


if __name__ == "__main__":
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_"):
            _fn()
            print("PASS", _name)
    _static = len(service_loop.reading_static_prompt())
    _req = ("I run a small venue. Help me not oversell tickets. "
            "Nobody may take more than 8 tickets in one order.")
    _t = "x" * 1800
    _percall = len(service_loop.reading_prompt(_req, [_t, _t]))
    print("all prompt invariants hold")
    print(f"static_prompt_chars = {_static}")
    print(f"sample_percall_prompt_chars = {_percall}")

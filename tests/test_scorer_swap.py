#!/usr/bin/env python3
"""Z-F scorer FREEZE (WP-L) teeth -- swap speculate's flat scorer for the
macro-aware reading scorer, LLM-free and hand-planted.

Runnable under pytest AND as a bare script
(`python3 tests/test_scorer_swap.py` -> PASS lines, exit 0).

The freeze exposes ONE clean scoring seam and pins exactly three things:

  * `planner.choices.score_reading(reading, {})` is the FLAT reading DL
    byte-for-byte: it equals `mdl_macros.dl_reading(reading, {})` (and the
    None-table call agrees with the {}-table call);
  * a macro table that abbreviates a consecutive window of the reading COLLAPSES
    that window to one cheap invocation, so the macro-aware score is strictly
    LOWER than the flat score -- the compression the freeze buys;
  * speculate's ranking key `rank_score` USES that scorer: at the same stage the
    macro-aware ranking tuple is strictly lower than the flat one, and with an
    empty/None table it falls back byte-for-byte to the flat score.

Deterministic (house rule 5): no randomness, no clocks, no LLM.
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from planner import choices
from buildloop import mdl_macros
from buildloop import speculate

# --------------------------------------------------------------------------- #
# A hand-written reading whose choice tail (lifecycle + one transition) is a
# consecutive window a structural macro can abbreviate.
READING = {
    "service": "svc",
    "statements": [
        {"id": "s1", "force": "presupposition", "quote": "balance",
         "lf": {"kind": "quantity", "name": "balance", "min": 0, "max": 100}},
        {"id": "s2", "force": "presupposition", "quote": "act",
         "lf": {"kind": "action", "name": "act"}},
        {"id": "s3", "force": "choice", "quote": "",
         "lf": {"kind": "lifecycle", "states": ["open", "closed"],
                "initial": "open"}},
        {"id": "s4", "force": "choice", "quote": "",
         "lf": {"kind": "transition", "action": "act",
                "from": "open", "to": "closed"}},
    ]
}

# A macro whose body matches EXACTLY the (lifecycle, transition) tail window of
# READING: matching it collapses two statements into one cheap 0-arg invocation.
TABLE = {
    "tail": {
        "name": "tail", "params": [],
        "body": [
            {"kind": "lifecycle", "states": ["open", "closed"],
             "initial": "open"},
            {"kind": "transition", "action": "act",
             "from": "open", "to": "closed"},
        ]}}


# --------------------------------------------------------------------------- #
def test_flat_score_equals_dl_reading_empty_table():
    """score_reading(reading, {}) IS the flat reading DL, byte-for-byte, and the
    None-table call agrees with the {}-table call."""
    flat = choices.score_reading(READING, {})
    assert flat == mdl_macros.dl_reading(READING, {}), flat
    # None must equal the empty table (the freeze's flat-fallback contract).
    assert choices.score_reading(READING, None) == flat, flat


def test_macro_table_compresses_score():
    """A macro that abbreviates the reading's tail window makes the macro-aware
    score STRICTLY LOWER than the flat score (the matched window collapses to one
    invocation)."""
    flat = choices.score_reading(READING, {})
    macro = choices.score_reading(READING, TABLE)
    assert macro < flat, (macro, flat)
    # the compression is real: the reading needs one fewer statement to write.
    assert mdl_macros.statement_count(READING, TABLE) < \
        mdl_macros.statement_count(READING, {})


def test_speculate_rank_uses_scorer():
    """speculate.rank_score routes through the Z-F scorer: at the SAME stage the
    macro-aware ranking tuple is strictly lower than the flat one, and the flat
    fallback ({}/None) reproduces the flat score exactly."""
    rank_macro = speculate.rank_score(READING, TABLE)
    rank_flat = speculate.rank_score(READING, {})
    # same stage_rank (same reading, default stage) -> tuple order is the score.
    assert rank_macro[0] == rank_flat[0], (rank_macro, rank_flat)
    assert rank_macro < rank_flat, (rank_macro, rank_flat)
    # the ranking's score element is precisely the frozen Z-F scorer ...
    assert rank_flat[1] == choices.score_reading(READING, {})
    assert rank_macro[1] == choices.score_reading(READING, TABLE)
    # ... and the empty/None table falls back byte-for-byte to the flat score.
    assert speculate.rank_score(READING, None) == rank_flat


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print("PASS", _name)
    print("Z-F scorer freeze holds "
          "(flat score == dl_reading({}); a matching macro compresses the score; "
          "speculate.rank_score routes through score_reading with a flat "
          "fallback)")

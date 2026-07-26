"""The `^` refusal is DEMAND, and it reaches the demand pipeline.

THE SEAM THIS CLOSES.  `generators/math_reading.py`'s `^` branch refused
every non-literal exponent with a bare `BadMathReading`.  That exception
means MALFORMED READING -- a bug in the transcription.  Only `FragmentMiss`
carries a `missing_kind_guess`, and only `FragmentMiss` reaches
`run/formalize.certify_statement`'s `fragment-miss` event sink, which is the
AUTOMATIC half of the demand pipeline (the other half is the hand-recorded
refusal ledger, `tools/frontier_refusals.py`).

So a symbolic exponent was filed as "this reading is broken" rather than as
"the fragment is missing something", and `refusal-symbolic-exponent`'s price
could never rise no matter how much corpus was intaken.  Output that
structurally could not become input -- a break in the feedback path of a loop
whose entire premise is that measured demand prices the next purchase.

WHAT THESE TESTS PIN, AND WHY BOTH DIRECTIONS MATTER.  Relabelling
everything on that branch as demand would be the opposite defect: a malformed
reading counted as demand inflates the price list with transcriptions that
are simply wrong, and the census's honesty rules exist precisely to stop a
number from being flattered.  So the split is asserted in BOTH directions,
and the end-to-end test asserts the event actually ARRIVES rather than
merely that the exception type changed -- this file's sibling teeth have been
bitten three times by checks that matched a mention of the thing instead of
the thing.
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from generators.math_reading import (  # noqa: E402
    BadMathReading, FragmentMiss, _check_term, _check_carrier_ops)

SCOPE = {"a": "Int", "n": "Int"}


def _pow(exp):
    return {"op": "^", "args": [{"ref": "a"}, exp]}


# --------------------------------------------------------------------------
# 1. DEMAND: the reading is well formed and the FRAGMENT cannot express it.
# --------------------------------------------------------------------------

# P7 SPLIT THIS TABLE IN TWO, and the split is the purchase's shape rather than
# a bookkeeping detail.  A NEGATIVE LITERAL exponent is refusable without
# knowing any carrier -- the literal is right there -- so it stays a
# `_check_term` refusal.  A SYMBOLIC exponent is admissible at carrier `Nat` and
# refused elsewhere, and `_check_term` is carrier-blind, so its refusal moved to
# `_check_carrier_ops`, the one walk that resolves carriers.  The guess narrowed
# to match: `pow:symbolic-exponent` meant "the fragment cannot express this at
# all", which stopped being true, and `pow:symbolic-exponent@Int` is the
# residual demand that is still real (an exponent that may be negative).
#
# `where` names which walk owns each refusal, so a case cannot quietly migrate
# between them and keep passing.
DEMAND = {
    "bare symbolic exponent": (
        {"ref": "n"}, "pow:symbolic-exponent@Int", "carrier"),
    "compound symbolic exponent": (
        {"op": "+", "args": [{"ref": "n"}, {"lit": 1}]},
        "pow:symbolic-exponent@Int", "carrier"),
    "negative literal exponent": (
        {"lit": -2}, "pow:negative-exponent", "term"),
}


@pytest.mark.parametrize("name,case", sorted(DEMAND.items()))
def test_a_well_formed_inexpressible_exponent_is_demand(name, case):
    exp, guess, where = case
    with pytest.raises(FragmentMiss) as exc:
        if where == "term":
            _check_term(_pow(exp), dict(SCOPE))
        else:
            _check_carrier_ops({"op": "=", "args": [_pow(exp), {"lit": 0}]},
                               dict(SCOPE), None, "c1")
    assert exc.value.missing_kind_guess == guess, name


def test_a_symbolic_exponent_at_carrier_Nat_is_no_longer_demand():
    """The other side of the same purchase: what P7 BOUGHT.  At carrier `Nat`
    every case above is admitted rather than priced, which is why the guess
    narrowed instead of disappearing -- the demand that remains is real and the
    demand that was met is gone.  A row that kept its old price after being
    partly paid would over-price the next purchase."""
    for exp, _guess, _where in DEMAND.values():
        if "lit" in exp:                    # the negative literal is still demand
            continue
        _check_term(_pow(exp), {"a": "Nat", "n": "Nat"})
        _check_carrier_ops({"op": "=", "args": [_pow(exp), {"lit": 0}]},
                           {"a": "Nat", "n": "Nat"}, None, "c1")


def test_the_two_demand_kinds_are_kept_apart():
    """A negative exponent leaves the integer carrier; a symbolic one is an
    env-indexed family.  Different missing primitives, different purchases --
    collapsing them would price one row with the other's evidence."""
    guesses = {g for _exp, g, _where in DEMAND.values()}
    assert len(guesses) == 2, guesses


# --------------------------------------------------------------------------
# 2. NOT demand: a malformed exponent stays a malformed reading.
# --------------------------------------------------------------------------

MALFORMED = {
    "boolean literal": {"lit": True},
    "undeclared reference": {"ref": "zzz"},
    "not a term at all": ["not", "a", "dict"],
    "lit with extra keys": {"lit": 2, "extra": 1},
}


@pytest.mark.parametrize("name,exp", sorted(MALFORMED.items()))
def test_a_malformed_exponent_is_not_demand(name, exp):
    """The other direction, and the one that protects the price list: a
    transcription bug counted as demand would flatter the histogram."""
    with pytest.raises(BadMathReading) as exc:
        _check_term(_pow(exp), dict(SCOPE))
    assert not isinstance(exc.value, FragmentMiss), (
        f"{name} was filed as DEMAND; a malformed reading is not evidence "
        f"that the fragment is missing anything")


def test_a_valid_literal_exponent_still_passes():
    """The control.  Without it, every assertion above would hold on a checker
    that refused all exponents -- the flaw this repo's ksy purity test shipped
    with for one run."""
    assert _check_term(_pow({"lit": 3}), dict(SCOPE)) is None


# --------------------------------------------------------------------------
# 3. END TO END: the demand actually reaches the sink.
#    Changing the exception type proves nothing on its own -- the claim is
#    that the fragment-miss EVENT fires and carries the guess.
# --------------------------------------------------------------------------

def test_the_fragment_miss_event_fires_with_the_guess():
    """Shaped after tests/test_math_reading.py's own fixtures, so the reading
    is valid in every respect EXCEPT the exponent -- otherwise an earlier gate
    refuses it and this test would pass on the wrong refusal."""
    import json

    from run.formalize import certify_statement

    src = "let a and n be given, a to the n is zero"
    stmts = [
        {"id": "o1", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "o2", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "c1", "force": "demand", "quote": "a to the n is zero",
         "lf": {"kind": "conclusion",
                "pred": {"op": "=", "args": [_pow({"ref": "n"}), {"lit": 0}]}}},
    ]
    events = []
    res = certify_statement(src, json.dumps({"theorem": "thm",
                                             "statements": stmts}),
                            event_sink=lambda k, p: events.append((k, p)))
    assert not res.ok
    assert res.stage == "math-reading-gate", res.stage
    kinds = [k for k, _ in events]
    assert "fragment-miss" in kinds, (
        f"no fragment-miss event was emitted (saw {kinds}; error={res.error!r}) "
        f"-- the refusal never reached the demand pipeline, which is the whole "
        f"defect this file exists to close")
    payload = dict(events[kinds.index("fragment-miss")][1])
    assert payload.get("missing_kind_guess") == "pow:symbolic-exponent@Int", payload

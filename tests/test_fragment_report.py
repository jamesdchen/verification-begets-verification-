"""WP-K: the fragment-miss ranking report (F4.2).

A source construal that does not transcribe into the F1 fragment is DEMAND DATA
(F4.1), logged as a `fragment-miss` event (F-I).  The report ranks candidate LF
extensions by demand unlocked per kernel surface -- the demand-unlocked count is
read from the corpus MANIFEST's non-transcribable tags (X14), never a hardcoded
map.  Admission stays human-gated (F4.3).
"""
import tempfile
import os

import pytest

from library import Registry
import cgb


def _reg():
    return Registry(db_path=os.path.join(tempfile.mkdtemp(), "t.sqlite"))


# the three intended misses the corpus manifest marks non-transcribable.
_GUESSES = ["operator:prime", "carrier:Real", "kind:set-object"]


def test_planted_misses_appear_with_nonzero_unlock():
    reg = _reg()
    for i, g in enumerate(_GUESSES):
        reg.log_event("fragment-miss", {"source_id": f"s{i}",
                                        "span": "…", "missing_kind_guess": g})
    rows = cgb._fragment_report(reg)
    by = {r["missing_kind_guess"]: r for r in rows}
    for g in _GUESSES:
        assert g in by, f"{g} missing from report"
        assert by[g]["observed_misses"] >= 1
        # unlock count comes FROM the manifest (each guess tags one
        # non-transcribable corpus file) -- X14, not a hardcoded map.
        assert by[g]["demand_unlocked_estimate"] >= 1


def test_report_is_deterministic():
    reg = _reg()
    for g in _GUESSES:
        reg.log_event("fragment-miss", {"source_id": "x", "span": "y",
                                        "missing_kind_guess": g})
    assert cgb._fragment_report(reg) == cgb._fragment_report(reg)


def test_ranking_is_by_unlock_then_misses():
    reg = _reg()
    # operator:prime gets three observed misses; the others one each.  All three
    # unlock exactly one manifest file, so the tie breaks on observed misses.
    for _ in range(3):
        reg.log_event("fragment-miss", {"source_id": "a", "span": "b",
                                        "missing_kind_guess": "operator:prime"})
    for g in ("carrier:Real", "kind:set-object"):
        reg.log_event("fragment-miss", {"source_id": "a", "span": "b",
                                        "missing_kind_guess": g})
    rows = cgb._fragment_report(reg)
    # every row with a positive unlock precedes any with zero; within equal
    # unlock, more observed misses ranks first.
    unlocked = [r for r in rows if r["demand_unlocked_estimate"] > 0]
    assert unlocked[0]["missing_kind_guess"] == "operator:prime"


def test_unlock_zero_for_kind_not_in_manifest():
    reg = _reg()
    reg.log_event("fragment-miss", {"source_id": "a", "span": "b",
                                    "missing_kind_guess": "operator:bogus"})
    by = {r["missing_kind_guess"]: r for r in cgb._fragment_report(reg)}
    # a guessed kind with no matching non-transcribable manifest entry unlocks
    # nothing (the estimate is manifest-derived, X14).
    assert by["operator:bogus"]["demand_unlocked_estimate"] == 0


def test_empty_report_does_not_crash():
    rows = cgb._fragment_report(_reg())
    # even with no events, the manifest's non-transcribables appear as candidates.
    assert all(r["observed_misses"] == 0 for r in rows)

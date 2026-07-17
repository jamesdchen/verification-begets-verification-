"""Teeth for WP-T3-CK -- the op-signature-skeleton cluster key + force-only math
windows (COMPRESSION.md §11.9 FI-W1-3 / §11.10 follow-up).

Two layers:
  * UNIT teeth over hand-built readings: the skeleton is deterministic and
    single-sourced from math_reading.op_signature; force-only math windows form
    where strict-quote windows did not; the skeleton separates the congruence
    family from generic (hyp,hyp) noise yet keeps even/odd together; legacy mode
    is byte-identical (including the pinned service digest).
  * MEASURED teeth (the acceptance criteria a-e) via tools.measure_cluster_key
    over the FROZEN checkpoint.  These re-run the harness that gets re-measured
    at merge against the grown corpus: mostly relational (refined < baseline;
    congruence body reached; even/odd covered; <= MAX_MACROS; service byte-
    identical), plus the WP-FLIP (§12.1) census-of-record REPRODUCTION pins (the
    post-flip refined+GC value 2377.0 and the GC pass's -9.0 effect) -- pinned
    because reproducing the committed census-of-record IS the point of the flip.

Deterministic, LLM-free.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import common                                                    # noqa: E402
from buildloop import recurrence                                 # noqa: E402
from generators import math_reading                              # noqa: E402
from tools import measure_cluster_key as mck                     # noqa: E402


def _math_stmt(kind, op, args, force="demand", quote="q", sid="x"):
    return {"id": sid, "force": force, "quote": quote,
            "lf": {"kind": kind, "pred": {"op": op, "args": args}}}


def _refs(*names):
    return [{"ref": n} for n in names]


def _mod(a, b):
    return {"op": "mod", "args": _refs(a, b)}


# ============================================================ UNIT: the skeleton
def test_skeleton_is_single_sourced_from_op_signature():
    # the top-level op-kind IS op_signature (carrier frozenset -> sorted tuple),
    # nothing tuned or hand-tabled.
    lf = {"kind": "hypothesis", "pred": {"op": "dvd", "args": _refs("a", "b")}}
    top, args = recurrence._stmt_op_skeleton(lf)
    role, arity, carrier = math_reading.op_signature("dvd")
    assert top == (role, arity, tuple(sorted(carrier)))
    assert args == (("ref",), ("ref",))
    # a non-pred LF (object/quantifier/ambient) has no skeleton.
    assert recurrence._stmt_op_skeleton({"kind": "object", "name": "n"}) is None
    # an unknown op degrades to None-kind, deterministically (no crash).
    assert recurrence._op_kind("frobnicate") is None


def test_skeleton_keeps_evenodd_together_but_splits_congruence():
    # even and odd share a skeleton (op SIGNATURES, not words, key it) ...
    ev = recurrence._stmt_op_skeleton(
        {"kind": "hypothesis", "pred": {"op": "even", "args": _refs("a")}})
    od = recurrence._stmt_op_skeleton(
        {"kind": "hypothesis", "pred": {"op": "odd", "args": _refs("b")}})
    assert ev == od                       # same skeleton up to the slot op
    # ... but the congruence hypothesis `=`(mod, mod) keys AWAY from a bare
    # `dvd(a,b)` (both pred/2/{Nat,Int} at the top, different depth-1 arg kinds).
    cong = recurrence._stmt_op_skeleton(
        {"kind": "hypothesis", "pred": {"op": "=", "args": [_mod("a", "m"),
                                                            _mod("b", "m")]}})
    dvd = recurrence._stmt_op_skeleton(
        {"kind": "hypothesis", "pred": {"op": "dvd", "args": _refs("a", "b")}})
    assert cong != dvd
    # and the congruence conclusion's varying inner op (+/*/-) sits BELOW the
    # one-level horizon, so all three congruence conclusions share a skeleton
    # (=> the inner op anti-unifies to the slot, not a cluster split).
    concl = [recurrence._stmt_op_skeleton(
        {"kind": "conclusion", "pred": {"op": "=", "args": [
            {"op": "mod", "args": [{"op": inner, "args": _refs("a", "c")},
                                   {"ref": "m"}]},
            {"op": "mod", "args": [{"op": inner, "args": _refs("b", "d")},
                                   {"ref": "m"}]}]}})
        for inner in ("+", "*", "-")]
    assert concl[0] == concl[1] == concl[2]


def test_cluster_key_math_refined_vs_legacy():
    lfs = [{"kind": "hypothesis", "pred": {"op": "even", "args": _refs("a")}},
           {"kind": "hypothesis", "pred": {"op": "even", "args": _refs("b")}}]
    win = (0, 1)
    legacy = recurrence._cluster_key(win, lfs, "legacy")
    refined = recurrence._cluster_key(win, lfs, "refined")
    assert legacy == (2, ("hypothesis", "hypothesis"))          # width, kinds
    assert refined[:2] == legacy and len(refined) == 3          # + skeleton tuple
    # every key is canonical-json serializable (the miner sorts clusters by it).
    assert common.canonical_json(refined)


def test_cluster_key_service_untouched_in_both_modes():
    # a service (non-math) window keeps the legacy 2-tuple key in refined mode.
    lfs = [{"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}},
           {"kind": "bound", "action": "a"}]
    assert recurrence._cluster_key((0, 1), lfs, "legacy") == \
        recurrence._cluster_key((0, 1), lfs, "refined")


# ============================================================ UNIT: the windows
def test_forceonly_math_window_forms_where_strict_did_not():
    # two adjacent demand hypotheses with DIFFERENT quotes: strict (legacy) mode
    # proposes no window; refined force-only math mode proposes exactly one.
    mr = {"theorem": "t", "statements": [
        _math_stmt("hypothesis", "even", _refs("a"), quote="alpha"),
        _math_stmt("hypothesis", "odd", _refs("b"), quote="beta")]}
    assert recurrence._is_math_domain(mr["statements"]) is True
    assert recurrence._demand_windows(mr, 4, math_mode="legacy") == []
    wins = recurrence._demand_windows(mr, 4, math_mode="refined")
    assert len(wins) == 1 and len(wins[0]) == 2


def test_forceonly_still_respects_force_boundary():
    # force-only relaxes QUOTE, never FORCE: a demand/presupposition boundary
    # still splits the window in refined mode.
    mr = {"theorem": "t", "statements": [
        _math_stmt("hypothesis", "even", _refs("a"), force="demand", quote="q"),
        _math_stmt("hypothesis", "odd", _refs("b"), force="presupposition",
                   quote="q")]}
    assert recurrence._demand_windows(mr, 4, math_mode="refined") == []


def test_service_windows_strict_in_both_modes():
    # SERVICE domain is strict-(force, quote) in BOTH modes (byte-identity pin):
    # a mixed-quote service window is never proposed, refined or not.
    from tests import fixtures_macro_corpora as fx
    mixed = fx.mixed_quote_reading()
    assert recurrence._is_math_domain(recurrence._statements(mixed)) is False
    assert recurrence._demand_windows(mixed, 4, math_mode="legacy") == []
    assert recurrence._demand_windows(mixed, 4, math_mode="refined") == []


def test_legacy_mine_byte_identical_and_service_pin_holds():
    # (d) legacy mode is byte-identical to the committed miner, and the service
    # corpus mines byte-identically in BOTH modes (the pinned digest).
    from tests import fixtures_macro_corpora as fx
    svc = [fx._reading("r1", "ABCD"), fx._reading("r2", "ABCD")]
    d_legacy = common.sha256_json(recurrence.mine(svc, {}, math_mode="legacy"))[:16]
    d_refined = common.sha256_json(recurrence.mine(svc, {}, math_mode="refined"))[:16]
    assert d_legacy == d_refined == "b9f1f0b9bb198732"
    # default arg is legacy.
    assert recurrence.mine(svc, {}) == recurrence.mine(svc, {}, math_mode="legacy")


# ==================================================== MEASURED: acceptance a-d
def _measured():
    if not hasattr(_measured, "_c"):
        _measured._c = mck.measure()
    return _measured._c


def test_a_refined_strictly_beats_baseline():
    m = _measured()
    ref = m["governed"]["refined"]["corpus_dl"]            # census-of-record (post-GC)
    base = m["governed"]["legacy"]["corpus_dl"]
    # WP-FLIP: baseline is the FROZEN PRE-FLIP census-of-record (legacy), carried
    # as lineage and REPRODUCED by the legacy replay (2139.0 -> 2920.0 at WP-AUTH
    # growth).  The harness compares refined against this frozen legacy value,
    # never against a refined baseline.
    assert base == m["baseline_governed_dl"] == 2920.0
    assert ref < base                                      # strictly better
    assert ref <= m["acceptance_bars"]["max_dl"]           # a real harvest
    assert m["verdicts"]["a_beats_baseline"] is True
    # acceptance = the post-flip census-of-record REPRODUCES its committed value
    # (reproduced live from the refined+GC re-mine, not assumed).
    assert ref == m["census_of_record_dl"] == 2377.0
    assert m["verdicts"]["a_reproduces_census_of_record"] is True


def test_a_congruence_body_reached_by_greedy_then_gc_retires_it():
    # the mechanism: the greedy refined path admits the EXACT body the census
    # could only reach counterfactually.  On the frozen 37-reading corpus its
    # realized marginal was the census's -179; on the grown 46-reading corpus
    # the FINAL-TABLE marginal flipped to +7.0 -- H19 admission-order drift
    # (it paid at admission; later admissions stole occurrences).  WP-FLIP §12.1
    # ADJUDICATED this by landing the re-mine-time GC pass: reached-by-greedy at
    # +7.0, then retired by the non-negative-marginal law -- the pricing law
    # working, not a failure.
    c = _measured()["congruence_macro"]
    assert c["reached_by_greedy"] is True
    assert c["uses"] >= 2
    assert c["realized_marginal_delta"] == 7.0
    assert c["retired_by_gc"] is True


def test_a_gc_pass_retires_only_nonnegative_marginal_macros():
    # the §12.1 GC pass is a LAW (retire iff realized_marginal_delta >= 0,
    # threshold 0 -- no tuned constant), applied to ALL macros uniformly.  Its
    # measured effect: refined greedy 2386.0 -> census-of-record 2377.0 (-9.0),
    # retiring exactly the two macros whose final-table marginal is >= 0 (the
    # congruence macro at +7 and the object/quantifier macro at +2).
    m = _measured()
    gc = m["gc_pass"]
    assert gc["governed_dl_before_gc"] == 2386.0           # refined greedy
    assert gc["governed_dl_after_gc"] == 2377.0            # census-of-record
    assert gc["gc_delta"] == -9.0
    assert m["governed"]["refined_greedy"]["corpus_dl"] == 2386.0
    assert m["governed"]["refined"]["corpus_dl"] == 2377.0
    # every retired macro genuinely had a non-negative realized marginal at the
    # GREEDY final table (the law is uniform, not a per-macro carve-out).
    greedy = {mm["name"]: mm for mm in m["governed"]["refined_greedy"]["macros"]}
    for name in gc["retired"]:
        assert name in greedy
    assert len(gc["retired"]) == 2


def test_a_congruence_windows_unblocked():
    # the pass-3 blocker (0 demand windows over the congruence cluster) is lifted
    # under force-only math windows.
    w = _measured()["congruence_windows"]
    assert w["legacy"] == 0
    assert w["refined"] > 0


def test_b_evenodd_macro_survives_and_covers():
    e = _measured()["evenodd_macro"]
    assert e["op_slot_arities"] == [1]        # pred/1 => {even, odd} only
    assert e["uses"] >= 2
    assert set(e["covers"]) == {"04_even_plus_even", "05_odd_plus_odd"}
    assert _measured()["verdicts"]["b_evenodd_survives"] is True


def test_c_no_macro_count_explosion():
    m = _measured()
    assert m["governed"]["refined"]["count"] <= m["acceptance_bars"]["max_macros"]
    assert m["verdicts"]["c_no_macro_explosion"] is True


def test_d_service_byte_identical_measured():
    m = _measured()
    sd = m["service_digest"]
    assert sd["legacy"] == sd["refined"] == sd["pinned"]
    assert m["verdicts"]["d_service_byte_identical"] is True


def test_e_ungoverned_reported_and_not_worse():
    # (e) the ungoverned arm is measured alongside; the refined key helps it too
    # (a sanity relation, not an acceptance bar).
    m = _measured()
    assert m["ungoverned"]["legacy"]["corpus_dl"] == 3208.0   # grown corpus
    assert m["ungoverned"]["refined"]["corpus_dl"] <= \
        m["ungoverned"]["legacy"]["corpus_dl"]


def test_measure_json_byte_stable():
    a = mck.render_json(mck.measure())
    b = mck.render_json(mck.measure())
    assert a == b


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all cluster-key teeth pass")

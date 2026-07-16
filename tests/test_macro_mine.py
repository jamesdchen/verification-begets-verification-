"""Teeth for the S1 miner filters and searched admission (WP-E + WP-J).

Deterministic, LLM-free, no external tools -- everything runs over the planted
corpora in tests/fixtures_macro_corpora.py through buildloop.recurrence /
buildloop.mdl_macros only.

Covers:
  * H3  -- the concreteness filter rejects a bare-wildcard candidate the pre-H3
           gate would have minted.
  * H2  -- windows are uniform (force, quote); a mixed-quote window is not mined.
  * S1.3 trap -- the searched admission sequence is STRICTLY cheaper than the
           greedy one-max-saving-per-step baseline on the planted trap.
  * S1.3 never-worse -- searched <= greedy everywhere.
  * part_c -- nothing is admitted on the incompressible corpus.
  * Z1  -- every macro the search admits independently passes the explicit
           macro_admission_decision gate.
"""
from buildloop import recurrence, mdl_macros
from buildloop.mdl_macros import corpus_dl, macro_admission_decision
from tests import fixtures_macro_corpora as fx


# ------------------------------------------------------------------ H3 filter
def test_h3_rejects_bare_wildcard_body():
    assert recurrence._body_admissible(["$p0", "$p1"]) is False
    # a mostly-concrete parametric body is fine (only the varying leaf is a param)
    assert recurrence._body_admissible(
        [{"kind": "always", "pred": {"op": ">=", "left": "$p0", "right": 0}}])


def test_h3_wildcard_corpus_mines_nothing_but_would_without_filter():
    corpus = fx.wildcard_corpus()
    assert recurrence.mine(corpus, {}) == []          # H3 removes the wildcard
    # prove the wildcard is exactly what the pre-H3 gate would have minted
    saved = recurrence._body_admissible
    recurrence._body_admissible = lambda body: True
    try:
        raw = recurrence.mine(corpus, {})
    finally:
        recurrence._body_admissible = saved
    assert len(raw) == 1 and raw[0]["candidate"]["body"] == ["$p0", "$p1"]


# ------------------------------------------------------------------ H2 windows
def test_h2_mixed_quote_window_not_mined():
    assert recurrence._demand_windows(fx.mixed_quote_reading(), 4) == []


def test_h2_uniform_window_is_mined():
    r = {"service": "u", "statements": [
        {"id": "s0", "force": "demand", "quote": "same",
         "lf": {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}},
        {"id": "s1", "force": "demand", "quote": "same",
         "lf": {"kind": "bound", "action": "a", "left": "n",
                "cmp": "<=", "right": "q"}}]}
    wins = recurrence._demand_windows(r, 4)
    assert len(wins) == 1 and len(wins[0]) == 2


# --------------------------------------------------------------- searched trap
def _greedy(corpus):
    return recurrence.searched_macro_sequence(corpus, {}, beam_width=1,
                                              max_depth=6)


def _searched(corpus):
    return recurrence.searched_macro_sequence(corpus, {}, beam_width=10,
                                              max_depth=6)


def test_trap_searched_strictly_beats_greedy():
    corpus = fx.trap_corpus()
    g, s = _greedy(corpus), _searched(corpus)
    gt = corpus_dl(corpus, g)["total"]
    st = corpus_dl(corpus, s)["total"]
    assert st < gt                       # STRICT: the trap is escaped
    assert len(g) == 1                   # greedy stranded on the len-4 macro
    assert len(s) == 2                   # searched admits the better pair {B, C}


def test_searched_never_worse_than_greedy():
    for corpus in (fx.trap_corpus(), fx.incompressible_corpus()):
        gt = corpus_dl(corpus, _greedy(corpus))["total"]
        st = corpus_dl(corpus, _searched(corpus))["total"]
        assert st <= gt


def test_incompressible_admits_nothing():
    corpus = fx.incompressible_corpus()
    assert recurrence.mine(corpus, {}) == []
    assert recurrence.searched_macro_sequence(
        corpus, {}, beam_width=6, max_depth=4) == {}


def test_searched_macros_each_pass_the_explicit_gate():
    # Z1: rebuild the winning table one macro at a time; each admission must be
    # independently justified by the MDL gate against the table so far.
    corpus = fx.trap_corpus()
    winner = _searched(corpus)
    table = {}
    for name in sorted(winner):
        cand = winner[name]
        assert macro_admission_decision(corpus, cand, table)["admit"]
        table[name] = cand


# ============================================================ WP-T3-REAL teeth
# FI-W1-3 (COMPRESSION.md §11.9 / §11.3), SLOT-TYPING HALF ONLY.  The window-rule
# half (math-domain force-only relaxation) was measured to REGRESS the greedy
# governed corpus_dl (+29, 2139->2168) with its -179 congruence gain staying
# counterfactual, so it is HELD (see recurrence._demand_windows) -- the window
# rule is uniform-(force, quote) for BOTH domains.  What landed is the pure
# honesty restriction: op-slot semantic typing.  `_is_math_domain` survives
# because it now gates slot typing to math bodies (no longer the window rule).
# Deterministic, LLM-free, over hand-built readings.
import common                                                     # noqa: E402
from generators import math_reading                               # noqa: E402


def _math_hyp(op, args, force="demand", quote="q"):
    return {"id": "x", "force": force, "quote": quote,
            "lf": {"kind": "hypothesis", "pred": {"op": op, "args": args}}}


def _refs(*names):
    return [{"ref": n} for n in names]


# ---------------------------------- window rule uniform-(force,quote) both domains
def test_window_rule_quote_uniform_for_both_domains():
    # SERVICE: a mixed-quote, same-force window is NOT proposed (quotes gate
    # membership) -- byte-identical to before.
    assert recurrence._demand_windows(fx.mixed_quote_reading(), 4) == []
    # MATH: the FI-W1-3 force-only relaxation is HELD, so a math reading whose two
    # adjacent demand statements DIFFER in quote ALSO yields NO window -- the same
    # strict rule as service.  (`_is_math_domain` still classifies it as math for
    # the slot-typing gate below; it just no longer relaxes the window rule.)
    mr = {"theorem": "t", "statements": [
        _math_hyp("even", _refs("a"), quote="alpha"),
        _math_hyp("odd", _refs("b"), quote="beta")]}
    assert recurrence._is_math_domain(mr["statements"]) is True
    assert recurrence._demand_windows(mr, 4) == []      # quote boundary splits


def test_math_force_uniformity_retained():
    # FORCE uniformity holds for math too: a demand/presupposition boundary
    # splits the window (independently of the quotes, which here agree).
    mr = {"theorem": "t", "statements": [
        _math_hyp("even", _refs("a"), force="demand", quote="same"),
        _math_hyp("odd", _refs("b"), force="presupposition", quote="same")]}
    assert recurrence._is_math_domain(mr["statements"]) is True
    assert recurrence._demand_windows(mr, 4) == []      # force boundary splits


def test_service_mining_byte_identity_pin():
    # (c): the service mining path is pinned byte-for-byte -- `mine` over a
    # service corpus is unchanged by the T3 package.  Captured against the
    # pre-change output (canonical digest), so any future drift in the service
    # branch fails here loudly.
    corpus = [fx._reading("r1", "ABCD"), fx._reading("r2", "ABCD")]
    out = recurrence.mine(corpus, {})
    # canonical digest pinned against the pre-change (strict-rule) output.
    assert common.sha256_json(out)[:16] == "b9f1f0b9bb198732"
    # relational identity: every window a service reading yields is quote-uniform
    # (the strict invariant), for both readings.
    for r in corpus:
        for w in recurrence._demand_windows(r, 4):
            quotes = {s.get("quote", "") for s in w}
            assert len(quotes) == 1
    # exact structural pin: the six mined candidates and their savings.
    assert [(c["candidate"]["name"], c["dl_saving"], c["uses"]) for c in out] == [
        ("m_32407b3f587a", 35.0, 2), ("m_2be002bfc461", 28.0, 2),
        ("m_499a075ea135", 25.0, 2), ("m_d8ce4b965acd", 18.0, 2),
        ("m_44787ef8d9c8", 16.0, 2), ("m_584572a516fa", 14.0, 2)]


# ---------------------------------------------- slot typing (T3 proper, §11.9)
def test_op_slot_congruence_and_evenodd_admitted():
    # A congruence-style op-slot ranging over {+, *, -} (all term, arity 2,
    # carrier {Nat, Int}) is admissible; likewise even/odd (pred, arity 1).
    occ = [[{"kind": "conclusion",
             "pred": {"op": op, "args": _refs("a", "c")}}]
           for op in ("+", "*", "-")]
    body, params = recurrence._antiunify_windows(occ)
    assert recurrence._op_slot_params(body) == {"p0": 2}
    assert recurrence._op_slots_admissible(body, params, occ) is True

    eo = [[{"kind": "hypothesis", "pred": {"op": op, "args": _refs("a")}}]
          for op in ("even", "odd")]
    b, p = recurrence._antiunify_windows(eo)
    assert recurrence._op_slots_admissible(b, p, eo) is True


def test_op_slot_role_incompatible_refused():
    # (b): a planted op-slot whose bindings are role-incompatible -- dvd (pred)
    # vs mod (term), SAME arity 2 -- is REFUSED.  (=/dvd, the §11.9 example, are
    # both pred/arity-2/{Nat,Int} and would NOT be a refusal; the tables say so,
    # so a genuinely incompatible pair is used instead.)
    assert math_reading.op_signature("dvd")[0] != math_reading.op_signature("mod")[0]
    occ = [[{"kind": "hypothesis", "pred": {"op": op, "args": _refs("a", "b")}}]
           for op in ("dvd", "mod")]
    body, params = recurrence._antiunify_windows(occ)
    assert recurrence._op_slot_params(body) == {"p0": 2}
    assert recurrence._op_slots_admissible(body, params, occ) is False


def test_op_slot_carrier_incompatible_refused():
    # carrier-support incompatibility: coprime is Nat-only, dvd is {Nat, Int};
    # same role (pred) and arity (2), yet the slot is REFUSED.
    assert (math_reading.op_signature("coprime")[2]
            != math_reading.op_signature("dvd")[2])
    occ = [[{"kind": "hypothesis", "pred": {"op": op, "args": _refs("a", "b")}}]
           for op in ("coprime", "dvd")]
    body, params = recurrence._antiunify_windows(occ)
    assert recurrence._op_slots_admissible(body, params, occ) is False


def test_op_slot_unknown_op_refused():
    # an unknown op word (outside the lexicon and builtins) is incompatible.
    assert math_reading.op_signature("frobnicate") is None
    occ = [[{"kind": "hypothesis", "pred": {"op": op, "args": _refs("a", "b")}}]
           for op in ("dvd", "frobnicate")]
    body, params = recurrence._antiunify_windows(occ)
    assert recurrence._op_slots_admissible(body, params, occ) is False


def test_op_slot_typing_math_only_service_untouched():
    # slot typing applies ONLY to math-domain bodies; a service body with a
    # $-param at an op position is not subjected to the math op tables (whose
    # vocabulary is disjoint) -- so the service branch cannot be broken by it.
    svc_body = [{"kind": "always", "pred": {"op": "$p0", "args": _refs("q")}}]
    assert recurrence._is_math_domain([{"lf": t} for t in svc_body]) is False
    assert recurrence._op_slots_admissible(svc_body, ["p0"], [
        [{"kind": "always", "pred": {"op": ">=", "args": _refs("q")}}]]) is True


def test_slot_pricing_unchanged_one_token_per_param():
    # the log2|vocab| re-pricing is NOT implemented: an op-slot param prices the
    # same 1 token as any other param (dl_macro charges +1 per param name).
    body = [{"kind": "conclusion", "pred": {"op": "$p0", "args": _refs("a", "c")}}]
    m1 = {"name": "m", "params": ["p0"], "body": body}
    m0 = {"name": "m", "params": [], "body": body}
    assert mdl_macros.dl_macro(m1) - mdl_macros.dl_macro(m0) == 1.0


if __name__ == "__main__":
    for fn in list(globals().values()):
        if callable(fn) and getattr(fn, "__name__", "").startswith("test_"):
            fn()
    print("all macro-mine teeth pass")

"""Teeth for the Z-E witness discipline (WP-K, S5.2/S5.3).

Fixed, deterministic, LLM-free.  The rule under test: *dreams propose, only real
witnesses decide*.  `mine`, `macro_admission_decision`, and `gc_macros` all
accept an additive `witness_filter` predicate; when set they restrict the
readings that price the corpus (and count as witnesses) to those satisfying it
-- here the real, exogenous-origin readings.  A statement cluster witnessed only
by dream (system-origin) readings is therefore mined-but-REFUSED, and only flips
to admitted once real witnesses carry it.

Corpora are lists of reading dicts
`{"service","origin","statements":[{"id","force","quote","lf"}]}`.  Every window
statement shares force AND quote (uniform-(force, quote), the H2 honesty rule),
and distinct LF kinds per window position keep clusters clean.  The extra
`origin` key is ignored by mine/corpus_dl (they read only `r["statements"]`).
"""
import os
import tempfile

import common
from buildloop import recurrence, mdl_macros
from library import Registry

# the S5 witness predicate: real == exogenous-origin, dream == system-origin.
EXO = lambda r: r.get("origin") == "exogenous"


# ------------------------------------------------------------- LF builders
def _lf_a():
    # distinct-kind window position 0
    return {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}


def _lf_b():
    # distinct-kind window position 1
    return {"kind": "bound", "action": "a", "left": "n", "cmp": "<=", "right": "q"}


def _filler(tag):
    # a non-shared demand statement used only to perturb dream readings
    return {"kind": "effect", "action": "act", "quantity": "q",
            "op": "dec", "amount": {"arg": tag}}


def _bound(action, left, cmp_, right):
    return {"kind": "bound", "action": action, "left": left,
            "cmp": cmp_, "right": right}


def _stmt(sid, lf, force="demand", quote="s"):
    return {"id": sid, "force": force, "quote": quote, "lf": lf}


def _pattern_stmts(prefix):
    """The clean 2-statement uniform-(force, quote) demand cluster over
    distinct-kind LFs -- identical content, so it anti-unifies to a fully
    concrete (H3-passing) body with no parameters."""
    return [_stmt(f"{prefix}0", _lf_a()), _stmt(f"{prefix}1", _lf_b())]


def _reading(service, origin, statements):
    return {"service": service, "origin": origin, "statements": statements}


def _real_singleton(name):
    """A real reading carrying no mineable 2-window."""
    return _reading(name, "exogenous",
                    [_stmt(f"{name}a", {"kind": "action", "name": "go"},
                           force="choice", quote="")])


# ------------------------------------------------------------- corpora
def _dream_only_corpus():
    """The pattern in 3 DREAM (system) readings, 0 REAL witnesses; two real
    readings carry no mineable window."""
    return [_reading("d1", "system", _pattern_stmts("d1")),
            _reading("d2", "system", _pattern_stmts("d2")),
            _reading("d3", "system", _pattern_stmts("d3")),
            _real_singleton("r1"),
            _real_singleton("r2")]


def _flipped_corpus():
    """The same 3 dream witnesses PLUS the pattern hand-added to 2 REAL readings
    -- now there are real witnesses for the exogenous filter to admit."""
    return [_reading("d1", "system", _pattern_stmts("d1")),
            _reading("d2", "system", _pattern_stmts("d2")),
            _reading("d3", "system", _pattern_stmts("d3")),
            _reading("r1", "exogenous", _pattern_stmts("r1")),
            _reading("r2", "exogenous", _pattern_stmts("r2"))]


def _pattern_candidate():
    """The macro definition for the planted pattern, obtained by mining the
    dream corpus WITHOUT the filter (dreams alone are enough to PROPOSE it).
    Its body/name depend only on the (identical) window content, so it is the
    same candidate the real readings mine after the flip."""
    cands = recurrence.mine(_dream_only_corpus(), {})
    assert cands, "sanity: the planted pattern must mine without a witness filter"
    return cands[0]["candidate"]


def _reg():
    return Registry(db_path=os.path.join(tempfile.mkdtemp(), "reg.sqlite"))


def _gc_setup():
    """A stranded-macro scenario (mirrors test_scheduler): macro A=[s1,s2] is
    shadowed by the longer B=[s1,s2,s3] under greedy longest-first rewriting, so
    A drops below two uses and its ablation strictly reduces DL -> A is retired.
    Returns (registry, readings) with origin-tagged readings."""
    reg = _reg()
    s1, s2, s3 = (_bound("a", "x", "<=", 1), _bound("b", "y", "<=", 2),
                  _bound("c", "z", "<=", 3))
    stmts = [_stmt("s1", s1), _stmt("s2", s2), _stmt("s3", s3)]
    readings = [_reading("svc", "exogenous", stmts),
                _reading("svc2", "exogenous", stmts)]
    reg.macro_add("A", common.canonical_json(
        {"name": "A", "params": [], "body": [s1, s2]}))
    reg.macro_add("B", common.canonical_json(
        {"name": "B", "params": [], "body": [s1, s2, s3]}))
    return reg, readings


# ============================================================ default-None
# byte-identity: witness_filter defaulting to None (omitted) must behave exactly
# as `witness_filter=lambda r: True` (an all-pass filter changes no reading).
def test_default_none_byte_identical_mine():
    corpus = _flipped_corpus()
    omitted = recurrence.mine(corpus)
    all_pass = recurrence.mine(corpus, witness_filter=lambda r: True)
    assert omitted != []                                  # non-vacuous
    assert common.canonical_json(omitted) == common.canonical_json(all_pass)


def test_default_none_byte_identical_admission():
    corpus = _flipped_corpus()
    cand = _pattern_candidate()
    omitted = mdl_macros.macro_admission_decision(corpus, cand)
    all_pass = mdl_macros.macro_admission_decision(
        corpus, cand, witness_filter=lambda r: True)
    assert omitted["admit"] is True                       # non-vacuous
    assert common.canonical_json(omitted) == common.canonical_json(all_pass)


def test_default_none_byte_identical_gc():
    reg_a, readings_a = _gc_setup()
    reg_b, readings_b = _gc_setup()
    retired_omitted = recurrence.gc_macros(reg_a, readings_a)
    retired_all_pass = recurrence.gc_macros(
        reg_b, readings_b, witness_filter=lambda r: True)
    assert retired_omitted == retired_all_pass == ["A"]   # non-vacuous
    assert sorted(reg_a.macro_table()) == sorted(reg_b.macro_table()) == ["B"]


# =================================================================== teeth
def test_dream_only_pattern_mined_but_refused_under_witness_filter():
    corpus = _dream_only_corpus()
    # PROPOSE: the dream witnesses alone are enough to mine the pattern...
    assert recurrence.mine(corpus, {}) != []
    # DECIDE: ...but with only real witnesses counting, nothing is admissible.
    assert recurrence.mine(corpus, {}, witness_filter=EXO) == []
    cand = _pattern_candidate()
    dec = mdl_macros.macro_admission_decision(corpus, cand, witness_filter=EXO)
    assert dec["admit"] is False
    assert dec["uses"] == 0                                # no real witnesses


def test_flip_to_real_witnesses_admits_the_same_candidate():
    corpus = _flipped_corpus()
    cand = _pattern_candidate()
    mined = recurrence.mine(corpus, {}, witness_filter=EXO)
    assert mined != [] and mined[0]["candidate"] == cand   # same body/name
    assert mined[0]["uses"] == 2                            # the 2 real witnesses
    dec = mdl_macros.macro_admission_decision(corpus, cand, witness_filter=EXO)
    assert dec["admit"] is True
    assert dec["uses"] >= 2


def test_witness_filtered_mine_invariant_to_dream_perturbation():
    """Objective-side invariance: because the filter drops dream readings before
    any pricing, changing the dreams' NON-SHARED statements cannot move the
    witness-filtered mine() result."""
    reals = [_reading("r1", "exogenous", _pattern_stmts("r1")),
             _reading("r2", "exogenous", _pattern_stmts("r2"))]

    def dream(name, tag):
        return _reading(name, "system",
                        _pattern_stmts(name) + [_stmt(f"{name}f", _filler(tag))])

    v1 = reals + [dream("d1", "x"), dream("d2", "y"), dream("d3", "z")]
    v2 = reals + [dream("d1", "PERTURBED_1"), dream("d2", "PERTURBED_2"),
                  dream("d3", "PERTURBED_3")]
    m1 = recurrence.mine(v1, {}, witness_filter=EXO)
    m2 = recurrence.mine(v2, {}, witness_filter=EXO)
    assert m1 != []                                        # non-vacuous
    assert common.canonical_json(m1) == common.canonical_json(m2)


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"ok {_name}")
    print("all witness-filter teeth pass")

"""Teeth for tools/blueprint_census.py (the 'faithfully stated' MVP scaffold).

LLM-free, Lean-free, network-free.  The fixture nodes below are SYNTHETIC
(authored for this test, in blueprint-node shape) -- they are NOT quotes from
any real blueprint; the real-corpus run is a fetch + one command wherever
network egress allows.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.blueprint_census import (
    FORWARD_LOOKING, MISS_SIGNALS, _FRAGMENT_WORDS, _fragment_hits, _signals,
    census, census_node, render_md,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIXTURE = [
    # in-fragment arithmetic: no miss signal, fragment vocabulary present.
    {"label": "fix:dvd-sum", "kind": "lemma",
     "prose": "If d divides a and d divides b then d divides a + b, for "
              "natural numbers a, b, d.",
     "lean_names": ["dvd_add"]},
    # entropy/probability: the PFR-shaped out-of-fragment class.  Names BOTH
    # split signals (entropy-log via "entropy"; probability-mass via "random
    # variables") -- the split narrows attribution without demoting the miss.
    {"label": "fix:ent-subadd", "kind": "lemma",
     "prose": "The entropy of a pair of random variables is at most the sum "
              "of their entropies.",
     "lean_names": ["entropy_pair_le"]},
    # rational-mass probability WITHOUT the log: the P3-un-blockable slice,
    # probability-mass ONLY (no entropy-log signal).
    {"label": "fix:fair-die", "kind": "lemma",
     "prose": "For two independent random variables the probability of the "
              "joint outcome is the product of the marginal probabilities.",
     "lean_names": []},
    # group theory: a second, distinct miss category.  Typeclass-parametric
    # ("vector space" over an unnamed field), so it carries the P4 sub-signal
    # `algebra-abstract` ON TOP OF `algebra-structures` -- additive, the way
    # probability-mass/entropy-log overlap.
    {"label": "fix:torsion", "kind": "definition",
     "prose": "An elementary abelian group of exponent two is a vector space "
              "over the field with two elements.",
     "lean_names": []},
    # the CONCRETE algebra counterpart: a statement about one finite field,
    # which is exactly what PLAN_FRAGMENT §4 P4's `ZMod n` carrier targets.
    # algebra-structures ONLY -- the sub-signal must not swallow it, or P4's
    # re-census delta would under-count what the carrier bought.
    {"label": "fix:mult-cyclic", "kind": "theorem",
     "prose": "The multiplicative group of the finite field with q elements "
              "is cyclic of order q-1.",
     "lean_names": []},
    # the \mathbb-spacing tooth: plasTeX emits `\mathbb {H}` WITH A SPACE, so
    # this node's only entropy signal is reachable through the fold in
    # `_signals`.  Deliberately written with parentheses, not `H[`, so no
    # other entropy-log term can rescue the match.
    {"label": "fix:spaced-entropy", "kind": "lemma",
     "prose": "The quantity \\(\\mathbb {H}(X)\\) is subadditive.",
     "lean_names": []},
    # prose the census recognizes in neither direction.
    {"label": "fix:opaque", "kind": "remark",
     "prose": "This chapter fixes notation.", "lean_names": []},
]


def test_verdicts_and_histogram():
    rep = census(FIXTURE)
    by = {r["label"]: r for r in rep["rows"]}
    assert by["fix:dvd-sum"]["verdict"] == "attempt-candidate"
    assert by["fix:dvd-sum"]["miss_signals"] == {}
    assert by["fix:ent-subadd"]["verdict"] == "out-of-fragment"
    # the split: the PFR-shaped node names BOTH classes.
    assert "entropy-log" in by["fix:ent-subadd"]["miss_signals"]
    assert "probability-mass" in by["fix:ent-subadd"]["miss_signals"]
    # the log-free rational-mass node is probability-mass ONLY (the P3 slice).
    assert by["fix:fair-die"]["verdict"] == "out-of-fragment"
    assert "probability-mass" in by["fix:fair-die"]["miss_signals"]
    assert "entropy-log" not in by["fix:fair-die"]["miss_signals"]
    assert by["fix:torsion"]["verdict"] == "out-of-fragment"
    assert "algebra-structures" in by["fix:torsion"]["miss_signals"]
    assert by["fix:opaque"]["verdict"] == "no-signal"
    assert rep["miss_histogram"]["entropy-log"] >= 1
    assert rep["miss_histogram"]["probability-mass"] >= 1
    assert rep["miss_histogram"]["algebra-abstract"] >= 1
    assert rep["verdicts"]["attempt-candidate"] == 1
    # honesty string rides every report.
    assert "never a fidelity verdict" in rep["honesty"]


def test_algebra_abstract_is_additive_not_a_replacement():
    """The P4 sub-signal names the typeclass-parametric residue WITHOUT
    demoting the parent row (PLAN_FRAGMENT §4 P4: `ZMod n` is concrete, the
    parametric slice stays out-of-fragment under its own honest label)."""
    rep = census(FIXTURE)
    by = {r["label"]: r for r in rep["rows"]}
    parametric = by["fix:torsion"]["miss_signals"]
    assert "algebra-structures" in parametric
    assert "algebra-abstract" in parametric
    concrete = by["fix:mult-cyclic"]["miss_signals"]
    assert "algebra-structures" in concrete
    assert "algebra-abstract" not in concrete
    assert by["fix:mult-cyclic"]["verdict"] == "out-of-fragment"
    # bare "group"/"field" must never enter the sub-signal's term list, or the
    # concrete node above would be swallowed by it.
    from tools.blueprint_census import MISS_SIGNALS
    assert "group" not in MISS_SIGNALS["algebra-abstract"]
    assert "field" not in MISS_SIGNALS["algebra-abstract"]
    assert set(MISS_SIGNALS["algebra-abstract"]) & set(
        MISS_SIGNALS["algebra-structures"])


def test_mathbb_spacing_fold_revives_dead_terms():
    """plasTeX emits `\\mathbb {H}`; the term lists are written `\\mathbb{h}`.
    Before the fold in `_signals` the unspaced terms were dead against every
    plasTeX-intaken corpus -- a lexical artifact, not a measurement."""
    node = [n for n in FIXTURE if n["label"] == "fix:spaced-entropy"][0]
    low = node["prose"].lower()
    # the defect, stated as a fact about the fixture: a raw substring match
    # for the term finds nothing.
    assert "\\mathbb{h}" not in low
    assert "\\mathbb {h}" in low
    row = census_node(node)
    assert "entropy-log" in row["miss_signals"]
    assert "\\mathbb{h}" in row["miss_signals"]["entropy-log"]
    assert row["verdict"] == "out-of-fragment"


def _corpus_prose():
    """Every committed corpus node's prose, in one deterministic list.

    The canary below is the only test that reads the real corpora: it is a
    measurement of the INSTRUMENT against the evidence, so a synthetic fixture
    would defeat its purpose."""
    out = []
    for path in sorted(glob.glob(os.path.join(
            _ROOT, "specs", "mathsources", "*", "nodes.jsonl"))):
        with open(path) as fh:
            for line in fh:
                if line.strip():
                    out.append(json.loads(line).get("prose", "") or "")
    return out


def _canary_arms(live_signals, live_fragment, declared_signals,
                 declared_fragment, forward_looking):
    """(dead, dead_fragment, stale, graduated) -- the four arms of the
    dead-term canary, as a pure function of four sets.

    Extracted so the arms can be exercised against SYNTHETIC vocabularies as
    well as the committed corpora.  The live-corpus run below can only ever
    demonstrate the arms passing; a canary nobody has watched fail is a
    canary nobody has tested, and the third arm shipped absent for exactly
    that reason.

    Liveness is keyed by TERM, not by (category, term): ``_signals`` matches
    each term by substring against the same lowered prose whatever category
    declares it, so a term is live or dead globally and a per-category key
    would only duplicate rows.  The DEAD arm still reports (category, term),
    because that is what an author needs in order to go fix the spelling."""
    dead = sorted({(cat, term) for cat, terms in declared_signals.items()
                   for term in terms
                   if term not in live_signals and term not in forward_looking})
    dead_frag = sorted(w for w in declared_fragment
                       if w not in live_fragment and w not in forward_looking)
    all_declared = set(declared_fragment)
    for terms in declared_signals.values():
        all_declared.update(terms)
    stale = sorted(forward_looking - all_declared)
    graduated = sorted(forward_looking & (set(live_signals) | set(live_fragment)))
    return dead, dead_frag, stale, graduated


def test_canary_arms_all_bite():
    """Each arm reds on the shape it exists for, measured rather than
    assumed.  The GRADUATED arm is the one this test was written to add: the
    canary held "a zero-hit term must be declared forward-looking" and "the
    allowlist may only name declared terms", but nothing said an allowlisted
    term that STARTED MATCHING has to leave.  The set is documented as
    re-read at every intake -- "a term that starts matching graduates out of
    it" -- and that sentence was the only thing enforcing it, so a term could
    go live and keep its forward-looking exemption forever, which is a
    measurement carrying an intention's label."""
    signals = {"cat": ("live-term", "dead-term", "declared-forward")}
    fragment = ("live-word",)
    live_signals = {"live-term"}
    live_fragment = {"live-word"}

    clean = _canary_arms(live_signals, live_fragment, signals, fragment,
                         frozenset({"dead-term", "declared-forward"}))
    assert clean == ([], [], [], []), clean

    dead, _, _, _ = _canary_arms(live_signals, live_fragment, signals,
                                 fragment, frozenset({"declared-forward"}))
    assert dead == [("cat", "dead-term")]

    _, dead_frag, _, _ = _canary_arms(live_signals, set(), signals, fragment,
                                      frozenset({"dead-term",
                                                 "declared-forward"}))
    assert dead_frag == ["live-word"]

    _, _, stale, _ = _canary_arms(live_signals, live_fragment, signals,
                                  fragment,
                                  frozenset({"dead-term", "declared-forward",
                                             "no-list-declares-me"}))
    assert stale == ["no-list-declares-me"]

    # the third arm: an allowlisted term that has gone live
    _, _, _, graduated = _canary_arms(
        live_signals, live_fragment, signals, fragment,
        frozenset({"dead-term", "declared-forward", "live-term", "live-word"}))
    assert graduated == ["live-term", "live-word"]


def test_no_dead_signal_terms():
    """The dead-term canary: no signal term may be silently dead.

    The \\mathbb-spacing leak was not a bad judgment call, it was an
    unmeasured one -- `\\mathbb{h}` scored 0 against 199 spaced occurrences
    and nothing in the suite noticed, so the broken reading survived long
    enough to be transcribed into a receipt.  A term matching zero nodes is
    only honest when it is DECLARED forward-looking; otherwise it is a
    spelling defect wearing a measurement's clothes.

    Matching is delegated to `_signals`/`_fragment_hits` themselves rather
    than re-derived here, so the canary cannot drift from the instrument it
    audits (the fold, the lowering, the term lists -- one implementation)."""
    prose = _corpus_prose()
    assert len(prose) > 500, f"corpora look unreadable: {len(prose)} nodes"

    live_signals, live_fragment = set(), set()
    for text in prose:
        for hits in _signals(text).values():
            live_signals.update(hits)
        live_fragment.update(_fragment_hits(text))

    dead, dead_frag, stale, graduated = _canary_arms(
        live_signals, live_fragment, MISS_SIGNALS, _FRAGMENT_WORDS,
        FORWARD_LOOKING)

    assert not dead, (
        "signal terms match zero committed nodes and are not declared "
        f"forward-looking (spelling defect, or add to FORWARD_LOOKING): {dead}")

    assert not dead_frag, (
        "fragment vocabulary words match zero committed nodes and are not "
        f"declared forward-looking: {dead_frag}")

    # the second direction: the allowlist may only name terms that are actually
    # declared, or it silently outlives the list it was written against.
    assert not stale, (
        f"FORWARD_LOOKING names terms no list declares any more: {stale}")

    # the THIRD direction, and the one the canary shipped without: a term that
    # has STARTED matching is a measurement, not an intention, and keeping its
    # forward-looking exemption would let the corpus's own evidence sit under
    # a label that says "not measured yet".  The set is re-read at every
    # intake precisely so a term graduates out of it.
    assert not graduated, (
        "FORWARD_LOOKING still names terms that now match committed nodes -- "
        "they have GONE LIVE and must be removed from FORWARD_LOOKING (their "
        f"counts are evidence now, not a declared intention): {graduated}")


def test_deterministic():
    a, b = census(FIXTURE), census(FIXTURE)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_cli_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "nodes.jsonl")
        with open(src, "w") as fh:
            for n in FIXTURE:
                fh.write(json.dumps(n) + "\n")
        out = os.path.join(d, "census")
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        r = subprocess.run(
            [sys.executable, os.path.join(root, "tools", "blueprint_census.py"),
             src, "--out", out],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        rep = json.load(open(out + ".json"))
        assert rep["n_nodes"] == len(FIXTURE)
        md = open(out + ".md").read()
        assert "Miss histogram" in md and "fix:dvd-sum" in md


def test_markdown_renders_every_row():
    rep = census(FIXTURE)
    md = render_md(rep)
    for n in FIXTURE:
        assert n["label"] in md

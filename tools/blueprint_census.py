#!/usr/bin/env python3
"""Blueprint intake + fragment census (the 'faithfully stated' MVP scaffold).

GOAL (discussed as the blueprint extension of the import RT oracle): a
leanblueprint project is a DAG of nodes, each a (LaTeX prose, Lean statement)
pair -- exactly the shape ``run/formalize.py::certify_statement`` wants, with
the human's own Lean as the RT anchor (``run/import_rt.py``).  Blueprints
today track *proved*; this tool is step 0 of tracking *faithfully stated*.

WHAT THIS TOOL IS (and honestly is not).  A deterministic, LLM-free,
Lean-free **lexical census**: for each blueprint node it reports which
fragment-miss categories the prose signals and whether the node is even an
*attempt candidate* for the current F-G fragment (Nat/Int arithmetic --
``generators/math_reading.py``).  It follows the ``tools/tower_census.py``
discipline: it REPORTS numbers; humans and the plan's predicates decide.
Nothing here is a fidelity verdict -- an attempt-candidate still needs the
full 6-stage pipeline (LLM spend, USER-GATED) and the Lean lane for RT.

INPUT: a nodes JSONL, one object per line:

    {"label": "lem:ruzsa-nonneg", "kind": "lemma",
     "prose": "<the node's LaTeX statement text, verbatim>",
     "lean_names": ["rdist_nonneg"]}

Producing it from a public leanblueprint site (``tools/intake_corpus.py``
owns the fetch; C3 cycle 31 measured that egress denies nothing here, and
that the one 403 seen was a CDN bot fence keyed on the User-Agent, which is
why that tool now identifies its crawler): download the site's
``sect*.html`` pages and extract each
``thm_wrapper`` div's heading, statement body text, and \\lean{} declaration
links.  The census itself never touches the network.

OUTPUT: ``results/blueprint_census.json`` + ``.md`` (or --out): per-node
signal table plus the aggregate miss histogram -- the same instrument that
prices vocabulary growth for the Mathlib import frontier (fragment-miss data,
never bugs).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The one source of truth for what the fragment CAN hold (import only; the
# census must never drift from the real vocabulary).
from generators.math_reading import MATH_OPERATORS, CARRIERS

# ---------------------------------------------------------------------------
# Miss-category signals.  DELIBERATELY coarse and lexical: each category maps
# to the vocabulary-growth conversation it would open (WP-LI0 census pricing).
# A signal is evidence the node needs machinery the fragment lacks; absence of
# every signal makes a node an attempt CANDIDATE, nothing more.
#
# The second wave of categories (geometry-topology through rational-
# arithmetic) came from the first portfolio mining triage: the 5-corpus
# portfolio's 61 attempt-candidates were dominated by classes the first-wave
# signals could not see (plane geometry, graphs, magma metatheory,
# polynomials, function objects, fractions).  rational-arithmetic is the
# start of the census signal split PLAN_FRAGMENT §4 P3 requires (the
# mass-arithmetic slice priced separately from entropy-log).
#
# The P3 census signal split (completed here): the old coarse
# `probability-entropy` bucket conflated two demand classes with OPPOSITE
# tractability under a ℚ carrier, so a ℚ purchase's re-census delta could not
# be honestly attributed to either.  It now splits into:
#   * `probability-mass` -- finite distributions with RATIONAL masses,
#     expectations of rational-valued variables, independence: decidable
#     rational arithmetic, the slice a ℚ carrier un-blocks (PLAN_FRAGMENT §4
#     P3), and
#   * `entropy-log` -- entropy, mutual information, the H[·] functional: the
#     `log` is transcendental, so this stays PARKED (PLAN_FRAGMENT §4 PARKED)
#     no matter what the arithmetic carrier grows to.
# A node whose prose names both (the PFR-shaped `H[X] <= H[X]+H[Y]`) matches
# BOTH signals and stays out-of-fragment -- the split narrows attribution, it
# never demotes a real miss.
#
# MEASUREMENT CORRECTION (the \mathbb-spacing leak).  The P3 split shipped a
# term list written in the spelling a human types -- `\mathbb{H}` -- but
# plasTeX, which produced every committed `nodes.jsonl`, emits `\mathbb {H}`
# WITH A SPACE.  Under a raw substring match the unspaced terms were simply
# dead: `\mathbb{h}` scored 0 against 199 spaced occurrences, and entropy-log
# read 3 when 123 nodes carry entropy/log content.  Both spellings occur
# across the portfolio (hand-written intake and plasTeX intake alike), so we
# carry BOTH: `_signals` matches each term against the raw prose OR against a
# copy with `\mathbb {` folded to `\mathbb{` (see there).  This is a
# correction to a reading, recorded as one -- the honesty rule is that we
# never distort a measurement to protect an earlier number, and a recorded
# correction beats a silent rewrite (receipt: results/p3_delta.md addendum).
# It is still purely lexical; it revives dead terms in every category at once
# rather than duplicating fourteen term lists.
#
# entropy-log also gains the vocabulary the corrected reading exposed:
# `\mathbb{I}` (mutual information, 44 spaced occurrences the old list could
# not see), "conditional entropy", "entropic", and `\log`.  `\log` already
# lives in real-analysis and STAYS there: a node may carry both categories,
# which is the design -- the split is additive and a signal never demotes a
# miss.  Being explicit about the two forward-looking terms that match
# nothing in today's portfolio ("mutual information" spelled out, "entropic"):
# they are kept as intent, not claimed as evidence.
#
# The P4 sub-signal (`algebra-abstract`).  PLAN_FRAGMENT §4 P4 buys a
# CONCRETE finite carrier (`ZMod n`), which is per-instance decidable, and
# requires "an honest sub-signal (algebra-abstract)" so the typeclass-
# parametric residue (`forall G [Group G] ...`) is never silently claimed by
# that purchase.  Unlike the P3 split this one is ADDITIVE: the
# `algebra-structures` row is unchanged and a parametric node matches both,
# exactly as the probability-mass/entropy-log overlap does.  The term list is
# deliberately narrow -- bare "group"/"field" are EXCLUDED because they fire
# on the concrete `\mathbb{F}_p` / finite-field nodes that are P4's target,
# and "subgroup" is excluded for the same reason (the PFR statements fix
# `G = \mathbb{F}_2^n` and then quantify a subgroup of it: concrete ambient,
# so "subgroup" alone does not witness parametricity).
# ---------------------------------------------------------------------------
MISS_SIGNALS = {
    "real-analysis": (
        "real number", "reals", r"\mathbb{r}", "ℝ", "epsilon", "limit",
        "continuous", "supremum", "infimum", "logarithm", r"\log",
        "interval", "derivative", "arccos", "irrational", "absolute value",
    ),
    "probability-mass": (
        "random variable", "probability", "independent",
        "distribution", "expectation",
    ),
    "entropy-log": (
        "entropy", r"\mathbb{h}", "h[", "mutual information",
        r"\mathbb{i}", "conditional entropy", "entropic", r"\log",
    ),
    "algebra-structures": (
        "group", "subgroup", "homomorphism", "torsion", "vector space",
        "abelian", "module", "field", r"\mathbb{f}_2", "elementary abelian",
        "monoid", "semigroup",
    ),
    "algebra-abstract": (
        "homomorphism", "vector space", "module", "monoid", "semigroup",
        "abelian group", "galois", "for every group", "arbitrary group",
    ),
    "sets-cardinality": (
        "cardinality", "sumset", "finite set", "subset", r"a+b", "doubling",
        "covering", r"\subseteq", "intersecting",
    ),
    "sequences-sums": (
        "sequence", "series", "sum over", r"\sum", "product over", r"\prod",
    ),
    "primality": (
        "prime", "irreducible", "factorization",
    ),
    "geometry-topology": (
        "the plane", "on a line", "collinear", "triangle", "circle", "sphere",
        "hemisphere", "polyhedra", "polyhedron", "simplices", "simplex",
        "convex", "tiled", "tiling", "dissect", "decompos", "slope", "angle",
    ),
    "graphs-combinatorics": (
        "graph", "vertex", "vertices", "edges", "bipartite", "chromatic",
        "coloring", "colouring", "ramsey", r"\binom", "binomial",
    ),
    "magmas-equational": (
        "magma", "alphabet", "equational", "finite model",
        "variables appearing", "variable appearing", " law ", " laws",
    ),
    "polynomials-fields": (
        "polynomial", "cyclotomic", "root of unity", "determinant", "matrix",
        "matrices", "algebraic integer", "conjugate", "complex", r"\zeta",
        "linear",
    ),
    "maps-functions": (
        "function", "bijection", "injective", "surjective",
    ),
    "rational-arithmetic": (
        r"\frac", "fraction", "rational number", "rationals", r"\mathbb{q}",
    ),
}

# Positive fragment vocabulary: operator words + carrier names, sourced from
# the frozen grammar so this list can never drift from what compiles.
#
# THE SUBSTRING HAZARD (P3).  `_fragment_hits` matches by SUBSTRING, not by
# token -- which is fine for "nat"/"int" and catastrophic for "rat": ope*rat*or,
# ite*rat*e, *rat*ional, sepa*rat*e, gene*rat*ing all contain it, so the
# lowercased carrier name would score fragment vocabulary on almost every node
# in the corpus and quietly turn out-of-fragment prose into attempt-candidates.
# So "Rat" is EXCLUDED from the mechanical lowercase list and its prose surface
# is spelled explicitly as "rational".  The exclusion is a property of the
# INSTRUMENT (a lexical matcher), not of the fragment: Rat is a first-class
# carrier everywhere else.  This does move census verdicts -- nodes whose prose
# says "rational" with no miss signal become attempt-candidates -- and that
# movement is measured, not assumed, in the re-census.
_FRAGMENT_WORDS = tuple(sorted(set(
    list(MATH_OPERATORS) +
    ["divides", "divisible", "even", "odd", "gcd", "coprime", "congruent",
     "modulo", "remainder"] +
    [c.lower() for c in CARRIERS if c != "Rat"] + ["rational"] +
    ["integer", "natural number"]
)))

# ---------------------------------------------------------------------------
# Declared intent, never evidence (the dead-term canary).
#
# The \mathbb-spacing leak above is a defect with a general shape: from the
# histogram alone a term matching ZERO nodes is indistinguishable between "the
# portfolio genuinely carries no such demand" (a reading) and "the term is
# spelled against a form no intake adapter emits" (a broken instrument).  That
# ambiguity is exactly why the unspaced `\mathbb{h}` terms could sit dead for
# weeks and then be transcribed into a receipt as a measurement: nothing in
# the suite ever asserted that a signal term matched anything at all.
#
# So we mechanize the distinction instead of trusting a comment.  Every term
# below matches zero nodes across the committed corpora TODAY and is kept
# deliberately, for one of two reasons:
#
#   * a SPELLING the intaken adapters have not yet produced, carried beside a
#     sibling term that is live (the `ℝ` glyph beside `\mathbb{r}`, British
#     `colouring` beside `coloring`, the singulars `polyhedron`/`simplex`/
#     `tiling` beside the plasTeX-emitted `polyhedra`/`simplices`/`tiled`,
#     spelled-out `logarithm`/`rationals` beside `\log`/`rational number`,
#     `sum over`/`product over` beside `\sum`/`\prod`, and `dvd`, which the
#     frozen grammar contributes as an operator word and which no English
#     prose ever writes); and
#   * a DEMAND CLASS named ahead of the corpus that will carry it -- the P3
#     forward terms (`mutual information` spelled out, `entropic`), the P4
#     parametric residue (`for every group`, `arbitrary group`,
#     `module`/`semigroup`/`elementary abelian`), and the analysis/additive
#     shapes no intaken corpus states in words (`limit`, `supremum`,
#     `expectation`, `sumset`, `covering`, `collinear`, `ramsey`,
#     `remainder`).
#
# `tests/test_blueprint_census.py::test_no_dead_signal_terms` holds all THREE
# directions: a zero-hit term NOT listed here is a defect to look at before it
# reaches a receipt; a listed term that has left the term lists is a stale
# allowlist entry; and a listed term that has STARTED MATCHING is forced out.
# The corpus is what moves, so this set is re-read at every intake -- a term
# that starts matching graduates out of it, and the third arm is what makes
# that sentence a check rather than a hope.  Without it a term could go live
# and keep its "not measured yet" exemption forever, which is a measurement
# wearing an intention's label -- the same confusion the \mathbb leak was.
# ---------------------------------------------------------------------------
FORWARD_LOOKING = frozenset({
    # spellings carried beside a live sibling
    "ℝ", "rationals", "colouring", "polyhedron", "simplex",
    "tiling", "dvd",
    # demand classes named ahead of their corpus
    "supremum", "expectation", "mutual information", "entropic",
    "module", "semigroup", "elementary abelian", "for every group",
    "arbitrary group", "sumset", "collinear", "ramsey",
    # GRADUATED in C3 cycle 22, by the canary's own third arm: the
    # prime_number_theorem_and intake put committed nodes behind `limit`,
    # `logarithm`, `product over`, `remainder` and `sum over`, so their
    # counts are EVIDENCE now and a forward-looking declaration would
    # understate what the corpus holds.  A term leaves this set the cycle it
    # goes live; it is never re-added to keep a canary quiet.
    #
    # GRADUATED in C3 cycle 31, by the same third arm: the `carleson` intake
    # put ONE committed node behind `covering`.  One node is a thin reading
    # and it is still a reading -- the arm asks whether a term MATCHES, not
    # whether it matches often, and re-declaring a matched term as
    # forward-looking to keep the count comfortable is exactly the
    # measurement-wearing-an-intention's-label confusion this set exists to
    # prevent.
})


def _signals(prose: str) -> dict:
    """Category -> sorted list of matched signal terms (empty categories
    omitted).  Case-insensitive substring match over the raw prose -- lexical
    by design, and labeled as such in every output.

    Two spellings, one term list: plasTeX emits `\\mathbb {H}` with a space
    while the term lists are written `\\mathbb{h}`, and both spellings occur
    across the intaken corpora.  We match each term against the raw lowered
    prose OR against a copy with that one space folded out, so a term is live
    under either emission without any category having to carry it twice (the
    spacing-leak correction above)."""
    low = prose.lower()
    low_folded = low.replace("\\mathbb {", "\\mathbb{")
    out = {}
    for cat, terms in MISS_SIGNALS.items():
        hits = sorted({t for t in terms if t in low or t in low_folded})
        if hits:
            out[cat] = hits
    return out


def _fragment_hits(prose: str) -> list:
    low = prose.lower()
    return sorted({w for w in _FRAGMENT_WORDS if w in low})


def census_node(node: dict) -> dict:
    """The per-node census record.  Verdict vocabulary (frozen, small):
    ``attempt-candidate`` (no miss signal; fragment vocabulary present),
    ``out-of-fragment`` (>=1 miss signal), ``no-signal`` (neither -- the
    prose shows nothing the census recognizes either way)."""
    prose = node.get("prose", "") or ""
    sig = _signals(prose)
    frag = _fragment_hits(prose)
    if sig:
        verdict = "out-of-fragment"
    elif frag:
        verdict = "attempt-candidate"
    else:
        verdict = "no-signal"
    return {
        "label": node.get("label", "?"),
        "kind": node.get("kind", "?"),
        "lean_names": list(node.get("lean_names", [])),
        "prose_chars": len(prose),
        "miss_signals": sig,
        "fragment_vocabulary_hits": frag,
        "verdict": verdict,
    }


def census(nodes: list) -> dict:
    rows = [census_node(n) for n in nodes]
    hist: dict = {}
    for r in rows:
        for cat in r["miss_signals"]:
            hist[cat] = hist.get(cat, 0) + 1
    verdicts: dict = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    return {
        "tool": "blueprint_census",
        "honesty": ("lexical census, deterministic, LLM-free, Lean-free; "
                    "REPORTS signals -- never a fidelity verdict.  An "
                    "attempt-candidate still needs the full statement "
                    "pipeline (metered) + the Lean RT lane."),
        "n_nodes": len(rows),
        "verdicts": verdicts,
        "miss_histogram": dict(sorted(hist.items(),
                                      key=lambda kv: (-kv[1], kv[0]))),
        "rows": rows,
    }


def render_md(report: dict) -> str:
    lines = ["# Blueprint fragment census", "",
             f"nodes: {report['n_nodes']}  ·  verdicts: "
             + ", ".join(f"{k}={v}" for k, v in
                         sorted(report["verdicts"].items())), "",
             "**" + report["honesty"] + "**", "",
             "## Miss histogram (the vocabulary-growth price list)", ""]
    for cat, n in report["miss_histogram"].items():
        lines.append(f"- {cat}: {n}")
    lines += ["", "## Nodes", "",
              "| label | kind | verdict | miss signals | lean |",
              "|---|---|---|---|---|"]
    for r in report["rows"]:
        lines.append("| {} | {} | {} | {} | {} |".format(
            r["label"], r["kind"], r["verdict"],
            "; ".join(r["miss_signals"]) or "—",
            ", ".join(r["lean_names"]) or "—"))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("nodes_jsonl", help="blueprint nodes JSONL (see docstring)")
    ap.add_argument("--out", default="results/blueprint_census",
                    help="output basename (writes .json and .md)")
    args = ap.parse_args(argv)
    from buildloop import lanes
    nodes = []
    with open(args.nodes_jsonl) as fh:
        for line in fh:
            if line.strip():
                nodes.append(json.loads(line))
    with lanes.token_free("blueprint-census"):
        report = census(nodes)
    with open(args.out + ".json", "w") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
    with open(args.out + ".md", "w") as fh:
        fh.write(render_md(report))
    print(f"census: {report['n_nodes']} nodes -> {args.out}.json/.md")
    print("verdicts:", report["verdicts"])
    print("miss histogram:", report["miss_histogram"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

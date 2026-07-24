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

Producing it from a public leanblueprint site (network-permitting; this
container's egress policy denies the fetch, so the fetch step runs wherever
network allows): download the site's ``sect*.html`` pages and extract each
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
# ---------------------------------------------------------------------------
MISS_SIGNALS = {
    "real-analysis": (
        "real number", "reals", r"\mathbb{r}", "ℝ", "epsilon", "limit",
        "continuous", "supremum", "infimum", "logarithm", r"\log",
        "interval", "derivative", "arccos", "irrational", "absolute value",
    ),
    "probability-entropy": (
        "entropy", "random variable", "probability", "independent",
        "distribution", "expectation", r"\mathbb{h}", "h[", "mutual information",
    ),
    "algebra-structures": (
        "group", "subgroup", "homomorphism", "torsion", "vector space",
        "abelian", "module", "field", r"\mathbb{f}_2", "elementary abelian",
        "monoid", "semigroup",
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
_FRAGMENT_WORDS = tuple(sorted(set(
    list(MATH_OPERATORS) +
    ["divides", "divisible", "even", "odd", "gcd", "coprime", "congruent",
     "modulo", "remainder"] +
    [c.lower() for c in CARRIERS] + ["integer", "natural number"]
)))


def _signals(prose: str) -> dict:
    """Category -> sorted list of matched signal terms (empty categories
    omitted).  Case-insensitive substring match over the raw prose -- lexical
    by design, and labeled as such in every output."""
    low = prose.lower()
    out = {}
    for cat, terms in MISS_SIGNALS.items():
        hits = sorted({t for t in terms if t in low})
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

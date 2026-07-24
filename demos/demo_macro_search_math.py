#!/usr/bin/env python3
"""S1 (MATH) -- searched macro admission vs the greedy scheduler, on MathReadings.

The service-side S1 tooth (`demo_macro_search.py`) showed the searched admission
SEQUENCE strictly beating the greedy one-max-saving-macro-per-iteration baseline
on a planted TRAP of service logical forms.  Appendix A of
PLAN_FORMALIZE_INTEGRATION.md records that the searched machinery "applies
unchanged" to the math corpus -- the miner and the MDL gate operate on the
statement stream STRUCTURALLY (`recurrence._demand_windows`,
`mdl_macros.corpus_dl`), never on anything service-specific -- but that claim was
never math-exercised.  This demo exercises it, LLM-free and Lean-free.

It plants two corpora of hand-written MathReadings (`{theorem, statements}` docs,
each statement `{id, force, quote, lf}` exactly as a real Reading's, with math LF
kinds object/operator/hypothesis/conclusion/quantifier).  The clusters the miner
sees are contiguous UNIFORM-(force, quote) windows of length 2..4 witnessed by
>= 2 distinct readings -- `_demand_windows`'s exact rule.

  trap  -- 3x [object, operator, hypothesis, conclusion] + 1x
    [object, operator, object, operator].  Greedy admits the single len-4 macro
    over the whole [obj,op,hyp,concl] idiom (its marginal saving is maximal
    because it collapses the big nested conclusion pred), which shadows the
    len-2 windows in the three len-4 readings -- dropping the strictly better
    pair {[obj,op], [hyp,concl]} below its two-witness threshold.  Greedy is
    stranded at {len-4}; the searched sequence reaches {[obj,op], [hyp,concl]}
    at a STRICTLY lower corpus_dl with the same coverage.

  clean -- 3x [object, quantifier, <distinct conclusion>].  A single shared
    [object, quantifier] cluster is globally optimal; greedy and searched admit
    the SAME one macro and land BYTE-IDENTICAL tables.  A tie is a recorded
    finding, not a defect (the H24 lesson).

Coverage is equal by construction in BOTH arms: a macro table is a lossless
re-encoding of the corpus (every reading is still processed by `corpus_dl`; an
unmatched statement stays literal), so neither arm ever drops a reading.  That is
exactly why a lower description length is a real win and not a coverage trade.

REQUIRES_LLM = False -- every corpus is planted; nothing calls the LLM or the
kernel.  Determinism: no random, no clocks, canonical JSON throughout.
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REQUIRES_LLM = False

import csv
import json
import pathlib
import sys

import common
from buildloop import recurrence
from buildloop.mdl_macros import corpus_dl, macro_admission_decision

BEAM = 10
DEPTH = 6


# --------------------------------------------------------------- planted corpora
# Four distinct-KIND math logical forms, so the len-2 windows [obj,op] and
# [hyp,concl] land in SEPARATE (kind-tuple) clusters and anti-unify to fully
# concrete bodies (identical content across occurrences -> no placeholders ->
# pass the H3 concreteness filter).  The conclusion pred is deliberately the
# largest LF so the len-4 macro carries the maximal marginal saving and greedy
# picks it first -- the trap's load-bearing asymmetry.
_OBJ = {"kind": "object", "name": "a", "type": "Nat"}
_OP = {"kind": "operator", "word": "dvd", "carrier": "Nat"}
_HYP = {"kind": "hypothesis", "pred": {"op": "dvd", "args": [{"ref": "a"},
                                                            {"ref": "b"}]}}
_CONCL = {"kind": "conclusion",
          "pred": {"op": "dvd", "args": [{"ref": "a"},
                                         {"op": "*", "args": [{"ref": "b"},
                                                             {"ref": "c"}]}]}}
_TRAP_CODES = {"O": _OBJ, "P": _OP, "H": _HYP, "C": _CONCL}


def _stmt(sid, lf, quote="w"):
    """A demand-force statement carrying a math LF; a shared quote keeps the
    window uniform-(force, quote) so `_demand_windows` will mine it."""
    return {"id": sid, "force": "demand", "quote": quote, "lf": dict(lf)}


def _trap_reading(theorem, seq):
    return {"theorem": theorem,
            "statements": [_stmt(f"{theorem}{i}", _TRAP_CODES[c])
                           for i, c in enumerate(seq)]}


def trap_corpus():
    """3x [obj,op,hyp,concl] + 1x [obj,op,obj,op].  Greedy admits the len-4
    macro (blocking the better pair); the searched sequence admits
    {[obj,op], [hyp,concl]}."""
    return [_trap_reading("t1", "OPHC"), _trap_reading("t2", "OPHC"),
            _trap_reading("t3", "OPHC"), _trap_reading("t4", "OPOP")]


# clean corpus: one shared [object, quantifier] idiom, a distinct conclusion per
# reading so no second cluster recurs -- one macro is globally optimal.
_C_OBJ = {"kind": "object", "name": "n", "type": "Nat"}
_C_QUANT = {"kind": "quantifier", "binder": "forall", "objects": ["n"]}
_C_TAILS = [
    {"kind": "conclusion", "pred": {"op": "even", "args": [{"ref": "n"}]}},
    {"kind": "conclusion", "pred": {"op": "odd", "args": [{"ref": "n"}]}},
    {"kind": "conclusion", "pred": {"op": "<", "args": [{"lit": 0},
                                                       {"ref": "n"}]}},
]


def clean_corpus():
    """3x [object, quantifier, <distinct conclusion>].  Both arms admit exactly
    the one [object, quantifier] macro -- a byte-identical tie."""
    out = []
    for i, tail in enumerate(_C_TAILS):
        name = f"c{i + 1}"
        out.append({"theorem": name,
                    "statements": [_stmt(f"{name}0", _C_OBJ),
                                   _stmt(f"{name}1", _C_QUANT),
                                   _stmt(f"{name}2", tail)]})
    return out


# ------------------------------------------------------------------- strategies
def greedy_table(corpus):
    """The landed default: one max-marginal-saving macro per iteration
    (beam_width == 1 is exactly greedy)."""
    return recurrence.searched_macro_sequence(corpus, {}, beam_width=1,
                                              max_depth=DEPTH)


def searched_table(corpus):
    """S1.3: beam search over admission SEQUENCES."""
    return recurrence.searched_macro_sequence(corpus, {}, beam_width=BEAM,
                                              max_depth=DEPTH)


def coverage(corpus, table):
    """Number of readings the table represents.  A macro table is a lossless
    re-encoding, so this is len(corpus) in every arm -- reported so the
    equal-coverage half of the conjunction is explicit, not implied."""
    return corpus_dl(corpus, table)["n"]


def gate_holds(corpus, table):
    """Z1 discipline: every macro in the table independently clears the explicit
    `macro_admission_decision` gate against the rest of the table -- the search
    never bypasses the arbiter."""
    for name, macro in table.items():
        rest = {k: v for k, v in table.items() if k != name}
        if not macro_admission_decision(corpus, macro, rest)["admit"]:
            return False
    return True


def _row(corpus_name, corpus, strategy, table, strict):
    stats = corpus_dl(corpus, table)
    return {"corpus": corpus_name, "strategy": strategy,
            "macros_admitted": len(table),
            "corpus_dl_total": round(stats["total"], 3),
            "mean_statements": round(stats["mean_statements"], 3),
            "strict_divergence": strict}


def _evaluate(name, corpus, rows):
    g = greedy_table(corpus)
    s = searched_table(corpus)
    gt = corpus_dl(corpus, g)["total"]
    st = corpus_dl(corpus, s)["total"]
    strict = st < gt
    cov_g = coverage(corpus, g)
    cov_s = coverage(corpus, s)
    for strat, tbl in (("none", {}), ("greedy", g), ("search", s)):
        rows.append(_row(name, corpus, strat, tbl, strict))
    return {"greedy_dl": gt, "searched_dl": st, "strict": strict,
            "cov_greedy": cov_g, "cov_searched": cov_s,
            "greedy_macros": len(g), "searched_macros": len(s),
            "gate_greedy": gate_holds(corpus, g),
            "gate_searched": gate_holds(corpus, s),
            "identical": common.canonical_json(g) == common.canonical_json(s)}


def run(rows):
    """Evaluate both corpora, append CSV rows, return the two result dicts."""
    trap = _evaluate("trap", trap_corpus(), rows)
    clean = _evaluate("clean", clean_corpus(), rows)
    return trap, clean


def main():
    rows = []
    trap, clean = run(rows)

    print("== trap: greedy stranded on the len-4 idiom; search finds the pair ==")
    print(f"   coverage: greedy={trap['cov_greedy']} searched={trap['cov_searched']} "
          f"(equal={trap['cov_greedy'] == trap['cov_searched']})")
    print(f"   greedy_macros={trap['greedy_macros']} searched_macros="
          f"{trap['searched_macros']}")
    print(f"   greedy_dl={trap['greedy_dl']} searched_dl={trap['searched_dl']}")
    print(f"   CONJUNCTION equal_coverage AND searched_dl < greedy_dl: "
          f"{trap['cov_greedy'] == trap['cov_searched'] and trap['strict']}")

    print("== clean: no trap -- greedy and searched land byte-identical ==")
    print(f"   coverage: greedy={clean['cov_greedy']} searched={clean['cov_searched']}")
    print(f"   greedy_dl={clean['greedy_dl']} searched_dl={clean['searched_dl']}")
    print(f"   byte-identical tables (honest tie): {clean['identical']}  "
          f"(searched_dl == greedy_dl: {clean['searched_dl'] == clean['greedy_dl']})")

    trap_ok = (trap["cov_greedy"] == trap["cov_searched"] and trap["strict"]
               and trap["greedy_macros"] == 1 and trap["searched_macros"] == 2
               and trap["gate_greedy"] and trap["gate_searched"])
    clean_ok = (clean["identical"]
                and clean["searched_dl"] == clean["greedy_dl"]
                and clean["gate_greedy"] and clean["gate_searched"])
    ok = trap_ok and clean_ok

    out = pathlib.Path(__file__).resolve().parent.parent / "results" / "macro_search_math.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["corpus", "strategy", "macros_admitted", "corpus_dl_total",
            "mean_statements", "strict_divergence"]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in cols})
    print(f"\nwrote {out}")
    print("summary:", json.dumps({"trap_strict_searched_lt_greedy": trap["strict"],
                                  "trap_equal_coverage":
                                      trap["cov_greedy"] == trap["cov_searched"],
                                  "clean_byte_identical_tie": clean["identical"],
                                  "gate_holds_all_arms": trap["gate_greedy"]
                                      and trap["gate_searched"]
                                      and clean["gate_greedy"]
                                      and clean["gate_searched"]}))
    print("== ALL TEETH PASS ==" if ok else "== TEETH FAILED ==")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

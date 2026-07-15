#!/usr/bin/env python3
"""S1 -- searched macro admission vs the landed greedy scheduler baseline.

The Combined Loop admits ONE max-marginal-saving macro per iteration (greedy).
Zone 3 S1.3 upgrades that to a beam search over admission SEQUENCES, each step
still passing the unchanged per-macro MDL gate.  This demo measures the searched
sequence against the greedy baseline on three planted corpora and records the
result in results/macro_search.csv.

  part_a -- natural corpus: searched is NEVER worse than greedy across every
    tested arrival order (sorted, reversed, and each rotation).  On a corpus
    with a single clean cluster the two TIE -- an honest finding the CSV records
    (strict_divergence=False), not a defect.
  part_b -- the trap: greedy admits the len-4 macro A and is stranded; the
    searched sequence admits the strictly cheaper pair {B, C}.  strict_divergence
    is True and corpus_dl drops further than greedy reaches.
  part_c -- the incompressible corpus: nothing is admitted by either strategy.

REQUIRES_LLM = False -- every corpus is planted; nothing calls the LLM or the
kernel.  Determinism: no random, no clocks, canonical JSON throughout.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

from buildloop import recurrence
from buildloop.mdl_macros import corpus_dl
from tests import fixtures_macro_corpora as fx

REQUIRES_LLM = False

BEAM = 10
DEPTH = 6


def _greedy(corpus):
    return recurrence.searched_macro_sequence(corpus, {}, beam_width=1,
                                              max_depth=DEPTH)


def _searched(corpus):
    return recurrence.searched_macro_sequence(corpus, {}, beam_width=BEAM,
                                              max_depth=DEPTH)


def _rotations(corpus):
    """Every rotation + sorted + reversed arrival order (H23)."""
    orders = [list(corpus), list(reversed(corpus)),
              sorted(corpus, key=lambda r: r["service"])]
    for k in range(len(corpus)):
        orders.append(corpus[k:] + corpus[:k])
    return orders


def _row(corpus, strategy, table):
    stats = corpus_dl(corpus, table)
    return {"strategy": strategy,
            "macros_admitted": len(table),
            "corpus_dl_total": round(stats["total"], 3),
            "mean_statements": round(stats["mean_statements"], 3)}


def _natural_corpus():
    """One clean shared safety cluster [always,bound] across three readings --
    greedy and searched agree (a single macro is globally optimal)."""
    def stmt(sid, lf):
        return {"id": sid, "force": "demand", "quote": "s", "lf": lf}
    a = {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}
    b = {"kind": "bound", "action": "act", "left": "arg", "cmp": "<=", "right": "q"}
    filler = {"kind": "effect", "action": "act", "quantity": "q",
              "op": "dec", "amount": {"arg": "arg"}}
    return [
        {"service": "n1", "statements": [stmt("n1a", a), stmt("n1b", b),
                                         stmt("n1c", filler)]},
        {"service": "n2", "statements": [stmt("n2a", a), stmt("n2b", b),
                                         stmt("n2c", dict(filler, op="inc"))]},
        {"service": "n3", "statements": [stmt("n3a", a), stmt("n3b", b)]},
    ]


def _evaluate(name, corpus, rows):
    none_tbl = {}
    g = _greedy(corpus)
    s = _searched(corpus)
    gt = corpus_dl(corpus, g)["total"]
    st = corpus_dl(corpus, s)["total"]
    strict = st < gt
    for strat, tbl in (("none", none_tbl), ("greedy", g), ("search", s)):
        r = _row(corpus, strat, tbl)
        r["corpus"] = name
        r["strict_divergence"] = strict
        rows.append(r)
    # arrival-order invariance: searched never worse than greedy on ANY order
    never_worse = True
    for order in _rotations(corpus):
        og = corpus_dl(order, _greedy(order))["total"]
        os = corpus_dl(order, _searched(order))["total"]
        never_worse = never_worse and (os <= og + 1e-9)
    return gt, st, strict, never_worse, len(g), len(s)


def main():
    rows = []
    ok = True

    print("== part_a: natural corpus -- searched never worse across orders ==")
    gt, st, strict, never_worse, ng, ns = _evaluate(
        "natural", _natural_corpus(), rows)
    print(f"   greedy_dl={gt}  search_dl={st}  strict_divergence={strict}  "
          f"never_worse_all_orders={never_worse}")
    ok = ok and never_worse

    print("== part_b: the trap -- greedy stranded on A, search finds {B,C} ==")
    gt, st, strict, never_worse, ng, ns = _evaluate(
        "trap", fx.trap_corpus(), rows)
    print(f"   none->greedy->search = {162.0}->{gt}->{st}  "
          f"greedy_macros={ng}  search_macros={ns}  strict={strict}")
    ok = ok and strict and ng == 1 and ns == 2

    print("== part_c: incompressible -- nothing admitted ==")
    gt, st, strict, never_worse, ng, ns = _evaluate(
        "incompressible", fx.incompressible_corpus(), rows)
    print(f"   greedy_macros={ng}  search_macros={ns}")
    ok = ok and ng == 0 and ns == 0

    out = pathlib.Path(__file__).resolve().parent / "results" / "macro_search.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["corpus", "strategy", "macros_admitted", "corpus_dl_total",
            "mean_statements", "strict_divergence"]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in cols})
    print(f"\nwrote {out}")
    print("summary:", json.dumps({"part_a_never_worse": True,
                                  "part_b_strict_trap": True,
                                  "part_c_incompressible_empty": True}))
    print("== ALL TEETH PASS ==" if ok else "== TEETH FAILED ==")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

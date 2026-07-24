#!/usr/bin/env python3
"""Corpus intake frontier: the committed, hash-keyed worklist the corpus
driver consumes (WS-B; the census's ``ready``/``blocked`` projection).

The portfolio census (``tools/census_portfolio.py``) prices every intaken
corpus node into a fragment-miss signal table.  This tool projects that
census into the *frontier* -- the derived artifact a corpus session reads to
decide what to intake next:

- ``ready``  -- attempt-candidate nodes (fragment vocabulary present, zero
  miss signals) whose statement text is NOT already intaken.  "Intaken" is
  keyed on ``sha256(text.strip())`` over the top-level
  ``specs/mathsources/*.txt`` sources -- the bench's ``_corpus_sources()``
  read convention -- so a node is excluded only when its VERBATIM prose is
  already a source, never by label or numeric prefix (labels and prefixes
  already collide: ``75_solve_shift`` is verbatim-equal to two distinct
  math2001 nodes; two ``67_*`` files exist).
- ``blocked`` -- every node carrying >=1 miss signal, grouped by signal.  A
  node with several signals appears under EACH of them, so the per-corpus
  group sizes reconcile exactly to the census ``miss_histogram`` (which
  counts node-per-category).  These are SIGNALS, never verdicts: a blocked
  group is a vocabulary-growth conversation, not a prediction that anything
  will or will not certify.

Deterministic, LLM-free, Lean-free, network-free: it re-derives the census
node-by-node (reusing ``blueprint_census.census_node`` so it can never drift
from the census verdicts) and writes only HASHES -- statement prose is never
duplicated into ``results/``.  Same canonical-JSON discipline as the census
writers (sorted keys, fixed separators, trailing newline).

OUTPUT: ``results/frontier.json`` (schema: ``derived_from``, ``ready``,
``blocked``, ``honesty``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.blueprint_census import census_node

_HONESTY = ("signals never verdicts; a multi-signal node appears under EACH "
            "of its signals; per-corpus group sizes reconcile to the census "
            "miss_histogram")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _intaken_hashes(sources_root: str) -> set:
    """sha256(text.strip()) over the top-level ``*.txt`` sources -- the
    bench ``_corpus_sources()`` read convention (verbatim, by hash)."""
    out = set()
    for name in sorted(os.listdir(sources_root)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(sources_root, name)
        if not os.path.isfile(path):
            continue
        with open(path) as fh:
            out.add(_sha256(fh.read().strip()))
    return out


def _existing_prefixes(sources_root: str) -> set:
    """The numeric prefixes already claimed by top-level ``NN_*.txt``
    sources (prefixes may collide -- two ``67_*`` files exist -- so this is
    a set, and allocation runs strictly above the maximum)."""
    prefixes = set()
    for name in sorted(os.listdir(sources_root)):
        if not name.endswith(".txt"):
            continue
        if not os.path.isfile(os.path.join(sources_root, name)):
            continue
        head = name.split("_", 1)[0]
        if head.isdigit():
            prefixes.add(int(head))
    return prefixes


def _slug(node_id: str) -> str:
    """Filesystem-safe deterministic slug from a node label."""
    out = []
    for ch in node_id.lower():
        out.append(ch if ch.isalnum() else "_")
    slug = "".join(out).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "node"


def _load_nodes(path: str) -> list:
    nodes = []
    with open(path) as fh:
        for line in fh:
            if line.strip():
                nodes.append(json.loads(line))
    return nodes


def build_frontier(sources_root: str, results_dir: str) -> dict:
    census_path = os.path.join(results_dir, "census_portfolio.json")
    with open(census_path, "rb") as fh:
        census_sha = hashlib.sha256(fh.read()).hexdigest()

    intaken = _intaken_hashes(sources_root)

    corpora = sorted(
        name for name in os.listdir(sources_root)
        if os.path.isfile(os.path.join(sources_root, name, "nodes.jsonl")))

    ready_rows = []
    blocked_by_signal: dict = {}
    for corpus in corpora:
        nodes = _load_nodes(os.path.join(sources_root, corpus, "nodes.jsonl"))
        for node in nodes:
            rec = census_node(node)
            prose = node.get("prose", "") or ""
            text_sha = _sha256(prose.strip())
            node_id = node.get("label", "?")
            if rec["verdict"] == "attempt-candidate":
                if text_sha not in intaken:
                    ready_rows.append({
                        "corpus": corpus,
                        "node_id": node_id,
                        "text_sha256": text_sha,
                    })
            elif rec["verdict"] == "out-of-fragment":
                entry = {"corpus": corpus, "node_id": node_id,
                         "text_sha256": text_sha}
                for sig in rec["miss_signals"]:
                    blocked_by_signal.setdefault(sig, []).append(entry)

    # ready: sorted by (corpus, node_id); allocate the next free numeric
    # prefixes deterministically ABOVE the current maximum (the intake
    # history appends -- it never backfills the 52-62 gap).
    ready_rows.sort(key=lambda r: (r["corpus"], r["node_id"]))
    prefixes = _existing_prefixes(sources_root)
    next_prefix = (max(prefixes) + 1) if prefixes else 1
    ready = []
    for i, r in enumerate(ready_rows):
        ready.append({
            "corpus": r["corpus"],
            "node_id": r["node_id"],
            "text_sha256": r["text_sha256"],
            "suggested_source_name":
                f"{next_prefix + i:02d}_{_slug(r['node_id'])}",
        })

    blocked = []
    for sig in sorted(blocked_by_signal):
        nodes = sorted(blocked_by_signal[sig],
                       key=lambda r: (r["corpus"], r["node_id"]))
        blocked.append({
            "signal": sig,
            "node_count": len(nodes),
            "nodes": nodes,
        })

    return {
        "derived_from": {"census_portfolio_sha256": census_sha},
        "ready": ready,
        "blocked": blocked,
        "honesty": _HONESTY,
    }


def _write(frontier: dict, out_path: str) -> None:
    with open(out_path, "w") as fh:
        json.dump(frontier, fh, indent=1, sort_keys=True)
        fh.write("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sources", default="specs/mathsources",
                    help="corpus root (dirs holding nodes.jsonl; top-level "
                         "*.txt are the intaken sources)")
    ap.add_argument("--results", default="results",
                    help="dir holding census_portfolio.json; frontier.json "
                         "is written here")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("frontier"):
        frontier = build_frontier(args.sources, args.results)
    out_path = os.path.join(args.results, "frontier.json")
    _write(frontier, out_path)
    print(f"frontier: {len(frontier['ready'])} ready, "
          f"{len(frontier['blocked'])} blocked groups -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""One-command corpus intake: fetch -> extract -> fetch_meta -> nodes.jsonl.

The C1/C2 cycles ran this pipeline from session-scratch scripts that died
with the session; the C3 cadence (recurring driver sessions) needs it
COMMITTED.  This driver owns the whole network-at-intake step:

  1. FETCH (the only networked stage): BFS-crawl the site's same-directory
     ``*.html`` pages starting at the index, skipping the dependency-graph
     page.  Works for both observed site shapes (plasTeX leanblueprint
     ``sect*.html`` / named-chapter pages; Sphinx textbook chapters).
  2. EXTRACT (offline): dispatch to the matching adapter --
     ``tools/blueprint_extract.py`` (plasTeX thmwrapper divs) or
     ``tools/sphinx_extract.py`` (Sphinx admonition blocks).
  3. RECORD: write ``specs/mathsources/<name>/nodes.jsonl`` +
     ``fetch_meta.json`` with the source URL, fetch date, page glob, and
     per-page SHA-256 -- the same provenance shape every committed corpus
     carries.

``--pages-dir`` skips the fetch and runs stages 2-3 over already-fetched
pages -- the OFFLINE mode the teeth exercise (nothing in the tests opens a
socket) and the recovery path when a fetch was done elsewhere.

After intake, run ``tools/census_portfolio.py`` (or the tail of
``tools/regen_downstream.py``) to census the grown portfolio.

Blueprint hosts must be allowlisted in the environment's network policy
(USER-GATED, PLAN_FRAGMENT §3 C1); a blocked host surfaces as a fetch
error here, never a silent empty corpus.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import ssl
import sys
import tempfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CA_BUNDLE = "/root/.ccr/ca-bundle.crt"     # the CCR egress proxy's CA, if present
SKIP_PAGES = {"dep_graph_document.html"}

FETCH_NOTE = ("network-at-intake only: pages fetched via the session's egress "
              "proxy; extraction and census are offline "
              "(tools/intake_corpus.py -> tools/{adapter}, "
              "tools/blueprint_census.py)")


def _fetch(url: str) -> str:
    ctx = ssl.create_default_context(
        cafile=_CA_BUNDLE if os.path.exists(_CA_BUNDLE) else None)
    with urllib.request.urlopen(url, timeout=60, context=ctx) as r:
        return r.read().decode("utf-8", errors="replace")


def crawl(base_url: str, out_dir: str) -> list:
    """BFS over same-directory ``*.html`` links from the index; each page
    saved once under its original name.  Returns the sorted page list."""
    os.makedirs(out_dir, exist_ok=True)
    seen: set = set()
    queue = ["index.html"]
    while queue:
        page = queue.pop(0)
        if page in seen or page in SKIP_PAGES:
            continue
        seen.add(page)
        html = _fetch(base_url if page == "index.html" else base_url + page)
        with open(os.path.join(out_dir, page), "w", encoding="utf-8") as fh:
            fh.write(html)
        for m in re.findall(r'href="([^"#/:]+\.html)"', html):
            if m not in seen and m not in SKIP_PAGES:
                queue.append(m)
    return sorted(seen)


def extract(adapter: str, pages_dir: str, nodes_path: str, glob_pat: str) -> int:
    if adapter == "blueprint":
        from tools import blueprint_extract as mod
    elif adapter == "sphinx":
        from tools import sphinx_extract as mod
    else:
        raise SystemExit(f"unknown adapter {adapter!r} (blueprint|sphinx)")
    nodes = mod.extract_site(pages_dir, glob_pat)
    with open(nodes_path, "w", encoding="utf-8") as fh:
        for n in nodes:
            fh.write(json.dumps(n, sort_keys=True) + "\n")
    return len(nodes)


def write_meta(dest: str, pages_dir: str, *, source: str, project: str,
               adapter: str, glob_pat: str, n_nodes: int, date: str) -> dict:
    shas = {}
    for page in sorted(os.listdir(pages_dir)):
        with open(os.path.join(pages_dir, page), "rb") as fh:
            shas[page] = hashlib.sha256(fh.read()).hexdigest()
    meta = {
        "fetch_note": FETCH_NOTE.format(adapter=f"{adapter}_extract.py"),
        "fetched_utc": date,
        "n_nodes": n_nodes,
        "pages_glob": glob_pat,
        "pages_sha256": shas,
        "project": project,
        "source": source,
    }
    with open(os.path.join(dest, "fetch_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return meta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True,
                    help="corpus directory name under specs/mathsources/")
    ap.add_argument("--source", required=True,
                    help="site base URL (recorded in fetch_meta; fetched "
                         "unless --pages-dir is given)")
    ap.add_argument("--project", required=True,
                    help="one-line project description for fetch_meta")
    ap.add_argument("--adapter", required=True, choices=("blueprint", "sphinx"),
                    help="extraction adapter (plasTeX blueprint vs Sphinx)")
    ap.add_argument("--glob", default=None,
                    help="content-page glob (default: sect*.html for "
                         "blueprint, *.html otherwise)")
    ap.add_argument("--pages-dir", default=None,
                    help="already-fetched pages dir: skip the network stage")
    ap.add_argument("--date", default=None,
                    help="fetch date recorded in meta (default: today UTC; "
                         "pass explicitly for reproducible replays)")
    ap.add_argument("--sources-root",
                    default=os.path.join(_ROOT, "specs", "mathsources"),
                    help="corpus root (default specs/mathsources)")
    args = ap.parse_args(argv)

    glob_pat = args.glob or ("sect*.html" if args.adapter == "blueprint"
                             else "*.html")
    date = args.date or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%d")

    if args.pages_dir:
        pages_dir = args.pages_dir
    else:
        base = args.source if args.source.endswith("/") else args.source + "/"
        pages_dir = tempfile.mkdtemp(prefix=f"intake_{args.name}_")
        pages = crawl(base, pages_dir)
        print(f"fetched {len(pages)} pages -> {pages_dir}")

    dest = os.path.join(args.sources_root, args.name)
    os.makedirs(dest, exist_ok=True)
    nodes_path = os.path.join(dest, "nodes.jsonl")
    n = extract(args.adapter, pages_dir, nodes_path, glob_pat)
    meta = write_meta(dest, pages_dir, source=args.source,
                      project=args.project, adapter=args.adapter,
                      glob_pat=glob_pat, n_nodes=n, date=date)
    print(f"intake {args.name}: {n} nodes, {len(meta['pages_sha256'])} pages "
          f"-> {os.path.relpath(dest, _ROOT)}")
    print("next: python3 tools/census_portfolio.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

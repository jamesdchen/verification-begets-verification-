#!/usr/bin/env python3
"""Blueprint site -> nodes JSONL (the intake half of the fragment census).

Companion to ``tools/blueprint_census.py`` (which is network-free by design):
this tool turns an ALREADY-FETCHED leanblueprint site -- a directory of
``*.html`` content pages, plastex output -- into the census's input corpus, one
JSON object per node:

    {"label": ..., "kind": ..., "prose": ..., "lean_names": [...]}

Deterministic and LLM-free: pages are processed in sorted filename order,
nodes in document order; the parser is the stdlib HTMLParser walking the
plastex markup shape observed on real blueprint sites:

    <div class="{kind}_thmwrapper ..." id="{label}">
      ...
      <a ... class="lean_decl">{Lean declaration name}</a>   (0..n)
      <div class="{kind}_thmcontent"> {statement HTML} </div>
    </div>

The prose field is the thmcontent's text content with whitespace collapsed;
MathJax LaTeX (``\\(...\\)`` / display math) rides along verbatim, which is
exactly what the census's lexical signals match on.  The FETCH itself (an
``https`` mirror of the site) happens wherever network egress allows and is
recorded by the caller in a sibling meta file; nothing here opens a socket.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from html.parser import HTMLParser


class _BlueprintParser(HTMLParser):
    """One page's node stream.  A tiny state machine over div nesting."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list = []
        self._wrapper = None          # {label, kind, depth, lean_names, prose}
        self._content_depth = None    # div depth of the open thmcontent, if any
        self._lean_pending = False

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            if tag == "a" and self._wrapper is not None:
                cls = dict(attrs).get("class", "")
                if "lean_decl" in cls.split():
                    self._lean_pending = True
            return
        cls = dict(attrs).get("class", "") or ""
        if self._wrapper is None:
            m = re.match(r"([a-zA-Z]+)_thmwrapper(\s|$)", cls)
            if m:
                self._wrapper = {
                    "label": dict(attrs).get("id", ""),
                    "kind": m.group(1).lower(),
                    "depth": 1,
                    "lean_names": [],
                    "prose": [],
                }
            return
        self._wrapper["depth"] += 1
        if self._content_depth is None and re.match(
                r"[a-zA-Z]+_thmcontent(\s|$)", cls):
            self._content_depth = self._wrapper["depth"]

    def handle_endtag(self, tag):
        if tag != "div" or self._wrapper is None:
            return
        if (self._content_depth is not None
                and self._wrapper["depth"] == self._content_depth):
            self._content_depth = None
        self._wrapper["depth"] -= 1
        if self._wrapper["depth"] == 0:
            w = self._wrapper
            self.nodes.append({
                "label": w["label"],
                "kind": w["kind"],
                "prose": re.sub(r"\s+", " ", " ".join(w["prose"])).strip(),
                "lean_names": w["lean_names"],
            })
            self._wrapper = None
            self._lean_pending = False

    def handle_data(self, data):
        if self._wrapper is None:
            return
        if self._lean_pending:
            name = data.strip()
            if name:
                self._wrapper["lean_names"].append(name)
                self._lean_pending = False
            return
        if self._content_depth is not None:
            self._wrapper["prose"].append(data)


def extract_page(html_text: str) -> list:
    """All blueprint nodes on one page, in document order."""
    p = _BlueprintParser()
    p.feed(html_text)
    p.close()
    return p.nodes


class RestatementConflict(Exception):
    """One blueprint label carrying two DIFFERENT statements across pages."""


def extract_site(pages_dir: str, pattern: str = "*.html") -> list:
    """All nodes across the site's content pages, pages in sorted name order.

    ``pattern`` covers plasTeX's ``sect*.html`` and the named-chapter shape
    (``*-chapter.html``, ``chapter*.html``) alike; index and dep-graph pages
    carry no thmwrapper divs, so the wide glob adds no nodes on sect-only
    sites and every intaken corpus records it (``fetch_meta.pages_glob``).

    A wide glob does introduce ONE hazard the narrow one could not: a site
    may render the same node on two pages, and counting it twice would
    inflate the corpus.  MEASURED on prime_number_theorem_and, where
    ``Meissel-Mertens-constant`` is rendered identically in both
    ``explicit-chapter.html`` and ``secondary-chapter.html``.  So a repeated
    label whose record is identical in EVERY field we keep is one node --
    the first in sorted-page order -- while a repeated label whose content
    DIFFERS is an ambiguity no machine may resolve and raises
    ``RestatementConflict`` rather than picking a side.  Both branches are
    no-ops on all six previously-intaken corpora (zero repeated labels)."""
    out: list = []
    seen: dict = {}
    for path in sorted(glob.glob(os.path.join(pages_dir, pattern))):
        with open(path, encoding="utf-8") as fh:
            for node in extract_page(fh.read()):
                label = node["label"]
                prior = seen.get(label) if label else None
                if prior is None:   # an empty label is no identifier: keep it
                    if label:
                        seen[label] = node
                    out.append(node)
                elif prior != node:
                    raise RestatementConflict(
                        f"label {label!r} carries two different statements "
                        f"(second seen in {os.path.basename(path)})")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages_dir", help="directory holding the fetched pages")
    ap.add_argument("--out", required=True, help="output nodes JSONL path")
    ap.add_argument("--glob", default="*.html",
                    help="content-page glob within pages_dir (default "
                         "*.html: covers sect pages and named chapters alike)")
    args = ap.parse_args(argv)
    nodes = extract_site(args.pages_dir, args.glob)
    with open(args.out, "w", encoding="utf-8") as fh:
        for n in nodes:
            fh.write(json.dumps(n, sort_keys=True) + "\n")
    print(f"wrote {len(nodes)} nodes -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

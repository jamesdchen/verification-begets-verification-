#!/usr/bin/env python3
"""Sphinx textbook site -> nodes JSONL (the second intake adapter).

Sibling of ``tools/blueprint_extract.py`` (plasTeX leanblueprint sites): this
one reads a SPHINX-rendered mathematics text -- the observed shape is
Macbeth's *The Mechanics of Proof* (math2001) -- and emits the same census
corpus format, one JSON object per node:

    {"label": ..., "kind": ..., "prose": ..., "lean_names": []}

Markup shape (Sphinx admonitions):

    <div class="admonition-{kind} admonition">
      <p class="admonition-title">{Kind}</p>
      <p> {statement, with LaTeX inside <span class="math ...">\\(...\\)</span>} </p>
      ...
    </div>

Deterministic and LLM-free: pages in sorted filename order, nodes in document
order, labels = ``{page-stem}#{kind}-{NNN}`` with a per-page running index.
STATEMENT kinds only: ``proof`` and ``solution`` admonitions are proofs, not
statements, and are skipped.  ``lean_names`` is always empty -- this corpus
states its Lean inline in code blocks, not via \\lean{} anchors; the census
does not read Lean either way.  The FETCH happens wherever egress allows and
is recorded by the caller in fetch_meta.json; nothing here opens a socket.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from html.parser import HTMLParser

STATEMENT_KINDS = ("definition", "lemma", "theorem", "corollary",
                   "proposition", "problem", "example")


class _SphinxParser(HTMLParser):
    """One page's admonition stream.  A tiny state machine over div nesting."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list = []
        self._kind = None            # open statement admonition's kind
        self._depth = 0              # div depth inside the open admonition
        self._in_title = False
        self._prose: list = []

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "") or ""
        if tag == "div":
            if self._kind is None:
                m = re.match(r"admonition-([a-z]+)\s", cls + " ")
                if m and "admonition" in cls.split() \
                        and m.group(1) in STATEMENT_KINDS:
                    self._kind = m.group(1)
                    self._depth = 1
                    self._prose = []
            else:
                self._depth += 1
            return
        if tag == "p" and self._kind is not None \
                and "admonition-title" in cls.split():
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "p" and self._in_title:
            self._in_title = False
            return
        if tag != "div" or self._kind is None:
            return
        self._depth -= 1
        if self._depth == 0:
            self.nodes.append({
                "kind": self._kind,
                "prose": re.sub(r"\s+", " ", " ".join(self._prose)).strip(),
            })
            self._kind = None

    def handle_data(self, data):
        if self._kind is not None and not self._in_title:
            self._prose.append(data)


def extract_page(html_text: str) -> list:
    p = _SphinxParser()
    p.feed(html_text)
    p.close()
    return p.nodes


def extract_site(pages_dir: str, pattern: str = "*.html") -> list:
    """All statement nodes across the site, pages in sorted name order, labels
    stamped ``{page-stem}#{kind}-{NNN}`` in document order."""
    out = []
    for path in sorted(glob.glob(os.path.join(pages_dir, pattern))):
        stem = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            nodes = extract_page(fh.read())
        counters: dict = {}
        for n in nodes:
            k = n["kind"]
            counters[k] = counters.get(k, 0) + 1
            out.append({
                "label": f"{stem}#{k}-{counters[k]:03d}",
                "kind": k,
                "prose": n["prose"],
                "lean_names": [],
            })
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages_dir", help="directory holding fetched *.html pages")
    ap.add_argument("--out", required=True, help="output nodes JSONL path")
    ap.add_argument("--glob", default="*.html",
                    help="content-page glob within pages_dir")
    args = ap.parse_args(argv)
    nodes = extract_site(args.pages_dir, args.glob)
    with open(args.out, "w", encoding="utf-8") as fh:
        for n in nodes:
            fh.write(json.dumps(n, sort_keys=True) + "\n")
    print(f"wrote {len(nodes)} nodes -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

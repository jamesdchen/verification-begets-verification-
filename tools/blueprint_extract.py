#!/usr/bin/env python3
"""Blueprint site -> nodes JSONL (the intake half of the fragment census).

Companion to ``tools/blueprint_census.py`` (which is network-free by design):
this tool turns an ALREADY-FETCHED leanblueprint site -- a directory of
``sect*.html`` pages, plastex output -- into the census's input corpus, one
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


def extract_site(pages_dir: str) -> list:
    """All nodes across the site's sect*.html, pages in sorted name order."""
    out = []
    for path in sorted(glob.glob(os.path.join(pages_dir, "sect*.html"))):
        with open(path, encoding="utf-8") as fh:
            out.extend(extract_page(fh.read()))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages_dir", help="directory holding fetched sect*.html")
    ap.add_argument("--out", required=True, help="output nodes JSONL path")
    args = ap.parse_args(argv)
    nodes = extract_site(args.pages_dir)
    with open(args.out, "w", encoding="utf-8") as fh:
        for n in nodes:
            fh.write(json.dumps(n, sort_keys=True) + "\n")
    print(f"wrote {len(nodes)} nodes -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

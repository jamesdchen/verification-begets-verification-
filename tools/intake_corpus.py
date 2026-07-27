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
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CA_BUNDLE = "/root/.ccr/ca-bundle.crt"     # the CCR egress proxy's CA, if present
SKIP_PAGES = {"dep_graph_document.html"}

FETCH_NOTE = ("network-at-intake only: pages fetched via the session's egress "
              "proxy; extraction and census are offline "
              "(tools/intake_corpus.py -> tools/{adapter}, "
              "tools/blueprint_census.py)")

#: Sent on every intake fetch.  Left at urllib's default
#: (``Python-urllib/<v>``), a CDN bot fence answers 403 BEFORE the origin is
#: reached, and the intake reads that as the corpus refusing -- MEASURED
#: 2026-07-27 on the ``carleson`` candidate: the same URL returned 403 to
#: ``Python-urllib/3.11`` and 200 to an ordinary browser UA, through the same
#: egress proxy, in the same second.  Every corpus intaken before it happened
#: to sit on GitHub Pages, which does not fence, which is why seven intakes
#: never surfaced this.  Identify the crawler honestly rather than
#: impersonate a browser: the string names the project and the tool.
USER_AGENT = ("Mozilla/5.0 (compatible; cgb-corpus-intake/1.0; "
              "+https://github.com/jamesdchen/verification-begets-verification-)")


#: How an intake failure must be READ, keyed by HTTP status class.  The
#: cycle-31 measurement (USER_AGENT above) fixed one wire artifact and left
#: the general defect standing: the driver still had to diagnose the wire BY
#: HAND before it could record anything, because a bare traceback says only
#: "the fetch died".  The three readings are genuinely different acts:
#:
#:   404/410 -- a DECIDED FACT ABOUT THE DECLARATION.  The origin answered,
#:     and it says this resource does not exist.  Retrying cannot change it;
#:     the honest product is `corpus_candidates.py --mark NAME refused`.
#:   403/401/429 -- the origin REFUSED US rather than denying the resource.
#:     That is the carleson shape (a bot fence) or a rate limit, and it is
#:     diagnosed before it is recorded -- a fence filed as demand data is
#:     exactly the honesty failure cycle 31 caught.
#:   5xx / transport -- WEATHER.  Retry under the hiccup protocol; a
#:     transport error is NEVER a reading (CLAUDE.md's honesty rules).
#:
#: MEASURED 2026-07-27 (C3 cycle 33) on the `flt` candidate: the declared
#: blueprint URL answered 404 while the project root answered 200, so the
#: declaration was wrong rather than the wire being blocked -- and telling
#: those apart cost a hand-run curl session that this table now makes
#: unnecessary.
FETCH_READINGS = {
    "resource-absent": (
        frozenset({404, 410}),
        "the origin ANSWERED and says this resource does not exist -- a "
        "decided fact about the DECLARATION, not about the wire.  Retrying "
        "cannot change it: record it with `corpus_candidates.py --mark NAME "
        "refused --reason ...` so the registry carries the evidence",
    ),
    "origin-refused-us": (
        frozenset({401, 403, 429}),
        "the origin refused THIS CLIENT rather than denying the resource "
        "(a CDN bot fence, an auth wall, or a rate limit).  DIAGNOSE before "
        "recording -- the carleson shape, where a wire-side fence was "
        "indistinguishable from a corpus refusing",
    ),
}


class IntakeFetchError(RuntimeError):
    """A fetch that failed, carrying HOW TO READ IT.

    ``reading`` is a key of ``FETCH_READINGS`` or ``"transport"``; ``status``
    is the HTTP status when there was one, else ``None``."""

    def __init__(self, url, reading, guidance, status=None, cause=None):
        self.url, self.reading, self.status = url, reading, status
        self.guidance, self.cause = guidance, cause
        super().__init__(
            f"intake fetch {reading.upper()}"
            f"{'' if status is None else f' (HTTP {status})'}: {url}\n"
            f"  how to read it: {guidance}"
            + (f"\n  underlying: {cause}" if cause is not None else ""))


def classify_fetch_failure(url, status=None, cause=None) -> IntakeFetchError:
    """The reading, DERIVED from the status -- so a session never has to
    hand-diagnose the wire to know which act it is looking at."""
    for reading, (codes, guidance) in FETCH_READINGS.items():
        if status in codes:
            return IntakeFetchError(url, reading, guidance, status, cause)
    return IntakeFetchError(
        url, "transport",
        "server-side or transport failure -- WEATHER, never a verdict: retry "
        "under the hiccup protocol (2s/4s/8s/16s) and never record a refusal, "
        "a park or any ledger row from it",
        status, cause)


def _fetch(url: str) -> str:
    ctx = ssl.create_default_context(
        cafile=_CA_BUNDLE if os.path.exists(_CA_BUNDLE) else None)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise classify_fetch_failure(url, status=e.code, cause=e) from e
    except urllib.error.URLError as e:
        raise classify_fetch_failure(url, status=None, cause=e) from e


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
    """Extract, refusing to lay down a SILENTLY EMPTY corpus.

    The module docstring promises a blocked host surfaces as an error and
    "never a silent empty corpus"; an adapter that matches no page breaks
    that promise just as thoroughly as a 403 does.  MEASURED 2026-07-26 on
    prime_number_theorem_and: the fetch retrieved 15 pages carrying 945
    nodes, the then-default ``sect*.html`` glob matched only two node-free
    front-matter pages, and the intake reported success while writing a
    zero-node corpus.  So: pages present but no node extracted is a REFUSAL
    -- raised before anything is written, naming the glob and the pages it
    saw, so the caller records a refusal instead of committing an empty
    directory.  A genuinely empty PAGE SET is the caller's fetch error."""
    if adapter == "blueprint":
        from tools import blueprint_extract as mod
    elif adapter == "sphinx":
        from tools import sphinx_extract as mod
    else:
        raise SystemExit(f"unknown adapter {adapter!r} (blueprint|sphinx)")
    nodes = mod.extract_site(pages_dir, glob_pat)
    if not nodes:
        pages = sorted(p for p in os.listdir(pages_dir) if p.endswith(".html"))
        raise SystemExit(
            f"intake refused: adapter {adapter!r} with glob {glob_pat!r} "
            f"extracted 0 nodes from {len(pages)} fetched page(s) "
            f"({', '.join(pages[:6])}{' ...' if len(pages) > 6 else ''}). "
            "Nothing written -- record the refusal rather than committing "
            "an empty corpus.")
    os.makedirs(os.path.dirname(nodes_path), exist_ok=True)
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
                    help="content-page glob (default *.html for both "
                         "adapters: plasTeX sect pages and named chapters)")
    ap.add_argument("--pages-dir", default=None,
                    help="already-fetched pages dir: skip the network stage")
    ap.add_argument("--date", default=None,
                    help="fetch date recorded in meta (default: today UTC; "
                         "pass explicitly for reproducible replays)")
    ap.add_argument("--sources-root",
                    default=os.path.join(_ROOT, "specs", "mathsources"),
                    help="corpus root (default specs/mathsources)")
    args = ap.parse_args(argv)

    glob_pat = args.glob or "*.html"
    date = args.date or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%d")

    if args.pages_dir:
        pages_dir = args.pages_dir
    else:
        base = args.source if args.source.endswith("/") else args.source + "/"
        pages_dir = tempfile.mkdtemp(prefix=f"intake_{args.name}_")
        try:
            pages = crawl(base, pages_dir)
        except IntakeFetchError as e:
            # The READING is the product here, so it goes to the driver as a
            # message rather than as a traceback: a stack trace says only
            # "the fetch died" and leaves the wire to be diagnosed by hand.
            print(str(e), file=sys.stderr)
            return 2
        print(f"fetched {len(pages)} pages -> {pages_dir}")

    # dest is created by extract(), and only once extraction has produced
    # nodes -- a refused intake leaves no directory behind at all.
    dest = os.path.join(args.sources_root, args.name)
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

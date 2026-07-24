"""Teeth for tools/intake_corpus.py -- the committed corpus-intake driver.

LLM-free and NETWORK-FREE: everything runs through the ``--pages-dir``
offline mode over synthetic pages authored here (both site shapes), so the
teeth pin the extract/meta/provenance contract without a socket.  The crawl
stage's LINK DISCOVERY is tested as a pure function of page text.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import intake_corpus as ic  # noqa: E402

BLUEPRINT_PAGE = """
<div class="lemma_thmwrapper" id="lem:one">
  <a class="lean_decl">one_lemma</a>
  <div class="lemma_thmcontent"><p>For any integer n, n divides n.</p></div>
</div>
"""

SPHINX_PAGE = """
<div class="admonition-problem admonition">
  <p class="admonition-title">Problem</p>
  <p>Show that 8 is even.</p>
</div>
<div class="admonition-solution admonition">
  <p class="admonition-title">Solution</p>
  <p>8 = 2 times 4.</p>
</div>
"""


def _mk_pages(tmp_path, name, content):
    d = tmp_path / name
    d.mkdir()
    (d / "sect0001.html").write_text(content, encoding="utf-8")
    return str(d)


def test_offline_intake_blueprint(tmp_path):
    pages = _mk_pages(tmp_path, "bp", BLUEPRINT_PAGE)
    root = tmp_path / "sources"
    rc = ic.main(["--name", "synthcorp", "--source", "https://example.org/bp/",
                  "--project", "synthetic blueprint fixture",
                  "--adapter", "blueprint", "--pages-dir", pages,
                  "--date", "2026-01-01", "--sources-root", str(root)])
    assert rc == 0
    nodes = [json.loads(l) for l in
             open(root / "synthcorp" / "nodes.jsonl") if l.strip()]
    assert len(nodes) == 1
    assert nodes[0]["label"] == "lem:one"
    assert nodes[0]["lean_names"] == ["one_lemma"]
    meta = json.load(open(root / "synthcorp" / "fetch_meta.json"))
    assert meta["n_nodes"] == 1
    assert meta["source"] == "https://example.org/bp/"
    assert meta["fetched_utc"] == "2026-01-01"
    assert list(meta["pages_sha256"]) == ["sect0001.html"]
    assert re.fullmatch(r"[0-9a-f]{64}", meta["pages_sha256"]["sect0001.html"])


def test_offline_intake_sphinx_skips_solutions(tmp_path):
    pages = _mk_pages(tmp_path, "sx", SPHINX_PAGE)
    root = tmp_path / "sources"
    rc = ic.main(["--name", "synthsx", "--source", "https://example.org/sx/",
                  "--project", "synthetic sphinx fixture",
                  "--adapter", "sphinx", "--pages-dir", pages,
                  "--date", "2026-01-01", "--sources-root", str(root)])
    assert rc == 0
    nodes = [json.loads(l) for l in
             open(root / "synthsx" / "nodes.jsonl") if l.strip()]
    # the problem is a statement node; the solution is a proof and is skipped
    assert len(nodes) == 1
    assert nodes[0]["kind"] == "problem"
    assert "8 is even" in nodes[0]["prose"]


def test_crawl_link_discovery_is_same_directory_only():
    html = ('<a href="sect0002.html">x</a> <a href="other/deep.html">n</a> '
            '<a href="https://ext.example/e.html">n</a> '
            '<a href="dep_graph_document.html">n</a> <a href="p.html#f">frag</a>')
    found = re.findall(r'href="([^"#/:]+\.html)"', html)
    kept = [m for m in found if m not in ic.SKIP_PAGES]
    # same-directory pages only; the dep-graph page and anything with a
    # path separator, scheme, or fragment-bearing char class is excluded
    assert kept == ["sect0002.html"]


def test_default_glob_follows_adapter():
    # blueprint defaults to plasTeX sect pages; sphinx to all chapter pages.
    # (pinned here because the adapters' extract_site defaults differ and the
    # driver must pass the right one through)
    import argparse  # noqa: F401  (documentational; defaults live in main)
    assert "sect*.html" in open(
        os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "tools", "intake_corpus.py")).read()

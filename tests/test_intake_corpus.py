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


def test_default_glob_reaches_named_chapter_pages(tmp_path):
    """The blueprint default must cover the NAMED-CHAPTER site shape.

    MEASURED 2026-07-26 on prime_number_theorem_and: the default was
    ``sect*.html``, the site renders its nodes into ``*-chapter.html``, and
    the intake wrote a zero-node corpus while reporting success.  This runs
    the driver with NO --glob over a named-chapter page set, so it reds if
    the default ever narrows back to the sect-only pattern."""
    d = tmp_path / "named"
    d.mkdir()
    (d / "primary-chapter.html").write_text(BLUEPRINT_PAGE, encoding="utf-8")
    root = tmp_path / "sources"
    rc = ic.main(["--name", "namedcorp", "--source", "https://example.org/bp/",
                  "--project", "synthetic named-chapter fixture",
                  "--adapter", "blueprint", "--pages-dir", str(d),
                  "--date", "2026-01-01", "--sources-root", str(root)])
    assert rc == 0
    nodes = [json.loads(l) for l in
             open(root / "namedcorp" / "nodes.jsonl") if l.strip()]
    assert [n["label"] for n in nodes] == ["lem:one"]
    assert json.load(open(root / "namedcorp" / "fetch_meta.json"))[
        "pages_glob"] == "*.html"


def test_zero_extracted_nodes_refuses_and_writes_nothing(tmp_path):
    """Pages fetched but no node extracted is a REFUSAL, not a corpus.

    The module docstring promises "never a silent empty corpus"; an adapter
    matching no page breaks that promise exactly as a blocked host would.
    The refusal must also leave NO directory behind, so a driver cannot
    commit an empty corpus it never noticed was empty."""
    d = tmp_path / "nonodes"
    d.mkdir()
    (d / "index.html").write_text("<p>front matter only</p>", encoding="utf-8")
    root = tmp_path / "sources"
    try:
        ic.main(["--name", "emptycorp", "--source", "https://example.org/bp/",
                 "--project", "synthetic node-free fixture",
                 "--adapter", "blueprint", "--pages-dir", str(d),
                 "--date", "2026-01-01", "--sources-root", str(root)])
    except SystemExit as exc:
        msg = str(exc)
    else:
        raise AssertionError("a zero-node extraction must refuse, not succeed")
    assert "intake refused" in msg and "0 nodes" in msg
    assert "index.html" in msg          # names what it actually saw
    assert not os.path.exists(root / "emptycorp")

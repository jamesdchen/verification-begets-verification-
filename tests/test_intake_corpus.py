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


def test_the_fetch_identifies_itself_and_never_ships_the_urllib_default():
    """A CDN bot fence answers urllib's default UA with 403 before the origin.

    MEASURED 2026-07-27 on the ``carleson`` candidate: the same URL, through
    the same egress proxy, in the same second, returned 403 to
    ``Python-urllib/3.11`` and 200 to an ordinary browser UA.  Read through
    ``_fetch``, that 403 is indistinguishable from a corpus that refused --
    so a driver would have recorded a wire-side bot fence as demand data,
    which the honesty rules forbid (a transport error is not a reading).

    Network-free: ``urlopen`` is stubbed, so this pins the REQUEST the crawler
    builds and opens no socket.  Both directions matter -- the header must be
    present, and it must not be the default the fence rejects."""
    seen = {}

    class _Resp:
        def read(self):
            return b"<html></html>"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=None, context=None):
        seen["req"] = req
        return _Resp()

    real = ic.urllib.request.urlopen
    ic.urllib.request.urlopen = _fake_urlopen
    try:
        ic._fetch("https://example.org/bp/index.html")
    finally:
        ic.urllib.request.urlopen = real

    req = seen["req"]
    assert isinstance(req, ic.urllib.request.Request), (
        "_fetch must build a Request so its headers are carriable; a bare "
        "URL string ships urllib's default User-Agent")
    ua = req.get_header("User-agent")
    assert ua, "every intake fetch must send a User-Agent"
    assert "Python-urllib" not in ua, (
        "the urllib default is exactly what the bot fence 403s")
    assert ua == ic.USER_AGENT
    assert "cgb-corpus-intake" in ua, (
        "identify the crawler honestly rather than impersonate a browser")


# --- the fetch-failure READING (C3 cycle 33) --------------------------------
def _stub_urlopen_raising(exc):
    """Network-free: every fetch raises ``exc`` instead of opening a socket."""
    def _fake(req, timeout=None, context=None):
        raise exc
    return _fake


def _fetch_error(exc):
    real = ic.urllib.request.urlopen
    ic.urllib.request.urlopen = _stub_urlopen_raising(exc)
    try:
        try:
            ic._fetch("https://example.org/bp/index.html")
        except ic.IntakeFetchError as e:
            return e
    finally:
        ic.urllib.request.urlopen = real
    raise AssertionError("_fetch swallowed a failed fetch")


def _http_error(code):
    return ic.urllib.error.HTTPError(
        "https://example.org/bp/index.html", code, "msg", {}, None)


def test_a_404_reads_as_a_fact_about_the_declaration_not_about_the_wire():
    """MEASURED 2026-07-27 (C3 cycle 33) on the `flt` candidate: the declared
    blueprint URL answered 404 while the project root answered 200.

    The origin ANSWERED -- so this is a decided fact about the declaration,
    not weather, and retrying it is wasted.  The cycle-31 fix made one wire
    artifact legible; this makes the READING itself derived, so a driver
    never again hand-diagnoses the wire with curl before it may record."""
    err = _fetch_error(_http_error(404))
    assert err.reading == "resource-absent", err.reading
    assert err.status == 404
    assert "does not exist" in err.guidance
    assert "--mark" in err.guidance, (
        "the guidance must name the ACT: a resource-absent fetch is recorded "
        "as a refused registry row, which is what makes the registry evidence")
    # 410 is the same act with a different spelling.
    assert _fetch_error(_http_error(410)).reading == "resource-absent"


def test_a_403_stays_DIAGNOSE_FIRST_and_is_never_the_same_act_as_a_404():
    """The carleson shape.  A fence refuses the CLIENT, not the resource, and
    filing it as demand data is the honesty failure cycle 31 caught -- so it
    must never collapse into the record-it-now reading above."""
    for code in (401, 403, 429):
        err = _fetch_error(_http_error(code))
        assert err.reading == "origin-refused-us", (code, err.reading)
        assert "DIAGNOSE before" in err.guidance
        assert "--mark" not in err.guidance, (
            f"HTTP {code} must not carry the record-it-now guidance: a bot "
            f"fence recorded as a corpus refusal is demand data that is false")


def test_a_5xx_or_a_transport_failure_is_WEATHER_and_never_a_reading():
    """CLAUDE.md's honesty rule, mechanized: a transport error is not a
    reading, so its guidance must send the driver to the hiccup protocol and
    must never authorize a ledger row."""
    for exc in (_http_error(500), _http_error(503),
                ic.urllib.error.URLError("connection reset")):
        err = _fetch_error(exc)
        assert err.reading == "transport", err.reading
        assert "WEATHER" in err.guidance
        assert "never record a refusal" in err.guidance
        assert "--mark" not in err.guidance


def test_every_reading_is_distinct_and_the_status_classes_never_overlap():
    """The dead-branch canary: a status may resolve to exactly ONE reading,
    or the table has two answers to one question."""
    seen = set()
    for reading, (codes, guidance) in ic.FETCH_READINGS.items():
        assert codes, reading
        assert not (codes & seen), f"{reading} overlaps an earlier class"
        seen |= set(codes)
        assert isinstance(guidance, str) and len(guidance.split()) >= 8, reading


def test_the_cli_reports_the_reading_instead_of_a_traceback():
    """A stack trace says only 'the fetch died'.  The whole point of the
    classification is that the driver reads the ACT off the failure, so the
    CLI must surface it and exit non-zero rather than raise."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools", "intake_corpus.py")).read()
    assert "except IntakeFetchError as e:" in src, (
        "main() must catch the classified error; an uncaught one reaches the "
        "driver as a traceback with the reading buried in it")
    assert "return 2" in src, "a refused intake must exit non-zero"


# --- the absence SCOPE (C3 cycle 34) ------------------------------------
#
# Two 404s, one per cycle, and they are not the same fact: `flt`'s project
# root answered 200 while the blueprint path did not, and `lean_cam_combi`
# answered 404 at the bare host.  Both cycles told them apart by hand with
# curl before they were allowed to record.  These teeth pin the split so a
# third cycle does not pay for it again.  Every one injects its probe: the
# scope classifier must be decidable with no socket, or it could not be
# tested at all.

_DECLARED = "https://acct.example.io/Project/blueprint/"


def _absent(probe):
    return ic.classify_fetch_failure(
        _DECLARED, status=404, cause=_http_error(404), probe=probe)


def test_a_404_under_a_serving_origin_reads_as_PATH_absent():
    """The `flt` shape (C3 cycle 33).  The origin publishes, so what is wrong
    is the declared PATH -- and the guidance must say the re-declaration
    stays inside the project without ever naming a path to move to."""
    err = _absent(lambda root: 200)
    assert err.reading == "resource-absent", err.reading
    assert err.scope == "path-absent", err.scope
    assert "ORIGIN SERVES" in ic.ABSENCE_SCOPES[err.scope]
    assert "MAINTAINER call" in ic.ABSENCE_SCOPES[err.scope], (
        "path-absent must hand the re-declaration to a human: a tool that "
        "picked the replacement path would be shopping, not diagnosing")
    assert "--mark" in err.guidance, "an absence is still recordable evidence"


def test_a_404_at_the_bare_ORIGIN_reads_as_HOST_absent():
    """The `lean_cam_combi` shape (C3 cycle 34): every path under the host
    404s, the host included, so the declaration's ORIGIN is wrong.  This must
    not collapse into path-absent -- they send a maintainer to different
    places, which is the whole reason the scope exists."""
    err = _absent(lambda root: 404)
    assert err.scope == "host-absent", err.scope
    assert "SERVES NOTHING" in ic.ABSENCE_SCOPES[err.scope]
    assert err.scope != _absent(lambda root: 200).scope, (
        "a serving origin and a dead origin must never read the same")
    # 410 at the root is the same absence with a different spelling.
    assert _absent(lambda root: 410).scope == "host-absent"


def test_an_unprobeable_ORIGIN_is_scope_unknown_and_never_guessed():
    """The honesty half.  A probe that errors, times out, answers nothing, or
    is absent entirely leaves the scope UNKNOWN -- and never disturbs the
    reading it refines, because a 404 at the declared URL is already
    decided."""
    def boom(root):
        raise OSError("connection reset")
    for probe in (boom, lambda root: None, lambda root: 500, None):
        err = _absent(probe)
        assert err.scope == "scope-unknown", (probe, err.scope)
        assert err.reading == "resource-absent", (
            "an unreadable probe must never un-decide the reading: the "
            "declared URL answered 404 and that stands")


def test_the_scope_probe_touches_the_ORIGIN_ROOT_and_nothing_else():
    """The bound that keeps this a diagnosis rather than URL-shopping: the
    probe is called exactly once, with the bare `scheme://netloc/`, and the
    error never carries a substitute address."""
    seen = []

    def record(root):
        seen.append(root)
        return 200

    err = _absent(record)
    assert seen == ["https://acct.example.io/"], seen
    assert ic.origin_root(_DECLARED) == "https://acct.example.io/"
    assert "/Project" not in ic.ABSENCE_SCOPES[err.scope]
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools", "intake_corpus.py")).read()
    body = src[src.index("def classify_absence_scope"):
               src.index("class IntakeFetchError")]
    for shopped in ("index.html", ".pdf", "blueprint", "for ", "while "):
        assert shopped not in body, (
            f"classify_absence_scope must not walk candidate paths ({shopped!r} "
            f"appears in it); it reads the origin root once and stops")


def test_only_an_ABSENCE_carries_a_scope():
    """A fence and a 5xx have no scope to ask about -- probing an origin that
    refused us or fell over says nothing about a declaration, and a scope
    attached there would read as evidence that was never gathered."""
    for code in (401, 403, 429, 500, 503):
        err = ic.classify_fetch_failure(_DECLARED, status=code,
                                        cause=_http_error(code),
                                        probe=lambda root: 404)
        assert err.scope is None, (code, err.scope)
        assert "scope" not in str(err), code
    err = ic.classify_fetch_failure(_DECLARED, status=None,
                                    cause=ic.urllib.error.URLError("x"),
                                    probe=lambda root: 200)
    assert err.scope is None


def test_the_scope_reaches_the_MESSAGE_the_driver_actually_reads():
    """The reading is only derived if the driver sees it: a scope computed
    and not printed is the hand-run curl session all over again."""
    text = str(_absent(lambda root: 404))
    assert "[host-absent]" in text, text
    assert "SERVES NOTHING" in text
    assert "https://acct.example.io/" in text, (
        "the message must name the address that was probed, so the reading "
        "is checkable rather than asserted")


def test_the_live_fetch_wires_the_probe_in():
    """The classifier is only useful on the path that actually runs.  Pinned
    by source inspection because the alternative is a socket."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools", "intake_corpus.py")).read()
    fetch = src[src.index("def _fetch("):src.index("def crawl(")]
    assert fetch.count("probe=_probe_origin_status") == 2, (
        "both failure arms of _fetch must pass the probe, or a driver gets "
        "an unscoped absence on the very path this was built for")

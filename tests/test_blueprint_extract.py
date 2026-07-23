"""Teeth for tools/blueprint_extract.py (blueprint intake, offline half).

LLM-free, Lean-free, network-free: the page below is a SYNTHETIC fixture in
the plastex markup shape the extractor targets -- not a quote from any real
blueprint.  The real-corpus artifacts live in specs/mathsources/pfr/ with
their fetch provenance.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.blueprint_extract import extract_page

PAGE = """
<html><body><div class="main-text">
<h1>1 Fixture</h1>
<div class="lemma_thmwrapper theorem-style-plain" id="fix:one">
  <div class="lemma_thmheading">
    <span class="lemma_thmcaption">Lemma</span>
    <div class="thm_header_hidden_extras">
      <ul class="uses">
        <li><a href="x" class="lean_decl">Fix.one</a></li>
        <li><a href="y" class="lean_decl">Fix.one'</a></li>
      </ul>
    </div>
  </div>
  <div class="lemma_thmcontent">
  <p> If \\(d\\) divides   \\(a\\) then </p>
  <div class="displaymath">\\[ d \\mid a + a \\]</div>
  <p> holds. </p>
  </div>
</div>
<div class="proof_wrapper" id="pf"><div class="proof_content">
  <p>Not a node.</p>
</div></div>
<div class="definition_thmwrapper" id="fix:two">
  <div class="definition_thmheading">
    <span class="definition_thmcaption">Definition</span>
  </div>
  <div class="definition_thmcontent"><p>A bare node, no Lean link.</p></div>
</div>
</div></body></html>
"""


def test_nodes_in_document_order_with_shape():
    nodes = extract_page(PAGE)
    assert [n["label"] for n in nodes] == ["fix:one", "fix:two"]
    assert [n["kind"] for n in nodes] == ["lemma", "definition"]


def test_lean_names_and_prose_capture():
    one, two = extract_page(PAGE)
    assert one["lean_names"] == ["Fix.one", "Fix.one'"]
    # whitespace collapsed; nested displaymath div's text kept in place;
    # heading/caption text NOT leaked into prose.
    assert one["prose"] == (
        "If \\(d\\) divides \\(a\\) then \\[ d \\mid a + a \\] holds.")
    assert "Lemma" not in one["prose"]
    assert two["lean_names"] == []
    assert two["prose"] == "A bare node, no Lean link."


def test_proof_wrappers_are_not_nodes():
    assert all("proof" not in n["kind"] for n in extract_page(PAGE))


def test_deterministic():
    assert extract_page(PAGE) == extract_page(PAGE)

"""Teeth for WP-T4b, the autonomous proposal EMITTER (tools/subtree_mine.py).

The miner half of auto-R2: mine recurring self-contained pred subtrees from a
corpus of certified exogenous readings, mechanically lift each to a proposal
row, and STAGE it under ``specs/mathsources/operators/proposed/`` as inert data.
The R2 battery remains the sole admitter; this module imports NO admission code.

Teeth (COMPRESSION.md §11.4 / the WP-T4b package):
  (a) run on the committed corpus: the mod-congruence subtree
      ``=(mod(a,m),mod(b,m))`` (4 witnesses per the census) is emitted, with the
      SHARED modulus preserved (3 params); single-kernel-atom aliases are
      emitted but explicitly ``alias_shaped``-flagged (the emit-with-flag policy).
  (b) determinism: two runs are byte-identical.
  (c) a 1-witness subtree is NOT emitted.
  (d) inertness regression: emitting into a temp registry's ``proposed/`` leaves
      ``parse_math_reading`` and ``load_admitted`` behaviour byte-unchanged --
      the staging dir stays dead to the live path.

Relational / structural asserts; no absolute solver constants; nothing here runs
the battery.  ``load_corpus`` replays the committed checkpoint (a few seconds).
"""
import json
import os
import tempfile

import common
import tools.subtree_mine as sm
from generators import operator_growth as og
from generators.math_reading import parse_math_reading

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The mod-congruence subtree, alpha-canonically lifted: shared modulus v1.
CONG_DEF = {"op": "=", "args": [
    {"op": "mod", "args": [{"ref": "v0"}, {"ref": "v1"}]},
    {"op": "mod", "args": [{"ref": "v2"}, {"ref": "v1"}]}]}


# ------------------------------------------------------------ small unit checks
def test_alpha_canonical_preserves_sharing():
    """A repeated ref becomes ONE param (self-containment), and a differently-
    named but structurally-identical subtree lifts to the SAME definition."""
    sub_a = {"op": "=", "args": [
        {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
        {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}
    sub_b = {"op": "=", "args": [
        {"op": "mod", "args": [{"ref": "x"}, {"ref": "k"}]},
        {"op": "mod", "args": [{"ref": "y"}, {"ref": "k"}]}]}
    def_a, params_a = sm.canonical_subtree(sub_a)
    def_b, params_b = sm.canonical_subtree(sub_b)
    assert def_a == def_b == CONG_DEF
    assert params_a == params_b == ["v0", "v1", "v2"]      # 3, NOT 4: m shared

    # an INDEPENDENT modulus lifts to a DIFFERENT (4-param) definition -- the
    # census's full ref-abstraction would conflate these two; the miner does not.
    indep = {"op": "=", "args": [
        {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
        {"op": "mod", "args": [{"ref": "b"}, {"ref": "n"}]}]}
    def_i, params_i = sm.canonical_subtree(indep)
    assert def_i != CONG_DEF
    assert params_i == ["v0", "v1", "v2", "v3"]


def test_self_containment_refuses_non_plain_leaf():
    """A leaf that is not a plain ref/lit (a bound-variable-shaped node) is
    refused -- the capture guard (§11.4)."""
    ok, _ = sm._self_contained(CONG_DEF)
    assert ok
    bad = {"op": "=", "args": [{"bound": "i"}, {"ref": "a"}]}
    ok, reason = sm._self_contained(bad)
    assert not ok and "self-contained" in reason


def test_word_is_content_derived_and_valid_identifier():
    row = sm.candidate_to_row({
        "definition": CONG_DEF, "params": ["v0", "v1", "v2"], "arity": 3,
        "witnesses": 4, "witness_sids": ["s1", "s2", "s3", "s4"],
        "alias_shaped": False, "carriers_observed": ["Int", "Nat"]})
    assert row["word"] == "op_" + common.sha256_json(CONG_DEF)[:12]
    assert row["word"] not in og.KERNEL_OPS
    from generators.math_reading import _ID
    assert _ID.fullmatch(row["word"])


# --------------------------------------------------------------- corpus teeth
def _mine_committed():
    return sm.emit_proposals(sm.load_corpus(), dry_run=True)


def test_tooth_a_mod_congruence_emitted_with_shared_modulus():
    """(a) On the committed corpus the mod-congruence subtree is emitted, its
    shared modulus preserved (3 params, one param used twice)."""
    staged = _mine_committed()
    by_def = {common.canonical_json(s["row"]["definition"]): s for s in staged}
    key = common.canonical_json(CONG_DEF)
    assert key in by_def, "mod-congruence subtree not emitted"
    cong = by_def[key]["row"]
    assert cong["params"] == ["v0", "v1", "v2"] and cong["arity"] == 3
    assert cong["provenance"]["witness_count"] == 4          # census's 4
    assert cong["provenance"]["alias_shaped"] is False
    assert len(cong["provenance"]["witness_source_ids"]) == 4


def test_tooth_a_aliases_emitted_but_flagged():
    """(a) Single-kernel-atom aliases (e.g. ``dvd(v0,v1)``) ARE emitted (the
    flood is documented, not hidden) but every one carries alias_shaped=True; no
    non-alias row is spuriously flagged, and the census's headline non-alias
    candidate is NOT flagged."""
    staged = _mine_committed()
    dvd_alias = {"op": "dvd", "args": [{"ref": "v0"}, {"ref": "v1"}]}
    by_def = {common.canonical_json(s["row"]["definition"]): s for s in staged}
    dkey = common.canonical_json(dvd_alias)
    assert dkey in by_def, "expected the dvd alias to be emitted (with a flag)"
    assert by_def[dkey]["row"]["provenance"]["alias_shaped"] is True
    # the mod-congruence candidate is a genuine composite, never flagged.
    assert by_def[common.canonical_json(CONG_DEF)]["row"][
        "provenance"]["alias_shaped"] is False
    # every alias-flagged row is in fact a single kernel op over bare leaves.
    for s in staged:
        if s["row"]["provenance"]["alias_shaped"]:
            assert sm._is_single_kernel_atom_alias(s["row"]["definition"])


def test_tooth_a_provenance_carries_miner_and_witnesses():
    for s in _mine_committed():
        p = s["row"]["provenance"]
        assert p["miner"] == sm.MINER_VERSION
        assert p["witness_count"] >= sm.MIN_WITNESSES
        assert p["witness_source_ids"] == sorted(p["witness_source_ids"])
        assert len(set(p["witness_source_ids"])) == p["witness_count"]


def test_tooth_b_determinism_byte_identical(tmp_path):
    """(b) Two full emissions into fresh dirs produce byte-identical files."""
    corpus = sm.load_corpus()
    d1, d2 = tmp_path / "a", tmp_path / "b"
    os.makedirs(d1 / "operators" / "proposed", exist_ok=True)
    os.makedirs(d2 / "operators" / "proposed", exist_ok=True)
    s1 = sm.emit_proposals(corpus, op_dir=str(d1 / "operators"))
    s2 = sm.emit_proposals(corpus, op_dir=str(d2 / "operators"))
    assert [x["word"] for x in s1] == [x["word"] for x in s2]
    pd1 = os.path.join(str(d1 / "operators"), "proposed")
    pd2 = os.path.join(str(d2 / "operators"), "proposed")
    names = sorted(os.listdir(pd1))
    assert names == sorted(os.listdir(pd2)) and names
    for n in names:
        with open(os.path.join(pd1, n), "rb") as f1, \
                open(os.path.join(pd2, n), "rb") as f2:
            assert f1.read() == f2.read(), f"{n} not byte-identical across runs"


def test_tooth_c_one_witness_not_emitted():
    """(c) A subtree witnessed by a single reading is NOT emitted."""
    only_once = {"op": "<", "args": [{"ref": "a"}, {"op": "^", "args": [
        {"ref": "b"}, {"lit": 7}]}]}          # a distinctive one-off shape
    twice = {"op": "even", "args": [{"ref": "a"}]}
    corpus = [
        {"_sid": "r1", "statements": [
            {"lf": {"kind": "conclusion", "pred": only_once}},
            {"lf": {"kind": "hypothesis", "pred": twice}}]},
        {"_sid": "r2", "statements": [
            {"lf": {"kind": "hypothesis", "pred": twice}}]},
    ]
    staged = sm.emit_proposals(corpus, dry_run=True)
    defs = {common.canonical_json(s["row"]["definition"]) for s in staged}
    # the `<` one-off (and its nested `^` subtree) appear in exactly one reading.
    assert common.canonical_json({"op": "<", "args": [
        {"ref": "v0"}, {"op": "^", "args": [{"ref": "v1"}, {"lit": 7}]}]}) \
        not in defs
    # the 2-witness `even(a)` IS emitted -- the corpus is otherwise live.
    assert common.canonical_json({"op": "even", "args": [{"ref": "v0"}]}) in defs


def test_tooth_d_staging_is_inert_to_the_live_path(monkeypatch):
    """(d) Emitting into a temp registry's proposed/ leaves load_admitted and
    parse_math_reading byte-unchanged: the staging dir is dead to the live path.
    (Empty registry => the expansion hook is identity, so a parse is a stable
    reference point.)"""
    op_dir = tempfile.mkdtemp(prefix="subtree-mine-inert-")
    monkeypatch.setenv("CGB_OPERATORS_DIR", op_dir)
    og.reload()

    # baseline: empty registry, and a reference parse through the live fragment.
    before_admitted = json.dumps(og.load_admitted(), sort_keys=True)
    before_proposed = json.dumps(og.load_proposed(), sort_keys=True)
    sample_doc = {"theorem": "t", "statements": [
        {"id": "x", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "a", "type": "Nat"}},
        {"id": "c", "force": "demand", "quote": "a is even",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "a"}]}}}]}
    before_parse = parse_math_reading(json.dumps(sample_doc), "a is even")

    # emit the real proposals INTO this temp registry's proposed/.
    staged = sm.emit_proposals(sm.load_corpus(), op_dir=op_dir)
    assert staged and os.listdir(os.path.join(op_dir, "proposed"))
    og.reload()

    # load_admitted unchanged (proposed/ is never read by the admitted path);
    # load_proposed now SEES the staged rows (its only reader), but that reader
    # is not on the live parse/expand path.
    assert json.dumps(og.load_admitted(), sort_keys=True) == before_admitted
    after_proposed = og.load_proposed()
    assert json.dumps(after_proposed, sort_keys=True) != before_proposed
    assert len(after_proposed) == len(staged)

    # parse_math_reading is byte-identical: the expansion hook is still identity
    # because admitted.json is still empty despite a populated proposed/.
    after_parse = parse_math_reading(json.dumps(sample_doc), "a is even")
    assert common.canonical_json(after_parse.__dict__ if hasattr(
        after_parse, "__dict__") else after_parse) == common.canonical_json(
        before_parse.__dict__ if hasattr(before_parse, "__dict__")
        else before_parse)


def test_module_does_not_import_or_call_admission_entrypoints():
    """The one-way-data-flow invariant, as source: the emitter never IMPORTS the
    admission module nor CALLS admit_operator / save_admitted (prose mentions in
    the docstring are fine -- it's coupling, not vocabulary, that is banned)."""
    import ast
    path = os.path.join(HERE, "tools", "subtree_mine.py")
    with open(path) as fh:
        src = fh.read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert "operator_growth" not in a.name
        if isinstance(node, ast.ImportFrom):
            assert "operator_growth" not in (node.module or "")
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(
                fn, "id", "")
            assert name not in ("admit_operator", "save_admitted")

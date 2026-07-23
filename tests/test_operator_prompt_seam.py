"""WP-T4-WIRE teeth: the miner -> gate -> registry -> PROMPT loop closes.

All LLM-free and Lean-free.  These teeth exercise the seam that WP-T4-WIRE adds
on TOP of the WP-T4a gate and WP-T4b miner:

  * the admission RUNNER (``tools/admit_proposals.py``) batches the staged
    ``proposed/`` rows through ``admit_operator`` and persists the payers via the
    sole-admitter ``save_admitted`` path -- deterministic and idempotent;
  * the PROMPT seam (``buildloop/math_prompt.render_operator_table`` +
    ``render_math_reading_prompt``'s ``operator_registry`` argument) surfaces the
    PRICED admitted operators as authoring vocabulary (§11.4 mechanism (i)),
    inert-by-default (empty / grandfathered-only registry => byte-identical
    prompt), and the authoring parse path already expands admitted words.

The committed ``specs/mathsources/operators/admitted.json`` is the post-runner
registry: the grandfathered ``multiple_of`` (no ``pricing`` block, alias-refused
under the current gate) plus the four priced rows the runner admitted.
"""
import copy
import json
import os
import shutil

import pytest

import common
from generators import operator_growth as og
from buildloop import math_prompt as mp
from run.formalize import certify_statement
import tools.admit_proposals as ap

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OP_DIR = os.path.join(HERE, "specs", "mathsources", "operators")
CORPUS = os.path.join(HERE, "results", "formalize_bench_state.jsonl")
GOLDEN = os.path.join(HERE, "tests", "golden", "math_prompt_operator_seam.json")

# op_580885f772c7 is the mined mod-congruence word (the WP-T4 headline candidate):
# params (v0, v1, v2), definition =(mod(v0, v1), mod(v2, v1)); the SHARED modulus
# is v1, so "a and b congruent mod m" is op_580885f772c7(a, m, b).
CONGM_WORD = "op_580885f772c7"


@pytest.fixture(autouse=True)
def _reload():
    og.reload()
    yield
    og.reload()


def _golden():
    with open(GOLDEN, encoding="utf-8") as fh:
        return json.load(fh)


def _priced_words(registry):
    return sorted(w for w, e in registry.items()
                  if isinstance(e, dict) and "pricing" in (e.get("cert") or {}))


# =============================================== (d) prompt pins: inert-by-default
def test_prompt_is_byte_identical_on_inert_registry():
    """Default / None / empty operator_registry => the prompt is byte-identical
    to the pre-seam golden captured before any edit (the inert-by-default pin
    that protects the concurrent authoring run)."""
    g = _golden()
    src = g["src"]
    assert mp.render_math_reading_prompt(src, {}) == g["prompt_empty"]
    assert mp.render_math_reading_prompt(src, {}, None) == g["prompt_empty"]
    assert mp.render_math_reading_prompt(src, {}, {}) == g["prompt_empty"]
    # the macro E1 seam is unchanged (a macro table still renders as before)
    assert mp.render_math_reading_prompt(src, g["macro"]) == g["prompt_macro"]


def test_grandfathered_row_is_not_prompt_vocabulary():
    """The grandfathered multiple_of (no pricing block) is NOT advertised, so a
    grandfathered-only registry renders NO operator section and the prompt stays
    byte-identical -- 'unchanged registry => identical bytes'."""
    g = _golden()
    reg = og.load_admitted()
    assert "multiple_of" in reg
    assert "pricing" not in (reg["multiple_of"].get("cert") or {})
    grand = {"multiple_of": reg["multiple_of"]}
    assert mp.render_operator_table(grand) == ""
    assert mp.render_math_reading_prompt(g["src"], {}, grand) == g["prompt_empty"]


def test_prompt_surfaces_priced_operators_second_tooth():
    """With the newly-admitted (committed) registry, the prompt gains an ADMITTED
    OPERATORS section naming every PRICED word with a gloss rendered from its
    definition AST -- and adds prompt bytes (the priced E1 mechanism).  The
    grandfathered multiple_of is filtered out."""
    g = _golden()
    reg = og.load_admitted()
    priced = _priced_words(reg)
    assert CONGM_WORD in priced, priced
    prompt = mp.render_math_reading_prompt(g["src"], {}, reg)
    assert prompt != g["prompt_empty"]                 # priced ops added bytes
    assert len(prompt) > len(g["prompt_empty"])
    assert "ADMITTED OPERATORS" in prompt
    for w in priced:
        assert w in prompt, w
    assert "multiple_of" not in prompt                 # grandfathered filtered
    # the gloss is rendered from the kernel definition AST
    assert "=(mod(v0, v1), mod(v2, v1))" in prompt
    # deterministic + insertion-order-independent
    reversed_reg = dict(reversed(list(reg.items())))
    assert mp.render_operator_table(reg) == mp.render_operator_table(reversed_reg)


# ================================= (a) end-to-end certify via expansion (REAL reg)
def _planted_congruence_reading():
    src = ("For a, b and m, if a and b leave the same remainder on division by m "
           "then a is congruent to b modulo m.")
    reading = {"theorem": "same_rem_gives_cong", "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "om", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "m", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "a, b and m",
         "lf": {"kind": "quantifier", "binder": "forall",
                "objects": ["a", "b", "m"]}},
        {"id": "h", "force": "presupposition",
         "quote": "same remainder on division by m",
         "lf": {"kind": "hypothesis", "pred": {"op": "=", "args": [
             {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
             {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}}},
        # USE the derived word (shared modulus v1 => call as (a, m, b)).
        {"id": "c", "force": "demand", "quote": "congruent to b modulo m",
         "lf": {"kind": "conclusion", "pred": {"op": CONGM_WORD, "args": [
             {"ref": "a"}, {"ref": "m"}, {"ref": "b"}]}}}]}
    return src, reading


def test_planted_reading_certifies_through_the_real_registry():
    """A planted reading whose demanded conclusion USES the newly-admitted word
    certifies end-to-end: the reading layer expands it to kernel mod/=, so the
    engines never see the derived word."""
    reg = og.load_admitted()
    assert CONGM_WORD in reg
    src, reading = _planted_congruence_reading()
    r = certify_statement(src, json.dumps(reading))
    assert r.ok, (r.stage, r.error)
    assert CONGM_WORD not in r.lean_text          # engines saw only kernel ops
    assert "%" in r.lean_text                     # the kernel mod notation


# ============================================ (b) tamper + append-only after batch
def test_committed_registry_digest_chain_intact():
    """Every committed admitted row (grandfathered + priced) verifies its stored
    cert-id / row-digest / battery-digest chain -- the batch left the tamper
    substrate consistent."""
    reg = og.load_admitted()
    assert reg
    for word, entry in reg.items():
        og._verify_entry(word, entry)             # raises on any mismatch


def test_tampered_priced_row_refuses_to_lower(tmp_path, monkeypatch):
    """Editing an admitted priced row's definition AFTER admission makes its
    per-use expansion refuse (cert-id mismatch), so a tampered row can never
    silently reach the engines."""
    opd = str(tmp_path)
    os.makedirs(os.path.join(opd, "proposed"), exist_ok=True)
    shutil.copy(os.path.join(OP_DIR, "admitted.json"),
                os.path.join(opd, "admitted.json"))
    monkeypatch.setenv("CGB_OPERATORS_DIR", opd)
    og.reload()
    path = os.path.join(opd, "admitted.json")
    disk = json.load(open(path))
    # corrupt op_580885f772c7's definition (swap a modulus ref) -> row hash no
    # longer matches the stored cert id.
    disk[CONGM_WORD]["row"]["definition"]["args"][0]["args"][1] = {"ref": "v0"}
    with open(path, "w") as fh:
        json.dump(disk, fh)
    og.reload()
    _src, reading = _planted_congruence_reading()
    doc = json.loads(json.dumps(reading))
    with pytest.raises(og.OperatorExpansionError):
        og.expand_reading_doc(doc, verify=True)


def test_append_only_refuses_meaning_change(tmp_path, monkeypatch):
    """save_admitted refuses to overwrite an already-admitted word with a
    DIFFERENT-definition row -- a meaning-changing overwrite of certified corpus
    bytes is loud, never last-writer-wins."""
    opd = str(tmp_path)
    os.makedirs(os.path.join(opd, "proposed"), exist_ok=True)
    shutil.copy(os.path.join(OP_DIR, "admitted.json"),
                os.path.join(opd, "admitted.json"))
    monkeypatch.setenv("CGB_OPERATORS_DIR", opd)
    og.reload()
    corpus = ap.load_pricing_corpus(CORPUS)
    reg = og.load_admitted()
    # a different definition under the same word (shared modulus moved to v2):
    # not the committed digest.  Whatever the re-admission verdict, a
    # meaning-changing overwrite is refused (SaveRefused).
    tampered = copy.deepcopy(reg[CONGM_WORD]["row"])
    tampered["definition"]["args"][1]["args"][1] = {"ref": "v0"}
    with pytest.raises(og.SaveRefused):
        og.save_admitted({CONGM_WORD: {"row": tampered,
                                       "cert": reg[CONGM_WORD]["cert"]}},
                         pricing_corpus=corpus)


# ================================= (c) the runner: batch verdicts + idempotency
def _seed_op_dir(tmp_path):
    opd = os.path.join(str(tmp_path), "ops")
    os.makedirs(os.path.join(opd, "proposed"))
    # seed with the committed grandfathered admitted.json + every proposed row.
    shutil.copy(os.path.join(OP_DIR, "admitted.json"),
                os.path.join(opd, "admitted.json"))
    src_proposed = os.path.join(OP_DIR, "proposed")
    for name in os.listdir(src_proposed):
        if name.endswith(".json"):
            shutil.copy(os.path.join(src_proposed, name),
                        os.path.join(opd, "proposed", name))
    return opd


def test_runner_admits_payers_preserves_grandfathered_and_is_idempotent(
        tmp_path, monkeypatch):
    monkeypatch.delenv("CGB_OPERATORS_DIR", raising=False)
    opd = _seed_op_dir(tmp_path)
    resdir = os.path.join(str(tmp_path), "res")
    og.reload()

    report = ap.run(opd, CORPUS, resdir, execute=True)

    # exactly the five priced payers admit (op_3c0de4c8920b -- nonnegativity,
    # 0 <= v0 -- crossed the two-witness bar with the C2 census-sourced
    # corpus growth and prices positive on the grown corpus)
    admitted = sorted(v["word"] for v in report["verdicts"] if v["admitted"])
    assert admitted == ["op_3c0de4c8920b", "op_580885f772c7",
                        "op_600a6c7b92c4", "op_c7e5b035d6b3",
                        "op_f39960716d99"], admitted
    assert report["n_proposed"] == 27
    assert report["n_admitted"] == 5

    # the congm-shape row is the Δ<0 headline (delta ~ -116)
    congm = next(v for v in report["verdicts"] if v["word"] == CONGM_WORD)
    assert congm["admitted"] and congm["pricing"]["delta"] < 0

    # every refusal family is represented and honestly staged
    refusal_stages = {v["stage"] for v in report["verdicts"] if not v["admitted"]}
    assert {"trivial-alias", "pricing", "well-formedness", "nonvacuity"} \
        <= refusal_stages

    # the grandfathered multiple_of is NOT evicted (append-only only ADDS)
    reg = json.load(open(os.path.join(opd, "admitted.json")))
    assert set(reg) == {"multiple_of"} | set(admitted)
    assert "pricing" not in reg["multiple_of"]["cert"]

    # idempotent: a second run is a byte-identical no-op (registry + report)
    before = open(os.path.join(opd, "admitted.json"), "rb").read()
    report2 = ap.run(opd, CORPUS, resdir, execute=True)
    after = open(os.path.join(opd, "admitted.json"), "rb").read()
    assert before == after
    assert common.canonical_json(report) == common.canonical_json(report2)


def test_runner_dry_run_does_not_mutate(tmp_path, monkeypatch):
    monkeypatch.delenv("CGB_OPERATORS_DIR", raising=False)
    opd = _seed_op_dir(tmp_path)
    resdir = os.path.join(str(tmp_path), "res")
    og.reload()
    before = open(os.path.join(opd, "admitted.json"), "rb").read()
    report = ap.run(opd, CORPUS, resdir, execute=False)
    after = open(os.path.join(opd, "admitted.json"), "rb").read()
    assert before == after                        # dry run mutates nothing
    assert report["n_admitted"] == 5              # but still measures the payers
    assert all(v["saved"] is False for v in report["verdicts"])


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))

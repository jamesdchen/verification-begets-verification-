"""Combined-Loop W5.1 -- universal-translation (translator promotion) teeth.

The second pinned Combined-Loop contract type.  A translator promotion resolves
as an honest `complete-to-size(N)` bounded result (NOT flipped to universal), and
an unsound sample refuses it outright.  LLM-free, Dafny-free.
"""
import json
import tempfile

import kernel
from kernel.certs import Certificate
from library import Registry
from buildloop import promote as promote_mod
from demo_macros import NO_OVERSELL, BAD_OVERSELL, CORPUS, _reading, \
    _compile_and_emit


def _sample(c, macro=None):
    inlined, macro_form = _reading(macro=macro, **c) if macro else _reading(**c)
    name = (macro or NO_OVERSELL)["name"]
    files = _compile_and_emit(macro_form, c["request"],
                              {name: macro or NO_OVERSELL})
    return {"high_spec_text": json.dumps(macro_form),
            "reference_lowering": json.dumps(inlined),
            "expansion_context": {"macro_table": {name: macro or NO_OVERSELL}},
            "request": c["request"], "files": files}


def _translator(reg):
    return reg.register(
        name="macro-reading-lowering", tier="emit-check",
        spec_language="macro-reading", output_language="reading",
        spec_grammar={"atoms": ["macro"]},
        emit_entrypoint={"kind": "macro-expand"}, contract={}, provenance={},
        kind="translator")


def test_universal_translation_in_allowlist():
    assert "universal-translation" in kernel.IMPLEMENTED_CONTRACT_TYPES


def test_honest_translator_is_bounded_not_universal(tmp_path):
    reg = Registry(db_path=str(tmp_path / "r.sqlite"))
    gh = _translator(reg)
    res = promote_mod.promote(
        reg, gh, translator_samples=[_sample(c) for c in CORPUS])
    assert res["status"] == "refused-bounded"
    assert res["tier"] == "complete-to-size(N)"
    assert reg.get(gh)["tier"] == "emit-check"        # NOT flipped


def test_unsound_translator_sample_refuses_promotion(tmp_path):
    reg = Registry(db_path=str(tmp_path / "r.sqlite"))
    gh = _translator(reg)
    samples = [_sample(CORPUS[0]), _sample(CORPUS[1]),
               _sample(CORPUS[2], BAD_OVERSELL)]       # one lossy
    res = promote_mod.promote(reg, gh, translator_samples=samples)
    assert res["status"] == "rejected"
    assert reg.get(gh)["tier"] == "emit-check"


def test_universal_translation_channels_are_two_and_independent(tmp_path):
    reg = Registry(db_path=str(tmp_path / "r.sqlite"))
    gh = _translator(reg)
    v = kernel.check(
        {"kind": "translator", "files": {}},
        {"type": "universal-translation", "high_language": "macro-reading",
         "translator_hash": gh,
         "samples": [_sample(c) for c in CORPUS]})
    assert isinstance(v, Certificate)
    backs = {c["backend"] for c in v.channels}
    assert backs == {"bounded-translation-compile-identity",
                     "bounded-translation-scenario-fuzz"}
    assert v.tier == "complete-to-size(N)"

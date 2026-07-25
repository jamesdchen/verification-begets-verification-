"""The ksy purity guarantee, measured on the path that actually runs.

WHY THIS FILE EXISTS.  `buildloop/validate.py` carried `validate_ksy_purity`,
a pre-check refusing four constructs in ksy text: `process:`,
`ks-opaque-types`, `imports:` and `!!python`.  Nothing called it -- not the
LLM path, not the kernel, not a test.  A guard that is never invoked provides
exactly no guarantee, and the four names sitting in the source read as though
one existed.

It was also strictly WEAKER than the thing that does run.  It matched raw
SUBSTRINGS, so `process:` inside a doc field would trip it and `process :`
would slip past; `generators/ksy_model.parse_ksy` instead refuses
STRUCTURALLY -- forbidden keys checked against the parsed `meta` mapping,
after `yaml.safe_load`, whose constructor rejects `!!python` tags outright.

So the guard was deleted and the guarantee moved here, where it is a
measurement rather than an assertion: each construct is fed to the REAL parse
path and its refusal is checked.  If `parse_ksy` ever stops refusing one,
this reddens -- which is what the deleted function only appeared to promise.

`kernel/__init__.py` calls `parse_ksy(low_text)` on model output, so this is
the path that carries the risk.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.ksy_model import parse_ksy


# A spec that PARSES.  Every forbidden case below is this exact text plus the
# one construct under test, so a refusal is attributable to that construct and
# never to incidental malformedness -- the trap the first draft of this file
# fell into, where `seq: []` was itself rejected and made all four cases pass
# for the wrong reason.  The control below is what caught it.
BASE = "meta:\n  id: x\n  endian: be\nseq:\n  - id: a\n    type: u1\n"

_INJECT = "  endian: be\n"
FORBIDDEN = {
    "process": BASE.replace(_INJECT, _INJECT + "  process: zlib\n"),
    "imports": BASE.replace(_INJECT, _INJECT + "  imports: [other]\n"),
    "ks-opaque-types": BASE.replace(_INJECT, _INJECT + "  ks-opaque-types: true\n"),
    "python-tag": BASE.replace(
        _INJECT, _INJECT + "  fake: !!python/object/apply:os.system ['echo pwned']\n"),
}


def test_the_control_parses():
    """Without a control, every case below would pass on a parser that refused
    EVERYTHING -- including valid specs.  This is not hypothetical: it is the
    bug this file shipped with for one run."""
    assert parse_ksy(BASE) is not None


@pytest.mark.parametrize("name,text", sorted(FORBIDDEN.items()))
def test_the_real_parse_path_refuses(name, text):
    assert parse_ksy(BASE) is not None, "control broken; a refusal proves nothing"
    assert text != BASE, f"{name} did not actually modify the base spec"
    with pytest.raises(Exception) as exc:
        parse_ksy(text)
    # A refusal, not an incidental crash: the parser's own violation type.
    assert type(exc.value).__name__ in ("UnsupportedSpec", "SpecViolation"), (
        f"{name} was rejected by {type(exc.value).__name__}, which is not the "
        f"parser refusing it deliberately")


def test_the_deleted_guard_has_not_come_back():
    """Two enforcement stories for one guarantee is how they drift apart."""
    import buildloop.validate as v
    assert not hasattr(v, "validate_ksy_purity"), (
        "validate_ksy_purity is back; either it is wired into the ksy path "
        "and owns the guarantee, or parse_ksy owns it and this file is the "
        "measurement -- not both")

"""Level B teeth: the generated pin file (tools/fg_emit_pins.lean) is
byte-fresh, compiler-true, gate-clean, and (Lean lane) kernel-discharged
when appended to the module.

The claim structure the pins carry:

    emitProp bytes == pin bytes    (kernel rfl, Lean lane)
    pin bytes == compiler bytes    (these teeth, every container)

so a green lane plus a green suite means the Lean reference emitter and
the shipped Python compiler agree byte-for-byte on every pinned corpus
reading -- with the pairing example routing the SAME datum through
toReading into compile_preserves (level A), tying the pinned surface to
the statement the reflection checkers speak about.
"""
import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop.validate_lean import validate_lean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "tools", "gen_fg_emit_pins.py")
PINS = os.path.join(ROOT, "tools", "fg_emit_pins.lean")
MODULE = os.path.join(ROOT, "tools", "FgReflect.lean")


def _gen():
    spec = importlib.util.spec_from_file_location("gen_fg_emit_pins", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pins_text() -> str:
    with open(PINS) as fh:
        return fh.read()


def test_regeneration_is_byte_identical():
    # The committed file IS the generator's output -- any hand edit, corpus
    # drift, or generator change without regeneration fails here.
    assert _gen().build_text() == _pins_text()


def test_every_corpus_reading_is_pinned_or_named_skip():
    gen = _gen()
    pins, skips = gen.collect()
    import glob
    total = len(glob.glob(os.path.join(ROOT, "specs", "mathsources",
                                       "readings", "*.json")))
    assert len(pins) + len(skips) == total
    assert len(pins) >= 11                      # the full current corpus pins
    for _stem, reason in skips:
        assert reason.startswith(("slice-miss:", "nary-flattening",
                                  "pow-surface-form")), reason


def test_pins_restate_live_compiler_bytes():
    # Independent restatement (not via build_text): each pinned prop, wrapped
    # back into the theorem form, must equal a LIVE compile_math_reading run.
    from generators.math_compile import compile_math_reading
    from generators.math_reading import parse_math_reading
    gen = _gen()
    pins, _ = gen.collect()
    text = _pins_text()
    for rec in pins:
        path = os.path.join(ROOT, "specs", "mathsources", "readings",
                            rec["stem"] + ".json")
        d = json.load(open(path))
        reading = parse_math_reading(json.dumps(d["reading"]), d["source"])
        lt = compile_math_reading(reading)["lean_text"]
        assert lt == (f"theorem {rec['theorem']} : " + rec["prop"]
                      + " := " + "sorry"), rec["stem"]
        # and the committed file carries that prop VERBATIM as a pin string.
        assert f'"{rec["prop"]}" := rfl' in text, rec["stem"]


def test_pins_file_passes_gate_alone_and_appended():
    ok, reason = validate_lean(_pins_text())
    assert ok, reason
    with open(MODULE) as fh:
        both = fh.read() + "\n" + _pins_text()
    ok, reason = validate_lean(both)
    assert ok, reason


def test_pins_carry_no_deferred_proof():
    text = _pins_text()
    assert "sorry" not in text
    assert "GENERATED" in text                  # provenance banner stays


def test_emitter_interface_names_present():
    # emit* / toReading are defs (not theorems), so the FgReflect interface
    # tooth doesn't cover them; renaming any is an interface change.
    with open(MODULE) as fh:
        src = fh.read()
    for name in ("structure Seg", "structure EReading", "def emitInt",
                 "def emitTm", "def emitPd", "def emitProp", "def toReading"):
        assert name in src, name


@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent (Lean-lane test)")
def test_pins_elaborate_appended_to_module():
    from kernel.backends import LeanBackend
    with open(MODULE) as fh:
        text = fh.read() + "\n" + _pins_text()
    res = LeanBackend().elaborate(text, expect_sorry=False)
    assert not res.get("unavailable"), res
    assert res.get("ok"), res

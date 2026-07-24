"""Combined-Loop W1.3b -- tests for the `fixed-deriver` anchor of
`translation-cert` on the abnf->ksy stage (DAFNY-FREE, LLM-FREE).

Teeth:
  * a FAITHFUL abnf->ksy translation certifies -- both channels pass;
  * a PLANTED LOSSY translation (a dropped field) is refuted by BOTH channels
    (compile-identity differs AND the codec differential diverges);
  * the channel-2 oracle (ref_fields) and the channel-1 obligation both enter
    cache identity, so a corrupt-ref route cannot collide with the clean route.

The two behavioural teeth need ksc (Kaitai) + the sandbox; the cache-identity
tooth is pure (no ksc).
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import kernel
from kernel.certs import Certificate
from demos import demo_translation_abnf as demo


def _channels(v, ok):
    return v.channels if ok else v.to_dict()["channels"]


def test_faithful_translation_certifies():
    high, low_ksy, low_files = demo._faithful()
    v, ok, ch = demo._check(high, low_ksy, low_files)
    assert ok and isinstance(v, Certificate), \
        f"faithful translation not certified: {ch}"
    assert len(ch) == 2 and all(c["result"] == "pass" for c in ch), ch
    backends = {c["backend"] for c in ch}
    assert backends == {"translation-abnf-compile-identity",
                        "translation-abnf-codec-differential"}, backends
    roles = {c["backend"]: c["role"] for c in ch}
    assert roles["translation-abnf-compile-identity"] == "cross-impl-differential"
    assert roles["translation-abnf-codec-differential"] == "behavioral-witness"
    assert v.tier == "emit-check"


def test_lossy_translation_refuted_by_both_channels():
    high, low_ksy, low_files = demo._lossy()
    v, ok, ch = demo._check(high, low_ksy, low_files)
    assert not ok and not isinstance(v, Certificate), \
        "lossy translation was wrongly certified"
    ch1 = [c for c in ch if c["backend"] == "translation-abnf-compile-identity"]
    ch2 = [c for c in ch if c["backend"] == "translation-abnf-codec-differential"]
    assert ch1 and ch1[0]["result"] != "pass", ("channel-1 did not refute", ch)
    assert ch2 and ch2[0]["result"] != "pass", ("channel-2 did not refute", ch)


def test_ref_fields_and_obligations_enter_cache_identity():
    """A corrupt-ref route (different high spec => different derived ref_fields /
    obligations) must NOT collide with the clean route; and a changed low spec is
    a clean miss.  Pure (no ksc)."""
    base_high = demo.SPEC_PATH.read_text()
    other_high = "record = \"ZZ\" 3DIGIT CRLF\n"
    art = {"kind": "translation", "files": {}}
    c_base = demo._contract(base_high, "meta:\n  id: x\n", {})
    c_other_high = demo._contract(other_high, "meta:\n  id: x\n", {})
    c_other_low = demo._contract(base_high, "meta:\n  id: y\n", {})
    k_base = kernel.cache_key(art, c_base)
    k_other_high = kernel.cache_key(art, c_other_high)
    k_other_low = kernel.cache_key(art, c_other_low)
    assert len({k_base, k_other_high, k_other_low}) == 3, \
        "high/low changes must each be a clean cache miss"
    # the derived oracle is explicitly folded into the cdesc
    _subj, cdesc = kernel._subject_and_cdesc(art, c_base)
    assert cdesc["anchor"] == "fixed-deriver"
    assert "ref_fields_hash" in cdesc and "obligations_hash" in cdesc
    _subj2, cdesc2 = kernel._subject_and_cdesc(art, c_other_high)
    assert cdesc["ref_fields_hash"] != cdesc2["ref_fields_hash"]
    assert cdesc["obligations_hash"] != cdesc2["obligations_hash"]


if __name__ == "__main__":
    test_faithful_translation_certifies()
    print("PASS faithful")
    test_lossy_translation_refuted_by_both_channels()
    print("PASS lossy")
    test_ref_fields_and_obligations_enter_cache_identity()
    print("PASS cache-identity")

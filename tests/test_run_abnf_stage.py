"""Combined-Loop W1.3b -- unit test for the per-stage `translation-cert`
wiring at the abnf->ksy stage in `run/__init__.py` (the `fixed-deriver`
anchor).  DAFNY-FREE and LLM-FREE.

This exercises ONLY the new wiring (`run._abnf_translation_cert` and
`run._record_translation_cert`) in ISOLATION -- it does NOT drive a full
`run.run_task`, because the abnf chain's terminal codec emit-check needs Dafny
(unavailable in this sandbox) for the final codec proof.  The fixed-deriver
anchor itself is Dafny-free (channel 1 = compile-identity, channel 2 =
Hypothesis+ksc codec-differential), so the stage cert CAN be exercised here.

Inputs for a FAITHFUL abnf->ksy stage are built via the fixed-deriver route
(`generators.abnf_chain.tokenize`/`tokens_to_ksy`) and the ksc emitter
(`emit_ksc_python_rw`) -- the same route the deriver's channels are derived
from, so a faithful stage certifies.  Needs ksc (Kaitai); no Dafny.

Teeth:
  * a faithful abnf->ksy stage issues the translation-cert and BOTH channels
    (compile-identity + codec-differential) come back passing, and the verdict
    is recorded (stage record annotated, certificate stored);
  * the wiring is GUARDED on the emit kind: a non-abnf stage yields no cert
    (so a run without an abnf stage is untouched).
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import common
import run
from kernel.certs import Certificate
from generators import abnf_chain
from generators.emitters import emit_ksc_python_rw


SPEC_PATH = (pathlib.Path(__file__).resolve().parent.parent
             / "specs/backlog/k_abnf_001.abnf")


class _FakeRegistry:
    """Minimal registry double: only the cache/event/cert sinks the per-stage
    wiring threads (matching library.Registry's signatures)."""

    def __init__(self):
        self.events = []
        self.stored = []
        self._cache = {}

    def log_event(self, kind, payload):
        self.events.append((kind, payload))

    def cache_get(self, key):
        return self._cache.get(key)

    def cache_put(self, key, value):
        self._cache[key] = value

    def store_certificate(self, cert, generator_hash=None):
        self.stored.append((cert, generator_hash))


def _faithful_inputs():
    """The faithful abnf->ksy stage inputs via the fixed-deriver route."""
    high = SPEC_PATH.read_text()
    toks = abnf_chain.tokenize(high)
    low_ksy = abnf_chain.tokens_to_ksy(toks, common.sha256_bytes(high.encode()))
    return high, low_ksy


def _abnf_entry():
    return {"emit_entrypoint": {"kind": "abnf-to-ksy"},
            "generator_hash": "test-abnf-gh", "name": "abnf->ksy",
            "tier": "emit-check"}


def test_abnf_stage_issues_translation_cert_both_channels():
    """A faithful abnf->ksy stage: the wiring issues the fixed-deriver
    translation-cert and both derived channels pass -- Dafny-free."""
    high, low_ksy = _faithful_inputs()
    reg = _FakeRegistry()
    verdict = run._abnf_translation_cert(_abnf_entry(), high, low_ksy, reg)
    assert verdict is not None, "wiring did not issue a translation-cert"
    assert isinstance(verdict, Certificate), \
        f"faithful stage not certified: {verdict.to_dict()['channels']}"
    ch = verdict.channels
    assert len(ch) == 2 and all(c["result"] == "pass" for c in ch), ch
    backends = {c["backend"] for c in ch}
    assert backends == {"translation-abnf-compile-identity",
                        "translation-abnf-codec-differential"}, backends
    assert verdict.tier == "emit-check"


def test_abnf_stage_records_certificate():
    """The passing verdict is recorded analogous to the emit-check handling:
    the stage record is annotated and the certificate is stored."""
    high, low_ksy = _faithful_inputs()
    reg = _FakeRegistry()
    entry = _abnf_entry()
    verdict = run._abnf_translation_cert(entry, high, low_ksy, reg)
    rec = {"generator": entry["generator_hash"], "name": entry["name"]}
    cert = run._record_translation_cert(verdict, entry, rec, reg)
    assert cert is not None and cert["cert_id"], cert
    assert rec["translation_cert"]["ok"] is True
    assert set(b for b, _ in rec["translation_cert"]["channels"]) == {
        "translation-abnf-compile-identity",
        "translation-abnf-codec-differential"}
    assert reg.stored and reg.stored[0][1] == "test-abnf-gh"
    # non-fatal path: a pass logs no rejection event
    assert not any(k == "translation-cert-rejection" for k, _ in reg.events)


def test_non_abnf_stage_is_guarded():
    """A stage that is not an abnf->ksy emit yields no cert (a run without an
    abnf stage is untouched by the wiring)."""
    reg = _FakeRegistry()
    ksc_entry = {"emit_entrypoint": {"kind": "ksc-python-rw"},
                 "generator_hash": "gh"}
    assert run._abnf_translation_cert(ksc_entry, "x", "meta:\n  id: y\n",
                                      reg) is None
    # a missing emit_entrypoint is likewise a clean skip, never a crash
    assert run._abnf_translation_cert({}, "x", "y", reg) is None
    assert reg.stored == [] and reg.events == []


if __name__ == "__main__":
    test_abnf_stage_issues_translation_cert_both_channels()
    print("PASS issue")
    test_abnf_stage_records_certificate()
    print("PASS record")
    test_non_abnf_stage_is_guarded()
    print("PASS guard")

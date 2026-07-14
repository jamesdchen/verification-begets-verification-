"""W5.1 tier-routing unit tooth -- LLM-free, Dafny-free.

Exercises the promotion DECISION (`_should_set_universal`) directly and the
`promote()` control flow with a fake registry + fake kernel, so NO real
ksc/Dafny/Hypothesis promotion runs here.  The load-bearing invariant: a
non-universal certificate NEVER flips the generator's tier (plan tooth (c)),
while the certificate is still kept as evidence.
"""
from __future__ import annotations

from kernel.certs import Certificate
from buildloop import promote as promote_mod


def _cert(tier: str) -> Certificate:
    return Certificate.make(
        "promotion", "subject-hash", "contract-hash",
        [{"backend": "dafny", "result": "pass"},
         {"backend": "hypothesis", "result": "pass"}],
        tier=tier)


# --------------------------------------------------------------- pure decision
def test_should_set_universal_true_only_for_universal():
    assert promote_mod._should_set_universal(_cert("universal")) is True


def test_should_set_universal_false_for_bounded_and_others():
    for tier in ("complete-to-size(4)", "complete-to-size(N)", "emit-check",
                 "bounded-K", "conformance-relative(3)", "monitored",
                 "tier-unclassified", ""):
        assert promote_mod._should_set_universal(_cert(tier)) is False, tier


# ---------------------------------------------------- promote() control flow
class _FakeRegistry:
    """Records set_tier / store_certificate calls; returns a canned entry and
    a canned verdict via a monkeypatched kernel.check."""

    def __init__(self, entry):
        self._entry = entry
        self.stored = []      # (cert, ghash)
        self.tier_calls = []  # (ghash, tier)
        self.events = []      # (kind, payload)

    def get(self, ghash):
        return dict(self._entry)

    def log_event(self, kind, payload):
        self.events.append((kind, payload))

    def counter_add(self, key, delta):
        pass

    def cache_get(self, key):
        return None

    def cache_put(self, key, value):
        pass

    def store_certificate(self, cert, generator_hash=None):
        self.stored.append((cert, generator_hash))

    def set_tier(self, ghash, tier):
        self.tier_calls.append((ghash, tier))


def _emitter_entry():
    return {"tier": "emit-check", "kind": "emitter", "name": "g",
            "spec_grammar": {"atoms": ["endian:le", "uint:8", "uint:16"]},
            "emit_entrypoint": {"module": "x"},
            "emission_checked": 5, "emission_failures": 0}


def _stub_sampling_and_kernel(monkeypatch, verdict):
    """Replace the heavy emitter-sampling + kernel.check so no ksc/Dafny runs."""
    monkeypatch.setattr(promote_mod, "emit_ksc_python_rw",
                        lambda text: {"codec.py": b""})

    class _FakeKsy:
        @staticmethod
        def parse_ksy(text):
            return object()

    monkeypatch.setattr(promote_mod, "ksy_model", _FakeKsy)

    class _FakeKernel:
        @staticmethod
        def check(*a, **k):
            return verdict

    monkeypatch.setattr(promote_mod, "kernel", _FakeKernel)


def test_promote_non_universal_verdict_never_sets_tier(monkeypatch):
    cert = _cert("complete-to-size(4)")
    reg = _FakeRegistry(_emitter_entry())
    _stub_sampling_and_kernel(monkeypatch, cert)

    res = promote_mod.promote(reg, "ghash-1")

    assert res["status"] == "refused-bounded"
    assert res["tier"] == "complete-to-size(4)"
    assert reg.tier_calls == []          # the invariant: tier NEVER flipped
    assert len(reg.stored) == 1          # cert kept as evidence
    assert reg.stored[0][0] is cert


def test_promote_universal_verdict_flips_tier(monkeypatch):
    cert = _cert("universal")
    reg = _FakeRegistry(_emitter_entry())
    _stub_sampling_and_kernel(monkeypatch, cert)

    res = promote_mod.promote(reg, "ghash-2")

    assert res["status"] == "promoted"
    assert reg.tier_calls == [("ghash-2", "universal")]
    assert len(reg.stored) == 1


def test_promote_translator_without_samples_is_a_noop(monkeypatch):
    """A translator promotion with no sampled corpus does not touch the tier and
    does not run the kernel (W5.1: the universal-translation contract needs a
    bounded sample set)."""
    entry = _emitter_entry()
    entry["kind"] = "translator"
    reg = _FakeRegistry(entry)
    monkeypatch.setattr(promote_mod.kernel, "check",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("kernel.check must not run without samples")))
    res = promote_mod.promote(reg, "ghash-3")
    assert res["status"] == "no-samples"
    assert reg.tier_calls == []
    assert reg.stored == []


def test_promote_translator_bounded_cert_does_not_flip_tier(monkeypatch):
    """A complete-to-size(N) universal-translation verdict is stored as evidence
    but NEVER flips the tier (the honest bounded refusal)."""
    entry = _emitter_entry()
    entry.update({"kind": "translator", "spec_language": "macro-reading",
                  "generator_hash": "ghash-3"})
    reg = _FakeRegistry(entry)
    monkeypatch.setattr(promote_mod.kernel, "check",
                        lambda *a, **k: _cert("complete-to-size(N)"))
    res = promote_mod.promote(reg, "ghash-3", translator_samples=[{"x": 1}])
    assert res["status"] == "refused-bounded"
    assert res["tier"] == "complete-to-size(N)"
    assert reg.tier_calls == []              # tier NOT flipped
    assert reg.stored                        # cert kept as evidence


def test_promote_already_universal_short_circuits():
    entry = _emitter_entry()
    entry["tier"] = "universal"
    reg = _FakeRegistry(entry)
    res = promote_mod.promote(reg, "ghash-4")
    assert res["status"] == "already-universal"
    assert reg.tier_calls == []

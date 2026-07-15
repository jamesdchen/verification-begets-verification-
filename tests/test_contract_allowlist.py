"""Combined-Loop W1.4 -- the contract-type allowlist (house rule 6).

A new kernel contract type must be pinned.  The implemented dispatch types must
be a SUBSET of the frozen vocabulary = the 16 pre-existing types + the two
Combined-Loop additions (translation-cert, universal-translation) + the two
FORMALIZATION F0 additions (statement-cert, proof-cert -- the non-pooled,
direct-path Lean contracts, WP-G).  A deliberate frozen-vocabulary amendment,
named in the commit (⚠A8).  translation-cert must be present; universal-
translation is allowed-but-absent until W5; this test passes at every wave.
"""
import re

import kernel

_PREEXISTING = frozenset({
    "codec-roundtrip", "codec-differential", "vpl-differential",
    "universal-fixed-uint", "tool-differential", "tool-lift",
    "constraint-cert", "protocol-cert", "service-conformance",
    "intent-scenarios", "monitor-cert", "cage-conformance",
    "tier-classification", "macro-expansion-cert", "smt-obligation",
    "reading-consistency"})
_COMBINED_LOOP = frozenset({"translation-cert", "universal-translation"})
# FORMALIZATION F0 (WP-G): the two Lean proof-assistant contracts.
_FORMALIZATION = frozenset({"statement-cert", "proof-cert"})
_FROZEN = _PREEXISTING | _COMBINED_LOOP | _FORMALIZATION


def test_implemented_types_are_pinned():
    impl = kernel.IMPLEMENTED_CONTRACT_TYPES
    assert impl <= _FROZEN, \
        f"unpinned contract types: {sorted(impl - _FROZEN)}"
    assert "translation-cert" in impl
    # the FORMALIZATION F0 additions are present (WP-G landed them).
    assert _FORMALIZATION <= impl, \
        f"missing FORMALIZATION types: {sorted(_FORMALIZATION - impl)}"
    assert len(_PREEXISTING) == 16


def test_declared_constant_matches_dispatch_source():
    """The declared constant must not drift from what _dispatch actually
    branches on -- every `ctype == "..."` / `ctype in (...)` literal in the
    kernel source is in IMPLEMENTED_CONTRACT_TYPES."""
    src = (kernel.__file__)
    text = open(src).read()
    # Match ANY quoted dispatch literal (not just lowercase-hyphen), so a rogue
    # `ctype == "rogue_type"` / uppercase branch cannot evade the pin.
    dispatched = set(re.findall(r'ctype == "([^"]+)"', text))
    missing = dispatched - kernel.IMPLEMENTED_CONTRACT_TYPES
    assert not missing, f"dispatched but not declared: {sorted(missing)}"

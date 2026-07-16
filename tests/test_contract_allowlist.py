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
# Wave-1 FI-W1-1 (COMPRESSION.md §11.9): the norm-cert contract type.  Landed as
# SCHEMA ONLY (kernel.certs), so it is allowed-but-ABSENT from dispatch until its
# producer lands -- exactly universal-translation's status before W5.  The frozen
# vocabulary must name it in the same commit as the schema (⚠A8, house rule 6).
_WAVE1 = frozenset({"norm-cert"})
_FROZEN = _PREEXISTING | _COMBINED_LOOP | _FORMALIZATION | _WAVE1


def test_implemented_types_are_pinned():
    impl = kernel.IMPLEMENTED_CONTRACT_TYPES
    assert impl <= _FROZEN, \
        f"unpinned contract types: {sorted(impl - _FROZEN)}"
    assert "translation-cert" in impl
    # the FORMALIZATION F0 additions are present (WP-G landed them).
    assert _FORMALIZATION <= impl, \
        f"missing FORMALIZATION types: {sorted(_FORMALIZATION - impl)}"
    assert len(_PREEXISTING) == 16
    # norm-cert is pinned in the frozen vocabulary but allowed-but-ABSENT from
    # dispatch (schema-only, no producer yet -- §11.9 order).
    assert _WAVE1 <= _FROZEN
    assert "norm-cert" not in impl, \
        "norm-cert must stay schema-only until its producer lands (§11.9)"


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

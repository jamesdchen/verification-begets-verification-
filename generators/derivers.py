"""Per-language trusted lowerings and obligation/harness derivers (W1.2).

The generic `translation-cert` kernel contract certifies a per-emission
translation `Spec_high -> Spec_low` against a NAMED INDEPENDENT ANCHOR (house
rule 11 -- no translation-cert without one).  This module is the fixed,
LLM-free registry the kernel dispatches through, so a new rung becomes one
entry here plus one TRUST.md line -- never a kernel edit.

Two anchor mechanisms are registered here:

  * reference-lowering (`LOWERINGS`): a trusted, fixed lowering `L` of the high
    language (the macro-cert pattern, fact 3).  The certificate holds that the
    translator's output, lowered by `L`, is byte-identical to a trusted
    REFERENCE input lowered by `L`, and that the emitted artifact reproduces the
    scenarios the reference's demands solver-entail.  Channel 2's harness is
    derived from the HIGH spec via `L`, never via the translator under test.

  * fixed-deriver (`DERIVERS`): a per-language LLM-free
    `(derive_obligations, derive_harness)` pair.  `derive_obligations(high)`
    returns a reference the artifact's low spec must match; `derive_harness(high)`
    returns a differential harness built from the HIGH spec.

`incumbent-differential` is the conversion oracle mode (W4.2) and is NOT a
lowering here -- its anchor is the caged incumbent, carried as `oracle_ref` in
the contract.
"""
from __future__ import annotations

import pathlib

import common


# --------------------------------------------------------- reference lowerings
def _lower_reading(text: str, context: dict):
    """Trusted lowering of a Reading (possibly carrying macro invocations) to a
    compiled meta-spec.  Returns {'spec', 'reading'}; `context` may carry
    `request` (the grounding text) and `macro_table` (the expansion context)."""
    from generators import reading as _rd, reading_compile as _rc
    request = (context or {}).get("request", "")
    macro_table = (context or {}).get("macro_table")
    r = _rd.parse_reading(text, request, macro_table=macro_table)
    spec, _prov = _rc.compile_reading(r)
    return {"spec": spec, "reading": r}


def _reading_scenarios(lowered: dict):
    """Behavioural harness for the reading domain: the scenarios the reference
    reading's demands solver-ENTAIL, derived from the reference (HIGH) via the
    trusted lowering -- never from the translator under test (house rule 11)."""
    from generators import reading_compile as _rc, service_model as _svm
    m = _svm.parse_service_spec(lowered["spec"])
    return _rc.entailed_scenarios(m, lowered["reading"])


# high_language -> {"lower": (text, context) -> {spec, ...},
#                   "scenarios": lowered -> [scenario, ...]}
LOWERINGS = {
    "reading": {"lower": _lower_reading, "scenarios": _reading_scenarios},
    "macro-reading": {"lower": _lower_reading, "scenarios": _reading_scenarios},
}


# ------------------------------------------------------------- fixed derivers
def _abnf_obligations(high_spec_text: str):
    """Reference token list for an ABNF spec (the independent cross-check
    oracle the artifact's ksy mapping must reproduce)."""
    from generators import abnf_chain
    return abnf_chain.tokenize(high_spec_text)


def _abnf_harness(high_spec_text: str):
    """Independent reference field route for an ABNF spec (feeds a refcodec
    differential harness on the emitted low artifact)."""
    from generators import abnf_chain
    return {"ref_fields": abnf_chain.abnf_reference_fields(high_spec_text)}


# high_language -> (derive_obligations, derive_harness)
DERIVERS = {
    "abnf": (_abnf_obligations, _abnf_harness),
}


# ------------------------------------------------------- lowering-module hash
_LOWERING_MODULES = (
    "generators/derivers.py", "generators/reading.py",
    "generators/reading_compile.py", "generators/abnf_chain.py",
)


def lowering_pipeline_hash() -> str:
    """sha256 over the fixed lowering module sources -- the kernel-computable
    `translator_hash`/`lowering_pipeline_hash` for a reference-lowering or
    fixed-deriver anchor (a translator that is fixed code, not a registry
    entry).  Naming these in one place stops two builders populating the pin
    differently and silently changing every cache key."""
    h = []
    for rel in _LOWERING_MODULES:
        p = common.REPO_ROOT / rel
        try:
            h.append((rel, common.sha256_bytes(p.read_bytes())))
        except OSError:
            h.append((rel, ""))
    return common.sha256_json(h)

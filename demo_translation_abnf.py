#!/usr/bin/env python3
"""Combined-Loop W1.3b -- the `fixed-deriver` anchor of the generic
`translation-cert` contract, exercised on the abnf->ksy translation stage.

DAFNY-FREE and LLM-FREE.  The named independent anchor (house rule 11) is the
fixed per-language deriver `generators.derivers.DERIVERS["abnf"]`: an LLM-free
obligation-deriver (the reference token list) + harness-deriver (the independent
reference fields).  Both channels are derived from the HIGH (abnf) spec, never
via the translator under test:

  * channel 1  `translation-abnf-compile-identity` (cross-impl-differential):
      the REFERENCE ksy the deriver builds from the high spec --
      tokens_to_ksy(tokenize(high), sha256(high)) -- must be COMPILE-IDENTICAL
      to the translator's emitted low_spec_text.  A lossy translator that drops
      or renames a field emits a different ksy and is refuted here.
  * channel 2  `translation-abnf-codec-differential` (behavioral-witness): a
      codec differential (Hypothesis round-trip + ksc, NO Dafny) between the
      emitted codec (parse_ksy(low_spec_text)) and the independent reference
      fields (abnf_reference_fields(high)).  A byte divergence refuses.

Teeth:
  (a) a FAITHFUL abnf->ksy translation (built via abnf_chain, the fixed deriver
      route) certifies -- BOTH channels pass.
  (b) a PLANTED LOSSY translation (emit a ksy that DROPS the trailing field) is
      refuted by BOTH channels: a different compile hash AND a codec differential
      byte-divergence.  No certificate issues.

REQUIRES_LLM = False
"""
from __future__ import annotations

import json
import pathlib
import sys

import common
import kernel
from kernel.certs import Certificate
from generators import abnf_chain, emitters

REQUIRES_LLM = False

# An abnf spec from the committed backlog (an existing, standard notation).
SPEC_PATH = pathlib.Path(__file__).resolve().parent / "specs/backlog/k_abnf_001.abnf"


def _faithful():
    """The faithful abnf->ksy translation: the fixed-deriver route itself.
    Returns (high_text, low_ksy, low_files)."""
    high = SPEC_PATH.read_text()
    toks = abnf_chain.tokenize(high)
    sha = common.sha256_bytes(high.encode())
    low_ksy = abnf_chain.tokens_to_ksy(toks, sha)
    low_files = emitters.emit_ksc_python_rw(low_ksy)
    return high, low_ksy, low_files


def _lossy():
    """A planted LOSSY translation: emit a ksy that DROPS the final field
    (the trailing CRLF literal), so it differs from the reference ksy.  Returns
    (high_text, low_ksy, low_files)."""
    high = SPEC_PATH.read_text()
    toks = abnf_chain.tokenize(high)
    sha = common.sha256_bytes(high.encode())
    dropped = toks[:-1]                      # drop the last token -> lossy
    low_ksy = abnf_chain.tokens_to_ksy(dropped, sha)
    low_files = emitters.emit_ksc_python_rw(low_ksy)
    return high, low_ksy, low_files


def _contract(high, low_ksy, low_files):
    return {"type": "translation-cert", "anchor": "fixed-deriver",
            "high_language": "abnf", "high_spec_text": high,
            "low_spec_text": low_ksy, "low_artifact_files": low_files}


def _check(high, low_ksy, low_files):
    v = kernel.check({"kind": "translation", "files": low_files},
                     _contract(high, low_ksy, low_files))
    if isinstance(v, Certificate):
        return v, True, v.channels
    return v, False, v.to_dict()["channels"]


def part_a() -> bool:
    print("== Tooth (a): a faithful abnf->ksy translation certifies (both) ==")
    high, low_ksy, low_files = _faithful()
    v, ok, ch = _check(high, low_ksy, low_files)
    chan = [(c["backend"], c["role"], c["result"]) for c in ch]
    print(f"  {'OK' if ok else 'XX'} translation-cert  channels={chan}")
    if ok:
        print(f"  tier={v.tier}  anchor="
              f"{[cl[1] for cl in v.claims if cl[0] == 'anchor']}")
    passed = ok and len(ch) == 2 and all(c["result"] == "pass" for c in ch)
    print(f"  part_a: {passed}")
    return passed


def part_b() -> bool:
    print("\n== Tooth (b): a planted lossy translation is refuted (both) ==")
    high, low_ksy, low_files = _lossy()
    v, ok, ch = _check(high, low_ksy, low_files)
    refuted = not ok
    chan = [(c["backend"], c["role"], c["result"]) for c in ch]
    ch1_fail = any(c["backend"] == "translation-abnf-compile-identity"
                   and c["result"] != "pass" for c in ch)
    ch2_fail = any(c["backend"] == "translation-abnf-codec-differential"
                   and c["result"] != "pass" for c in ch)
    print(f"  refuted={refuted}  channels={chan}")
    print(f"  channel-1 (compile identity) refutes:   {ch1_fail}")
    print(f"  channel-2 (codec differential) refutes: {ch2_fail}")
    for c in ch:
        if c["result"] != "pass":
            print(f"    [{c['backend']}] {c.get('detail', '')[:160]}")
    passed = refuted and ch1_fail and ch2_fail
    print(f"  part_b: {passed}")
    return passed


if __name__ == "__main__":
    a, b = part_a(), part_b()
    print("\nsummary:", json.dumps({
        "tooth_a_faithful_translation_certifies": a,
        "tooth_b_lossy_translation_refuted_both_channels": b}))
    sys.exit(0 if all([a, b]) else 1)

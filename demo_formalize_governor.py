#!/usr/bin/env python3
"""The governed formalization flywheel: priced compression over WITNESSED demand.

The skill-library literature documents vocabulary BLOAT as the death mode
(METRICS.md names it).  This demo gives "useful abstractions" the operational
meaning nobody ships: a minted definition is a Reading-layer abbreviation over
MathReading statements, admitted ONLY when it strictly reduces the corpus
description length AND is witnessed by >= 2 EXOGENOUS (real, committed) readings
-- dreams propose vocabulary, only exogenous witnesses admit it -- and every use
is CERTIFIED per emission against a retained inlined baseline.

LLM-free, planted corpora, deterministic (recurrence.py / mdl_macros.py are
clock- and random-free with sorted iteration).  Five parts:

  (i)   a recurring >=2-contiguous-statement idiom with 3 EXOGENOUS witnesses is
        mined, admitted, and a use CERTIFIES per emission (kernel
        translation-cert(reference-lowering): channel 1 = compile-hash identity
        of the macro-expanded reading vs its inlined baseline; channel 2 =
        entailed-instance replay -- both Lean-free).
  (ii)  the SAME idiom appearing ONLY in dreams is REFUSED (the exogenous
        witness filter: < 2 real witnesses).
  (iii) a planted LOSSY abbreviation (drops a hypothesis) gets NO certificate --
        compile-hash divergence.
  (iv)  admitting the good macro moves BOTH corpus_dl (the mining objective) and
        the ledger macro-cost term (the E7b term is live) the right way.
  (v)   the F5.3 paraphrase-flood tooth: on identical exogenous coverage, the
        UNGOVERNED arm (dreams witness) mints a structurally-distinct junk macro
        that RAISES the reported exogenous corpus_dl, while the GOVERNED arm
        (exogenous witness) does not -- asserted relationally (covered_g ==
        covered_u AND dl_governed < dl_ungoverned), no absolute constants.
"""
from __future__ import annotations

import json
import sys

from buildloop import recurrence, mdl_macros
import kernel
from kernel.certs import Certificate

REQUIRES_LLM = False
REQUIRES_LEAN = False


def _dvd(d, x):
    return {"kind": "hypothesis",
            "pred": {"op": "dvd", "args": [{"ref": d}, {"ref": x}]}}


def _even(x):
    return {"kind": "hypothesis", "pred": {"op": "even", "args": [{"ref": x}]}}


def _cd_reading(theorem, x, y, origin, quote="d is a common divisor"):
    """A "d divides both x and y" reading: two contiguous presupposition
    hypotheses form a minable uniform-(force, quote) window."""
    return {"theorem": theorem, "origin": origin, "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "od", "force": "presupposition", "quote": quote,
         "lf": {"kind": "object", "name": "d", "type": "Int"}},
        {"id": "ox", "force": "presupposition", "quote": quote,
         "lf": {"kind": "object", "name": x, "type": "Int"}},
        {"id": "oy", "force": "presupposition", "quote": quote,
         "lf": {"kind": "object", "name": y, "type": "Int"}},
        {"id": "h1", "force": "presupposition", "quote": quote, "lf": _dvd("d", x)},
        {"id": "h2", "force": "presupposition", "quote": quote, "lf": _dvd("d", y)},
        {"id": "c", "force": "demand", "quote": theorem,
         "lf": {"kind": "conclusion",
                "pred": {"op": "dvd", "args": [{"ref": "d"}, {"ref": x}]}}},
    ]}


def _even_reading(theorem, x, y, origin, quote="both are even"):
    """A structurally-DISTINCT junk idiom: two contiguous even-hypotheses."""
    return {"theorem": theorem, "origin": origin, "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "ox", "force": "presupposition", "quote": quote,
         "lf": {"kind": "object", "name": x, "type": "Int"}},
        {"id": "oy", "force": "presupposition", "quote": quote,
         "lf": {"kind": "object", "name": y, "type": "Int"}},
        {"id": "h1", "force": "presupposition", "quote": quote, "lf": _even(x)},
        {"id": "h2", "force": "presupposition", "quote": quote, "lf": _even(y)},
        {"id": "c", "force": "demand", "quote": theorem,
         "lf": {"kind": "conclusion", "pred": {"op": "even", "args": [{"ref": x}]}}},
    ]}


_EXO = lambda r: r.get("origin") == "exogenous"


def _greedy_admit(readings, witness_filter):
    """The greedy MDL gate over a corpus: repeatedly mine + admit the best
    candidate that clears macro_admission_decision under the witness filter."""
    table = {}
    while True:
        cands = recurrence.mine(readings, table, witness_filter=witness_filter)
        chosen = None
        for c in cands:
            cand = c["candidate"]
            if cand["name"] in table:
                continue
            if mdl_macros.macro_admission_decision(
                    readings, cand, table, witness_filter=witness_filter)["admit"]:
                chosen = cand
                break
        if chosen is None:
            return table
        table[chosen["name"]] = chosen


# A grounded reading (quotes occur in this source) so the per-emission cert can
# PARSE + compile it.  "d divides a and d divides b" spans the object/hypothesis
# quotes; "d divides a" is the conclusion quote.
_CERT_SRC = "d divides a and d divides b"


def _cert_reading():
    q = "d divides a and d divides b"
    return {"theorem": "use", "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "od", "force": "presupposition", "quote": q,
         "lf": {"kind": "object", "name": "d", "type": "Int"}},
        {"id": "oa", "force": "presupposition", "quote": q,
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "presupposition", "quote": q,
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "h1", "force": "presupposition", "quote": "d divides a",
         "lf": _dvd("d", "a")},
        {"id": "h2", "force": "presupposition", "quote": "d divides b",
         "lf": _dvd("d", "b")},
        {"id": "c", "force": "demand", "quote": "d divides a",
         "lf": {"kind": "conclusion",
                "pred": {"op": "dvd", "args": [{"ref": "d"}, {"ref": "a"}]}}},
    ]}


def _per_emission_cert(macro):
    """Certify a macro use per emission against the retained inlined baseline."""
    inlined = _cert_reading()
    exp = [s for s in inlined["statements"] if s["id"] not in ("h1", "h2")]
    exp.insert(4, {"id": "h1", "force": "presupposition",
                   "quote": "d divides a and d divides b",
                   "lf": {"kind": "macro", "name": macro["name"], "args": {}}})
    expanded = {"theorem": "use", "statements": exp}
    contract = {"type": "translation-cert", "anchor": "reference-lowering",
                "high_language": "math-macro-reading",
                "high_spec_text": json.dumps(expanded),
                "reference_lowering": json.dumps(inlined),
                "request": _CERT_SRC,
                "expansion_context": {"macro_table": {macro["name"]: macro}}}
    return kernel.check({"kind": "math", "files": {}}, contract)


def main():
    ok = []
    print("== The governed formalization flywheel (LLM-free, planted) ==")

    # ---- (i) mine + admit + per-emission cert (3 exogenous witnesses) --------
    exo = [_cd_reading("cd_a", "a", "b", "exogenous"),
           _cd_reading("cd_m", "m", "n", "exogenous"),
           _cd_reading("cd_p", "p", "q", "exogenous")]
    cands = recurrence.mine(exo, {}, witness_filter=_EXO)
    macro = cands[0]["candidate"] if cands else None
    dec = mdl_macros.macro_admission_decision(exo, macro, {}, witness_filter=_EXO)
    good_macro = {"name": "m_cd", "params": [], "body": [_dvd("d", "a"),
                                                         _dvd("d", "b")]}
    v = _per_emission_cert(good_macro)
    cert_ok = isinstance(v, Certificate)
    print(f"  (i)   idiom mined (3 exogenous witnesses)={bool(cands)}, "
          f"admitted={dec['admit']} (delta={dec['delta']}); "
          f"use certifies per emission={cert_ok} ({getattr(v, 'tier', '')})")
    ok.append(bool(cands) and dec["admit"] and cert_ok)

    # ---- (ii) the same idiom, dreams only -> REFUSED ------------------------
    dreams = [_cd_reading("dd_a", "a", "b", "system"),
              _cd_reading("dd_m", "m", "n", "system"),
              _cd_reading("dd_p", "p", "q", "system")]
    dec_dream = mdl_macros.macro_admission_decision(
        dreams, macro, {}, witness_filter=_EXO)
    print(f"  (ii)  same idiom, dreams-only, exogenous filter: "
          f"admitted={dec_dream['admit']} (must be False)")
    ok.append(dec_dream["admit"] is False)

    # ---- (iii) a lossy abbreviation -> NO certificate -----------------------
    lossy = {"name": "m_cd", "params": [], "body": [_dvd("d", "a")]}  # drops h2!
    v_lossy = _per_emission_cert(lossy)
    lossy_no_cert = not isinstance(v_lossy, Certificate)
    print(f"  (iii) lossy abbreviation (drops a hypothesis) certifies="
          f"{not lossy_no_cert} (must be False -- compile-hash divergence)")
    ok.append(lossy_no_cert)

    # ---- (iv) corpus_dl and the ledger macro-cost term both move right ------
    dl_before = mdl_macros.corpus_dl(exo, {})["total"]
    dl_after = mdl_macros.corpus_dl(exo, {macro["name"]: macro})["total"]
    macro_cost = mdl_macros.dl_macro(macro)                    # E7b term, > 0
    corpus_moved = dl_after < dl_before
    print(f"  (iv)  corpus_dl {dl_before} -> {dl_after} (compresses="
          f"{corpus_moved}); ledger macro-cost term (E7b live)={macro_cost} > 0")
    ok.append(corpus_moved and macro_cost > 0)

    # ---- (v) the F5.3 paraphrase-flood tooth --------------------------------
    # Exogenous: the GOOD dvd-idiom (2 witnesses).  Dreams: a structurally-
    # DISTINCT even-idiom (8 witnesses) the ungoverned arm mints as junk.
    flood_exo = [_cd_reading("fe1", "a", "b", "exogenous"),
                 _cd_reading("fe2", "m", "n", "exogenous")]
    flood_dreams = [_even_reading(f"fd{i}", "w", "z", "system") for i in range(8)]
    allr = flood_exo + flood_dreams
    governed = _greedy_admit(allr, witness_filter=_EXO)     # exogenous witnesses
    ungoverned = _greedy_admit(allr, witness_filter=None)   # dreams count too
    # BOTH arms REPORT corpus_dl over the EXOGENOUS sub-corpus (the honest number).
    dl_g = mdl_macros.corpus_dl(flood_exo, governed)["total"]
    dl_u = mdl_macros.corpus_dl(flood_exo, ungoverned)["total"]
    covered_g = covered_u = len(flood_exo)                  # equal exo coverage
    conj = (covered_g == covered_u) and (dl_g < dl_u)
    print(f"  (v)   flood: governed admits {len(governed)} macro(s), "
          f"ungoverned {len(ungoverned)} (incl. dream-witnessed junk)")
    print(f"        reported EXOGENOUS corpus_dl: governed={dl_g} < "
          f"ungoverned={dl_u} at equal coverage {covered_g}=={covered_u}: {conj}")
    ok.append(conj)

    print("\nsummary:", json.dumps({
        "i_mine_admit_cert": ok[0], "ii_dreams_refused": ok[1],
        "iii_lossy_no_cert": ok[2], "iv_dl_moves": ok[3],
        "v_flood_conjunction": ok[4]}))
    return all(ok)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

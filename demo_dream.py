#!/usr/bin/env python3
"""S5.3 -- the Z-E witness discipline: dreams propose, only real witnesses decide.

Zone 3 lets the system DREAM readings (system-origin) to explore, but a dream may
only PROPOSE a recurrence macro -- it can never be the witness that admits one.
Every DL-pricing entry point (`mine`, `macro_admission_decision`, `gc_macros`,
`searched_macro_sequence`) takes an additive `witness_filter`; when set to the
exogenous predicate it restricts the readings that price the corpus (and count as
witnesses) to the real ones.  Provenance itself is enforced upstream, at seed
time, by `cgb._seed_readings` (H44).

Three teeth (exit 0 iff all pass):

  (i)   A clean 2-statement pattern witnessed by 3 DREAM readings and 0 REAL ones
        is MINED without the filter but REFUSED under it (no real witnesses);
        hand-adding the same pattern to 2 REAL readings FLIPS it to admitted.
  (ii)  Perturbing the dream corpus (its non-shared statements) leaves the
        admitted, witness-filtered sequence byte-unchanged -- the objective sees
        only the real witnesses.
  (iii) The seed-time provenance hard-error (a real-classified reading with no
        committed request byte-match) is enforced by `cgb._seed_readings`; we
        drive it here on a temp tree, mirroring tests/test_seed_readings.py.

REQUIRES_LLM = False -- every corpus is planted and the seed hard-error fires
before any certification runs; nothing calls the LLM or the kernel.
Determinism: no random, no clocks, canonical JSON throughout.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import common
from buildloop import recurrence, mdl_macros

REQUIRES_LLM = False

# the S5 witness predicate: real == exogenous-origin, dream == system-origin.
EXO = lambda r: r.get("origin") == "exogenous"


# ----------------------------------------------------------- planted LFs
def _lf_a():
    return {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}


def _lf_b():
    return {"kind": "bound", "action": "a", "left": "n", "cmp": "<=", "right": "q"}


def _filler(tag):
    return {"kind": "effect", "action": "act", "quantity": "q",
            "op": "dec", "amount": {"arg": tag}}


def _stmt(sid, lf, force="demand", quote="s"):
    return {"id": sid, "force": force, "quote": quote, "lf": lf}


def _pattern(prefix):
    """The clean uniform-(force, quote) 2-statement demand cluster over distinct
    LF kinds -- anti-unifies to a fully concrete, parameter-free (H3-passing)
    body, so its candidate name is stable across corpora."""
    return [_stmt(f"{prefix}0", _lf_a()), _stmt(f"{prefix}1", _lf_b())]


def _reading(service, origin, statements):
    return {"service": service, "origin": origin, "statements": statements}


def _singleton(name):
    return _reading(name, "exogenous",
                    [_stmt(f"{name}a", {"kind": "action", "name": "go"},
                           force="choice", quote="")])


def _dream_only():
    """Pattern in 3 dream witnesses, 0 real witnesses."""
    return [_reading("d1", "system", _pattern("d1")),
            _reading("d2", "system", _pattern("d2")),
            _reading("d3", "system", _pattern("d3")),
            _singleton("r1"), _singleton("r2")]


def _flipped():
    """The 3 dream witnesses PLUS the pattern hand-added to 2 real readings."""
    return [_reading("d1", "system", _pattern("d1")),
            _reading("d2", "system", _pattern("d2")),
            _reading("d3", "system", _pattern("d3")),
            _reading("r1", "exogenous", _pattern("r1")),
            _reading("r2", "exogenous", _pattern("r2"))]


def _report(label, ok):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


# ================================================================ tooth (i)
def tooth_propose_refuse_flip():
    print("== (i) dreams propose, real witnesses decide ==")
    ok = True

    dream_only = _dream_only()
    proposed = recurrence.mine(dream_only, {})
    ok &= _report("3 dream / 0 real: pattern is MINED without the filter",
                  proposed != [])

    refused = recurrence.mine(dream_only, {}, witness_filter=EXO)
    ok &= _report("3 dream / 0 real: REFUSED under the exogenous filter (mine=[])",
                  refused == [])

    cand = proposed[0]["candidate"]
    dec = mdl_macros.macro_admission_decision(dream_only, cand, witness_filter=EXO)
    ok &= _report(f"admission gate: admit=False, real uses={dec['uses']}",
                  dec["admit"] is False and dec["uses"] == 0)

    flipped = _flipped()
    mined = recurrence.mine(flipped, {}, witness_filter=EXO)
    same = bool(mined) and mined[0]["candidate"] == cand
    ok &= _report("flip: add pattern to 2 REAL readings -> same candidate mines",
                  same and mined[0]["uses"] == 2)
    dec2 = mdl_macros.macro_admission_decision(flipped, cand, witness_filter=EXO)
    ok &= _report(f"flip: admission gate FLIPS to admit=True (real uses={dec2['uses']})",
                  dec2["admit"] is True and dec2["uses"] >= 2)
    return ok


# =============================================================== tooth (ii)
def tooth_objective_invariance():
    print("== (ii) perturbing the dream corpus leaves the admitted sequence fixed ==")
    reals = [_reading("r1", "exogenous", _pattern("r1")),
             _reading("r2", "exogenous", _pattern("r2"))]

    def dream(name, tag):
        return _reading(name, "system",
                        _pattern(name) + [_stmt(f"{name}f", _filler(tag))])

    v1 = reals + [dream("d1", "x"), dream("d2", "y"), dream("d3", "z")]
    v2 = reals + [dream("d1", "P1"), dream("d2", "P2"), dream("d3", "P3")]

    m1 = recurrence.mine(v1, {}, witness_filter=EXO)
    m2 = recurrence.mine(v2, {}, witness_filter=EXO)
    mine_ok = (m1 != [] and
               common.canonical_json(m1) == common.canonical_json(m2))
    ok = _report("witness-filtered mine() is byte-identical across perturbation",
                 mine_ok)

    s1 = recurrence.searched_macro_sequence(v1, {}, witness_filter=EXO)
    s2 = recurrence.searched_macro_sequence(v2, {}, witness_filter=EXO)
    seq_ok = (sorted(s1) != [] and sorted(s1) == sorted(s2) and
              common.canonical_json(s1) == common.canonical_json(s2))
    ok &= _report(f"admitted searched sequence is unchanged (macros={sorted(s1)})",
                  seq_ok)
    return ok


# ============================================================== tooth (iii)
def tooth_seed_provenance_hard_error():
    print("== (iii) seed-time provenance hard-error (enforced in cgb._seed_readings) ==")
    import cgb                                        # imported lazily; LLM-free path
    from library import Registry

    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, "specs", "readings"))
    os.makedirs(os.path.join(tmp, "specs", "requests"))   # committed, but EMPTY
    # a grounded-enough, top-level (real-classified) reading whose request
    # byte-matches NO committed specs/requests file -> must hard-error (H44).
    bad = {"request": "an uncommitted request that matches nothing",
           "reading": {"service": "svc", "statements": [
               {"id": "s1", "force": "choice", "quote": "",
                "lf": {"kind": "action", "name": "go"}},
               {"id": "s2", "force": "choice", "quote": "",
                "lf": {"kind": "lifecycle", "states": ["open", "closed"],
                       "initial": "open"}}]}}
    with open(os.path.join(tmp, "specs", "readings", "orphan.json"), "w") as fh:
        fh.write(json.dumps(bad))

    reg = Registry(db_path=os.path.join(tempfile.mkdtemp(), "reg.sqlite"))
    raised = False
    try:
        cgb._seed_readings(reg, root=tmp)
    except SystemExit:
        raised = True                                 # the H44 hard-error fired
    ok = _report("real-classified reading with no byte-match -> SystemExit at seed",
                 raised)
    print("      (documented: this provenance gate is also covered by "
          "tests/test_seed_readings.py)")
    return ok


def main():
    ok = True
    ok &= tooth_propose_refuse_flip()
    ok &= tooth_objective_invariance()
    ok &= tooth_seed_provenance_hard_error()
    print()
    print("ALL TEETH PASS" if ok else "TEETH FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

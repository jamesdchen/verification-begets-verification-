"""WP-J: the governed formalization flywheel for math readings (F3.3/F3.4).

Mining, the exogenous witness discipline, per-emission certification via the
pluggable-replay kernel seam (A2), and the F5.3 flood tooth -- all LLM-free and
deterministic.  Plus a regression check that the A2 seam left the non-math
reference-lowering path unchanged.
"""
import json

import kernel
from kernel.certs import Certificate
from buildloop import recurrence, mdl_macros

import demo_formalize_governor as G


def test_idiom_mined_and_admitted_under_exogenous_witnesses():
    exo = [G._cd_reading("a", "a", "b", "exogenous"),
           G._cd_reading("b", "m", "n", "exogenous"),
           G._cd_reading("c", "p", "q", "exogenous")]
    cands = recurrence.mine(exo, {}, witness_filter=G._EXO)
    assert cands, "the common-divisor idiom should mine over 3 exogenous readings"
    dec = mdl_macros.macro_admission_decision(
        exo, cands[0]["candidate"], {}, witness_filter=G._EXO)
    assert dec["admit"] and dec["delta"] < 0


def test_dreams_do_not_witness_admission():
    # the SAME structural idiom, but every witness is a dream (system-origin):
    # the exogenous filter must refuse it (< 2 real witnesses).
    exo = [G._cd_reading("a", "a", "b", "exogenous"),
           G._cd_reading("b", "m", "n", "exogenous")]
    macro = recurrence.mine(exo, {}, witness_filter=G._EXO)[0]["candidate"]
    dreams = [G._cd_reading("d1", "a", "b", "system"),
              G._cd_reading("d2", "m", "n", "system"),
              G._cd_reading("d3", "p", "q", "system")]
    dec = mdl_macros.macro_admission_decision(
        dreams, macro, {}, witness_filter=G._EXO)
    assert dec["admit"] is False


def test_per_emission_cert_issues_for_faithful_macro():
    good = {"name": "m_cd", "params": [],
            "body": [G._dvd("d", "a"), G._dvd("d", "b")]}
    v = G._per_emission_cert(good)
    assert isinstance(v, Certificate)


def test_lossy_abbreviation_gets_no_certificate():
    lossy = {"name": "m_cd", "params": [], "body": [G._dvd("d", "a")]}  # drops h2
    v = G._per_emission_cert(lossy)
    assert not isinstance(v, Certificate)


def test_flood_tooth_governed_beats_ungoverned_at_equal_coverage():
    flood_exo = [G._cd_reading("fe1", "a", "b", "exogenous"),
                 G._cd_reading("fe2", "m", "n", "exogenous")]
    dreams = [G._even_reading(f"fd{i}", "w", "z", "system") for i in range(8)]
    allr = flood_exo + dreams
    governed = G._greedy_admit(allr, witness_filter=G._EXO)
    ungoverned = G._greedy_admit(allr, witness_filter=None)
    dl_g = mdl_macros.corpus_dl(flood_exo, governed)["total"]
    dl_u = mdl_macros.corpus_dl(flood_exo, ungoverned)["total"]
    # equal exogenous coverage, strictly lower governed exogenous DL (E5).
    assert dl_g < dl_u
    assert len(ungoverned) > len(governed)   # ungoverned mints the junk macro


def test_a2_seam_leaves_non_math_lowering_unchanged():
    # A macro-reading (non-math) translation-cert must still route through the
    # DEFAULT replay -- the A2 seam only adds a `replay` key to the math entry.
    from generators import derivers
    assert "replay" not in derivers.LOWERINGS["reading"]
    assert "replay" not in derivers.LOWERINGS["macro-reading"]
    assert "replay" in derivers.LOWERINGS["math-macro-reading"]


def test_demo_runs_green():
    assert G.main() is True

"""S1 (MATH) teeth -- searched vs greedy macro admission on planted MathReadings.

Guards the math-side analogue of the service S1 trap
(`tests/test_searched_recurrence_flag.py` / `demos/demo_macro_search.py`).  Every
assertion is RELATIONAL -- searched < greedy on the trap, searched == greedy on
the clean corpus -- never a brittle absolute description-length constant
(E5/H52).  Determinism, the admission-gate discipline (Z1), and the global
default of `SEARCHED_RECURRENCE` are all pinned so this work flips nothing
elsewhere.

Deterministic and LLM-free: the corpora are planted inline in
`demo_macro_search_math`, nothing calls the LLM or the kernel.
"""
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

import common
from buildloop import loop
from buildloop.mdl_macros import corpus_dl, macro_admission_decision

from demos import demo_macro_search_math as dm


# --------------------------------------------------------------- the trap tooth
def test_trap_conjunction_searched_strictly_beats_greedy():
    """The load-bearing claim: on the trap, greedy strands on the single len-4
    macro while the searched sequence admits the strictly cheaper pair, at EQUAL
    coverage.  Relational only -- no absolute DL constant is asserted."""
    corpus = dm.trap_corpus()
    g = dm.greedy_table(corpus)
    s = dm.searched_table(corpus)

    # greedy is stranded at one macro; search reaches two.
    assert len(g) == 1, "greedy should strand on the single len-4 idiom macro"
    assert len(s) == 2, "search should reach the {[obj,op], [hyp,concl]} pair"

    greedy_dl = corpus_dl(corpus, g)["total"]
    searched_dl = corpus_dl(corpus, s)["total"]

    # equal coverage (a macro table is a lossless re-encoding -- neither arm
    # drops a reading) AND a STRICTLY lower searched description length.
    assert dm.coverage(corpus, g) == dm.coverage(corpus, s) == len(corpus)
    assert searched_dl < greedy_dl, (searched_dl, greedy_dl)

    # the searched pair is a proper superset relationship: it is not the greedy
    # table plus extras, it is a different, cheaper table.
    assert set(g) != set(s)


# ---------------------------------------------------------------- the tie tooth
def test_clean_corpus_is_an_honest_tie():
    """On a clean corpus with a single globally-optimal cluster, greedy and
    searched land BYTE-IDENTICAL tables and equal description length -- a tie is
    a recorded finding, not a defect (the H24 lesson)."""
    corpus = dm.clean_corpus()
    g = dm.greedy_table(corpus)
    s = dm.searched_table(corpus)

    assert common.canonical_json(g) == common.canonical_json(s)
    assert corpus_dl(corpus, s)["total"] == corpus_dl(corpus, g)["total"]
    assert dm.coverage(corpus, g) == dm.coverage(corpus, s) == len(corpus)
    # a non-trivial tie: both actually admitted the shared idiom, not nothing.
    assert len(g) == 1 and len(s) == 1


# ------------------------------------------------------ the admission-gate tooth
def test_every_admitted_macro_passes_the_explicit_gate():
    """Z1: the search never bypasses `macro_admission_decision`.  Every macro in
    BOTH arms of BOTH corpora independently clears the explicit gate against the
    rest of its table."""
    for builder in (dm.trap_corpus, dm.clean_corpus):
        corpus = builder()
        for table in (dm.greedy_table(corpus), dm.searched_table(corpus)):
            assert dm.gate_holds(corpus, table)
            # spelled out (not only via the helper) so the discipline is visible.
            for name, macro in table.items():
                rest = {k: v for k, v in table.items() if k != name}
                decision = macro_admission_decision(corpus, macro, rest)
                assert decision["admit"], (name, decision)
                assert decision["uses"] >= 2       # the two-witness discipline


# ------------------------------------------------------------- determinism tooth
def test_two_runs_produce_byte_identical_csv(tmp_path):
    """Running the demo twice yields byte-identical CSV -- no random, no clocks,
    canonical JSON throughout."""
    demo = _ROOT / "demos/demo_macro_search_math.py"
    csv_path = _ROOT / "results" / "macro_search_math.csv"

    def _run_and_read():
        proc = subprocess.run([sys.executable, str(demo)],
                              cwd=str(_ROOT), capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        return csv_path.read_bytes()

    first = _run_and_read()
    second = _run_and_read()
    assert first == second


def test_row_construction_is_deterministic():
    """The in-process row list is identical across two independent builds (a
    fast, subprocess-free determinism check on the same data path)."""
    rows_a, rows_b = [], []
    dm.run(rows_a)
    dm.run(rows_b)
    assert common.canonical_json(rows_a) == common.canonical_json(rows_b)


# ------------------------------------------------------- global-default guard
def test_searched_recurrence_flag_default_is_false():
    """This work flips nothing globally: the scheduler's recurrence dispatcher
    stays greedy by default.  The math demo drives `searched_macro_sequence`
    directly and never touches the module flag."""
    assert loop.SEARCHED_RECURRENCE is False


def test_demo_is_llm_free():
    """The first executable line after the docstring is REQUIRES_LLM = False --
    every corpus is planted; the `--full` regression glob must never gate this
    demo as an LLM item."""
    assert dm.REQUIRES_LLM is False


if __name__ == "__main__":
    import tempfile
    test_trap_conjunction_searched_strictly_beats_greedy()
    test_clean_corpus_is_an_honest_tie()
    test_every_admitted_macro_passes_the_explicit_gate()
    test_two_runs_produce_byte_identical_csv(pathlib.Path(tempfile.mkdtemp()))
    test_row_construction_is_deterministic()
    test_searched_recurrence_flag_default_is_false()
    test_demo_is_llm_free()
    print("ALL MACRO-SEARCH-MATH TEETH PASS")

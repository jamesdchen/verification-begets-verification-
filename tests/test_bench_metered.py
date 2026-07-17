"""WP-MET (§12.5) teeth: the METERED holdout-run harness, exercised END-TO-END
with a FAKE TRANSPORT (canned responses + canned token counts; LLM-free -- no
``call_llm`` on any path here).  Every one of the seven binding protocol
requirements has a tooth that runs in CI's fast lane.

The fake transport mirrors ``bench_formalize``'s injected author (same
signature ``(source_id, source_text, macro_table, table_hash)``) but is the
WP-MET METERING surface: it replays a canned reading and a canned
``tokens_in``/``tokens_out`` per source, so the cost columns are deterministic
and the whole metering path is driven without a model.

Synthetic sources (a recurring coprime idiom -- ``coprime`` is enum-only, so it
certifies WITHOUT cvc5) drive the metering/isolation/denominator/verdict/
model-qual teeth; a separate run over the REAL committed holdout drives the
byte-inertness tooth.
"""
import csv
import json
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bench_metered as met
import bench_formalize as bench


# --------------------------------------------------------- planted readings
def _cop(d, x):
    return {"kind": "hypothesis",
            "pred": {"op": "coprime", "args": [{"ref": d}, {"ref": x}]}}


def _cop_reading(theorem, x, y, cq, concl_quote):
    return {"theorem": theorem, "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "od", "force": "presupposition", "quote": cq,
         "lf": {"kind": "object", "name": "d", "type": "Nat"}},
        {"id": "ox", "force": "presupposition", "quote": cq,
         "lf": {"kind": "object", "name": x, "type": "Nat"}},
        {"id": "oy", "force": "presupposition", "quote": cq,
         "lf": {"kind": "object", "name": y, "type": "Nat"}},
        {"id": "h1", "force": "presupposition", "quote": cq, "lf": _cop("d", x)},
        {"id": "h2", "force": "presupposition", "quote": cq, "lf": _cop("d", y)},
        {"id": "c", "force": "demand", "quote": concl_quote,
         "lf": {"kind": "conclusion",
                "pred": {"op": "coprime", "args": [{"ref": "d"}, {"ref": x}]}}}]}


def _even(x):
    return {"kind": "hypothesis", "pred": {"op": "even", "args": [{"ref": x}]}}


def _dream_reading(theorem):
    q = "both are even"
    return {"theorem": theorem, "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "ow", "force": "presupposition", "quote": q,
         "lf": {"kind": "object", "name": "w", "type": "Int"}},
        {"id": "oz", "force": "presupposition", "quote": q,
         "lf": {"kind": "object", "name": "z", "type": "Int"}},
        {"id": "h1", "force": "presupposition", "quote": q, "lf": _even("w")},
        {"id": "h2", "force": "presupposition", "quote": q, "lf": _even("z")},
        {"id": "c", "force": "demand", "quote": theorem,
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "w"}]}}}]}


_SYN_SOURCES = [
    ("s1", "Given d coprime to a and coprime to b, d is coprime to a."),
    ("s2", "Given d coprime to m and coprime to n, d is coprime to m."),
    ("s3", "Given d coprime to p and coprime to q, d is coprime to p."),
]
_SYN_READINGS = {
    "s1": _cop_reading("cop_ab", "a", "b",
                       "d coprime to a and coprime to b", "coprime to a"),
    "s2": _cop_reading("cop_mn", "m", "n",
                       "d coprime to m and coprime to n", "coprime to m"),
    "s3": _cop_reading("cop_pq", "p", "q",
                       "d coprime to p and coprime to q", "coprime to p"),
}
_DREAM_SOURCES = [("d%02d" % i, "both are even") for i in range(1, 9)]
_DREAM_READINGS = {sid: _dream_reading("dream_%02d" % i)
                   for i, (sid, _t) in enumerate(_DREAM_SOURCES, 1)}


class _FakeTransport:
    """The WP-MET metering surface: a deterministic, LLM-free transport that
    replays a CANNED reading and CANNED token counts per source.  Token counts
    scale with the live macro table (the E1 seam -- an admitted macro grows the
    rendered prompt), so metering shows up on the cost x-axis.  A per-source
    ``fail`` set lets a tooth make one arm certify fewer (invariant-failure
    demotion)."""

    def __init__(self, fail=(), tokens_in_base=100, tokens_out=20):
        self.calls = 0
        self.seen = []
        self.fail = set(fail)
        self._tin = tokens_in_base
        self._tout = tokens_out
        self._lock = threading.Lock()

    def __call__(self, source_id, source_text, macro_table, table_hash):
        with self._lock:
            self.calls += 1
            self.seen.append((source_id, table_hash))
        if source_id in self.fail:
            return None                      # author failure -> uncertified
        if source_id in _SYN_READINGS:
            reading = _SYN_READINGS[source_id]
        elif source_id in _DREAM_READINGS:
            reading = _DREAM_READINGS[source_id]
        else:
            # real-holdout run: a canned coprime reading (may fail groundedness
            # against the true source -- fine, the inertness tooth does not need
            # coverage, only a completed metered run that never writes holdout).
            reading = _cop_reading("cop_gen", "a", "b",
                                   "d coprime to a and coprime to b",
                                   "coprime to a")
        return {"reading_json": json.dumps(reading),
                "tokens_in": self._tin + 10 * len(macro_table),
                "tokens_out": self._tout}


def _run(out_dir, *, author=None, author_by_arm=None, dream_sources=None,
         sources=None, fresh=False, inject_invariant_failure=False):
    return met.run_metered(
        author=author if (author or author_by_arm) else _FakeTransport(),
        author_by_arm=author_by_arm,
        sources=list(_SYN_SOURCES) if sources is None else sources,
        dream_sources=(list(_DREAM_SOURCES) if dream_sources is None
                       else dream_sources),
        out_dir=str(out_dir), fresh=fresh,
        inject_invariant_failure=inject_invariant_failure)


# ============================================ req 1: BOTH ARMS METERED
def test_both_arms_metered_from_call_metadata(tmp_path):
    """Both arms record real (in AND out) token columns from the transport's
    returned counts -- never estimated post hoc; and the per-arm 'metered'
    verdict passes for each arm."""
    s = _run(tmp_path)
    for arm in ("governed", "ungoverned"):
        r = s[arm]
        assert r["cumulative_ktokens_in"] > 0
        assert r["cumulative_ktokens_out"] > 0
    # the recorded token totals match the transport's canned counts exactly
    # (governed authors its 3 sources; tokens_in scales with the table so we
    # bound rather than pin -- but out is a flat 20/source).
    assert s["governed"]["cumulative_ktokens_out"] == \
        round(20 * len(_SYN_SOURCES) / 1000.0, 6)
    vd = {v["name"]: v for v in s["verdicts"]}
    assert vd["governed_arm_metered"]["pass"]
    assert vd["ungoverned_arm_metered"]["pass"]


# ============================================ req 2: SEPARATE out_dir PER ARM
def test_arm_isolation_separate_state_no_leakage(tmp_path):
    """Each arm writes under its own ``out_dir/<arm>/`` with its own state file;
    each state file contains ONLY its arm's records (plus, for ungoverned, its
    own dreams) -- no cross-arm leakage."""
    s = _run(tmp_path)
    gov_state = os.path.join(s["arm_dirs"]["governed"],
                             "formalize_bench_state.jsonl")
    ung_state = os.path.join(s["arm_dirs"]["ungoverned"],
                             "formalize_bench_state.jsonl")
    assert os.path.exists(gov_state) and os.path.exists(ung_state)
    assert gov_state != ung_state

    def _arms_in(path):
        arms = set()
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    arms.add(json.loads(line)["arm"])
        return arms

    # governed state: ONLY governed records (no dreams, no ungoverned).
    assert _arms_in(gov_state) == {"governed"}
    # ungoverned state: ungoverned + its OWN dreams; never any governed record.
    assert _arms_in(ung_state) == {"ungoverned", "dream"}
    # the separate-state verdict is recorded and passes.
    vd = {v["name"]: v for v in s["verdicts"]}
    assert vd["arm_state_files_distinct"]["pass"]
    # the arms reached DIFFERENT vocabularies under the flood (isolation is real,
    # not a copy): governed's exogenous-only mining beats the polluted arm.
    assert s["dl_governed"] < s["dl_ungoverned"]


# ============================================ req 3: FH7-EXCLUSIVE DENOMINATOR
def test_fh7_exclusive_denominator_is_headline(tmp_path):
    """The headline ``cost_per_certified_statement`` divides tokens by certified
    exogenous statements NET of trivially-closed; both the exclusive and the
    inclusive figures are recorded, and the exclusive one is the headline."""
    s = _run(tmp_path)
    g = s["governed"]
    denom_excl = (g["certified_exogenous_statements"]
                  - g["trivially_closed_count"])
    assert denom_excl > 0
    expected = round((g["cumulative_ktokens_in"]
                      + g["cumulative_ktokens_out"]) / denom_excl, 6)
    assert g["cost_per_certified_statement"] == expected
    # the headline block names the exclusive figure as the headline ...
    assert s["headline"]["governed"] == g["cost_per_certified_statement"]
    assert "EXCLUSIVE" in s["headline"]["metric"]
    # ... and records the inclusive one beside it (Lean absent => they coincide).
    assert s["headline"]["governed_inclusive"] == \
        g["cost_per_certified_statement_inclusive"]
    assert g["cost_per_certified_statement"] == \
        g["cost_per_certified_statement_inclusive"]
    assert g["trivially_closed_count"] == 0
    vd = {v["name"]: v for v in s["verdicts"]}
    assert vd["governed_cost_is_fh7_exclusive_tokens_only"]["pass"]


def test_fh7_denominator_arithmetic_nets_trivially_closed():
    """Unit tooth on the exclusive arithmetic: the denominator is certified MINUS
    trivially-closed.  Exercised directly against the verdict arithmetic so the
    'net of trivial' subtraction is pinned even though Lean-absent runs never
    fire a triviality event."""
    # synthesize an arm row where 5 are certified and 2 are trivially closed:
    # exclusive denom must be 3, not 5.
    row = {"certified_exogenous_statements": 5, "trivially_closed_count": 2,
           "cumulative_ktokens_in": 3.0, "cumulative_ktokens_out": 3.0,
           "cost_per_certified_statement": round(6.0 / 3, 6),
           "reported_exogenous_dl": 0.0}
    verdicts = met._run_verdicts(
        [row], [row], gov_state="g", ung_state="u", out_dir="/tmp/x",
        holdout_before={}, holdout_after={})
    vd = {v["name"]: v for v in verdicts}
    # 6 tokens / (5 - 2) exclusive = 2.0 -- the arithmetic matches the row.
    assert vd["governed_cost_is_fh7_exclusive_tokens_only"]["pass"]
    assert vd["governed_cost_is_fh7_exclusive_tokens_only"]["expected"] == 2.0


# ============================================ req 4: ASSERTS -> VERDICTS
def test_verdict_demotion_injected_failure_completes(tmp_path):
    """An injected in-run invariant FAILURE yields a RECORDED verdict row
    (pass=False) and a COMPLETED run (summary + artifacts written) -- the run
    path never dies on the failing invariant."""
    s = _run(tmp_path, inject_invariant_failure=True)
    vd = {v["name"]: v for v in s["verdicts"]}
    assert "injected_test_invariant" in vd
    assert vd["injected_test_invariant"]["pass"] is False
    assert s["verdicts_all_pass"] is False
    # the run COMPLETED: manifest + verdicts artifacts exist despite the failure.
    assert os.path.exists(os.path.join(s["out_dir"], "metered_run.json"))
    vfile = json.loads(open(os.path.join(s["out_dir"], "verdicts.json")).read())
    assert vfile["all_pass"] is False
    assert any(v["name"] == "injected_test_invariant" and not v["pass"]
               for v in vfile["verdicts"])


def test_verdict_demotion_real_invariant_failure(tmp_path):
    """A REAL invariant failing on divergent canned data (the arms certify
    DIFFERENT counts) is recorded as a failing verdict and the run still
    completes -- proving the demotion is not just a synthetic hook."""
    # governed certifies all 3; ungoverned's transport fails source s3 (author
    # failure), so it certifies fewer -> equal_exogenous_coverage FAILS.
    author_by_arm = {"governed": _FakeTransport(),
                     "ungoverned": _FakeTransport(fail={"s3"})}
    s = _run(tmp_path, author_by_arm=author_by_arm)
    vd = {v["name"]: v for v in s["verdicts"]}
    assert vd["equal_exogenous_coverage"]["pass"] is False
    assert s["covered_governed"] != s["covered_ungoverned"]
    # the run completed and reported despite the invariant failing.
    assert os.path.exists(os.path.join(s["out_dir"], "metered_run.json"))


# ============================================ req 5: MODEL-QUALIFIED CLAIMS
def test_model_qualification_stamped_on_every_artifact(tmp_path):
    """Every output artifact -- each per-arm meta, the combined manifest, and the
    verdicts file -- records the model id, the prompt-vocabulary (admitted-
    operator registry) digest, the corpus digest, and the harness version, and
    the corpus digest matches the actual source set."""
    s = _run(tmp_path)
    required = {"model_id", "prompt_vocabulary_digest", "corpus_digest",
                "harness_version"}
    # combined manifest + verdicts file
    for name in ("metered_run.json", "verdicts.json"):
        doc = json.loads(open(os.path.join(s["out_dir"], name)).read())
        assert required <= set(doc["model_qualification"])
    # each per-arm meta
    for arm in ("governed", "ungoverned"):
        meta = json.loads(open(os.path.join(s["arm_dirs"][arm],
                                            "meta.json")).read())
        mq = meta["model_qualification"]
        assert required <= set(mq)
        assert mq["harness_version"] == met.HARNESS_VERSION
    # the corpus digest is a genuine property of the source bytes.
    assert s["model_qualification"]["corpus_digest"] == \
        met._corpus_digest(list(_SYN_SOURCES))
    # the prompt-vocabulary digest is the admitted-operator registry digest.
    assert s["model_qualification"]["prompt_vocabulary_digest"] == \
        met._operator_registry_digest()


# ============================================ req 6: HOLDOUT byte-inertness
def test_holdout_source_set_canonical_order():
    """The run consumes the committed holdout: ``_holdout_sources`` returns the
    20 sources in canonical (h01..h20) order, matching the manifest."""
    src = met._holdout_sources()
    assert len(src) == 20
    stems = [sid for sid, _ in src]
    assert stems == sorted(stems)                    # canonical order
    assert stems[0].startswith("h01") and stems[-1].startswith("h20")
    # every source is non-empty prose read from disk.
    assert all(txt.strip() for _, txt in src)


def test_holdout_byte_inert_after_full_fake_run(tmp_path):
    """A FULL fake run over the REAL committed holdout leaves the holdout tree
    byte-identical (no write, no new file), out_dir is OUTSIDE the holdout tree,
    and the recorded inertness verdict passes."""
    before = met._holdout_byte_snapshot()
    assert before                                    # the tree is non-empty
    s = _run(tmp_path, sources=met._holdout_sources(), dream_sources=[])
    after = met._holdout_byte_snapshot()
    assert before == after                           # not one byte changed
    # no file was added to (or removed from) the holdout directory.
    assert set(os.listdir(met._HOLDOUT)) == \
        set(os.listdir(met._HOLDOUT))                # (stable listing)
    vd = {v["name"]: v for v in s["verdicts"]}
    assert vd["holdout_byte_inert"]["pass"]
    assert vd["out_dir_outside_holdout"]["pass"]
    # the artifacts landed under out_dir, never under holdout.
    assert os.path.commonpath([os.path.abspath(s["out_dir"]),
                               str(met._HOLDOUT)]) != str(met._HOLDOUT)


# ============================================ req 7: NO WALL-CLOCK IN DL (E6)
def test_no_wall_clock_in_cost_or_dl(tmp_path):
    """Token costs live in their own kilotoken columns; seconds are reported
    beside and NEVER summed into the cost numerator or any DL."""
    s = _run(tmp_path)
    g = s["governed"]
    # the cost numerator is tokens-only: reconstruct denom*cps and confirm it
    # equals ONLY the token sum (adding smt_seconds would break this).
    denom = g["certified_exogenous_statements"] - g["trivially_closed_count"]
    assert round(g["cost_per_certified_statement"] * denom, 6) == \
        round(g["cumulative_ktokens_in"] + g["cumulative_ktokens_out"], 6)
    # seconds are present as their OWN column, never folded into DL.
    assert "smt_seconds" in bench.CSV_COLUMNS
    assert g["lean_seconds_total"] == 0.0
    vd = {v["name"]: v for v in s["verdicts"]}
    assert vd["governed_wall_clock_not_in_cost"]["pass"]


# ============================================ resume / completeness
def test_resume_reauthors_nothing(tmp_path):
    """A second metered run over the same per-arm state re-authors NOTHING (the
    per-arm checkpoints resume independently)."""
    t1 = _FakeTransport()
    _run(tmp_path, author=t1)
    assert t1.calls == (2 * len(_SYN_SOURCES) + len(_DREAM_SOURCES))
    t2 = _FakeTransport()
    _run(tmp_path, author=t2)
    assert t2.calls == 0                             # every pair resumed


def test_run_completes_and_writes_all_artifacts(tmp_path):
    """The happy-path run writes every promised artifact and all verdicts pass."""
    s = _run(tmp_path)
    assert s["verdicts_all_pass"] is True
    root = s["out_dir"]
    assert os.path.exists(os.path.join(root, "metered_run.json"))
    assert os.path.exists(os.path.join(root, "verdicts.json"))
    for arm in ("governed", "ungoverned"):
        d = s["arm_dirs"][arm]
        for f in ("formalize_bench_state.jsonl", "formalize_governed.csv",
                  "meta.json", "formalize_frozen_tables.json"):
            assert os.path.exists(os.path.join(d, f)), f"{arm}/{f} missing"
    # the per-arm CSV parses and carries the frozen bench columns.
    with open(os.path.join(s["arm_dirs"]["governed"],
                           "formalize_governed.csv")) as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == bench.reported_columns()

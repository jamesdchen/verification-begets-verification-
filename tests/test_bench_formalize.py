"""WP-D D6 teeth: the wave-parallel, dream-wired, checkpointed, cost-accounted
formalization bench, exercised END-TO-END with an INJECTED deterministic fake
author (LLM-free; no ``call_llm`` on any path here).  cvc5 may be absent -- the
bench degrades honestly, and the coprime idiom below certifies through the
Lean-free ENUMERATION channel (no SMT), so coverage is non-zero regardless.

The planted corpus mirrors demo_formalize_governor part (v):
  * EXOGENOUS: a recurring coprime idiom (contiguous presupposition
    hypotheses) with >=2 witnesses -- both arms mint it, both certify it;
  * DREAMS: an even idiom flooded across the dream corpus that shares the
    idiom's cluster shape.  The GOVERNED arm (exogenous witness filter) mints
    the clean, exo-optimal macro; the UNGOVERNED arm (origin-blind) lets the
    dream flood POLLUTE the shared cluster, so its exogenous compression is
    strictly worse -- the reported EXOGENOUS description length is strictly
    higher.  Governance is enforced by corpus membership + the witness filter.

Asserted RELATIONALLY (⚠E5), never against an absolute constant.
"""
import csv
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bench_formalize as bench


# ------------------------------------------------------------- planted readings
def _cop(d, x):
    return {"kind": "hypothesis",
            "pred": {"op": "coprime", "args": [{"ref": d}, {"ref": x}]}}


def _cop_reading(theorem, x, y, cq, concl_quote):
    """A coprime idiom: two contiguous presupposition hypotheses (coprime is
    enum_only, so this certifies without cvc5)."""
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
    """A structurally DISTINCT even idiom -- the paraphrase flood that shares an
    idiom so the ungoverned arm mints a dream-witnessed junk macro."""
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


# Exogenous sources (the coprime idiom, three witnesses) and their readings.
_EXO_SOURCES = [
    ("e1", "Given d coprime to a and coprime to b, d is coprime to a."),
    ("e2", "Given d coprime to m and coprime to n, d is coprime to m."),
    ("e3", "Given d coprime to p and coprime to q, d is coprime to p."),
]
_EXO_READINGS = {
    "e1": _cop_reading("cop_ab", "a", "b",
                       "d coprime to a and coprime to b", "coprime to a"),
    "e2": _cop_reading("cop_mn", "m", "n",
                       "d coprime to m and coprime to n", "coprime to m"),
    "e3": _cop_reading("cop_pq", "p", "q",
                       "d coprime to p and coprime to q", "coprime to p"),
}
# The dream flood (eight paraphrases sharing the even idiom).
_DREAM_SOURCES = [("d%02d" % i, "both are even") for i in range(1, 9)]
_DREAM_READINGS = {sid: _dream_reading("dream_%02d" % i)
                   for i, (sid, _t) in enumerate(_DREAM_SOURCES, 1)}


class _FakeAuthor:
    """A deterministic, LLM-free author.  Signature matches ``_llm_author``:
    ``(source_id, source_text, macro_table, table_hash)``.  Synthetic token
    counts scale with the live table so an admitted macro shows up on the cost
    x-axis (the E1 mechanism), and a call counter proves resume re-authors
    nothing."""

    def __init__(self):
        self.calls = 0
        self.seen = []

    def __call__(self, source_id, source_text, macro_table, table_hash):
        self.calls += 1
        self.seen.append((source_id, table_hash))
        if source_id in _EXO_READINGS:
            reading = _EXO_READINGS[source_id]
        elif source_id in _DREAM_READINGS:
            reading = _DREAM_READINGS[source_id]
        else:
            return None
        # tokens grow with the table (E1): a bigger admitted vocabulary => a
        # bigger rendered prompt => more input tokens.
        return {"reading_json": json.dumps(reading),
                "tokens_in": 100 + 10 * len(macro_table),
                "tokens_out": 20}


def _run(tmp_path, *, fresh=False, author=None, dream_sources=None):
    author = author or _FakeAuthor()
    summary = bench.run_bench(
        author=author, sources=list(_EXO_SOURCES),
        dream_sources=_DREAM_SOURCES if dream_sources is None else dream_sources,
        out_dir=str(tmp_path), fresh=fresh)
    return author, summary


# ================================================================ D6 teeth
def test_relational_pair_and_dream_flood_strict(tmp_path):
    """Equal exogenous coverage AND governed reported exogenous DL <= ungoverned,
    with STRICT inequality under the planted dream flood."""
    _author, s = _run(tmp_path)
    # equal exogenous coverage (both arms certify the same idiom readings).
    assert s["covered_governed"] == s["covered_ungoverned"]
    assert s["covered_governed"] == len(_EXO_SOURCES)     # all three certify
    # the relational pair: governed no worse ...
    assert s["dl_governed"] <= s["dl_ungoverned"]
    # ... and STRICTLY better under the dream flood (origin-blind mining lets the
    # dreams pollute the shared cluster, degrading ungoverned exo compression).
    assert s["dl_governed"] < s["dl_ungoverned"]
    # the arms reached DIFFERENT vocabularies -- the dreams changed the outcome.
    assert (s["governed"]["live_macros"], s["dl_governed"]) != \
        (s["ungoverned"]["live_macros"], s["dl_ungoverned"])


def test_no_dream_flood_ties(tmp_path):
    """With NO dream flood the arms tie: equal coverage AND equal reported DL
    (the honest tie the plan admits) -- the <= half of the relational pair."""
    _author, s = _run(tmp_path, dream_sources=[])
    assert s["covered_governed"] == s["covered_ungoverned"]
    assert s["dl_governed"] <= s["dl_ungoverned"]
    assert s["dl_governed"] == s["dl_ungoverned"]


def test_governed_per_use_certs_issue(tmp_path):
    """The governed arm's per-use translation certs actually issue (Lean-free),
    and none fail; the ungoverned arm records no per-use certs."""
    _author, s = _run(tmp_path)
    assert s["governed"]["translation_cert_count"] >= 1
    assert s["governed"]["per_use_cert_failures"] == 0
    assert s["ungoverned"]["translation_cert_count"] == 0
    assert s["ungoverned"]["per_use_cert_failures"] == 0


def test_dream_row_charged_to_neither(tmp_path):
    """The dream spend lands on its own ``arm="dream"`` row and is charged to
    neither arm's cost metric (⚠E3)."""
    _author, s = _run(tmp_path)
    dream = s["dream"]
    assert dream["arm"] == "dream"
    # dreams were authored (spend recorded) ...
    assert (dream["cumulative_ktokens_in"] + dream["cumulative_ktokens_out"]) > 0
    # ... but carry no exogenous coverage and no macros.
    assert dream["certified_exogenous_statements"] == 0
    assert dream["reported_exogenous_dl"] == 0.0
    # the arms' cumulative tokens count ONLY their own authoring, never dreams.
    exo_calls_tokens = (100 + 20) * len(_EXO_SOURCES) / 1000.0
    assert s["governed"]["cumulative_ktokens_in"] <= exo_calls_tokens + 1.0


def test_checkpoint_resume_no_reauthor(tmp_path):
    """Kill/re-run: a second run over the same state re-authors NOTHING."""
    author1, _s1 = _run(tmp_path)
    calls_after_first = author1.calls
    assert calls_after_first == (2 * len(_EXO_SOURCES) + len(_DREAM_SOURCES))
    # resume with a FRESH author instance over the same checkpoint file.
    author2 = _FakeAuthor()
    _a2, s2 = _run(tmp_path, author=author2)
    assert author2.calls == 0                       # every pair was resumed
    # the resumed run still reproduces the same relational verdict.
    assert s2["covered_governed"] == s2["covered_ungoverned"]
    assert s2["dl_governed"] < s2["dl_ungoverned"]


def test_fresh_flag_reauthors(tmp_path):
    """``--fresh`` ignores existing state and re-authors everything."""
    author1, _s1 = _run(tmp_path)
    author2 = _FakeAuthor()
    _a2, _s2 = _run(tmp_path, author=author2, fresh=True)
    assert author2.calls == author1.calls           # nothing skipped


def test_csv_schema_frozen(tmp_path):
    """The CSV header is exactly the frozen F-INT-4 column list, in order."""
    _author, s = _run(tmp_path)
    with open(s["csv"]) as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == bench.CSV_COLUMNS
    body = rows[1:]
    arms = {r[0] for r in body}
    assert arms == {"dream", "governed", "ungoverned"}
    # every data row has one cell per frozen column.
    assert all(len(r) == len(bench.CSV_COLUMNS) for r in body)


def test_cost_numerator_is_tokens_only(tmp_path):
    """The cost numerator is (ktokens_in + ktokens_out) / FH7-denominator --
    seconds are NEVER summed in (⚠E6).  Verified against the frozen columns."""
    _author, s = _run(tmp_path)
    g = s["governed"]
    denom = g["certified_exogenous_statements"]      # trivially_closed all false
    expected = round((g["cumulative_ktokens_in"]
                      + g["cumulative_ktokens_out"]) / denom, 6)
    assert g["cost_per_certified_statement"] == expected
    # Lean absent => the two variants coincide, seconds reported not divided.
    assert (g["cost_per_certified_statement"]
            == g["cost_per_certified_statement_inclusive"])
    assert g["lean_seconds_total"] == 0.0
    assert g["trivially_closed_count"] == 0


def test_plot_and_sidecar_written(tmp_path):
    """The two-curve plot and the pins sidecar are written; the sidecar carries
    the pins and the CSV stays pure rows."""
    _author, s = _run(tmp_path)
    assert s["plot"] is not None and os.path.exists(s["plot"])
    assert os.path.getsize(s["plot"]) > 0
    assert os.path.exists(s["meta"])
    meta = json.loads(open(s["meta"]).read())
    for pin in ("model_id", "prompt_scaffold_sha256", "arm_configs",
                "spend_cap_calls", "mathlib_commit", "lean_toolchain"):
        assert pin in meta
    # the deferred F5.2 fields are named, not silently omitted.
    assert set(bench.DEFERRED_F52_FIELDS) == set(
        meta["honesty_notes"]["deferred_f52_fields"])


def test_wave_engine_multiple_waves(tmp_path, monkeypatch):
    """The wave engine tiles sources into K-sized waves: with K forced small,
    the governed arm emits ceil(n/K) per-wave rows."""
    monkeypatch.setattr(bench, "WAVE_SIZE", 2)
    _author, s = _run(tmp_path)
    gov_rows = [r for r in s["rows"] if r["arm"] == "governed"]
    import math
    assert len(gov_rows) == math.ceil(len(_EXO_SOURCES) / 2)
    # waves are numbered 0..W-1 in order.
    assert [r["wave"] for r in gov_rows] == list(range(len(gov_rows)))


def test_checkpoint_records_frozen_fields(tmp_path):
    """Every checkpoint line carries exactly the F-INT-4 record fields."""
    _author, s = _run(tmp_path)
    expect = {"source_id", "arm", "wave", "table_hash", "reading_json",
              "tokens_in", "tokens_out", "certified", "stage"}
    with open(s["state"]) as fh:
        lines = [json.loads(x) for x in fh if x.strip()]
    assert lines
    for rec in lines:
        assert set(rec) == expect


# ============================================ LAT-A: concurrent-arm teeth
#: the only CSV column that is a wall-clock MEASUREMENT (time.monotonic of the
#: certify call) and thus varies run-to-run for reasons orthogonal to the arm
#: order -- masked out of the byte-determinism comparison below.
_TIMING_COLUMNS = {"smt_seconds"}


def _csv_accounting_bytes(path):
    """The CSV rendered to bytes with the wall-clock timing column(s) masked --
    i.e. exactly the deterministic accounting the arm order must not perturb."""
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    mask = {rows[0].index(c) for c in _TIMING_COLUMNS if c in rows[0]}
    return "\n".join(",".join("" if i in mask else cell
                              for i, cell in enumerate(r)) for r in rows)


def test_concurrent_matches_serial_bytes(tmp_path, monkeypatch):
    """The CONCURRENT-arm run (default) produces byte-IDENTICAL CSV accounting to
    the SERIAL fallback (``CGB_BENCH_SERIAL=1``) given the same authored readings
    -- the fixed dream/governed/ungoverned row order makes the artifact
    deterministic regardless of which arm thread finishes first.  Only the
    wall-clock ``smt_seconds`` measurement (nondeterministic between ANY two
    runs, serial or not) is masked; every accounting column must match to the
    byte."""
    monkeypatch.delenv("CGB_BENCH_SERIAL", raising=False)
    con_dir = tmp_path / "concurrent"
    _a1, s_con = _run(con_dir)

    monkeypatch.setenv("CGB_BENCH_SERIAL", "1")
    ser_dir = tmp_path / "serial"
    _a2, s_ser = _run(ser_dir)

    assert _csv_accounting_bytes(s_con["csv"]) == _csv_accounting_bytes(s_ser["csv"])
    # the masked column really is present (guard against a silent header drift).
    assert "smt_seconds" in bench.CSV_COLUMNS
    # sanity: the run actually exercised both arms and the relational verdict.
    assert s_con["dl_governed"] < s_con["dl_ungoverned"]


def test_concurrent_checkpoint_parses_cleanly(tmp_path, monkeypatch):
    """After a CONCURRENT run the JSONL checkpoint is intact: every line is
    valid JSON (the lock-atomic append never interleaves a partial line), and
    the full set of authored ``(source_id, arm)`` pairs is present."""
    monkeypatch.delenv("CGB_BENCH_SERIAL", raising=False)
    _author, s = _run(tmp_path)
    pairs = []
    with open(s["state"]) as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)                    # raises if any line is torn
            pairs.append((rec["source_id"], rec["arm"]))
    # every dream + per-arm pair authored exactly once, none torn/duplicated.
    expect = {(sid, "dream") for sid, _ in _DREAM_SOURCES}
    expect |= {(sid, "governed") for sid, _ in _EXO_SOURCES}
    expect |= {(sid, "ungoverned") for sid, _ in _EXO_SOURCES}
    assert set(pairs) == expect
    assert len(pairs) == len(expect)                 # no duplicate lines


def test_resume_after_one_arm_kill_reauthors_only_missing(tmp_path, monkeypatch):
    """Simulate a mid-run KILL of one arm: drop a subset of the ungoverned
    arm's checkpoint lines, then resume.  The resumed run re-authors NOTHING
    already checkpointed (dreams + governed + the surviving ungoverned pair)
    and re-spends only the dropped ungoverned pairs."""
    monkeypatch.delenv("CGB_BENCH_SERIAL", raising=False)
    author1, s1 = _run(tmp_path)
    assert author1.calls == (2 * len(_EXO_SOURCES) + len(_DREAM_SOURCES))

    # Emulate the ungoverned arm being killed after checkpointing only "e1":
    # rewrite the state file with the "e2"/"e3" ungoverned lines removed.
    dropped = {("e2", "ungoverned"), ("e3", "ungoverned")}
    kept = []
    with open(s1["state"]) as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)
            if (rec["source_id"], rec["arm"]) not in dropped:
                kept.append(raw)
    with open(s1["state"], "w") as fh:
        fh.write("\n".join(kept) + "\n")

    author2 = _FakeAuthor()
    _a2, s2 = _run(tmp_path, author=author2)
    # exactly the dropped pairs were re-authored -- nothing already present.
    assert author2.calls == len(dropped)
    assert {(sid, "ungoverned") for sid, _th in author2.seen} == dropped
    # no governed / dream / surviving-ungoverned source was re-authored.
    reauthored_ids = {sid for sid, _th in author2.seen}
    assert reauthored_ids == {"e2", "e3"}
    # and the resumed run still reproduces the relational verdict.
    assert s2["covered_governed"] == s2["covered_ungoverned"]
    assert s2["dl_governed"] < s2["dl_ungoverned"]

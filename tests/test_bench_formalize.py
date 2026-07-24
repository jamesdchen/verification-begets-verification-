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
        import threading
        self.calls = 0
        self.seen = []
        self._lock = threading.Lock()   # both arm threads share one instance;
        # the counter feeds asserted values, so the read-modify-write must be
        # atomic (reviewer note on the LAT-A merge).

    def __call__(self, source_id, source_text, macro_table, table_hash):
        with self._lock:
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


#: The frozen CSV header prefix as it stood BEFORE the WP-P1 append (captured
#: pre-edit).  ``prequential_counting_dl`` is appended after ALL of these, at the
#: END -- append-only (CSV_COLUMNS law), so downstream readers keyed on the old
#: columns are byte-stable.  Pinned here so the append can never silently reorder
#: or insert into the middle.
_PREEDIT_CSV_COLUMNS = [
    "arm", "wave", "certified_exogenous_statements",
    "cumulative_ktokens_in", "cumulative_ktokens_out", "prompt_bytes_mean",
    "live_macros", "retired_macros", "reported_exogenous_dl",
    "translation_cert_count", "per_use_cert_failures", "trivially_closed_count",
    "cost_per_certified_statement", "cost_per_certified_statement_inclusive",
    "lean_seconds_total", "smt_seconds", "order0_entropy_dl_est",
]


def test_csv_schema_frozen(tmp_path):
    """The CSV header is exactly the frozen column list, in order, with the WP-P1
    ``prequential_counting_dl`` APPENDED at the END (append-only)."""
    _author, s = _run(tmp_path)
    with open(s["csv"]) as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == bench.CSV_COLUMNS
    # append-only: the pre-edit columns are an exact prefix; the new column is
    # last (never inserted into the middle, never renamed to `prequential_dl`).
    assert bench.CSV_COLUMNS[:len(_PREEDIT_CSV_COLUMNS)] == _PREEDIT_CSV_COLUMNS
    assert bench.CSV_COLUMNS[len(_PREEDIT_CSV_COLUMNS):] == ["prequential_counting_dl"]
    assert bench.CSV_COLUMNS[-1] == "prequential_counting_dl"
    assert "prequential_dl" not in bench.CSV_COLUMNS   # -log p name stays reserved
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
    """Every checkpoint line carries exactly the F-INT-4 record fields PLUS the
    WP-P1 per-wave ``frozen_table`` bodies (persisted going forward, §11.1
    requirement 2)."""
    _author, s = _run(tmp_path)
    expect = {"source_id", "arm", "wave", "table_hash", "frozen_table",
              "reading_json", "tokens_in", "tokens_out", "certified", "stage"}
    with open(s["state"]) as fh:
        lines = [json.loads(x) for x in fh if x.strip()]
    assert lines
    for rec in lines:
        assert set(rec) == expect
        # the frozen table is the PRE-wave macro bodies, hashing to table_hash.
        assert isinstance(rec["frozen_table"], dict)
        assert bench._table_hash(rec["frozen_table"]) == rec["table_hash"]


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


# ================================ WP-P1: counting prequential DL (§11.1)
def _gov_rows(s):
    return [r for r in s["rows"] if r["arm"] == "governed"]


def _ung_rows(s):
    return [r for r in s["rows"] if r["arm"] == "ungoverned"]


def test_prequential_column_present_and_populated(tmp_path):
    """The new column exists on every arm row and is a non-negative DL value;
    the dream row (system-origin) carries 0 (no exogenous data)."""
    _author, s = _run(tmp_path)
    for r in _gov_rows(s) + _ung_rows(s):
        assert "prequential_counting_dl" in r
        assert float(r["prequential_counting_dl"]) >= 0.0
    # cumulative: non-decreasing across waves (readings only ever add cost).
    for rows in (_gov_rows(s), _ung_rows(s)):
        vals = [float(r["prequential_counting_dl"]) for r in rows]
        assert vals == sorted(vals)
    assert float(s["dream"]["prequential_counting_dl"]) == 0.0


def test_governed_hindsight_le_prequential_by_construction(tmp_path):
    """TOOTH 4a (governed, ASSERTED, by construction): the hindsight
    ``reported_exogenous_dl`` (post-mine table, includes macro model bits) is
    <= the counting ``prequential_counting_dl`` (pre-wave tables, data bits
    only) at EVERY governed wave.  Relational (E5), never an absolute constant."""
    _author, s = _run(tmp_path)
    gov = _gov_rows(s)
    assert gov
    for r in gov:
        assert float(r["reported_exogenous_dl"]) <= float(r["prequential_counting_dl"])


def test_ungoverned_relation_reported_not_asserted(tmp_path):
    """TOOTH 4b (ungoverned, REPORTED ONLY): the hindsight<=prequential relation
    is NOT asserted on the ungoverned arm -- a dream-witnessed macro can charge
    exogenous MODEL bits into reported_exogenous_dl with zero exogenous savings,
    so the relation may invert; the divergence IS the governance effect and is
    documented in the meta honesty block (asserted here), not gated in code."""
    _author, s = _run(tmp_path)
    # the honesty block explains WHY it is report-only (the governance effect).
    meta = json.loads(open(s["meta"]).read())
    note = meta["honesty_notes"]["prequential_counting_dl"]
    assert "REPORTED" in note and "NEVER asserted" in note
    assert "governance effect" in note
    # the column is still populated on the ungoverned arm (reported beside).
    for r in _ung_rows(s):
        assert float(r["prequential_counting_dl"]) >= 0.0


# -- TOOTH 4c: anti-vacuity -- a NEW >=2-wave fixture where mining admits
# MID-RUN (wave 1) so an early reading is priced under the pre-macro table in
# prequential but repriced cheaper in hindsight => STRICT prequential > hindsight
# on the governed arm.  This CANNOT be shown on the single-wave flood fixture
# (there all readings share the one empty pre-wave table), which is why §11.1
# requires a dedicated multi-wave plant.  A "vacuous" implementation that priced
# from the POST-mine table would fail this strict >.
def _filler_reading(theorem):
    """A structurally distinct single-conclusion reading that forms NO macro --
    it occupies a wave-0 slot so the coprime cluster lacks 2 witnesses until
    wave 1, forcing MID-RUN admission."""
    return {"theorem": theorem, "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "c", "force": "demand", "quote": theorem,
         "lf": {"kind": "conclusion",
                "pred": {"op": "prime", "args": [{"ref": "n"}]}}}]}


# wave 0 (K=2): one coprime witness + one filler  -> NO admission (1 witness);
# wave 1 (K=2): two more coprime witnesses         -> macro admitted MID-RUN.
_AV_SOURCES = [("a1", "coprime one"), ("a2", "filler"),
               ("a3", "coprime two"), ("a4", "coprime three")]
_AV_READINGS = {
    "a1": _cop_reading("cop_ab", "a", "b",
                       "d coprime to a and coprime to b", "coprime to a"),
    "a2": _filler_reading("filler_prime"),
    "a3": _cop_reading("cop_mn", "m", "n",
                       "d coprime to m and coprime to n", "coprime to m"),
    "a4": _cop_reading("cop_pq", "p", "q",
                       "d coprime to p and coprime to q", "coprime to p"),
}


class _AVAuthor:
    def __init__(self):
        import threading
        self.calls = 0
        self._lock = threading.Lock()

    def __call__(self, source_id, source_text, macro_table, table_hash):
        with self._lock:
            self.calls += 1
        r = _AV_READINGS.get(source_id)
        if r is None:
            return None
        return {"reading_json": json.dumps(r),
                "tokens_in": 100 + 10 * len(macro_table), "tokens_out": 20}


def test_anti_vacuity_multiwave_strict_governed(tmp_path, monkeypatch):
    """TOOTH 4c: with K forced to 2, the governed arm tiles the plant into two
    waves; the coprime macro is admitted MID-RUN (wave 1), so at the final wave
    prequential > hindsight STRICTLY (an early reading paid pre-macro in
    prequential and is repriced cheaper in hindsight)."""
    monkeypatch.setattr(bench, "WAVE_SIZE", 2)
    s = bench.run_bench(author=_AVAuthor(), sources=list(_AV_SOURCES),
                        dream_sources=[], out_dir=str(tmp_path), fresh=True)
    gov = _gov_rows(s)
    import math
    assert len(gov) == math.ceil(len(_AV_SOURCES) / 2) == 2   # genuinely >=2 waves
    # a macro was admitted (mid-run), so the arm is not vacuous.
    assert gov[-1]["live_macros"] >= 1
    # 4a still holds per wave ...
    for r in gov:
        assert float(r["reported_exogenous_dl"]) <= float(r["prequential_counting_dl"])
    # ... and the anti-vacuity STRICT inequality holds at the final wave.
    assert float(gov[-1]["reported_exogenous_dl"]) < float(gov[-1]["prequential_counting_dl"])


def test_single_wave_flood_prequential_ties_arms(tmp_path):
    """Provenance note for 4c: on the SINGLE-wave flood fixture the two arms'
    prequential TIES (both price the exogenous readings under the same empty
    pre-wave table), so it CANNOT witness the origin-blind separation -- exactly
    why §11.1 forbids reusing it for the strict tooth."""
    _author, s = _run(tmp_path)   # default fixture is single-wave (K=8)
    assert len(_gov_rows(s)) == 1
    assert s["prequential_governed"] == s["prequential_ungoverned"]


def test_frozen_tables_sidecar_written_and_hashes(tmp_path, monkeypatch):
    """The per-wave frozen-table sidecar (§11.1 requirement 2) is written; each
    wave records the PRE-wave table BODIES and their prequential/hindsight DL,
    and every recorded table_hash equals the hash of the recorded bodies."""
    monkeypatch.setattr(bench, "WAVE_SIZE", 2)
    s = bench.run_bench(author=_AVAuthor(), sources=list(_AV_SOURCES),
                        dream_sources=[], out_dir=str(tmp_path), fresh=True)
    side = json.loads(open(s["frozen_tables"]).read())
    for arm in ("governed", "ungoverned"):
        waves = side["arms"][arm]
        assert waves
        for w in waves:
            assert set(w) >= {"wave", "table_hash", "frozen_table",
                              "prequential_counting_dl", "reported_exogenous_dl"}
            assert bench._table_hash(w["frozen_table"]) == w["table_hash"]
        # wave 0's frozen table is empty (mining has not run yet).
        assert waves[0]["frozen_table"] == {}


def test_regenerated_csv_old_columns_byte_identical(tmp_path):
    """§11.1 requirement 3: regenerating the committed CSV via checkpoint RESUME
    (no re-authoring) leaves every PRE-WP-P1 column byte-identical to the golden
    committed before the append, and all token columns stay 0.  Pinned against a
    git-tracked snapshot of the pre-append CSV, so the pin cannot go vacuous.

    FROZEN-vs-LIVE (WP-SRC promotion + WP-AUTH continuation): the committed
    checkpoint now records 51 sources (the frozen 40 + the 11 promoted, authored
    as continuation waves 5-6 by WP-AUTH).  The GOLDEN this pins is the FROZEN
    40-source pre-append CSV -- a git-history artifact that is NEVER rewritten --
    so we must replay ONLY the 40 frozen sources (stems 01..40; the 11 promoted
    are stems 41..51).  Deriving the frozen set from the checkpoint's own
    source_ids would now (correctly) return all 51, so the frozen restriction is
    pinned INDEPENDENTLY of the checkpoint by the numeric-prefix partition the
    promotion established.  A raising author proves resume re-authors nothing
    (every frozen key is already present in the checkpoint copy)."""
    import shutil
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    golden = os.path.join(root, "tests", "golden",
                          "formalize_governed.pre_prequential.csv")
    state = os.path.join(root, "results", "formalize_bench_state.jsonl")
    if not (os.path.exists(golden) and os.path.exists(state)):
        pytest.skip("committed golden / state artifacts absent")
    # resume over a COPY of the committed checkpoint; a raising author proves
    # nothing is re-authored (every key already present).
    shutil.copy(state, tmp_path / "formalize_bench_state.jsonl")

    def _no_author(*a, **k):
        raise AssertionError("resume must not re-author any reading")

    # The FROZEN 40 are stems 01..40; the 11 WP-SRC-promoted sources are 41..51.
    # This numeric-prefix partition (a git-history invariant of the promotion) is
    # what keeps the frozen golden byte-identical INDEPENDENTLY of how far the
    # live checkpoint has since grown.
    def _is_frozen_stem(sid):
        head = sid.split("_", 1)[0]
        return head.isdigit() and int(head) <= 40
    live_corpus = bench._corpus_sources()
    # 51 post-promotion + the 4 S4a' exists-class sources (63..66, PLAN_REFLECT)
    # + the 4 C2 census-sourced sources (67..70, PLAN_FRAGMENT).  Size lives
    # in the corpus-era registration (one re-baseline point).
    _reg = json.load(open(os.path.join(root, "specs", "mathsources",
                                       "registration.json")))
    assert len(live_corpus) == _reg["n_top_level_sources"]
    frozen_corpus = [(sid, txt) for sid, txt in live_corpus if _is_frozen_stem(sid)]
    frozen_dreams = bench._dream_sources()          # all 8 dreams were in the frozen run
    assert len(frozen_corpus) == 40, "frozen committed run is 40 top-level sources"

    s = bench.run_bench(author=_no_author, sources=frozen_corpus,
                        dream_sources=frozen_dreams,
                        out_dir=str(tmp_path), fresh=False)
    with open(golden) as fh:
        old = list(csv.reader(fh))
    with open(s["csv"]) as fh:
        new = list(csv.reader(fh))
    old_cols = old[0]
    new_cols = new[0]
    assert new_cols[:len(old_cols)] == old_cols            # old header prefix
    assert new_cols[-1] == "prequential_counting_dl"       # appended at END
    assert len(old) == len(new)                            # same rows
    # every OLD column, every row, byte-identical -- EXCEPT prompt_bytes_mean,
    # which is derived from the LIVE prompt renderer at replay time, not from
    # the checkpoint: it legitimately grows whenever the fragment grammar
    # grows (a PLAN_FRAGMENT purchase; first mover: the P1 bigsum/bigprod
    # lines in _PRED_AST_NOTE).  Exempting it keeps this pin about what it
    # was built to prove (resume re-authors nothing; every checkpoint-derived
    # accounting column is byte-stable) without freezing the grammar by side
    # effect.
    _LIVE_RENDERED = {"prompt_bytes_mean"}
    old_idx = {c: i for i, c in enumerate(old_cols)}
    for orow, nrow in zip(old[1:], new[1:]):
        for c, i in old_idx.items():
            if c in _LIVE_RENDERED:
                continue
            assert orow[i] == nrow[new_cols.index(c)], f"drift in {c}"
    # token columns are all 0 on this unmetered run.
    for nrow in new[1:]:
        assert nrow[new_cols.index("cumulative_ktokens_in")] in ("0.0", "0")
        assert nrow[new_cols.index("cumulative_ktokens_out")] in ("0.0", "0")


#: The committed LIVE CSV's smt_seconds is a wall-clock MEASUREMENT (nonzero on
#: the continuation waves 5-6, where the new sources are actually re-certified);
#: masked out of the frozen-prefix byte-comparison below, exactly as the
#: concurrent-vs-serial determinism tooth masks it.
def test_live_csv_extends_frozen_prefix_with_new_waves():
    """WP-AUTH pin (the checkpoint holds 51): the COMMITTED live CSV
    (results/formalize_governed.csv) EXTENDS the frozen golden -- its 40-source
    prefix rows (waves 0..4, both arms) are byte-identical to the git-history
    golden on every pre-append column (smt_seconds masked -- a wall-clock
    measurement), and the new continuation rows (waves 5..6) carry the
    relational F5.2 verdict: equal exogenous coverage across the arms,
    monotone non-decreasing certified coverage, and governed reported DL never
    exceeding ungoverned."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    golden = os.path.join(root, "tests", "golden",
                          "formalize_governed.pre_prequential.csv")
    live = os.path.join(root, "results", "formalize_governed.csv")
    if not (os.path.exists(golden) and os.path.exists(live)):
        pytest.skip("committed golden / live CSV absent")
    with open(golden) as fh:
        old = list(csv.reader(fh))
    with open(live) as fh:
        new = list(csv.reader(fh))
    old_cols, new_cols = old[0], new[0]
    # the golden's columns are an exact prefix of the live header (append-only).
    assert new_cols[:len(old_cols)] == old_cols
    assert new_cols[-1] == "prequential_counting_dl"
    old_idx = {c: i for i, c in enumerate(old_cols)}
    live_by_key = {(r[new_cols.index("arm")], r[new_cols.index("wave")]): r
                   for r in new[1:]}
    # smt_seconds: wall-clock, not accounting.  prompt_bytes_mean: live-
    # renderer derived, grows with fragment purchases (see the exemption in
    # test_regenerated_csv_old_columns_byte_identical).
    _MASK = {"smt_seconds", "prompt_bytes_mean"}
    # every FROZEN-prefix golden row (dream + waves 0..4) must appear byte-
    # identical in the live CSV on every pre-append accounting column.
    for orow in old[1:]:
        key = (orow[old_idx["arm"]], orow[old_idx["wave"]])
        nrow = live_by_key.get(key)
        assert nrow is not None, f"frozen row {key} missing from live CSV"
        for c, i in old_idx.items():
            if c in _MASK:
                continue
            assert orow[i] == nrow[new_cols.index(c)], f"drift in frozen {key} col {c}"
    # the live CSV adds the continuation waves 5-6 (WP-AUTH) and 7 (the S4a'
    # exists-class sources 63-66 + the C2 census-sourced 67-70) for BOTH arms.
    gov = sorted((int(r[new_cols.index("wave")]) for r in new[1:]
                  if r[new_cols.index("arm")] == "governed"))
    ung = sorted((int(r[new_cols.index("wave")]) for r in new[1:]
                  if r[new_cols.index("arm")] == "ungoverned"))
    _reg = json.load(open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "specs", "mathsources", "registration.json")))
    assert gov == _reg["waves"] and ung == _reg["waves"]

    def _final(arm, col):
        rows = [r for r in new[1:] if r[new_cols.index("arm")] == arm]
        rows.sort(key=lambda r: int(r[new_cols.index("wave")]))
        return rows[-1][new_cols.index(col)]

    def _cov_series(arm):
        rows = [r for r in new[1:] if r[new_cols.index("arm")] == arm]
        rows.sort(key=lambda r: int(r[new_cols.index("wave")]))
        return [int(r[new_cols.index("certified_exogenous_statements")]) for r in rows]

    # equal exogenous coverage across the arms (F5.2 same-inputs discipline) ...
    assert _final("governed", "certified_exogenous_statements") == \
        _final("ungoverned", "certified_exogenous_statements")
    # ... certified coverage is monotone non-decreasing across waves ...
    for arm in ("governed", "ungoverned"):
        cov = _cov_series(arm)
        assert cov == sorted(cov)
    # ... and governed reported DL never exceeds ungoverned at the final wave.
    assert float(_final("governed", "reported_exogenous_dl")) <= \
        float(_final("ungoverned", "reported_exogenous_dl"))
    # token columns stay 0 on the whole unmetered live run.
    for r in new[1:]:
        assert r[new_cols.index("cumulative_ktokens_in")] in ("0.0", "0")
        assert r[new_cols.index("cumulative_ktokens_out")] in ("0.0", "0")

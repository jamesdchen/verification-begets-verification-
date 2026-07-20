"""B2 (PLAN_LEAN_IMPORT.md §8.2) teeth: INLINE VOCABULARY MINING in the
Mathlib import driver -- compression co-evolving with the corpus DURING
import (the user's ruling), LLM-free (fake authors, canned readings + token
counts, no network).

Covered:
  * a GOVERNED wave over readings with deliberate shared structure mines,
    prices and admits at least one macro with dl_after < dl_before, appends
    kind:"admission" ledger rows, and persists the append-only
    import_macros.json admission records (word, body, dl_before, dl_after,
    witness_decl_names, encoding_version);
  * mining is CPU: admission rows record ZERO ktokens and never contaminate
    the ledger spend decrement (item rows only);
  * an UNGOVERNED wave admits NOTHING and its ledger says so (mining off,
    DL fields null, empty macro table on every author call);
  * the LIVE macro table round-trips into the NEXT wave's author calls (the
    E1 seam: the author receives the non-empty table);
  * intra-wave mining (every MINE_EVERY_K_AUTHORED authored rows) grows the
    table MID-wave, so later prompts in the same wave see earlier vocabulary;
  * mining-error CONTAINMENT: an injected raiser records a first-class
    kind:"mining-error" ledger row and the wave still completes -- authored
    rows and persisted readings are never lost;
  * resumability is unaffected: a re-run re-authors nothing and re-admits
    nothing (the persisted table already carries the vocabulary).

NOTE (explicit, mirrored from the driver): every authored import reading is
EXOGENOUS -- the corpus is real Mathlib statements, the driver has no dream
lane -- so the bench's >= 2-exogenous-witness discipline is applied for
parity and satisfied by construction.
"""
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop import import_driver as drv

_HERE = pathlib.Path(__file__).resolve().parent


# ------------------------------------------------------------ canned reading
_PP = "d coprime to a and coprime to b -> d coprime to a"
_CQ = "d coprime to a and coprime to b"
_CONCL = "d coprime to a"


def _cop(d, x):
    return {"kind": "hypothesis",
            "pred": {"op": "coprime", "args": [{"ref": d}, {"ref": x}]}}


def _cop_reading(theorem, x, y):
    """The coprime idiom (enum_only => certifies without cvc5); the shared
    od/ox/oy/h1/h2 presupposition window is the DELIBERATE recurring
    structure the miner must find across readings."""
    return {"theorem": theorem, "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "od", "force": "presupposition", "quote": _CQ,
         "lf": {"kind": "object", "name": "d", "type": "Nat"}},
        {"id": "ox", "force": "presupposition", "quote": _CQ,
         "lf": {"kind": "object", "name": x, "type": "Nat"}},
        {"id": "oy", "force": "presupposition", "quote": _CQ,
         "lf": {"kind": "object", "name": y, "type": "Nat"}},
        {"id": "h1", "force": "presupposition", "quote": _CQ,
         "lf": _cop("d", x)},
        {"id": "h2", "force": "presupposition", "quote": _CQ,
         "lf": _cop("d", y)},
        {"id": "c", "force": "demand", "quote": _CONCL,
         "lf": {"kind": "conclusion",
                "pred": {"op": "coprime",
                         "args": [{"ref": "d"}, {"ref": x}]}}}]}


class _SharedStructureAuthor:
    """Deterministic fake author: every decl gets a coprime reading with the
    same recurring statement window (variable names vary per decl so the
    anti-unifier has parameters to bind).  Records the macro_table received
    on EVERY call -- the round-trip assertion surface."""

    _VARS = [("a", "b"), ("m", "n"), ("p", "q"), ("u", "v"), ("s", "t"),
             ("x", "y"), ("j", "k"), ("f", "g")]

    def __init__(self, tokens_in=1000, tokens_out=200):
        self.calls = 0
        self.tables = []            # macro_table per call, in call order
        self._tin, self._tout = tokens_in, tokens_out

    def __call__(self, decl_name, statement_pp, macro_table,
                 operator_registry):
        self.tables.append(dict(macro_table))
        x, y = self._VARS[self.calls % len(self._VARS)]
        self.calls += 1
        return {"reading_json": json.dumps(
                    _cop_reading("coprime_left_" + x + y, x, y)),
                "tokens_in": self._tin, "tokens_out": self._tout}


_GRANT = {"mode": "weekly-quota-exhaustion", "granted_ktokens": None,
          "per_wave_cap_ktokens": 2000, "arm": "ab-pilot-then-cheaper",
          "granted_by": "test", "granted_on": "2026-07-17",
          "expires": "2099-01-01"}
_TODAY = "2026-07-17"


def _queue(tmp_path, n, name="q", start=0):
    rows = [{"decl_name": "Syn.decl_%02d" % i, "module": "Syn",
             "statement_pp": _PP, "statement_hash": "sh-%02d" % i,
             "status": "pending"} for i in range(start, start + n)]
    q = tmp_path / (name + ".jsonl")
    q.write_text("\n".join(common.canonical_json(r) for r in rows) + "\n",
                 encoding="utf-8")
    return q


def _extend_queue(q, n, start):
    rows = drv.load_queue(q) + [
        {"decl_name": "Syn.decl_%02d" % i, "module": "Syn",
         "statement_pp": _PP, "statement_hash": "sh-%02d" % i,
         "status": "pending"} for i in range(start, start + n)]
    drv.write_queue(q, rows)


def _run(tmp_path, queue_path, *, arm, author, budget=100.0, fresh=False,
         **kw):
    return drv.run_wave(
        budget_ktokens=budget, arm=arm, author=author,
        queue_path=queue_path,
        ledger_path=tmp_path / "import_ledger.jsonl",
        readings_dir=tmp_path / "readings",
        state_path=tmp_path / "import_state.jsonl",
        macros_path=tmp_path / "import_macros.json",
        fresh=fresh, grant=_GRANT, today=_TODAY, **kw)


def _ledger(tmp_path):
    return drv.load_ledger(tmp_path / "import_ledger.jsonl")


# ============================================== governed: mine/price/admit ==
def test_governed_wave_mines_admits_and_persists(tmp_path):
    """A governed wave over 4 shared-structure readings admits >= 1 macro
    with STRICT DL descent, appends kind:"admission" ledger rows (zero-ktok),
    stamps the wave row with the B2 DL instrumentation, and persists the
    append-only import_macros.json admission records."""
    q = _queue(tmp_path, 4)
    author = _SharedStructureAuthor()
    s = _run(tmp_path, q, arm="governed", author=author)
    assert s["status"] == "completed"
    assert s["totals"]["authored"] == 4

    # -- wave-row DL instrumentation (the compounding instrument) -------------
    wave = s["wave_row"]
    assert wave["macros_admitted_this_wave"] >= 1
    assert wave["macro_table_size"] >= 1
    assert wave["corpus_dl_before"] is not None
    assert wave["corpus_dl_after"] is not None
    assert wave["corpus_dl_after"] < wave["corpus_dl_before"]   # strict descent
    assert wave["mining"]["enabled"] is True
    assert wave["mining"]["corpus_readings"] == 4
    assert wave["mining"]["mining_errors"] == 0
    assert wave["mining"]["ktokens"] == 0.0        # CPU, recorded zero

    # -- kind:"admission" ledger rows ----------------------------------------
    rows = _ledger(tmp_path)
    adm = [r for r in rows if r["kind"] == "admission"]
    assert len(adm) == wave["macros_admitted_this_wave"]
    for r in adm:
        assert r["dl_after"] < r["dl_before"]      # strict DL descent
        assert r["uses"] >= 2                      # >= 2 exogenous witnesses
        assert len(r["witness_decl_names"]) >= 2
        assert set(r["witness_decl_names"]) <= \
            {"Syn.decl_%02d" % i for i in range(4)}
        assert r["encoding_version"] == drv.READING_ENCODING_VERSION
        assert r["word"] and isinstance(r["body"], list)
        assert r["arm"] == "governed" and r["wave_id"] == 0
        # mining is CPU: zero-ktok RECORDED, never estimated.
        assert r["ktokens_in"] == 0.0 and r["ktokens_out"] == 0.0
    # admission rows never contaminate the spend decrement (item rows only).
    assert drv.ledger_spent_ktokens(rows) == pytest.approx(4 * 1.2)

    # -- the committed-artifact shape ----------------------------------------
    mp = tmp_path / "import_macros.json"
    assert mp.exists()
    recs = drv.load_import_macros(mp)
    assert [r["word"] for r in recs] == [r["word"] for r in adm]
    for rec in recs:
        for field in ("word", "body", "dl_before", "dl_after",
                      "witness_decl_names", "encoding_version"):
            assert field in rec
    # the LIVE table rebuilds from the records.
    table = drv.load_macro_table(mp)
    assert set(table) == {r["word"] for r in recs}
    assert all(m["body"] for m in table.values())
    # deterministic serialization: canonical JSON, byte-stable rewrite.
    before = mp.read_bytes()
    drv._write_import_macros(mp, recs)
    assert mp.read_bytes() == before


def test_governed_second_wave_table_at_wave_start_is_baseline(tmp_path):
    """Wave 2 loads the wave-1 table: its corpus_dl_before is priced WITH the
    already-admitted vocabulary (the trajectory is cross-wave, not reset)."""
    q = _queue(tmp_path, 3)
    s1 = _run(tmp_path, q, arm="governed", author=_SharedStructureAuthor())
    assert s1["wave_row"]["macros_admitted_this_wave"] >= 1
    dl_after_1 = s1["wave_row"]["corpus_dl_after"]

    _extend_queue(q, 2, start=3)
    s2 = _run(tmp_path, q, arm="governed", author=_SharedStructureAuthor(),
              fresh=True)
    w2 = s2["wave_row"]
    assert w2["wave_id"] == 1
    # baseline includes wave-1 vocabulary: before-wave-2 DL over the grown
    # corpus is already compressed relative to a macro-free recode.
    from buildloop import mdl_macros
    corpus = drv.load_authored_readings(tmp_path / "readings")
    assert len(corpus) == 5
    naked = mdl_macros.corpus_dl(corpus, {})["total"]
    assert w2["corpus_dl_before"] < naked
    assert w2["corpus_dl_after"] <= w2["corpus_dl_before"]
    assert w2["macro_table_size"] >= s1["wave_row"]["macro_table_size"]
    assert dl_after_1 is not None


# ========================================== ungoverned: mining OFF, truthful ==
def test_ungoverned_wave_admits_nothing_and_ledger_says_so(tmp_path):
    """The ungoverned arm's mining is OFF: no admission rows, no macros file,
    null DL fields, zero table -- and every author call gets an EMPTY table."""
    q = _queue(tmp_path, 4)
    author = _SharedStructureAuthor()
    s = _run(tmp_path, q, arm="ungoverned", author=author)
    assert s["status"] == "completed"
    assert s["totals"]["authored"] == 4

    wave = s["wave_row"]
    assert wave["macros_admitted_this_wave"] == 0
    assert wave["macro_table_size"] == 0
    assert wave["corpus_dl_before"] is None
    assert wave["corpus_dl_after"] is None
    assert wave["mining"]["enabled"] is False
    assert wave["arm_config"]["mining"].startswith("off")

    rows = _ledger(tmp_path)
    assert [r["kind"] for r in rows] == ["item"] * 4 + ["wave"]
    assert not (tmp_path / "import_macros.json").exists()
    assert author.tables == [{}] * 4               # empty table, every call

    # ARM_CONFIGS records the REAL arm semantics truthfully.
    assert "inline" in drv.ARM_CONFIGS["governed"]["mining"]
    assert drv.ARM_CONFIGS["ungoverned"]["mining"].startswith("off")


# ================================================= the E1 seam round-trip ==
def test_macro_table_round_trips_into_next_wave_author(tmp_path):
    """Vocabulary admitted in wave 1 reaches wave 2's author on EVERY call:
    the live table is loaded from import_macros.json at wave start and passed
    through the author's macro_table parameter (the E1 seam)."""
    q = _queue(tmp_path, 3)
    s1 = _run(tmp_path, q, arm="governed", author=_SharedStructureAuthor())
    admitted = {r["word"] for r in s1["macros_admitted"]}
    assert admitted                                 # wave 1 minted vocabulary

    _extend_queue(q, 2, start=3)
    author2 = _SharedStructureAuthor()
    s2 = _run(tmp_path, q, arm="governed", author=author2, fresh=True)
    assert s2["totals"]["items"] == 2               # only the new decls
    assert len(author2.tables) == 2
    for table in author2.tables:                    # NON-EMPTY on every call
        assert table
        assert admitted <= set(table)
        for word in admitted:
            assert table[word]["body"]              # full macro defs, not stubs


def test_intra_wave_mining_grows_table_mid_wave(tmp_path, monkeypatch):
    """With MINE_EVERY_K_AUTHORED=2, the 5-decl wave mines after the 2nd and
    4th authored rows, so LATER author calls in the SAME wave already receive
    the admitted vocabulary -- co-evolution within the wave, and the intra-
    wave admission rows are stamped stage:"intra-wave"."""
    monkeypatch.setattr(drv, "MINE_EVERY_K_AUTHORED", 2)
    q = _queue(tmp_path, 5)
    author = _SharedStructureAuthor()
    s = _run(tmp_path, q, arm="governed", author=author)
    assert s["totals"]["authored"] == 5
    assert author.tables[0] == {} and author.tables[1] == {}
    assert author.tables[2]                        # grown after 2 authored
    adm = [r for r in _ledger(tmp_path) if r["kind"] == "admission"]
    assert any(r["stage"] == "intra-wave" for r in adm)
    assert s["wave_row"]["macros_admitted_this_wave"] == len(adm)


# ==================================================== failure containment ==
def test_mining_error_never_loses_authored_work(tmp_path, monkeypatch):
    """An exception inside the mining stage is CONTAINED: the wave completes,
    every authored item row and persisted reading survives, and the failure
    is a first-class kind:"mining-error" ledger row -- never a crash."""
    def _boom(*a, **kw):
        raise RuntimeError("injected mining failure")
    monkeypatch.setattr(drv, "run_import_mining", _boom)

    q = _queue(tmp_path, 3)
    s = _run(tmp_path, q, arm="governed", author=_SharedStructureAuthor())
    assert s["status"] == "completed"              # never raised
    assert s["halt_reason"] == "frontier-empty"
    assert s["totals"]["authored"] == 3

    rows = _ledger(tmp_path)
    kinds = [r["kind"] for r in rows]
    assert kinds.count("item") == 3                # authored work intact
    assert kinds[-1] == "wave"
    errs = [r for r in rows if r["kind"] == "mining-error"]
    assert len(errs) == 1
    assert errs[0]["stage"] == "wave-end"
    assert "RuntimeError" in errs[0]["error"]
    assert "injected mining failure" in errs[0]["error"]
    assert errs[0]["ktokens_in"] == 0.0 and errs[0]["ktokens_out"] == 0.0
    # persisted readings are on disk BEFORE mining ran.
    assert len(list((tmp_path / "readings").glob("*.json"))) == 3
    # wave row still completes, with honest (null) DL fields + error count.
    wave = rows[-1]
    assert wave["corpus_dl_before"] is None
    assert wave["macros_admitted_this_wave"] == 0
    assert wave["mining"]["enabled"] is True
    assert wave["mining"]["mining_errors"] == 1


# ========================================================== resumability ==
def test_resume_reauthors_nothing_and_readmits_nothing(tmp_path):
    """A re-run against the same checkpoint re-authors NOTHING and the
    mining stage re-admits NOTHING (the persisted table already carries the
    vocabulary): admission records and ledger admission rows do not grow."""
    q = _queue(tmp_path, 4)
    s1 = _run(tmp_path, q, arm="governed", author=_SharedStructureAuthor())
    n_adm = len([r for r in _ledger(tmp_path) if r["kind"] == "admission"])
    assert n_adm >= 1
    recs_before = drv.load_import_macros(tmp_path / "import_macros.json")

    # crash window: queue statuses lost, checkpoint intact.
    rows = drv.load_queue(q)
    for r in rows:
        r["status"] = "pending"
    drv.write_queue(q, rows)

    author2 = _SharedStructureAuthor()
    s2 = _run(tmp_path, q, arm="governed", author=author2)
    assert author2.calls == 0                      # nothing re-authored
    assert s2["totals"]["items"] == 0
    assert s2["wave_row"]["macros_admitted_this_wave"] == 0
    # the table is stable: same records, no duplicate admissions anywhere.
    assert drv.load_import_macros(tmp_path / "import_macros.json") == \
        recs_before
    adm = [r for r in _ledger(tmp_path) if r["kind"] == "admission"]
    assert len(adm) == n_adm
    # wave 2's DL instrumentation still reports the (unchanged) trajectory
    # point over the accumulated corpus.
    assert s2["wave_row"]["corpus_dl_before"] == \
        s2["wave_row"]["corpus_dl_after"] == s1["wave_row"]["corpus_dl_after"]
    assert s2["wave_row"]["macro_table_size"] == \
        s1["wave_row"]["macro_table_size"]

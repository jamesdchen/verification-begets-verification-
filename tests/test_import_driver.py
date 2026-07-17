"""WP-LI1 (PLAN_LEAN_IMPORT.md §3/§4/§5/§6) teeth: the budget-bounded Mathlib
import driver, exercised END-TO-END with a FAKE TRANSPORT (canned readings +
canned token counts; LLM-free -- no ``call_llm`` on any path here, no network).

The fake transport mirrors ``tests/test_bench_metered.py``'s: a deterministic
callable with the driver's author signature ``(decl_name, statement_pp,
macro_table, operator_registry)`` replaying a canned reading and canned
``tokens_in``/``tokens_out`` per declaration, so the whole metering / breaker /
ledger path is driven without a model.  Every binding WP-LI1 requirement has a
tooth:

  * budget stop measured ONLY from returned usage metadata (F1.2 / E6);
  * both registered breakers (P-LI1-REFUSAL, P-LI1-COST) on synthetic
    histories -- fired verdicts RECORDED, never raised;
  * grant refusal paths (missing / expired / no-expiry / fixed-exhausted) and
    the bench_metered spend interlock (no --confirm-spend => skip, exit 0);
  * quota / rate-limit CLI errors are a GRACEFUL recorded wave halt
    (grant mode weekly-quota-exhaustion, RULED 2026-07-17), never a crash;
  * ledger append-only round-trip (a later wave strictly EXTENDS the bytes);
  * fragment-miss binning: both the author-declared structured miss and the
    gate-level FragmentMiss (missing_kind_guess) feed the WP-LI4 histogram;
  * resumability (re-run with the same checkpoint re-authors NOTHING);
  * READING_ENCODING_VERSION stamped on every item row and persisted reading
    (T-LI-ENC scaffolding, plan §2.5).

The fixture queue is ``tests/fixtures_import_queue.jsonl`` (WP-LI0 schema);
tests copy it into tmp_path -- the committed fixture is never mutated.  The
coprime idiom certifies through the Lean-free ENUMERATION channel (coprime is
enum_only), so no cvc5/z3 is needed; the kernel statement-cert defers honestly
in a Lean-absent container, which is exactly the Phase-A contract.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop import import_driver as drv

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent
_FIXTURE_QUEUE = _HERE / "fixtures_import_queue.jsonl"


# ------------------------------------------------------------ canned readings
def _cop(d, x):
    return {"kind": "hypothesis",
            "pred": {"op": "coprime", "args": [{"ref": d}, {"ref": x}]}}


def _cop_reading(theorem, x, y, cq, concl_quote):
    """The coprime idiom (enum_only => certifies without cvc5).  Quotes are
    verbatim substrings of the fixture row's statement_pp (groundedness)."""
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


# A reading whose `operator` statement names a word OUTSIDE MATH_OPERATORS:
# the math-reading-gate raises FragmentMiss with missing_kind_guess
# "operator:prime" -- the GATE-level miss path (vs the author-DECLARED one).
_GATE_MISS_READING = {"theorem": "prime_dvd_of_dvd_mul", "statements": [
    {"id": "op1", "force": "presupposition", "quote": "p prime",
     "lf": {"kind": "operator", "word": "prime", "carrier": "Nat"}},
    {"id": "c", "force": "demand", "quote": "p prime",
     "lf": {"kind": "conclusion", "pred": {"op": "even", "args": [{"lit": 2}]}}}]}

_CANNED = {
    "Nat.Coprime.left_of_pair": _cop_reading(
        "coprime_left_ab", "a", "b",
        "d coprime to a and coprime to b", "d coprime to a"),
    "Nat.Coprime.left_of_pair'": _cop_reading(
        "coprime_left_mn", "m", "n",
        "d coprime to m and coprime to n", "d coprime to m"),
    # the author-DECLARED structured miss (the import prompt's rule).
    "Real.add_comm_declared_miss": {"fragment_miss": {"missing":
                                                      ["carrier:Real"]}},
    "Nat.Prime.gate_level_miss": _GATE_MISS_READING,
}


class _FakeTransport:
    """Deterministic LLM-free author with the driver's signature.  ``fail``
    decls return None (author failure -> refused); after ``quota_after`` calls
    every further call raises QuotaExhausted (the CLI quota signal); unknown
    decls (synthetic queues) get a fresh coprime reading built from their
    statement_pp so they certify."""

    def __init__(self, fail=(), tokens_in=1000, tokens_out=200,
                 quota_after=None, garbage=False):
        self.calls = 0
        self.seen = []
        self.fail = set(fail)
        self._tin = tokens_in
        self._tout = tokens_out
        self.quota_after = quota_after
        self.garbage = garbage

    def __call__(self, decl_name, statement_pp, macro_table, operator_registry):
        if self.quota_after is not None and self.calls >= self.quota_after:
            raise drv.QuotaExhausted("claude CLI rc=1: 429 rate limit reached")
        self.calls += 1
        self.seen.append(decl_name)
        if self.garbage:                           # bills tokens, never certifies
            return {"reading_json": json.dumps({"theorem": "t",
                                                "statements": []}),
                    "tokens_in": self._tin, "tokens_out": self._tout}
        if decl_name in self.fail:
            return None
        reading = _CANNED.get(decl_name)
        if reading is None:                        # synthetic good decl
            reading = _cop_reading("coprime_left_ab", "a", "b",
                                   "d coprime to a and coprime to b",
                                   "d coprime to a")
        return {"reading_json": json.dumps(reading),
                "tokens_in": self._tin, "tokens_out": self._tout}


# ------------------------------------------------------------------- helpers
_GRANT = {"mode": "weekly-quota-exhaustion", "granted_ktokens": None,
          "per_wave_cap_ktokens": 2000, "arm": "ab-pilot-then-cheaper",
          "granted_by": "test", "granted_on": "2026-07-17",
          "expires": "2099-01-01"}
_TODAY = "2026-07-17"


def _fixture_queue(tmp_path):
    q = tmp_path / "queue.jsonl"
    shutil.copyfile(_FIXTURE_QUEUE, q)
    return q


def _synthetic_queue(tmp_path, n, name="syn"):
    """n GOOD pending decls sharing the coprime statement_pp."""
    rows = [{"decl_name": "Syn.decl_%02d" % i, "module": "Syn",
             "statement_pp": "d coprime to a and coprime to b -> d coprime to a",
             "statement_hash": "sh-%02d" % i, "status": "pending"}
            for i in range(n)]
    q = tmp_path / (name + ".jsonl")
    q.write_text("\n".join(common.canonical_json(r) for r in rows) + "\n",
                 encoding="utf-8")
    return q


def _run(tmp_path, queue_path, *, budget=100.0, author=None, arm="ungoverned",
         grant=None, fresh=False, **kw):
    return drv.run_wave(
        budget_ktokens=budget, arm=arm,
        author=author if author is not None else _FakeTransport(),
        queue_path=queue_path,
        ledger_path=tmp_path / "import_ledger.jsonl",
        readings_dir=tmp_path / "readings",
        state_path=tmp_path / "import_state.jsonl", fresh=fresh,
        grant=_GRANT if grant is None else grant, today=_TODAY, **kw)


def _seed_wave_history(tmp_path, costs):
    """Pre-seed the ledger with prior wave rows carrying the given
    cost_per_certified_statement values (the P-LI1-COST trailing history)."""
    p = tmp_path / "import_ledger.jsonl"
    with open(p, "a", encoding="utf-8") as fh:
        for i, c in enumerate(costs):
            fh.write(common.canonical_json(
                {"kind": "wave", "wave_id": i, "arm": "ungoverned",
                 "totals": {"cost_per_certified_statement": c},
                 "breaker_verdicts": [], "halt_reason": "frontier-empty"})
                + "\n")
    return p


# ========================================================= end-to-end wave ==
def test_wave_end_to_end_outcomes_ledger_and_queue(tmp_path):
    """One wave over the committed fixture queue: every outcome class lands
    (authored / declared fragment-miss / gate fragment-miss / refused), the
    queue statuses flip, the ledger carries item rows + one wave row with the
    recorded breaker verdicts, and the reading artifact persists with its
    R1 anchor + encoding version."""
    q = _fixture_queue(tmp_path)
    fake = _FakeTransport(fail={"Nat.author_always_fails"})
    s = _run(tmp_path, q, author=fake)

    assert s["status"] == "completed"
    assert s["halt_reason"] == "frontier-empty"
    by_decl = {r["decl_name"]: r for r in s["items"]}
    assert by_decl["Nat.Coprime.left_of_pair"]["outcome"] == "authored"
    assert by_decl["Nat.Coprime.left_of_pair'"]["outcome"] == "authored"
    assert by_decl["Real.add_comm_declared_miss"]["outcome"] == "fragment-miss"
    assert by_decl["Nat.Prime.gate_level_miss"]["outcome"] == "fragment-miss"
    assert by_decl["Nat.author_always_fails"]["outcome"] == "refused"
    assert by_decl["Nat.author_always_fails"]["stage"] == "author-failed"

    # queue statuses flipped in place (WP-LI0 schema values only).
    statuses = {r["decl_name"]: r["status"] for r in drv.load_queue(q)}
    assert statuses["Nat.Coprime.left_of_pair"] == "authored"
    assert statuses["Real.add_comm_declared_miss"] == "fragment-miss"
    assert statuses["Nat.author_always_fails"] == "refused"
    assert set(statuses.values()) <= set(drv.QUEUE_STATUSES)

    # ledger: item rows + ONE wave row, wave row carries the plan-§6 verdicts.
    rows = drv.load_ledger(tmp_path / "import_ledger.jsonl")
    assert [r["kind"] for r in rows] == ["item"] * 5 + ["wave"]
    wave = rows[-1]
    assert wave["halt_reason"] == "frontier-empty"
    assert {b["name"] for b in wave["breaker_verdicts"]} == \
        {"P-LI1-REFUSAL", "P-LI1-COST"}
    assert all(not b["fired"] for b in wave["breaker_verdicts"])
    assert wave["totals"]["items"] == 5
    assert wave["totals"]["authored"] == 2
    assert wave["totals"]["fragment_miss"] == 2
    assert wave["totals"]["refused"] == 1
    assert wave["frontier_remaining"] == 0
    # timestamps are RECORDED on every row (never compared anywhere).
    assert all("ts" in r for r in rows if r["kind"] == "item")

    # the persisted reading: R2 provenance chain + R1 anchor.
    rp = tmp_path / "readings" / "Nat.Coprime.left_of_pair.json"
    doc = json.loads(rp.read_text(encoding="utf-8"))
    assert doc["decl_name"] == "Nat.Coprime.left_of_pair"
    assert doc["statement_hash"] == "sh-cop-ab"          # the anchor
    assert doc["reading"]["theorem"] == "coprime_left_ab"
    assert doc["encoding_version"] == drv.READING_ENCODING_VERSION
    # only AUTHORED rows persist a reading artifact.
    assert not (tmp_path / "readings" /
                "Real.add_comm_declared_miss.json").exists()
    assert not (tmp_path / "readings" /
                "Nat.author_always_fails.json").exists()


def test_arm_recorded_per_row_and_unknown_arm_refused(tmp_path):
    """--arm is recorded on every item row AND the wave row (the ab-pilot
    ruling's audit surface); an unknown arm is a refusal, not a crash."""
    q = _fixture_queue(tmp_path)
    s = _run(tmp_path, q, arm="governed",
             author=_FakeTransport(fail={"Nat.author_always_fails"}))
    rows = drv.load_ledger(tmp_path / "import_ledger.jsonl")
    assert all(r["arm"] == "governed" for r in rows)
    assert rows[-1]["arm_config"] == drv.ARM_CONFIGS["governed"]
    bad = _run(tmp_path, q, arm="frankenarm")
    assert bad["status"] == "refused"
    assert "unknown-arm" in bad["reason"]


# ==================================================== budget stop (F1.2/E6) ==
def test_budget_stop_from_usage_metadata_only(tmp_path):
    """The wave stops on the kilotoken budget measured ONLY from the
    transport's RETURNED token counts (1000+200 per call = 1.2 kt): budget
    2.5 kt admits exactly 3 authorings (spend checked BEFORE each call),
    the rest of the frontier stays pending, and the halt is a recorded
    verdict -- never an exception."""
    q = _synthetic_queue(tmp_path, 10)
    fake = _FakeTransport()
    s = _run(tmp_path, q, budget=2.5, author=fake)
    assert s["status"] == "completed"
    assert s["halt_reason"] == "budget-exhausted"
    assert fake.calls == 3
    assert s["totals"]["items"] == 3
    assert s["totals"]["ktokens_total"] == pytest.approx(3 * 1.2)
    assert s["totals"]["ktokens_in"] == pytest.approx(3 * 1.0)
    assert s["totals"]["ktokens_out"] == pytest.approx(3 * 0.2)
    statuses = [r["status"] for r in drv.load_queue(q)]
    assert statuses.count("pending") == 7          # untouched frontier
    assert s["frontier_remaining"] == 7
    # per-item kilotokens come straight from the returned usage.
    assert all(r["ktokens_in"] == 1.0 and r["ktokens_out"] == 0.2
               for r in s["items"])


def test_budget_capped_by_grant_per_wave_cap_and_fixed_remainder(tmp_path):
    """The effective budget is min(CLI budget, grant per-wave cap, and -- in
    fixed mode -- the ledger-decremented remainder)."""
    q = _synthetic_queue(tmp_path, 10)
    grant = dict(_GRANT, per_wave_cap_ktokens=2.5)
    s = _run(tmp_path, q, budget=1000.0, grant=grant, author=_FakeTransport())
    assert s["wave_row"]["budget_ktokens_effective"] == 2.5
    assert s["totals"]["items"] == 3

    # fixed mode: remainder = granted - ledger spend caps the next wave.
    tmp2 = tmp_path / "fixed"
    tmp2.mkdir()
    q2 = _synthetic_queue(tmp2, 10)
    fixed = {"mode": "fixed", "granted_ktokens": 5.0, "expires": "2099-01-01"}
    s1 = _run(tmp2, q2, budget=2.5, grant=fixed, author=_FakeTransport())
    assert s1["totals"]["items"] == 3              # spent 3.6 of 5.0
    s2 = _run(tmp2, q2, budget=100.0, grant=fixed, author=_FakeTransport())
    assert s2["wave_row"]["budget_ktokens_effective"] == pytest.approx(
        5.0 - 3.6)                                 # the decremented remainder
    s3 = _run(tmp2, q2, budget=100.0, grant=fixed, author=_FakeTransport())
    assert s3["status"] == "refused"
    assert s3["reason"] == "grant-exhausted"


# ======================================================= breakers (plan §6) ==
def test_refusal_breaker_verdict_on_synthetic_histories():
    """P-LI1-REFUSAL unit teeth: never fires under a partial window; fires
    strictly above 60% over the trailing 20."""
    v = drv.refusal_breaker_verdict(["refused"] * 19)
    assert not v["fired"] and v["observed"]["refusal_rate"] is None
    v = drv.refusal_breaker_verdict(["authored"] * 5 + ["refused"] * 13
                                    + ["authored"] * 7)        # 13/20 = 65%
    assert v["fired"] and v["pass"] is False
    v = drv.refusal_breaker_verdict(["refused"] * 12 + ["authored"] * 8)
    assert not v["fired"]                          # 60% is NOT > 60%
    assert v["name"] == "P-LI1-REFUSAL"


def test_refusal_breaker_halts_wave_recorded_not_raised(tmp_path):
    """25 straight author failures: the wave halts at the 20th item with
    halt_reason breaker:P-LI1-REFUSAL, the fired verdict is RECORDED on the
    wave row, and the untouched frontier stays pending."""
    q = _synthetic_queue(tmp_path, 25)
    fake = _FakeTransport(fail={"Syn.decl_%02d" % i for i in range(25)})
    s = _run(tmp_path, q, author=fake)
    assert s["status"] == "completed"
    assert s["halt_reason"] == "breaker:P-LI1-REFUSAL"
    assert s["totals"]["items"] == drv.REFUSAL_WINDOW
    fired = [b for b in s["wave_row"]["breaker_verdicts"] if b["fired"]]
    assert [b["name"] for b in fired] == ["P-LI1-REFUSAL"]
    assert fired[0]["observed"]["refusal_rate"] == 1.0
    statuses = [r["status"] for r in drv.load_queue(q)]
    assert statuses.count("pending") == 5


def test_cost_breaker_verdict_on_synthetic_histories():
    """P-LI1-COST unit teeth: fires strictly above 3x the trailing median;
    cannot fire with no history (the first wave defines the baseline); stays
    disarmed under the minimum in-wave sample."""
    hist = [1.0, 1.0, 2.0]                         # median 1.0
    v = drv.cost_breaker_verdict(15.0, 4, hist, wave_items=8)   # cost 3.75
    assert v["fired"] and v["observed"]["trailing_median"] == 1.0
    v = drv.cost_breaker_verdict(12.0, 4, hist, wave_items=8)   # cost 3.0
    assert not v["fired"]                          # 3x is NOT > 3x
    v = drv.cost_breaker_verdict(1000.0, 1, [], wave_items=8)
    assert not v["fired"]                          # no history, no median
    v = drv.cost_breaker_verdict(1000.0, 1, hist,
                                 wave_items=drv.COST_BREAKER_MIN_ITEMS - 1)
    assert not v["fired"]                          # disarmed: sample too small
    assert v["name"] == "P-LI1-COST"


def test_cost_breaker_halts_wave_on_ledger_history(tmp_path):
    """With a seeded trailing wave-cost history (median 1.0 kt/statement) a
    wave burning 1.2 kt per item with ZERO certified rows (garbage readings:
    tokens billed, nothing certifies) blows past 3x the median as soon as the
    breaker arms -- halt recorded, never raised."""
    _seed_wave_history(tmp_path, [1.0, 1.0, 1.0])
    q = _synthetic_queue(tmp_path, 10)
    fake = _FakeTransport(garbage=True)
    s = _run(tmp_path, q, author=fake)
    assert s["status"] == "completed"
    assert s["halt_reason"] == "breaker:P-LI1-COST"
    assert s["totals"]["items"] == drv.COST_BREAKER_MIN_ITEMS
    fired = [b for b in s["wave_row"]["breaker_verdicts"] if b["fired"]]
    assert "P-LI1-COST" in [b["name"] for b in fired]
    # wave_id advanced past the seeded history (append-only wave count).
    assert s["wave_id"] == 3


# ============================================== grant governance (plan §5) ==
def test_grant_refusal_paths(tmp_path):
    """Missing / expired / no-expiry / unknown-mode grants all REFUSE before a
    single author call -- and the refusal names its reason."""
    q = _fixture_queue(tmp_path)
    fake = _FakeTransport()

    missing = drv.run_wave(budget_ktokens=10, author=fake, queue_path=q,
                           ledger_path=tmp_path / "l.jsonl",
                           readings_dir=tmp_path / "r",
                           state_path=tmp_path / "s.jsonl",
                           grant_path=tmp_path / "no_such_grant.json",
                           today=_TODAY)
    assert missing == {"status": "refused", "reason": "missing-grant",
                       "grant_verdict": missing["grant_verdict"]}

    expired = _run(tmp_path, q, author=fake,
                   grant=dict(_GRANT, expires="2026-01-01"))
    assert expired["status"] == "refused"
    assert expired["reason"] == "grant-expired"

    no_expiry = _run(tmp_path, q, author=fake,
                     grant={"mode": "weekly-quota-exhaustion"})
    assert no_expiry["reason"] == "grant-has-no-expiry"

    unknown = _run(tmp_path, q, author=fake, grant=dict(_GRANT, mode="vibes"))
    assert unknown["status"] == "refused"
    assert "unknown-grant-mode" in unknown["reason"]

    assert fake.calls == 0                         # not one author call
    assert not (tmp_path / "import_ledger.jsonl").exists()


def test_grant_check_is_pure_and_reads_committed_grant():
    """check_grant is a pure function of (grant, ledger, today) -- and the
    COMMITTED specs/ops/spend_grant.json parses and passes it inside its own
    validity window (the RULED weekly-quota-exhaustion mode)."""
    grant = drv.load_grant()                       # the committed artifact
    assert grant is not None
    assert grant["mode"] == "weekly-quota-exhaustion"
    ok = drv.check_grant(grant, [], today=grant["granted_on"])
    assert ok["ok"] and ok["remaining_ktokens"] is None
    late = drv.check_grant(grant, [], today="2099-12-31")
    assert late == {"ok": False, "reason": "grant-expired",
                    "expires": grant["expires"], "today": "2099-12-31"}


def test_interlock_no_confirm_skips_and_never_runs(monkeypatch):
    """bench_metered's interlock, verbatim: a bare main() (no --confirm-spend,
    no env) SKIPS with exit 0 and never reaches run_wave -- an accidental
    invocation can never spend."""
    monkeypatch.delenv(drv._CONFIRM_SPEND_ENV, raising=False)
    entered = {"n": 0}

    def _boom(**kw):
        entered["n"] += 1
        raise AssertionError("run_wave must not be reached without confirm")

    monkeypatch.setattr(drv, "run_wave", _boom)
    assert drv.main([]) == 0
    assert drv.main(["--budget-ktokens", "5", "--fresh"]) == 0
    assert entered["n"] == 0


def test_interlock_flag_or_env_reaches_run_and_exit_codes(monkeypatch):
    """--confirm-spend (or CGB_METERED_CONFIRM_SPEND=1) reaches run_wave; a
    completed wave exits 0, a post-confirm refusal exits 2 (a scheduling lane
    must notice a confirmed-but-refused wave)."""
    monkeypatch.delenv(drv._CONFIRM_SPEND_ENV, raising=False)
    calls = {"n": 0}
    result = {"status": "completed", "halt_reason": "frontier-empty",
              "wave_id": 0, "arm": "ungoverned", "totals": {},
              "breakers": [], "frontier_remaining": 0, "spent_ktokens": 0.0,
              "ledger_path": "x"}

    def _fake_run(**kw):
        calls["n"] += 1
        return dict(result)

    monkeypatch.setattr(drv, "run_wave", _fake_run)
    assert drv.main(["--budget-ktokens", "5", "--confirm-spend"]) == 0
    assert calls["n"] == 1
    monkeypatch.setenv(drv._CONFIRM_SPEND_ENV, "1")
    assert drv.main(["--budget-ktokens", "5"]) == 0
    assert calls["n"] == 2
    monkeypatch.setattr(drv, "run_wave",
                        lambda **kw: {"status": "refused",
                                      "reason": "missing-grant"})
    assert drv.main(["--budget-ktokens", "5", "--confirm-spend"]) == 2


def test_cgb_import_subcommand_help():
    """`python3 cgb.py import --help` works (the WP-LI1 wiring) and shows the
    budget flag + the spend interlock."""
    proc = subprocess.run(
        [sys.executable, str(_ROOT / "cgb.py"), "import", "--help"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(_ROOT),
        timeout=120)
    out = proc.stdout.decode()
    assert proc.returncode == 0
    assert "--budget-ktokens" in out
    assert "--confirm-spend" in out
    assert "--arm" in out and "--queue" in out and "--fresh" in out


# ================================== quota exhaustion => GRACEFUL halt (§5) ==
def test_quota_error_is_graceful_recorded_halt(tmp_path):
    """A CLI quota/rate-limit signal mid-wave halts GRACEFULLY: the wave row
    records halt_reason=quota-exhausted + a quota-signal verdict, the rows
    already done keep their outcomes, the interrupted decl stays pending for
    the next wave (weekly reset), and nothing raises."""
    q = _synthetic_queue(tmp_path, 6)
    fake = _FakeTransport(quota_after=2)
    s = _run(tmp_path, q, author=fake)
    assert s["status"] == "completed"              # never a crash
    assert s["halt_reason"] == "quota-exhausted"
    assert s["totals"]["items"] == 2
    quota = [b for b in s["wave_row"]["breaker_verdicts"]
             if b["name"] == "quota-signal"]
    assert len(quota) == 1 and quota[0]["fired"]
    assert "429" in quota[0]["observed"]
    statuses = [r["status"] for r in drv.load_queue(q)]
    assert statuses.count("authored") == 2
    assert statuses.count("pending") == 4          # incl. the interrupted decl
    rows = drv.load_ledger(tmp_path / "import_ledger.jsonl")
    assert rows[-1]["kind"] == "wave"
    assert rows[-1]["halt_reason"] == "quota-exhausted"


def test_llm_author_maps_cli_errors(monkeypatch):
    """The REAL author's error mapping (no subprocess is ever spawned: call_llm
    is monkeypatched): a quota-marked LLMError raises QuotaExhausted; an
    ordinary LLMError returns None (a refused item, not a halt)."""
    from buildloop import llm

    def _quota_boom(prompt, model=None):
        raise llm.LLMError("claude CLI rc=1: usage limit reached, "
                           "resets Thursday")

    monkeypatch.setattr(llm, "call_llm", _quota_boom)
    with pytest.raises(drv.QuotaExhausted):
        drv._llm_author("d", "n = n", {}, {})

    def _plain_boom(prompt, model=None):
        raise llm.LLMError("claude CLI rc=1: some transient parse failure")

    monkeypatch.setattr(llm, "call_llm", _plain_boom)
    assert drv._llm_author("d", "n = n", {}, {}) is None


def test_is_quota_error_markers():
    assert drv._is_quota_error("HTTP 429 Too Many Requests")
    assert drv._is_quota_error("weekly QUOTA exhausted")
    assert drv._is_quota_error("rate limit hit")
    assert not drv._is_quota_error("segfault in the CLI")
    assert not drv._is_quota_error("")


# =========================================== ledger append-only round-trip ==
def test_ledger_append_only_round_trip_across_waves(tmp_path):
    """A later wave strictly EXTENDS the ledger bytes (append-only: the old
    content is a byte prefix of the new), every line round-trips through
    load_ledger, and the cumulative spend sums ITEM rows only.  --fresh
    re-keys the CHECKPOINT and never touches the ledger."""
    q = _synthetic_queue(tmp_path, 2)
    _run(tmp_path, q, author=_FakeTransport())
    ledger = tmp_path / "import_ledger.jsonl"
    before = ledger.read_bytes()

    # second wave over new frontier rows, SAME ledger.
    rows = drv.load_queue(q) + [
        {"decl_name": "Syn.late_%d" % i, "module": "Syn",
         "statement_pp": "d coprime to a and coprime to b -> d coprime to a",
         "statement_hash": "sh-late-%d" % i, "status": "pending"}
        for i in range(2)]
    drv.write_queue(q, rows)
    s2 = _run(tmp_path, q, author=_FakeTransport(), fresh=True)
    after = ledger.read_bytes()
    assert after.startswith(before)                # append-only
    assert len(after) > len(before)
    assert s2["wave_id"] == 1                      # wave count advanced

    parsed = drv.load_ledger(ledger)
    assert [r["kind"] for r in parsed] == ["item", "item", "wave",
                                           "item", "item", "wave"]
    # spend decrements from ITEM rows only (wave totals never double-count).
    assert drv.ledger_spent_ktokens(parsed) == pytest.approx(4 * 1.2)
    # ledger rows survive canonical-JSON round-trip byte-for-byte.
    assert [common.canonical_json(r) for r in parsed] == \
        [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln]


# ================================================== fragment-miss binning ==
def test_fragment_miss_binning_feeds_wave_histogram(tmp_path):
    """Both miss channels bin into the wave miss_histogram (WP-LI4 demand
    data): the author-DECLARED structured miss keeps its declared constants;
    the GATE-level FragmentMiss bins by missing_kind_guess."""
    q = _fixture_queue(tmp_path)
    s = _run(tmp_path, q, author=_FakeTransport(
        fail={"Nat.author_always_fails"}))
    by_decl = {r["decl_name"]: r for r in s["items"]}
    declared = by_decl["Real.add_comm_declared_miss"]
    assert declared["outcome"] == "fragment-miss"
    assert declared["stage"] == "declared-by-author"
    assert declared["miss_bins"] == ["carrier:Real"]
    gate = by_decl["Nat.Prime.gate_level_miss"]
    assert gate["outcome"] == "fragment-miss"
    assert gate["stage"] == "math-reading-gate"
    assert gate["miss_bins"] == ["operator:prime"]
    assert s["wave_row"]["miss_histogram"] == {"carrier:Real": 1,
                                               "operator:prime": 1}
    # authored/refused rows carry NO bins.
    assert by_decl["Nat.Coprime.left_of_pair"]["miss_bins"] == []
    assert by_decl["Nat.author_always_fails"]["miss_bins"] == []


def test_declared_fragment_miss_parser():
    """Only the exact structured shape counts as a declared miss."""
    assert drv._declared_fragment_miss(
        '{"fragment_miss": {"missing": ["carrier:Real", "operator:prime"]}}'
    ) == ["carrier:Real", "operator:prime"]
    assert drv._declared_fragment_miss('{"theorem": "t", "statements": []}') \
        is None
    assert drv._declared_fragment_miss("not json at all") is None
    assert drv._declared_fragment_miss('{"fragment_miss": "Real"}') is None


# =========================================================== resumability ==
def test_resume_skips_checkpointed_decls_and_replays_outcomes(tmp_path):
    """A re-run against the same checkpoint re-authors NOTHING: even with the
    queue statuses reset to pending (the killed-before-queue-rewrite window),
    every checkpointed decl is replayed from its record -- outcomes land back
    on the queue and no duplicate ledger item row is appended."""
    q = _fixture_queue(tmp_path)
    fake1 = _FakeTransport(fail={"Nat.author_always_fails"})
    s1 = _run(tmp_path, q, author=fake1)
    assert fake1.calls == 5
    outcomes1 = {r["decl_name"]: r["status"] for r in drv.load_queue(q)}

    # simulate the crash window: queue rewrite lost, statuses back to pending.
    rows = drv.load_queue(q)
    for r in rows:
        r["status"] = "pending"
    drv.write_queue(q, rows)

    fake2 = _FakeTransport(fail={"Nat.author_always_fails"})
    s2 = _run(tmp_path, q, author=fake2)
    assert fake2.calls == 0                        # nothing re-authored
    assert s2["totals"]["items"] == 0              # no NEW billed items
    assert s2["spent_ktokens"] == 0.0
    assert {r["decl_name"]: r["status"]
            for r in drv.load_queue(q)} == outcomes1
    ledger = drv.load_ledger(tmp_path / "import_ledger.jsonl")
    item_keys = [r["decl_name"] for r in ledger if r["kind"] == "item"]
    assert sorted(item_keys) == sorted(set(item_keys))   # no duplicates


def test_fresh_reauthors_but_never_truncates_ledger(tmp_path):
    """--fresh re-keys the CHECKPOINT (decls re-author) while the ledger only
    ever grows."""
    q = _synthetic_queue(tmp_path, 2)
    _run(tmp_path, q, author=_FakeTransport())
    ledger = tmp_path / "import_ledger.jsonl"
    before = ledger.read_bytes()
    # reset the queue so the frontier is non-empty again.
    rows = drv.load_queue(q)
    for r in rows:
        r["status"] = "pending"
    drv.write_queue(q, rows)
    fake = _FakeTransport()
    _run(tmp_path, q, author=fake, fresh=True)
    assert fake.calls == 2                         # checkpoint re-keyed
    assert ledger.read_bytes().startswith(before)  # ledger NEVER truncated


# ================================================ encoding version (§2.5) ==
def test_encoding_version_stamped_everywhere(tmp_path):
    """READING_ENCODING_VERSION (T-LI-ENC scaffolding) is stamped on every
    ledger ITEM row and every persisted reading artifact."""
    assert drv.READING_ENCODING_VERSION == 1
    q = _fixture_queue(tmp_path)
    _run(tmp_path, q, author=_FakeTransport(fail={"Nat.author_always_fails"}))
    rows = drv.load_ledger(tmp_path / "import_ledger.jsonl")
    items = [r for r in rows if r["kind"] == "item"]
    assert items and all(r["encoding_version"] == drv.READING_ENCODING_VERSION
                         for r in items)
    for p in (tmp_path / "readings").iterdir():
        doc = json.loads(p.read_text(encoding="utf-8"))
        assert doc["encoding_version"] == drv.READING_ENCODING_VERSION


# ============================================== the import prompt (WP-LI1) ==
def test_import_prompt_composes_fragment_machinery_deterministically():
    """render_import_reading_prompt: byte-deterministic; COMPOSES the same
    single-source fragment machinery as the NL prompt (grammar block,
    envelope, definition table, force rules -- never a duplicated fragment
    description); embeds the FORMAL statement + decl name; and carries the
    structured fragment-miss rule the driver's classifier parses."""
    from buildloop import math_prompt
    pp = "∀ (n m : ℕ), Nat.gcd n m = Nat.gcd m n"
    p1 = math_prompt.render_import_reading_prompt("Nat.gcd_comm", pp, None, {})
    p2 = math_prompt.render_import_reading_prompt("Nat.gcd_comm", pp, None, {})
    assert p1 == p2                                # deterministic bytes
    assert "Nat.gcd_comm" in p1 and pp in p1
    # the SAME single-source sections as the NL prompt (compose, not copy).
    nl = math_prompt.render_math_reading_prompt("some source text")
    for shared in (math_prompt.render_grammar_block(),
                   math_prompt.render_definition_table({}),
                   math_prompt._ENVELOPE_NOTE, math_prompt._RULES):
        assert shared in p1 and shared in nl
    # the structured miss rule matches what _declared_fragment_miss parses.
    assert '{"fragment_miss": {"missing":' in p1
    assert "fragment_miss" not in nl               # import-specific rule

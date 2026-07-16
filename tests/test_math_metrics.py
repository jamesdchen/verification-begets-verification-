"""WP-B teeth: math metrics fields (F-INT-3), the m9/m9_planted milestones,
and the formalization reach-vs-cost curve.

CAPTURE-BEFORE-EDIT (§1, ⚠FI-11): `PREEDIT_CSV_HEADER` below is the
`metrics.export_csv` header captured from the FROZEN pre-swarm base, BEFORE any
`metrics/` edit landed.  The CSV tooth asserts the four F-INT-3 columns are
APPENDED after every one of these pre-existing columns (append-only), so the pin
is against the base bytes, never against post-edit code.
"""
from __future__ import annotations

import csv

import pytest

# Captured from the frozen pre-swarm base (metrics.export_csv on a fresh
# registry), before touching metrics/__init__.py.  Do NOT regenerate from the
# edited code -- that would make the pin vacuous.
PREEDIT_CSV_HEADER = [
    "seq", "at", "event", "policy", "corpus", "reach", "covered",
    "backlog_n", "llm_input_tokens", "llm_output_tokens", "verifier_seconds",
    "avg_chain_depth", "max_chain_depth", "tier_universal", "tier_emit_check",
    "total_dl", "live_size", "corpus_caught", "fresh_caught",
]


def _fresh_registry(tmp_path):
    from library import Registry
    return Registry(db_path=str(tmp_path / "reg.sqlite"))


def _export_header(registry, tmp_path):
    import metrics
    out = tmp_path / "metrics.csv"
    metrics.export_csv(registry, str(out))
    with open(out) as f:
        return next(csv.reader(f))


MATH_COLS = ["math_total", "math_covered", "math_dream_rows",
             "tier_kernel_checked", "prequential_counting_dl"]


def _seed_mixed(reg, *, n_exo=3, n_covered=2, n_dream=2):
    """A mixed math-source registry: n_exo exogenous rows (n_covered of them
    with a persisted reading) + n_dream system-origin dream rows."""
    for i in range(n_exo):
        did = f"exo{i}"
        reg.demand_upsert({"demand_id": did, "kind": "math-source",
                           "origin": "exogenous", "status": "open",
                           "payload_ref": f"specs/mathsources/{i}.txt",
                           "size_bytes": 10})
        if i < n_covered:
            reg.reading_add(did, '{"theorem": "t", "statements": []}',
                            "planted:" + did)
    for j in range(n_dream):
        did = f"dream{j}"
        reg.demand_upsert({"demand_id": did, "kind": "math-source",
                           "origin": "system", "status": "open",
                           "payload_ref": f"specs/mathsources/dream/d{j}.txt",
                           "size_bytes": 10})


# --------------------------------------------------------------- B4: fields
def test_snapshot_math_fields_mixed_registry(tmp_path):
    """F-INT-3 frozen defs on a mixed exogenous+dream registry: covered<=total,
    dreams counted ONLY in math_dream_rows, tier_kernel_checked==0 (Lean-absent)."""
    import metrics
    reg = _fresh_registry(tmp_path)
    _seed_mixed(reg, n_exo=3, n_covered=2, n_dream=2)
    row = metrics.snapshot(reg, [], event="mixed")
    assert row["math_total"] == 3           # exogenous rows only
    assert row["math_covered"] == 2         # exogenous rows WITH a reading
    assert row["math_dream_rows"] == 2      # system-origin, separate bucket
    assert row["tier_kernel_checked"] == 0  # no proof-cert without Lean
    # relational, never an absolute constant: covered <= total by construction.
    assert row["math_covered"] <= row["math_total"]
    # dreams are NOT in total or covered.
    assert row["math_total"] + row["math_dream_rows"] == 5


def test_covered_le_total_is_structural(tmp_path):
    """Even with a reading persisted for EVERY exogenous row, covered<=total."""
    import metrics
    reg = _fresh_registry(tmp_path)
    _seed_mixed(reg, n_exo=4, n_covered=4, n_dream=1)
    fields = metrics.math_fields(reg)
    assert fields["math_covered"] == fields["math_total"] == 4
    assert fields["math_covered"] <= fields["math_total"]
    assert fields["math_dream_rows"] == 1


def test_dream_only_registry_has_zero_total_and_covered(tmp_path):
    import metrics
    reg = _fresh_registry(tmp_path)
    _seed_mixed(reg, n_exo=0, n_covered=0, n_dream=3)
    fields = metrics.math_fields(reg)
    assert fields["math_total"] == 0
    assert fields["math_covered"] == 0
    assert fields["math_dream_rows"] == 3


# ----------------------------------------------------------- B4: CSV append
def test_csv_header_appends_math_columns(tmp_path):
    """The four F-INT-3 columns are APPENDED after every pre-existing column,
    pinned against the pre-edit capture (⚠FI-11)."""
    reg = _fresh_registry(tmp_path)
    header = _export_header(reg, tmp_path)
    assert header[: len(PREEDIT_CSV_HEADER)] == PREEDIT_CSV_HEADER   # prefix
    assert header[len(PREEDIT_CSV_HEADER):] == MATH_COLS            # appended
    assert header == PREEDIT_CSV_HEADER + MATH_COLS


def test_prequential_column_appended_and_populated(tmp_path):
    """WP-P1 (§11.1 requirement 6): the counting-prequential column is appended
    after the four F-INT-3 columns and carries a non-negative DL value."""
    import metrics
    reg = _fresh_registry(tmp_path)
    _seed_mixed(reg, n_exo=3, n_covered=2, n_dream=2)
    fields = metrics.math_fields(reg)
    assert "prequential_counting_dl" in fields
    assert float(fields["prequential_counting_dl"]) >= 0.0
    assert MATH_COLS[-1] == "prequential_counting_dl"     # appended at END
    assert "prequential_dl" not in MATH_COLS              # -log p name reserved


def test_math_metrics_alter_table_guard_idempotent(tmp_path):
    """WP-P1 (§11.1 requirement 6): a DB created with the OLD 4-column
    math_metrics table must not break -- `_ensure_math_metrics` ADDs the column
    once (idempotent) and existing rows survive with the new column NULL."""
    import metrics
    reg = _fresh_registry(tmp_path)
    # emulate a pre-WP-P1 DB: create the OLD 4-column table and seed a row.
    reg.db.execute("DROP TABLE IF EXISTS math_metrics")
    reg.db.execute(
        "CREATE TABLE math_metrics(seq INTEGER PRIMARY KEY, math_total INTEGER,"
        " math_covered INTEGER, math_dream_rows INTEGER,"
        " tier_kernel_checked INTEGER)")
    reg.db.execute("INSERT INTO math_metrics VALUES(1,7,5,2,0)")
    reg.db.commit()
    # first ensure MIGRATES (adds column); second is a no-op (idempotent).
    metrics._ensure_math_metrics(reg)
    metrics._ensure_math_metrics(reg)
    cols = {r[1] for r in reg.db.execute("PRAGMA table_info(math_metrics)")}
    assert "prequential_counting_dl" in cols
    # the pre-existing row survived; the new column is NULL for it.
    old = reg.db.execute(
        "SELECT math_total, prequential_counting_dl FROM math_metrics "
        "WHERE seq=1").fetchone()
    assert old[0] == 7 and old[1] is None
    # a fresh snapshot writes the column going forward (JOIN still exports).
    _seed_mixed(reg, n_exo=2, n_covered=1, n_dream=1)
    row = metrics.snapshot(reg, [], event="post-migrate")
    assert "prequential_counting_dl" in row


def test_csv_join_aligns_math_fields_on_seq(tmp_path):
    """The side table JOINs onto the metrics_log row written in the same
    snapshot() call, so the data row carries the correct four values."""
    import csv as _csv
    import metrics
    reg = _fresh_registry(tmp_path)
    _seed_mixed(reg, n_exo=3, n_covered=2, n_dream=2)
    metrics.snapshot(reg, [], event="row")
    out = tmp_path / "m.csv"
    metrics.export_csv(reg, str(out))
    with open(out) as f:
        rows = list(_csv.DictReader(f))
    assert len(rows) == 1
    r = rows[0]
    assert (int(r["math_total"]), int(r["math_covered"]),
            int(r["math_dream_rows"]), int(r["tier_kernel_checked"])) == (3, 2, 2, 0)


# ------------------------------------------------- B3/B4: m9_planted (gated)
def _wp_a_ready():
    from buildloop import loop
    return hasattr(loop, "_math_moves")


def test_m9_planted_monotone_reach(tmp_path):
    """B3/B4: the planted runner yields a monotone-nondecreasing reach series
    and a strictly-increasing synthetic cost axis.  SKIP-gated on WP-A: without
    `_math_moves` the loop proposes no math move (⚠FI-1) -- do not fake green."""
    if not _wp_a_ready():
        pytest.skip("requires WP-A _math_moves")
    import milestones
    reg = _fresh_registry(tmp_path)
    milestones._seed_math_backlog(reg)
    fixtures = milestones._committed_fixture_readings()
    dispatch = {"math": milestones._planted_math_dispatch(fixtures)}
    series = milestones._run_math_curve(
        reg, n_iter=20, dispatch=dispatch, label="m9_planted_test",
        title="test", out_png=str(tmp_path / "curve.png"))
    covered = [row["math_covered"] for row in series]
    tokens = [row["llm_input_tokens"] + row["llm_output_tokens"]
              for row in series]
    assert covered == sorted(covered)              # reach nondecreasing
    assert all(b >= a for a, b in zip(tokens, tokens[1:]))  # cost nondecreasing
    assert covered[-1] >= 1                         # at least one fixture served

"""Teeth for tools/cycle_telemetry.py.

LLM-free, network-free, clock-free (the writer never reads wall-clock; the
timestamp is always supplied).  Covers: schema enforcement, unknown-stage
rejection, append-only behaviour (existing rows untouched), canonical
serialization determinism, and per-axis path routing.
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import cycle_telemetry as ct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TS = "2026-07-24T12:00:00+00:00"


# --- path routing ---------------------------------------------------------

def test_per_axis_path_routing(tmp_path):
    for axis in ("corpus", "purchase", "watchdog"):
        p = ct.ledger_path(axis, root=str(tmp_path))
        assert p.endswith(f"results/cycle_telemetry_{axis}.jsonl")
    # The three axes route to three distinct files.
    paths = {ct.ledger_path(a, root=str(tmp_path)) for a in ct.AXES}
    assert len(paths) == 3


def test_unknown_axis_rejected_by_path():
    with pytest.raises(ValueError):
        ct.ledger_path("bogus")


def test_watchdog_is_its_own_file(tmp_path):
    ct.append_row("corpus", TS, "b", "sha1", 4, {"select": 1.0},
                  root=str(tmp_path))
    ct.append_row("watchdog", TS, "b", "sha1", 0, {},
                  root=str(tmp_path))
    corpus_p = ct.ledger_path("corpus", root=str(tmp_path))
    watchdog_p = ct.ledger_path("watchdog", root=str(tmp_path))
    assert os.path.exists(corpus_p) and os.path.exists(watchdog_p)
    # Watchdog rows never land in the corpus file.
    with open(corpus_p) as fh:
        corpus_lines = [json.loads(x) for x in fh if x.strip()]
    assert len(corpus_lines) == 1 and corpus_lines[0]["axis"] == "corpus"
    with open(watchdog_p) as fh:
        wd_lines = [json.loads(x) for x in fh if x.strip()]
    assert len(wd_lines) == 1 and wd_lines[0]["axis"] == "watchdog"


# --- schema enforcement ---------------------------------------------------

def test_row_schema_fields():
    row = ct.build_row("corpus", TS, "swarm/ws-a", "deadbeef", 7,
                       {"select": 12.5, "author": 600},
                       gate_wallclock_s=118.0,
                       merge_to_next_start_s=None)
    assert set(row) == {
        "axis", "ts", "branch", "sha", "batch_size", "stages",
        "gate_wallclock_s", "merge_to_next_start_s"}
    assert row["axis"] == "corpus"
    assert row["batch_size"] == 7
    assert row["stages"] == {"select": 12.5, "author": 600.0}
    assert row["gate_wallclock_s"] == 118.0
    # merge_to_next_start_s is present and nullable.
    assert row["merge_to_next_start_s"] is None


def test_merge_to_next_start_recorded_when_given():
    row = ct.build_row("corpus", TS, "b", "s", 1, {},
                       merge_to_next_start_s=4.2)
    assert row["merge_to_next_start_s"] == 4.2


def test_unknown_stage_rejected():
    with pytest.raises(ValueError):
        ct.build_row("corpus", TS, "b", "s", 1, {"deploy": 3.0})


def test_all_known_stages_accepted():
    stages = {name: float(i) for i, name in enumerate(ct.STAGES)}
    row = ct.build_row("corpus", TS, "b", "s", 1, stages)
    assert set(row["stages"]) == set(ct.STAGES)


def test_wake_stage_is_in_the_vocabulary():
    # Wake-on-red (PLAN_FRAGMENT §3.1 rule 2) is only a claim until a cycle
    # can RECORD one, so the stage vocabulary carries it explicitly.
    assert "wake" in ct.STAGES
    row = ct.build_row("purchase", TS, "b", "s", 1,
                       {"ship": 40.0, "wake": 310.0})
    assert row["stages"]["wake"] == 310.0


def test_non_numeric_stage_rejected():
    with pytest.raises(TypeError):
        ct.build_row("corpus", TS, "b", "s", 1, {"select": "fast"})


def test_bool_batch_size_rejected():
    # bool is an int subclass; a batch size of True is a bug, not a count.
    with pytest.raises(TypeError):
        ct.build_row("corpus", TS, "b", "s", True, {})


def test_negative_batch_size_rejected():
    with pytest.raises(ValueError):
        ct.build_row("corpus", TS, "b", "s", -1, {})


def test_bad_timestamp_rejected():
    with pytest.raises(ValueError):
        ct.build_row("corpus", "not-a-timestamp", "b", "s", 1, {})


def test_empty_timestamp_rejected():
    with pytest.raises(ValueError):
        ct.build_row("corpus", "", "b", "s", 1, {})


def test_writer_reads_no_clock():
    # The timestamp in the row is exactly what was passed; the writer never
    # substitutes the wall clock.
    row = ct.build_row("corpus", TS, "b", "s", 1, {})
    assert row["ts"] == TS


# --- canonical serialization ----------------------------------------------

def test_serialization_is_sorted_and_deterministic():
    row = ct.build_row("corpus", TS, "b", "s", 3,
                       {"suite": 1.0, "author": 2.0, "select": 3.0})
    line = ct.serialize_row(row)
    # Keys sorted at top level.
    assert line.index('"axis"') < line.index('"batch_size"') \
        < line.index('"branch"')
    # Compact separators (no spaces after commas/colons).
    assert ", " not in line and ": " not in line
    # Deterministic: same inputs -> byte-identical line.
    row2 = ct.build_row("corpus", TS, "b", "s", 3,
                        {"select": 3.0, "author": 2.0, "suite": 1.0})
    assert ct.serialize_row(row2) == line
    # Round-trips.
    assert json.loads(line) == row


def test_appended_line_matches_serialize(tmp_path):
    row = ct.append_row("purchase", TS, "b", "s", 2, {"ship": 5.0},
                        root=str(tmp_path))
    p = ct.ledger_path("purchase", root=str(tmp_path))
    with open(p) as fh:
        line = fh.read().splitlines()[-1]
    assert line == ct.serialize_row(row)


# --- append-only behaviour -------------------------------------------------

def test_append_only_leaves_existing_rows_untouched(tmp_path):
    p = ct.ledger_path("corpus", root=str(tmp_path))
    ct.append_row("corpus", TS, "b", "sha1", 1, {"select": 1.0},
                  root=str(tmp_path))
    with open(p) as fh:
        first = fh.read()
    ct.append_row("corpus", TS, "b", "sha2", 2, {"author": 2.0},
                  root=str(tmp_path))
    with open(p) as fh:
        both = fh.read()
    # The original bytes are a strict prefix of the file after the 2nd append.
    assert both.startswith(first)
    lines = both.splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["sha"] == "sha1"
    assert json.loads(lines[1])["sha"] == "sha2"


def test_each_row_is_one_line(tmp_path):
    for i in range(5):
        ct.append_row("corpus", TS, "b", f"sha{i}", i, {"mine": float(i)},
                      root=str(tmp_path))
    p = ct.ledger_path("corpus", root=str(tmp_path))
    with open(p) as fh:
        lines = [x for x in fh.read().splitlines() if x]
    assert len(lines) == 5
    for line in lines:
        json.loads(line)  # each line is independently valid JSON


# --- CLI -------------------------------------------------------------------

def test_cli_appends_row(tmp_path):
    cmd = [
        sys.executable, os.path.join(ROOT, "tools", "cycle_telemetry.py"),
        "--axis", "corpus", "--ts", TS, "--branch", "swarm/ws-a",
        "--sha", "cafe", "--batch-size", "4",
        "--stage", "select=12.5", "--stage", "author=600",
        "--gate-wallclock", "118", "--merge-to-next-start", "15120",
        "--root", str(tmp_path),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    p = ct.ledger_path("corpus", root=str(tmp_path))
    with open(p) as fh:
        row = json.loads(fh.read().splitlines()[-1])
    assert row["stages"] == {"select": 12.5, "author": 600.0}
    assert row["gate_wallclock_s"] == 118.0
    assert row["merge_to_next_start_s"] == 15120.0
    assert out.stdout.strip() == ct.serialize_row(row)


def test_cli_rejects_unknown_stage(tmp_path):
    cmd = [
        sys.executable, os.path.join(ROOT, "tools", "cycle_telemetry.py"),
        "--axis", "corpus", "--ts", TS, "--branch", "b", "--sha", "s",
        "--batch-size", "1", "--stage", "deploy=3", "--root", str(tmp_path),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True)
    assert out.returncode != 0


# --- the COMMITTED ledgers, not just the encoder ---------------------------
# THE GAP THIS CLOSES (measured 2026-07-27).  Every test above exercises
# `ct.serialize_row` on rows it builds itself, so all three stayed green while
# the committed `results/cycle_telemetry_purchase.jsonl` sat 26/26 rows
# NON-canonical: PR #198 re-serialized the whole file with default separators
# (`{"axis": "purchase", ...}`) and inserted its own row mid-file instead of
# appending.  Nothing was lost -- all 25 prior rows survived -- but every open
# PR appends a canonical row to the canonical base, so all 26 lines collided
# at once and #212, #203 and #181 went un-mergeable in the same minute on the
# same file.  A ledger that only ever gains a line cannot conflict; one that
# gets rewritten conflicts with everything in flight.
#
# Testing the encoder proves the encoder.  These test the ARTIFACT, which is
# the thing that actually merges.

def _committed_rows(axis):
    path = os.path.join(ROOT, "results", f"cycle_telemetry_{axis}.jsonl")
    with open(path) as fh:
        return path, [l.rstrip("\n") for l in fh if l.strip()]


@pytest.mark.parametrize("axis", ct.AXES)
def test_committed_ledger_rows_are_canonically_serialized(axis):
    """Byte-for-byte what `serialize_row` would emit.  A row written any other
    way is a whole-file rewrite waiting to happen: the next tool run
    re-emits it canonically and every line moves."""
    path, lines = _committed_rows(axis)
    for i, line in enumerate(lines, 1):
        assert line == ct.serialize_row(json.loads(line)), (
            f"{path}:{i} is not canonically serialized -- it will be rewritten "
            f"by the next append, conflicting with every PR in flight")


@pytest.mark.parametrize("axis", ct.AXES)
def test_committed_ledger_is_append_shaped(axis):
    """Rows carry no wall-clock the writer chose, so the ledger's only
    invariant is structural: every row parses, and no row repeats a
    (sha, branch, ts) identity.  A duplicate means a rewrite re-emitted a row
    the file already held."""
    path, lines = _committed_rows(axis)
    seen = set()
    for i, line in enumerate(lines, 1):
        row = json.loads(line)
        ident = (row.get("sha"), row.get("branch"), row.get("ts"))
        assert ident not in seen, f"{path}:{i} repeats {ident}"
        seen.add(ident)

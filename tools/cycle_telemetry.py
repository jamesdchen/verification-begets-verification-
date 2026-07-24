#!/usr/bin/env python3
"""Per-cycle telemetry: an append-only, per-axis ledger of where a flywheel
cycle's wall-clock actually goes.

The latency question the loop cannot answer from prose: each cycle claims a
duration, but the *breakdown* -- how long selection vs authoring vs the CI
gate vs the suite took, and (the number that matters most) how long the gap
between one cycle's merge and the next cycle's session start was -- decays
the instant it is spoken.  So we record it as committed evidence, one
canonical JSON line per cycle, DERIVED from timings the caller measured.

Design constraints (all load-bearing):

  * **No clock inside the writer.**  ``append_row`` takes ``ts`` as an
    argument; it never reads the wall clock.  Only the CLI defaults ``--ts``
    to now.  This keeps the ledger reproducible from its inputs and keeps
    tests deterministic.
  * **One file per axis.**  corpus / purchase / watchdog each get their own
    ``results/cycle_telemetry_<axis>.jsonl``.  A single shared file would
    become a rebase meeting-point between two concurrently-merging loops;
    separate files never collide on append.
  * **Fixed stage vocabulary.**  Stage names are restricted to
    {select, author, certify, mine, regen, suite, ship}; an unknown stage is
    a hard error, not a silently-recorded typo that would fragment the
    breakdown across misspellings.
  * **Path-locked.**  The writer constructs the ledger path from the axis;
    there is no way to make it write anywhere else.
  * **Canonical serialization.**  Rows are ``sort_keys=True`` with compact
    separators, so the same inputs always yield byte-identical lines.

The single most important field is ``merge_to_next_start_s`` (nullable): the
seconds from the previous cycle's merge to this cycle's session start.  It
measures whether merge-event chaining actually fires.

Stdlib-only, offline, deterministic, LLM-free.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The only axes that exist; each maps 1:1 to its own ledger file.
AXES = ("corpus", "purchase", "watchdog")

#: The only stage names a row may carry.  Ordered for documentation; the set
#: is what enforces membership.  Unknown names are a hard error.
STAGES = ("select", "author", "certify", "mine", "regen", "suite", "ship")
_STAGE_SET = frozenset(STAGES)


def ledger_path(axis: str, root: str | None = None) -> str:
    """Absolute path of the ledger for ``axis``.  Rejects any unknown axis --
    the path can only ever be one of the three per-axis files, so the writer
    cannot be pointed at an arbitrary file."""
    if axis not in AXES:
        raise ValueError(
            f"unknown axis {axis!r}; must be one of {', '.join(AXES)}")
    base = root if root is not None else _ROOT
    return os.path.join(base, "results", f"cycle_telemetry_{axis}.jsonl")


def _check_stages(stages: dict) -> dict:
    """Validate the stage map: keys in the vocabulary, values numeric.
    Returns a plain float-valued dict (canonical), never mutates the input."""
    if not isinstance(stages, dict):
        raise TypeError("stages must be a dict of {stage_name: seconds}")
    out = {}
    for name, seconds in stages.items():
        if name not in _STAGE_SET:
            raise ValueError(
                f"unknown stage {name!r}; must be one of "
                f"{', '.join(STAGES)}")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise TypeError(
                f"stage {name!r} seconds must be a number, got "
                f"{type(seconds).__name__}")
        out[name] = float(seconds)
    return out


def _check_ts(ts: str) -> str:
    """The timestamp is always supplied by the caller (never the clock here).
    Require an ISO-8601 string that actually parses."""
    if not isinstance(ts, str) or not ts:
        raise ValueError("ts must be a non-empty ISO-8601 string")
    try:
        _dt.datetime.fromisoformat(ts)
    except ValueError as e:
        raise ValueError(f"ts is not valid ISO-8601: {ts!r} ({e})") from None
    return ts


def build_row(
    axis: str,
    ts: str,
    branch: str,
    sha: str,
    batch_size: int,
    stages: dict,
    gate_wallclock_s: float | None = None,
    merge_to_next_start_s: float | None = None,
) -> dict:
    """Assemble one canonical telemetry row from measured inputs.

    No clock is read here: ``ts`` is the caller's measured session start.
    Pure and side-effect free so the schema can be tested without touching
    the filesystem.
    """
    if axis not in AXES:
        raise ValueError(
            f"unknown axis {axis!r}; must be one of {', '.join(AXES)}")
    if isinstance(batch_size, bool) or not isinstance(batch_size, int):
        raise TypeError("batch_size must be an int")
    if batch_size < 0:
        raise ValueError("batch_size must be >= 0")
    row = {
        "axis": axis,
        "ts": _check_ts(ts),
        "branch": str(branch),
        "sha": str(sha),
        "batch_size": batch_size,
        "stages": _check_stages(stages),
        "gate_wallclock_s": (
            None if gate_wallclock_s is None else float(gate_wallclock_s)),
        "merge_to_next_start_s": (
            None if merge_to_next_start_s is None
            else float(merge_to_next_start_s)),
    }
    return row


def serialize_row(row: dict) -> str:
    """The canonical one-line encoding: sorted keys, compact separators.

    Same inputs -> byte-identical output, so appends are deterministic and
    two writers of the same row produce the same bytes.
    """
    return json.dumps(row, sort_keys=True, separators=(",", ":"))


def append_row(
    axis: str,
    ts: str,
    branch: str,
    sha: str,
    batch_size: int,
    stages: dict,
    gate_wallclock_s: float | None = None,
    merge_to_next_start_s: float | None = None,
    root: str | None = None,
) -> dict:
    """Append one canonical row to the axis's ledger and return the row.

    Append-only: existing lines are never read or rewritten.  The path is
    derived from ``axis`` (path-locked); ``ts`` comes from the caller.
    """
    row = build_row(
        axis, ts, branch, sha, batch_size, stages,
        gate_wallclock_s=gate_wallclock_s,
        merge_to_next_start_s=merge_to_next_start_s,
    )
    path = ledger_path(axis, root=root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(serialize_row(row) + "\n")
    return row


def _parse_stage(spec: str) -> tuple[str, float]:
    """Parse a CLI ``--stage name=seconds`` token."""
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            f"--stage expects name=seconds, got {spec!r}")
    name, _, val = spec.partition("=")
    name = name.strip()
    if name not in _STAGE_SET:
        raise argparse.ArgumentTypeError(
            f"unknown stage {name!r}; must be one of {', '.join(STAGES)}")
    try:
        seconds = float(val)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"stage {name!r} seconds must be a number, got {val!r}")
    return name, seconds


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Append one cycle-telemetry row to its per-axis ledger.")
    ap.add_argument("--axis", required=True, choices=AXES)
    ap.add_argument(
        "--ts", default=None,
        help="ISO-8601 session-start timestamp (defaults to now at the CLI "
             "boundary only; the writer never reads the clock).")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--batch-size", type=int, required=True)
    ap.add_argument(
        "--stage", action="append", default=[], metavar="NAME=SECONDS",
        help=f"per-stage seconds; NAME in {{{', '.join(STAGES)}}}. Repeatable.")
    ap.add_argument("--gate-wallclock", type=float, default=None,
                    help="CI-gate wall-clock seconds (nullable).")
    ap.add_argument(
        "--merge-to-next-start", type=float, default=None,
        help="seconds from the previous cycle's merge to this session start "
             "(nullable); measures whether merge-event chaining fires.")
    ap.add_argument("--root", default=None,
                    help="repo root override (tests only).")
    args = ap.parse_args(argv)

    ts = args.ts
    if ts is None:
        ts = _dt.datetime.now(_dt.timezone.utc).isoformat()

    stages: dict = {}
    for spec in args.stage:
        name, seconds = _parse_stage(spec)
        stages[name] = seconds

    try:
        row = append_row(
            axis=args.axis, ts=ts, branch=args.branch, sha=args.sha,
            batch_size=args.batch_size, stages=stages,
            gate_wallclock_s=args.gate_wallclock,
            merge_to_next_start_s=args.merge_to_next_start,
            root=args.root,
        )
    except (ValueError, TypeError) as e:
        print(f"cycle_telemetry: {e}", file=sys.stderr)
        return 2

    print(serialize_row(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

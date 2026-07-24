#!/usr/bin/env python3
"""Regenerate `ci/pytest_shard_weights.json` -- the measured per-file suite
durations `run_regression._pytest_shard` balances the CI pytest shards with.

The weights are a BALANCE input, never a coverage input: `_pytest_shard`
partitions the test files exactly whatever this file says (a missing file
falls back to sorted-file parity; an unknown file gets a default weight), so
stale weights cost seconds, not tests.  Regenerate occasionally -- after
adding a slow test file, or when the CI shard durations visibly drift apart:

    python3 -m pytest tests/ -q --durations=0 > /tmp/durations.txt
    python3 tools/pytest_shard_weights.py --from /tmp/durations.txt

Deterministic from its input: parses pytest's `--durations=0` report lines
(`<seconds>s call|setup|teardown tests/<file>::<test>`), sums seconds per
file, floors every existing test file at 0.05s (files whose tests are all
sub-threshold never appear in the report), and writes the sorted JSON map.
Stdlib-only, offline, LLM-free.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = _ROOT / "ci" / "pytest_shard_weights.json"

_LINE = re.compile(r"([\d.]+)s\s+(?:call|setup|teardown)\s+(tests/[^:]+)::")

#: Floor for a test file with no (or sub-threshold) reported durations.
FLOOR_S = 0.05


def parse_durations(text: str) -> dict:
    """Sum reported seconds per test file from a `--durations=0` report."""
    per_file: dict = {}
    for line in text.splitlines():
        m = _LINE.match(line.strip())
        if m:
            f = m.group(2)
            per_file[f] = per_file.get(f, 0.0) + float(m.group(1))
    return per_file


def build_weights(per_file: dict, root: pathlib.Path = _ROOT) -> dict:
    """One weight per EXISTING tests/test_*.py (deleted files are pruned,
    unmeasured files get the floor), rounded for a stable committed diff."""
    files = sorted(str(p.relative_to(root))
                   for p in (root / "tests").glob("test_*.py"))
    return {f: round(max(per_file.get(f, 0.0), FLOOR_S), 2) for f in files}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="src", metavar="FILE", default=None,
                    help="pytest --durations=0 output (default: stdin)")
    args = ap.parse_args(argv)
    text = (pathlib.Path(args.src).read_text() if args.src
            else sys.stdin.read())
    weights = build_weights(parse_durations(text))
    if not any(w > FLOOR_S for w in weights.values()):
        print("error: no duration lines parsed -- was the input a "
              "`pytest --durations=0` report?", file=sys.stderr)
        return 1
    OUT.write_text(json.dumps(weights, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(_ROOT)} ({len(weights)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

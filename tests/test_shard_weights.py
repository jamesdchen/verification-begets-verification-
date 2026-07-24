"""Teeth for the duration-balanced pytest sharding (run_regression
`_pytest_shard` + `ci/pytest_shard_weights.json`).

The load-bearing invariant: WHATEVER the weights file contains -- fresh,
stale, missing, or garbage -- the n shards are an EXACT partition of the
test files (disjoint, complete, deterministic).  Weights may only ever move
seconds between shards, never a test out of the gate.
"""
import importlib.util
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _harness():
    spec = importlib.util.spec_from_file_location(
        "run_regression", _ROOT / "run_regression.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_RR = _harness()
_FILES = sorted(str(p.relative_to(_ROOT))
                for p in (_ROOT / "tests").glob("test_*.py"))


def test_shards_partition_exactly_for_all_matrixed_n():
    for n in (2, 3, 4, 6):
        shards = [_RR._pytest_shard(_FILES, i, n) for i in range(n)]
        combined = sorted(f for s in shards for f in s)
        assert combined == _FILES, f"n={n}: shards are not an exact partition"
        assert all(len(s) > 0 for s in shards), f"n={n}: an empty shard"


def test_sharding_is_deterministic():
    for i in range(4):
        a = _RR._pytest_shard(_FILES, i, 4)
        b = _RR._pytest_shard(_FILES, i, 4)
        assert a == b


def test_partition_survives_unknown_and_missing_weights(monkeypatch, tmp_path):
    # files the weights map has never seen still land in exactly one shard
    files = _FILES + ["tests/test_zz_hypothetical_new_file.py"]
    shards = [_RR._pytest_shard(files, i, 4) for i in range(4)]
    assert sorted(f for s in shards for f in s) == sorted(files)

    # a missing weights file falls back to the historical parity split
    monkeypatch.setattr(_RR, "SHARD_WEIGHTS", tmp_path / "absent.json")
    shards = [_RR._pytest_shard(_FILES, i, 4) for i in range(4)]
    assert sorted(f for s in shards for f in s) == _FILES
    parity = [f for i, f in enumerate(_FILES) if i % 4 == 0]
    assert shards[0] == parity

    # garbage weights also fall back, never crash, still partition
    bad = tmp_path / "bad.json"
    bad.write_text("[not a dict]")
    monkeypatch.setattr(_RR, "SHARD_WEIGHTS", bad)
    shards = [_RR._pytest_shard(_FILES, i, 4) for i in range(4)]
    assert sorted(f for s in shards for f in s) == _FILES


def test_committed_weights_are_wellformed_and_current():
    # every key names an EXISTING test file (deleting a test file prunes its
    # weight -- `tools/pytest_shard_weights.py` regenerates), every value is a
    # positive number.  Staleness of the NUMBERS is allowed by design; only
    # dangling keys and malformed rows are teeth.
    weights = json.loads((_ROOT / "ci" / "pytest_shard_weights.json").read_text())
    assert isinstance(weights, dict) and weights
    for f, w in weights.items():
        assert (_ROOT / f).is_file(), f"weights name a deleted file: {f}"
        assert isinstance(w, (int, float)) and w > 0, (f, w)


def test_weights_tool_roundtrip(tmp_path):
    from tools import pytest_shard_weights as tool
    report = ("12.34s call     tests/test_shard_weights.py::test_x\n"
              "0.50s setup    tests/test_shard_weights.py::test_x\n"
              "not a duration line\n")
    per_file = tool.parse_durations(report)
    assert per_file == {"tests/test_shard_weights.py": 12.84}
    weights = tool.build_weights(per_file)
    assert weights["tests/test_shard_weights.py"] == 12.84
    # unmeasured existing files get the floor, and every existing file appears
    assert set(weights) == set(_FILES)
    assert all(w >= tool.FLOOR_S for w in weights.values())


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if fn.__code__.co_argcount:
                continue            # fixture-taking teeth run under pytest
            fn()
            print("ok", name)

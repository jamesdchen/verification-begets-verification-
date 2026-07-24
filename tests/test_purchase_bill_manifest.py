"""Teeth for the purchase-bill manifest narrower (tools/purchase_bill_manifest.py).

Pure-function coverage only -- the git plumbing is exercised by the CI job;
these teeth pin the judgment logic so it cannot drift silently."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import purchase_bill_manifest as m  # noqa: E402


def test_ceremony_scope_allows_growth_protocol_only():
    ok, touched = m.ceremony_scope([
        "buildloop/growth_protocol.py", "specs/mathsources/registration.json",
        "results/p9_delta.md", "tests/test_operator_growth.py"])
    assert ok and touched == ["buildloop/growth_protocol.py"]


def test_ceremony_scope_rejects_other_ceremony_paths():
    for bad in ("kernel/certs.py", "TRUST.md", "setup.sh",
                "ci/Dockerfile", ".claude/hooks/x.sh",
                ".github/workflows/ci.yml"):
        ok, touched = m.ceremony_scope(["buildloop/growth_protocol.py", bad])
        assert not ok and bad in touched


def test_ceremony_scope_clean_diff_passes():
    ok, touched = m.ceremony_scope(["tools/frontier.py", "results/x.json"])
    assert ok and touched == []


ANTI_SRC = (
    "X = 1\n"
    "ANTI_LIST = (\n"
    '    "kernel checkers", "contract types", "escape-gate blocklist",\n'
    '    "primitive ladder rungs",\n'
    ")\n")


def test_anti_list_extraction_and_equality():
    assert m.extract_anti_list(ANTI_SRC) == (
        "kernel checkers", "contract types", "escape-gate blocklist",
        "primitive ladder rungs")
    grown = ANTI_SRC.replace('"primitive ladder rungs",',
                             '"primitive ladder rungs", "new root",')
    assert m.extract_anti_list(grown) != m.extract_anti_list(ANTI_SRC)


def test_anti_list_absent_is_failure_never_pass():
    try:
        m.extract_anti_list("Y = 2\n")
    except ValueError:
        return
    raise AssertionError("missing ANTI_LIST must raise, never pass")


def test_anti_list_extracts_from_the_real_file():
    root = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(root, "buildloop", "growth_protocol.py")) as fh:
        real = m.extract_anti_list(fh.read())
    assert "escape-gate blocklist" in real and len(real) >= 4


def test_delta_receipt_patterns():
    assert m.has_delta_receipt(["specs/mathsources/registration.json"])
    assert m.has_delta_receipt(["results/p1_delta.md"])
    assert m.has_delta_receipt(["results/p12_bigop_delta.md"])
    assert not m.has_delta_receipt(["results/c3_cycle_03.md", "tools/x.py"])

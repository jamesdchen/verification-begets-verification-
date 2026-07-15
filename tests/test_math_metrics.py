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


def test_preedit_header_capture_is_faithful(tmp_path):
    """The captured baseline equals the export header on a fresh registry.

    On the frozen base this asserts export == PREEDIT_CSV_HEADER exactly; after
    WP-B's append it becomes a prefix (see test_csv_header_appends_math_columns),
    but the frozen substrate constant above never changes."""
    reg = _fresh_registry(tmp_path)
    header = _export_header(reg, tmp_path)
    assert header[: len(PREEDIT_CSV_HEADER)] == PREEDIT_CSV_HEADER

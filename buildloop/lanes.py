"""Resource lanes: crossing a lane's resource class is an ERROR, not a cost.

THE GENERALIZATION of the one guard the repo already trusts: ``CGB_TASK_TIME``
makes any LLM call raise inside ``buildloop/llm.py::call_llm`` -- a tripwire,
not a convention.  That guard protects exactly one lane (the task-time path).
This module makes the same mechanism available to every lane that DECLARES
itself token-free: mining, censuses, recompression sweeps, RT re-validation
-- the cheap CPU pipelines that must never queue behind (or accidentally
bill) the metered chokepoint.  Principle: don't let the expensive resource
gate the cheap pipeline; make the crossing loud.

``token_free(lane_name)`` is a context manager that sets the SAME env flag
``call_llm`` already honors, so no new guard code exists to drift -- one
tripwire, many lanes.  Nesting and restoration are exact; the lane name is
carried in ``CGB_LANE`` purely for error-message and audit clarity.
"""
from __future__ import annotations

import contextlib
import os


@contextlib.contextmanager
def token_free(lane_name: str):
    """Run a block in a token-free lane: any ``call_llm`` inside raises
    ``TaskTimeLLMViolation`` (the existing guard, reused verbatim).  Restores
    both env vars exactly on exit, even on error."""
    prev_guard = os.environ.get("CGB_TASK_TIME")
    prev_lane = os.environ.get("CGB_LANE")
    os.environ["CGB_TASK_TIME"] = "1"
    os.environ["CGB_LANE"] = lane_name
    try:
        yield
    finally:
        if prev_guard is None:
            os.environ.pop("CGB_TASK_TIME", None)
        else:
            os.environ["CGB_TASK_TIME"] = prev_guard
        if prev_lane is None:
            os.environ.pop("CGB_LANE", None)
        else:
            os.environ["CGB_LANE"] = prev_lane


def current_lane() -> str | None:
    """The declared lane name, if any (audit/reporting convenience)."""
    return os.environ.get("CGB_LANE")

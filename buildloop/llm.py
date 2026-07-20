"""LLM client for the build loop -- the ONLY module that may talk to an LLM.

Calls the Anthropic API through the authenticated `claude` CLI in headless
mode (`claude -p --output-format json`).  The JSON result carries token
usage, which feeds the cumulative-cost metric.

A task-time guard makes any call raise while run/ is executing a spec: the
task-time path provably contains no LLM involvement (hard constraint #1).
"""
from __future__ import annotations

import json
import os
import subprocess

import common

DEFAULT_MODEL = os.environ.get("CGB_LLM_MODEL", "claude-opus-4-8")


class TaskTimeLLMViolation(RuntimeError):
    pass


class LLMError(RuntimeError):
    pass


def strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t


def call_llm(prompt: str, model: str = None, timeout: int = 600,
             system_prompt: str = None, no_tools: bool = False) -> dict:
    """-> {"text": str, "input_tokens": int, "output_tokens": int}

    `system_prompt` REPLACES the CLI's default system prompt and `no_tools`
    disallows every tool: a default `claude -p` session carries ~26 ktok of
    system-prompt + tool-schema overhead per call (measured 2026-07-17:
    25,694 cache-creation tokens on a trivial probe vs 164 total with both
    flags set).  Spec-authoring callers that need only text completion pass
    both; legacy callers are byte-for-byte unaffected."""
    if os.environ.get("CGB_TASK_TIME") == "1":
        raise TaskTimeLLMViolation(
            "LLM call attempted on the task-time path -- forbidden")
    model = model or DEFAULT_MODEL
    argv = [common.CLAUDE_CLI, "-p", prompt, "--model", model,
            "--output-format", "json"]
    if system_prompt is not None:
        argv += ["--system-prompt", system_prompt]
    if no_tools:
        argv += ["--disallowedTools", "*"]
    proc = subprocess.run(
        argv,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if proc.returncode != 0:
        raise LLMError(f"claude CLI rc={proc.returncode}: "
                       f"{proc.stderr[-800:].decode(errors='replace')}")
    try:
        out = json.loads(proc.stdout.decode())
    except json.JSONDecodeError as e:
        raise LLMError(f"unparseable CLI output: {e}")
    if out.get("is_error"):
        raise LLMError(f"CLI reported error: {out.get('result', '')[:500]}")
    usage = out.get("usage", {})
    tokens_in = (usage.get("input_tokens", 0)
                 + usage.get("cache_creation_input_tokens", 0)
                 + usage.get("cache_read_input_tokens", 0))
    return {"text": strip_fences(out.get("result", "")),
            "input_tokens": tokens_in,
            "output_tokens": usage.get("output_tokens", 0),
            "model": model}

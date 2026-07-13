"""Shared utilities: canonical hashing, tool paths, event log helpers.

Everything here is deterministic plumbing. No policy decisions live in this
module; the kernel (kernel/) is the only adjudicator.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent
ARTIFACTS = pathlib.Path(os.environ.get("CGB_ARTIFACTS", REPO_ROOT / "artifacts"))
DB_PATH = pathlib.Path(os.environ.get("CGB_DB", str(ARTIFACTS / "registry.sqlite")))

# --- outsourced tool locations (overridable via env) -----------------------
KSC_CLASSPATH = os.environ.get("CGB_KSC_CLASSPATH", "/opt/ksc/lib/*")
KSC_MAIN = "io.kaitai.struct.JavaMain"
JAVA = os.environ.get("CGB_JAVA", "java")
TREE_SITTER = os.environ.get("CGB_TREE_SITTER", "/root/.cargo/bin/tree-sitter")
DAFNY = os.environ.get("CGB_DAFNY", "/root/.dotnet/tools/dafny")
CLAUDE_CLI = os.environ.get("CGB_CLAUDE_CLI", "/opt/node22/bin/claude")
CC = os.environ.get("CGB_CC", "cc")


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj) -> str:
    return sha256_bytes(canonical_json(obj).encode())


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run_cmd(cmd, cwd=None, timeout=300, env=None, input_bytes=None):
    """Run a *trusted tool* (compiler/verifier binary) outside the sandbox.

    Emitted (generated) code must never go through here -- use sandbox.run_sandboxed.
    """
    return subprocess.run(
        cmd,
        cwd=cwd,
        timeout=timeout,
        env=env,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def ensure_dirs():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "events").mkdir(exist_ok=True)
    (ARTIFACTS / "certs").mkdir(exist_ok=True)
    (ARTIFACTS / "out").mkdir(exist_ok=True)

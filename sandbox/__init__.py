"""OS-level sandbox for executing *emitted* (generated) code.

Containment is enforced by the operating system, not by any type system:

  * new network namespace (``unshare --net``): no interfaces, no routes --
    any socket connect fails at the OS level;
  * new mount namespace: tmpfs is mounted over /root, /home and /tmp, so the
    repository, credentials and the rest of the user's files are simply not
    present in the sandbox's view of the filesystem;
  * a fresh scratch directory bind-mounted at /work is the only writable,
    persistent location;
  * new PID namespace with --kill-child: no runaway orphans;
  * the payload runs as uid/gid 65534 (nobody), with a cleared environment
    and rlimits on CPU time, address space and file size.

Every execution of generated code -- during kernel checking and at task
time -- goes through Sandbox.run.  This module is part of the
trusted-by-fiat computing base (see TRUST.md).
"""
from __future__ import annotations

import dataclasses
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

_SANDBOX_UID = 65534
# {ro_mounts}: optional READ-ONLY bind mounts under /ro/<name> (F0.5).  The
# Lean cert path needs the setup-time Mathlib checkout and toolchain visible
# INSIDE the jail (require-by-local-path, ⚠D3) -- they are bound read-only
# BEFORE the tmpfs mounts hide /root and /home, so a source living under
# either stays reachable via its own mount while the payload still cannot see
# (or write) anything else.  With no ro_mounts the block renders empty and the
# jail behaves exactly as before.  NOTE: this template's bytes are folded into
# cage identity (run/guarded.py `_inner_hash`), so ANY edit here is a clean
# cache miss for every cage-conformance certificate -- the designed L2
# behavior, never a stale false-green.
_INNER = r"""
set -e
mount --make-rprivate /
mkdir -p /work 2>/dev/null || true
mount --bind {scratch} /work
{ro_mounts}mount -t tmpfs -o size=1m,mode=755 tmpfs /root
mount -t tmpfs -o size=1m,mode=755 tmpfs /home
mount -t tmpfs -o size=256m,mode=1777 tmpfs /tmp
cd /work
exec setpriv --reuid={uid} --regid={uid} --clear-groups \
  env -i PATH={path} HOME=/work TMPDIR=/tmp {extra_env}\
  bash -c 'ulimit -t {cpu} -v {mem_kb} -f {fsize_kb}; exec "$@"' -- {argv}
"""
_DEFAULT_PATH = "/usr/bin:/bin:/usr/local/bin"
_RO_BLOCK = r"""mkdir -p /ro 2>/dev/null || true
mount -t tmpfs -o size=1m,mode=755 tmpfs /ro
"""
_RO_ENTRY = r"""mkdir -p /ro/{name}
mount --bind {src} /ro/{name}
mount -o remount,bind,ro /ro/{name}
"""


@dataclasses.dataclass
class SandboxResult:
    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def _shq(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


class Sandbox:
    """A scratch directory plus the namespace-jailed way to run things in it."""

    def __init__(self, keep: bool = False, ro_mounts: dict = None):
        """`ro_mounts`: optional {name: host_path} bound READ-ONLY at
        /ro/<name> inside the jail (the Lean cert path's Mathlib checkout +
        toolchain, F0.5/⚠D3).  Names are [a-z0-9_]+ only; a missing source is
        a hard error here, not a silent empty mount inside the jail."""
        base = pathlib.Path(tempfile.mkdtemp(prefix="cgb-sbx-"))
        os.chmod(base, 0o777)  # payload runs as nobody
        self.root = base
        self._keep = keep
        self._ro_mounts = {}
        for name, src in (ro_mounts or {}).items():
            if not re.fullmatch(r"[a-z0-9_]+", name):
                raise ValueError(f"ro_mount name must be [a-z0-9_]+: {name!r}")
            sp = pathlib.Path(src)
            if not sp.exists():
                raise FileNotFoundError(f"ro_mount source missing: {src}")
            self._ro_mounts[name] = str(sp.resolve())

    def add_file(self, relpath: str, content) -> pathlib.Path:
        p = self.root / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content)
        os.chmod(p, 0o666)
        for parent in p.parents:
            if parent == self.root:
                break
            os.chmod(parent, 0o777)
        return p

    def run(self, argv, timeout=120, cpu_seconds=60, mem_mb=1024,
            fsize_mb=32, extra_path=(), extra_env=None) -> SandboxResult:
        """Execute argv inside the jail, cwd=/work (the scratch dir).

        `extra_path`: directories PREPENDED to the jail PATH (e.g. the
        read-only-mounted Lean toolchain's bin).  `extra_env`: extra
        environment entries for the payload (e.g. LEAN_PATH) -- the base
        environment stays cleared (`env -i`) either way."""
        ro = ""
        if self._ro_mounts:
            ro = _RO_BLOCK + "".join(
                _RO_ENTRY.format(name=name, src=_shq(src))
                for name, src in sorted(self._ro_mounts.items()))
        path = ":".join(list(extra_path) + [_DEFAULT_PATH])
        env_extra = "".join(
            f"{k}={_shq(str(v))} " for k, v in sorted((extra_env or {}).items())
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", k))
        script = _INNER.format(
            scratch=_shq(str(self.root)),
            ro_mounts=ro,
            path=path,
            extra_env=env_extra,
            uid=_SANDBOX_UID,
            cpu=cpu_seconds,
            mem_kb=mem_mb * 1024,
            fsize_kb=fsize_mb * 1024,
            argv=" ".join(_shq(a) for a in argv),
        )
        cmd = ["unshare", "--net", "--mount", "--pid", "--fork",
               "--kill-child", "bash", "-c", script]
        try:
            proc = subprocess.run(cmd, timeout=timeout,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return SandboxResult(proc.returncode, proc.stdout, proc.stderr, False)
        except subprocess.TimeoutExpired as e:
            return SandboxResult(-1, e.stdout or b"", e.stderr or b"", True)

    def read(self, relpath: str) -> bytes:
        return (self.root / relpath).read_bytes()

    def exists(self, relpath: str) -> bool:
        return (self.root / relpath).exists()

    def close(self):
        if not self._keep:
            shutil.rmtree(self.root, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

import os
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Skip-with-reason for EXTERNAL-toolchain tests (the X7 discipline, repo-wide).
#
# The CI `fast` job installs every outsourced checker (Dafny, Kaitai, the
# flloat closure in the SYSTEM interpreter the sandbox uses), so nothing skips
# there and the gate keeps its full strength.  A thin dev environment (e.g. a
# cloud container without dotnet/maven) previously showed these as FAILURES,
# which buried real regressions in known-red noise; they now skip with a
# reason naming the missing tool.  Probes run once per session.
# ---------------------------------------------------------------------------

_SBX = "sandbox-python-deps (hypothesis/pydantic/flloat in /usr/bin/python3)"


def _probe_dafny() -> bool:
    import common
    return bool(shutil.which("dafny") or pathlib.Path(common.DAFNY).exists())


def _probe_ksc() -> bool:
    import glob
    import common
    return bool(glob.glob(common.KSC_CLASSPATH.replace("*", "*.jar"))
                or glob.glob("/opt/ksc/lib/*.jar"))


def _probe_matplotlib() -> bool:
    """F-INT (WP-G/G2): the plot-rendering test files import matplotlib.  The CI
    toolchain image bakes it in (ci/Dockerfile), so nothing skips there; a thin
    dev environment without matplotlib skips-with-reason instead of ImportError
    (the X7 discipline, mirroring the dafny/kaitai probes)."""
    try:
        import matplotlib  # noqa: F401
        return True
    except Exception:
        return False


def _probe_sandbox_pydeps() -> bool:
    """The sandbox runs payloads under /usr/bin/python3 as nobody with a
    CLEARED env (HOME=/work), so venv- or user-site-installed libs are
    invisible there.  Approximate that view: system interpreter, env -i."""
    try:
        r = subprocess.run(
            ["env", "-i", "HOME=/nonexistent", "/usr/bin/python3", "-c",
             "import hypothesis, pydantic, flloat"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        return r.returncode == 0
    except Exception:
        return False


_PROBES = {
    "dafny": _probe_dafny,
    "kaitai-struct-compiler": _probe_ksc,
    "matplotlib": _probe_matplotlib,
    _SBX: _probe_sandbox_pydeps,
}

# test file -> the external tools its channels execute.  Coarse-grained by
# design: a file skips only when a tool it NEEDS is absent; CI has them all.
_FILE_REQUIREMENTS = {
    # F-INT (WP-G/G2): the plot-exercising math test files (WP-D bench, WP-B
    # metrics curve) render via matplotlib -> skip-with-reason in thin envs.
    "test_bench_formalize.py": ["matplotlib"],
    "test_math_metrics.py": ["matplotlib"],
    "test_cage_teeth.py": [_SBX],
    # invariants' task-time determinism walks the generator kinds, which
    # emits a ksy codec through the outsourced compiler -- both tools needed
    # (surfaced when the SessionStart hook closed the sandbox-pydeps gap in
    # web containers, un-skipping the file into a half-present toolchain).
    "test_invariants.py": ["kaitai-struct-compiler", _SBX],
    "test_monitor_gen.py": [_SBX],
    "test_pass_certs.py": ["dafny", _SBX],
    "test_promote_translation.py": [_SBX],
    "test_rung.py": [_SBX],
    "test_run_abnf_stage.py": ["kaitai-struct-compiler", _SBX],
    "test_temporal_teeth.py": [_SBX],
    "test_toll_meter.py": [_SBX],
    "test_translation_abnf.py": ["kaitai-struct-compiler", _SBX],
}

_probe_cache: dict = {}


def _missing_for(fname: str) -> list:
    out = []
    for tool in _FILE_REQUIREMENTS.get(fname, ()):
        if tool not in _probe_cache:
            _probe_cache[tool] = _PROBES[tool]()
        if not _probe_cache[tool]:
            out.append(tool)
    return out


def pytest_collection_modifyitems(config, items):
    import pytest
    for item in items:
        missing = _missing_for(pathlib.Path(str(item.fspath)).name)
        if missing:
            item.add_marker(pytest.mark.skip(
                reason="external-tool absent: " + ", ".join(missing)))

"""The Lean positive-path plumbing: sandbox ro-mounts, pp_roundtrip, real pin.

These are the pieces that make a REAL toolchain run possible (the 'proper fix'
after the in-container work): the read-only jail mounts (without which the
local-path `require` can never resolve), the ⚠D6 pp.all round-trip primitive
(without which channel 1 returns "unknown" even for a true statement), and a
real Mathlib pin (the draft shipped a placeholder).  The mount tests execute
LIVE (the container has root + unshare); the Lean-invoking paths degrade
honestly and are exercised for real by the CI `lean` job.
"""
import os
import pathlib
import tempfile

import pytest

import common
from sandbox import Sandbox
from kernel.backends import LeanBackend


def _ro_src():
    d = pathlib.Path(tempfile.mkdtemp(prefix="romnt-"))
    os.chmod(d, 0o755)
    (d / "pin.txt").write_text("checkout-stand-in\n")
    os.chmod(d / "pin.txt", 0o644)
    return d


# ---------------------------------------------------------- sandbox ro mounts
def test_ro_mount_readable_inside_jail():
    src = _ro_src()
    with Sandbox(ro_mounts={"mathlib": str(src)}) as sb:
        r = sb.run(["cat", "/ro/mathlib/pin.txt"])
        assert r.ok and b"checkout-stand-in" in r.stdout


def test_ro_mount_is_read_only_at_the_fs_level():
    src = _ro_src()
    with Sandbox(ro_mounts={"mathlib": str(src)}) as sb:
        r = sb.run(["bash", "-c", "echo x > /ro/mathlib/evil.txt"])
        assert not r.ok
        assert b"Read-only file system" in r.stderr
    assert not (src / "evil.txt").exists()


def test_default_jail_unchanged_and_net_still_off():
    with Sandbox() as sb:
        r = sb.run(["bash", "-c",
                    "ls /ro 2>/dev/null; ls /home; echo $PATH"])
        out = r.stdout.decode()
        assert "/ro" not in out.splitlines()[0] if out else True
        assert "/usr/bin:/bin:/usr/local/bin" in out
        # network namespace: any connect fails at the OS level.
        r2 = sb.run(["python3", "-c",
                     "import socket; s=socket.socket();"
                     "s.settimeout(2); s.connect(('1.1.1.1', 443))"])
        assert not r2.ok


def test_extra_path_and_env_reach_the_payload():
    src = _ro_src()
    with Sandbox(ro_mounts={"tc": str(src)}) as sb:
        r = sb.run(["bash", "-c", "echo $PATH; echo $LEAN_PATH"],
                   extra_path=("/ro/tc/bin",),
                   extra_env={"LEAN_PATH": "/ro/tc/lib"})
        out = r.stdout.decode()
        assert out.startswith("/ro/tc/bin:")
        assert "/ro/tc/lib" in out


def test_bad_ro_mount_rejected_early():
    with pytest.raises(ValueError):
        Sandbox(ro_mounts={"Bad-Name": "/tmp"})
    with pytest.raises(FileNotFoundError):
        Sandbox(ro_mounts={"x": "/nonexistent/path/xyz"})


# ------------------------------------------------------------- pp_roundtrip
def test_pp_roundtrip_present_and_degrades_honestly():
    be = LeanBackend()
    assert hasattr(be, "pp_roundtrip")
    r = be.pp_roundtrip("theorem t : True := sorry")
    if not common.lean_available():
        assert r.get("unavailable") is True     # honest, never a fake pass
        assert r.get("ok") is False


def test_pp_roundtrip_extracts_theorem_name():
    m = LeanBackend._THEOREM_NAME.search(
        "theorem dvd_self_mul : ∀ (n : Int), (n ∣ n) := sorry")
    assert m and m.group(1) == "dvd_self_mul"


@pytest.mark.skipif(not common.lean_available(),
                    reason="lean toolchain absent")
def test_pp_roundtrip_accepts_true_statement():
    # the real-toolchain positive path (CI lean job): a well-formed statement
    # round-trips under pp.all to a definitionally-equal term.
    be = LeanBackend()
    r = be.pp_roundtrip(
        "theorem cgb_pp_probe : ∀ (n : Int), n ∣ n := sorry")
    assert r.get("ok") is True, r


# ------------------------------------------------------------------ the pin
def test_mathlib_pin_is_a_real_sha_not_the_placeholder():
    assert common.MATHLIB_COMMIT != "a1120f34fbf1c4c0f8e2b3d5c6a7e8f9012a3b4c"
    assert len(common.MATHLIB_COMMIT) == 40
    int(common.MATHLIB_COMMIT, 16)              # 40-hex


def test_toolchain_dirs_are_configured():
    # elan's mangling and the checker dir are derivable + env-overridable.
    assert "leanprover--lean4---v4.15.0" in common.LEAN_TOOLCHAIN_DIR \
        or os.environ.get("CGB_LEAN_TOOLCHAIN_DIR")
    assert common.LEAN4CHECKER_DIR

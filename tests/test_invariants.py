"""Hard-constraint invariants, runnable as a script or under pytest.

- the task-time path is deterministic (byte-identical output on repeat);
- the task-time path performs no LLM call (the guard raises if one is tried);
- the spec-only validator rejects general-purpose code;
- the sandbox blocks network and hides the repo/home.
"""
from __future__ import annotations

import os
import pathlib
import tempfile

import common
from library import Registry
from buildloop import admission
from buildloop.loop import backlog_index


def _fresh_registry_with_seed():
    d = tempfile.mkdtemp(prefix="cgb-test-")
    os.environ["CGB_ARTIFACTS"] = d
    import importlib
    importlib.reload(common)
    from metrics import backlog as backlog_mod
    backlog_mod.generate(pathlib.Path(d) / "backlog")
    reg = Registry(pathlib.Path(d) / "t.sqlite")
    backlog = backlog_index(pathlib.Path(d) / "backlog")
    cand = {
        "name": "kaitai-fixed-uint-be", "spec_language": "ksy",
        "output_language": "python-codec",
        "spec_grammar": {"atoms": ["endian:be", "uint:1", "uint:2",
                                   "uint:4", "uint:8"]},
        "emit_entrypoint": {"kind": "ksc-python-rw"},
        "contract": {"type": "codec-roundtrip"},
        "provenance": {"author": "test", "depth": 1},
    }
    admission.admit(reg, cand, backlog, use_corpus=False)
    return reg, pathlib.Path(d), backlog


def test_task_time_deterministic_and_llm_free():
    reg, d, backlog = _fresh_registry_with_seed()
    import run as runner
    spec = next(s["path"] for s in backlog if s["language"] == "ksy")
    r1 = runner.run_task(reg, spec)
    r2 = runner.run_task(reg, spec)
    assert r1.ok and r2.ok
    assert r1.files == r2.files, "task-time output not deterministic"


def test_llm_guard_blocks_task_time():
    from buildloop import llm
    os.environ["CGB_TASK_TIME"] = "1"
    try:
        raised = False
        try:
            llm.call_llm("hello")
        except llm.TaskTimeLLMViolation:
            raised = True
        assert raised, "LLM call at task time was not blocked"
    finally:
        os.environ.pop("CGB_TASK_TIME", None)


def test_validator_rejects_code():
    from buildloop import validate
    for bad in ('{"name":"x","spec_language":"ksy","grammar_atoms":["uint:1"],'
                '"emitter":"ksc-python-rw","notes":"import os"}',):
        # notes is not an allowed key -> rejected
        raised = False
        try:
            validate.validate_generator_spec(bad)
        except validate.SpecViolation:
            raised = True
        assert raised
    # grammar_js with a function body is rejected
    raised = False
    try:
        validate.validate_grammar_js(
            "module.exports = grammar({rules:{r: $ => { return 1; }}})")
    except validate.SpecViolation:
        raised = True
    assert raised


def test_sandbox_contains():
    from sandbox import Sandbox
    with Sandbox() as sb:
        sb.add_file("p.py",
                    "import socket,os,json\n"
                    "r={}\n"
                    "try:\n"
                    " socket.create_connection(('1.1.1.1',443),timeout=3); r['net']='LEAK'\n"
                    "except Exception: r['net']='blocked'\n"
                    "r['home']=os.path.exists('/home/user')\n"
                    "print(json.dumps(r))\n")
        res = sb.run(["python3", "p.py"], timeout=30)
        import json
        out = json.loads(res.stdout.decode().strip().splitlines()[-1])
        assert out["net"] == "blocked", "sandbox network not blocked"
        assert out["home"] is False, "sandbox did not hide /home/user"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
    print("all invariants hold")

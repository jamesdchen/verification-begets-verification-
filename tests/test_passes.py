"""W6 byte-preserving pass decomposition tests.

Asserts that composing the seven service compiler passes reproduces exactly
the bytes `service_gen.emit_service(model)` produces, and that the pass 5
conditional-emission gate (no obligations -> empty monitor keys, no flloat
import) holds.  The byte-CHANGING parts of W6 (golden regen, per-pass certs,
_EVAL split) are deferred and NOT exercised here."""
import pathlib
import sys

import pytest

from generators import service_model, service_gen, service_passes

SPECS = ["orders", "tickets", "nested_txn"]
SPEC_DIR = pathlib.Path(__file__).resolve().parent.parent / "specs" / "services"


def _model(name):
    return service_model.parse_service_spec((SPEC_DIR / f"{name}.json").read_text())


@pytest.mark.parametrize("name", SPECS)
def test_compose_reproduces_emit_service_bytes(name):
    """compose(ALL_PASSES)(model).files == emit_service(model), byte for byte."""
    m = _model(name)
    expected = service_gen.emit_service(m)
    bundle = service_passes.run_passes(m, service_passes.ALL_PASSES)
    got = bundle["files"]
    assert set(got) == set(expected)
    for k in expected:
        assert got[k] == expected[k], f"{name}:{k} bytes differ"


@pytest.mark.parametrize("name", SPECS)
def test_emit_passes_match_all_passes_files(name):
    """The file-producing subset (EMIT_PASSES) and the full pipeline agree on
    files -- i.e. adversary_golden does not perturb emitted bytes."""
    m = _model(name)
    a = service_passes.run_passes(m, service_passes.EMIT_PASSES)["files"]
    b = service_passes.run_passes(m, service_passes.ALL_PASSES)["files"]
    assert a == b


def test_order_contract_is_data_record():
    """Pass 1 produces the frozen enforcement order as a plain list (its
    certificate obligation is deferred)."""
    m = _model("orders")
    bundle = service_passes.parse_normalize({"model": m})
    assert bundle["order_contract"] == service_passes.ORDER_CONTRACT
    # sequencing precedes schema precedes constraint precedes guard precedes
    # obligation precedes monitor-advance -- the runtime layer order.
    oc = bundle["order_contract"]
    assert oc.index("sequencing") < oc.index("schema") < oc.index("constraint")
    assert oc.index("guard") < oc.index("obligation") < oc.index("monitor-advance")


@pytest.mark.parametrize("name", SPECS)
def test_conditional_emission_no_obligations(name):
    """None of the demo specs declare obligations: pass 5 must yield empty
    monitor keys, emit no MON_ tables, and NOT import flloat."""
    m = _model(name)
    assert not service_gen._obligations(m)  # precondition for these specs
    # flloat must not be pulled in by the no-obligation monitor pass.
    sys.modules.pop("flloat", None)
    bundle = service_passes.run_passes(m, service_passes.EMIT_PASSES)
    assert bundle["monitor"] == {"consts": "", "init": "", "check": "", "adv": ""}
    assert "flloat" not in sys.modules
    src = bundle["files"]["service.py"].decode()
    assert "MON_TABLES" not in src
    assert "TERMINAL_TOOLS" not in src
    assert "self.mon" not in src


def test_stack_conditional_emission():
    """A flat service emits empty stack fragments; the nested one emits the
    call/return machinery (byte-parity discipline, per-feature)."""
    flat = service_passes.run_passes(_model("orders"),
                                     service_passes.EMIT_PASSES)
    assert flat["stack"]["consts"] == ""
    assert flat["stack"]["pre"] == ""
    assert flat["stack"]["state"] == '        self.state = tr["to"]'
    assert "STACK_D" not in flat["files"]["service.py"].decode()

    nested = service_passes.run_passes(_model("nested_txn"),
                                       service_passes.EMIT_PASSES)
    assert nested["stack"]["consts"].startswith("\nSTACK_D")
    assert "STACK_TERMINALS" in nested["files"]["service.py"].decode()

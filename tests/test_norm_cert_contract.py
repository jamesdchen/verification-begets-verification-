"""Wave-1 FI-W1-1 -- the norm-cert contract SCHEMA (COMPRESSION.md §11.9).

Schema-only: there is no producer / `_dispatch` branch yet.  These tests pin the
stanza shape and its refusals (round-trip; missing canonical_form / rung_pipeline;
unknown channel verdicts), the allowed-but-absent status, and anti-drift between
the doc's FI-W1-1 field names and the code.
"""
import os
import re

import pytest

import kernel
from kernel import certs
from kernel.certs import Certificate

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPRESSION = os.path.join(REPO, "COMPRESSION.md")


def _well_formed():
    return certs.make_norm_cert(
        statement_hash="raw-stmt-hash",
        canonical_form_hash="canon-hash",
        rung_pipeline_hash="rung-pipe-hash",
        meta_equivalence_class="arg-perm",
        solver_equivalence="equivalent",
        instance_replay="vacuous-by-symmetry")


def test_well_formed_norm_cert_validates_and_round_trips():
    cert = _well_formed()
    certs.validate_norm_cert(cert)                     # builder already validated
    # subject = the RAW statement hash (store/ledger/audit key on raw bytes).
    assert cert.subject_hash == "raw-stmt-hash"
    claims = dict(cert.claims)
    assert claims["canonical_form"] == "canon-hash"
    assert claims["rung_pipeline"] == "rung-pipe-hash"
    # JSON round-trip (tuples <-> lists) and re-validate; identity preserved.
    rehydrated = Certificate.from_dict(cert.to_dict())
    certs.validate_norm_cert(rehydrated)
    assert rehydrated == cert


def test_channels_are_the_three_fi_w1_1_channels_in_order():
    cert = _well_formed()
    assert [c["backend"] for c in cert.channels] == list(certs.NORM_CERT_CHANNELS)
    assert certs.NORM_CERT_CHANNELS == ("meta_equivalence_class",
                                        "solver_equivalence", "instance_replay")


def test_missing_canonical_form_is_refused():
    cert = _well_formed()
    cert.claims = tuple(c for c in cert.claims if c[0] != "canonical_form")
    with pytest.raises(ValueError, match="canonical_form"):
        certs.validate_norm_cert(cert)


def test_missing_rung_pipeline_is_refused():
    cert = _well_formed()
    cert.claims = tuple(c for c in cert.claims if c[0] != "rung_pipeline")
    with pytest.raises(ValueError, match="rung_pipeline"):
        certs.validate_norm_cert(cert)


@pytest.mark.parametrize("verdict", sorted(certs.NORM_CERT_NOT_LOWERED_VERDICTS))
def test_not_lowered_solver_verdict_mints_no_cert(verdict):
    # The NOT-LOWERED discipline: a norm-cert cannot even be BUILT with these --
    # its existence would falsely assert a lowering that did not happen.
    with pytest.raises(ValueError, match="NOT lowered"):
        certs.make_norm_cert("raw", "canon", "rung", "arg-perm",
                             solver_equivalence=verdict,
                             instance_replay="vacuous-by-symmetry")


def test_unknown_solver_verdict_is_refused():
    with pytest.raises(ValueError, match="solver_equivalence"):
        certs.make_norm_cert("raw", "canon", "rung", "arg-perm",
                             solver_equivalence="probably",
                             instance_replay="vacuous-by-symmetry")


def test_unknown_meta_class_is_refused():
    with pytest.raises(ValueError, match="meta_equivalence_class"):
        certs.make_norm_cert("raw", "canon", "rung", "distributivity",
                             solver_equivalence="equivalent",
                             instance_replay="vacuous-by-symmetry")


def test_unknown_instance_replay_verdict_is_refused():
    with pytest.raises(ValueError, match="instance_replay"):
        certs.make_norm_cert("raw", "canon", "rung", "arg-perm",
                             solver_equivalence="equivalent",
                             instance_replay="load-bearing")


def test_norm_cert_is_schema_only_absent_from_dispatch():
    # allowed-but-absent: pinned type string, no dispatch entry (no producer yet).
    assert certs.NORM_CERT_TYPE == "norm-cert"
    assert "norm-cert" not in kernel.IMPLEMENTED_CONTRACT_TYPES


def _fi_w1_1_text():
    doc = open(COMPRESSION, encoding="utf-8").read()
    m = re.search(r"\*\*FI-W1-1(.*?)\*\*FI-W1-2", doc, re.S)
    assert m, "FI-W1-1 stanza not found in COMPRESSION.md §11.9"
    # collapse line-wrap whitespace so a wrapped "solver\nequivalence" still
    # matches the "solver equivalence" phrase.
    return re.sub(r"\s+", " ", m.group(1))


def test_doc_and_schema_field_names_do_not_drift():
    """Anti-drift: every FI-W1-1 field named in COMPRESSION.md §11.9 appears in
    the certs.py schema, and vice versa for the channel/claim names."""
    sec = _fi_w1_1_text().lower()
    src = open(certs.__file__, encoding="utf-8").read()
    # claims: verbatim `canonical_form` / `rung_pipeline` in BOTH doc and schema.
    for name in ("canonical_form", "rung_pipeline"):
        assert name in sec, f"{name} absent from §11.9 FI-W1-1"
        assert name in src, f"{name} absent from certs.py"
    # channels: the doc's prose name paired to the schema's snake_case field, so
    # neither side can drift without breaking the other.
    for doc_phrase, field in (("meta-equivalence", "meta_equivalence_class"),
                              ("solver equivalence", "solver_equivalence"),
                              ("instance replay", "instance_replay")):
        assert doc_phrase in sec, f"{doc_phrase!r} absent from doc §11.9"
        assert field in src, f"{field} absent from certs.py schema"
    # the schema's own ordered channel tuple must name exactly the three.
    assert certs.NORM_CERT_CHANNELS == ("meta_equivalence_class",
                                        "solver_equivalence", "instance_replay")

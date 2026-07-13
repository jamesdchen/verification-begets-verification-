"""Certificate and ErrorTranscript records (content-hash-bound)."""
from __future__ import annotations

import dataclasses

import common


@dataclasses.dataclass
class Certificate:
    cert_id: str
    kind: str              # emission-check | admission | promotion
    subject_hash: str      # sha256 over the checked artifact bytes
    contract_hash: str
    channels: list         # [{backend, result, detail}] -- the agreeing evidence
    created_at: str

    @staticmethod
    def make(kind, subject_hash, contract_hash, channels):
        body = {"kind": kind, "subject_hash": subject_hash,
                "contract_hash": contract_hash, "channels": channels}
        return Certificate(cert_id=common.sha256_json(body), kind=kind,
                           subject_hash=subject_hash,
                           contract_hash=contract_hash, channels=channels,
                           created_at=common.now_iso())

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ErrorTranscript:
    verdict: str           # "fail" | "disagreement"
    subject_hash: str
    contract_hash: str
    channels: list         # per-channel results incl. the failing one(s)
    failing_input: str     # hex, when a concrete witness exists
    observed: str
    expected: str
    llm_feedback: str      # formatted for the build loop's refinement prompt

    def to_dict(self):
        return dataclasses.asdict(self)


def artifact_hash(files: dict) -> str:
    """sha256 over the sorted (name, bytes) pairs of an emitted artifact."""
    h = []
    for name in sorted(files):
        h.append({"name": name, "sha256": common.sha256_bytes(files[name])})
    return common.sha256_json(h)

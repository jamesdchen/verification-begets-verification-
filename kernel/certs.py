"""Certificate and ErrorTranscript records (content-hash-bound)."""
from __future__ import annotations

import dataclasses

import common

# Bump whenever what a verdict CONTAINS or how an obligation is generated
# changes (e.g. a new hashed field here, or a change to bmc_smtlib output).
# It version-keys the registry cache (kernel.cache_key), so a bump makes every
# older cache entry a clean miss instead of a silently-stale hit.
#   v2 -> v3 (Phase 1): the protocol BMC obligation (bmc_smtlib) now enforces the
#   IDLE DISCIPLINE (act[i]==IDLE => act[i+1]==IDLE, an absorbing idle suffix), so
#   the obligation bytes changed for EVERY protocol; the new per-temporal-demand
#   LTLf obligations were also added.  A bump makes every pre-Phase-1 protocol-,
#   service- and reading-cert cache entry a clean miss instead of a stale hit.
CERTS_VERSION = 3


def _tuplify(x):
    """Recursively turn lists into tuples (JSON round-trips tuples to lists).
    Keeps a rehydrated claims/non_claims value == its freshly-made twin so
    dataclass __eq__ over certificates is stable across DB/cache/fresh."""
    if isinstance(x, (list, tuple)):
        return tuple(_tuplify(e) for e in x)
    return x


@dataclasses.dataclass
class Certificate:
    cert_id: str
    kind: str              # emission-check | admission | promotion
    subject_hash: str      # sha256 over the checked artifact bytes
    contract_hash: str
    channels: list         # [{backend, result, detail}] -- the agreeing evidence
    created_at: str
    # --- honest-tier fields (P0.5.1) ---------------------------------------
    # PLAIN IMMUTABLE DEFAULTS, never dataclasses.field(default_factory=...):
    # a default_factory installs no class attribute, so unpickling a cert that
    # predates the field raises AttributeError on first access; a plain default
    # is a class attribute that the instance falls back to.
    tier: str = ""             # one of the frozen tier vocabulary (TIERS)
    claims: tuple = ()         # what this certificate positively asserts
    non_claims: tuple = ()     # what it explicitly declines to assert

    @staticmethod
    def make(kind, subject_hash, contract_hash, channels,
             tier="", claims=(), non_claims=()):
        claims = tuple(claims)
        non_claims = tuple(non_claims)
        body = {"kind": kind, "subject_hash": subject_hash,
                "contract_hash": contract_hash, "channels": channels,
                "tier": tier, "claims": list(claims),
                "non_claims": list(non_claims)}
        return Certificate(cert_id=common.sha256_json(body), kind=kind,
                           subject_hash=subject_hash,
                           contract_hash=contract_hash, channels=channels,
                           created_at=common.now_iso(),
                           tier=tier, claims=claims, non_claims=non_claims)

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Certificate":
        """Rehydrate from a to_dict() payload (JSON round-trips tuples to
        lists; restore them so field types are stable)."""
        return cls(cert_id=d["cert_id"], kind=d["kind"],
                   subject_hash=d["subject_hash"],
                   contract_hash=d["contract_hash"], channels=d["channels"],
                   created_at=d["created_at"],
                   tier=d.get("tier", ""),
                   claims=_tuplify(d.get("claims", ())),
                   non_claims=_tuplify(d.get("non_claims", ())))


# Frozen tier vocabulary (interface-freeze item 1). Any certificate's tier must
# be one of these; "tier-unclassified" is honest, not a failure.
TIERS = frozenset({
    "universal", "emit-check", "bounded-K", "complete-to-depth(D)",
    "conformance-relative(n)", "monitored", "tier-unclassified",
})


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

    @classmethod
    def from_dict(cls, d: dict) -> "ErrorTranscript":
        return cls(verdict=d["verdict"], subject_hash=d["subject_hash"],
                   contract_hash=d["contract_hash"], channels=d["channels"],
                   failing_input=d["failing_input"], observed=d["observed"],
                   expected=d["expected"], llm_feedback=d["llm_feedback"])


def artifact_hash(files: dict) -> str:
    """sha256 over the sorted (name, bytes) pairs of an emitted artifact."""
    h = []
    for name in sorted(files):
        h.append({"name": name, "sha256": common.sha256_bytes(files[name])})
    return common.sha256_json(h)

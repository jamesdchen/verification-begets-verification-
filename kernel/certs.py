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
#   v3 -> v4 (Phase 2): adjudicate() now threads a contract descriptor's
#   `non_claims` onto the issued certificate (the `monitored`-tier cage declares
#   what it declines to certify), so what a verdict CONTAINS changed.  Existing
#   contracts set no `non_claims` in their cdesc, so their cert_ids are unchanged
#   (non_claims already defaulted to () inside the cert_id body) -- the bump only
#   forces a clean cache re-key.
#   v4 -> v5 (Phase 2 cage teeth): run.guarded.Cage.hash() now folds the
#   independent reference-oracle source (CF3) -- it determines the containment
#   verdict -- so every cage's cage_hash (surfaced in the cage-conformance cdesc
#   and its cert claims) changed.  A bump makes every pre-teeth cage-conformance
#   cache entry a clean miss instead of a stale hit.
#   v5 -> v6 (Phase 1 stranding/monitor soundness): TWO obligation-generation
#   changes.  (1) The protocol stranding query (ltlf_smt.protocol_temporal_solver)
#   is now product DEAD-END reachability over (control state x monitor state),
#   not the gameable "last real action completes the session" query -- so the
#   emitted temporal obligation bytes change for every protocol carrying an
#   `eventually` demand.  (2) The emitted monitor.py now bakes `_LIVE` and
#   redefines pending as "an accepting state is still reachable AND not already
#   permanently-accepting" (a doomed/dead state -- missed `within` deadline,
#   `before` violation -- is no longer pending forever), so monitor.py bytes and
#   thus every monitor-cert subject_hash change.  A bump makes every pre-v6
#   protocol-/service-/monitor-cert cache entry a clean miss instead of a stale
#   hit.
# v7 (Combined-Loop W1/W5.1): the generic `translation-cert` contract type, and
#   `universal-fixed-uint` now stamps tier='universal' onto its cdesc (so
#   promotion tier-routing recognises the verdict) -- both change verdict/cache
#   content, so bump.
# v8 (Combined-Loop W1.3b/W6.3): translation-cert's `fixed-deriver` anchor is now
#   wired (abnf, two Dafny-free channels) -- changes its verdict from honest-fail
#   to a real certificate; and the service reference interpreter is now an
#   INDEPENDENT `_REF_EVAL` (symmetric rule), changing ref_service_source bytes
#   and thus cage/service subject hashes.  Both change verdict/cache content.
# v9 (Combined-Loop W5.1): the `universal-translation` contract type (the second
#   pinned Combined-Loop type) -- new verdict/obligation generation, so bump.
# v10 (FORMALIZATION F0, WP-G): the two Lean proof-assistant contracts land --
#   `statement-cert` (tier `emit-check`) and `proof-cert` (tier `kernel-checked`,
#   the new TIERS entry below).  Both fold the FULL L2 checking apparatus into
#   their cache identity (statement/proof bytes, import set, joint toolchain+
#   Mathlib pin, escape-gate source hash, runner/driver source hash -- F-C / L2 /
#   ⚠T6), so what a verdict CONTAINS and how its obligation is generated is new;
#   bump makes every older entry a clean miss.  Existing contracts set no new
#   fields, so their cert_ids are unchanged -- the bump only forces a clean re-key.
# v11 (Wave-1 FI-W1-1, COMPRESSION.md §11.9): the `norm-cert` contract type lands
#   as SCHEMA ONLY (this stanza + validator, no producer/_dispatch branch yet, per
#   the §11.9 order "in the same commit as the schema, before any producer code").
#   A new contract type is a new thing a verdict can CONTAIN, so bump; existing
#   contracts set none of the new fields, so their cert_ids are unchanged -- the
#   bump only forces a clean cache re-key.
# v12 (Wave-3 FI-KA-4, COMPRESSION.md §12.2): the `exists-anchor-cert` contract
#   type lands -- the ∃-anchor kernel verdict (this stanza + validator + reference
#   builder here, PLUS the _subject_and_cdesc/_dispatch/IMPLEMENTED_CONTRACT_TYPES
#   entries in kernel/__init__.py, ALL in this one commit BEFORE any producer code,
#   the v11 order).  A new contract type is a new thing a verdict can CONTAIN, and
#   its cache identity folds NEW fields (rung "exists-anchor/v1", the shadow
#   {verdict,bound}, the emitter source hash), so a changed emitter/bound/shadow is
#   a clean cache MISS never a stale false-green; so bump.  Existing contracts set
#   none of the new fields, so their cert_ids are unchanged -- the bump only forces
#   a clean cache re-key.
CERTS_VERSION = 12


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
    # complete-to-size(N): W5.1 promotion adjudicated by bounded-exhaustive
    # enumeration to size N -- an honest bounded refusal, never universal.
    "complete-to-size(N)",
    "conformance-relative(n)", "monitored", "tier-unclassified",
    # P5.1 tier-classification: a complete, exact classification of a protocol's
    # CONTROL SKELETON (guards/context/stack excluded) as star-free or not, by two
    # independent algorithms (monoid aperiodicity + counter-free r-cycle search).
    "control-skeleton-star-free", "control-skeleton-not-star-free",
    # FORMALIZATION F0.3 (WP-G, ⚠A9/T5): the `proof-cert` tier -- a Lean statement
    # WITH a kernel-checked proof term whose run-2 (trusted, L5) axiom audit shows
    # NO sorryAx and axioms subset of the standard three.  (statement-cert stays
    # `emit-check`: a `sorry`-placeholder statement is checked, not proved.)
    "kernel-checked",
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


# ===========================================================================
# norm-cert contract (Wave-1 interface freeze FI-W1-1, COMPRESSION.md §11.9).
# ---------------------------------------------------------------------------
# SCHEMA + PRODUCER-WAVE IDENTITY.  The stanza + validator + builder landed in
# the CERTS_VERSION-bump commit with the contract-allowlist entry (the §11.9
# order).  When the PRODUCER landed (buildloop.rung_registry.norm_certs_for_reading,
# WP-T6a-INTEGRATE) the cache identity was wired: `kernel._subject_and_cdesc` now
# has a norm-cert branch that returns `norm_cert_cdesc` (the SHARED cdesc below),
# so a minted cert's `contract_hash` and `kernel.cache_key` agree byte-for-byte.
# A norm-cert is minted DIRECTLY by its producer, never adjudicated through the
# kernel's channel machinery, so it remains deliberately ABSENT from
# `kernel.IMPLEMENTED_CONTRACT_TYPES` and has no `_dispatch` / channel-runner
# branch (test_norm_cert_contract) -- exactly the status of a directly-minted cert.
#
# What a norm-cert ASSERTS: the RAW statement was LOWERED to a canonical form and
# the two are EQUIVALENT.  The subject stays the RAW statement's hash -- the
# store, ledger and audit chain keep keying on raw bytes; the canonical form is a
# VIEW carried in `claims`, never the identity (FI-W1-2).  A norm-cert's very
# EXISTENCE is the assertion that the lowering happened; a statement the solver
# channel leaves unlowered gets NO norm-cert (see NORM_CERT_NOT_LOWERED_VERDICTS).
#
# Contrast with the W5.2 `translation-cert`, whose channel-1 is compile-hash
# IDENTITY of high-spec and reference lowering: a norm-cert CANNOT anchor on byte
# identity, because canonicalization rewrites the bytes BY DESIGN (raw and canon
# hash differently).  Channel 1 is instead a syntactic-CLASS argument -- the
# rewrite lies wholly in an argued-safe meta-equivalence class -- not an identity.
NORM_CERT_TYPE = "norm-cert"

# The three channels, in the frozen FI-W1-1 order; each is one Certificate
# .channels entry keyed by `backend` == the channel name.
NORM_CERT_CHANNELS = ("meta_equivalence_class", "solver_equivalence",
                      "instance_replay")

# Channel 1 -- meta_equivalence_class: the argued-safe syntactic class the whole
# raw->canon rewrite inhabits, NAMED in the cert.  The pilot admits exactly:
#   "arg-perm"        -- argument permutations of a commutative op in {+,*,and,or,=,!=}
#   "same-op-flatten" -- flattening a nested same-op child (+(+(a,b),c) -> +(a,b,c))
# Asserting a tag MEANS: every step of the rewrite is a member of this class,
# whose safety is argued ONCE at the class level (not re-proved per certificate).
NORM_CERT_META_CLASSES = frozenset({"arg-perm", "same-op-flatten"})

# Channel 2 -- solver_equivalence: the dual-solver verdict on `raw == canon` over
# the fragment.  A minted norm-cert may carry ONLY the lowered verdict; the
# not-lowered verdicts are the discipline's teeth.
#   NORM_CERT_LOWERED_VERDICT ("equivalent") -- an independent dual-solver check
#     proved raw and canon denote the same predicate/term over the supported
#     fragment.  This is the ONLY verdict a norm-cert may carry.
#   NORM_CERT_NOT_LOWERED_VERDICTS -- unknown/timeout/enum-only mean the fragment
#     does NOT support the check: the statement is NOT lowered, the raw survives,
#     its tier is recorded honestly, and NO norm-cert is minted.  A cert carrying
#     any of these (or any other unknown string) is REFUSED by validate_norm_cert.
NORM_CERT_LOWERED_VERDICT = "equivalent"
NORM_CERT_NOT_LOWERED_VERDICTS = frozenset({"unknown", "timeout", "enum-only"})

# Channel 3 -- instance_replay: corroboration ONLY, recorded and NOT load-bearing.
#   "vacuous-by-symmetry" -- the pilot's permutation/flatten case: the
#     entailed-instance evaluator is symmetric by construction, so replay can
#     never disagree; it is kept as an audit trail, never as a reason to mint.
#   "replayed"            -- instances re-evaluated and agreed (corroboration).
#   "not-run"             -- replay skipped (still recorded, still non-load-bearing).
# Asserting any of these MEANS only "this is what the corroboration channel saw";
# it never carries the certificate on its own.
NORM_CERT_INSTANCE_REPLAY_VERDICTS = frozenset(
    {"vacuous-by-symmetry", "replayed", "not-run"})


def norm_cert_claims(canonical_form_hash, rung_pipeline_hash) -> tuple:
    """The FI-W1-1 `claims` tuple carried on every norm-cert.
    ("canonical_form", h) MEANS: the raw statement's canonical VIEW hashes to h.
    ("rung_pipeline", h) MEANS: that view was produced by the rung pipeline whose
    composition hashes to h (the FI-W1-2 identity; supplied by the future producer
    -- the multi-rung joint-fixpoint hash is not yet computed in kernel/rung.py)."""
    return (("canonical_form", canonical_form_hash),
            ("rung_pipeline", rung_pipeline_hash))


def norm_cert_cdesc(canonical_form_hash, rung_pipeline_hash,
                    meta_equivalence_class) -> dict:
    """The content-addressed contract descriptor of a norm-cert -- the SINGLE
    source of truth for its cache identity (schema reviewer's advisory, §11.9).

    `make_norm_cert` hashes this into the cert's `contract_hash`, and
    `kernel._subject_and_cdesc`'s norm-cert branch returns the SAME dict, so
    `kernel.cache_key` for a norm-cert reproduces a minted cert's contract_hash
    byte-for-byte -- the producer and the kernel identity can never drift.  A
    changed canonicalizer (canonical_form / rung_pipeline) or a changed
    meta-class is a clean cache MISS, never a stale false-green (FI-W1-2)."""
    return {"type": NORM_CERT_TYPE,
            "canonical_form": canonical_form_hash,
            "rung_pipeline": rung_pipeline_hash,
            "meta_equivalence_class": meta_equivalence_class,
            "tier": "emit-check",
            "claims": list(norm_cert_claims(canonical_form_hash,
                                            rung_pipeline_hash))}


def validate_norm_cert(cert: "Certificate") -> None:
    """Validate a Certificate against the norm-cert schema (FI-W1-1).  Raises
    ValueError on any violation; returns None when well-formed.  SCHEMA-level
    only -- checks SHAPE and the channel vocabularies, not the solver run."""
    if not cert.subject_hash:
        raise ValueError("norm-cert: empty subject_hash (must be the RAW "
                         "statement's hash -- store/ledger key on raw bytes)")
    claims = dict(cert.claims)
    if "canonical_form" not in claims:
        raise ValueError("norm-cert: claims missing canonical_form")
    if "rung_pipeline" not in claims:
        raise ValueError("norm-cert: claims missing rung_pipeline")
    names = tuple(c["backend"] for c in cert.channels)
    if names != NORM_CERT_CHANNELS:
        raise ValueError(f"norm-cert: channels must be {NORM_CERT_CHANNELS} in "
                         f"order, got {names}")
    result = {c["backend"]: c["result"] for c in cert.channels}
    mec = result["meta_equivalence_class"]
    if mec not in NORM_CERT_META_CLASSES:
        raise ValueError(f"norm-cert: unknown meta_equivalence_class {mec!r}")
    sv = result["solver_equivalence"]
    if sv in NORM_CERT_NOT_LOWERED_VERDICTS:
        raise ValueError(f"norm-cert: solver_equivalence {sv!r} means NOT lowered "
                         "-- no norm-cert may be minted for an unlowered statement")
    if sv != NORM_CERT_LOWERED_VERDICT:
        raise ValueError(f"norm-cert: unknown solver_equivalence verdict {sv!r}")
    ir = result["instance_replay"]
    if ir not in NORM_CERT_INSTANCE_REPLAY_VERDICTS:
        raise ValueError(f"norm-cert: unknown instance_replay verdict {ir!r}")


def make_norm_cert(statement_hash, canonical_form_hash, rung_pipeline_hash,
                   meta_equivalence_class,
                   solver_equivalence=NORM_CERT_LOWERED_VERDICT,
                   instance_replay="vacuous-by-symmetry") -> "Certificate":
    """Build a validated norm-cert Certificate (the schema's reference builder;
    the future producer will construct the same shape from its channel runs).
    `subject_hash` = the RAW statement hash.  Folds the canon + rung-pipeline
    identity into the cdesc so a changed canonicalizer is a clean cache miss,
    then validates; a malformed norm-cert raises before it can acquire an id."""
    channels = [
        {"backend": "meta_equivalence_class", "result": meta_equivalence_class,
         "detail": "the raw->canon rewrite lies wholly in this argued-safe "
                   "syntactic class (no byte-identity anchor: canonicalization "
                   "changes the bytes by design)"},
        {"backend": "solver_equivalence", "result": solver_equivalence,
         "detail": "dual-solver proof raw == canon over the supported fragment; "
                   "unknown/timeout/enum-only would mean NOT lowered and no cert"},
        {"backend": "instance_replay", "result": instance_replay,
         "detail": "entailed-instance corroboration, recorded not load-bearing "
                   "(vacuous-by-symmetry for permutation/flatten rewrites)"},
    ]
    claims = norm_cert_claims(canonical_form_hash, rung_pipeline_hash)
    # cdesc: the content-addressed identity kernel._subject_and_cdesc's norm-cert
    # branch folds into the cache key.  Built by the SHARED norm_cert_cdesc helper
    # so the producer's contract_hash and the kernel's cache_key never drift
    # (schema reviewer's advisory, §11.9 -- one source of truth).
    cdesc = norm_cert_cdesc(canonical_form_hash, rung_pipeline_hash,
                            meta_equivalence_class)
    contract_hash = common.sha256_json(cdesc)
    non_claims = (
        ("instance_replay_non_load_bearing",
         "channel 3 is corroboration only; for permutation/flatten rewrites the "
         "evaluator is symmetric so replay is vacuous-by-symmetry and never mints"),
        ("class_level_safety",
         "the meta-equivalence class's safety is argued ONCE at the class level, "
         "not re-proved per certificate"),
        ("no_byte_identity_anchor",
         "unlike translation-cert's channel-1, raw and canon are NOT compile-hash "
         "identical (canonicalization rewrites the bytes); equivalence is argued "
         "by class membership + dual solver, not identity"),
    )
    cert = Certificate.make(kind="admission", subject_hash=statement_hash,
                            contract_hash=contract_hash, channels=channels,
                            tier="emit-check", claims=claims,
                            non_claims=non_claims)
    validate_norm_cert(cert)
    return cert


# ===========================================================================
# exists-anchor-cert contract (Wave-3 interface freeze FI-KA-4, COMPRESSION.md
# §12.2). SCHEMA + PRODUCER-WAVE IDENTITY.
# ---------------------------------------------------------------------------
# The ∃-anchor kernel verdict.  An emitter (FI-KA-1, generators/math_witness.py)
# AUTHORS a proof term from a found witness; the kernel CHECKS it (the only thing
# the elaborate-then-kernel-check seam can honestly certify an ∃ with).  This
# stanza + `validate_anchor_cert` + `make_anchor_cert` landed in the
# CERTS_VERSION 11->12 bump commit alongside the kernel/__init__.py
# `_subject_and_cdesc` / `_dispatch` / IMPLEMENTED_CONTRACT_TYPES entries and the
# contract-allowlist pin -- the §11.9/§12.2 order (schema before any producer).
#
# What an exists-anchor-cert ASSERTS: at lattice point `kernel-proved`, an
# emitted witness proof for the RAW ∃ statement was KERNEL-CHECKED (two-run L5
# audit: no sorryAx, axioms subset of the standard three, pp.all round-trip
# def-eq) AND corroborated by an exhaustive tool-independent template-eval replay.
# A Certificate is a POSITIVE assertion; the other four lattice points
# (shadow-certified / shadow-edge-refused / kernel-failed / divergent) live in the
# reported artifact + events, NEVER as certs -- `validate_anchor_cert` refuses any
# `lattice_point != "kernel-proved"` (refuse-by-construction, FI-KA-4 tooth 5).
#
# The SUBJECT is the RAW `:= sorry` statement's sha256 -- IDENTICAL to the
# statement-cert subject (the v11 raw-statement rule), so anchor verdicts join
# statement-certs and the store/ledger/audit chain on ONE key.  The proof term is
# EVIDENCE, never identity.  When `shadow_verdict == "refuted"` the cert IS the
# §7.2 permanent-differential record: the bounded shadow refutes only the *bounded*
# claim (source 43's box-edge honesty), which never contradicts the unbounded
# theorem the kernel proved -- so the shadow rides in `claims`, honestly labelled,
# and deliberately NOT as a channel result (a fail-class channel would make
# adjudicate() refuse the mint; the 43 cert MUST be mintable with shadow refuted,
# FI-KA-4 tooth 2).
ANCHOR_CERT_TYPE = "exists-anchor-cert"

# The fixed rung of this channel (folds into the cache identity, never the proof
# bytes -- the bound lives in the search + cache KEY, FI-KA-1).
ANCHOR_RUNG = "exists-anchor/v1"

# tier `kernel-checked` (already in the frozen TIERS -- the proof-cert amendment).
ANCHOR_TIER = "kernel-checked"

# The FIVE frozen verdict-lattice points (FI-KA-2).  B1 CONSUMES these strings
# (frozen in the spec), it does NOT import kernel.verdict_lattice (B2's module).
ANCHOR_LATTICE_POINTS = ("kernel-proved", "shadow-certified",
                         "shadow-edge-refused", "kernel-failed", "divergent")
# The ONLY point that mints a cert: certificates are positive assertions.
ANCHOR_MINTABLE_LATTICE_POINT = "kernel-proved"

# The bounded shadow's three verdicts (recomputed fresh at the pipeline bound;
# `refuted` is the honest box-edge refusal, e.g. source 43).
ANCHOR_SHADOW_VERDICTS = frozenset({"pass", "refuted", "skip"})

# The two channels, in frozen order.  Channel 1 is byte-for-byte the proof-cert
# kernel leg (two-run L5 audit + pp-roundtrip); channel 2 is the emitter's
# exhaustive template-eval replay (role cross-impl-differential).  The channel
# list is PINNED to exactly these two: the shadow verdict is NOT a channel.
ANCHOR_CERT_CHANNELS = ("lean-elaborate+lean4checker", "template-eval-replay")

# The `eval_props` discharge ladder (frozen order, FI-KA-1): the tactic that
# closed the emitted proof rides in claims as `discharge`.  native_decide is
# escape-gate-forbidden and never appears.
ANCHOR_DISCHARGE_RUNGS = ("decide", "omega", "norm_num", "simp")


def anchor_cert_claims(*, statement_hash, template_hash, discharge,
                       shadow_verdict, shadow_bound, axioms=(),
                       lattice_point=ANCHOR_MINTABLE_LATTICE_POINT) -> tuple:
    """The FI-KA-4 `claims` tuple carried on every exists-anchor-cert (frozen
    order).  `("statement_hash", subject)` is the raw-statement join key;
    `("lattice_point", "kernel-proved")` is the ONLY point a cert exists at;
    `("witness_template", h)` is the emitted template's hash; `("discharge", t)`
    names the closing tactic; `("shadow_verdict", v)`+`("shadow_bound", B)` carry
    the bounded shadow honestly (NOT as a channel) -- when v == "refuted" the cert
    IS the permanent-differential record."""
    return (("statement_hash", statement_hash),
            ("lattice_point", lattice_point),
            ("witness_template", template_hash),
            ("discharge", discharge),
            ("shadow_verdict", shadow_verdict),
            ("shadow_bound", shadow_bound),
            ("axioms", tuple(sorted(axioms))),
            ("kernel_checked", True))


def anchor_cert_non_claims() -> tuple:
    """The FI-KA-4 `non_claims` tuple (frozen).  Includes the REPORTED-FIRST
    `dl_pricing` non-claim (the wave-3 DL law, §12.9): a kernel verdict prices
    nothing in wave 3."""
    return (
        ("fidelity_to_text",
         "the proof is kernel-checked against the sorry'd STATEMENT; fidelity of"
         " that statement to the source text is the statement-cert's gates (F2.1"
         " non-vacuity + F2.2 entailed instances), NOT this certificate (⚠T10)"),
        ("shadow_agreement",
         "the bounded shadow's refutation at the box edge is recorded, not"
         " overruled; it remains the permanent differential channel"),
        ("dl_pricing",
         "REPORTED-FIRST: this verdict prices nothing; no DL, coverage, census or"
         " admission surface reads it in wave 3 (§12.9)"),
        ("novelty",
         "the statement's mathematical importance or novelty is NOT judged"),
        ("kernel_independence",
         "channel 1 is `kernel-family` -- lean4checker links Lean's OWN kernel,"
         " not an independent reimplementation (⚠D6/L4), weaker than Z3-vs-CVC5;"
         " the disjoint evidence is the exhaustive template-eval replay (channel"
         " 2), NOT two kernel-family passes (⚠T3)"),
    )


def anchor_cert_cdesc(*, statement_hash, proof_sha, template_hash, discharge,
                      shadow_verdict, shadow_bound, emitter_hash, axioms=(),
                      import_set=None, mathlib_commit=None, toolchain=None,
                      independence="kernel-family",
                      lattice_point=ANCHOR_MINTABLE_LATTICE_POINT) -> dict:
    """The content-addressed contract descriptor of an exists-anchor-cert -- the
    SINGLE source of truth for its cache identity (schema reviewer's advisory,
    §11.9).  `make_anchor_cert` hashes this into the cert's `contract_hash`, and
    `kernel._subject_and_cdesc`'s exists-anchor branch returns the SAME dict, so
    `kernel.cache_key` reproduces a minted cert's contract_hash byte-for-byte --
    producer and kernel identity can never drift (FI-KA-4 tooth 6).

    Folds the FULL statement/proof-cert L2 apparatus (`lean_text_hash` == the
    statement bytes' sha == the subject; `proof_sha` == statement+proof bytes;
    import set; joint toolchain+Mathlib pin; escape-gate source hash; runner/driver
    sha) PLUS the v12 additions: `rung` "exists-anchor/v1", the `shadow`
    {verdict,bound}, and `emitter_hash` (the FI-KA-1 emitter source sha).  A
    changed emitter, search bound, or shadow verdict is therefore a clean cache
    MISS, never a stale false-green.  This is where B lives: the bound is cache
    KEY, never statement bytes (the v11 precedent -- the ∃ fidelity channel
    already declares "bound": B as data)."""
    from kernel.backends import LeanBackend as _LB     # lazy: no import cycle
    cdesc = {
        "type": ANCHOR_CERT_TYPE,
        # lean_text_hash == the statement's sha == the SUBJECT (the raw `:= sorry`
        # bytes); the proof bytes ride in proof_sha, never the identity.
        "lean_text_hash": statement_hash,
        "proof_sha": proof_sha,
        "import_set": sorted(import_set or common.MATHLIB_IMPORTS),
        "toolchain_hash": common.lean_toolchain_hash(),
        "mathlib_commit": mathlib_commit or common.MATHLIB_COMMIT,
        "toolchain": toolchain or common.LEAN_TOOLCHAIN,
        "gate_hash": common.validate_lean_hash(),          # F0.4 source hash
        "driver_hash": _LB._driver_hash(),                 # runner/driver sha
        # --- v12 additions (a changed emitter/bound/shadow is a clean miss) ---
        "rung": ANCHOR_RUNG,
        "shadow": {"verdict": shadow_verdict, "bound": shadow_bound},
        "emitter_hash": emitter_hash,
        "tier": ANCHOR_TIER,
        "claims": list(anchor_cert_claims(
            statement_hash=statement_hash, template_hash=template_hash,
            discharge=discharge, shadow_verdict=shadow_verdict,
            shadow_bound=shadow_bound, axioms=axioms,
            lattice_point=lattice_point)),
        "non_claims": list(anchor_cert_non_claims()),
    }
    return cdesc


def validate_anchor_cert(cert: "Certificate") -> None:
    """Validate a Certificate against the exists-anchor-cert schema (FI-KA-4).
    Raises ValueError on any violation; returns None when well-formed.  SCHEMA
    level -- checks SHAPE, the raw-statement join, the refuse-by-construction
    lattice-point rule, and the pinned channel list, not the Lean run (the v11
    Lean-free precedent: schema + refuse-by-construction + subject-join teeth run
    without a toolchain)."""
    if not cert.subject_hash:
        raise ValueError("exists-anchor-cert: empty subject_hash (must be the RAW "
                         "sorry'd-statement sha256 -- store/ledger key on raw bytes)")
    claims = dict(cert.claims)
    for req in ("statement_hash", "lattice_point", "witness_template",
                "discharge", "shadow_verdict", "shadow_bound", "axioms",
                "kernel_checked"):
        if req not in claims:
            raise ValueError(f"exists-anchor-cert: claims missing {req}")
    # FI-KA-4 tooth 1: subject = the RAW sorry'd-statement sha, IDENTICAL to the
    # statement-cert subject -- it MUST equal the statement_hash claim, never the
    # proof hash (the proof term is evidence, never identity).
    if cert.subject_hash != claims["statement_hash"]:
        raise ValueError(
            "exists-anchor-cert: subject_hash must equal the statement_hash claim "
            "(the raw sorry'd-statement sha; the proof term is evidence, never "
            "identity -- the v11 raw-statement join rule)")
    # FI-KA-4 tooth 5: refuse-by-construction.  A Certificate is a POSITIVE
    # assertion, minted ONLY at kernel-proved; E/F/D points are reported, never
    # certified.
    if claims["lattice_point"] not in ANCHOR_LATTICE_POINTS:
        raise ValueError(
            f"exists-anchor-cert: unknown lattice_point {claims['lattice_point']!r}")
    if claims["lattice_point"] != ANCHOR_MINTABLE_LATTICE_POINT:
        raise ValueError(
            f"exists-anchor-cert: lattice_point {claims['lattice_point']!r} != "
            f"{ANCHOR_MINTABLE_LATTICE_POINT!r} -- only kernel-proved mints a cert; "
            "shadow-certified / shadow-edge-refused / kernel-failed / divergent are "
            "REPORTED (artifact + events), never certified")
    if claims["shadow_verdict"] not in ANCHOR_SHADOW_VERDICTS:
        raise ValueError(
            f"exists-anchor-cert: unknown shadow_verdict "
            f"{claims['shadow_verdict']!r} (must be one of {sorted(ANCHOR_SHADOW_VERDICTS)})")
    if claims["kernel_checked"] is not True:
        raise ValueError("exists-anchor-cert: kernel_checked claim must be True")
    if cert.tier != ANCHOR_TIER:
        raise ValueError(f"exists-anchor-cert: tier must be {ANCHOR_TIER!r}, "
                         f"got {cert.tier!r}")
    # FI-KA-4 tooth 2: the channel list is PINNED to exactly (kernel, template-eval
    # replay), in order.  The shadow verdict deliberately does NOT ride as a
    # channel result -- it rides in claims.  A shadow refutation smuggled onto the
    # channels would make adjudicate() count a fail and the 43 cert could NEVER
    # mint.
    names = tuple(c["backend"] for c in cert.channels)
    if names != ANCHOR_CERT_CHANNELS:
        raise ValueError(
            f"exists-anchor-cert: channels must be {ANCHOR_CERT_CHANNELS} in order "
            "(kernel leg + exhaustive template-eval replay; the shadow verdict is "
            f"NOT a channel), got {names}")


def make_anchor_cert(*, statement_hash, lean_text, template, discharge,
                     shadow_verdict, shadow_bound, emitter_hash, axioms=(),
                     import_set=None, mathlib_commit=None, toolchain=None,
                     independence="kernel-family",
                     lattice_point=ANCHOR_MINTABLE_LATTICE_POINT,
                     kernel_channel=None, template_eval_channel=None
                     ) -> "Certificate":
    """Build a validated exists-anchor-cert Certificate (the schema's reference
    builder; the future B6 runner constructs the SAME shape from its real channel
    runs).  Lean-free by construction: the kernel + template-eval channels default
    to `pass` stubs so the schema + refuse-by-construction + subject-join teeth
    run without a toolchain (the v11 precedent) -- the SOURCE-43 cert (kernel-
    proved, shadow refuted) is mintable here with no Lean present.

    `statement_hash` = subject = the RAW `:= sorry` statement's sha.  `lean_text`
    = the statement+proof bytes (its sha is `proof_sha`).  Folds the emitter/bound/
    shadow identity into the cdesc via the SHARED `anchor_cert_cdesc` helper (so a
    minted cert's contract_hash and `kernel.cache_key` never drift), then
    validates; a malformed anchor cert raises before it can acquire an id."""
    proof_sha = common.sha256_bytes(lean_text.encode())
    template_hash = common.sha256_json(template)
    cdesc = anchor_cert_cdesc(
        statement_hash=statement_hash, proof_sha=proof_sha,
        template_hash=template_hash, discharge=discharge,
        shadow_verdict=shadow_verdict, shadow_bound=shadow_bound,
        emitter_hash=emitter_hash, axioms=axioms, import_set=import_set,
        mathlib_commit=mathlib_commit, toolchain=toolchain,
        independence=independence, lattice_point=lattice_point)
    contract_hash = common.sha256_json(cdesc)
    if kernel_channel is None:
        kernel_channel = {
            "backend": ANCHOR_CERT_CHANNELS[0], "role": "behavioral-witness",
            "independence": independence, "result": "pass",
            "detail": "reference-builder stub: kernel-proved (L5 two-run audit + "
                      "pp-roundtrip) -- the real leg runs in the B6 runner"}
    if template_eval_channel is None:
        template_eval_channel = {
            "backend": ANCHOR_CERT_CHANNELS[1], "role": "cross-impl-differential",
            "result": "pass",
            "detail": "reference-builder stub: exhaustive template-eval replay "
                      "(every admitted outer point, never sampled)"}
    channels = [kernel_channel, template_eval_channel]
    claims = anchor_cert_claims(
        statement_hash=statement_hash, template_hash=template_hash,
        discharge=discharge, shadow_verdict=shadow_verdict,
        shadow_bound=shadow_bound, axioms=axioms, lattice_point=lattice_point)
    cert = Certificate.make(kind="exists-anchor-admission",
                            subject_hash=statement_hash,
                            contract_hash=contract_hash, channels=channels,
                            tier=ANCHOR_TIER, claims=claims,
                            non_claims=anchor_cert_non_claims())
    validate_anchor_cert(cert)
    return cert

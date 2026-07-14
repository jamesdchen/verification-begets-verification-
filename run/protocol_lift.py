"""Task-time protocol lift: learn an incumbent stateful service's protocol as
a Mealy machine (Angluin L*, black-box) and certify it conformance-relative to
a declared state bound n.  ZERO LLM involvement -- this runs under
``common.task_time_guard()`` and never imports the LLM client (buildloop.lstar
does not import buildloop.llm).

Pipeline (all deterministic: same incumbent + abstraction + bound => identical
learned machine and byte-identical protocol spec):

    incumbent (black box)  --L* + W-method(n)-->  Mealy machine
                           --to_protocol_spec-->  protocol spec text
                           --kernel protocol-cert-->  dual BMC + validator<->
                                                       reference-simulator conf.
                           --wrap-->  protocol-lift certificate

The lift REUSES the existing ``protocol-cert`` contract (kernel.check) exactly
as demo_protocol.py does -- the same dual BMC (Z3 & CVC5) plus the emitted
session-validator vs. independent reference-simulator conformance differential.
On top of it we bind a lift certificate that records, in ``claims``, the state
bound n and the declared abstraction map, and in ``non_claims`` the circularity
(the equivalence oracle queries the SAME incumbent that answered membership) --
the honest limit that makes a state deeper than n invisible.
"""
from __future__ import annotations

import dataclasses
import json

import common
import kernel
from kernel.certs import Certificate, artifact_hash
from generators import protocol_model as pm, protocol_gen as pg
from buildloop import lstar


@dataclasses.dataclass
class LiftResult:
    ok: bool
    status: str = ""
    name: str = ""
    machine: object = None
    protocol_spec: str = ""
    files: dict = dataclasses.field(default_factory=dict)
    certificate: dict = dataclasses.field(default_factory=dict)
    protocol_cert: dict = dataclasses.field(default_factory=dict)
    learn_stats: dict = dataclasses.field(default_factory=dict)
    out_dir: str = ""
    error: str = ""


def lift_protocol(incumbent_src, name, abstraction, state_bound_n, *,
                  max_rounds=32, write_output=False, event_sink=None):
    """Learn + certify.  Wrapped in the task-time guard so the whole lift is on
    the provably-LLM-free path."""
    with common.task_time_guard():
        return _lift(incumbent_src, name, abstraction, state_bound_n,
                     max_rounds=max_rounds, write_output=write_output,
                     event_sink=event_sink)


def _lift(incumbent_src, name, abstraction, state_bound_n, *,
          max_rounds, write_output, event_sink):
    alphabet = list(abstraction.keys())
    oracle = lstar.Oracle(incumbent_src, alphabet, abstraction)

    # 1. learn the Mealy machine (determinism is checked inside the oracle) ----
    try:
        res = lstar.learn(oracle, alphabet, state_bound_n, max_rounds=max_rounds)
    except lstar.NondeterministicIncumbent as e:
        # First-class result: L* presupposes a deterministic target.
        return LiftResult(ok=False, status="nondeterministic-incumbent",
                          name=name, error=str(e),
                          learn_stats={"sandbox_runs": oracle.sandbox_runs})
    H = res["machine"]

    # 2. project to a protocol spec and emit the session validator ------------
    spec_text = H.to_protocol_spec(name)
    try:
        model = pm.parse_protocol_spec(spec_text)
    except pm.UnsupportedProtocol as e:
        return LiftResult(ok=False, status="unliftable-protocol", name=name,
                          machine=H, protocol_spec=spec_text,
                          error=f"learned model does not project to a valid "
                                f"protocol: {e}", learn_stats=res)
    K, complete = model.acyclic_bound()
    files = pg.emit_validator(model)

    # 3. REUSE the existing protocol-cert contract (dual BMC + conformance) ----
    verdict = kernel.check(
        {"kind": "protocol-validator", "files": files},
        {"type": "protocol-cert", "spec_text": spec_text},
        event_sink=event_sink)
    certified = isinstance(verdict, Certificate)
    pcert = verdict.to_dict()
    channels = [(c["backend"], c["result"]) for c in pcert["channels"]]

    # 4. bind the lift certificate: what it claims / declines to claim --------
    n = state_bound_n
    lifecycle = [(sym, o) for sym, o, _ in
                 H.lifecycle_path(("login", "pay_big", "ship", "close"))]
    claims = (
        f"conformance-relative(n={n}): the learned Mealy machine was checked "
        f"against the incumbent by Chow's W-method up to {n} states; if the "
        f"incumbent has at most {n} states, the learned protocol is EXACT.",
        f"abstraction map (declared, not inferred): "
        f"{common.canonical_json(abstraction)}",
        f"output alphabet: {list(lstar.KNOWN_OUTPUTS)} plus canonical-JSON hash "
        f"classes; legal protocol transitions are exactly the 'ok' edges.",
        f"the emitted session validator faithfully implements the learned "
        f"protocol: validator-vs-reference-simulator conformance is the "
        f"load-bearing evidence. The dual (Z3 & CVC5) BMC ran at bound K={K} "
        f"({'complete' if complete else 'bounded'}) but is STRUCTURAL ONLY for "
        f"this data-free abstraction -- not a data-safety proof (see non_claims).",
        f"learned {res['num_states']} control states in {res['rounds']} "
        f"equivalence round(s); recovered order lifecycle "
        f"login->pay->ship->close = {[o for _, o in lifecycle]}.",
    )
    non_claims = (
        "CIRCULARITY: the equivalence oracle queries the SAME incumbent that "
        "answered the membership queries. This anchors the model to observed "
        "behaviour only -- it cannot detect an incumbent that lies "
        "consistently, and it gives NO guarantee beyond the declared bound n.",
        f"any incumbent state that is Myhill-Nerode distinguishable only by a "
        f"sequence deeper than the W-method reaches at n={n} is INVISIBLE to "
        f"this certificate (a trapdoor deeper than n is silently missed).",
        "the safety invariant proven by BMC is structural (the abstracted "
        "service carries no data variables); this certificate asserts "
        "sequencing/conformance fidelity, not a data-safety property.",
        "no claim that the incumbent itself is correct -- only that the learned "
        "protocol matches its observable behaviour up to bound n.",
        "RESET is per-query-INSTANCE (a fresh Incumbent() per query line), not "
        "per-process: a batch shares one python process, so an incumbent that "
        "leaks state through module globals or class attributes (violating the "
        "no-globals interface precondition) could corrupt later queries in a "
        "batch. Determinism is double-checked on EVERY batch, but that re-runs "
        "the same order and so cannot catch an order-dependent global leak; such "
        "an incumbent is out of contract (fork-per-reset is the heavier "
        "fallback).",
    )

    lift_cert = {
        "kind": "protocol-lift-certificate",
        "incumbent": name,
        "artifact_hash": artifact_hash(files),
        "protocol_spec_hash": common.sha256_bytes(spec_text.encode()),
        "state_bound_n": n,
        "abstraction_map": abstraction,
        "learned_states": res["num_states"],
        "equivalence_rounds": res["rounds"],
        "counterexamples": res["counterexamples"],
        "protocol_cert": {
            "certified": certified,
            "cert_id": pcert.get("cert_id"),
            "verdict": pcert.get("verdict"),
            "channels": channels,
            "bound_K": K,
            "complete": complete,
        },
        "tier": "conformance-relative(n)",
        "claims": list(claims),
        "non_claims": list(non_claims),
        "learn_stats": {k: res[k] for k in
                        ("sandbox_runs", "membership_queries", "max_batch",
                         "num_experiments", "status")},
        "created_at": common.now_iso(),
    }

    out_dir = ""
    if write_output:
        od = (common.ARTIFACTS / "out" /
              f"protocol-lift-{name}-n{n}-{lift_cert['protocol_spec_hash'][:8]}")
        od.mkdir(parents=True, exist_ok=True)
        for fn, data in files.items():
            (od / fn).write_bytes(data)
        (od / "protocol_spec.json").write_text(spec_text)
        (od / "lift_certificate.json").write_text(json.dumps(lift_cert, indent=2))
        (od / "protocol_cert.json").write_text(json.dumps(pcert, indent=2))
        out_dir = str(od)

    return LiftResult(
        ok=certified, status="certified" if certified else "not-certified",
        name=name, machine=H, protocol_spec=spec_text, files=files,
        certificate=lift_cert, protocol_cert=pcert, learn_stats=res,
        out_dir=out_dir)

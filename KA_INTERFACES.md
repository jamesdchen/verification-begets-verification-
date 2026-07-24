# WP-KA frozen interfaces (FI-KA-1..5) — written before code, per COMPRESSION.md §11.5/§11.9

Produced by the pre-implementation fable sweep (2026-07-17), committed BEFORE any
WP-KA builder starts. Binding for wave 3: builders implement these interfaces
verbatim; deviations require a re-registration commit. See COMPRESSION.md §12.2.

All reading done (COMPRESSION.md §7/§11.5/§11.6/§11.9/§11.10–13/§12, `kernel/certs.py`, `kernel/__init__.py` (dispatch/adjudicate/cache identity), `kernel/backends.py` (LeanBackend), `kernel/rung.py` outline, `generators/math_eval.py`, `generators/math_compile.py`, `run/formalize.py`, `buildloop/validate_lean.py`, `bench/bench_formalize.py` extraction seams, `tools/entropy_refs.py`, `wp_auth_readings.py` source 43, `.github/workflows/ci.yml`, tests layout). Below is the frozen-interfaces spec + failure-mode sweep for WP-KA. Everything cites the repo fact it is anchored to.

---

# WP-KA FROZEN INTERFACES (written before code, per §11.9/§11.5)

**Grounding facts the whole design leans on** (verified in-repo, not assumed):

- The compiled shape for an ∃ reading is `theorem <thm> : ∀ (x:C)…, ∃ (y:C)…, H1 → … → C := sorry` — ∃ segments sit **before** the hypothesis chain (`generators/math_compile.py:236–277`). `statement_hash` = sha256 over `lean_text` bytes only.
- The bounded shadow's scope is `exists_shadow_shape` (∀\*∃\* prefix, ≥1 outer, disjoint sets, hypotheses reference outer only; size guard `EXISTS_SHADOW_MAX_ASSIGNMENTS = 2_000_000`) and its gate is `exists_instances` (exhaustive outer box × full inner product, conservative edge policy) — `generators/math_eval.py:440–645`.
- Source 43 (`∀ n:Int, ∃ m:Int, n < m`) is the committed honest upper-edge refusal: at `n = B = 8` no in-box witness exists (`wp_auth_readings.py:107–118`).
- The only kernel seam is `LeanBackend.{elaborate, recheck, eval_props, pp_roundtrip}` (`kernel/backends.py:567–1010`), consumed through `kernel.check` → `_lean_kernel_channel` (`kernel/__init__.py:811–934`); `proof-cert` dispatch already exists (`expect_sorry=False, forbid_sorry=True`, axioms ⊆ {propext, Classical.choice, Quot.sound}, pp-roundtrip def-eq).
- `adjudicate()` mints a Certificate iff ≥2 channel passes and zero results in {fail, unknown, error} (`kernel/__init__.py:594–640`). So a channel that records a *negative* fact must not ride as a channel `result` on a cert we intend to mint.
- CERTS v11 discipline: new contract type ⇒ `CERTS_VERSION` bump + allowlist entry in the same commit as the schema, **before any producer code**; subject = RAW statement hash; views/evidence ride in `claims`, never the identity (`kernel/certs.py:59–65, 175–348`).
- DL/pricing walks **authored** readings, not certified ones (`tools/entropy_refs.py:73–80`); the `certified` bit keys on `FormalizeResult.ok` and feeds only coverage counts (`bench/bench_formalize.py:485–507`). Both surfaces are what reported-first must leave byte-inert.
- Escape gate blocks `native_decide`, attributes, `#eval/#check/#print`, macros; `by / intro / refine / exact / decide / omega / norm_num / simp` are legal (`buildloop/validate_lean.py`).

---

## FI-KA-1 — Witness-template emitter

**File (frozen):** `generators/math_witness.py` — the *fourth* deterministic translation sibling (compile / smt / eval / **witness**). Pure, Lean-free, LLM-free (E3/L1: nothing here dreams; the emitter is deterministic code and its output is *proposed*, the kernel is the only certifier). Read-only imports allowed: `generators.math_eval` (`exists_shadow_shape`, `hypotheses_of`, `conclusions_of`, `eval_pred`, `eval_term`, `_canonical_assignments`, `_ranges_for`, `EXISTS_SHADOW_MAX_ASSIGNMENTS`), `generators.math_compile` (`_render_term` — import, do not copy, so term rendering can never drift from the compiler). **No edits to either file** (they are T6b/F1 property, not KA's ownership row).

### Scope (input)

`emit_witness_proofs(reading: MathReading, *, bound: int) -> dict`

In scope exactly when `exists_shadow_shape(reading, bound=None)["mode"] == "supported"` — i.e. the bounded shadow's own shape class, which includes both the shadow-certifiable readings (41/42/44-class) **and** the honest edge-refusal class (source 43: shape-supported, gate-refuting). Everything else returns a named honest skip (below). Shape classification uses `bound=None` deliberately: an `exists-domain-too-large` reading is still shape-eligible for the kernel channel; its *search* is what gets the ceiling (next paragraph).

### Witness search (where it lives, and the bound's provenance)

Search **reuses the bounded enumerator**, full-product semantics, never k-smallest:

1. Sweep every hypothesis-admitted outer assignment in the bounded box (`_canonical_assignments(outer, carrier_of, bound)` + `hypotheses_of` filter — byte-identical semantics to `exists_instances`' outer walk). If `n_outer_box × n_inner_box > EXISTS_SHADOW_MAX_ASSIGNMENTS` (reuse the T6b constant read-only; do **not** mint a new ceiling — that would be a tuned constant), return skip `witness-search-domain-too-large`.
2. For each admitted outer point, collect the **full set** of in-bound witness tuples (every inner assignment making the conclusion hold — `itertools.product` over `_ranges_for(exists, …)`, `eval_pred` on the conclusion).
3. **Candidate template family (frozen, v1, data-derived — no tuned constants, E5/H52).** Per ∃-object `y`, a candidate term is an F-G term dict over outer refs and derived constants:
   - `{"lit": c}` where `c` ∈ ⋂ over *witnessed* admitted outer points of {this-position values across that point's witness tuples};
   - `{"ref": x}` for outer `x` such that at every witnessed point some witness tuple has position-`y` equal to `x`'s value;
   - `{"op":"+","args":[{"ref":x},{"lit":c}]}` / `{"op":"-","args":[{"ref":x},{"lit":c}]}` with `c > 0` drawn from ⋂ of the per-point difference sets `{w_y − a(x)}` (resp. `{a(x) − w_y}`);
   - `{"op":"+"|"-"|"*","args":[{"ref":x},{"ref":x'}]}` for outer pairs matching some witness component at every witnessed point.
   Every constant is the intersection of observed data — its provenance is the record, not a menu. Integer division is **excluded** in v1 (Int `ediv` convention hazard; declared limitation — 44 already certifies via the shadow and does not need this channel). Joint candidates = cross product over ∃-objects, ordered canonically by `(sum of term sizes, canonical_json)`; deterministic.
4. **Full-check filter (exhaustive, never sampled):** a candidate survives iff for **every** admitted outer point in the box (including edge points with *no* in-bound witness — this is the point of the channel), substituting the eval'd template values into the conclusion yields True under `eval_pred`. Template values may lie outside the box — `eval_term` is pure-integer, unbounded. For source 43 at B=8: witnessed points n∈[−8,7] give difference-intersection {1}; the survivor `m := n + 1` also passes at the edge point n=8 (m=9, out of box, still True) — the shadow keeps refusing, the emitter proposes.
5. First surviving joint candidate wins (canonical order). None ⇒ honest skip.

**The bound never enters bytes.** `bound` parameterizes the *search* (steps 1–4) and joins provenance + the v12 cache identity (FI-KA-4); the emitted proof bytes contain only reading-derived names and data-derived witness constants. Tooth: for the fixture family, emitting at B=8 and B=12 yields byte-identical proofs; only provenance/cache key differ.

### Output / template grammar (frozen)

On success:

```python
{"status": "emitted",
 "statement_lean_text": <compile_math_reading(reading)["lean_text"]>,   # byte-identical, still `:= sorry`
 "statement_hash": <its sha256>,                                        # the v12 SUBJECT
 "template": {<exists_name>: <F-G term dict>, ...},                     # canonical, hashable
 "proofs": [ {"discharge": rung, "lean_text": <full theorem text>} 
             for rung in ("decide", "omega", "norm_num", "simp") ],     # the eval_props ladder order, frozen
 "search": {"bound": B, "rung": "exists-anchor/v1",
            "n_outer_admitted": ..., "n_witnessed": ..., "candidates_tried": ...}}
```

Each proof text is the compiled statement with `:= sorry` replaced by (exact shape, one tactic per line):

```
:= by
  intro <o1> <o2> …          -- one name per emitted binder, in emitted order (leading-∀ then ∀-segments)
  refine ⟨<t1>, <t2>, …, ?_⟩ -- one component per ∃-bound object, binder order; anonymous constructor
  intro hyp_<id1> hyp_<id2> … -- the hypothesis chain sits AFTER the ∃ binder in the compiled prop (math_compile fact above); omit line when no hypotheses
  <rung>                      -- decide | omega | norm_num | simp
```

Terms rendered by `math_compile._render_term` (identical parenthesization/negative-literal rules). `native_decide` is forbidden by the escape gate and must never appear. The emitter runs `validate_lean` on every emitted text and refuses its own output on gate failure (compile-stage convention, `run/formalize.py:555–562`).

### Honest-skip semantics (frozen vocabulary)

`{"status": "skip", "reason": r}` with `r` ∈ {`no-exists-binder`, `shape-unsupported:<exists_shadow_shape reason>`, `witness-search-domain-too-large`, `no-template-found`}. A skip is **never** a refutation, never mutates the shadow verdict, never surfaces as ok=False anywhere in the fidelity pipeline. "No witness found ⇒ honest skip, never false" (§12.2 item 1).

**Who runs Lean:** not this module. `generators/` stays Lean-free. The runner (`run/anchor.py`, builder B6 below) probes the ladder variants via `LeanBackend.elaborate` (run-1, untrusted preselection only) and submits the first building variant to the **full** `kernel.check` v12 contract (two-run + axiom audit + pp-roundtrip). Untrusted probing + trusted single adjudication = no new trusted surface (§12.9); emitted terms are checked, never trusted because we emitted them.

---

## FI-KA-2 — Verdict lattice

**File (frozen):** `kernel/verdict_lattice.py`. Pure functions, no I/O, no clocks.

### The enum (frozen strings, exactly §12.2's five)

```python
LATTICE_POINTS = ("kernel-proved", "shadow-certified", "shadow-edge-refused",
                  "kernel-failed", "divergent")
```

### Inputs

- `shadow` ∈ {`"pass"`, `"refuted"`, `"skip"`} — recomputed fresh from `math_eval.exists_instances` / `exists_shadow_shape` at the pipeline's bound (never parsed out of a committed CSV), with `refuting_outer` (the witness-less outer assignment) when refuted.
- `kernel` ∈ {`"proved"`, `"failed"`, `"unavailable"`, `"not-attempted"`} — proved iff `kernel.check` on the v12 contract returned a `Certificate`; failed iff it returned an `ErrorTranscript` with the toolchain present; unavailable iff `common.lean_available()` is False; not-attempted iff the emitter skipped.
- `contradiction: bool` — the divergence bit, computed by exactly two triggers (nothing else may set it):
  - **T-a (in-bound-witness contradiction):** kernel proved AND shadow refuted at outer point `o` AND `eval_term` of the accepted template at `o` yields inner values **all inside the bounded box** — the shadow's exhaustive sweep should have found that witness; one of enumerator/evaluator/kernel is wrong.
  - **T-b (decidable-instance mismatch):** during probing, Python `eval_pred` says the fully-instantiated conclusion is True at an admitted point but Lean `decide` on the same closed instance (via `eval_props`) returns a *disproof*/False-class result — the T4 mirror-divergence class surfacing on the kernel channel. (A mere tactic failure to close is NOT T-b.)

### Mapping (total function; frozen)

| shadow \ kernel | proved | failed | unavailable / not-attempted |
|---|---|---|---|
| pass | **kernel-proved** | **kernel-failed** | **shadow-certified** |
| refuted | **kernel-proved** (T-a false) / **divergent** (T-a true) | **kernel-failed** | **shadow-edge-refused** |
| skip | **kernel-proved** | **kernel-failed** | *(no lattice point — no anchor claim exists; honest absence)* |

`contradiction` (T-a or T-b) forces `divergent` from any cell. The critical row: **shadow-refuted × kernel-proved is NOT divergent** — it is the §7.2 permanent differential realized, the package's tooth (source 43). The shadow refutes only the *bounded* claim; that never contradicts the unbounded theorem.

### Partial order and legal transitions

Order (evidence strength): `kernel-failed ⊑ shadow-edge-refused ⊑ shadow-certified ⊑ kernel-proved`; `divergent` is the designated absorbing tripwire, incomparable to the chain. Legal transitions across runs (a "transition" = the point for a subject changing between evaluations; always via a fresh cache key, never mutation of an issued cert):

- `shadow-certified → kernel-proved`, `shadow-edge-refused → kernel-proved` (kernel evidence lands),
- `shadow-* → kernel-failed`, `kernel-failed → kernel-proved` (new template / repaired toolchain),
- any point → `divergent` (a trigger fires),
- **illegal by construction:** `kernel-proved → anything except divergent`; any downward move; `divergent → anything` *by code* (only the human resolution field, FI-KA-3, releases it; the lattice function takes the committed-artifact state as input and returns `divergent` unconditionally while an unresolved artifact exists for the subject).

**Terminal:** `kernel-proved`, `shadow-certified`, `shadow-edge-refused`, `kernel-failed` — honest, reportable end-states for the wave record (the latter three supersedable upward in later runs). **Demands adjudication:** `divergent` only.

The Lean-absent container maps every ∃ reading to the shadow column (S/E) — `unavailable` is never `kernel-failed` (mirrors `_lean_kernel_channel`'s honest `unknown`).

---

## FI-KA-3 — Divergence adjudicator

**File (frozen):** `buildloop/anchor_divergence.py` (the `speculate.log_divergence` precinct — events-only discipline Z1, `tests/test_divergence_ledger.py` is the template). Artifacts commit under **`results/anchor_divergences/`**.

### API

```python
def record_divergence(payload: dict, *, out_dir=RESULTS_DIR, registry=None) -> pathlib.Path
def unresolved_divergence(subject_hash: str, *, out_dir=RESULTS_DIR) -> dict | None
```

`record_divergence` writes `results/anchor_divergences/<subject_hash[:16]>-<n>.json` (append-only: an existing file is never overwritten or deleted; a new divergence for the same subject increments `n`) and, when a registry handle is supplied, logs one first-class event of kind `"anchor-divergence"` (queryable via `registry.events`, creates no cert row and no readings row — the Z1 tooth). Canonical JSON, byte-deterministic, **no wall-clock field in the body** (E6-adjacent; git history carries the time).

### Artifact schema (frozen)

```json
{"schema": "anchor-divergence/v1",
 "subject_hash": "<raw compiled-statement sha256>",
 "source_id": "...",
 "trigger": "in-bound-witness-contradiction" | "decidable-instance-mismatch",
 "shadow": {"verdict": "...", "bound": 8, "refuting_outer": {...}|null, "n_outer_admitted": N},
 "kernel": {"verdict": "...", "cert_id": "...|null", "discharge": "...", "transcript_tail": "..."},
 "template": {"<exists_name>": <F-G term dict>},
 "witness_eval": {"outer": {...}, "template_values": {...}, "in_bound": true, "conclusion_holds_eval": true},
 "identity": {"certs_version": 12, "rung": "exists-anchor/v1",
              "toolchain_hash": "...", "mathlib_commit": "...", "driver_hash": "...", "emitter_hash": "..."},
 "resolution": null}
```

### The no-auto-resolve invariant (three teeth)

1. `resolution` is `null` at write time and **no code path in the repo writes a non-null `resolution`** — a static test greps every `.py` under `kernel/ buildloop/ run/ generators/ tools/` for assignment to that key; only a human commit editing the JSON resolves (fields `{by, date, verdict, note}`; the auditor role of §7).
2. While an unresolved artifact exists for a subject, the lattice function returns `divergent` for it regardless of fresh channel inputs, and **minting any anchor cert for that subject raises** — the divergence check runs *before* mint in the runner, and a test proves order-independence (divergence recorded after a cert attempt still blocks the next mint).
3. No deletion API exists; re-running the pipeline with the divergence "gone" (e.g. after a bound change) does not remove the artifact — recomputation can add artifacts, never subtract.

---

## FI-KA-4 — CERTS v12

**Files:** `kernel/certs.py` (stanza + validator + reference builder), `kernel/__init__.py` (`_subject_and_cdesc` branch, `_dispatch` branch, `IMPLEMENTED_CONTRACT_TYPES` entry), `tests/test_contract_allowlist.py` (pin update) — **all in one commit with the `CERTS_VERSION = 12` bump, before any producer code** (the v11 order, `kernel/certs.py:59–64`).

### The claim kind

New contract type **`"exists-anchor-cert"`**, tier **`"kernel-checked"`** (already in the frozen TIERS). A Certificate of this kind is minted **only** at lattice point `kernel-proved` — certificates are positive assertions; E/F/D points live in the reported artifact and events, never as certs (refuse-by-construction: `validate_anchor_cert` raises on any `lattice_point != "kernel-proved"`).

### Subject / dispatch identity (consistent with v11's raw-statement-hash rule)

- **Subject = the RAW compiled statement's hash** — sha256 over the `:= sorry` `lean_text` bytes, *identical to the statement-cert subject*, so anchor verdicts join statement-certs and the store/ledger/audit chain on one key. The proof term is **evidence, never identity** (the norm-cert precedent: view in claims, not subject).
- **cdesc (cache identity)** folds: `type`, `lean_text_hash` (statement), `proof_sha` (statement+proof bytes), `import_set`, `toolchain_hash`, `mathlib_commit`, `gate_hash`, `driver_hash` (all as in the statement/proof-cert branch, `kernel/__init__.py:435–463`) **plus** `rung: "exists-anchor/v1"`, `shadow: {"verdict", "bound"}`, and `emitter_hash` (sha256 of `generators/math_witness.py` source, the `_driver_hash` pattern) — a changed emitter, bound, or shadow verdict is a clean cache miss, never a stale false-green. This is where B lives: **cache key, never statement bytes** (v11 precedent: the ∃ fidelity channel already declares `"bound": B` as data).
- **`claims` (frozen tuple):** `("statement_hash", subject)`, `("lattice_point", "kernel-proved")`, `("witness_template", sha256_json(template))`, `("discharge", rung)`, `("shadow_verdict", "pass"|"refuted"|"skip")`, `("shadow_bound", B)`, `("axioms", …)`, `("kernel_checked", True)`. When `shadow_verdict == "refuted"`, the cert **is** the permanent-differential record — the §7.2 channel, carried forever on the overlap.
- **v13 amendment (PLAN_REFLECT S4b, maintainer-signed 2026-07-23):** the `discharge` claim's vocabulary is now VALIDATED and pinned to `ANCHOR_DISCHARGE_RUNGS ∪ {"reflection/checkAll_witness"}` (`ANCHOR_LIVE_DISCHARGES`); the full three-route tuple `ANCHOR_REFLECTION_ROUTES` is pinned alongside, with `reflection/checkStmtBox_sound_exOnly` and `reflection/sall_guard_of_check` vocabulary-reserved (refused on this cert kind until their own stanzas land — template-free search and ∀-guard shapes carry different claims). The reflection runner path is incumbent-last in `run/anchor.py::_kernel_leg`: ladder variants first (previously-minting readings mint byte-identically), the FgReflect probe only where the ladder cannot close. Teeth: `tests/test_anchor_reflection_route.py` (route mints, reserved-route + unknown-discharge refusals, ladder/reflection parity join) and the post-ceremony vocabulary pin in `tests/test_reflect_shadow.py`. TRUST.md carries the honestly-labelled entry (FgReflect PROVEN; the quoter/probe glue named as fiat-with-teeth; the shadow pairing permanent).
- **`non_claims` (frozen):** `("fidelity_to_text", …statement-cert's gates, not this cert…)`, `("shadow_agreement", "the bounded shadow's refutation at the box edge is recorded, not overruled; it remains the permanent differential channel")`, `("dl_pricing", "REPORTED-FIRST: this verdict prices nothing; no DL, coverage, census or admission surface reads it in wave 3 (§12.9)")`, `("novelty", …)`, `("kernel_independence", "kernel-family …")`.

### Dispatch (reuses the existing seam only)

```python
if ctype == "exists-anchor-cert":
    ch1 = _lean_kernel_channel(contract["lean_text"],      # statement + emitted proof
                               expect_sorry=False, forbid_sorry=True, contract=contract)
    ch2 = contract["template_eval_channel"]                # role="cross-impl-differential"
    return "exists-anchor-admission", [ch1, ch2]
```

Channel 1 is byte-for-byte the proof-cert kernel leg (two-run L5, axiom audit, pp-roundtrip). Channel 2 is the emitter's exhaustive template-eval replay (`result: "pass"` required — genuinely disjoint tool-independent evidence, satisfying ⚠T3's two-pass rule the same way statement-cert does). The *shadow verdict* deliberately does **not** ride as a channel result: `adjudicate()` refuses any cert carrying a fail-class channel (`kernel/__init__.py:601–604`), and the 43 tooth requires minting *with* shadow refuted — so the shadow rides in claims, honestly labeled, not in the pass/fail calculus.

### Reported-first enforcement — how the DL law grows teeth

New reported artifact: **`results/anchor_report.json`** (built by the B6 runner; deterministic; regeneration joins the re-baseline-coupled artifact set): per ∃-shaped reading `{source_id, subject_hash, lattice_point, shadow, kernel, template?}` + summary counts. This is the only place lattice points aggregate in wave 3.

Teeth (new test `tests/test_anchor_reported_first.py` + a static pin):

1. **Static:** `buildloop/dl.py`, `buildloop/mdl_macros.py`, `buildloop/admission.py`, `bench/bench_formalize.py`, `tools/tower_census.py`, `tools/measure_cluster_key.py` contain no occurrence of `exists-anchor` / `lattice_point` / `anchor_report` (the allowlist-test grep pattern; catches the eager import before it prices anything).
2. **Behavioral (the wave-3 DL law, proved not asserted):** construct a fixture anchor cert for `43_larger_integer_exists` (kernel-proved, shadow refuted — stub channels, no Lean needed since `make`-style reference builder + validator run Lean-free), install it in the registry/artifacts, then recompute (a) `mdl_macros.corpus_dl` over the governed exogenous stream, (b) the bench coverage counters (`certified_exogenous_statements` path — 43 must stay **uncertified**: `FormalizeResult.ok` is untouched by anchors), (c) `results/tower_census.json` bytes, (d) `results/cluster_key_measure.json` bytes — all byte-identical to the anchor-free run. Kernel verdicts change no DL, no coverage, no census, no admission in wave 3; pricing them is a later wave's separately gated decision (§12.9).
3. **Pipeline inertness:** `run/formalize.py` is not edited by this package at all (it is not in KA's ownership row); a byte-identity pin on the committed 40-source frozen run and the 88-record bench prefix stands as-is.

---

## FI-KA-5 — Lean smoke job

**File:** `.github/workflows/ci.yml` — one **additive** job `lean-smoke`; the existing `lean` and `lean-fresh` jobs are untouched.

**Triggers:** `workflow_dispatch`, `schedule`, or push with `[lean-smoke]` OR `[lean-ci]` in the head commit message (the self-serve gate of §12.8; `[lean-ci]` fires both jobs so the current shakeout round exercises the smoke lane for free). **Own** concurrency group `lean-smoke-${{ github.ref }}` (never shared with `lean` — a shared group would cancel one lane with the other). Cache restore + **save-on-failure** copied verbatim from the `lean` job (shakeout must not re-fetch ~5 GB per round). `timeout-minutes: 45`.

**Minimal green means (all asserting, fail-fast):**

1. **Toolchain is actually present:** a first step asserts `common.lean_available()` is True and fails the job otherwise — smoke must never go green by honest degradation (the green-by-skip trap).
2. **The four backend surfaces, one probe each** (the current informational "Diagnostics" step, promoted to asserting): `elaborate('theorem cgb_probe : ∀ (n : Int), n ∣ n := sorry', expect_sorry=True).ok`; `recheck(olean).ok and audited and axioms == ["sorryAx"]`; `eval_props('', ['1 + 1 = 2'])[0]["closed_by"] == "decide"` (decide only — norm_num/simp heartbeat variance stays out of the smoke lane); `pp_roundtrip(stmt).ok`.
3. **Both cert paths the anchor reuses, one statement each:** `kernel.check` issues a `Certificate` for one committed forall reading's statement-cert, and for one fixed trivial proof-cert (`theorem cgb_smoke : ∀ (n : Int), n ∣ n := by intro n; exact dvd_refl n`) with the run-2 audit showing no `sorryAx` and axioms ⊆ the standard three.
4. Nothing else. No test files, no demo.

**Difference from the full `lean` job:** smoke proves the **seam** (toolchain up, all four LeanBackend surfaces live, statement-cert and proof-cert dispatch mint end-to-end) in ~10–15 warm minutes; full proves the **suite** (`test_lean_backend / test_statement_cert / test_formalize_pipeline / test_lean_positive_path` + `demo_formalize`, 120-min budget). **Gate semantics (frozen):** WP-KA builders may *launch* on `lean-smoke` green (the §12.6 artifact = the named check-run on this branch); the first anchor certificate minted against the committed corpus additionally requires the full `lean` job green (§12.2's hard precondition is the user-dispatched job, unchanged — smoke narrows iteration latency, it does not replace the gate).

---

## Failure-mode sweep (what an eager builder gets wrong, and the tooth that catches it)

**FI-KA-1 (emitter)**
1. *Bound in bytes* — witness literal or comment leaks B into the proof (the silent bound-in-bytes class §11.6 killed). Tooth: dual-bound test — emit fixture family at B=8 and B=12, proof bytes identical; `statement_hash` unchanged from `compile_math_reading`; B present in `search` provenance and cache key only.
2. *Trusting the fit* — minting on the Python eval pass ("we already checked it") without the kernel run. Tooth: in the Lean-absent container, assert **no** `exists-anchor-cert` can ever be constructed through the runner (channel 1 is `unknown` ⇒ no Certificate — the existing `_lean_kernel_channel` honesty); only skips/reports appear.
3. *Skip laundered into a verdict* — `no-template-found` surfacing as ok=False, or worse mutating the shadow verdict. Tooth: frozen skip vocabulary test + byte-identity of 43's committed bench row and `formalize_governed.csv` after an emitter run.
4. *k-smallest creep* — sampling admitted outer points in the step-4 full check (the exact single-run/eval_props-class error the original sweep killed). Tooth: planted fixture whose template fits the first shells but fails at a later in-box admitted point — the eval-replay channel must reject it (and therefore channel 2 must be *recomputed exhaustively* in the test, not read from the emitter's own claim).
5. *Tuned constants* — an offset menu `c ∈ {1,2,3}`, a candidate cap, or a fresh size ceiling. Tooth: candidate set for a fixture asserted equal to the derived intersection exactly; the only ceiling in the module is the imported `EXISTS_SHADOW_MAX_ASSIGNMENTS`; review gate flags any numeric literal without record-provenance.
6. *Editing non-owned files* — "just make `_render_term` public" in `math_compile.py`, or a helper added to `math_eval.py`. Tooth: the §12.7 file-ownership row + the T6b byte-order pins already in CI (`test_math_eval_lazy`, `test_math_eval_exists`).
7. *`native_decide` or a decide-with-free-vars discharge* — fast, and either gate-refused or unsound-adjacent. Tooth: escape-gate refusal is already wired (emitter self-validates); ladder is frozen to the four `eval_props` rungs.

**FI-KA-2 (lattice)**
1. *Edge-refusal misread as divergence* — mapping shadow-refuted × kernel-proved to `divergent`. This inverts the package's whole point. Tooth: the source-43 fixture maps to `kernel-proved` with `shadow_verdict="refuted"` on the cert; `divergent` requires trigger T-a/T-b, both concrete and testable.
2. *Kernel failure retracting shadow evidence* — a failed anchor attempt downgrading an already-issued v11 statement-cert or its `exists-finitized-enum` channel. Tooth: committed statement-cert bytes for a shadow-pass ∃ reading identical before/after a failed anchor run.
3. *Auto-resolution* — "kernel wins" logic collapsing `divergent`. Tooth: lattice function's only resolution input is the committed artifact state; stickiness test (FI-KA-3 tooth 2).
4. *Boolean-ization downstream* — a report writing `bool(lattice_point == "kernel-proved")`. Tooth: `anchor_report.json` schema requires the 5-valued field; round-trip test over all five.
5. *`unavailable` conflated with `failed`* — every Lean-free CI run would then report a wall of kernel-failed. Tooth: Lean-absent mapping test (S/E only) in the fast suite.

**FI-KA-3 (adjudicator)**
1. *Registry-only recording* (events but no committed artifact) or scratch-dir artifacts. Tooth: path + canonical-bytes test under `results/anchor_divergences/`.
2. *Re-run erases divergence* — recompute finds no trigger, code deletes the file. Tooth: append-only writer, no delete API, grep tooth on `resolution` writers.
3. *Order dependence* — cert minted first, divergence recorded after, cert survives. Tooth: mint-refuses-on-unresolved test run in both orders.
4. *Wall-clock in the artifact* — `created_at` breaking byte-determinism (and E6 hygiene). Tooth: two writes of the same payload byte-identical.

**FI-KA-4 (CERTS v12)**
1. *Subject = proof hash* — breaks the raw-statement join the ledger keys on (v11's rule). Tooth: validator asserts subject == sorry'd-statement sha; join test against the statement-cert for the same reading.
2. *Shadow verdict as a channel result* — the 43 cert then can never mint (`adjudicate` counts the fail). Tooth: the 43 fixture must mint; the channel list is pinned to exactly (kernel, template-eval-replay).
3. *Producer-before-schema / no version bump* — stale v11 cache entries silently rehydrating as v12 verdicts. Tooth: `test_contract_allowlist` pin + `CERTS_VERSION == 12` assert in the schema test; same-commit rule at the review gate.
4. *The eager "43 certifies now!" move* — coverage/census/DL reading the anchor. Tooth: the three reported-first teeth (static grep + byte-identity behavioral + formalize.py untouched). This is the sweep's headline tooth: **kernel verdicts change no DL in wave 3.**
5. *Certs minted for E/F/D points* — negative facts dressed as certificates. Tooth: `validate_anchor_cert` raises on `lattice_point != "kernel-proved"`.
6. *Cache identity missing emitter/rung/shadow/bound* — a changed emitter silently reusing old verdicts. Tooth: mutate emitter source hash input ⇒ `kernel.cache_key` changes (the norm-cert single-source-of-truth pattern: one shared cdesc helper used by both builder and `_subject_and_cdesc`).

**FI-KA-5 (smoke)**
1. *Green-by-skip* — smoke passes in a toolchain-less runner because every method honest-degrades. Tooth: the `lean_available()` hard assert, step 1.
2. *Smoke asserting flaky surfaces* — norm_num/simp probes under heartbeat variance turn the gate into a coin. Tooth: probes pinned to `decide`-closable facts only.
3. *Shared concurrency group* — smoke cancels the full shakeout run (or vice versa). Tooth: distinct group names, reviewed in the YAML diff.
4. *No cache-save-on-failure* — every shakeout round pays the 5 GB fetch. Tooth: copy the `if: always()` save step; job-time budget assert in review.
5. *Gate conflation* — treating smoke green as the §12.8 precondition and minting on it. Tooth: the frozen gate semantics above (launch on smoke; mint on full), written into the runner's precondition check (it verifies the full job's check-run, the §12.6 artifact-not-prose rule).

---

## Parallelization plan (max width 5 + one serial integrator)

Non-overlapping file DAG (per §12.7's ownership-row-before-builders rule):

| builder | FI | owns (exclusively) | depends on |
|---|---|---|---|
| **B1** | KA-4 | `kernel/certs.py`, `kernel/__init__.py`, `tests/test_contract_allowlist.py`, `tests/test_anchor_cert_contract.py` | this spec only |
| **B2** | KA-2 | `kernel/verdict_lattice.py`, `tests/test_verdict_lattice.py` | this spec only |
| **B3** | KA-1 | `generators/math_witness.py`, `tests/test_math_witness.py` | this spec only (read-only imports of math_eval/math_compile) |
| **B4** | KA-3 | `buildloop/anchor_divergence.py`, `tests/test_anchor_divergence.py`, `results/anchor_divergences/` (.gitkeep) | this spec only |
| **B5** | KA-5 | `.github/workflows/ci.yml` (additive job only) | this spec only |
| **B6** | integration | `run/anchor.py` (runner: shadow recompute → emitter → elaborate-probe ladder → `kernel.check` v12 → lattice → divergence check → `results/anchor_report.json`), `tests/test_anchor_runner.py`, `tests/test_anchor_reported_first.py` | B1–B4 merged; first *mint* additionally gated on full-lean green |

B1–B5 launch simultaneously the moment the smoke/full lean status permits (B2/B3/B4 are Lean-free and can launch **now**; B1 is Lean-free too — schema + refuse-by-construction tests run without a toolchain, the v11 precedent; B5 needs only the YAML). All five interfaces are frozen above, so no cross-talk is needed: B1 consumes the lattice **strings** (frozen here), not B2's module; B3 emits dicts (frozen here), not B1's types. Merge order (for clean CI at each step): **B2 → B1 → B4 → B3 → B5 → B6**. B6 is the wave's serial tail (the T6a-INTEGRATE lesson: integration is its own owned package, with the reported-first teeth as its acceptance gate), and its final act is regenerating `results/anchor_report.json` into the committed tree with the byte-determinism test that couples it to future re-baselines (the WP-DASH coupling-tooth pattern).

House-rule conformance summary: no tuned constants (all search constants data-derived or reused pins); dreams propose never witness (emitter deterministic; kernel sole certifier); no wall-clock in DL or in any new artifact body; reported-first with three teeth; refuse-by-construction at validator, minting, and divergence gates; every skip named; the kernel channel touches Lean exclusively through `LeanBackend.elaborate/recheck/eval_props/pp_roundtrip` via `kernel.check` — zero new trusted surface.

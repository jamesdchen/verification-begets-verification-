# PLAN_FORMALIZE_INTEGRATION.md — Zone F-INT: wiring the formalization extension into the active machinery

**v2 — hardened by a six-lens Fable adversarial sweep, every finding
independently verified or refuted by an Opus verifier against the live tree
(25 verdicts; Appendix A).** Fatal-as-filed findings that survived
verification are folded into the frozen interfaces below with ⚠FI markers;
refuted findings are recorded so a builder does not re-litigate them.

FORMALIZATION.md landed the math fragment, the fidelity pipeline, the
governor, and the Lean kernel seam. A two-agent integration audit (file:line
evidence throughout this document) found the extension is integrated only
where a subsystem is **corpus/ledger-generic**: macro mining shares the
corpus and table (`loop.py:313` has no kind filter), the examiner is a shared
module wired into `certify_statement` (`run/formalize.py:367`), the trust
tiers landed (`kernel/certs.py:135`), and the CI lean job runs the real
positive path (`ci.yml:183-189`). Every subsystem that embeds a
*service-shaped model* never sees math:

- **G1** the scheduler prices `math-source` rows (`dl.py:280-291,335-338`)
  but has **no move** to serve one (`loop.py` move generators filter to
  `spec-file` / `nl-request` / readings / `caged-incumbent`;
  `DEFAULT_DISPATCH` has no math entry) — an unserved exogenous math row is
  a permanent, un-retirable `UNCOVERED_PENALTY`, served only by the one-shot
  seed path (`cgb.py:482-536`).
- **G2** `metrics/`, `milestones.py`, and `metrics/plots.py` contain zero
  formalization logging — no milestone, no CSV, no reach-vs-cost curve for
  the math corpus (`metrics/__init__.py:14-58` counts only live generators).
- **G3** the SMT nonvacuity and instance-enumeration gates recompute
  uncached on every run (`run/formalize.py:124-125,177-195` never touch
  `cache_get`/`cache_put`; only the Lean kernel stage caches per L2,
  `kernel/__init__.py:454-463,563-573`).
- **G4** `bench_formalize.py` cannot measure what F5.2 specifies: every
  authored reading is tagged `origin:"exogenous"` and the dream corpus
  (`specs/mathsources/dream/d01–d08`) is never loaded, so both arms see
  identical inputs (a tie by construction); the macro table never reaches a
  prompt (`_author_reading(src, {})`); no checkpointing; the CSV lacks the
  F5.2 cost tuple; the bench is wired into neither `run_regression.py` nor CI.
- **G5** Zone-3 speculation (`buildloop/speculate.py:30-34,204`) fans out
  service Readings only; MathReadings have no speculative path.
- **G6** carrier (ℕ-vs-ℤ) and operator binding are represented in
  MathReadings but nothing searches that residue; `planner/choices.py`
  searches only the service lifecycle family, `planner/lookahead.py` is
  ksy-only. **⚠FI-6 (verified with a full compile/eval trace): the residue
  does NOT live in the ambient statement** — truncated subtraction and
  instance domains are decided by declared object types
  (`math_compile.py:52-53`, `math_eval.py:86-92,117-121`); ambient only
  selects Lean names for gcd/coprime. Any search over "formalization
  freedom" must substitute **whole carrier assignments** (object types +
  operator carriers + ambient, consistently) on a copied reading.

This plan closes G1–G6. It is written to be executed by a **swarm of Opus
builder agents without access to the conversation that produced it**, with
**maximum parallel fan-out at all times**: every cross-package interface is
frozen in §2 before any builder starts, every file is owned by exactly one
work package (§4), and five of the seven packages start simultaneously at
wave 0. **⚠FI-1: v1 claimed six; the sweep proved WP-B's live-loop milestone
depends on WP-A's move generator (the `dispatch=` seam overrides executors,
never proposals — `loop.py:365-373,561-571`), so WP-B carries one declared
ordering edge (§3 WP-B).**

Out of scope, unchanged from FORMALIZATION.md: autonomous fragment growth,
new certificate tiers, Mathlib contribution, proof-search research,
mathematical-importance claims. No existing certificate schema changes; no
`CERTS_VERSION` bump is needed by any package (a package that discovers it
needs one must STOP and report — that is a plan defect, not a decision a
builder may take alone).

---

## 1. Swarm execution protocol

- **Builders:** one Opus agent per work package (WP-A…WP-F), plus a
  merge-owner (WP-G) that lands last. Within a package, the builder is
  encouraged to fan out further sub-agents in parallel (impl / tests /
  fixtures are separable everywhere below; per-wave LLM authoring in WP-D is
  embarrassingly parallel by design).
- **Isolation is explicit, not implied:** every builder works in its own
  git worktree/branch forked from the same frozen pre-swarm base commit;
  done-when gates that say "`--fast` green" are evaluated **in that
  builder's tree** (its own new files + the frozen suite). Whole-suite
  green over the merged tree is checked only by WP-G at wave 1.
- **Wave 0 (parallel):** WP-A, WP-C, WP-D, WP-E, WP-F start simultaneously.
  WP-B starts at wave 0 too, but its live-loop items (B2 tooth, the
  loop-driven curve) verify only after WP-A merges — the one declared
  ordering edge (⚠FI-1). Their file sets are disjoint (§4). None may edit a
  file owned by another package; a needed change in a foreign file is
  expressed against the frozen interface in §2 or reported as a plan defect.
- **Wave 1 (serial, last):** WP-G (harness + docs).
- **Interfaces are frozen, not negotiated.** §2 is the contract. A builder
  who believes a frozen interface is wrong reports it and stops that
  sub-task; it does not improvise a variant (the X14 lesson).
- **Honesty disciplines inherited whole:** relational asserts only, never
  absolute constants (E5/H52); never sum tokens with seconds (E6); no wall
  clock in any DL-adjacent number (house rule 13); LLM-requiring paths skip
  with an honest note (H43/X15); every demo tooth must be LLM-free and
  Lean-free; deferred layers record `deferred`, never fake `pass`.
- **Byte-identity pins are captured BEFORE editing:** a package that
  promises "byte-identical to pre-WP-X" commits the golden fixture from the
  **frozen pre-swarm base** as its first commit, before touching the
  implementation file (⚠FI-11 — a pin captured after the edit pins the new
  code against itself and is vacuous).
- **Every package lands:** implementation + tests + (where stated) an
  LLM-free demo tooth + a five-line summary in its final commit message of
  what is claimed and at what strength.

## 2. Frozen interfaces (the cross-WP contract)

**F-INT-1 — the `math` move (WP-A produces, WP-B/WP-G consume).**
Move dict, mirroring `_request_moves` (`loop.py:284-296`):

```python
{"kind": "math", "candidate_key": "math:%s" % demand_id,
 "score": dl.UNCOVERED_PENALTY - est_reading_cost,   # NET, see ⚠FI-2
 "demand_id": demand_id, "row": row}
```

⚠FI-2 (verified by recomputation): a served math row is priced at
`READING_CHAIN_COST + dl_reading(...)` (`dl.py:285-288`), and committed
fixture `04_even_plus_even.json` prices at 68.0 > `UNCOVERED_PENALTY` 50.0 —
a flat +50 score with unconditional persistence makes the loop take
DL-**increasing** moves it priced as −50. Therefore: `est_reading_cost =
dl.READING_CHAIN_COST + (row.get("size_bytes") or 0) / 8.0` (a cheap
pre-authoring proxy, the `_toll_moves` idiom at `loop.py:338-341`), and
`_dispatch_math` persists **only if** the authored reading's actual served
price `READING_CHAIN_COST + dl_reading(statements, snap.macro_table)` is
`< dl.UNCOVERED_PENALTY`; otherwise it returns
`{"status": "math-refused", "reason": "dl-raising", ...}` and logs the
event. The A4 DL tooth plants fixtures 01/02 (33.0 → serve at 35.0 < 50.0,
DL strictly drops) and separately plants 04 to assert the **refusal** path.

`_math_moves(snap)` generates a move for every demand row with
`kind == "math-source"`, `status != "retired"`, `origin == "exogenous"`
(system-origin dream rows price at 0 — `dl.py:289-291` — and MUST NOT
generate moves), and no reading in `snap.readings[demand_id]`.
**`KIND_ORDER` gains `"math": 4`** (after toll; existing four values
untouched) — the sort at `loop.py:370-371` KeyErrors without it, and the
math-vs-request score tie is common, so the rank is frozen here, not
improvised (⚠FI-15).

Dispatch executor signature identical to the other four:

```python
_dispatch_math(move, snap, registry, backlog, policy, use_corpus, model)
```

Behavior: read the source text via the row's `payload_ref` (same resolution
as `_dispatch_request`), render the prompt with
`buildloop.math_prompt.render_math_reading_prompt(source, snap.macro_table)`
(the E1 seam — the LIVE table reaches the prompt), author via
`buildloop.llm.call_llm`, certify via `run.formalize.certify_statement`
passing `event_sink`, the registry cache hooks, and
`source_id=demand_id`; on `res.ok` AND the ⚠FI-2 price gate, persist with
`registry.reading_add(demand_id, common.canonical_json(reading_doc),
cert_id)` where **`reading_doc` is exactly `{"theorem": ..., "statements":
...}` — no `origin` key** (⚠FI-13, four critics: the seed path at
`cgb.py:510,533` persists no origin key, and `dl.snapshot` derives origin
from the demand row at `dl.py:185-194`, overwriting any embedded key; the
v1 text was self-contradictory). Return `{"status":
"math-certified"|"math-refused", "demand_id": ..., "stage": <failing stage
or None>}`; `run_iteration` logs a `math-refused {demand_id, stage}` event
from the returned status (the toll precedent, `loop.py:572-576`).
Registered as `DEFAULT_DISPATCH["math"]`. Tests inject `dispatch={"math":
fake}` exactly like the existing LLM-free loop tests.

**F-INT-2 — fidelity-gate cache (WP-C).** ⚠FI-4 (verified): the registry's
`cache_put` **silently drops any value that is not a
`Certificate`/`ErrorTranscript`** (`library/__init__.py:623-629`), so v1's
"thread dicts through the existing registry hooks" was a no-op on every
production path. Frozen replacement: WP-C adds a small JSON side-store
**inside `run/formalize.py`'s territory** — table `formalize_cache(key TEXT
PRIMARY KEY, value TEXT)` created lazily by WP-C's own module against the
same SQLite handle the registry exposes (`registry.db_conn()` accessor if
present, else a WP-C-owned `sqlite3.connect(os.environ["CGB_DB"])` — the
conftest isolation pattern), wrapped as `formalize_cache_get/put(key) ->
dict|None`. `certify_statement`'s existing `cache_get`/`cache_put`
**parameters keep their current meaning** (kernel certs only, untouched);
the new gates use the side-store directly. New module-level constant
`FORMALIZE_CACHE_VERSION = 1`. Two cache entries:

```python
key_nonvacuity = common.sha256_json({
    "kind": "formalize-nonvacuity", "v": FORMALIZE_CACHE_VERSION,
    "reading_sha": reading_sha, "bound": bound})
key_instances  = common.sha256_json({
    "kind": "formalize-instances", "v": FORMALIZE_CACHE_VERSION,
    "reading_sha": reading_sha, "bound": bound})
```

**`reading_sha = common.sha256_json(json.loads(math_reading_json))` over
the post-gate input doc** (stage 1 has already passed; ⚠FI-16 — the parsed
`MathReading` is a dataclass with no canonical serialization, so the input
doc is the only well-defined substrate). Cached value = the stage result
dict; **channels are normalized to lists in BOTH the cached and the
recomputed paths** (⚠FI-19 — JSON round-trips tuples to lists; freeze lists
so hit-vs-miss layers compare equal). A cache hit appends a
`("cache", "hit")` channel to the layer detail; the tooth is: hit and miss
produce byte-identical `FormalizeResult` fields **except that marker**.
Stage-1 parse always runs (groundedness is never cached); failures are NOT
cached (a divergent/refused reading recomputes — this also preserves the
`mirror-divergence` event cardinality, whose once-per-cold-compute behavior
matches the `kernel.check` precedent and was verified non-lossy).

**F-INT-3 — metrics fields (WP-B produces, WP-D/WP-G consume).** Frozen
definitions (⚠FI-5, verified: v1 stated three incompatible scopes and
`dl.py:335-340`'s `total_math` counts ALL rows):

- `math_total` = count of **exogenous-origin** `math-source` demand rows;
- `math_covered` = count of **exogenous-origin** `math-source` rows with a
  persisted reading (so `math_covered ≤ math_total` holds by construction);
- `math_dream_rows` = count of system-origin `math-source` rows;
- `tier_kernel_checked` = count of `proof-cert` certificates in the
  registry (0 in Lean-absent containers).

These deliberately differ from `dl.py`'s all-rows `total_math`/`covered_math`
ledger counters — the metrics names are new and scoped, the ledger names are
untouched (the dl.py:9-11 same-name rule). `math_certified` from v1 is
**dropped** (⚠FI-17: both persistence paths write only on `res.ok`, so it
was definitionally identical to `math_covered`). Storage (⚠FI-8): the four
fields are persisted in a **metrics-owned side table** `math_metrics(seq
INTEGER PRIMARY KEY, math_total INT, math_covered INT, math_dream_rows INT,
tier_kernel_checked INT)` created from `metrics/` code and JOINed into
`export_csv` on `seq` — `metrics_log`'s schema in the unowned
`library/__init__.py` is NOT touched (its fixed-column INSERT would
`OperationalError` on new named params). `snapshot()`'s returned dict gains
the four keys. The math reach series is `math_covered / math_total`,
plotted via the established shim pattern (`milestones.py:74-92`): an
intermediate CSV with `reach = math_covered/math_total`,
`verifier_seconds = 0`, and the cumulative token columns, handed to the
existing `reach_vs_cost` — with seconds pinned to 0 the cost axis is
kilotokens only, so E6 is respected (verified; the residual axis-label
imprecision is accepted and noted in the plot title).

**F-INT-4 — bench wave protocol + artifacts (WP-D produces, WP-G consumes).**
Wave-parallel speculation against a frozen snapshot (the `run_iteration`
discipline): with wave size `K = 8`, freeze `table_hash =
common.sha256_json(sorted(macro_table))` (macro names are content-addressed
body hashes — `recurrence.py:151-153` — so the name digest is faithful;
verified), author the wave's K statements concurrently (each call stamped
with `table_hash`), then run the LLM-free tail **serially after the wave
barrier**: certify each, checkpoint each (single writer — the checkpoint
record carries post-certify fields, so it cannot be written from authoring
threads; resume keys on the `(source_id, arm)` set, line order explicitly
insignificant), mine/admit greedily (`recurrence.mine` +
`mdl_macros.macro_admission_decision`, arm's witness filter), advance to
the next wave with the grown table. A kill mid-wave re-spends at most the
un-checkpointed in-flight wave — standard checkpoint semantics.

Dream inputs: `specs/mathsources/dream/*.txt` are authored ONCE (single
wave, empty table) and enter **only the ungoverned arm's mining corpus** as
`origin:"system"` readings (the governed arm's corpus is exogenous-only —
governance is enforced by corpus membership, the shipped `_arm` pattern at
`bench_formalize.py:68-70`; the Z-E witness filter is belt-and-suspenders).
Dream authoring cost is recorded as a CSV row with `arm = "dream"` (its
`cumulative_ktokens_*` columns carry the spend), charged to neither
governed nor ungoverned `cost_per_certified_statement` (E3).

Checkpoint file `results/formalize_bench_state.jsonl`, one JSON object per
authored reading:

```
{"source_id", "arm", "wave", "table_hash", "reading_json",
 "tokens_in", "tokens_out", "certified", "stage"}
```

Final CSV `results/formalize_governed.csv`, columns frozen (append-only):

```
arm, wave, certified_exogenous_statements, cumulative_ktokens_in,
cumulative_ktokens_out, prompt_bytes_mean, live_macros, retired_macros,
reported_exogenous_dl, translation_cert_count, per_use_cert_failures,
trivially_closed_count, cost_per_certified_statement,
cost_per_certified_statement_inclusive, lean_seconds_total, smt_seconds
```

**The numerator is frozen** (⚠FI-22): `cost_per_certified_statement =
(cumulative_ktokens_in + cumulative_ktokens_out) / FH7-denominator` —
ktokens only; the seconds columns are reported beside it and never divided
in (E6). FH7 denominator (E3): exogenous entries with statement-cert green
AND `trivially_closed == false`; the inclusive variant and the excluded
count sit beside it. The four Lean-internal F5.2 tuple fields
(`refinement_rounds_mean`, `lean_seconds_cold`, `cache_hit_rate`,
`proof_rate`) are deliberately deferred to a Lean-toolchain run and named
in the module docstring as deferred — not silently omitted. Per-wave rows
ARE the reach-vs-cost curve; the plot is a two-curve figure written to
`results/formalize_reach_vs_cost.png`. Pins recorded in a sidecar
`results/formalize_governed.meta.json` (model id, sampling params, prompt
scaffold hash, arm configs, spend cap, `MATHLIB_COMMIT`, `LEAN_TOOLCHAIN`)
— the CSV stays pure rows.

**F-INT-5 — the math speculative pre-gate ladder (WP-E).** Cheapest-first,
mirroring `speculate.pre_gate`'s service ladder, all Lean-free:
`parse_math_reading` (gate) → `math_smt` hypothesis-sat (dual-solver) →
`compile_math_reading` + `validate_lean` escape gate → entailed-instance
replay (**rank-only, never a rejection** — the S4 discipline verbatim).
Fan-out authors K candidate MathReadings via
`math_prompt.render_math_reading_prompt`; losers get **no composed
certificate**; divergence between speculated and certified verdicts logs a
`speculation-divergence` event with the same payload shape as Z3.

**F-INT-6 — formalization choice search (WP-F).** ⚠FI-6 (verified by
trace): redefined from v1. New module `planner/math_choices.py`,
deterministic and LLM-free: `search_carrier(reading_json, *, bound=8) ->
[{"assignment", "certifies", "witness", "boundary_behavior",
"statement_hash"}, ...]` — enumerate **consistent carrier assignments**
(each choice-force object's declared type, each operator statement's
carrier, and the ambient, substituted together) from the frozen
`MATH_OPERATORS` table, apply each assignment to a **deep-copied,
re-parsed** candidate reading, re-run the LLM-free gates per candidate, and
rank: certifying candidates first, then by compiled-statement DL. Only
**choice-force** elements may be substituted; a demand- or
presupposition-force type/carrier is never overridden (attempting to
raises) — the trichotomy is load-bearing. A (word, carrier) pair outside
`MATH_OPERATORS` yields a fragment-miss candidate entry, not a crash. No
new certificate type: the result is examiner-grade evidence (L3), consumed
by callers as ranking. The original reading object is never mutated.

## 3. Work packages

### WP-A — the scheduler `math` move (closes G1)

- **A1** `_math_moves(snap)` per F-INT-1 (net score, KIND_ORDER entry);
  wired into `score_moves` alongside the existing four (docstring's "four
  typed misses" becomes five; the decision log gains `kind:"math"` rows —
  append-only payload change, no schema break).
- **A2** `_dispatch_math` per F-INT-1 (⚠FI-2 price gate before persist);
  `DEFAULT_DISPATCH["math"]` entry. LLM use at loop time is the
  established pattern (`_dispatch_request` calls
  `service_loop.synthesize_semantic`); the `CGB_TASK_TIME` guard is
  untouched.
- **A3** Refusal memory, **mark-don't-omit** (⚠FI-3, verified against the
  live W3.2 code): `_math_moves` always generates the move; `score_moves`
  marks a math move `suppressed_by` (never eligible for argmax) when the
  event log shows `MATH_MAX_ATTEMPTS = 2` failed attempts for its
  `demand_id` — exactly the toll pattern at `loop.py:362-381`, so the
  suppressed, still-ledger-priced miss stays visible in `log_moves` and
  `_log_miss_records`. `MATH_MAX_ATTEMPTS` lives in `buildloop/loop.py`
  beside `KIND_ORDER`.
- **A4** Teeth (all LLM-free, injected dispatch):
  - planted unserved exogenous math row → `_math_moves` proposes it, and
    with no cheaper move present it is argmax;
  - injected fake dispatch persists planted fixture 01 or 02 → next
    snapshot shows the row covered and `ledger_dl` strictly lower
    (relational; ⚠FI-2 — these fixtures price at 35.0 < 50.0);
  - planted fixture 04 (prices at 68.0 > 50.0) → the dispatch **refuses**
    (`math-refused`, reason `dl-raising`), the row stays uncovered;
  - dream (system-origin) rows generate NO move;
  - **byte-identity pin**: golden captured from the pre-swarm base as
    WP-A's FIRST commit (§1); on a registry with zero math-source rows,
    `score_moves` output is byte-identical to that golden;
  - two failed attempts → third iteration proposes the move but marks it
    `suppressed_by`; it is never picked.
- **Done when:** teeth green; `run_regression --fast` green in WP-A's
  tree; docstrings and the `scheduler-decision` log mention the fifth kind.

### WP-B — metrics, milestone m9, the formalization curve (closes G2)

- **B1** `metrics.snapshot()` four keys + the `math_metrics` side table +
  CSV JOIN per F-INT-3 (no `library/__init__.py` edit).
- **B2** Milestone `m9` in `milestones.py`: run the combined loop over a
  seeded registry whose backlog is the `specs/mathsources` corpus, N=20
  iterations, logging per-iteration `math_covered`, `math_total`,
  cumulative token counters, producing `results/math_reach_vs_cost.png`
  via the F-INT-3 shim. LLM-requiring → honest skip note (H43).
  **⚠FI-1: the live m9 run retires rows through the `math` move and
  therefore verifies only after WP-A merges — declared ordering edge.**
- **B3** The LLM-free variant `m9_planted`: same milestone runner with an
  injected `dispatch={"math": planted}` serving the committed
  `specs/mathsources/readings/` fixtures, **plus synthetic per-serve token
  increments in the injected dispatch** so the curve has a real x-axis
  (⚠FI-21 — with 3 committed fixtures and zero cost the plot is a 3-step
  artifact; the synthetic counts are labeled synthetic in the plot title;
  monotonicity is asserted over both axes). Deterministic; fast tier.
  Also gated on WP-A for the same ⚠FI-1 reason — `m9_planted` exercises
  move proposal, not just dispatch.
- **B4** Teeth: snapshot fields per the F-INT-3 frozen definitions on a
  mixed (exogenous + dream) registry — `math_covered ≤ math_total`, dreams
  counted only in `math_dream_rows`; CSV column append verified against a
  header fixture captured pre-edit; `m9_planted` produces a monotone
  nondecreasing reach series.
- **Done when:** B1/B4 green in WP-B's tree at wave 0; B2/B3 green after
  WP-A merges; `m9_planted` is invocable as `python3 milestones.py
  m9_planted` (WP-G wires the regression item — see G1; the v1 claim that
  the fast tier "auto-discovers" it was false: `FAST_DEMOS` is a hardcoded
  list, `run_regression.py:40-45`, and milestones are never invoked by the
  harness).

### WP-C — cache the Lean-free fidelity gates (closes G3)

- **C1** The `formalize_cache` side-store per F-INT-2 (⚠FI-4), threaded
  into `_nonvacuity` and `_instances`. Stage-1 parse always runs. On hit,
  the `("cache", "hit")` channel marker is appended; channels are lists in
  both paths (⚠FI-19).
- **C2** `demo_formalize.py` (owned by WP-C, §4 — the v1 matrix omitted
  it) gains an optional `--cache` flag exercising the store; the demo runs
  cache-less by default. WP-C's first commit captures the current demo
  stdout as a committed fixture (`tests/golden/formalize_demo_stdout.txt`)
  and adds the pin test — v1 asserted a pin against a transcript that
  nothing enforces (`results/formalize_demo.txt` is committed but
  unpinned; verified).
- **C3** Teeth: (i) monkeypatched `SmtBackend.run_z3` call-counter —
  second `certify_statement` over the same reading+bound performs zero
  solver calls; (ii) hit and miss produce byte-identical `FormalizeResult`
  fields except the honesty channel marker; (iii) a changed `bound`
  misses; (iv) a version bump misses; (v) failures are never cached (a
  stage-2 refusal recomputes and re-emits its events).
- **Done when:** teeth green; the newly-pinned demo stdout unchanged with
  the flag off; fast tier green in WP-C's tree.

### WP-D — the bench that can actually diverge (closes G4)

Rebuild `run_bench` per F-INT-4. Sub-tasks parallelize internally.

- **D1** Wave engine per F-INT-4: K=8 parallel authoring, serial
  post-barrier tail (certify → checkpoint → mine → admit). Per-arm wave
  sequences over the same sources (tables diverge ⇒ prompts diverge; that
  IS the E1 measurement).
- **D2** Dream wiring per F-INT-4: authored once, ungoverned mining corpus
  only, `arm="dream"` cost row.
- **D3** Checkpoint/resume per F-INT-4; `--fresh` flag to ignore state.
- **D4** Cost columns per F-INT-4 (frozen ktokens numerator, FH7
  denominator, sidecar pins). `trivially_closed` reuses the `triviality`
  event kind; in a Lean-absent container the flag is `false` for all and
  the two cost variants coincide (recorded honestly in the sidecar).
- **D5** Per-wave CSV rows + the two-curve plot.
- **D6** Teeth (LLM-free): wave engine, checkpointing, cost accounting,
  CSV/plot rendering run with an injected fake author (deterministic
  canned readings including the dream paraphrases) —
  `tests/test_bench_formalize.py`; asserts the relational pair (equal
  coverage; governed DL ≤ ungoverned) AND that with the planted dream
  flood the ungoverned arm's reported exogenous DL is STRICTLY higher.
- **Done when:** fake-author bench end-to-end green in WP-D's tree; a real
  run documented in the module docstring (spend estimate, resume
  semantics, X15 skip note unchanged).

### WP-E — speculative fan-out for MathReadings (closes G5)

- **E1** `speculate.py` gains the math path per F-INT-5: `pre_gate_math` +
  `fan_out_math`. Shares the ranking/ledger plumbing with the service
  path; does NOT touch the service ladder (byte-identity of existing
  fixtures).
- **E2** `demo_speculate_math.py`: LLM-free planted fan-out — K=4 planted
  candidate readings for one source (one certifying, one fabricating, one
  contradictory, one carrier-narrowed **via object types**, per ⚠FI-6),
  pre-gates kill each loser at its own rung, the winner alone reaches
  certification, one planted speculation-divergence recorded.
  `REQUIRES_LLM = False` is the first line committed (the `--full` glob
  picks up any `demo_*.py` immediately and treats an import error as a
  gating LLM item — `run_regression.py:74-80,98-100`).
- **E3** Teeth: rung-order assertion; loser-has-no-cert assertion; replay
  rank-only assertion; service-path fixtures byte-unchanged.
- **Done when:** `python3 demo_speculate_math.py` green + its pytest file
  green in WP-E's tree (fast-tier listing is WP-G's, not WP-E's — the v1
  done-when was unsatisfiable from WP-E's own files).

### WP-F — searched formalization choices (closes G6)

- **F1** `planner/math_choices.py` per F-INT-6 (carrier **assignments**,
  not ambient-only — ⚠FI-6).
- **F2** Teeth: the planted ℕ-vs-ℤ case built on **object-type
  substitution** (truncated subtraction flips truth): the wrong assignment
  is refuted by the instance gate and ranked below the certifying one; a
  demand-force type/carrier is never overridden (raises); an
  out-of-table (word, carrier) yields a fragment-miss entry.
- **F3** One consumer wiring, evidence-only, **delivered as a wave-1 patch
  applied by WP-G** (⚠FI-7: v1's dual-ownership row for `run/formalize.py`
  was self-contradictory — WP-C owns that file alone; WP-F's
  `choice_search=False` keyword + stage-5 evidence block is a small,
  frozen-text patch WP-G applies after WP-C merges). Default off:
  byte-identity of all existing outputs.
- **Done when:** F1/F2 green in WP-F's tree at wave 0; F3 lands with WP-G.

### WP-G — harness + docs, the merge-owner (wave 1, lands last)

- **G1** `run_regression.py`: `--full` adds `bench_formalize.py`
  (best-effort, honest-skip, like `bench_latency`); the fast tier gains an
  **explicit** `[sys.executable, "milestones.py", "m9_planted"]` item and
  explicit `FAST_DEMOS` entries for the new demos — nothing here is
  glob-auto-discovered (⚠FI-9/FI-10; only `pytest tests/` auto-discovers,
  and only test files).
- **G2** `conftest.py` (owned by WP-G): add a matplotlib probe and
  `_FILE_REQUIREMENTS` entries for the plot-exercising test files so thin
  environments skip-with-reason instead of ImportError (⚠FI-12 — the CI
  toolchain image has matplotlib, `ci/Dockerfile:26`, but the X7 skip
  discipline covers dev environments). CI: NO new mandatory job; the lean
  job is untouched.
- **G3** Apply WP-F's F3 patch to `run/formalize.py` (⚠FI-7).
- **G4** Docs, one commit: README (five-move scheduler, math metrics, the
  bench protocol), METRICS.md (math reach-vs-cost + the frozen F-INT-3
  definitions vs dl.py's ledger counters), FORMALIZATION.md addendum
  pointer (G1–G6 closed), TRUST.md untouched (events are not certs;
  verified — no plan text mandates TRUST notes for event kinds).
- **Done when:** `run_regression --fast` green and within the wall-clock
  target on the MERGED tree (measure; if the new fast items break the
  budget, move the slowest to `--full` and record the decision); full tier
  discovers everything; docs landed; the §4 matrix updated to "landed" per
  row. Global acceptance item 6 below **is** WP-A's A4 tooth 2 — same
  test, no stronger end-to-end variant is demanded (verified reading).

## 4. File ownership matrix (exactly one owner per file)

**Status: ALL ROWS LANDED.** Wave 0 (WP-A…WP-F) built in parallel isolated
worktrees, each independently reviewed (APPROVE) before merge; wave 1 (WP-G)
merged last with the F3 patch applied to `run/formalize.py`, the temporary
regression scaffolding removed, and `planner/F3_PATCH.md` deleted after
application. Per-package claims and test counts are in the merge commit
messages on this branch.

| file | owner |
|---|---|
| `buildloop/loop.py` | WP-A |
| `tests/test_math_moves.py` (new), WP-A's golden fixture | WP-A |
| `metrics/**`, `milestones.py` | WP-B |
| `tests/test_math_metrics.py` (new) | WP-B |
| `run/formalize.py` | **WP-C alone** (⚠FI-7; WP-F's F3 patch is applied by WP-G at wave 1) |
| `demo_formalize.py`, `tests/golden/formalize_demo_stdout.txt` (new) | WP-C (⚠FI-14) |
| `tests/test_formalize_cache.py` (new) | WP-C |
| `bench_formalize.py`, `tests/test_bench_formalize.py` (new) | WP-D |
| `buildloop/speculate.py`, `demo_speculate_math.py` (new) | WP-E |
| `tests/test_speculate_math.py` (new) | WP-E |
| `planner/math_choices.py` (new), `tests/test_math_choices.py` (new) | WP-F |
| `run_regression.py`, `conftest.py`, `.github/workflows/ci.yml`, `README.md`, `METRICS.md`, `FORMALIZATION.md`, `TRUST.md` | WP-G |
| `cgb.py`, `library/__init__.py` | untouched (⚠FI-4/FI-8 route around them) |
| `kernel/**`, `generators/**`, `buildloop/dl.py`, `buildloop/recurrence.py`, `buildloop/math_prompt.py`, `tests/fixtures_math_readings.py`, `specs/mathsources/**` | untouched by ALL packages (frozen consumers; each WP authors bespoke fixtures in its own test file — verified, the X16 discipline is scoped to the parser/compiler/pipeline agreement) |

## 5. Global acceptance

1. `python3 run_regression.py --fast` green on the merged tree, within the
   wall-clock target.
2. All byte-identity pins hold, each captured from the pre-swarm base
   before its package's first implementation edit: zero-math-row
   `score_moves`, service speculation fixtures, the newly-pinned
   `demo_formalize` stdout (cache off).
3. The planted curve exists: `m9_planted` writes a monotone math
   reach-vs-cost plot with no LLM and no Lean (synthetic token x-axis,
   labeled).
4. The bench, run with a fake author, reproduces the F5.3 conjunction
   through the full wave/checkpoint/cost path.
5. Relational asserts only; grep the diff for new absolute-constant
   assertions (reviewer step).
6. = WP-A A4 tooth 2 (single referent, verified): an unserved exogenous
   math row's penalty is retired by a loop iteration with a planted
   dispatch, `ledger_dl` strictly lower on fixtures 01/02, and the
   dl-raising fixture 04 is refused.

---

## Appendix A — the adversarial sweep (six Fable critics, 25 Opus verdicts)

Six Fable agents critiqued v1 through fixed lenses (seam truth, parallel
safety, mechanism, house honesty rules, test/harness feasibility,
self-consistency), producing ~40 raw findings that deduplicated to 25.
Every finding was then independently adjudicated by an Opus verifier
instructed to REFUTE it against the live tree. Verdicts:

**Confirmed, folded into v2 (⚠FI markers above):**

| ID | severity | finding | disposition in v2 |
|---|---|---|---|
| FI-1 | major | `dispatch=` overrides executors, never proposals — WP-B's live milestone needs WP-A's `_math_moves` | declared ordering edge; B2/B3 gated on WP-A |
| FI-2 | major | flat +50 score / unconditional persist takes DL-raising moves (fixture 04 prices 68.0 > 50.0, recomputed) | net score + price gate + refusal tooth in F-INT-1/A4 |
| FI-3 | major | v1 suppressed failed rows at generation, hiding a ledger-priced miss from the decision log (W3.2 is mark-don't-omit) | A3 rewritten to mark-don't-omit in `score_moves` |
| FI-4 | major | registry `cache_put` silently drops non-Certificate values (`library/__init__.py:623-629`) — v1's cache was a no-op | F-INT-2 rebuilt on a WP-C-owned side-store |
| FI-5 | major | `math_total` had three incompatible definitions; covered>total hole on mixed registries | F-INT-3 frozen: exogenous-scoped total AND covered, `math_dream_rows` separate |
| FI-6 | major | ambient-only carrier search is semantically inert (declared object types decide truncation; full compile/eval trace) | F-INT-6 redefined as consistent carrier-assignment substitution on a copied reading |
| FI-7 | major | dual ownership of `run/formalize.py` was self-contradictory and "disjoint functions" false | WP-C sole owner; WP-F's F3 is a WP-G-applied wave-1 patch |
| FI-8 | major (plausible) | four new metrics columns can't land in `metrics_log` (schema in unowned `library/__init__.py`) | F-INT-3 freezes a metrics-owned side table + CSV JOIN |
| FI-9/10 | minor | `FAST_DEMOS` is hardcoded and milestones are never harness-invoked; WP-B/WP-E fast-tier done-whens were unsatisfiable from their own files | G1 explicit items; B/E done-whens scoped to their own trees |
| FI-11 | minor | byte-identity pins had no committed substrate or capture baseline | §1 capture-before-edit rule; A4/C2 first-commit goldens |
| FI-12 | minor | matplotlib has no conftest probe — plot tests ImportError instead of skip in thin envs | G2 conftest probe (conftest.py assigned to WP-G) |
| FI-13 | minor | `origin` key in reading_doc contradicted the seed path's bytes (inert anyway — snapshot overwrites it) | F-INT-1 persists `{theorem, statements}` exactly |
| FI-14 | minor | `demo_formalize.py` unowned while C2 edits it; the "committed transcript" pin was unenforced | matrix row added; stdout golden + pin test |
| FI-15 | minor | `KIND_ORDER` lacked "math" (KeyError) and the math-vs-request tie rank was unfrozen | frozen `"math": 4` |
| FI-16 | minor | `reading_canonical` named a nonexistent artifact (dataclass, no serialization) | frozen as sha over the post-gate input doc |
| FI-17 | minor | `math_certified` ≡ `math_covered` under the persistence rules | dropped |
| FI-19 | minor | JSON round-trip turns channel tuples into lists, breaking hit-vs-miss comparison | lists frozen in both paths |
| FI-21 | minor | planted curve degenerate (3 fixtures, zero cost axis) | synthetic labeled token increments in B3 |
| FI-22 | minor | cost numerator formula unstated | frozen ktokens-only in F-INT-4 |

**Refuted (recorded so builders do not re-litigate):** the
hit-marker/byte-identity "mutual unsatisfiability" (one consistent tooth,
marker carved out); cache-hit event swallowing (cold miss emits into the
same registry; `kernel.check` precedent); the F-INT-4/D2 dream-wiring
"contradiction" ("shared across arms" modifies authoring cost; corpus
membership enforces governance, per the shipped `_arm`); `reach_vs_cost`
reuse violating E6 (the seconds-pinned-to-zero shim is the established
`_metrics_run` pattern); thread-vs-checkpoint corruption (post-certify
fields force serial-tail writes); wave-0 pytest coupling (per-builder
worktrees, now explicit in §1); `table_hash` name-only hashing (names are
content-addressed body hashes); the five-way `fixtures_math_readings.py`
conflict (X16 is scoped to parser/compiler/pipeline agreement); the F5.2
cost-tuple omission (the four missing fields are Lean-internal and
explicitly deferred); `math-refused` mandating a TRUST entry (events are
not certs); acceptance-6/A4 ambiguity (same referent, now stated).

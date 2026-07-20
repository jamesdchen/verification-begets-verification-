# §13 sweep verdicts (fable critique sweep of the §13 draft; adversarial pre-binding review)

Run 2026-07-17, AFTER wave 3 landed (commits 394bdfb/fef7293/35812af/c229e5a/6a5a4dc/21370e1/53ada9d,
merged to main via PR #14 at 5948f09). Unlike the draft — which pledged not to peek at wave-3 results —
this sweep is REQUIRED to use them: every §13 premise below was checked against the executed records
(`results/metered_readout.json`, `results/metered_evidence/`, `results/holdout_transfer.json`,
`results/reentry_evaluations.json`, `results/tower_census.json`) and against the shipped tree.
Where a number is quoted, this reviewer recomputed it (census gapped block rebuilt in-memory;
transfer repricing re-run end-to-end from the committed snapshot and the reconstructed frozen table).
Where §13's text and this section disagree, this section wins.

## §13-S.0 Summary table

| package | verdict | one-line reason |
|---------|---------|-----------------|
| 13.0 loop definition | **proceed, one re-spec** | Event-triggering sound; but the preamble licenses WP-MET's cost columns for the X15 headline and the executed MET record says those columns are confounded n=1 — the headline needs its own registered predicate, and the "nothing below peeks" pledge is now false as written (EXECUTED stanzas were appended into the draft). |
| 13.1 WP-RECENSUS | **proceed, re-specified** | The build is right and wave 3 supplies its own motivating exhibit: the T2 evaluation's numbers are NOT in the byte-pinned census artifact its record cites (BUG-S1). The gates block must live IN the pinned artifact; the census log gets an artifact name; the (greedy;GC)* fixpoint policy must be adjudicated before the first standing T2 evaluation. |
| 13.2 WP-TRANSFER | **EXECUTED — record survives verification; the gate it feeds is re-specified** | Every headline number reproduced exactly (645/559/86; KT 737.9819/733.7474; model bits 253); freeze-before-authoring verified in git; the "bare two-Int-declaration idiom" claim is byte-true. Residuals: input-selection rule unregistered (benign, rule-like), "bench CSV rows" never delivered, and the §13.3 gate sentence ("if transfer fails") is a prose gate whose undefined middle the marginal verdict now occupies. |
| 13.3 WP-DOM-PRE | **proceed (stage 1), re-specified** | Calibration design is honest (it can kill itself), but one premise is stale post-§13.2 (compression-transfer can no longer justify stage-2 spend) and one axis is unregistered: the negative anchor's "source text" is machine JSON (`specs/services/*.json`), not prose — format confounds the raw-stream comparison and the stage-2 predicate must be format-qualified. |
| 13.4 WP-C2-TRIP | **proceed, re-specified (definitions pinned)** | Machinery premise checked true (`tools/c2_report.py` exists, single-sources `mdl_macros`); the report-not-gate stance is the §11.8 deferral preserved. Pin the sign-disagreement definition and the admission-order/context digest per instance, or the backfill is not reproducible. |
| 13.5 WP-KA-PRICE | **refusal sound; re-entry predicate well-formed — proceed as refusal** | "A verdict changes trust, not description length" is grounded: kernel verdicts are DL-inert by tooth (`tests/test_anchor_reported_first.py:127`), no pricing surface names the anchor, and the re-entry predicate (decoder + byte-identity pin + strict two-part drop + new named currency, reported-first) is evaluable and consistent with §3. |
| 13.6 WP-MECH | **proceed, re-specified — four concrete failure points fixed by artifact spec** | Wave 3 partially answers the handoff fear (two Opus adversarial catches on the record) but this sweep found prose gates inside §13 itself and a measurement-of-record drift that all-green CI did not see. Manifest needs artifact classes (regen vs frozen-one-shot); the honesty lint moves from prose to schema-checked JSON; the unchecked-axis register gets a file and a CI presence check; predicate-firings trigger mandatory full review. |
| 13.7 kill-list | **all kills stand; one reason overstated; three kills missing** | No kill is wrong. The window/order-normalization kill's stated reason ("the recurrence isn't there") is now partially contradicted by the wave-3 gapped count (39 idioms ≥2 witnesses) — the kill stands on the registered conjunction, so fix the reason, not the kill. Missing: the (greedy;GC)* gaming path, second-holdout-look, and confounded-cost-citation kills. |
| 13.8 USER-GATED | **proceed, two gates extended** | Item 2 (holdout promotion) now has wave-3 wrinkles nobody registered: only 8/20 sources certified, authored by a different pipeline (wp-met/1) than the training corpus. Re-authoring the 12 uncertified sources is authoring spend and must be explicitly user-gated. |

## §13-S.1 Pre-existing repo bugs the sweep surfaced (independent of the §13 draft)

- **BUG-S1 — the T2 evaluation's measurement-of-record does not contain its measurements.**
  §12.4 registered "both clauses ... read off the retrofitted census artifact" (COMPRESSION.md:1307-1308)
  and the EVALUATED stanza cites "census e81ec84abc267875" (COMPRESSION.md:1310). Checked: the committed
  `results/tower_census.json` hashes to exactly `e81ec84abc267875` (recomputed), but its top-level keys are
  `[artifact, census_math_mode, checkpoint, final_tables, hash_verification, records, slot_measurement,
  subtree_census, tower_census]` — **no `gapped_idiom_census` block, no `contiguous_admissible_remaining`
  anywhere** (`grep -c gapped results/tower_census.json` → 0). The T2 numbers (1 contiguous remaining,
  73 distinct gapped idioms, 39 at ≥2 witnesses) exist only in `results/reentry_evaluations.json:23-26`.
  Root cause: `tools/tower_census.py:900-907` defaults the instrument OFF so the default run stays
  byte-identical to the committed artifact, and the `--gapped` run at the fef7293 evaluation was never
  committed. **Mitigation verified by this sweep:** rebuilding the census in-memory with
  `build_census(math_mode="refined", gapped_instrument=True)` reproduces 1/73/39 exactly — the VERDICT
  is right; the record discipline failed. Fix (binding, folds into WP-RECENSUS): the gates block and every
  instrument a registered predicate reads must be present in the byte-pinned artifact whose digest the
  evaluation record cites; CI tooth = regenerate-and-diff the cited artifact, fail on any predicate input
  absent from it.
- **BUG-S2 — two different runs are both labeled "census-of-record" in the census tool's own docs.**
  `tools/tower_census.py:49-54`: the no-flags run is documented as "byte-identical to the committed run"
  while `--math-mode refined --gapped` is labeled "WP-T2E census-of-record". The committed
  census-of-record is the non-gapped run. This ambiguity is what enabled BUG-S1; fix the docstring in the
  same commit that fixes BUG-S1.
- **BUG-S3 — §13.2's registered measurement-of-record was partially undelivered.** The registration
  (COMPRESSION.md:1524-1525) names "`results/holdout_transfer.json` + the bench CSV rows, frozen-table
  hash embedded". Checked: no holdout row exists in any results CSV (`grep h13\|h20 results/*.csv` → 0
  matches). The EXECUTED stanza (COMPRESSION.md:1553-1554) silently drops the CSV clause. The JSON record
  is complete and verified; the drop should be recorded as a registration deviation, not left implicit.

## §13-S.2 Per-package verdicts

### 13.0 The loop definition — proceed, one re-spec

**Checked:** growth-event enumeration ("a source promotion, an authoring run, a holdout spend",
COMPRESSION.md:1450-1452) covers everything wave 3 actually did; the refusal of size thresholds is
consistent with the §13.1 n=2 refusal; the source-list-before-census discipline has working precedent
(§12.3/§12.4 REGISTERED-then-EVALUATED stanzas, with the freeze commit 35812af at 07:02 preceding the
metered authoring at c229e5a 08:06 — verified in `git log`).

**Premise contact with wave 3:** the §13 preamble names "WP-MET's metered cost columns (§12.5) — the
first data permitted to touch the X15 cost headline" (COMPRESSION.md:1446-1447). The executed MET record
says the cost columns establish no cost claim: 76% of the governed numerator is one runaway session
(h08, 1,044,942 input tokens), n=1 per arm, no variance estimate
(`results/metered_readout.json`, `confounds_named.cost_gap`). "Permitted to touch" without a predicate is
an invitation to cite a confounded 484-vs-55 ktok/cert ratio as a governance-cost headline.

**Binding re-spec:**
- **REG-COST-1 (registered predicate):** the X15 cost headline may cite metered columns only when
  (a) ≥2 metered runs per arm exist, (b) a runaway-excision policy was pre-registered before those runs,
  and (c) the per-arm variance is reported beside the ratio. Until then the metered numbers are
  harness-validation evidence only, and the honesty lint (13.6.3) treats a bare cost-ratio citation the
  way it treats a VOID citation.
- **Binding fix at fold-in:** the §13 heading's "nothing below peeks at a wave-3 result" pledge is now
  false for the document as committed (the §13.2 EXECUTED stanzas were appended into the draft,
  COMPRESSION.md:1527-1557). Not deception — the stanzas are dated and labeled — but the bound version
  must re-scope the pledge to "as drafted" and mark EXECUTED stanzas as post-draft records, or the
  section's first sentence is a standing counterexample to its own honesty discipline.

**Unchecked axes:** whether "growth event" needs a fourth species (a re-baseline that changes the
census-of-record table without changing the certified corpus — WP-FLIP was exactly this and it obligates
a census just as surely); flagged, not adjudicated.

### 13.1 WP-RECENSUS — proceed, re-specified

**Checked:** `tools/tower_census.py` exists and already computes per-gate metrics with named gate fields
(`tower_census.gate = "WP-T1 (COMPRESSION.md §11.2)"`, `subtree_census.gate = "WP-T4"`, verified in the
committed JSON); the carried predicate forms match their registrations exactly (T1: ≥1 MM pair ≥7
exogenous H2-realizable witnesses = COMPRESSION.md:1276-1283; T2: conjunction with G=1 =
COMPRESSION.md:1301-1308); both were evaluated once and did not fire
(`results/reentry_evaluations.json`: t1r.fired=false, max realizable 2; t2.fired=false, clause 1 fails
at 1). The gapped instrument and `math_mode` threading exist in-tool
(`tools/tower_census.py:373-492, 123-153`). The planted-fixture tooth spec is the right shape.

**Premise contact with wave 3:** two live findings sharpen the package.
1. **BUG-S1 is this package's motivating exhibit.** The ad-hoc evaluation §13.1 wants to end already
   produced one record whose cited artifact does not contain its inputs. The gates block is not an
   improvement; it is the fix.
2. **T2's clause 1 is now known to be policy-sensitive.** The evaluation recorded that GC retirement
   freed occurrences that re-admit one contiguous candidate — "greedy-then-GC is not a joint fixpoint in
   one round" (`results/reentry_evaluations.json` t2.consequence). Every future standing-loop T2
   evaluation inherits this: `contiguous_admissible_remaining` is a function of an unadjudicated
   fixpoint policy, and iterating (greedy;GC)* would mechanically drive clause 1 toward 0 — i.e. toward
   firing T2 (see kill K-NEW-1, §13-S.2/13.7).

**Binding re-spec:**
- **ART-GATES-1:** the gates block is emitted INTO `results/tower_census.json` on every census run (no
  off-by-default instrument may feed a registered predicate); the evaluation record cites the digest of
  the artifact that contains the numbers. CI tooth: regenerate-and-diff; fail if any registered
  predicate's input field is absent from the pinned artifact.
- **ART-LOG-1:** the append-only census log is a named artifact, `results/census_log.jsonl`, one line
  per growth event: `{event_commit, source_list_hash, census_digest, gates: {T1: fired?, T2: fired?,
  T4w: fired?}, banked_delta}` (the `banked_delta` column is 13.A.2's tooth, landed here). CI tooth:
  append-only (byte-prefix check, same pattern as the T4a admitted registry).
- **PRECOND-FIXPOINT-1:** before the FIRST standing-loop T2 evaluation, the (greedy;GC)* iteration
  question is adjudicated in the open as a re-baseline decision, and T2's clause 1 is re-registered
  against the adjudicated mining policy (per §12.3's re-registration discipline). Until then the gates
  block evaluates T2 but labels its verdict `policy-pending`.

**Unchecked axes:** whether the T4-widening trigger ("any event that changes the operator registry")
should also fire on macro-table changes (the subtree census walks the rewritten stream); not evaluated.

### 13.2 WP-TRANSFER — EXECUTED; the record survives verification; the gate it feeds is re-specified

This package's sweep question changed: it ran. So the sweep re-verified the execution record instead of
the plan, then asked what the verdict does to the rest of §13.

**Checked, all first-hand:**
- **Ordering (the registration's load-bearing clause):** table frozen at 35812af (07:02, "§13.2
  trained-table freeze") BEFORE any holdout reading existed; holdout readings authored during the
  metered run (c229e5a, 08:06); readout executed at 6a5a4dc (09:14). Verified in `git log`.
- **Numbers:** this reviewer re-ran the full repricing from the committed snapshot
  (`tools/holdout_transfer.py`: `reconstruct_frozen_table()` → digest check against ce5cb03fe2c5bdad
  passes; `data_bits(H,{})=645.0`, `data_bits(H,T)=559.0`, saving 86.0; KT 737.9819 empty /
  733.7474 frozen, gain 4.2345; `model_bits(T)=253.0`). Byte-exact match with
  `results/holdout_transfer.json`. The tool's teeth exist and cover the right things
  (`tests/test_holdout_transfer.py:34-146`, incl. digest-match, model-bits-exclusion,
  byte-stability, bootstrap determinism).
- **The crux claim is byte-true:** `m_5cfe6695215f`'s body is literally
  `[{kind:object,name:$p0,type:Int},{kind:object,name:$p1,type:Int}]` (reconstructed table, printed) —
  the "bare 'declare two Int variables' idiom" description is accurate, and the arithmetic closes
  (7 readings × 10 + h20's 16 = 86). The 21370e1 attribution correction was itself correct.
- **Guards:** `load_holdout` stops on snapshot-digest mismatch (`tools/holdout_transfer.py:97-104`);
  the table reconstruction stops on registered-digest mismatch (docstring:27-31 and verified live) —
  so a post-re-baseline regeneration fails hard rather than silently repricing against a new table.

**Residuals (recorded, none verdict-changing):**
1. **Input-selection degree of freedom, unregistered.** The registration never said which authored
   readings constitute H when certification is partial. The executed choice (ungoverned arm's 8
   certified readings) was made after the metered results were visible. It is rule-like and the right
   rule — the governed arm authored with a live self-mined macro in the loop
   (`results/metered_readout.json`: governed live_macros 1), so ungoverned is the
   vocabulary-uncontaminated set — but the rule was written down after the fact. Tooth for every future
   one-shot readout (folds into 13.6.4): the input-selection RULE is part of the registration,
   committed before any result that could inform it is visible.
2. **BUG-S3** (bench CSV rows never delivered) — see §13-S.1.
3. **"The holdout is then spent" has no tooth.** The one-evaluation invariant is prose. Partial cover
   exists (the digest-stop guards above); complete it via the frozen-artifact class in the regen
   manifest (MECH-1 below): `holdout_transfer.json` and `holdout_transfer_input.json` are class
   `frozen-one-shot` — CI checks byte-identity, never regenerates.

**What the verdict does to the rest of §13 (the assigned question):** the §13.2 sentence "The readout
gates §13.3's spend: if transfer fails within-domain, cross-domain authoring is dead a fortiori"
(COMPRESSION.md:1522-1524) is a **prose gate with an undefined middle — and the executed verdict landed
exactly in the middle**: +86 data bits (real), +4.23 bits vs learn-from-scratch (~0.6%, marginal),
−167 with model bits charged (negative). "Fails" was never defined; a §13 that bans prose gates
(COMPRESSION.md:1437-1440) shipped one at its own most consequential junction. Re-specified as
REG-DOM-GATE-1 under 13.3 below. Substantively, the verdict also extends C2 to transfer: the
vocabulary's durable value is certification structure, not coding and not transfer — which is 13.A.2's
telos-drift hypothesis acquiring its third independent instrument (C2 +365.8 bits §11.13; KT order-1
exhibit §10.7; transfer KT gain 4.23/738).

**Unchecked axes:** authoring-stability variance (n=1 authoring draw) — the record itself names this as
the only piece needing real spend; this sweep did not and could not check it.

### 13.3 WP-DOM-PRE — proceed (stage 1), re-specified

**Checked:** the two anchors exist and are exactly as cited — `results/service_refs.json:102-105`
carries `service_order1_surplus_pct_of_corpus_dl: 4.452` and `math_...: 34.292`; the ppm_ref instrument
exists (`tools/ppm_ref.py`, imported read-only by the transfer tool — exercised live in this sweep).
The two-stage design with a self-kill in stage 1 is honest and needs no invented objections.

**Two findings:**
1. **Format confound, unregistered.** The calibration says "mechanical tokenization of the math and
   service domains' *source texts* — the artifacts that exist before any authoring"
   (COMPRESSION.md:1568-1571). Checked: the math domain's pre-authoring artifacts are prose
   transcriptions (`specs/mathsources/*.txt`); the service domain's are machine-generated JSON state
   machines (`specs/services/nested_txn.json`, `orders.json`, `tickets.json` — inspected). A raw-stream
   rank comparison between prose and machine JSON can agree or disagree because of FORMAT, not domain
   structure — and stage 2 then anchors a (typically prose) candidate against a floor measured on a
   different text kind.
2. **Stale premise post-§13.2.** The acquisition predicate selects domains by compression
   exploitability (order-1 undercut), but the transfer readout just measured that even within-domain,
   trained-vocabulary compression value is ~zero under honest accounting. §13.3's honesty note already
   half-concedes ("not a rescue of this corpus's DL slope") — the sweep makes it whole: compression
   transfer may no longer appear as a justification for stage-2 spend.

**Binding re-spec:**
- **REG-DOM-GATE-1 (replaces the §13.2 prose gate):** stage-2 authoring spend may be PROPOSED to the
  user only with `results/holdout_transfer.json` attached, and the proposal's value claim is restricted
  by predicate: it may cite certification-structure value (coverage, verdict lattice population,
  divergence-tripwire exercise) and domain-genericity; any compression- or transfer-value justification
  is refused mechanically (the honesty lint knows the field). This converts "dead a fortiori" from vibe
  to rule without pretending the marginal verdict was a clean kill.
- **ART-PRETEST-1:** `results/domain_pretest.json` gains a required `format_class` field per stream
  (prose | machine-spec | other) and a pinned per-format tokenizer identity (function name + digest).
  The stage-2 comparison is valid only against an anchor of the same format class; a candidate with no
  same-class negative anchor is recorded as `no-floor` — the predicate does not silently fall back to
  the cross-format floor. (Consequence stated openly: today a prose candidate has a positive anchor
  and NO negative floor; that weakness is the record's, not the sweep's to paper over.)

**Unchecked axes:** whether a raw window-recurrence count (the second stage-1 instrument) has any
discriminative power at all on prose — nobody has run it on the math source texts either; stage 1 is
where that gets learned.

### 13.4 WP-C2-TRIP — proceed, re-specified (definitions pinned)

**Checked:** the premise "the c2_report.py machinery already exists" is true — `tools/c2_report.py`
computes the two-part KT code single-sourcing `buildloop.mdl_macros` for model bits (docstring lines
1-60, read); admission sites exist for both species (macro admission in the miner/`mdl_macros`;
operator admission via `buildloop/admission.py` + the T4a registry, with `results/proposal_admissions.json`
already logging counting-currency Δs — inspected). The report-not-gate stance and the refusal of
auto-activation preserve §11.8's deferral rather than weakening it; the wave-3 metered run's one clean
signal (per-use cert failure 5/7, "weakly consistent with C2", `results/metered_readout.json`)
strengthens the motivation without changing the design.

**Binding re-spec (definitions the draft leaves loose):**
- **DEF-SIGN-1:** "sign disagreement" is pinned as `(Δ_counting < 0) XOR (Δ_c2 < 0)`, with Δ_c2 = 0
  counted as disagreement when Δ_counting < 0 (a macro the counting code admits that the entropy code
  is indifferent to is exactly the mispricing class C2 predicts). Ties on the counting side cannot
  occur at admission (strict-drop law).
- **ART-MISPRICE-1:** each `results/mispricing_instances.jsonl` line carries
  `{admission_commit, macro_or_op_id, delta_counting, delta_c2, table_digest_before, stream_digest}` —
  the two digests because Δ_c2 under an adaptive coder is admission-ORDER-dependent (the H19 drift
  precedent, §11.13); an instance without its context digests is not reproducible and the backfill
  claim ("backfilled once") is empty without them.
- Tooth as drafted (planted divergent fixture fires; committed backfill count recorded whatever it is)
  is fine — proceed.

**Unchecked axes:** whether per-admission Δ_c2 should be computed at the admission-time table or the
final table (both are defensible; the drafted "one extra call per admission" implies admission-time;
this sweep pins the FIELD, not the choice — the builder's review adjudicates it and records it).

### 13.5 WP-KA-PRICE — refusal sound; re-entry predicate well-formed; proceed as refusal

**Checked:**
- The lattice the refusal guards exists and landed reported-first: `kernel/verdict_lattice.py:26`
  (five points), `kernel/certs.py:75` (`CERTS_VERSION = 12`); DL-inertness is a real tooth, not prose —
  `tests/test_anchor_reported_first.py:61` (`test_static_pricing_surfaces_never_name_the_anchor`) and
  `:127` (`test_reported_first_byte_identity_across_anchor_install`).
- The refusal's central sentence ("a verdict changes trust, not description length; no decoder") is
  grounded in the shipped pricing code: nothing in `buildloop/dl.py`/`mdl_macros.py` reads a verdict
  (grepped).
- The re-entry predicate is well-formed AND evaluable: it names an implemented decoder, a byte-identity
  pin, a strict two-part drop with decoder model bits charged, and a NEW named currency reported-first —
  each clause machine-checkable, and "rung-below checker" is established repo vocabulary
  (COMPRESSION.md:150, 192), not a new coinage. The one honest candidate shape (cert-store pointer
  compression as a different corpus with its own currency) is correctly fenced OUT of `corpus_dl`.
- Wave-3 contact: the anchor runner has produced zero kernel-proved verdicts so far
  (`results/anchor_report.json`: by_kernel proved=0, lean_available=false; source 43 sits at
  shadow-edge-refused/kernel-unavailable). The temptation the refusal pre-empts has not even had its
  first occasion — registering the refusal BEFORE the first kernel-proved exists is the discipline at
  its best. No objection invented.

**Unchecked axes:** none needed checking mechanically beyond the above; the refusal requires no build.

### 13.6 WP-MECH — proceed, re-specified; the handoff scrutiny

This reviewer is the capacity being handed off, so this verdict is given with the specific failure
points named, each grounded in something checked this sweep — not in nostalgia.

**What wave 3 already shows about the handoff (evidence FOR partial sufficiency):** two Opus
adversarial passes caught two real over-claims before they were banked — the metered run's wrong
"vocabulary did not transfer" reading (`results/metered_readout.json` process_note) and the transfer
readout's wrong attribution (commit 21370e1). Both catches were on INTERPRETATION of fresh artifacts.
Neither was a design-premise falsification of the §11-§12 kind (H2-unrealizable census inflation, T6b
false-green, KA premise-false) — the historical Fable axis. The distinction matters and 13.A.3 has it
right.

**Where Opus + green CI will fail, concretely (each observed in this sweep, not hypothesized):**
1. **Prose gates with undefined middles.** §13 itself shipped one ("if transfer fails within-domain",
   COMPRESSION.md:1522-1524) and the marginal executed verdict landed exactly in its undefined region.
   All-green CI says nothing; a cooperative reader resolves the ambiguity in whichever direction they
   arrived wanting. Fixed by REG-DOM-GATE-1 above; the general tooth is 13.6.2 done thoroughly — this
   sweep's check found the ONE §13 gate that had escaped predicate form; the merge lint for the bound
   §13 must grep-verify that every "gates/proceeds iff/only if" sentence names a registered predicate ID.
2. **Measurement-of-record drift.** BUG-S1: an evaluation record citing a digest of an artifact that
   does not contain the evaluated numbers, everything green. No 13.6 item as drafted catches this class.
   Fixed by ART-GATES-1 (13.1).
3. **The regen manifest vs one-shot artifacts.** 13.6.1 as drafted ("any commit touching a census input
   must regenerate every listed artifact") collides with §13.2's spent-holdout invariant: after any
   re-baseline that changes the census-of-record table, regenerating `holdout_transfer.json` is either
   a silent second look (voiding the claim) or a hard stop (the tool's digest guard,
   `tools/holdout_transfer.py:27-31` — verified live) that turns CI permanently red. **Binding re-spec
   MECH-1:** `results/regen_manifest.json` entries carry `class: regen | frozen-one-shot`;
   frozen-one-shot artifacts are byte-identity-checked, never regenerated; `holdout_transfer.json`,
   `holdout_transfer_input.json`, `reentry_evaluations.json`, and `metered_*` are the initial frozen set.
4. **Prose linting is gameable.** 13.6.3's "transfer claims must carry the model+pipeline qualifier"
   as a lint over markdown will bit-rot into regex theater. **Binding re-spec MECH-2:** claims live in
   JSON verdict artifacts with a schema-required `model_qualification` block
   (`model_id, harness_version, corpus_digest, n_runs`) — the precedent already exists and is good
   (`results/metered_readout.json`, `results/holdout_transfer.json` both carry it); the CI lint
   validates artifact schemas, and the markdown rule reduces to "a claim sentence must cite its
   artifact", which IS grep-checkable.
5. **The unchecked-axis register has no artifact.** 13.6.4 names a register and re-reading ceremony but
   no file. **Binding re-spec MECH-3:** `results/review_register.jsonl`, append-only, one line per
   package review: `{package, review_commit, findings_landed_as: [...], unchecked_axes: [...] |
   {none_justification}}`; CI presence check keyed off the ownership table — a package row without a
   register line does not merge.
6. **Is the unchecked-axis field enough? No — and the draft knows it.** The field records known
   unknowns from the reviewer who already missed the axis. The real cap is 13.A.3's standing rule (no
   new rung class, currency, or trusted surface on teeth alone), which is well-formed and this sweep
   endorses unchanged. **One extension, event-driven not tuned (binding re-spec MECH-4):** any
   registered predicate FIRING that unlocks a build (T1, T2, T4-widening, DOM-PRE stage 2, KA-PRICE
   re-entry) triggers a mandatory full adversarial review of the unlocked package BEFORE the build —
   firing events are exactly the moments new machinery enters and unregistered failure axes matter
   most, and they are rare by construction (0 of 2 fired in wave 3).

**Sequencing correction (overtaken by events):** the drafted "WP-TRANSFER's registration immediately
(it must precede WP-MET's run)" (COMPRESSION.md:1716-1717) already happened; the bound §13 drops
TRANSFER from the sequencing sentence and keeps MECH-first + RECENSUS-with-MECH, which stands.

**Unchecked axes (this sweep's own):** whether the ci.yml lean lane went green after the ba55452
`[lean-ci]` trigger — the check-run lives on GitHub, not in the tree; `results/anchor_report.json`
still records `lean_available: false`, so the §12.2 hard precondition (lean GREEN) must be treated as
NOT YET MET by anything in-tree. Also: this sweep did not execute the full test suite (pytest/z3 absent
from this environment; `setup.sh` not run) — teeth were verified by reading and by targeted in-memory
re-execution of the two load-bearing measurements, not by a green `pytest` run.

### 13.7 Kill-list — all kills stand; one reason overstated; three kills missing

**Each kill checked against the record:**
- **Scheduler kill: stands.** The effort denominator claim survives wave 3 — metered cost now EXISTS
  but is n=1 and confounded (`results/metered_readout.json`), which satisfies neither clause of the
  registered re-entry (≥2 growth cycles of metered cost; ≥2 contending packages). §5's own one-step
  admission is on file (COMPRESSION.md:133).
- **Kernel-verdict pricing: stands** (§13.5 verdict above).
- **n=2 extrapolation kill: stands** — still exactly two growth points (37, 51).
- **C2 auto-activation refusal: stands** — and 13.4's tripwire as re-specced cannot trigger it.
- **Second-domain-without-pretest kill: stands**, with 13.3's re-spec tightening what a pre-test
  passing even means.
- **Prequential-as-gate kill: stands** — checked: the transfer readout used counting + KT comparator,
  no prequential gating anywhere in `tools/holdout_transfer.py`. The draft's fear ("a transfer readout
  will tempt exactly this") did not materialize; keep the restatement.
- **Window/order-normalization kill: stands on its predicate, but the stated REASON is now
  overstated.** The kill says "three independent instruments agreeing the recurrence isn't there"
  (COMPRESSION.md:1694-1697). The wave-3 gapped instrument found 39 one-statement-gapped idioms at ≥2
  exogenous witnesses (73 distinct) — clause 2 of T2 "would pass overwhelmingly"
  (`results/reentry_evaluations.json`). The recurrence IS there in gapped form; T2 refuses on clause 1
  (contiguous space not mined out), which is the correct, registered reason. **Binding fix:** the kill's
  reason becomes "absent a census firing — the registered conjunction refuses (clause 1)", dropping the
  "recurrence isn't there" prose, which the repo's own instrument now contradicts.
- **T5 restatement: stands.**

**Missing kills (each a gaming path opened BY wave-3 results, hence invisible to the draft):**
- **K-NEW-1 — (greedy;GC)* iteration as a T2 unlock.** The T2 evaluation recorded that GC retirement
  re-admits one contiguous candidate; iterating greedy;GC to a joint fixpoint would drive
  `contiguous_admissible_remaining` toward 0 — mechanically flipping T2's clause 1 toward firing.
  KILLED: no mining-policy change (including fixpoint iteration) may land in the same commit-window as
  a predicate evaluation it could flip; the policy decision is adjudicated first, then the affected
  predicate is RE-REGISTERED (per §12.3), then evaluated. (Also PRECOND-FIXPOINT-1, §13.1.)
- **K-NEW-2 — any second holdout look.** Re-selection of the input set, re-authoring the 12 uncertified
  sources "to complete the readout", or repricing under any other table: all reclassify the holdout as
  training data per §13.2's own registration. KILLED; tooth = the frozen-one-shot manifest class
  (MECH-1) plus the tool's existing digest-stop guards.
- **K-NEW-3 — citing the confounded metered cost ratio.** 484-vs-55 ktok/cert is a REAL number with a
  named confound (one runaway session = 76% of the numerator), which makes it more dangerous than a
  VOID column — VOID refuses citation by absence; this invites it by existence. KILLED as a headline
  until REG-COST-1's clauses are met; the honesty lint learns the artifact field.

### 13.8 USER-GATED items — proceed, two gates extended

**Checked:** the four items are the right species (spend, corpus identity, curation, adjudication),
and item 4 correctly keeps the human in exactly the seat 13.4's refusal requires. Wave-3 contact adds
two wrinkles the draft could not have seen:

- **Item 2 (holdout promotion) is now underdetermined.** The "spent holdout" is: 20 committed source
  texts, of which 8 have certified readings — authored by a DIFFERENT pipeline (wp-met/1 metered,
  model claude-opus-4-8) than the training corpus's inline authoring, with 12 sources reading-less
  (`results/holdout_transfer.json` holdout_H; `results/metered_readout.json`). Binding re-spec: the
  promotion decision put to the user must name its scope explicitly — (a) sources only (12 need future
  authoring spend), (b) sources + the 8 wp-met readings (a mixed-authoring-pipeline corpus, which every
  registered predicate would thereafter census over — the pipeline heterogeneity gets a provenance
  field, not silence), or (c) refused. The gates cannot make this call; they CAN refuse to let it pass
  unnamed.
- **New item 5:** any RE-AUTHORING spend on the 12 uncertified holdout sources is real model spend and
  is user-gated exactly as §12.5 was — it is neither "new domain" (item 1) nor "new sources" (item 3)
  under the drafted wording, and K-NEW-2 additionally forbids it from feeding a second transfer look.

## §13-S.3 The 13.A appendix — engaged directly

**Are the three self-deception hypotheses the right three?** They are three real axes, correctly
ranked, and each now has wave-3 evidence to score it against. They are not complete — one materialized
failure class fits none of them cleanly (below).

- **13.A.1 (forking paths in growth timing): CONFIRMED as the right axis; the tooth needs one
  extension.** The registered-then-evaluated discipline demonstrably works — both wave-3 predicates
  were registered blind (35812af, census "unpeekable") and both recorded DID-NOT-FIRE without ceremony
  loss. But the nearest ACTUAL instance of the forking-paths class in wave 3 was not growth timing —
  it was the §13.2 input-selection degree of freedom (which authored readings constitute H, chosen
  rule-like but post-hoc; §13-S.2/13.2 residual 1). The 13.A.1 tooth (source-list-before-census,
  commit-ancestry-checked) does not cover one-shot readout inputs. Extension, binding: every one-shot
  readout registration includes its input-selection rule; a readout whose input rule postdates any
  visible result of the process that produced the inputs is invalid by construction — the same
  ancestry check, pointed at readouts.
- **13.A.2 (telos drift): CONFIRMED — and now measured, three instruments deep.** C2 (+365.8 bits,
  §11.13), the KT order-1 exhibit (§10.7), and now the transfer readout (KT gain 4.23 of 738 bits;
  negative under model-bits accounting — verified by re-execution this sweep) agree: the vocabulary's
  value is certification structure, not coding, not transfer. The drafted tooth (banked-Δ column +
  honesty lint) is right and lands via ART-LOG-1/MECH-2. Its trigger has NOT yet fired — WP-FLIP banked
  a real Δ−543 (394bdfb) — so the "the coder is done" sentence is not yet due. One binding sharpening:
  the sentence's trigger gains the transfer verdict as an independent clause — it is written at the
  first growth event whose census banks Δ0 **or** whose transfer-class readout (if any) lands ≤1% of
  the from-scratch line, whichever first. Three instruments saying "certification, not compression"
  should not need a fourth before the section says it too.
- **13.A.3 (mechanization theater): PARTIALLY REFUTED in one direction, CONFIRMED in the other — the
  draft's own split is close to right.** Refuted: Opus adversarial review is not a null capacity —
  two real over-claims were caught before banking, on the record (c229e5a process_note; 21370e1).
  Confirmed: both catches were interpretation-of-artifact catches; the design-premise-falsification
  axis remains uncovered, and this sweep's own findings are the exhibit — a prose gate inside the
  section that bans prose gates (13.2→13.3), a measurement-of-record drift (BUG-S1), and a
  manifest/one-shot collision (MECH-1), none of which any drafted tooth would have caught, all of which
  were sitting in a tree with green CI. The standing rule (no new rung class/currency/trusted surface
  on teeth alone) is endorsed unchanged; MECH-4 (mandatory full review on any predicate firing) extends
  it to the exact moments the theater would be most expensive.

**The failure axis nobody registered:** **record/verdict divergence** — a verdict artifact citing a
byte-pinned measurement artifact that does not contain the verdict's inputs (BUG-S1 is the live
instance: `reentry_evaluations.json` cites census e81ec84abc267875; the census has no gapped block).
This is neither forking paths (nothing was tuned), nor telos drift, nor review-capacity loss — it is
the citation graph decaying while every individual artifact stays green. The VOID-citation lint (13.6.3)
catches citations of things that don't exist; nothing drafted catches citations of things that exist
but don't contain what is claimed. Registered here: **containment-check tooth** — for every evaluation
record, CI verifies the cited digest's artifact actually contains the fields the record reads
(ART-GATES-1 is its first instance; the rule is general and joins the regen manifest checks).

---

*Sweep discipline note: every number above was recomputed or byte-checked in this environment except
(a) the lean CI check-run status (lives on GitHub; in-tree evidence says `lean_available: false`) and
(b) the full pytest suite (pytest/z3 not installed here; the two load-bearing measurements — the T2
gapped census and the complete transfer repricing — were re-executed in-memory instead and matched the
committed records byte-for-byte / value-for-value). No repo file other than this report was created or
modified.*

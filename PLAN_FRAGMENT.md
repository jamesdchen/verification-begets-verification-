# PLAN_FRAGMENT.md — closing the corpus↔fragment gap

Status: ACTIVE — sibling packet to `PLAN_REFLECT.md` (which stays scoped to
the reflection program T1–T3).  A fresh session picking up FRAGMENT GROWTH
reads this file first, then the census results, then acts.  House rules
carry over verbatim: every done-condition below is a predicate a test, the
census, or the Lean lane evaluates — none exists only as prose.

## 0. The program in one paragraph

The FRAGMENT is the language the machine speaks (carriers, operator words,
quantifier shapes — defined by the validators/lexicon, changed only through
admission ceremonies).  A CORPUS is a body of math humans wrote (blueprint
sites, the committed readings), taken as found.  The census
(`tools/blueprint_extract.py` + `tools/blueprint_census.py`) measures their
intersection per corpus.  The gap closes from BOTH ends: purchases grow the
fragment toward math (expensive, battery-gated); corpus selection brings
math toward the fragment (free).  One law overrides all economics: TRUST
ROOTS NEVER GROW BY PURCHASE — anything touching a discharge route goes
through the shadow→evidence→promotion pattern PLAN_REFLECT S4a→S4a′→S4b
rehearses.

## 1. Verified current state (update every cycle)

- **C1 done — the corpus portfolio: 5 corpora, 748 nodes** (pfr 218,
  unit_fractions 52, formal_book 192, flt_regular 45, equational_theories
  241), each intaken under `specs/mathsources/<name>/` as `nodes.jsonl` +
  `fetch_meta.json` with per-page SHA-256.  The done-predicate is a test:
  `tests/test_census_portfolio.py` (≥5 corpora, committed censuses in sync).
  `tools/census_portfolio.py` is the §2 re-census instrument (one command,
  per-corpus reports + the rollup in `results/census_portfolio.json`).
- Census instrument: **second-wave miss signals** landed after the first
  mining triage (geometry-topology, graphs-combinatorics, magmas-equational,
  polynomials-fields, maps-functions, rational-arithmetic — the start of
  P3's signal split).  Portfolio verdicts under THIS instrument:
  **2 attempt-candidates**, 590 out-of-fragment, 156 no-signal.  Price list:
  magmas-equational 156, probability-entropy 116, rational-arithmetic 115,
  sequences-sums 109, algebra-structures 97, sets-cardinality 90,
  real-analysis 84, polynomials-fields 60, primality 57, maps-functions 42,
  graphs-combinatorics 41, geometry-topology 33.
- **C2 first mining cycle ran; queue triaged; done-predicate OPEN**
  (`results/fragment_mining_triage.md`): first-wave census showed 61
  candidates; triage exposed them as signal blind spots; under the refined
  instrument 2 survive — `fermats_little` (formal_book; near, blocked on
  `operator:pow-symbolic-exponent` = P1's binding machinery) and
  `edge-disjoint` (equational_theories; false candidate, subscripted
  operator notation is a recorded lexical blind spot).  Zero transcribe
  today; corpus-side demand and the price list now AGREE on P1.
- Fragment today: carriers Nat/Int; first-order operator words only (no
  binding operators); reflect slice = Int v0.1 (PLAN_REFLECT §1).
- No purchase from §4 has started.  Next flywheel action: **P1**.

## 2. The flywheel (the ONLY loop; one purchase per cycle)

census → miss histogram = price list → ONE purchase through the admission
batteries → re-census the full corpus portfolio → the measured delta
(attempt-candidate count + histogram shift, per corpus) is committed to
`results/` in the same session that learns it.  A purchase whose re-census
shows no delta across ≥2 corpora is recorded evidence to buy differently —
never silently retried, never quietly widened.

## 3. The corpus axis (free; runs first and continuously)

- **C1 — corpus portfolio: DONE** (cycle 1): intake + census of 4 more
  blueprint corpora chosen near the fragment — unit_fractions, formal_book,
  flt_regular, equational_theories — beside pfr.  The done-predicate
  (≥5 corpora under `specs/mathsources/` with committed census results) is
  evaluated by `tests/test_census_portfolio.py`.  Further corpora stay
  welcome under the same intake discipline (`nodes.jsonl` + `fetch_meta.json`
  with source URL, date, per-page SHA-256; network-at-intake only).
- **C2 — mine where candidates exist today: RUNNING, done-predicate OPEN**:
  cycle 1 triaged the whole 61-candidate queue
  (`results/fragment_mining_triage.md`) — zero transcribe into today's F-G;
  the near-candidate (`fermats_little`) is blocked on P1-class binding
  machinery and is the named first intake after P1 lands.  Done-predicate
  unchanged: first mined template whose source is a census
  attempt-candidate (not a hand-authored reading).
- **C3 — the 24/7 cadence**: continuous mining = a Routine firing driver
  sessions on a schedule, each running one census/mine/ledger cycle and
  committing results back.  Creating the Routine is USER-GATED (recurring
  scheduling is the maintainer's to authorize); this packet is the prompt
  such a session would follow.

## 4. The purchase queue (strict tractability order; each battery-gated)

Every purchase pays the SAME full bill: validator + lexicon entry, eval
semantics, SMT mirror, Lean rendering table, differential + symbolic
batteries (b/b2), growth-protocol registry row (extend `operator-words` or
register a new grower — the completeness canary must stay green), teeth,
AND a FgReflect slice extension (constructor + Decidable instance, lane-
checked) so reflection keeps pace with the fragment.  Done-predicates for
every purchase: admission batteries green; reflect-slice lane green; the
§2 re-census delta committed.

- **P1 — bounded big-operators** (prices sequences-sums: 45 in PFR; high
  frequency in every corpus).  A binding AST node CLASS — Σ/Π with an
  explicit literal bound — not an operator word: F-G is first-order today,
  so this is the one structural extension.  Bounded iteration is exactly
  what the repo already trusts: decidable by exhaustive computation, SMT
  by unrolling, Lean via `Finset.range`.  Largest single ROI; everything
  later rides its binding machinery.
- **P2 — bounded Finset carrier + card** (sets-cardinality: 24).  Rides
  P1's binding machinery; same bill.
- **P3 — ℚ carrier** (the mass-arithmetic slice of probability-entropy's
  111).  Rational arithmetic is decidable for the fragment's relations;
  finite distributions with rational masses become expressible WITHOUT
  touching `log`.  Requires a census signal split (probability-mass vs
  entropy-log) so the delta is honestly attributable, plus the D8-class
  divergence battery against Nat/Int.
- **P4 — concrete algebra: `ZMod n` carrier** (algebra-structures: 49,
  PARTIAL).  Finite carriers are per-instance decidable; typeclass-
  parametric statements (`∀ G [Group G]`) stay out-of-fragment under an
  honest sub-signal (algebra-abstract), never silently claimed.
- **P5 — abstract algebra discharge route: TRUST ROOT, NOT A PURCHASE.**
  A new rung (a group-tactic class) touches `ANCHOR_DISCHARGE_RUNGS`
  (PINNED, kernel/certs.py, FI-KA-1/4).  The ONLY route: shadow channel
  beside the ladder → durable agreement ledger → numeric entrance
  predicate → ONE-commit ceremony with explicit user sign-off — the
  PLAN_REFLECT S4a→S4a′→S4b pattern verbatim.  No queue entry may
  shortcut this, whatever the census prices it at.
- **PARKED (named, never promised)**: entropy proper (`log` is
  transcendental) and real-analysis (limits/continuity are undecidable).
  These need a DIFFERENT certifying story (interval-arithmetic or
  polyrith-class routes), i.e. a research program, not a queue entry.
  The census keeps measuring them; any future attempt starts with its own
  packet and its own shadow ceremony.

## 5. Guardrails (non-negotiable)

- The anti-list overrides the price list: trust roots never grow by
  economics (§4 P5 is the worked example).
- No kernel/cert/TRUST.md edits outside a PLAN_REFLECT-S4b-style ceremony.
- Census intake is network-at-intake only (committed SHA-256 per page);
  everything downstream is offline, deterministic, LLM-free, and runs
  under `buildloop.lanes.token_free`.
- One purchase per flywheel cycle; the delta is committed before the next
  purchase begins.
- Branch discipline, the escape-gate envelope, and the `[lean-ci]` tag
  carry over from PLAN_REFLECT §4 for every Lean-touching step.
- Honesty rules carry: the census reports signals, never fidelity
  verdicts; parked items stay parked in writing; a no-delta purchase is
  recorded, not hidden.

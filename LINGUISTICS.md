# What the System Can Achieve, Linguistically

TRUST.md states what is trusted and why. This document states what is *meant*
and how much of meaning the system actually captures — phenomenon by
phenomenon, with every claim pinned to an artifact in this repository. The
honest headline first:

> The system does not understand language. It **localizes interpretation**: it
> converts the global, unauditable question *"did the machine build what I
> meant?"* into a set of local, mechanically-bounded questions — *"is this
> quoted span correctly rendered by this small logical form?"* — plus an
> explicit ledger of everything that was interpretation rather than text.
> Inside a precisely-drawn semantic fragment, fidelity of code to analysis is
> **proved**; fidelity of analysis to text is **structured, grounded, and
> cross-examined**, but remains evidence, not proof.

That trade — proof below the Reading, disciplined evidence above it — is the
system's entire linguistic content. Everything below is the detail.

---

## 1. The pipeline as a linguistics experiment

The semantic path (`cgb.py synthesize --semantic`) factors the classic
natural-language-understanding problem into the two halves that a century of
semantics says it factors into:

```
  natural language ──[analysis: untrusted, disciplined]──▶ Reading
  Reading ──[compilation + proof: deterministic, checked]──▶ running code
```

- The **Reading** (`generators/reading.py`) is a Discourse Representation
  Structure in the practical sense: explicit discourse referents (quantities,
  actions), plus conditions over them, each tagged with speech-act force and a
  verbatim quote. Anaphora is resolved *by construction* — statements may only
  refer to declared referents, so there is no free pronoun resolution to get
  wrong.
- The **compiler** (`generators/reading_compile.py`) is a Montague-style
  compositional semantics for the fragment: each logical form contributes its
  meaning to the whole by fixed rules, and the meaning of the whole (the
  meta-spec, then the dispatcher) is a function of the meanings of the parts.
  Compositionality here is not an aesthetic: it is what makes **provenance**
  possible. Because each spec element is produced by identifiable statements,
  every guard, constraint, and invariant in shipped code traces to *quoted
  span → force → logical form → spec element → proof* (`provenance.json`
  beside every artifact).

What is deliberately **not** mechanized: the syntax–semantics interface.
The system contains no parser of English. The map from sentences to logical
forms — the step Montague grammar, CCG semantics, and semantic parsing all
try to mechanize — is performed by the untrusted LLM. The system's
contribution is to make that step *small* (one sentence → one small formula),
*grounded* (quotation-checked), *typed* (force-tagged), and *cross-examined*
(entailed scenarios + independent examiner), rather than to eliminate it.

## 2. Speech acts and the force trichotomy

A request is a **directive** (Searle). The Reading decomposes its content
into three illocutionary classes, and the gate enforces the decomposition
mechanically:

| force | theory | mechanical rule | catches |
|---|---|---|---|
| `demand` | directive propositional content | quote must occur **verbatim** in the request | fabricated obligations (`demo_reading.py` B1: a demand quoting "guarantee same-day refunds" is rejected by string containment, not judgment) |
| `presupposition` | accommodation (Lewis/von Fintel) | quotes its trigger, also verbatim | untriggered accommodation |
| `choice` | the pragmatic residue | quote must be **empty** | interpretation smuggled as text (B-teeth: a choice with a quote is rejected) |

This trichotomy is the system's central pragmatic achievement: **the
interpretive residue is first-class.** Most NL→code systems hide where the
model filled gaps; here every gap-filling act is a `choice` record with no
textual warrant, visible in the ledger, and *subordinated to the text* — a
chosen lifecycle must formally entail every demanded ordering
(`reading_compile.py` graph check; B3 shows a choice contradicting a demanded
`order` refused at compile). A design decision can never silently override a
sentence.

What quotation-grounding does **not** give: correct construal. The gate
proves the span exists, not that the logical form attached to it is the right
reading of it. Misconstrual survives the gate — but it is *localized* to one
sentence-sized, human-auditable pair, and it must additionally survive
dual-solver consistency, compilation, proof, entailed scenarios, and the
examiner. Fabrication is impossible; misreading is possible but pinned to
the page.

## 3. Lexical semantics: verbs, nouns, and what the fragment can say

**Verbs.** The `effect` logical form covers change-of-state verbs with
incremental themes — Vendler/Dowty accomplishments whose result is an integer
update: *sell/reserve/consume/add* n → `dec/inc/set` on a quantity. The live
run (`results/semantic_synth.txt`) shows the canonical case: "oversell"
presupposes a `sell` action whose effect *decrements* stock by its argument.
Outside the fragment: manner verbs, statives, verbs with non-scalar effects,
causative chains, aspectual composition. These do not compile — they are
refused at the gate, which is the honest outcome (§7).

**Nouns.** Quantities are integer **aggregates**. The system tracks *how
many* tickets, never *which* ticket. There are no individuals, no sorts, no
identity — so any request that quantifies over individuals ("no customer may
hold seats under two names") is unrepresentable. This is the sharpest
expressive boundary in the current fragment, and it is a logic boundary, not
a prompt boundary: fixing it means moving from QF_LIA counters to relational
logic (§8).

**Negation.** Handled only as it compiles into comparison polarity: "not
oversell" unpacks the lexicalized scalar verb (*sell beyond what remains*)
into `count <= remaining` and `G(remaining >= 0)`. Wide-scope/metalinguistic
negation, negation of manner, "don't X unless Y" — outside the fragment.

## 4. Quantification, comparatives, degrees

- **Measure comparatives** ("more than 8", "at most", "no more than") land in
  linear arithmetic and are fully handled — including their interaction with
  deontic negation: "Nobody may take more than 8" → `n <= 8`, dual-proved and
  boundary-tested (`constraint-cert`).
- **Quantification over agents** is *flattened*: "nobody may…" becomes a
  per-call constraint, which is exactly right under agent symmetry and wrong
  the moment the text distinguishes agents ("regulars may take 10"). The
  fragment has no agent variables; agent-relative deontics are future work
  with a known shape (parameterized guards).
- **Degree vagueness** ("too many", "a reasonable limit") is treated the only
  defensible way: it cannot be a demand (no verbatim span yields a number),
  so making it concrete is forcibly a `choice` — an explicit, audited
  standard-fixing, which is what degree semantics says context does anyway.
  The system does not resolve vagueness; it makes its resolution *visible*.

## 5. Modality and time: exactly the safety fragment

The deontic layer collapses obligation into **enforcement**: "may not / never
X" compiles to a mechanism under which X is impossible (guard + global
invariant), and the collapse is apt because a dispatcher *is* the norm's
implementation. What the temporal-deontic fragment contains:

- **G(φ)** — global prohibitions/invariants over every reachable state
  (`when:"*"` in the BMC; proved by Z3 ∧ CVC5, complete for acyclic control);
- **precedence** (`order`: a₂ only after a₁) — a weak past modality, checked
  against the chosen lifecycle and behaviorally via entailed traces;
- **conditional obligation** relative to state and per-call fields (guards;
  `implies` in constraints).

What it provably does **not** contain:

- **F/U — eventualities.** "Must eventually deliver", "respond within 24
  hours": no liveness, no metric time. The pipeline's liveness check is
  non-vacuity (a legal run exists), not guaranteed progress. The fragment is
  **safety-only**, and requests whose central verb is a promise of future
  action exceed it.
- **Violable norms.** Contrary-to-duty structure ("if you do oversell,
  refund") requires representing violation states; enforcement semantics
  cannot express norms about its own breach.
- **Permission as an object.** "May" is implicit (whatever is schema-legal
  and unforbidden); free-choice permission puzzles are sidestepped rather
  than solved.

## 6. Pragmatic enrichment: the honest core

"Help me not oversell tickets" *demands*, literally, an invariant. That the
answer should be a **gatekeeping service** — rather than, say, an alerting
system — is relevance-theoretic enrichment, and the system does not model it.
It verifies *a coherent enrichment*, not *the intended one*. Two mitigations,
both in the artifact record:

1. **Entailed scenarios** (`reading_compile.entailed_scenarios`): whatever
   the demands say, the solver derives the traces that would violate them and
   the finished service is checked to reject exactly those. Fidelity to the
   written demands is thereby *mechanical* — natural-logic entailment
   replaced by SMT.
2. **The independent examiner** (inter-annotator agreement, mechanized): a
   second, semantics-blind construal of the same request must converge on the
   same behavior. `demo_reading.py` B5 is the load-bearing honest tooth: an
   **omitted presupposition** (the analyst never states that selling depletes
   stock) satisfies every written demand *vacuously*, certifies fully — and
   is caught only by the examiner's meaning-level scenario. Fidelity to what
   was written and coverage of what was meant are different properties; the
   system delivers the first as proof and the second only as convergence
   evidence. Nothing can deliver the second as proof; intent is not a formal
   object.

Indexicality is absorbed by a single-principal assumption ("I", "me", "my
venue" — one requester, whose text is the sole ground truth). Multi-party
requests with conflicting deontic sources are out of scope.

## 7. Refusal as competence

A controlled fragment is only honest if its boundary is *enforced*. It is:
out-of-fragment logical forms fail the Reading gate; unreadable requests
exhaust the loop and return failure rather than a plausible guess
(`synthesize_semantic` → `exhausted`). Linguistically, the system knows what
it cannot say. The same discipline runs through the stack: contradictory
demand sets are refused before any code exists (dual-solver `unsat` on the
consistency obligation — B2); readings that misuse force are refused at the
gate; choices that override text are refused at compile. Each *kind* of
misreading has its own catch stage (`demo_reading.py`: five kinds, five
stages), which is what makes refinement feedback specific rather than
oracular.

## 8. Coverage summary and the growth path

| phenomenon | status | mechanism / boundary |
|---|---|---|
| directive force, prohibition ("never", "may not") | **handled** | demand → G(φ), dual BMC proof |
| change-of-state verbs, incremental theme | **handled** | `effect` dec/inc/set |
| numeric comparatives, measure phrases | **handled** | QF_LIA bounds, dual-proved |
| procedural precedence ("first…, then…") | **handled** | `order` ⊨ lifecycle + entailed traces |
| presupposition accommodation | **structured** | trigger-quoted; content checked only downstream (B5 = residual risk) |
| pragmatic residue / underspecification | **ledgered** | `choice` records, subordinated to demands |
| agent quantification ("nobody") | **flattened** | correct under agent symmetry only |
| degree vagueness ("too many") | **externalized** | forced into an audited `choice` |
| individuals, identity, relational nouns | **out of fragment** | needs relational logic (Alloy-class checkers) |
| eventualities, deadlines, liveness | **out of fragment** | needs F/U, metric time (LTL/timed-automata checkers) |
| violable/contrary-to-duty norms | **out of fragment** | needs violation-state semantics |
| counterfactuals, generics, habituals | **out of fragment** | — |

The growth path is the repo's founding rule applied to linguistics —
**outsource everything that exists**: each excluded phenomenon corresponds to
a formal extension with an off-the-shelf checker (relational logic for
individuals, LTL model checking for eventualities, timed automata for
deadlines), and the Reading grows one logical form at a time, each arriving
with its own proof obligation, entailed scenarios, and provenance rule. The
tower climbs by enlarging the fragment checker-first — never by letting the
analysis outrun what the kernel can adjudicate.

## 9. The claim, precisely

For requests whose demanded content lies in the **safety fragment of a
deontic-temporal logic over agent-symmetric integer aggregates**, the system
turns vague directives into running services such that:

1. code–analysis fidelity is **machine-checked** (proofs + entailed
   scenarios, dual-checker rule throughout);
2. every claimed obligation is **textually grounded** (verbatim quotation,
   checked exactly);
3. every interpretive act is **ledgered** (`choice` records + provenance
   chain from span to proof);
4. contradiction, fabrication, and choice-over-text are **refused
   mechanically**, each at its own stage;
5. the irreducible residue — construal of one quoted span by one small
   formula, and coverage of what was never written — is **narrowed,
   localized, and cross-examined**, and is honestly labeled as evidence
   rather than proof (TRUST.md §3.4).

That is what the system achieves: not understanding, but the compositional
containment of misunderstanding.

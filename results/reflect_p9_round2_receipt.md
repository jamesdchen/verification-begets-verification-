# Round 2 for `refusal-set-carrier` — COMPARED, the last capability the measurement names

*(the same purchase-driver firing that consumed round 1 and merged PR #162;
consuming freed the single slot, so this round could be authored into it)*

## The purchase that was not made

`python3 tools/lean_env_probe.py`, **run** in this container, never read off
disk:

    lean-absent:not-installed

Not `lean-local`, so PLAN_FRAGMENT §3.1 rule 3's YIELD clause fires and this
unattended session did not take a tower-class bill.

`python3 tools/purchase_frontier.py`, regenerated this session: **13 rows, 3
open, 0 ready**. Not one open row is additive-class —
`refusal-symbolic-exponent` iteration-class, `refusal-function-symbol`
definitional-extension, `refusal-set-carrier` tower-class — so the yield is
TOTAL rather than partial: there is no strictly-first Lean-free half to ship,
because no open row has one. Yielding the purchase is not yielding the
session, so the session consumed the open ride and authored the next round.

## Why this round is driven by a MEASUREMENT and not by a transcript

Round 1 PASSED. A pass carries `detail: null` **by design** — there is no
failure transcript to seed from — and that is explicitly not a dead end: the
measurement is the work queue, so the prototype is EXTENDED toward the next
requirement the row still names as unmet, one addition per round so a
regression stays attributable.

`results/c3_cycle_16.md` prices this row's gap as exactly three things P2's
`setbuild` cannot do (bold rendered as capitals, otherwise verbatim):

> a set can be **counted** but never inhabited, named, or compared.

| capability | round | state |
|---|---|---|
| **INHABITED** — `memS`, `PdS.pmem`, `denoteS` | r1 | PASSED |
| **NAMED** — `StS.svar`, the opaque set that therefore survives unfolding | r1 | PASSED |
| **COMPARED** — subset and set equality over set objects | **r2** | **this round** |

Round 1 left COMPARED unmet **by declaration** and recorded it in
`results/reflect_p9_round1_receipt.md` as round 2's single requirement. This
round takes it and nothing else.

## Why subset and set equality are ONE requirement, not two

The subjects that earned this signal are in the same cycle-16 table:

| subject | gate verdict | signal |
|---|---|---|
| `09_Sets#problem-005` (set equality) | `unknown atom/connective 'iff'` | `iff-connective` |
| `09_Sets#problem-017` (powerset) | `unknown atom/connective 'not'` | `not-connective` |
| ↳ probed past `not` | `unknown atom/connective 'mem'` | **`set-membership`** |

A powerset membership question *is* a subset question — `S ∈ 𝒫(T)` asks
`S ⊆ T` — so the two subjects that reached the `mem` atom price containment
and equality together. Splitting them would be two rounds pretending to be
independent.

## What COMPARED costs, arm by arm

| declaration | what it answers |
|---|---|
| `PdS.psub` / `PdS.pseteq` | the two new predicate arms: containment and set equality |
| `denoteS_psub` / `denoteS_pseteq` | one `rfl` unfolding tooth per new arm, so a silently mis-denoted arm cannot pass unnoticed (round 1's discipline, continued) |
| `boolS_ext` | Bool extensionality, proved **here** from `cases` rather than cited from Mathlib, so the round does not ride on a lemma NAME the pinned imports may spell differently — a failure should be about the construct, not about a citation |
| `pseteq_iff_mutual_psub` | **the theorem that makes the layer worth adopting**: set equality is mutual containment, which is exactly the reasoning step `#problem-005` asks for |
| `psub_sinter_left` | one concrete comparison fact, so the layer is shown to REASON and not merely to typecheck |

`pseteq` is denoted as pointwise `Bool` equality — the honest "same members"
reading — precisely so that antisymmetry has to be **proved** rather than
built in by definition. Denoting it *as* mutual containment would have made
`pseteq_iff_mutual_psub` an `Iff.rfl` and bought nothing.

Round 1's `TmS` / `evalTmS` / `StS` / `memS` and its four `rfl` teeth are
carried forward **verbatim**: a candidate is APPENDED text — the committed
`tools/FgReflect.lean`, then this text re-entering `namespace FgReflect` — and
nothing round 1 declared was adopted into the slice. The same splice
constraint is why this stays a PARALLEL tower: `Tm` and `Pd` cannot be
extended from appended text, so a set carrier lives in an inductive of its own
naming.

## What a pass would settle — including that authoring on this row would STOP

A pass would close the third and last capability `results/c3_cycle_16.md`
names for this row. The PASSED rule's terminal branch would then fire: the
measurement would name nothing further unmet, authoring on `refusal-set-carrier`
stops, and **adopting** the prototype into `tools/FgReflect.lean` is an
ATTENDED purchase decision under the ordinary bill discipline — never an
unattended session's act. All three open rows would then have complete
authoring queues (`refusal-symbolic-exponent` at r5,
`refusal-function-symbol` at r2, this one at r2), each closed on its own
measurement's terms rather than by running out of ideas.

A pass would **not**:

* change the row's class or status — still tower-class, still OPEN;
* move the ceiling this row records against its own interest.
  `results/purchase_frontier.json`, regenerated this session, still computes
  `refused_group_memberships: 4`,
  `held_by_a_signal_this_row_does_not_meet: 4`, `returns_to_ready: 0` — all
  four `set-membership` subjects carry a refusal this row does not meet, so it
  returns ZERO subjects to ready on its own and lands material only beside P6;
* touch the slice. `tools/FgReflect.lean` has no write path from the candidate
  queue. "It elaborated in the batch ride" is a reason to keep authoring and
  never a done-predicate; the CI lane verdict stays final.

## Bounds

No ceremony-reserved surface touched. P5 remains a trust root this session did
not promote. Batch reproduces at **24 goals** (`queued=114, unresolved=0`) with
`+1 authoring` candidate — both `assemble` flags passed, so the queued goals
are not silently dropped — and the readout is regenerated from the new batch so
its reproduction teeth stay green. Ride marker written unbracketed as
lean-hammer everywhere except the ride commit message itself.

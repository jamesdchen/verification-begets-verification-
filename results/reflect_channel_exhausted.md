# The authoring channel is out of rounds — measured on all three open rows

*(a purchase-driver firing that found the in-flight guard clear, YIELDED the
bill on a measured probe verdict, walked the authoring ride's three steps and
found every one of them empty — and spent itself moving that reading out of
three scattered receipts into the one place the next firing looks)*

## Why this commit exists rather than a bare no-op summary

The purchase prompt permits exactly one honest no-op on the authoring route:
*"a row whose class measurement names NO construct you could prototype — and
then say WHICH row and WHICH measurement you read, so the next firing starts
from your reading instead of re-deriving it."*

This firing is that no-op, and it is the SECOND consecutive firing to reach it.
The first (PR #164, `results/reflect_p9_round2_consumption.md`) said so in a
consumption receipt for one row. But a firing does not start by reading three
per-row receipts — it starts at `tools/session_brief.py`, which quotes
PLAN_FRAGMENT §1 verbatim. A reading that lives only where the next firing
will not look gets re-derived every firing, which is what happened here: this
session re-read all three class measurements to learn what the tree already
knew. So the deliverable is the reading, written where the brief will hand it
to the next session — and nothing else. No round was authored, no ride was
taken, no bill was paid, and no slice text was touched.

## The three steps of the ride, each walked and each empty

**(1) CONSUME.** `list_pull_requests(state=open)` returned this session's own
claim and nothing else: no open `C3 authoring ...` PR, so the single-slot
channel is free and there is nothing to consume. The slot being FREE is what
makes the emptiness below a real reading rather than a deferral — the 2026-07-26
wedge (three firings deferring to a finished ride) is not what happened here.

**(2) AUTHOR.** Nothing to author. All three open rows have COMPLETE authoring
queues, each closed on its own committed class measurement, and each closure
re-verified against that measurement this session rather than taken from the
receipt's word:

| open row | class measurement read | rounds | terminal because |
|---|---|---|---|
| `refusal-symbolic-exponent` (iteration-class) | `tests/test_symbolic_exponent_class.py` | r1–r5, all PASSED | the measurement names `evalTm`, `substTm`, `evalTmN`, `substTm_evalTm`, `evalTmN_subst` and the `check`/`decDenote` case; r5 took the last one (`results/reflect_round5_consumption.md`) |
| `refusal-function-symbol` (definitional-extension) | `tests/test_function_symbol_class.py`, finding (4) | r1–r2, both PASSED | the measurement prices the rung at EXACTLY TWO costs in its own docstring — an application node and a new `Decidable` story — and r2 took the second (`results/reflect_p8_round2_consumption.md`) |
| `refusal-set-carrier` (tower-class) | `results/c3_cycle_16.md` line 93 | r1–r2, both PASSED | the measurement names exactly three things `setbuild` cannot do — a set can be counted but never **inhabited**, **named** or **compared** — and r2 took COMPARED (`results/reflect_p9_round2_consumption.md`) |

Extending any of them further would need either a NEW class measurement naming
a construct no prototype has taken, or a NEW open row. Neither is an unattended
session's to manufacture, and inventing a construct no measurement names is the
one thing the seed rule forbids outright.

**(3) RIDE.** Nothing to ride: step (2) produced no candidate, and re-queueing a
PASSED candidate unchanged would re-run a round already ridden.

## The finding this walk exposed, and it is the one-path-over recurrence

`tools/supply_status.py`'s `attendance_routes` — regenerated this session, and
byte-identical to the committed copy — still names THREE exits for a
tower-class row: an attended session, a probe reading `lean-local`, **or the
batch-ride authoring kind**. The third is now measured EXHAUSTED on every open
row, by the table above. The watchdog quotes that verdict VERBATIM as the sole
alarm channel, so the alarm currently names an exit nobody can walk.

This is the LEXICAL-GREP defect §1 already recorded once for
`new-corpus-intake`, recurring one path over: a reading that says the driver
KNOWS the route, never that the route has a round left to take. It is recorded
here and NOT fixed, deliberately. The declaration filter that closed the sibling
defect worked because `corpus_candidates.select` could be ASKED — the state was
mechanically derivable from a committed registry. Here it is not: "does this
row's class measurement name anything still unmet?" is a judgment recorded in
receipt prose, and deriving it by grepping those receipts would re-commit the
very defect it means to close (two implementations of one rule drift, and the
drift is the defect). A mechanical route would need the queue rows to carry
their own terminal flag, which is a schema change and an attended call.

## Both axes, stated together, because that is the standstill

* **Corpus loop**: `supply-blocked`, `declaration: registry-exhausted -- NOT
  unattended-takeable`. Needs one declared row in
  `specs/mathsources/corpus_candidates.json` whose HOST this container's egress
  policy permits (cycle 21 measured a 403 at the wire).
* **Purchase loop**: `python3 tools/lean_env_probe.py`, RUN this session and
  never read off disk, reads **`lean-absent:not-installed`** — not `lean-local`,
  so PLAN_FRAGMENT §3.1 rule 3's YIELD clause fires. `purchase_frontier`
  regenerated: 13 rows, 3 open, 0 ready, and not one open row is additive-class,
  so the yield is TOTAL rather than partial — there is no strictly-first
  Lean-free half to ship, because no open row has one. And the yield's own
  fallback, the authoring ride, is the channel this receipt reports empty.

Both drivers are firing and both are correctly finding nothing they may take.
That is BLOCKED, not DEAD, and the distinction still holds — but with the ride
exhausted, the unattended half of this loop has no move left on either axis, and
every exit that remains is a maintainer's.

## Bounds

No ceremony-reserved surface touched: `kernel/certs.py` pins, `TRUST.md`, the
escape-gate blocklist, `buildloop/growth_protocol.py`, `setup.sh`, `ci/`,
`.claude/` and `.github/` are all untouched. P5 remains a trust root this
session did not promote. `tools/FgReflect.lean` is untouched, as is
`results/reflect_candidates.json` — a passed candidate is a PROPOSAL, and
adopting one is an attended purchase decision under the ordinary bill
discipline. No purchase was made and no flywheel slot was spent: an authoring
PR buys nothing, which is why this is titled `C3 authoring` and stays invisible
to the one-per-cycle in-flight guard. The lane marker is written unbracketed as
lean-hammer here, as it must be everywhere that is not a ride commit message.

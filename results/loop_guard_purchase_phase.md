# The purchase loop's post-claim phase was unreachable

**Measured 2026-07-27T01:05Z**, by the first C3 purchase firing after
`tools/loop_guard.py` landed in #194 (00:37Z — twenty-eight minutes earlier).

## The defect

`#194` moved both loop guards out of the driver prompts and into code, and
split the decision into the two phases the cycle-12 measurement demands:

* **pre-claim** — "is anyone else working?"
* **post-claim** (`--mine`) — "did I win the race?"

The split was implemented **for the corpus loop only**. The purchase branch
returned before the `mine_created_at` block, so the call the PURCHASE DRIVER
prompt mandates —

```
python3 tools/loop_guard.py --loop purchase --now <RFC3339> --prs - --mine <claim created_at>
```

— reached the any-open-purchase rule and answered **EXIT on the session's own
freshly-opened claim draft**, every time. Measured live on this firing:

```
CLAIM: no open purchase PR; the price list is unspent          # pre-claim
EXIT (PR #198): an open `C3 purchase` PR exists; ...           # post-claim, on my own claim
```

The tool's own docstring already advertised `[--mine …]` on the purchase usage
line, so the **prose was right and the code was wrong** — the failure was not a
design disagreement but an unexecuted branch.

## Why it is a closed loop, not a lost firing

Obeying that EXIT leaves the claim draft open, and the litter then blocks every
successor:

| firing | board | verdict |
|---|---|---|
| 1 | clear | CLAIM → opens draft → **EXIT on its own draft** |
| 2 (+1h) | draft, age < lock | EXIT (pre-claim any-open-purchase rule) |
| 3 (+3h) | draft, age > lock | CLOSE-STALE → re-claim → **EXIT on its own draft** |

No purchase can ever land unattended, and the cycle regenerates its own
blocker indefinitely.

**The alarm channel was blind to it.** The watchdog counts a claim-only draft
under two hours as *a cycle in flight → activity*, so it would have reported
the purchase loop **healthy** for as long as this ran. A wedge the only alarm
cannot see is the expensive kind.

## The fix

The tie-break is **loop-agnostic** — it operates on the already
title-filtered `open_prs` — so it is hoisted above the purchase branch and now
serves both loops. The purchase loop's strictness is untouched: it lives
entirely in the **pre-claim** phase, which still exits on any open
`C3 purchase` PR regardless of age or CI state, and that is what protects
one-purchase-per-flywheel-cycle.

`READS FAIL SAFE` reaches the new branch: an unreadable `--mine` returns EXIT,
never CLAIM.

## Verification

Five teeth, **mutation-verified in both directions**:

* `test_a_session_never_exits_on_its_own_claim` — now parameterized over
  **both** loops; reverting the fix reds the `purchase` case and only that case.
* `test_the_post_claim_tie_break_yields_to_an_earlier_claim_on_both_loops` —
  the other direction, so `return CLAIM` cannot pass as the fix; a rubber-stamp
  mutation reds it on both loops plus the pre-existing corpus test.
* `test_the_purchase_guard_stays_strict_in_its_PRE_claim_phase` — the fix must
  not widen the one-purchase-per-cycle rule.
* `test_the_purchase_post_claim_phase_fails_safe_on_an_unreadable_mine`.

## The lesson, recorded

`results/lessons.jsonl`: *a tooth parameterized over one of two symmetric
callers certifies the caller it skips.* The original pinning was written the
same hour as the bug it failed to catch, by the change that introduced both.

## Bounds

No ceremony-reserved path in the diff (`buildloop/growth_protocol.py`,
`kernel/certs.py`, `TRUST.md`, `setup.sh`, `ci/`, `.claude/`, `.github/` all
untouched). Lean-free; P5 not promoted; no park lifted; the ledgers stay
append-only. **No purchase was priced this firing** — this PR is titled
`C3 guard:` deliberately, so it buys no purchase, spends no flywheel slot, and
stays invisible to both loop guards.

# C3 cycle 21 — path (c) walked unattended for the first time, and refused at the wire

**Axis:** corpus. **Shipped: 0 sources. Frontier refusals: 0 new rows. Parks: 0.**
Corpus **121 → 121**; governed exogenous coverage **114 → 114**; ready **0 → 0**.
Full suite green.

Two products, neither of them a source:

1. a **registry refusal row** — the declared corpus `prime_number_theorem_and`
   is unreachable from a driver container, measured rather than predicted; and
2. a **closed instrument defect** — `tools/supply_status.py` was naming
   `new-corpus-intake` as an exit in the same firing whose selector had just
   answered `registry-exhausted`.

The second exists because of the first. This is the cycle that walked the
automated intake path end to end for the first time, and walking it is what
exposed the meter above it.

## What the cycle did

The freshness guard passed (no open `C3 cycle...` PR), the claim landed as
draft PR #143, and the yield re-query 60s later found no earlier claim. Ready
was **0**, so the driver took §3.2 path (c) exactly as the DRIVER prompt
orders: consult the declaration point first, run what it prints, verbatim.

```
$ python3 tools/corpus_candidates.py
reason: candidate-available  (a declared row is selectable; ...)
declared: candidate=1, example=1, intaken=6, refused=0
SELECTED: prime_number_theorem_and  (adapter blueprint)
```

That row was appended by an attended session (merged as #140) at the
maintainer's instruction, and it **anticipated this outcome in writing**:

> The URL follows the pattern every intaken row uses
> (`<owner>.github.io/<repo>/blueprint/`) but could NOT be verified from the
> declaring container: the agent proxy restricts the GitHub API to session
> repositories and 403s every corpus host. If the fetch or the adapter
> refuses, that is the expected recorded outcome.

It refused:

```
$ python3 tools/intake_corpus.py --name prime_number_theorem_and \
    --source https://alexkontorovich.github.io/PrimeNumberTheoremAnd/blueprint/ \
    --adapter blueprint --project "..."
urllib.error.URLError: <urlopen error Tunnel connection failed: 403 Forbidden>

$ curl -sS "$HTTPS_PROXY/__agentproxy/status"
  "recentRelayFailures": [{
     "ts": "2026-07-26T06:39:32.589Z",
     "kind": "connect_rejected",
     "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)",
     "host": "alexkontorovich.github.io:443" }]
```

**Not retried.** The hiccup protocol's 2s/4s/8s/16s backoff exists for 5xx and
timeouts; this is an organization egress-policy denial, and the proxy runbook
(`/root/.ccr/README.md`) says so in its own words — *"Do not retry or route
around it — report the blocked host."* Spending four backoffs to re-learn a
decided fact is the defect `lean_env_probe`'s never-retry-a-policy-denial rule
already names one layer up, and PR #142 names one layer down.

The row is marked, with the reason, and the row STANDS:

```
$ python3 tools/corpus_candidates.py --mark prime_number_theorem_and refused --reason "..."
prime_number_theorem_and: status -> refused
```

**What this refusal is NOT.** It is a REACHABILITY reading, not a fidelity
one. The adapter never ran; not one page was fetched; nothing whatever was
learned about whether this corpus is near the fragment. A future container
whose egress policy allows the host can re-declare it on the strength of the
rationale alone, and this row is the evidence of why it has to be re-declared
rather than an argument against the corpus. Recording it as *refused* rather
than deleting the row is the registry-is-evidence-not-inventory rule; recording
it as reachability rather than distance is the honesty rule that keeps the two
kinds of no distinguishable.

No second candidate was taken. One intake per corpus cycle — and taking
another to make the firing look productive is exactly what the prompt forbids.

## The defect the walk exposed

With the row spent, the registry declares zero `candidate` rows and the
selector answers `registry-exhausted`. The DRIVER prompt's own next sentence
sends a driver in that state to "a corpus the maintainer has NAMED" — which is
**attendance**. So after this cycle, no unattended firing can walk path (c).

`tools/supply_status.py` did not know that. Its verdict, regenerated on this
very firing, said:

> `supply-blocked: tower-class-only (...); new-corpus-intake (6 corpora already
> intaken, driver-automation: automates-new-corpus-intake); refusal-retirement (...)`

`machine_actionable: true`, on the strength of a **lexical grep of
`C3_PROMPTS.md`** for the string `intake_corpus`. The grep answers only half
the question: it says the driver KNOWS the command, never that the driver has a
row to run it on. The watchdog quotes that verdict verbatim every firing and is
told to "name the exits the verdict itself names" — so the sole alarm channel
would have gone on naming an exit nobody could walk.

This is the **attendance filter's defect, one path over**, and the §1 entry
recording that one says why it matters: the tool built precisely so a wedged
machine SAYS SO had the wedge's own blind spot, and three watchdog firings
reported healthy over a machine that could not move.

### The fix: THE DECLARATION FILTER

`machine_actionable` on `new-corpus-intake` now requires **both halves** — the
prompt automates the command AND the declaration point still holds a row marked
`candidate`. The declaration state is **asked of the selector**
(`tools/corpus_candidates.select`), never re-derived here: two implementations
of one rule drift, and that drift is the whole defect.

| selector reason | available | machine_actionable |
|---|---|---|
| `candidate-available` | yes | **yes** |
| `registry-empty` / `registry-exhausted` | yes | **no** — the exit is attended |
| `registry-absent` / `registry-unreadable` | yes | **no** — an errored read never impersonates an answer |

`available` deliberately stays **true** in every row: the supply really is
outside the tree, an attended session may name any corpus, and it is what keeps
a `supply-blocked` verdict from degenerating into a bare word with no exit
named. What changed is only the claim about who can walk it — and the reason
now rides in the **verdict string itself**, because the watchdog reads nothing
else:

> `... new-corpus-intake (6 corpora already intaken, driver-automation:
> automates-new-corpus-intake, declaration: registry-exhausted — NOT
> unattended-takeable); ...`

### Teeth

Five, in `tests/test_supply_status.py`, pinning the rule in **both**
directions (a whitelist checked only on the days it says no is half a
whitelist):

- `test_a_dry_registry_is_available_but_not_machine_actionable` — empty and
  exhausted, both shapes, verdict text included
- `test_a_declared_candidate_is_machine_actionable` — the other direction, so
  the gate cannot become a way of never reporting the one lever that has ever
  moved the ready list
- `test_both_halves_are_required_for_the_new_corpus_path` — the 2×2, so neither
  half alone computes actionable
- `test_an_unreadable_registry_is_never_read_as_no_candidates` — absent,
  non-JSON, and schema-broken all read as their own named reason
- `test_committed_declaration_state_is_read_from_the_selector_not_restated` —
  runs over the **committed** tree, the bill_class tooth's precedent: the state
  that was misreported was the real tree's, and a tooth that can only fire on a
  synthetic one would have missed it

Mutation-verified twice: dropping the registry half of the gate reds 4 tests;
restating the declaration reason locally instead of asking the selector reds
the same 4. `specs/mathsources/corpus_candidates.json` joins `INPUTS`, so a
moved registry reads as recorded staleness rather than a wrong derivation.

## Supply reading after this cycle

```
supply-blocked: tower-class-only (3 open rows need attendance or lean-local:
  refusal-function-symbol [definitional-extension], refusal-set-carrier
  [tower-class], refusal-symbolic-exponent [iteration-class]);
  new-corpus-intake (6 corpora already intaken, driver-automation:
  automates-new-corpus-intake, declaration: registry-exhausted -- NOT
  unattended-takeable);
  refusal-retirement (45 distinct subjects in refused:* groups)
```

**Every** supply path is now attended-only, and for the first time the
instrument says which kind of attention each one wants:

- **(a)/(d)** — purchase-gated, and all three open rows are outside the
  additive family, so §3.1 rule 3 yields on every one of them unattended.
- **(b)** — structurally empty; the park ledger has zero rows.
- **(c)** — needs one appended row, and after this cycle it needs something
  the last row did not have: **a host this container's egress policy allows**.

That last point is the maintainer-facing product of this cycle, and it is a
question no session can answer for itself. A declared row whose host 403s costs
one cycle and buys a measurement — which is the trade the declaring session
named and took deliberately. Declaring a *second* row against an unknown host
would buy the same measurement again. The cheaper next move is to establish
which corpus hosts are reachable at all, or to declare from a host already
proven reachable, before writing the next rationale.

## Boundaries held

No trust-surface-reserved surface touched (`kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/` all
untouched). No park lifted. No frontier refusal row invented from a transport
error — the ledger is for measured certification refusals, and a 403 is not a
reading of a subject. No registration re-baseline: no source was added, no
reading changed, and every count the file registers is unmoved.

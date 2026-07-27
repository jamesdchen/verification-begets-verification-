# The tower-class row's price was never only its Lean text

*(C3 purchase-axis firing, 2026-07-27T06:06Z.  **No purchase priced.**  The
one open row on the derived queue is `refusal-set-carrier`, and this firing
measured why paying it would buy nothing — then moved that measurement out of
a test docstring and onto the artifact a driver selects from.)*

Probe verdict, RUN in this container and quoted verbatim: **`lean-local`**
(`tools/lean_env_probe.py`, not read off disk).  So PLAN_FRAGMENT §3.1 rule
3's YIELD clause did not fire and the tower-class attempt was licensed.  The
row was declined anyway, for a reason that has nothing to do with attendance —
which is the finding.

## What the queue said, and what it could not say

`results/purchase_frontier.json` carried `refusal-set-carrier` as
`status: open`, `bill_class: tower-class`, `returns_to_ready: 0`, with the 0
attributed to `held_by_a_signal_this_row_does_not_meet: 1`.  Read straight,
that says: *a co-refusal holds this row's one subject; meet the other signal
and it frees up.*  `results/supply_status.json` then routed the row to
`supply-blocked: tower-class-only (… need attendance or lean-local)`.

Both readings are individually true and together they point a maintainer at
the wrong exit.

## The binding constraint is the decision procedure, not the bill

Every binder in this pipeline is decided by **sweeping its box-relativized
domain** — `run/formalize.py` stage 4 is pure `math_eval`, and the SMT mirror
is reached only from `_nonvacuity` and only over hypotheses, so it never sees
the conclusion.  An ordinary object binder contributes its box width.  A
**set** binder contributes the **powerset** of that box.

`tests/test_set_carrier_box_domain.py` measured this before this firing.  At
the committed bound (`run/anchor.py::BOUND = 8`):

| | box width | domain |
|---|---|---|
| `09_Sets#definition-003` — 2 set binders + 1 object, Int | 17 | **292,057,776,128** |
| the ceiling (`EXISTS_SHADOW_MAX_ASSIGNMENTS`) | — | 2,000,000 |
| the same construct, 1 set binder + 1 object, **Nat** | 9 | **4,608** |

`09_Sets#definition-003` is this row's **whole measured inventory** — one
subject.  So paying the tower-class bill in full, however well the Lean is
authored, leaves the row's entire inventory outside the sweep.  **Attendance
is not this row's exit.**  A re-bound of the gate, or a subject at a smaller
carrier, is.

### The sharper half: it would hang, not skip

`exists_shadow_shape` returns `forall-only` **before** it consults
`EXISTS_SHADOW_MAX_ASSIGNMENTS`, so the only combinatorial ceiling the gate
has guards the ∃ path alone.  The lead subject is a **definition** — ∀-only.
A paid tower would therefore not be honest-skipped as
`exists-domain-too-large`; nothing would stop it.

That distinction matters to a reader: a row that returns 0 reads as
*unprofitable*, and a row that would install a **hang** reads as something
else.  The artifact now says which.

## The defect, in house terms

CLAUDE.md: *a decision that branches on machine-readable state never ships as
a paragraph — it ships as a tool the paragraph points at.*  The measurement
existed and was committed; it lived in one test module's docstrings.  The
instrument a driver actually selects from did not carry it, so **three
consecutive firings** paid to re-derive it:

* **PR #203** read `lean-local`, was licensed, measured the bill's shape, declined.
* **PR #212** read `lean-local`, was licensed, spent its ride on the authoring channel instead.
* **this firing** read `lean-local`, was licensed, and declined for the same reason.

Each was individually correct.  Three of them is an instrument defect.

## What shipped

`tools/purchase_frontier.py` now publishes a derived **`decision_domain`**
block on any row whose subject shape has been measured, and the refill
projection carries **`outside_decision_domain`** beside the co-refusal count:

```
"decision_domain": {
  "shape": {"set_binders": 2, "object_binders": 1, "carrier": "Int"},
  "bound": 8, "box_width": 17,
  "assignments": 292057776128, "ceiling": 2000000,
  "inside_decision_procedure": false,
  "ceiling_guards_this_subject": false,
  "hazard": "… would not be honest-skipped … nothing would stop it",
  "reading": "… ATTENDANCE IS NOT THIS ROW'S EXIT …"
}
```

**The numbers are derived, never typed.**  The *shape* (how many set binders,
how many object binders, at which carrier) is a DECLARATION cited to the class
measurement, exactly as `bill_class` is; the arithmetic on top reads
`math_eval._box_size`, `math_eval.EXISTS_SHADOW_MAX_ASSIGNMENTS` and
`run/anchor.py::BOUND` live.  Re-bounding the gate re-prices the row with no
edit to the tool, and a row that becomes decidable says so by itself.

**Omission reads as `not measured`, never as `decidable`.**  Every other row
on the board publishes no `decision_domain` at all, and a tooth pins that none
of them can acquire an `inside_decision_procedure: true` by default.

The row's `bill_class` also now cites the measurement it rests on
(`class_evidence`), which the builder already enforces in both directions: the
cited file must still contain the named test, **and** the row's published
notes must cite the same path.

## The split this prices, stated but NOT taken

A row impossible at one carrier and cheap at another is **two rungs wearing
one name** — the P8 and P9 finding, a third time.  Here the split line is the
**carrier and the binder count**, not the vocabulary: one set binder over a
Nat box is 4,608 assignments and well inside the ceiling.

This firing did **not** split the row, and the reason is honesty about demand
rather than caution: the tractable rung's measured inventory is **zero
subjects** — the one inventory subject is Int with two set binders.  Buying a
rung that prices no measured demand is exactly the widening the purchase
discipline forbids, and it would manufacture a green.  The split is recorded
here as priced and available to a cycle that has a subject for it.

## Verification

Ten teeth (`tests/test_purchase_decision_domain.py`), **mutation-verified in
three directions**, each redding exactly its own:

| mutation | result |
|---|---|
| stop publishing `decision_domain` | 3 failed |
| force `inside_decision_procedure = True` | 3 failed |
| drop the projection's `outside_decision_domain` | 1 failed |

Presence teeth assert against **both** the committed artifact and a **fresh**
`build_purchase_frontier` derivation — an earlier draft asserted only against
the committed file, and mutations 1 and 3 passed under it, because yesterday's
field survives in a committed artifact until someone regenerates.

## The authoring ride this firing also consumed

The single-slot channel was owned by **#212**, whose lane had **finished**.
The measured failure mode is consecutive firings each deferring correctly
while the channel runs once, so this session consumed it rather than deferring:
merged main (the two append-only ledgers conflicted and were union-merged —
append-only means both sides' rows stand), ran the readout, ran the gate,
re-committed under its own credentials, and merged #212 at 22 green checks.

**`p9-parallel-tower-r4` PASSED on the CI Lean lane** — `gate_ok=true
elaborated=true replayed=true`, axioms `Quot.sound, lcProof, propext`, inside
the measured whitelist.  The lane's own commit-back tip carried **zero check
runs** (it pushes with `GITHUB_TOKEN`, firing no workflows) and must never
merge as it stands; re-committing under this session's credentials is what
re-armed them.  Detail in `results/p10_closure_constants.md`.

That upgrades the set-carrier tower's *prototype* from one container's local
green to the lane's verdict.  It does not change anything above: the tower
still would not decide the row's inventory, which is a fact about the sweep
and not about the Lean.

## Bounds

`tools/FgReflect.lean` **byte-unchanged**.  No ceremony-reserved surface in
the diff — `kernel/certs.py`, `TRUST.md`, `buildloop/growth_protocol.py`,
`buildloop/validate_lean.py`, `setup.sh`, `ci/`, `.claude/`, `.github/`
untouched.  The `ANTI_LIST` and the escape-gate blocklist were read, never
edited.  P5 not promoted.  No park recorded or lifted; **no refusal recorded**
— nothing here is a reading about a corpus subject.  Ledgers append-only.
**No purchase priced**, so no flywheel slot spent and no re-census delta owed;
the title is deliberately not `C3 purchase`, so this PR stays invisible to the
in-flight guard.

Gate: `CGB_LEAN=0 python3 -m pytest tests/ -q`.

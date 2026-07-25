# P4 purchase — the residue carrier `ZMod n` (PLAN_FRAGMENT §2/§4 P4)

**The purchase.** The parametric residue carrier `ZMod n` landed through the
full admission bill, riding the carrier machinery P3 built for `Rat`. It is the
second purchase on the carrier axis and the first anywhere here to buy a
**family** rather than a type: a carrier string matching `ZMod <n>` at a
LITERAL modulus `n >= 1` — the exact Lean type text, single-spaced, because
binders emit it verbatim. The admissibility argument is P1's and D10's,
one more time: a literal makes it exact. A literal modulus makes the carrier
FINITE, and a finite carrier makes the domain sweep the whole world rather
than a window on it.

The family is carried by a PREDICATE (`_zmod_modulus`), never by a row in
`CARRIERS`, which stays `("Nat", "Int", "Rat")`. That is the design decision
the rest of the bill hangs off: every consumer that ENUMERATES carriers — the
census aliases, `_BUILTIN_CARRIER_SUPPORT` and the miner's op-slot typing, the
admitted-operator certificate rows, the tower census — keeps its pre-P4
behaviour byte-for-byte, because none of them can see a carrier that is not in
the tuple.

## The bill, item by item

- **validator / scope** (`generators/math_reading.py`): `_zmod_modulus` as the
  family predicate; `_carrier_miss_guess` splitting the refusals; every
  `ty not in CARRIERS` check site extended with `and _zmod_modulus(ty) is None`
  (object type, ambient carrier, operator carrier); `_check_zmod_ops` as the
  carrier-admissibility walk (the `_check_carrier_ops` shape P3 froze);
  `_zmod_of` / `_check_zmod_carrier` pinning ONE residue carrier per reading;
  `_term_ref_carriers` admitting residue strings so the B1 `-` walk sees them;
  `MATH_LF_KINDS` signature strings now read `Nat|Int|Rat|ZMod <n>`;
- **eval semantics** (`generators/math_eval.py`): `_zmod_carrier_of` resolving
  the residue carrier from the reading's OBJECT MAP (not from a term's refs —
  an all-literal `2 - 4` inside a `ZMod 5` reading is a residue term, and
  resolving by first-ref would hand it to the Int rule, which is the D8-class
  divergence the battery plants); `_term_carrier`'s residue arm answering ABOVE
  the ambient/first-ref chain, so `-` takes real subtraction and never Nat
  truncation; the `% n` reduction at each `=`/`!=` ATOM, which is the one node
  where the quotient is observable; `enumerate_domain` / `_ranges_for` /
  `_box_size` sweeping `range(0, n)` — the EXACT carrier, `bound` deliberately
  ignored;
- **SMT mirror** (`generators/math_smt.py`): residue objects declared `Int`
  with `(assert (and (<= 0 x) (< x n)))`, so the solver's world is the
  evaluator's world; `_zmod_wrap` emitting `(mod _ n)` on BOTH sides of every
  `=`/`!=` atom — the constant-folded `y > 0` branch of the general `%`
  emission, so no dead `ite` tower rides along and a linear residue obligation
  stays `QF_LIA`; `_minus_carrier`'s residue arm rendering `-` plain;
- **Lean rendering** (`generators/math_compile.py`): nothing structural. The
  binder emits `(x : ZMod 7)` verbatim and `+ * - ^ = ≠` are CommRing notation,
  so the residue carrier costs the emitter no new rule and no new name lookup;
  `_lean_name` is never consulted, because the only carrier-indexed words are
  refused at `ZMod n` by the gate;
- **prompt grammar** (`buildloop/math_prompt.py`): the `_PRED_AST_NOTE` residue
  paragraph (literal modulus, `+ * - ^` and `= !=` only, no order, no
  divisibility family, no binder, one modulus per reading) and the regenerated
  golden;
- **growth registry** (`buildloop/growth_protocol.py`): the `zmod-carrier`
  GROWERS row, all seven roles, completeness canary green; `_zmod_modulus` and
  `_check_zmod_ops` signature-pinned; the generic `"carriers"` PLANNED
  intention now covers only the rest of the axis (ordered / field / abstract
  typeclass carriers), because both carrier growers have real rows;
- **reflect** (`run/reflect_shadow.py`): nothing new was needed. P3's
  fail-CLOSED layer choice (`_reflect_layer_is_nat`) already refuses any
  carrier outside the two PROVEN layers, and it covers the residue family for
  free — `ZMod 5` is no more one of Int/Nat than `Rat` is. The frozen skip
  vocabulary's entry gained the residue family by name, nothing else moved;
- **batteries** (`tests/test_zmod_battery.py`): 18 rows, 27 collected teeth,
  real dual-solver (z3 + cvc5, absent cvc5 degrading honestly).

## The measured delta: ZERO, predicted and confirmed

The prediction was written before the purchase and it held. `ZMod` contributes
no new fragment word — `"modulo"`, `"congruent"`, `"remainder"` were already in
`_FRAGMENT_WORDS` — so `tools/blueprint_census.py` was not touched, and
`buildloop/census.py` was not touched either (the enforcement loop iterates
`math_reading.CARRIERS`, which the family predicate deliberately stays out of;
there was no `ZMod` blocker row to retire, and the `Fin` / `class:group` rows
stay exactly where they were, because typeclass demand is still a blocker).

`python3 tools/regen_downstream.py --from census_portfolio` over the six
committed corpora (1 008 nodes) returns every artifact **byte-identical**:

| verdict | before | after |
|---|---|---|
| `attempt-candidate` | 108 | **108** |
| `no-signal` | 169 | **169** |
| `out-of-fragment` | 731 | **731** |

The miss histogram is unchanged row for row, including the two rows this
purchase is priced against: `algebra-structures` **97**, `algebra-abstract`
**45**. The mathlib-side census (`specs/mathsources/mathlib/census.json`) is
likewise unchanged, because no pattern row moved. The only regenerated artifact
that differs is `results/purchase_frontier.json`, where `p4-carrier` flips
`open → purchased` off the live registry row — status read from the tree, as
that view requires.

**The honest reading.** This is the P1/P2 outcome, for the P1/P2 reason: the
census is LEXICAL, and the corpus prose that mentions modular arithmetic states
it at a SYMBOLIC modulus (`n`, `p`, `q`) or as a `≡ mod` congruence over the
integers, neither of which this purchase buys. A zero delta is evidence, not a
failure to record — and the attribution instrument that makes it readable is
the `algebra-abstract` sub-signal shipped in the P3 cycle: of the 97
`algebra-structures` nodes, **45** carry parametric typeclass demand that no
concrete carrier can ever claim, leaving a **52**-node concrete residue as the
class P4 aims at. It does not reach that class at a literal modulus this cycle,
and saying so is the point of having split the signal.

**What the purchase DOES buy, and it is not nothing:** a pure-residue reading's
domain sweep is the WHOLE carrier. `enumerate_domain` over `ZMod 3` yields
exactly three assignments and yields the same three at every bound, so
`bounded_nonvacuous`, `satisfying_instances` and the ∃-shadow stop being
bound-relative evidence and become **COMPLETE DECISIONS** — the first carrier
here for which that is true. Nothing else in the fragment can say it: `Nat`,
`Int` and `Rat` sweeps are all windows.

## The v1 freeze, as named limits rather than gaps

- **`carrier:zmod-symbolic-modulus`** — a modulus that is an object rather than
  a literal (`ZMod n`). The same shape P1 named as its future purchase for
  bounds; refused in writing, ranked by F4, and the largest single piece of
  what the corpus actually asks for.
- **`carrier:zmod-zero-modulus`** — `ZMod 0` is Lean's integers, not a finite
  quotient. It gets its OWN signal rather than sharing the symbolic one:
  collapsing the two would let either masquerade as evidence for the other.
- **Non-canonical spellings are NOT normalized.** `"ZMod 07"`, `"ZMod -1"` and
  the two-space form fall to the generic `carrier:<ty>` miss. The carrier
  string is the exact Lean type TEXT that binders emit verbatim, so admitting a
  second spelling would put two strings on one carrier and hand the mirrors two
  names for one thing. Named, not normalized.
- **No order, no divisibility family**: `<=`, `<`, `%`, `mod`, `dvd`, `gcd`,
  `coprime`, `even`, `odd` at a residue carrier are
  `operator:<op>@ZMod <n>` — refused BY CONSTRUCTION. A congruence class has no
  order and no remainder; admitting either would be an untruth the compiler
  would happily render.
- **No binder inside a residue reading** (`zmod:binder-index-carrier`): P1 pins
  a bound index to `Nat`, and a residue reading has no `Nat` to pin it to. The
  same refusal `Rat` takes, for the same reason.
- **One modulus per reading**, never mixed with `Nat`/`Int`/`Rat` or with
  another modulus, and no ambient rescues the mix. Two moduli are two unrelated
  carriers; the rule is READING-wide rather than per-pred, because both mirrors
  resolve the modulus from the object map.
- **`zmod:carrier-type` — elaboration is DEFERRED at the import pin.** The
  pinned `common.MATHLIB_IMPORTS` whitelist does not carry `ZMod`, so a residue
  statement RENDERS (ASCII-clean, escape-gate green) but does not elaborate.
  This is exactly the state P2's `Finset.card` rendering started in:
  text-level rendering here, lane elaboration deferred. Widening the import pin
  is cert-identity surgery — it re-keys committed certificates — so it is named
  future work with a ceremony, never a side effect of a fragment purchase.
- **The reflect slice skips by name**:
  `carrier-out-of-reflect-slice:ZMod <n>`, on both probe routes. The congruence
  image is the named next step — a residue `=` atom quotes as
  `Pd.pdvd (Tm.lit n) (Tm.sub a b)` through an `FgReflect.zmodEq` lemma — and
  that is a Lean-side proof, i.e. CI-lane work no default-branch session may
  assume. It retires the way `nat-sub-out-of-reflect-slice` did: on proof of the
  matching layer, never on convenience.
- **`zmod:unit-inverse`** — there is no division and no inverse at a residue
  carrier, not even at a prime modulus where every non-zero class has one.
  Buying it means buying the primality side condition with it, which is a
  different purchase.

## Inherited limit, restated rather than re-discovered

The witness emitter's templates are integer-shaped
(`generators/math_witness.py` builds them out of `eval_term` values and renders
them through the compiler). P3 named this as its `Fraction` residue: a `Rat`
reading raised inside emission before any skip could be returned, and P3 made
it UNREACHABLE by deciding the carrier ahead of emission on both reflect
routes rather than by widening the emitter. The residue carrier inherits the
same shape and the same reachability: residue values are ordinary Python ints
so nothing raises, but a template value is the UNREDUCED integer, and the
`run/anchor.py` route does not gate on carrier at all — it is unreachable only
because no committed reading carries a residue carrier and no residue statement
can elaborate at the import pin. Named here, unfixed, and the place any future
residue-witness work has to start.

## Teeth

`tests/test_zmod_battery.py` — 18 rows / 27 collected teeth on the
bigop/finset/rat battery template:

- a **differential value battery** (10 planted rows: a wrapping sum, a wrapping
  product, a NEGATIVE difference `2 - 4 = 3`, a `^` unroll, a literal above the
  modulus, a chained `- +`, a `!=` row, a deliberately FALSE row that must come
  back `unsat`, and two rows at a second modulus so nothing can hard-code 5),
  each verdict corroborated three ways — an independent Python residue oracle,
  `math_eval.eval_pred`, and the ground SMT differential on both solvers — plus
  a free-object row swept at every point of the complete domain;
- a **symbolic battery** (`x + 5 = x` and `x^2 = x*x` over the whole carrier
  with the param never pinned, plus a deliberately false idempotence identity
  that must come back `sat` — the battery can fail);
- **`test_lossy_mod_drop_gets_no_certificate`**, the planted-lossy tooth and
  the registry's divergence index: the same AST rendered at `Int` is exactly
  what a wrap-less residue mirror would emit, and both halves refuse it — the
  ground obligation flips `sat → unsat`, the symbolic one flips
  `unsat → sat` — with the evaluator witnessing each divergence pointwise, so
  neither solver verdict is an artefact of the encoding;
- the **D8-class carrier divergence**: one atom, two carriers, the SHARED
  residue domain, xor'd (`sat` = a divergence point exists) and always
  corroborated by an eval-witnessed point, because a solver existence claim is
  never load-bearing alone. The point is named: `x = 2`, where `2 - 4` is `3`
  over `ZMod 5` and plainly not `3` over `Z`;
- the **complete-decision** tooth, pinned three ways — the box has exactly `n`
  points, they are the `n` residues in canonical order, and the sweep bound
  cannot change either;
- the refusal surface (symbolic / zero / non-canonical modulus, order and
  mod-family operators, mixed moduli and mixed carriers, a binder index inside
  a residue reading), the `QF_LIA` / `QF_NIA` classification, the reflect skip
  in its current honest state, and an end-to-end
  gate → eval → compile → escape-gate row with a hash-stability check.

The GATE half of the registry's teeth index points at
`tests/test_math_reading.py::test_symbolic_modulus_is_a_fragment_miss`, where
that refusal is decided; the DIVERGENCE half points into the battery, where a
lowering is caught lying. One tooth per half of the bill, the shape every row
above it uses.

**Full suite green.** One purchase this cycle, its re-census delta committed in
the same session that measured it.

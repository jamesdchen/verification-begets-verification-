/-
WP-LI0 (PLAN_LEAN_IMPORT.md §4) -- the ENUMERATION SURFACE, Lean side.

Walks the environment obtained by importing Mathlib at the pinned checkout
(.lean-pins / common.MATHLIB_COMMIT; the checkout `setup.sh --with-lean`
places at .lean/mathlib) and emits ONE JSON LINE per surviving declaration:

    {"decl_name": ..., "module": ..., "kind": ..., "statement_pp": ...}

This file is a TRUSTED TOOL (like the compiler/verifier binaries in
common.run_cmd's contract): it is never LLM-authored text and never passes
through buildloop/validate_lean.py's escape gate.  It runs at enumeration
time only -- it never touches common.MATHLIB_IMPORTS (the certification
surface) or any certification cache key (plan §4: the two surfaces are
deliberately distinct).

Invocation (the Python runner tools/enumerate_mathlib.py drives this):

    cd $CGB_LEAN_MATHLIB   # default <repo>/.lean/mathlib, per setup.sh
    lake env lean --run <repo>/tools/EnumerateMathlib.lean \
        --out RAW.jsonl [--limit N] [--modules Mathlib.A,Mathlib.B]

  --out      (required) path the JSONL is written to.  Progress/diagnostics
             go to stderr only; stdout is left alone.
  --modules  comma-separated module list: import ONLY these (fast smoke
             runs) and keep only declarations that LIVE in one of them.
             Default: import `Mathlib`, keep modules named `Mathlib` or
             `Mathlib.*` (dependencies such as Init/Std/Batteries/Aesop are
             imported but NOT enumerated).
  --limit    keep only the first N rows AFTER sorting (deterministic
             truncation for smoke runs).  0 = no limit.

DETERMINISM.  Rows are sorted by (module, decl_name) before emission
(String codepoint order).  The Python runner re-sorts with the same key --
Python's sort is the CANONICAL one (P-LI0-CENSUS byte-identity is asserted
on the runner's output, not on this raw stream).  This program emits TEXT
ONLY -- no hashes; statement_hash is added Python-side from the repo's
single-sourced canonical hashing (common.sha256_json).

SKIP RULES (documented here, the single home):
  S1  names with macro scopes (hygienic elaboration internals);
  S2  names with any `_`-prefixed component (`_private.*`, `_aux_*`,
      `_impl`, ...) or any numeric component (compiler-generated);
  S3  names whose last component is a generated-lemma suffix:
      `eq_def`, `eq_unfold`, `eq_<digits>` (equation lemmas), `match_<...>`,
      `proof_<...>`, `injEq`, `sizeOf_spec`, `noConfusion`,
      `noConfusionType`, `below`, `ibelow`;
  S4  kernel-generated recursors and quotient primitives (ConstantInfo
      kinds `recInfo` / `quotInfo`) and the aux recursors
      (`casesOn`/`recOn`/`brecOn`/..., via Lean.isAuxRecursor);
  S5  declarations carrying the `@[deprecated]` attribute at the pin
      (Lean.Linter.isDeprecated) -- the import operation must never spend
      tokens on rows Mathlib itself has retired;
  S6  declarations with no owning module index (locally-declared; none
      arise here) and declarations whose pretty-print RAISES -- each pp
      failure is reported on stderr and the row is skipped, never half-
      emitted.

PRETTY-PRINTER PINS (the DOCUMENTED, FROZEN option set -- determinism of
this exact set is the requirement; changing any value is a queue-regeneration
event at the same pin and will trip the P-LI0-CENSUS byte-identity tooth):
  pp.fullNames  := true     -- constants print fully qualified (`Nat.gcd`,
                               `Nat.Prime`) so names stay regex-classifiable
                               by buildloop/census.py;
  pp.universes  := false    -- universe metavariables/params stay out of the
                               classification surface;
  pp.notation   := true     -- standard notation kept (∀, ∃, ∣, ℕ, ℤ, ...);
                               the census's pattern table speaks both the
                               notation and the full-name spellings;
  pp.deepTerms  := true     -- no `⋯` depth elision (an elided statement is
                               unclassifiable by construction);
  pp.maxSteps   := 5000000  -- effectively disable the step-count elision
                               for the same reason;
  format width  := 1000000  -- one (logical) line per statement; any
                               residual newline is JSON-escaped anyway.
-/
import Lean

open Lean

namespace EnumerateMathlib

structure Config where
  out : String := ""
  limitN : Nat := 0
  modules : Option (List String) := none
  deriving Repr

partial def parseArgs : List String → Config → Except String Config
  | [], cfg =>
      if cfg.out.isEmpty then .error "--out <path> is required" else .ok cfg
  | "--out" :: v :: rest, cfg => parseArgs rest { cfg with out := v }
  | "--limit" :: v :: rest, cfg =>
      match v.toNat? with
      | some n => parseArgs rest { cfg with limitN := n }
      | none => .error s!"--limit expects a natural number, got {v}"
  | "--modules" :: v :: rest, cfg =>
      let ms := (v.splitOn ",").filter (· ≠ "")
      if ms.isEmpty then .error "--modules expects a non-empty comma list"
      else parseArgs rest { cfg with modules := some ms }
  | a :: _, _ => .error s!"unknown argument {a}"

/-- ConstantInfo constructor -> the queue row's `kind` string. -/
def kindOf : ConstantInfo → String
  | .axiomInfo _  => "axiom"
  | .defnInfo _   => "def"
  | .thmInfo _    => "theorem"
  | .opaqueInfo _ => "opaque"
  | .quotInfo _   => "quot"
  | .inductInfo _ => "inductive"
  | .ctorInfo _   => "constructor"
  | .recInfo _    => "recursor"

/-- S3: generated-lemma suffixes on the last name component. -/
def auxSuffix (s : String) : Bool :=
  s == "eq_def" || s == "eq_unfold" || s == "injEq" || s == "sizeOf_spec" ||
  s == "noConfusion" || s == "noConfusionType" || s == "below" || s == "ibelow" ||
  s.startsWith "match_" || s.startsWith "proof_" ||
  (s.startsWith "eq_" && s.length > 3 && (s.drop 3).all Char.isDigit)

/-- S1 + S2 + S3 (the purely name-shaped skips). -/
def isSkippedName (n : Name) : Bool :=
  n.hasMacroScopes ||
  n.components.any (fun c =>
    match c with
    | .str _ s => s.startsWith "_"
    | .num _ _ => true
    | _        => false) ||
  (match n with
   | .str _ s => auxSuffix s
   | _ => true)

structure Row where
  module : String
  declName : String
  kind : String
  pp : String

def rowLt (a b : Row) : Bool :=
  if a.module == b.module then decide (a.declName < b.declName)
  else decide (a.module < b.module)

/-- Walk env.constants, apply S1..S6, pretty-print each surviving type. -/
def collect (cfg : Config) : CoreM (Array Row) := do
  let env ← getEnv
  let keepMod : String → Bool := fun m =>
    match cfg.modules with
    | some ms => ms.contains m
    | none    => m == "Mathlib" || m.startsWith "Mathlib."
  let mut out : Array Row := #[]
  let mut ppFailures : Nat := 0
  for (n, ci) in env.constants.toList do
    if isSkippedName n then continue
    let kind := kindOf ci
    if kind == "recursor" || kind == "quot" then continue           -- S4
    if isAuxRecursor env n then continue                            -- S4
    if Lean.Linter.isDeprecated env n then continue                 -- S5
    let some midx := env.getModuleIdxFor? n | continue              -- S6
    -- ModuleIdx is a plain `def` over Nat at v4.15.0 -> index via .toNat
    let modName := (env.header.moduleNames.getD midx.toNat Name.anonymous).toString
    if !keepMod modName then continue
    try
      let fmt ← Meta.MetaM.run' (Meta.ppExpr ci.type)
      out := out.push { module := modName, declName := n.toString,
                        kind := kind, pp := fmt.pretty (width := 1000000) }
    catch _ =>                                                      -- S6
      ppFailures := ppFailures + 1
      IO.eprintln s!"[EnumerateMathlib] pp failed, skipping {n}"
  if ppFailures > 0 then
    IO.eprintln s!"[EnumerateMathlib] {ppFailures} declaration(s) skipped on pp failure"
  return out

/-- The pinned pretty-printer option set (see header). -/
def ppOptions : Options :=
  let o : Options := {}
  let o := o.setBool `pp.fullNames true
  let o := o.setBool `pp.universes false
  let o := o.setBool `pp.notation true
  let o := o.setBool `pp.deepTerms true
  let o := o.setNat  `pp.maxSteps 5000000
  o

end EnumerateMathlib

open EnumerateMathlib in
unsafe def main (args : List String) : IO Unit := do
  Lean.enableInitializersExecution
  -- lean's `--run` does not forward dash-prefixed argv to the program (lean
  -- parses them itself and rejects unknowns), so the runner passes parameters
  -- via ENUMERATE_* environment variables; argv parsing remains as a fallback.
  let cfg ← match (← IO.getEnv "ENUMERATE_OUT") with
    | some out => do
        let limitN := ((← IO.getEnv "ENUMERATE_LIMIT").bind String.toNat?).getD 0
        let modules :=
          match (← IO.getEnv "ENUMERATE_MODULES").map
              (fun v => (v.splitOn ",").filter (· ≠ "")) with
          | some [] => none
          | m => m
        pure { out := out, limitN := limitN, modules := modules : Config }
    | none => match parseArgs args {} with
      | .error e => throw <| IO.userError s!"EnumerateMathlib: {e}"
      | .ok cfg => pure cfg
  initSearchPath (← findSysroot)
  let importNames := (cfg.modules.getD ["Mathlib"]).map String.toName
  IO.eprintln s!"[EnumerateMathlib] importing {importNames}"
  let env ← importModules (importNames.toArray.map fun m => { module := m })
              {} (trustLevel := 1024)
  let ctx : Core.Context := {
    fileName := "<EnumerateMathlib>", fileMap := default,
    options := ppOptions, maxHeartbeats := 0, maxRecDepth := 8192 }
  let (rows, _) ← (collect cfg).toIO ctx { env := env }
  let sorted := rows.qsort rowLt
  let sorted := if cfg.limitN > 0 then sorted.extract 0 cfg.limitN else sorted
  let h ← IO.FS.Handle.mk cfg.out IO.FS.Mode.write
  for r in sorted do
    let j := Json.mkObj [
      ("decl_name", Json.str r.declName),
      ("module", Json.str r.module),
      ("kind", Json.str r.kind),
      ("statement_pp", Json.str r.pp)]
    h.putStrLn j.compress
  h.flush
  IO.eprintln s!"[EnumerateMathlib] wrote {sorted.size} row(s) to {cfg.out}"

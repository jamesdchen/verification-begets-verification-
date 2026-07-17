"""WP-LI0 (PLAN_LEAN_IMPORT.md §4) -- the fragment-fit CENSUS: a
deterministic classifier over the declaration queue, and the frontier order.

    queue.jsonl (tools/enumerate_mathlib.py)
        -> classify_row per row (pure, Lean-free, zero LLM calls)
        -> specs/mathsources/mathlib/census.json   (byte-stable)
        -> frontier_order(queue_rows, census)      (P-LI0-ORDER)

THE RESIDENT SET IS DERIVED, NEVER COPIED.  ``derive_resident_set()`` reads
the F-G fragment live from ``generators/math_reading.py`` (MATH_OPERATORS,
CARRIERS, the builtin term/atom/connective op sets) and from the admitted
derived-operator registry ``specs/mathsources/operators/admitted.json``.
Admitted operators are eliminable by construction (plan §2.5 R3: their
definitions bottom out in kernel ops), so they contribute no new Lean
constants -- but the derivation still walks every admitted definition and
REFUSES (ValueError) if one mentions a non-kernel op, so a registry that
violated R3 could never silently widen the census's notion of "in fragment".
A fragment-vocabulary change in math_reading.py flows through automatically;
the only hand-maintained piece is the SURFACE ALIAS tables mapping each
derived fragment token to its Lean pretty-print spellings (``+`` is also
``Nat.add``/``HAdd.hAdd``; ``Nat`` is also ``ℕ``), and those tables are
keyed BY the derived tokens so an alias can never exist without its
fragment source (an uncovered new builtin raises at derive time).

CLASSIFICATION (per row, over ``statement_pp`` as pinned by
tools/EnumerateMathlib.lean -- pp.fullNames true keeps names regex-able):

  1. every pattern in MISS_PATTERNS (the extensible table below) is tested
     against the raw text; each match records one MISSING CONSTANT;
  2. all matched spans are then deleted and the RESIDUE is scanned:
     capitalized (dotted) identifier tokens not in the resident set, and
     non-ASCII characters outside the resident/structural symbol set;
  3. in_fragment  iff nothing was missing and the residue is empty
     (the statement mentions only F-G-resident constants/carriers);
     single-blocker iff exactly ONE missing constant and NO residue
     (adding that one constant would make the row in-fragment);
     unclassified iff nothing matched a pattern but residue remains
     (the table needs extending -- that is demand data, not an error).

SINGLE-BLOCKER vs BLOCKED_BY (the census's two count families -- the
distinction P-LI0/§8 prices kernel growth with):
  * unlock_counts[c]  -- rows for which c is the ONLY missing constant
    (and no unclassified residue): adding c to the fragment unlocks
    EXACTLY these rows.  This is the honest "adding Prime unlocks N rows"
    number -- a conservative, per-addition marginal gain.
  * blocked_by[c]     -- TOTAL rows whose missing set CONTAINS c, however
    many other blockers they have.  This is demand pressure, NOT unlock
    count: a row blocked by {Prime, Real} appears under both, and adding
    Prime alone unlocks none of it.  Summing blocked_by over-counts;
    summing unlock_counts never does.
  * co_occurrence     -- the top blocker PAIRS, so multi-blocker mass is
    visible instead of hidden in the blocked_by/unlock gap.

P-LI0-CENSUS (registered tooth): census regeneration at the same pin is
byte-identical -- build_census is a pure function of the queue rows + the
derived resident set, and render_census_bytes serializes with sorted keys,
fixed separators and LF only.  P-LI0-ORDER: frontier_order is a pure
function of (queue, census), deterministic and permutation-invariant (its
sort keys are total orders ending in the unique decl_name).

House rules: deterministic everything; zero LLM calls; no network; Lean-free.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import namedtuple

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import common  # noqa: E402
from generators import math_reading  # noqa: E402

ADMITTED_PATH = _ROOT / "specs" / "mathsources" / "operators" / "admitted.json"
QUEUE_PATH = _ROOT / "specs" / "mathsources" / "mathlib" / "queue.jsonl"
CENSUS_PATH = _ROOT / "specs" / "mathsources" / "mathlib" / "census.json"

# How many co-occurring blocker pairs the census reports.
CO_OCCURRENCE_TOP = 20

# ===========================================================================
# Surface alias tables (fragment token -> Lean pp spellings).
#
# KEYED BY the tokens derive_resident_set() reads out of math_reading, so an
# alias can never exist without its fragment source; a builtin added to
# math_reading without an alias row here makes derive_resident_set raise
# (loud, at import/derive time -- never a silently-wrong census).
# ===========================================================================
_CARRIER_ALIASES = {
    "Nat": ("Nat", "ℕ"),
    "Int": ("Int", "ℤ"),
}

_BUILTIN_ALIASES = {
    # term ops (math_reading._BUILTIN_TERM_OPS)
    "+": ("+", "Nat.add", "Int.add", "HAdd.hAdd"),
    "*": ("*", "Nat.mul", "Int.mul", "HMul.hMul"),
    "-": ("-", "Nat.sub", "Int.sub", "Int.neg", "HSub.hSub", "Neg.neg",
          "Nat.pred"),
    "%": ("%", "HMod.hMod"),
    "^": ("^", "HPow.hPow"),
    # atom ops (math_reading._BUILTIN_ATOM_OPS)
    "=": ("=", "Eq"),
    "!=": ("≠", "Ne"),
    "<=": ("≤", "LE.le", "Nat.le", "Int.le"),
    "<": ("<", "LT.lt", "Nat.lt", "Int.lt"),
    # connectives (math_reading._CONNECTIVES)
    "and": ("∧", "And"),
    "or": ("∨", "Or"),
    "implies": ("→",),
}

# Lexicon Lean names (MATH_OPERATORS[word]["lean"] values) that ALSO print
# as notation; names absent here alias only to themselves.
_LEXICON_ALIASES = {
    "Dvd.dvd": ("Dvd.dvd", "∣"),
    "Nat.mod": ("Nat.mod", "%"),
    "Int.emod": ("Int.emod", "%"),
}

# The fragment's quantifiers (F-G: ∀, bounded-shadow ∃) -- structural, not
# operator words, so listed here rather than derived from MATH_OPERATORS.
_QUANTIFIER_SURFACE = ("∀", "∃", "Exists")

# Structural pp characters that carry no constant at all: binder daggers,
# strict-implicit braces, anonymous-constructor brackets, primes and the
# sub-/superscript digits Lean uses in hygienic binder names.
_STRUCTURAL_SYMBOLS = frozenset(
    "✝⦃⦄⟨⟩′₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹")

_IDENT_ALIAS_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.']*$")

ResidentSet = namedtuple("ResidentSet", ["identifiers", "symbols"])


def _walk_definition_ops(node, out):
    """Collect every {op,...} op word inside an admitted-operator definition
    (preds and terms share the {op, args} shape)."""
    if not isinstance(node, dict):
        return
    if "op" in node:
        out.add(node["op"])
    for a in node.get("args", []):
        _walk_definition_ops(a, out)


def _add_alias(identifiers, symbols, alias):
    if _IDENT_ALIAS_RE.match(alias):
        identifiers.add(alias)
    elif len(alias) == 1 and ord(alias) > 0x7F:
        symbols.add(alias)
    # bare ASCII punctuation (+, %, <, ...) is implicitly allowed: the
    # residue scan only looks at identifier tokens and non-ASCII chars.


def derive_resident_set(admitted_path=ADMITTED_PATH) -> ResidentSet:
    """Derive the F-G-resident surface PROGRAMMATICALLY (never a hardcoded
    copy) from generators/math_reading.py + the admitted-operator registry.

    Returns ResidentSet(identifiers=frozenset[str], symbols=frozenset[str]):
    the capitalized-token allowlist and the non-ASCII character allowlist a
    statement_pp may use while staying in-fragment.

    Raises ValueError if (a) math_reading grew a builtin with no surface
    alias row, or (b) an admitted operator's definition mentions a
    non-kernel op (an R3 eliminability violation)."""
    identifiers, symbols = set(), set()

    # carriers
    for carrier in math_reading.CARRIERS:
        if carrier not in _CARRIER_ALIASES:
            raise ValueError(
                f"carrier {carrier!r} (math_reading.CARRIERS) has no surface "
                "alias row in census._CARRIER_ALIASES -- extend the table")
        for alias in _CARRIER_ALIASES[carrier]:
            _add_alias(identifiers, symbols, alias)

    # lexicon operators: every carrier-indexed Lean name
    for word in sorted(math_reading.MATH_OPERATORS):
        for lean_name in math_reading.MATH_OPERATORS[word]["lean"].values():
            for alias in _LEXICON_ALIASES.get(lean_name, (lean_name,)):
                _add_alias(identifiers, symbols, alias)

    # builtin term/atom ops and connectives
    builtin_tokens = (set(math_reading._BUILTIN_TERM_OPS)
                      | set(math_reading._BUILTIN_ATOM_OPS)
                      | set(math_reading._CONNECTIVES))
    for tok in sorted(builtin_tokens):
        if tok not in _BUILTIN_ALIASES:
            raise ValueError(
                f"builtin op {tok!r} (math_reading) has no surface alias row "
                "in census._BUILTIN_ALIASES -- extend the table")
        for alias in _BUILTIN_ALIASES[tok]:
            _add_alias(identifiers, symbols, alias)

    # quantifiers (structural fragment surface)
    for alias in _QUANTIFIER_SURFACE:
        _add_alias(identifiers, symbols, alias)

    # admitted derived operators: contribute NOTHING new (R3: eliminable to
    # the kernel basis), but walk every definition and refuse a registry
    # that violates that -- the derivation must stay live against the file.
    admitted_path = pathlib.Path(admitted_path)
    if admitted_path.exists():
        registry = json.loads(admitted_path.read_text(encoding="utf-8"))
        kernel_ops = (set(math_reading.MATH_OPERATORS) | builtin_tokens
                      | set(registry))
        for word in sorted(registry):
            ops = set()
            _walk_definition_ops(
                registry[word].get("row", {}).get("definition", {}), ops)
            bad = sorted(ops - kernel_ops)
            if bad:
                raise ValueError(
                    f"admitted operator {word!r} definition mentions "
                    f"non-kernel op(s) {bad} -- R3 eliminability violated; "
                    "refusing to derive a resident set from it")
            # ops that ARE lexicon words already contributed their Lean
            # names above; builtins likewise.  Nothing to add.

    symbols |= _STRUCTURAL_SYMBOLS
    return ResidentSet(identifiers=frozenset(identifiers),
                       symbols=frozenset(symbols))


# ===========================================================================
# The extensible missing-constant pattern table.
#
# Each entry: (canonical constant, miss_kind, regex over statement_pp).
# miss_kind follows the repo's miss_kind_guess naming (specs/mathsources/
# manifest.json: "operator:prime", "carrier:Real", "kind:set-object", ...)
# extended with class:* (typeclass demand) and connective:* (logic surface).
# A row matching an entry is BLOCKED BY that constant.  Patterns speak both
# the full-name spelling (pp.fullNames true) and the notation spelling
# (pp.notation true) of each constant.  Extending the table is the intended
# growth path for unclassified rows; entries are matched independently
# against the RAW text (order-insensitive detection), so adding an entry
# can only move rows from "unclassified"/"residue" into named bins.
# ===========================================================================
MISS_PATTERNS = (
    ("Prime", "operator:prime", r"\bPrime\b|\bIrreducible\b"),
    ("Real", "carrier:Real", r"ℝ|\bReal\b"),
    ("Rat", "carrier:Rat", r"ℚ|\bRat\b"),
    ("Complex", "carrier:Complex", r"ℂ|\bComplex\b"),
    ("Fin", "carrier:Fin", r"\bFin\b"),
    ("Bool", "carrier:Bool", r"\bBool\b"),
    ("Finset", "kind:finset", r"\bFinset\b|∑|∏"),
    ("Set", "kind:set-object", r"\bSet\b|∈|∉|⊆|⊂|∪|∩|∅|⋃|⋂"),
    ("List", "kind:list", r"\bList\b|\+\+"),
    ("Multiset", "kind:multiset", r"\bMultiset\b"),
    ("Polynomial", "operator:polynomial", r"\bPolynomial\b|\bMvPolynomial\b"),
    ("Monoid", "class:monoid", r"\b\w*Monoid\b"),
    ("Group", "class:group", r"\b\w*Group\b"),
    ("Ring", "class:ring", r"\b\w*Ring\b"),
    ("Field", "class:field", r"\b\w*Field\b"),
    ("Module", "class:module", r"\bModule\b|\bAlgebra\b|•"),
    ("Order", "class:order", r"\b\w*Order\b|\bLattice\b|⊓|⊔|\bMonotone\b|"
                             r"\bStrictMono\b"),
    ("Decidable", "class:decidable", r"\bDecidable\w*"),
    ("Type", "kind:universe-polymorphism", r"\bType\b|\bSort\b|\bProp\b"),
    ("Iff", "connective:iff", r"↔|\bIff\b"),
    ("Not", "connective:not", r"¬|\bNot\b|\bFalse\b"),
    ("Div", "operator:div", r"(?<!/)/(?!/)"),
    ("Inv", "operator:inv", r"⁻¹|\bInv\b"),
    ("Abs", "operator:abs", r"\|"),
    ("Norm", "kind:norm", r"‖"),
    ("MinMax", "operator:min-max", r"\bmin\b|\bmax\b"),
    ("ModEq", "operator:modeq", r"≡|\bNat\.ModEq\b|\bInt\.ModEq\b"),
    ("Coe", "kind:coercion", r"↑|\bNat\.cast\b|\bInt\.ofNat\b|\bInt\.toNat\b|"
                             r"\bInt\.natAbs\b"),
    ("Function", "kind:higher-order", r"↦|∘|\bfun\b|\bFunction\.\w+"),
    ("Prod", "kind:product-type", r"\bProd\b|×|\bSigma\b|\bSubtype\b"),
)

_COMPILED_PATTERNS = tuple(
    (const, kind, re.compile(rx)) for const, kind, rx in MISS_PATTERNS)

# canonical constant -> miss_kind (exported for readouts / WP-LI4 binning)
MISS_KIND = {const: kind for const, kind, _ in MISS_PATTERNS}

# Capitalized (possibly dotted) identifier tokens -- Lean constants of
# interest all start with an uppercase root (Nat.gcd, Finset, Prime).
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z0-9_']+)*")


def classify_row(statement_pp, resident=None):
    """Classify ONE statement_pp.  Pure and deterministic.

    Returns {"in_fragment": bool, "missing": [constants...], "residue":
    [tokens/chars...], "single_blocker": str|None, "unclassified": bool}.

      in_fragment    -- no missing constants AND no residue;
      single_blocker -- the one missing constant, iff len(missing) == 1 and
                        residue is empty (adding it makes the row
                        in-fragment); None otherwise;
      unclassified   -- NO pattern matched but the row is still out of
                        fragment (pure residue): the table needs a new entry.
    A row with matched patterns AND residue is neither single-blocker nor
    unclassified: it counts in blocked_by for each matched constant but
    never in unlock_counts (the residue proves one addition cannot free it).
    An empty/blank statement_pp is unclassified by fiat (nothing to read)."""
    if resident is None:
        resident = derive_resident_set()
    s = statement_pp or ""
    if not s.strip():
        return {"in_fragment": False, "missing": [], "residue": [],
                "single_blocker": None, "unclassified": True}

    matched = [(const, rx) for const, _kind, rx in _COMPILED_PATTERNS
               if rx.search(s)]
    missing = sorted({const for const, _rx in matched})

    # delete every matched span, then scan what remains
    s2 = s
    for _const, rx in matched:
        s2 = rx.sub(" ", s2)
    residue = set()
    for m in _TOKEN_RE.finditer(s2):
        tok = m.group(0)
        if tok[0].isupper() and tok[0].isascii() \
                and tok not in resident.identifiers:
            residue.add(tok)
    for ch in s2:
        if ord(ch) > 0x7F and ch not in resident.symbols:
            residue.add(ch)
    residue = sorted(residue)

    in_fragment = not missing and not residue
    single = missing[0] if (len(missing) == 1 and not residue) else None
    unclassified = (not in_fragment) and not missing
    return {"in_fragment": in_fragment, "missing": missing,
            "residue": residue, "single_blocker": single,
            "unclassified": unclassified}


# ============================================================== census =====
def load_queue(path):
    """Read a WP-LI0 queue (JSONL, one row per declaration)."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_census(queue_rows, resident=None):
    """The census dict (plan WP-LI0) -- a pure function of the queue rows
    and the derived resident set.  See the module docstring for the
    unlock_counts (single-blocker) vs blocked_by (total-mention) semantics."""
    if resident is None:
        resident = derive_resident_set()
    total = 0
    n_in = n_single = n_multi = n_unclassified = 0
    unlock, blocked, pairs = {}, {}, {}
    for row in queue_rows:
        total += 1
        c = classify_row(row.get("statement_pp", ""), resident)
        if c["in_fragment"]:
            n_in += 1
            continue
        for const in c["missing"]:
            blocked[const] = blocked.get(const, 0) + 1
        if c["single_blocker"] is not None:
            n_single += 1
            b = c["single_blocker"]
            unlock[b] = unlock.get(b, 0) + 1
        elif c["unclassified"]:
            n_unclassified += 1
        else:
            n_multi += 1
        ms = c["missing"]
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                key = ms[i] + "+" + ms[j]      # ms is sorted, so canonical
                pairs[key] = pairs.get(key, 0) + 1
    co = sorted(pairs.items(), key=lambda kv: (-kv[1], kv[0]))
    co = [[k, v] for k, v in co[:CO_OCCURRENCE_TOP]]
    return {
        "pin": common.MATHLIB_COMMIT,
        "total": total,
        "in_fragment": n_in,
        "single_blocker_rows": n_single,
        "multi_blocker_rows": n_multi,
        "unclassified": n_unclassified,
        "unlock_counts": {k: unlock[k] for k in sorted(unlock)},
        "blocked_by": {k: blocked[k] for k in sorted(blocked)},
        "miss_kinds": {k: MISS_KIND[k] for k in sorted(blocked)},
        "co_occurrence": co,
        "semantics": {
            "unlock_counts": "rows for which the key is the ONLY missing "
                             "constant (single-blocker: adding it makes the "
                             "row in-fragment); never over-counts",
            "blocked_by": "TOTAL rows whose missing set contains the key, "
                          "however many other blockers remain; demand "
                          "pressure, NOT an unlock count",
            "unclassified": "rows out of fragment with NO pattern match "
                            "(pure residue) -- extend census.MISS_PATTERNS",
        },
    }


def render_census_bytes(census) -> bytes:
    """Byte-stable serialization (the P-LI0-CENSUS tooth's subject): sorted
    keys, fixed 2-space indent, ensure_ascii, single trailing LF."""
    return (json.dumps(census, sort_keys=True, indent=2, ensure_ascii=True)
            + "\n").encode("utf-8")


def write_census(census, out_path=CENSUS_PATH):
    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(render_census_bytes(census))
    return out_path


# ======================================================= frontier order ====
def frontier_order(queue_rows, census, resident=None):
    """P-LI0-ORDER (v2, census-derived): the deterministic frontier.

    A PURE function of (queue_rows, census): returns the rows reordered
      1. in-fragment rows, by (module, decl_name);
      2. single-blocker rows, grouped by blocker with groups in DESCENDING
         census unlock_count (ties by blocker name ascending), rows within
         a group by (module, decl_name);
      3. everything else (multi-blocker + unclassified), by
         (module, decl_name).
    Permutation-invariant: every sort key is a total order ending in the
    unique decl_name, so any two runs over any input permutation agree."""
    if resident is None:
        resident = derive_resident_set()
    unlock = census.get("unlock_counts", {})
    in_frag, single, rest = [], [], []
    for row in queue_rows:
        cls = classify_row(row.get("statement_pp", ""), resident)
        tail = (row.get("module", ""), row.get("decl_name", ""))
        if cls["in_fragment"]:
            in_frag.append((tail, row))
        elif cls["single_blocker"] is not None:
            b = cls["single_blocker"]
            single.append(((-unlock.get(b, 0), b) + tail, row))
        else:
            rest.append((tail, row))
    in_frag.sort(key=lambda t: t[0])
    single.sort(key=lambda t: t[0])
    rest.sort(key=lambda t: t[0])
    return ([r for _k, r in in_frag] + [r for _k, r in single]
            + [r for _k, r in rest])


# ================================================================== CLI ====
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="WP-LI0: deterministic fragment-fit census over the "
                    "declaration queue.")
    ap.add_argument("--queue", default=str(QUEUE_PATH),
                    help="queue.jsonl path (default: %(default)s)")
    ap.add_argument("--out", default=str(CENSUS_PATH),
                    help="census.json path (default: %(default)s)")
    args = ap.parse_args(argv)
    queue_path = pathlib.Path(args.queue)
    if not queue_path.exists():
        sys.stderr.write(
            f"REFUSED: queue not found at {queue_path} -- run "
            "python3 tools/enumerate_mathlib.py first (Lean lane).\n")
        return 2
    rows = load_queue(queue_path)
    census = build_census(rows)
    out = write_census(census, args.out)
    print(f"[census] {census['total']} rows @ pin {census['pin'][:12]}: "
          f"{census['in_fragment']} in-fragment, "
          f"{census['single_blocker_rows']} single-blocker, "
          f"{census['multi_blocker_rows']} multi-blocker, "
          f"{census['unclassified']} unclassified -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

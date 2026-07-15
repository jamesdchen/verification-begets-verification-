"""F0.4 -- the lexical escape gate for Lean text.

DEFENSE-IN-DEPTH and cheap-fast-reject, **NEVER the trust boundary** (⚠T7).
Lean elaboration is metaprogramming-complete: a tactic block can run arbitrary
code at elaboration time, so a lexical gate over that surface is bypassable by
construction (qualified `Lean.Elab` names, `run_cmd`, homoglyphs,
`maxHeartbeats 0`).  The trust boundary is the OS sandbox (network off via
`unshare --net`, tmpfs, rlimits) plus the two-run adjudication rule L5.  This
gate exists to reject the obvious escapes early and to make forgery *loud*; it
is applied to every LLM-authored proof script AND (defense in depth) to the
deterministic compiler's own output (F1.2).

Its source hash --- `common.validate_lean_hash()` --- is part of cache
identity (L2): a changed gate is a clean cache miss, never a stale false-green.

`validate_lean(text) -> (ok: bool, reason: str)`.  `ok` True iff the text
survives every check below; `reason` names the first refusal.
"""
from __future__ import annotations

import re
import unicodedata

import common

# ---------------------------------------------------------------------------
# Blocklisted keyword tokens (⚠D of F0.4).  Matched as whole `_`-delimited
# tokens after NFKC normalization.  The `_rules` variants are listed
# explicitly because `\b`-style boundaries treat `_` as a word char, so a bare
# `macro` would NOT catch `macro_rules` (its own token) -- and the L5 teeth
# require `macro_rules` refused.
_BLOCKED_KEYWORDS = (
    "native_decide", "unsafe", "axiom",
    "macro", "macro_rules", "elab", "elab_rules",
    "initialize", "run_cmd", "deriving", "notation", "syntax", "attribute",
)

# `#`-commands (metaprogramming / info surface) that must never appear.
_BLOCKED_COMMANDS = ("eval", "check", "print")

# Only these two `set_option`s are whitelisted, each with a lexically-enforced
# numeric cap (⚠D12).  Everything else is refused.
_MAXHEARTBEATS = "maxHeartbeats"
_MAXRECDEPTH = "maxRecDepth"


def _kw_present(norm: str, kw: str) -> bool:
    # whole-token match: not flanked by an identifier char on either side.
    return re.search(r"(?<![\w])" + re.escape(kw) + r"(?![\w])", norm) is not None


def validate_lean(text: str):
    """Return (ok, reason).  Cheap-fast-reject; the sandbox+L5 are the boundary."""
    if not isinstance(text, str):
        return False, "non-string input"

    # (T7) Lean raw-identifier guillemets let a keyword hide inside a name --
    # `«macro_rules»` etc.  Refuse the syntax outright.
    if "«" in text or "»" in text:
        return False, "guillemet raw identifier («…») is refused (T7)"

    # (T7) non-ASCII IDENTIFIER characters (homoglyph bypass).  Math OPERATORS
    # (∀ ∃ ∧ ∨ → ≤ ≠ ∣ …) are symbols, not `\w`, so they survive; any non-ASCII
    # *word* character is a non-ASCII identifier and is refused.  Checked on the
    # raw text so a compatibility char that NFKC-folds to ASCII cannot slip an
    # identifier past.
    for ch in re.findall(r"\w", text, re.UNICODE):
        if ord(ch) > 0x7F:
            return False, ("non-ASCII identifier character "
                           f"U+{ord(ch):04X} refused (homoglyph bypass, T7)")

    # NFKC-normalize BEFORE keyword matching (a fullwidth `ｍacro` folds to
    # `macro` and must be caught).
    norm = unicodedata.normalize("NFKC", text)

    # (`@[extern]` and every other attribute) attributes are metaprogramming
    # surface; refuse any `@[…]`.
    if "@[" in norm:
        return False, "attribute syntax @[…] is refused (@[extern] and all)"

    # `#eval` / `#check` / `#print` (and, defensively, any `#`-command).
    for cmd in _BLOCKED_COMMANDS:
        if re.search(r"#\s*" + cmd + r"(?![\w])", norm):
            return False, f"#{cmd} command is refused"

    # blocklisted keyword tokens.
    for kw in _BLOCKED_KEYWORDS:
        if _kw_present(norm, kw):
            return False, f"blocklisted token {kw!r} present"

    # imports outside the pinned narrow set (⚠D15).
    for module in re.findall(r"(?m)^\s*import\s+(\S+)", norm):
        if module not in common.MATHLIB_IMPORTS:
            return False, (f"import {module!r} is outside the pinned "
                           "common.MATHLIB_IMPORTS set")

    # whitelisted set_option with numeric caps (⚠D12).  Any other option, or a
    # non-integer / out-of-range value, refuses.  `maxHeartbeats 0` = unlimited
    # => REFUSE.
    for opt, val in re.findall(r"set_option\s+(\S+)\s+(\S+)", norm):
        if opt not in (_MAXHEARTBEATS, _MAXRECDEPTH):
            return False, f"non-whitelisted set_option {opt!r}"
        m = re.match(r"-?\d+$", val)
        if not m:
            return False, f"set_option {opt} value {val!r} is not an integer"
        n = int(val)
        if opt == _MAXHEARTBEATS:
            if not (0 < n <= common.LEAN_MAXHEARTBEATS):
                return False, (f"set_option maxHeartbeats {n} out of range "
                               f"(need 0 < N <= {common.LEAN_MAXHEARTBEATS}; "
                               "0 = unlimited is refused)")
        else:  # maxRecDepth
            if not (0 < n <= common.LEAN_MAXRECDEPTH):
                return False, (f"set_option maxRecDepth {n} out of range "
                               f"(need 0 < N <= {common.LEAN_MAXRECDEPTH})")

    return True, "ok"

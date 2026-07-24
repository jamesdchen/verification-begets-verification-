#!/bin/bash
# SessionStart hook (Claude Code on the web): install the pinned Python
# closure so the pytest suite runs from the session's first minute -- the
# C2-cycle lesson (pytest arrived uv-isolated; yaml/matplotlib were missing
# until mid-session pip archaeology).  Single source of pins: setup.sh.
set -euo pipefail

# Web sessions only; local environments manage their own toolchain.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Commit-signing guard (the C3 cycle-02 stranding): web containers ship
# commit.gpgsign=true pointing at an SSH key file that is sometimes EMPTY,
# which hard-fails commit rewrites (`git commit --amend`) and can strand a
# whole cycle's work unpushed in a dead container.  The repo does not
# require signatures (unsigned pushes are accepted); an unsigned commit
# always beats a stranded one.
SIGNKEY="$(git config --global user.signingkey || true)"
if [ "$(git config --global commit.gpgsign || true)" = "true" ] \
   && { [ -z "$SIGNKEY" ] || [ ! -s "$SIGNKEY" ]; }; then
  git config --global commit.gpgsign false
  echo ">> commit signing disabled: signing key '${SIGNKEY:-unset}' missing or empty"
fi

# Push-capability probe (cycle-02 lesson #2: the stranding surfaced only
# AFTER the work was committed).  Fail LOUD at session start instead: a
# dry-run push contacts the remote and exercises auth without writing.
if ! git push --dry-run origin HEAD >/dev/null 2>&1; then
  echo ">> WARNING: 'git push --dry-run origin HEAD' FAILED -- pushes from"
  echo "   this container may not work.  Diagnose BEFORE doing cycle work"
  echo "   (git remote -v; git config -l | grep -i 'credential\\|url').  If"
  echo "   push stays broken, ship via the salvage protocol (C3_PROMPTS.md):"
  echo "   git bundle + format-patch, delivered through the session summary."
fi

# Fast path: skip the ~40s pip stage only when EVERY pin in setup.sh is
# installed at its EXACT version (mere importability is not enough: the
# environment cache can serve a snapshot up to ~7 days old, and an
# import-based check would let a pin bump drift silently).  setup.sh
# stays the single source of pins; any mismatch falls through to it.
if python3 - setup.sh <<'PY' 2>/dev/null
import re, sys
from importlib import metadata
from packaging.version import Version  # matplotlib dep; present with the closure
pins = re.findall(r'"([A-Za-z0-9_.\-]+)==([0-9][^"]*)"', open(sys.argv[1]).read())
assert pins, "no pins parsed from setup.sh"
for name, ver in pins:
    if Version(metadata.version(name)) != Version(ver):  # PEP 440: 1.14 == 1.14.0
        raise SystemExit(f"pin drift: {name} {metadata.version(name)} != {ver}")
PY
then
  echo ">> pinned Python closure present at exact versions -- skipping setup.sh --python-only"
else
  bash setup.sh --python-only
fi

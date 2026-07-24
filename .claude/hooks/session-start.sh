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

bash setup.sh --python-only

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
bash setup.sh --python-only

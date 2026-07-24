#!/bin/bash
# Stop-gate (Claude Code hook): a C3 cadence session may not stop before the
# chain is re-armed.  The re-arm itself cannot live in a hook -- creating a
# trigger needs the authenticated meta-MCP channel only the model holds --
# so this hook enforces the DONE-CONDITION instead: it blocks the first stop
# of a driver/watchdog session until the session attests (marker file) that
# it re-armed the chain or verified a pending C3 one-shot.  The block reason
# re-instructs the model, so a forgotten re-arm self-corrects in one round.
set -uo pipefail

INPUT="$(cat)"
MARKER="/tmp/c3_rearm.done"

field() {
  python3 -c 'import json,sys; d=json.loads(sys.argv[1]); v=d.get(sys.argv[2],""); print(v if not isinstance(v,bool) else ("true" if v else "false"))' \
    "$INPUT" "$1" 2>/dev/null
}

# One reinforcement round only: if we already blocked once, let the stop
# through (a hard wedge would burn the container forever).
[ "$(field stop_hook_active)" = "true" ] && exit 0

# Attested: the session re-armed (or verified the chain alive).
[ -f "$MARKER" ] && exit 0

# Gate only C3 cadence sessions: their firing prompt is the transcript's
# opening user message.  Interactive sessions pass through untouched.
TRANSCRIPT="$(field transcript_path)"
[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] || exit 0
head -c 300000 "$TRANSCRIPT" | grep -q "C3 DRIVER CYCLE\|C3 WATCHDOG" || exit 0

cat <<'JSON'
{"decision": "block", "reason": "C3 stop-gate: the chain is not attested as re-armed. Before stopping you MUST either (a) create exactly ONE one-shot fresh-session trigger named 'C3 driver cycle' per PLAN_FRAGMENT S3.1 rule 5, using the DRIVER prompt text from C3_PROMPTS.md in your checkout (+75 min after Lean-tagged work, +15 min with Lean-free work queued, +6 h if idle/blocked), or (b) verify via list_triggers that a pending C3 one-shot already exists in the future. Then run: touch /tmp/c3_rearm.done  -- and stop again."}
JSON
exit 0

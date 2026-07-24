#!/bin/bash
# Stop-gate (Claude Code hook): a C3 cadence session may not stop before its
# cycle is CONCLUDED.  Under the recurring-Routine model (C3_PROMPTS.md
# "Architecture") the next firing rides the Routine's own schedule, so the
# done-condition is no longer "re-armed a trigger" but: the cycle's work is
# pushed (or salvaged into the summary per the PUSH-FAILURE SALVAGE
# protocol), or the summary states an explicit no-op reason.  The session
# attests with a marker file; the block reason re-instructs the model, so a
# forgotten conclusion self-corrects in one round.
set -uo pipefail

INPUT="$(cat)"
MARKER="/tmp/c3_cycle.done"
LEGACY_MARKER="/tmp/c3_rearm.done"   # pre-rewiring sessions still in flight

field() {
  python3 -c 'import json,sys; d=json.loads(sys.argv[1]); v=d.get(sys.argv[2],""); print(v if not isinstance(v,bool) else ("true" if v else "false"))' \
    "$INPUT" "$1" 2>/dev/null
}

# One reinforcement round only: if we already blocked once, let the stop
# through (a hard wedge would burn the container forever).
[ "$(field stop_hook_active)" = "true" ] && exit 0

# Attested: the session concluded its cycle (either marker generation).
[ -f "$MARKER" ] || [ -f "$LEGACY_MARKER" ] && exit 0

# Gate only C3 cadence sessions: their firing prompt is the transcript's
# opening user message.  Interactive sessions pass through untouched.
TRANSCRIPT="$(field transcript_path)"
[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] || exit 0
head -c 300000 "$TRANSCRIPT" | grep -q "C3 DRIVER CYCLE\|C3 PURCHASE CYCLE\|C3 WATCHDOG" || exit 0

cat <<'JSON'
{"decision": "block", "reason": "C3 stop-gate: this cycle is not attested as concluded. Before stopping you MUST make sure that (a) the cycle's work is pushed to your claude/c3-* or claude/p-* branch, OR (b) push failed and the work is salvaged into your summary (git bundle + format-patch with the exact sha, per C3_PROMPTS.md PUSH-FAILURE SALVAGE), OR (c) your summary states the explicit no-op reason (freshness guard, blocked, nothing queued). Do NOT create triggers or one-shots -- the next firing rides the Routine's own schedule. Then run: touch /tmp/c3_cycle.done  -- and stop again."}
JSON
exit 0

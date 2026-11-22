#!/bin/sh
input=$(tr -d '\n\r')
case "${KS_REVIEW:-}" in
  0) exit 0 ;;
  1) ;;
  *) [ "${CLAUDE_CODE_SESSION_ATTENDED:-}" = 1 ] || exit 0 ;;
esac
head=$(git rev-parse --verify --quiet HEAD) || exit 0
marker=$(git rev-parse --git-path kagestack-reviewed) || exit 0
asked=$(git rev-parse --git-path kagestack-review-asked) || exit 0
reviewed=$(cat "$marker" 2>/dev/null)
descends() { git merge-base --is-ancestor "$1" "$2" 2>/dev/null; }

if [ -f "$asked" ] && printf '%s' "$input" | grep -q '"stop_hook_active" *: *true'; then
  rm -f "$asked"
  if [ -n "$reviewed" ] && descends "$reviewed" "$head"; then
    echo "$head" > "$marker"
  fi
  exit 0
fi
printf '%s' "$input" | grep -q '"background_tasks" *: *\[ *[^] ]' && exit 0

for ref in origin/HEAD origin/main origin/master main master; do
  if git rev-parse --verify --quiet "$ref^{commit}" > /dev/null; then
    base=$(git merge-base "$ref" "$head")
    break
  fi
done
[ -n "${base:-}" ] || exit 0
from=$base
if [ -n "$reviewed" ] && descends "$base" "$reviewed" && descends "$reviewed" "$head"; then
  from=$reviewed
fi
[ "$from" = "$head" ] && exit 0
echo "$head" > "$marker"
: > "$asked"

brief=$(printf '%s' "$CLAUDE_PLUGIN_ROOT/hooks/review.md" | sed 's/\\/\\\\/g; s/"/\\"/g')
range=$(printf '%.12s..%.12s' "$from" "$head")
printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' \
  "Commits $range are not reviewed yet. Before you finish, start one fresh subagent to review them, in the foreground, and wait for its report. Tell it to read $brief first, and give it the user's request and the range $range. Fix each finding it confirms with a test, give a reason for each one you dismiss, then finish your reply. KS_REVIEW=0 turns this off."

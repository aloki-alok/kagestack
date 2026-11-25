import json
import os
import re
import sys

WAITS = re.compile(
    r'\b(for|while|until)\b.*?\bdo\b.*?\bsleep\b.*?\bdone\b'
    r'|\bgh\s+run\s+watch\b'
    r'|\bgh\s+pr\s+checks\b.*--watch\b',
    re.DOTALL,
)

BACKGROUND = (
    'This command waits in the foreground and blocks the session. Run it again '
    'with run_in_background: true and keep working until the notification '
    'arrives. For a GitHub Actions run, background `gh run watch <run-id> '
    '--exit-status`. To wait for any other condition, use the Monitor tool '
    'with an until-loop.'
)


def main():
    if os.environ.get('KS_WAIT') == '0':
        return
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    command = event.get('tool_input') or {}
    if command.get('run_in_background') or not WAITS.search(
        command.get('command') or ''
    ):
        return
    decision = {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': BACKGROUND,
    }
    print(json.dumps({'hookSpecificOutput': decision}))


main()

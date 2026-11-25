import json
import os
import re
import sys

SLEEP_LOOP = re.compile(
    r'\b(for|while|until)\b.*?\bdo\b.*?\bsleep\b.*?\bdone\b', re.DOTALL
)

WATCH = re.compile(
    r'(^|[;&|(\n])\s*((sudo|time|timeout\s+\S+|\w+=\S*)\s+)*'
    r'(gh\s+run\s+watch\b|gh\s+pr\s+checks\b[^;&|\n]*--watch\b|watch\s)'
)

HEREDOC_BODY = re.compile(r'<<-?\s*([\'"]?)(\w+)\1.*?\n.*?\n\s*\2\b', re.DOTALL)

QUOTED = re.compile(r'"[^"]*"|\'[^\']*\'')


def waits(command):
    unquoted = QUOTED.sub('', HEREDOC_BODY.sub('', command))
    return bool(SLEEP_LOOP.search(command) or WATCH.search(unquoted))


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
    if command.get('run_in_background') or not waits(command.get('command') or ''):
        return
    decision = {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': BACKGROUND,
    }
    print(json.dumps({'hookSpecificOutput': decision}))


main()

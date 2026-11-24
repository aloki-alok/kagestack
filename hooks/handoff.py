import json
import os
import sys

MARKER = b'"compact_boundary"'

HANDOFF = (
    'This session has been compacted {count} times, so the detail of its early '
    'turns, and decisions made there, survive only as summaries. Finish the step '
    'you are on, then run `kagestack:handoff`, and tell the user to continue in a '
    'fresh session from the handoff. KS_HANDOFF_AFTER sets the count, and 0 turns '
    'this off.'
)


def compactions(path):
    count = 0
    with open(path, 'rb') as transcript:
        for line in transcript:
            if MARKER not in line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get('type') == 'system' and entry.get('subtype') == 'compact_boundary':
                count += 1
    return count


def main():
    after = int(os.environ.get('KS_HANDOFF_AFTER') or 3)
    if after <= 0 or os.environ.get('CLAUDE_CODE_SESSION_ATTENDED') != '1':
        return
    try:
        event = json.load(sys.stdin)
        if event.get('source') != 'compact':
            return
        count = compactions(event['transcript_path'])
    except (ValueError, KeyError, OSError):
        return
    if count >= after:
        context = HANDOFF.format(count=count)
        print(json.dumps({
            'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': context},
        }))


main()

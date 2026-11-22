import json
import os
import re
import sys

OFFER = re.compile(
    r'\b(want me to|should i|shall i|would you like|do you want|'
    r'let me know (whether|which)|say (yes|go|the word)|pick one|'
    r'which (one|option) (do )?you)\b',
    re.IGNORECASE,
)

DECIDE = (
    'Your reply ends with a question. Keep it only for a deploy, a production '
    "write, money, a migration, a delete you can't undo, a message to people, "
    'or if the user asked you to check first. Otherwise do what you would '
    'recommend, or drop the question, and list your calls under **Decided**.'
)


def asks(message):
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', message) if p.strip()]
    if not paragraphs:
        return False
    unquoted = re.sub(r'"[^"]*"|“[^”]*”|`[^`]*`', '', paragraphs[-1])
    last = re.split(r'(?<=[.!?])\s+', unquoted.strip())[-1].rstrip('*_ )')
    return last.endswith('?') or bool(OFFER.search(last))


def main():
    if os.environ.get('KS_DECIDE') == '0':
        return
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    if event.get('stop_hook_active'):
        return
    if asks(event.get('last_assistant_message') or ''):
        print(json.dumps({'decision': 'block', 'reason': DECIDE}))


main()

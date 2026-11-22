import json
import os
import re
import sys

OFFER = re.compile(
    r'\b(want me to|should i|shall i|would you like|do you want|'
    r'let me know (if|whether|which)|say (yes|go|the word)|pick one|'
    r'which (one|option) (do )?you)\b',
    re.IGNORECASE,
)

DECIDE = (
    'Your reply ends by asking the user to choose or approve. '
    'Keep the question only if the answer leads to a deploy, a write to production '
    'data, money, a schema or data migration, deleting something that cannot be '
    'restored, an auth or permission change, a message to people outside this '
    'session, or a product choice only the user can make. Then end the turn again '
    'with the question in one line. '
    'Otherwise take the option you would recommend and do it now. '
    'End the reply with a **Decided** list, one line per call you made for the user: '
    'what you chose, why, and the cost if it is wrong. '
    'Mark a line "(taste)" when the user might reasonably have chosen differently. '
    'KS_DECIDE=0 turns this off.'
)


def asks(message):
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', message) if p.strip()]
    if not paragraphs:
        return False
    last = paragraphs[-1].rstrip('*_` )')
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

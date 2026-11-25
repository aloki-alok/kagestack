import json
import os
import re
import sys

SLEEP_LOOP_WORDS = [
    re.compile(rf'\b{word}\b') for word in ('(for|while|until)', 'do', 'sleep', 'done')
]

COMMAND_BREAK = re.compile(r'[;&|(){}`\n]|\b(?:then|do|else)\b')

WATCH_COMMAND = re.compile(
    r'[ \t]*((sudo|time|env|exec|command|nice|timeout[ \t]+\S+|\w+=\S*)[ \t]+)*'
    r'(watch[ \t]|gh[ \t]+((-R|--repo)[ \t=]+\S+[ \t]+)?'
    r'(run[ \t]+watch\b|pr[ \t]+checks\b.*[ \t](--watch|-w)\b))'
)

SHELL_STRING = re.compile(
    r'\b(?:ba|z|da)?sh[ \t]+-[a-z]*c[ \t]+(?:\'([^\']*)\'|"((?:[^"\\]|\\.)*)")'
)

HEREDOC_START = re.compile(r'<<-?[ \t]*([\'"]?)([A-Za-z_]\w*)\1')

COMMENT_MAY_START_AFTER = ' \t\n;&|('


def sleeps_in_a_loop(command):
    position = 0
    for word in SLEEP_LOOP_WORDS:
        found = word.search(command, position)
        if not found:
            return False
        position = found.end()
    return True


def without_heredoc_bodies(command):
    kept, closing = [], None
    for line in command.split('\n'):
        if closing:
            closing = None if line.strip() == closing else closing
            continue
        kept.append(line)
        opened = HEREDOC_START.search(line.replace('<<<', ' '))
        closing = opened.group(2) if opened else None
    return '\n'.join(kept)


def code_only(command):
    kept, open_quote, escaped = [], None, False
    for char in command:
        if escaped:
            escaped = False
        elif open_quote == '#':
            if char == '\n':
                open_quote = None
                kept.append(char)
        elif open_quote:
            escaped = char == '\\' and open_quote == '"'
            open_quote = None if char == open_quote else open_quote
        elif char == '\\':
            escaped = True
        elif char in '\'"' or (
            char == '#' and (not kept or kept[-1] in COMMENT_MAY_START_AFTER)
        ):
            open_quote = char
            kept.append(' ')
        else:
            kept.append(char)
    return ''.join(kept)


def waits(command):
    script = without_heredoc_bodies(command)
    code = code_only(script)
    commands = COMMAND_BREAK.split(code)
    if sleeps_in_a_loop(code) or any(map(WATCH_COMMAND.match, commands)):
        return True
    return any(waits(''.join(inner)) for inner in SHELL_STRING.findall(script))


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

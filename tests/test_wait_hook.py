import json
import os
import subprocess
from pathlib import Path

HOOK = Path(__file__).parent.parent / 'hooks/wait.py'

POLL_LOOP = (
    'for i in $(seq 1 24); do r=$(gh run list --limit 1); '
    'case "$r" in done*) break;; esac; sleep 15; done; echo "$r"'
)


def run(command, background=False, env=None):
    clean = {k: v for k, v in os.environ.items() if not k.startswith('KS_')}
    event = {
        'hook_event_name': 'PreToolUse',
        'tool_name': 'Bash',
        'tool_input': {'command': command, 'run_in_background': background},
    }
    return subprocess.run(
        ['python3', HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        check=True,
        env={**clean, **(env or {})},
    ).stdout


def denied(output):
    served = json.loads(output)['hookSpecificOutput']
    assert served['hookEventName'] == 'PreToolUse'
    assert served['permissionDecision'] == 'deny'
    return served['permissionDecisionReason']


def test_foreground_poll_loop_is_sent_to_the_background():
    reason = denied(run(POLL_LOOP))

    assert 'run_in_background' in reason
    assert 'gh run watch' in reason
    assert 'Monitor' in reason


def test_until_loop_waiting_on_a_server_is_sent_back():
    assert denied(run('until curl -sf localhost:3000; do sleep 2; done'))


def test_multiline_while_loop_is_sent_back():
    assert denied(run('while true\ndo\n  gh pr checks 42 && break\n  sleep 30\ndone'))


def test_foreground_gh_watch_is_sent_back():
    assert denied(run('gh run watch 123 --exit-status'))
    assert denied(run('gh pr checks 42 --watch'))


def test_watch_after_another_command_is_sent_back():
    assert denied(run('cd repo && timeout 600 gh run watch 123'))
    assert denied(run('watch -n 5 gh run list'))


def test_quoted_mention_of_a_watch_command_runs():
    assert run('git commit -m "docs: explain gh run watch"') == ''
    assert run('gh run view 1 --log | grep "gh pr checks --watch"') == ''


def test_poll_loop_in_the_background_runs():
    assert run(POLL_LOOP, background=True) == ''


def test_loop_without_sleep_runs():
    assert run('for f in *.py; do ruff check "$f"; done') == ''


def test_plain_command_mentioning_sleep_runs():
    assert run('grep -rn "sleep" src/') == ''


def test_switch_turns_the_check_off():
    assert run(POLL_LOOP, env={'KS_WAIT': '0'}) == ''

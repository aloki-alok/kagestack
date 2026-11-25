import json
import os
import subprocess
import time
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
        timeout=5,
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


def test_watch_behind_a_prefix_is_sent_back():
    assert denied(run('time gh run watch 1'))
    assert denied(run('CI=1 sudo watch ls'))


def test_quoted_mention_of_a_watch_command_runs():
    assert run('git commit -m "docs: explain gh run watch"') == ''
    assert run('git commit -m "fix; gh run watch" -m \'x; watch tests\'') == ''
    assert run('git commit -m "say \\"hi\\"; gh run watch"') == ''
    assert run("cat > notes.md <<'EOF'\nwatch -n 5 ls\nEOF") == ''


def test_quote_in_a_comment_does_not_hide_a_watch():
    assert denied(run("echo hi # it's here\ngh run watch 1\n# it's there"))


def test_escaped_quote_does_not_hide_a_watch():
    assert denied(run('echo \\"; gh run watch 1; echo \\"'))


def test_arithmetic_shift_is_not_a_heredoc():
    assert denied(run('x=$((1<<2))\ngh run watch 1\n2'))


def test_watch_inside_a_quote_that_spans_commands_runs():
    assert run("echo don't; gh run watch 1; echo 'x'") == ''


def test_long_commands_are_checked_in_well_under_a_second():
    slow_before = (
        'cat <<EOF\n' + 'line\n' * 10_000,
        'for x do ' + 'sleep 1 ' * 6_000,
        '\n' * 50_000,
        '  \n' * 15_000,
        ';a=' * 16_000,
        '&a=b' * 12_000,
    )

    started = time.monotonic()
    for command in slow_before:
        run(command)

    assert time.monotonic() - started < 1


def test_loop_words_in_quoted_text_run():
    assert run('git commit -m "while loop: do not sleep until done"') == ''
    assert run("cat > poll.sh <<'EOF'\nwhile true; do sleep 1; done\nEOF") == ''


def test_wait_inside_a_shell_string_is_sent_back():
    assert denied(run('bash -c "while true; do sleep 5; done"'))
    assert denied(run("sh -c 'gh run watch 1'"))
    assert denied(run("bash -lc 'gh run watch 1'"))


def test_watch_in_a_block_or_substitution_is_sent_back():
    assert denied(run('if true; then gh run watch 1; fi'))
    assert denied(run('for r in 1 2; do gh run watch $r; done'))
    assert denied(run('{ gh run watch 1; }'))
    assert denied(run('r=`gh run watch 1`'))
    assert denied(run('env CI=1 gh -R a/b run watch 1'))
    assert denied(run('gh pr checks 1 -w'))


def test_heredoc_ends_at_its_delimiter():
    assert denied(run('cat <<EOF\nnotes\nEOF\ngh run watch 1'))
    assert run('cat > notes.md <<EOF\nnotes\nwatch -n 1 ls\nEOF') == ''
    assert denied(run('cat <<<word\ngh run watch 1\nword'))


def test_quotes_follow_bash_rules():
    assert denied(run('echo a#b; gh run watch 1'))
    assert denied(run("echo 'a\\'; gh run watch 1"))


def test_poll_loop_in_the_background_runs():
    assert run(POLL_LOOP, background=True) == ''


def test_loop_without_sleep_runs():
    assert run('for f in *.py; do ruff check "$f"; done') == ''


def test_plain_command_mentioning_sleep_runs():
    assert run('grep -rn "sleep" src/') == ''


def test_switch_turns_the_check_off():
    assert run(POLL_LOOP, env={'KS_WAIT': '0'}) == ''

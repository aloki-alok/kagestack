import json
import os
import subprocess
from pathlib import Path

HOOK = Path(__file__).parent.parent / 'hooks/decide.py'


def stop(message, active=False, env=None):
    clean = {k: v for k, v in os.environ.items() if not k.startswith('KS_')}
    event = {
        'hook_event_name': 'Stop',
        'stop_hook_active': active,
        'last_assistant_message': message,
    }
    return subprocess.run(
        ['python3', HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        check=True,
        env={**clean, **(env or {})},
    ).stdout


def sent_back(output):
    served = json.loads(output)
    assert served['decision'] == 'block'
    return served['reason']


def test_reply_that_ends_by_asking_is_sent_back_to_decide():
    reply = 'Both fixes are small.\n\nWant me to build both on a feature branch?'

    assert 'Decided' in sent_back(stop(reply))


def test_offer_without_a_question_mark_is_sent_back():
    assert sent_back(stop('The PR is green.\n\nSay yes and I will merge it.'))


def test_trailing_blank_lines_and_markdown_do_not_hide_the_ask():
    assert sent_back(stop('Done with step 1.\n\n**Should I start step 2?**\n\n'))


def test_reply_that_ends_with_a_statement_finishes():
    assert stop('Fixed, 1,213 stuck calls now dial. The cause was the reaper.') == ''


def test_question_earlier_in_the_reply_does_not_count():
    reply = 'Should I rotate the token? It had expired.\n\nRotated it, the job passes.'

    assert stop(reply) == ''


def test_second_stop_in_a_row_finishes_so_a_real_ask_reaches_the_user():
    assert stop('Deploy to prod now?', active=True) == ''


def test_switch_turns_it_off():
    assert stop('Want me to merge it?', env={'KS_DECIDE': '0'}) == ''


def test_input_it_cannot_read_finishes():
    result = subprocess.run(
        ['python3', HOOK], input='not json', capture_output=True, text=True
    )

    assert (result.returncode, result.stdout) == (0, '')

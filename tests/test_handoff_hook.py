import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).parent.parent / 'hooks/handoff.py'
ATTENDED = {'CLAUDE_CODE_SESSION_ATTENDED': '1'}
BOUNDARY = {'type': 'system', 'subtype': 'compact_boundary', 'content': 'Conversation compacted'}
TURN = {'type': 'user', 'message': {'role': 'user', 'content': 'keep going'}}


def transcript(tmp_path, entries):
    path = tmp_path / 'session.jsonl'
    path.write_text(''.join(json.dumps(entry) + '\n' for entry in entries))
    return path


def start(path, source='compact', env=ATTENDED):
    clean = {
        k: v for k, v in os.environ.items()
        if not k.startswith('KS_') and k != 'CLAUDE_CODE_SESSION_ATTENDED'
    }
    event = {'hook_event_name': 'SessionStart', 'source': source, 'transcript_path': str(path)}
    return subprocess.run(
        ['python3', HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        check=True,
        env={**clean, **env},
    ).stdout


def told(output):
    served = json.loads(output)['hookSpecificOutput']
    assert served['hookEventName'] == 'SessionStart'
    return served['additionalContext']


def test_third_compaction_asks_for_a_handoff(tmp_path):
    path = transcript(tmp_path, [TURN, BOUNDARY, TURN, BOUNDARY, TURN, BOUNDARY])

    context = told(start(path))

    assert 'kagestack:handoff' in context
    assert '3 times' in context


def test_second_compaction_says_nothing(tmp_path):
    path = transcript(tmp_path, [TURN, BOUNDARY, TURN, BOUNDARY])

    assert start(path) == ''


def test_a_resume_says_nothing_however_often_it_was_compacted(tmp_path):
    path = transcript(tmp_path, [BOUNDARY] * 5)

    assert start(path, source='resume') == ''


def test_text_that_mentions_the_marker_is_not_a_compaction(tmp_path):
    quoted = {
        'type': 'user',
        'message': {'content': [{'type': 'tool_result', 'content': '"subtype":"compact_boundary"'}]},
    }
    path = transcript(tmp_path, [BOUNDARY, BOUNDARY, quoted, quoted])

    assert start(path) == ''


def test_the_threshold_is_a_setting(tmp_path):
    path = transcript(tmp_path, [BOUNDARY, BOUNDARY])

    assert '2 times' in told(start(path, env={**ATTENDED, 'KS_HANDOFF_AFTER': '2'}))
    assert start(transcript(tmp_path, [BOUNDARY] * 9), env={**ATTENDED, 'KS_HANDOFF_AFTER': '0'}) == ''


@pytest.mark.parametrize('setting', ['abc', '2.5', '-1', '--5', '²', ''])
def test_a_count_that_is_not_a_whole_number_falls_back_to_three(tmp_path, setting):
    path = transcript(tmp_path, [BOUNDARY] * 3)

    assert '3 times' in told(start(path, env={**ATTENDED, 'KS_HANDOFF_AFTER': setting}))


def test_unattended_sessions_are_left_alone(tmp_path):
    path = transcript(tmp_path, [BOUNDARY] * 4)

    assert start(path, env={}) == ''


def test_a_missing_transcript_says_nothing(tmp_path):
    assert start(tmp_path / 'gone.jsonl') == ''

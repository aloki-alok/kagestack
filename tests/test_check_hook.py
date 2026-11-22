import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
HOOK = ROOT / 'hooks/check.py'


def git(repo, *args):
    subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True)


def edited(path, cwd):
    event = {'hook_event_name': 'PostToolUse', 'tool_name': 'Edit'}
    event['tool_input'] = {'file_path': str(path)}
    return subprocess.run(
        ['python3', HOOK],
        input=json.dumps(event),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, 'CLAUDE_PLUGIN_ROOT': str(ROOT)},
    ).stdout


def repo_with(tmp_path, text):
    repo = tmp_path / 'repo'
    repo.mkdir()
    git(repo, 'init', '-q', '-b', 'main')
    git(
        repo,
        '-c',
        'user.name=k',
        '-c',
        'user.email=k@k',
        'commit',
        '-q',
        '--allow-empty',
        '-m',
        'base',
    )
    (repo / 'app.py').write_text(text)
    return repo


def test_edit_that_adds_a_comment_is_sent_back(tmp_path):
    repo = repo_with(tmp_path, 'x = 1  # retry three times\n')

    served = json.loads(edited(repo / 'app.py', tmp_path))

    assert served['decision'] == 'block'
    assert 'app.py:1: # retry three times' in served['reason']


def test_edit_without_comments_is_silent(tmp_path):
    repo = repo_with(tmp_path, 'retries = 3\n')

    assert edited(repo / 'app.py', tmp_path) == ''


def test_file_outside_a_repo_is_silent(tmp_path):
    loose = tmp_path / 'loose.py'
    loose.write_text('x = 1  # note\n')

    assert edited(loose, tmp_path) == ''


def test_uv_failure_is_not_a_finding(tmp_path):
    repo = repo_with(tmp_path, 'x = 1  # note\n')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    (bin_dir / 'uv').write_text('#!/bin/sh\nexit 1\n')
    (bin_dir / 'uv').chmod(0o755)
    event = {'tool_input': {'file_path': str(repo / 'app.py')}}

    result = subprocess.run(
        ['python3', HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env={
            **os.environ,
            'CLAUDE_PLUGIN_ROOT': str(ROOT),
            'PATH': f'{bin_dir}:/usr/bin:/bin',
        },
    )

    assert result.stdout == ''


def test_edit_that_skips_a_test_is_sent_back(tmp_path):
    repo = repo_with(tmp_path, '@pytest.mark.skip\ndef test_a():\n    pass\n')

    served = json.loads(edited(repo / 'app.py', tmp_path))

    assert 'app.py:1: @pytest.mark.skip' in served['reason']

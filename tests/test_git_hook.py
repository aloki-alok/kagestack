import os
import subprocess
import sys
from pathlib import Path

import pytest

KS = Path(sys.executable).parent / 'ks'


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', str(tmp_path / 'gitconfig'))
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'config'))
    monkeypatch.setenv('PATH', f'{KS.parent}{os.pathsep}{os.environ["PATH"]}')
    return tmp_path


def run(cwd, *args):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def repo(home):
    path = home / 'repo'
    path.mkdir()
    run(path, 'git', 'init', '-q', '-b', 'main')
    run(path, 'git', 'config', 'user.email', 'ks@example.com')
    run(path, 'git', 'config', 'user.name', 'ks')
    run(path, 'git', 'commit', '-q', '--allow-empty', '-m', 'base')
    return path


def commit(path, text):
    (path / 'app.py').write_text(text)
    run(path, 'git', 'add', 'app.py')
    return run(path, 'git', 'commit', '-q', '-m', 'change')


def own_hook(path, name):
    hook = path / '.git/hooks' / name
    hook.write_text(f'#!/bin/sh\ntouch "{path}/{name}-ran"\n')
    hook.chmod(0o755)


def test_commit_that_adds_a_comment_is_refused(home):
    assert run(home, KS, 'git-hook').returncode == 0
    path = repo(home)

    refused = commit(path, 'retries = 3  # three is enough\n')

    assert refused.returncode != 0
    assert 'app.py:1: # three is enough' in refused.stdout + refused.stderr
    assert commit(path, 'retries = 3\n').returncode == 0


def test_repo_hooks_still_run(home):
    run(home, KS, 'git-hook')
    path = repo(home)
    own_hook(path, 'pre-commit')
    own_hook(path, 'commit-msg')

    assert commit(path, 'retries = 3\n').returncode == 0
    assert (path / 'pre-commit-ran').exists()
    assert (path / 'commit-msg-ran').exists()


def test_other_global_hooks_folder_is_left_alone(home):
    run(home, 'git', 'config', '--global', 'core.hooksPath', '/elsewhere')

    result = run(home, KS, 'git-hook')

    assert result.returncode == 1
    hooks_path = run(home, 'git', 'config', '--global', 'core.hooksPath')
    assert hooks_path.stdout.strip() == '/elsewhere'

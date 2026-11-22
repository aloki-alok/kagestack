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


def test_read_only_git_config_gets_the_line_to_add(home, monkeypatch):
    locked = home / 'nix'
    locked.mkdir()
    (locked / 'config').write_text('')
    locked.chmod(0o555)
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', str(locked / 'config'))

    result = run(home, KS, 'git-hook')

    assert result.returncode == 1
    assert 'Traceback' not in result.stderr
    assert f'core.hooksPath = {home}/config/kagestack/git-hooks' in result.stdout


def test_rerun_with_hooks_path_already_set_skips_the_config_write(home):
    run(home, KS, 'git-hook')
    config = Path(os.environ['GIT_CONFIG_GLOBAL'])
    config.parent.chmod(0o555)

    try:
        result = run(home, KS, 'git-hook')
    finally:
        config.parent.chmod(0o755)

    assert result.returncode == 0


def test_new_repo_and_first_commit_stay_quiet(home):
    run(home, KS, 'git-hook')
    path = home / 'fresh'
    path.mkdir()

    started = run(path, 'git', 'init', '-q', '-b', 'main')
    (path / 'app.py').write_text('retries = 3\n')
    run(path, 'git', 'add', 'app.py')
    first = run(
        path,
        'git',
        '-c',
        'user.name=k',
        '-c',
        'user.email=k@k',
        'commit',
        '-qm',
        'first',
    )

    assert (started.stderr, first.returncode, first.stdout + first.stderr) == (
        '',
        0,
        '',
    )


def test_merge_commit_is_not_blocked_by_the_other_branch(home):
    run(home, KS, 'git-hook')
    path = repo(home)
    commit(path, 'f = 1\n')
    run(path, 'git', 'checkout', '-q', '-b', 'theirs')
    run(path, 'git', 'commit', '-qam', 'x', '--no-verify')
    (path / 'app.py').write_text('f = 6  # theirs\n')
    run(path, 'git', 'commit', '-qam', 'theirs', '--no-verify')
    run(path, 'git', 'checkout', '-q', 'main')
    (path / 'app.py').write_text('f = 2\n')
    run(path, 'git', 'commit', '-qam', 'ours')
    run(path, 'git', 'merge', '-q', 'theirs')
    (path / 'app.py').write_text('f = 6  # theirs\n')
    run(path, 'git', 'add', 'app.py')

    assert run(path, 'git', 'commit', '-qm', 'merge').returncode == 0


def test_push_into_a_checked_out_repo_still_updates_its_files(home):
    run(home, KS, 'git-hook')
    server = repo(home)
    commit(server, 'v = 1\n')
    run(server, 'git', 'config', 'receive.denyCurrentBranch', 'updateInstead')
    client = home / 'client'
    run(home, 'git', 'clone', '-q', str(server), str(client))
    (client / 'app.py').write_text('v = 2\n')
    run(
        client,
        'git',
        '-c',
        'user.name=k',
        '-c',
        'user.email=k@k',
        'commit',
        '-qam',
        'two',
    )

    assert run(client, 'git', 'push', '-q', 'origin', 'main').returncode == 0
    assert (server / 'app.py').read_text() == 'v = 2\n'

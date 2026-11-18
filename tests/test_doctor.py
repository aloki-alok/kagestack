import os
import subprocess
import sys
from pathlib import Path

KS = Path(sys.executable).parent / 'ks'
V0_15_0 = 'f291e92b1b8fc78a1758663a5f3b335b3a480ff5'
V0_16_0 = 'd561b19ca9495ac3c2b126796c2d03cd500ce12e'
REPO = 'https://github.com/aloki-alok/kagestack'
OFFLINE = {
    'GIT_CONFIG_COUNT': '1',
    'GIT_CONFIG_KEY_0': 'url.https://offline.invalid/.insteadOf',
    'GIT_CONFIG_VALUE_0': 'https://github.com/',
}


def doctor(repo, env=None):
    return subprocess.run(
        [KS, 'doctor'],
        check=False,
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )


def newest_release():
    refs = subprocess.run(
        ['git', 'ls-remote', '--tags', '--sort=-v:refname', REPO, 'v*^{}'],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return refs.split()[0]


def set_up(tmp_path, pin, manifest='[commands]\ntest = "pytest"\n'):
    subprocess.run(['git', 'init', '-q', '-b', 'main', tmp_path], check=True)
    (tmp_path / 'kagestack.toml').write_text(manifest)
    subprocess.run(
        [KS, 'setup', '--yes', '--pin', pin],
        check=True,
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    return tmp_path


def test_repo_on_the_newest_release_is_healthy(tmp_path):
    repo = set_up(tmp_path, newest_release(), manifest='[commands]\ntest = "none"\n')

    result = doctor(repo)

    assert result.returncode == 0, result.stdout
    assert [line.split()[0] for line in result.stdout.splitlines()] == ['ok', 'ok']


def test_older_release_warns_but_passes(tmp_path):
    repo = set_up(tmp_path, V0_15_0)

    result = doctor(repo)

    assert result.returncode == 0
    assert result.stdout.splitlines()[1].startswith('warn')
    assert 'pinned to v0.15.0' in result.stdout


def test_pin_that_is_no_release_fails(tmp_path):
    repo = set_up(tmp_path, 'b' * 40)

    result = doctor(repo)

    assert result.returncode == 1
    assert 'not a release' in result.stdout


def test_empty_test_command_fails(tmp_path):
    repo = set_up(tmp_path, V0_16_0, manifest='[commands]\ntest = []\n')

    result = doctor(repo)

    assert result.returncode == 1
    assert 'test = "none"' in result.stdout


def test_missing_setup_fails_and_says_what_to_run(tmp_path):
    subprocess.run(['git', 'init', '-q', '-b', 'main', tmp_path], check=True)

    result = doctor(tmp_path)

    assert result.returncode == 1
    assert 'ks setup' in result.stdout


def test_workflow_setup_did_not_write_is_skipped(tmp_path):
    repo = set_up(tmp_path, V0_16_0)
    (repo / '.github/workflows/ks.yml').write_text('name: mine\n')

    result = doctor(repo)

    assert result.returncode == 0
    assert 'not written by ks setup' in result.stdout


def test_no_network_still_reports_the_manifest(tmp_path):
    repo = set_up(tmp_path, V0_16_0)

    result = doctor(repo, env=OFFLINE)

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith('ok')
    assert 'cannot reach' in result.stdout


def test_empty_workflow_is_reported_as_empty(tmp_path):
    repo = set_up(tmp_path, V0_16_0)
    (repo / '.github/workflows/ks.yml').write_text('')

    result = doctor(repo)

    assert result.returncode == 1
    assert 'is empty' in result.stdout


def test_stale_packaged_skills_warn(tmp_path):
    repo = set_up(tmp_path, V0_16_0)
    subprocess.run([KS, 'package'], check=True, cwd=repo, capture_output=True)
    (repo / '.agents/skills/kagestack-pr/SKILL.md').write_text('old\n')

    result = doctor(repo, env=OFFLINE)

    assert result.returncode == 0
    assert result.stdout.splitlines()[-1].startswith('warn')
    assert 'ks package' in result.stdout

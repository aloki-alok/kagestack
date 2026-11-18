import subprocess
import sys
from pathlib import Path

KS = Path(sys.executable).parent / 'ks'
V0_15_0 = 'f291e92b1b8fc78a1758663a5f3b335b3a480ff5'
V0_16_0 = 'd561b19ca9495ac3c2b126796c2d03cd500ce12e'


def doctor(repo):
    return subprocess.run(
        [KS, 'doctor'], check=False, cwd=repo, capture_output=True, text=True
    )


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


def test_repo_on_a_release_is_healthy(tmp_path):
    repo = set_up(tmp_path, V0_16_0)

    result = doctor(repo)

    assert result.returncode == 0, result.stdout
    assert 'pinned to v0.16.0' in result.stdout


def test_older_release_warns_but_passes(tmp_path):
    repo = set_up(tmp_path, V0_15_0)

    result = doctor(repo)

    assert result.returncode == 0
    assert 'v0.15.0' in result.stdout
    assert 'run ks setup again' in result.stdout


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

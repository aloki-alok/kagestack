import json
import subprocess
import sys
import tomllib
from pathlib import Path

KS = Path(sys.executable).parent / 'ks'
SHA = 'a' * 40


def ks(repo, *args, stdin=''):
    return subprocess.run(
        [KS, *args],
        check=False,
        cwd=repo,
        input=stdin,
        capture_output=True,
        text=True,
    )


def setup(repo, *args, stdin=''):
    return ks(repo, 'setup', '--pin', SHA, *args, stdin=stdin)


def git_repo(path):
    subprocess.run(['git', 'init', '-q', '-b', 'main', path], check=True)
    return path


def commands(repo):
    return tomllib.loads((repo / 'kagestack.toml').read_text())['commands']


def workflow(repo):
    return (repo / '.github/workflows/ks.yml').read_text()


def test_uv_project_gets_commands_found_in_its_files(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'uv.lock').write_text('')
    (repo / 'pyproject.toml').write_text(
        '[tool.pytest.ini_options]\n[tool.ruff]\n[project]\nname = "x"\n'
    )

    result = setup(repo, '--yes')

    assert result.returncode == 0, result.stderr
    assert commands(repo) == {
        'install': ['uv sync --locked'],
        'lint': ['uv run ruff check'],
        'test': ['uv run pytest'],
    }
    assert f'kagestack@{SHA} ks ci' in workflow(repo)
    assert 'setup-node' not in workflow(repo)


def test_npm_project_uses_its_scripts_and_skips_the_stub_test(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'package-lock.json').write_text('{}')
    stub = 'echo "Error: no test specified" && exit 1'
    package = {'scripts': {'lint': 'oxlint', 'test': stub}}
    (repo / 'package.json').write_text(json.dumps(package))

    setup(repo, '--yes')

    assert commands(repo) == {
        'install': ['npm ci'],
        'lint': ['npm run lint'],
        'test': [],
    }
    assert 'actions/setup-node@' in workflow(repo)


def test_mixed_repo_runs_both_stacks(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'uv.lock').write_text('')
    (repo / 'pyproject.toml').write_text('[dependency-groups]\ndev = ["pytest>=8"]\n')
    (repo / 'pnpm-lock.yaml').write_text('')
    package = {'packageManager': 'pnpm@12.21.0', 'scripts': {'test': 'vitest run'}}
    (repo / 'package.json').write_text(json.dumps(package))

    setup(repo, '--yes')

    assert commands(repo)['test'] == ['uv run pytest', 'pnpm test']
    assert 'pnpm/action-setup@' in workflow(repo)


def test_nothing_found_leaves_test_empty_for_you(tmp_path):
    repo = git_repo(tmp_path)

    result = setup(repo, '--yes')

    assert commands(repo) == {'test': []}
    assert 'fill in test' in result.stdout


def test_no_answer_writes_nothing(tmp_path):
    repo = git_repo(tmp_path)

    result = setup(repo, stdin='n\n')

    assert result.returncode == 1
    assert not (repo / 'kagestack.toml').exists()
    assert not (repo / '.github').exists()


def test_yes_at_the_prompt_writes_and_a_second_run_writes_nothing(tmp_path):
    repo = git_repo(tmp_path)
    setup(repo, stdin='y\n')

    again = setup(repo)

    assert (repo / 'kagestack.toml').exists()
    assert again.returncode == 0
    assert 'wrote' not in again.stdout


def test_makefile_test_target_is_the_test_command(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'Makefile').write_text('build:\n\tcc x.c\ntest: build\n\t./x\n')

    setup(repo, '--yes')

    assert commands(repo) == {'test': ['make test']}


def test_pnpm_without_a_pinned_version_is_left_to_you(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'pnpm-lock.yaml').write_text('')
    (repo / 'package.json').write_text(json.dumps({'scripts': {'test': 'vitest'}}))

    result = setup(repo, '--yes')

    assert commands(repo) == {'test': []}
    assert 'pnpm/action-setup' not in workflow(repo)
    assert 'packageManager' in result.stdout


def test_two_lockfiles_install_once_with_the_declared_manager(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'package-lock.json').write_text('{}')
    (repo / 'pnpm-lock.yaml').write_text('')
    package = {'packageManager': 'pnpm@12.21.0', 'scripts': {'test': 'vitest'}}
    (repo / 'package.json').write_text(json.dumps(package))

    setup(repo, '--yes')

    assert commands(repo) == {
        'install': ['pnpm install --frozen-lockfile'],
        'test': ['pnpm test'],
    }


def test_pin_must_be_a_full_commit(tmp_path):
    repo = git_repo(tmp_path)

    result = ks(repo, 'setup', '--yes', '--pin', 'main')

    assert result.returncode == 2
    assert not (repo / 'kagestack.toml').exists()


def test_rerun_keeps_your_manifest_and_a_workflow_it_did_not_write(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'kagestack.toml').write_text('[commands]\ntest = "make check"\n')
    (repo / '.github/workflows').mkdir(parents=True)
    (repo / '.github/workflows/ks.yml').write_text('name: mine\n')

    result = setup(repo, '--yes')

    assert commands(repo) == {'test': 'make check'}
    assert workflow(repo) == 'name: mine\n'
    assert 'kept' in result.stdout


def test_rerun_moves_the_pin_of_a_workflow_it_wrote(tmp_path):
    repo = git_repo(tmp_path)
    setup(repo, '--yes')
    old = workflow(repo).replace(SHA, 'b' * 40)
    (repo / '.github/workflows/ks.yml').write_text(old)

    setup(repo, '--yes')

    assert f'kagestack@{SHA}' in workflow(repo)


def test_ci_runs_commands_in_order_and_stops_at_the_first_failure(tmp_path):
    repo = git_repo(tmp_path)
    manifest = (
        '[commands]\ninstall = "echo one"\ntest = ["echo two", "exit 3", "echo four"]\n'
    )
    (repo / 'kagestack.toml').write_text(manifest)

    result = ks(repo, 'ci', '--all')

    assert result.returncode == 3
    assert result.stdout.splitlines()[:4] == [
        '$ echo one',
        'one',
        '$ echo two',
        'two',
    ]
    assert 'four' not in result.stdout


def test_ci_fails_on_an_empty_test(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'kagestack.toml').write_text('[commands]\ntest = []\n')

    result = ks(repo, 'ci', '--all')

    assert result.returncode == 2
    assert 'test = "none"' in result.stderr


def test_ci_rejects_a_blank_command(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'kagestack.toml').write_text('[commands]\ninstall = " "\ntest = "none"\n')

    result = ks(repo, 'ci', '--all')

    assert result.returncode == 2
    assert 'install' in result.stderr


def test_ci_rejects_commands_that_are_not_a_table(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'kagestack.toml').write_text('commands = 3\n')

    result = ks(repo, 'ci', '--all')

    assert result.returncode == 2
    assert result.stderr.startswith('ks: ')


def test_ci_with_test_none_runs_ks_check(tmp_path):
    repo = git_repo(tmp_path)
    (repo / 'kagestack.toml').write_text('[commands]\ntest = "none"\n')
    (repo / 'app.py').write_text('x = 1  # why\n')

    result = ks(repo, 'ci', '--all')

    assert result.returncode == 1
    assert 'app.py:1' in result.stdout

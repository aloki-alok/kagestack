import json
import subprocess
import sys
from pathlib import Path

KS = Path(sys.executable).parent / 'ks'


def ks_tools(repo):
    return subprocess.run(
        [KS, 'tools'], check=False, cwd=repo, capture_output=True, text=True
    )


def test_old_js_tools_get_their_modern_swap(tmp_path):
    package = {'devDependencies': {'eslint': '9', 'prettier': '3', 'react': '19'}}
    (tmp_path / 'package.json').write_text(json.dumps(package))
    (tmp_path / '.husky').mkdir()

    result = ks_tools(tmp_path)

    assert result.returncode == 0
    assert 'eslint → oxlint' in result.stdout
    assert 'prettier → biome' in result.stdout
    assert 'husky → lefthook' in result.stdout
    assert 'react' not in result.stdout


def test_old_python_tools_get_their_modern_swap(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[tool.black]\nline-length = 88\n')
    (tmp_path / 'requirements-dev.txt').write_text('flake8==7\nmypy\n')

    result = ks_tools(tmp_path)

    assert 'black → ruff' in result.stdout
    assert 'flake8 → ruff' in result.stdout
    assert 'mypy → pyrefly' in result.stdout
    assert 'pip → uv' in result.stdout


def test_modern_repo_has_nothing_to_swap(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[tool.ruff]\n')
    (tmp_path / 'requirements.txt').write_text('httpx\n')
    (tmp_path / 'uv.lock').write_text('')

    result = ks_tools(tmp_path)

    assert result.returncode == 0
    assert '→' not in result.stdout
    assert 'checked 2026-11-18' in result.stdout


def test_broken_files_are_skipped_not_fatal(tmp_path):
    (tmp_path / 'package.json').write_text('{bad')
    (tmp_path / 'requirements.txt').write_bytes(b'flake8\n\xff\n')

    result = ks_tools(tmp_path)

    assert result.returncode == 0, result.stderr
    assert 'flake8 → ruff' in result.stdout


def test_null_dependencies_are_empty(tmp_path):
    (tmp_path / 'package.json').write_text('{"dependencies": null}')

    result = ks_tools(tmp_path)

    assert result.returncode == 0, result.stderr


def test_words_and_lookalike_packages_are_not_tools(tmp_path):
    pyproject = '[project]\ndescription = "not a black box"\ndependencies = []\n'
    (tmp_path / 'pyproject.toml').write_text(pyproject)
    (tmp_path / 'requirements.txt').write_text('mypy-extensions  # mypy later\n')
    (tmp_path / 'uv.lock').write_text('')

    result = ks_tools(tmp_path)

    assert '→' not in result.stdout


def test_poetry_project_without_a_lockfile_gets_uv(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[tool.poetry]\nname = "x"\n')

    result = ks_tools(tmp_path)

    assert 'poetry → uv' in result.stdout

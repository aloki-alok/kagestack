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

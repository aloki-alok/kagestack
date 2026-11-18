import json
import re
from pathlib import Path
from typing import NamedTuple

CHECKED = '2026-11-18'


class Swap(NamedTuple):
    old: str
    new: str
    gain: str
    verdict: str
    js: tuple = ()
    py: tuple = ()
    files: tuple = ()
    unless: tuple = ()


SWAPS = (
    Swap(
        'eslint',
        'oxlint',
        '60 to 118x faster on the VS Code repo',
        'adopt, keep eslint for plugin rules',
        js=('eslint',),
    ),
    Swap(
        'prettier',
        'biome format',
        'about 35x faster, 97% prettier output',
        'adopt',
        js=('prettier',),
    ),
    Swap(
        'jest', 'vitest', 'jest-style API with native ESM and TS', 'adopt', js=('jest',)
    ),
    Swap(
        'webpack',
        'vite',
        'Linear builds went from 46 s to 6 s',
        'adopt',
        js=('webpack',),
        files=('webpack.config.js',),
    ),
    Swap(
        'husky',
        'lefthook',
        'husky has had no release since 2024-11',
        'adopt',
        js=('husky',),
        files=('.husky',),
    ),
    Swap(
        'npm',
        'pnpm',
        'clean install 1 min 44 s down to 14 s',
        'adopt',
        files=('package-lock.json',),
    ),
    Swap(
        'yarn',
        'pnpm',
        'faster installs, strict dependencies',
        'adopt',
        files=('yarn.lock',),
    ),
    Swap(
        'black', 'ruff', '10 to 100x faster, 99.9% black output', 'adopt', py=('black',)
    ),
    Swap(
        'flake8',
        'ruff',
        '10 to 100x faster',
        'adopt',
        py=('flake8',),
        files=('.flake8',),
    ),
    Swap(
        'pylint',
        'ruff',
        '10 to 100x faster',
        'adopt, keep pylint for type inference checks',
        py=('pylint',),
    ),
    Swap('isort', 'ruff', 'same job inside the linter', 'adopt', py=('isort',)),
    Swap(
        'mypy',
        'pyrefly',
        '15x faster than mypy on PyTorch',
        'adopt, keep mypy in CI at first',
        py=('mypy',),
    ),
    Swap('poetry', 'uv', '10 to 100x faster installs', 'adopt', files=('poetry.lock',)),
    Swap(
        'pip',
        'uv',
        '10 to 100x faster installs',
        'adopt',
        files=('requirements.txt', 'requirements-dev.txt', 'Pipfile'),
        unless=('uv.lock',),
    ),
    Swap(
        'pre-commit',
        'prek',
        'same config, runs faster',
        'adopt, the config still runs in pre-commit',
        files=('.pre-commit-config.yaml',),
    ),
)


def js_dependencies(root):
    package = root / 'package.json'
    if not package.exists():
        return set()
    data = json.loads(package.read_text())
    return {*data.get('dependencies', {}), *data.get('devDependencies', {})}


def python_text(root):
    files = [
        root / 'pyproject.toml',
        root / 'setup.cfg',
        *root.glob('requirements*.txt'),
    ]
    return '\n'.join(path.read_text() for path in files if path.exists())


def found(swap, root, js, py):
    if any((root / name).exists() for name in swap.unless):
        return False
    return (
        any(name in js for name in swap.js)
        or any(re.search(rf'\b{re.escape(name)}\b', py) for name in swap.py)
        or any((root / name).exists() for name in swap.files)
    )


def tools(_args):
    root = Path.cwd()
    js, py = js_dependencies(root), python_text(root)
    swaps = [swap for swap in SWAPS if found(swap, root, js, py)]
    for swap in swaps:
        print(f'{swap.old} → {swap.new}: {swap.gain}. {swap.verdict}.')
    if not swaps:
        print('no older tools found ✧(◕‿◕)✧')
    print(f'checked {CHECKED}. the scout playbook rechecks the list.')
    return 0

import importlib.metadata
import json
import re
import subprocess
import tomllib
from pathlib import Path
from typing import NamedTuple

from ks.tools import package_json, python_tools

REPO = 'https://github.com/aloki-alok/kagestack'
MANIFEST = 'kagestack.toml'
WORKFLOW = '.github/workflows/ks.yml'
MARK = '# written by ks setup. run ks setup again to move the pin.'
KEYS = ('install', 'lint', 'test')
JS_SCRIPTS = {'lint': 'lint', 'typecheck': 'lint', 'test': 'test'}
JS_LOCKFILES = {
    'package-lock.json': ('npm ci', 'npm run'),
    'pnpm-lock.yaml': ('pnpm install --frozen-lockfile', 'pnpm'),
}
NPM_STUB_TEST = 'no test specified'
PIN = re.compile(r'[0-9a-f]{40}')
RELEASE = re.compile(r'v(\d+)\.(\d+)\.(\d+)')
PINNED = re.compile(r'kagestack@(\S+) ks ci')
CHECKOUT = 'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1'
SETUP_UV = 'astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3'
SETUP_PNPM = 'pnpm/action-setup@73e46992e05b19abd31f2f3c20e0e7370d762115 # v6.1.1'
SETUP_NODE = 'actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0'


class Found(NamedTuple):
    key: str
    command: str
    source: str


class ManifestError(ValueError):
    pass


def js_lockfile(root):
    declared = str(package_json(root).get('packageManager', ''))
    if (root / 'pnpm-lock.yaml').exists() and declared.startswith('pnpm@'):
        return 'pnpm-lock.yaml'
    if (root / 'package-lock.json').exists():
        return 'package-lock.json'
    return None


def js_commands(root):
    if not (lockfile := js_lockfile(root)):
        return
    install, run = JS_LOCKFILES[lockfile]
    yield Found('install', install, lockfile)
    scripts = package_json(root).get('scripts')
    scripts = scripts if isinstance(scripts, dict) else {}
    for script, key in JS_SCRIPTS.items():
        body = scripts.get(script)
        if isinstance(body, str) and NPM_STUB_TEST not in body:
            yield Found(key, f'{run} {script}', 'package.json')


def python_commands(root):
    if not (root / 'uv.lock').exists():
        return
    tools = python_tools(root)
    yield Found('install', 'uv sync --locked', 'uv.lock')
    if 'ruff' in tools or (root / 'ruff.toml').exists():
        yield Found('lint', 'uv run ruff check', 'pyproject.toml')
    if 'pytest' in tools or (root / 'pytest.ini').exists():
        yield Found('test', 'uv run pytest', 'pyproject.toml')


def make_test(root, found):
    makefile = root / 'Makefile'
    targets = makefile.read_text(errors='replace') if makefile.exists() else ''
    has_test = any(f.key == 'test' for f in found)
    if not has_test and any(line.startswith('test:') for line in targets.splitlines()):
        yield Found('test', 'make test', 'Makefile')


def draft(root):
    found = [*python_commands(root), *js_commands(root)]
    return [*found, *make_test(root, found)]


def manifest_text(found):
    lines = ['# ks ci runs these in order, then ks check.', '[commands]']
    for key in KEYS:
        items = [f for f in found if f.key == key]
        if items:
            sources = ', '.join(dict.fromkeys(f.source for f in items))
            comment = f'found in {sources}'
        elif key == 'test':
            comment = 'nothing found: add your test command, or "none"'
        else:
            continue
        commands = json.dumps([f.command for f in items])
        lines.append(f'{key} = {commands}  # {comment}')
    return '\n'.join(lines) + '\n'


def workflow_text(root, pin):
    node = []
    if (root / 'package.json').exists():
        if js_lockfile(root) == 'pnpm-lock.yaml':
            node.append(f'      - uses: {SETUP_PNPM}')
        version_file = next(
            (n for n in ('.nvmrc', '.node-version') if (root / n).exists()), None
        )
        version = (
            f'node-version-file: {version_file}'
            if version_file
            else ('node-version: lts/*')
        )
        node += [f'      - uses: {SETUP_NODE}', '        with:', f'          {version}']
    return '\n'.join(
        [
            MARK,
            'name: ks',
            '',
            'on:',
            '  pull_request:',
            '',
            'jobs:',
            '  check:',
            '    runs-on: ubuntu-latest',
            '    steps:',
            f'      - uses: {CHECKOUT}',
            '        with:',
            '          fetch-depth: 0',
            f'      - uses: {SETUP_UV}',
            *node,
            f'      - run: uvx --from git+{REPO}@{pin} ks ci --base "$BASE"',
            '        env:',
            '          BASE: origin/${{ github.base_ref }}',
            '',
        ]
    )


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def repo_root():
    return Path(run('git', 'rev-parse', '--show-toplevel').strip())


def releases():
    tags = {}
    for line in run('git', 'ls-remote', '--tags', REPO).splitlines():
        sha, ref = line.split('\t')
        name = ref.removeprefix('refs/tags/')
        if name.endswith('^{}'):
            tags[name.removesuffix('^{}')] = sha
        else:
            tags.setdefault(name, sha)
    return {tag: sha for tag, sha in tags.items() if RELEASE.fullmatch(tag)}


def version(tag):
    return tuple(int(part) for part in RELEASE.fullmatch(tag).groups())


def own_commit():
    dist = importlib.metadata.distribution('kagestack')
    direct = json.loads(dist.read_text('direct_url.json') or '{}')
    if commit := direct.get('vcs_info', {}).get('commit_id'):
        return commit
    tag = f'v{dist.version}'
    if not (commit := releases().get(tag)):
        raise ManifestError(f'no release {tag} found. pass --pin <commit>.')
    return commit


def read_commands(root):
    path = root / MANIFEST
    if not path.exists():
        raise ManifestError(f'no {MANIFEST}. run ks setup first.')
    try:
        table = tomllib.loads(path.read_text()).get('commands', {})
    except tomllib.TOMLDecodeError as error:
        raise ManifestError(f'{MANIFEST}: {error}') from error
    if not isinstance(table, dict):
        raise ManifestError(f'{MANIFEST}: commands must be a table')
    commands = {}
    for key, value in table.items():
        value = [value] if isinstance(value, str) else value
        if not isinstance(value, list) or not all(
            isinstance(v, str) and v.strip() for v in value
        ):
            raise ManifestError(f'{MANIFEST}: {key} must be a command or a list')
        commands[key] = value
    if not commands.get('test'):
        raise ManifestError(f'{MANIFEST} needs a test command, or test = "none".')
    return commands


def confirmed():
    try:
        return input('write these files? [y/N] ').strip().lower() == 'y'
    except EOFError:
        return False


def setup(args):
    root = repo_root()
    if args.pin and not PIN.fullmatch(args.pin):
        raise ManifestError('--pin takes a full 40-character commit hash.')
    found = draft(root)
    manifest, workflow = root / MANIFEST, root / WORKFLOW
    plan = {}
    if manifest.exists():
        print(f'kept {MANIFEST}')
    else:
        plan[manifest] = manifest_text(found)
    if workflow.exists() and MARK not in workflow.read_text():
        print(f'kept {WORKFLOW}: ks setup did not write it')
    else:
        plan[workflow] = workflow_text(root, args.pin or own_commit())
    plan = {
        p: text for p, text in plan.items() if not p.exists() or p.read_text() != text
    }
    for path, text in plan.items():
        print(f'--- {path.relative_to(root)}\n{text}')
    if plan and not args.yes and not confirmed():
        print('nothing written')
        return 1
    for path, text in plan.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f'wrote {path.relative_to(root)}')
    if manifest in plan and not any(f.key == 'test' for f in found):
        print(f'fill in test in {MANIFEST}, or set test = "none" (・_・;)')
    if (root / 'pnpm-lock.yaml').exists() and js_lockfile(root) != 'pnpm-lock.yaml':
        print('pnpm: set packageManager in package.json, then run ks setup again.')
    return 0


def pin_health(text):
    pin = PINNED.search(text)
    by_commit = {sha: tag for tag, sha in releases().items()}
    tag = by_commit.get(pin[1]) if pin else None
    if not tag:
        found = pin[1] if pin else 'nothing'
        return 'fail', f'{WORKFLOW} pins {found}, not a release. run ks setup again.'
    newest = max(by_commit.values(), key=version)
    if newest != tag:
        return (
            'warn',
            f'{WORKFLOW} pinned to {tag}, {newest} is out. run ks setup again.',
        )
    return 'ok', f'{WORKFLOW} pinned to {tag}'


def doctor(_args):
    root = repo_root()
    try:
        commands = read_commands(root)
        results = [('ok', f'{MANIFEST} runs {", ".join(commands)}')]
    except ManifestError as error:
        results = [('fail', str(error))]
    workflow = root / WORKFLOW
    text = workflow.read_text() if workflow.exists() else ''
    if not workflow.exists():
        results.append(('fail', f'no {WORKFLOW}. run ks setup.'))
    elif not text.strip():
        results.append(('fail', f'{WORKFLOW} is empty. run ks setup again.'))
    elif MARK not in text:
        results.append(('skip', f'{WORKFLOW} not written by ks setup'))
    else:
        try:
            results.append(pin_health(text))
        except subprocess.CalledProcessError:
            results.append(('warn', f'cannot reach {REPO} to check the pin'))
    for level, message in results:
        print(f'{level:5} {message}')
    return 1 if any(level == 'fail' for level, _ in results) else 0

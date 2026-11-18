import subprocess

from ks.package import OUT, PREFIX, stale_files
from ks.setup import (
    MANIFEST,
    MARK,
    PINNED,
    REPO,
    WORKFLOW,
    ManifestError,
    read_commands,
    releases,
    repo_root,
    version,
)


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
    out = root / OUT
    if any(out.glob(f'{PREFIX}*')) and stale_files(out):
        results.append(('warn', f'{OUT} is stale. run ks package.'))
    for level, message in results:
        print(f'{level:5} {message}')
    return 1 if any(level == 'fail' for level, _ in results) else 0

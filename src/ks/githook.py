import os
import subprocess
from pathlib import Path

HOOK_NAMES = (
    'applypatch-msg',
    'pre-applypatch',
    'post-applypatch',
    'pre-commit',
    'pre-merge-commit',
    'prepare-commit-msg',
    'commit-msg',
    'post-commit',
    'pre-rebase',
    'post-checkout',
    'post-merge',
    'pre-push',
    'pre-receive',
    'update',
    'proc-receive',
    'post-receive',
    'post-update',
    'reference-transaction',
    'push-to-checkout',
    'pre-auto-gc',
    'post-rewrite',
    'sendemail-validate',
    'post-index-change',
)

DISPATCH = """#!/bin/sh
name=$(basename "$0")
if [ "$name" = pre-commit ]; then
  if command -v ks > /dev/null; then
    ks check --base HEAD
    [ $? = 1 ] && exit 1
  else
    echo "kagestack: ks not found, comment check skipped" >&2
  fi
fi
own="$(git rev-parse --git-common-dir)/hooks/$name"
[ -x "$own" ] && exec "$own" "$@"
exit 0
"""


def hooks_folder():
    config = os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config'
    return Path(config) / 'kagestack' / 'git-hooks'


def git_hook(args):
    folder = hooks_folder()
    current = subprocess.run(
        ['git', 'config', '--global', '--get', 'core.hooksPath'],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if current and Path(current).expanduser() != folder:
        print(f'ks: git already uses {current} for hooks. left it alone.')
        return 1
    folder.mkdir(parents=True, exist_ok=True)
    for name in HOOK_NAMES:
        hook = folder / name
        hook.write_text(DISPATCH)
        hook.chmod(0o755)
    subprocess.run(
        ['git', 'config', '--global', 'core.hooksPath', str(folder)], check=True
    )
    print(f'every commit now runs ks check. hooks: {folder}')
    print("each repo's own hooks still run after it.")
    print('undo: git config --global --unset core.hooksPath')
    return 0

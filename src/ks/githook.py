import os
import subprocess
from pathlib import Path

HOOK_NAMES = (
    'pre-commit',
    'pre-merge-commit',
    'prepare-commit-msg',
    'commit-msg',
    'post-commit',
    'pre-rebase',
    'post-checkout',
    'post-merge',
    'pre-push',
    'post-rewrite',
)

DISPATCH = """#!/bin/sh
name=${0##*/}
if [ "$name" = pre-commit ]; then
  git_dir=$(git rev-parse --git-dir)
  if [ -e "$git_dir/MERGE_HEAD" ] || [ -e "$git_dir/CHERRY_PICK_HEAD" ] || [ -e "$git_dir/REVERT_HEAD" ]; then
    :
  elif command -v ks > /dev/null; then
    found=$(ks check --staged)
    [ $? = 1 ] && echo "$found" && exit 1
  else
    echo "kagestack: ks not found, check skipped" >&2
  fi
fi
if [ -d .git ]; then common=.git; else common=$(git rev-parse --git-common-dir 2> /dev/null); fi
own="$common/hooks/$name"
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
    if not current:
        saved = subprocess.run(
            ['git', 'config', '--global', 'core.hooksPath', str(folder)],
            capture_output=True,
            text=True,
        )
        if saved.returncode:
            print(f'ks: git could not save the setting. {saved.stderr.strip()}')
            print('if your git config is read-only (Nix home-manager), add this:')
            print(f'  core.hooksPath = {folder}')
            return 1
    print(f'every commit now runs ks check. hooks: {folder}')
    print("each repo's own hooks still run after it.")
    print('undo: git config --global --unset core.hooksPath')
    return 0

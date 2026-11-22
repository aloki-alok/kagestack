import argparse
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path
from typing import NamedTuple

from ks.doctor import doctor
from ks.githook import git_hook
from ks.package import package
from ks.screens import add_arguments as add_screen_arguments
from ks.screens import screens
from ks.setup import ManifestError, read_commands, setup
from ks.tools import tools

RULES = """
id: comment
language: python
rule: {kind: comment}
---
id: comment
language: javascript
rule: {kind: comment}
---
id: comment
language: typescript
rule: {kind: comment}
---
id: comment
language: tsx
rule: {kind: comment}
---
id: docstring
language: python
rule: {kind: string, inside: {kind: expression_statement}}
"""
TOOL_DIRECTIVE = re.compile(
    r'///\s*<reference'
    r'|(#|//|/\*+)\s*('
    r'noqa|type:\s*ignore|pyright:|pylint:|fmt:\s*(on|off|skip)|pragma: no cover'
    r'|eslint-(disable|enable|env)|@ts-(check|expect-error|ignore|nocheck)'
    r'|prettier-ignore|biome-ignore|#\s*sourceMappingURL=|SPDX-License-Identifier:'
    r')',
    re.IGNORECASE,
)
SUPPRESSES_EVERY_RULE = re.compile(
    r'noqa(?!\s*:\s*\w)|(type|pyright):\s*ignore(?!\s*\[)|@ts-(ignore|nocheck)'
    r'|eslint-disable(-next-line|-line)?(?=\s*(--|\*/|$))',
    re.IGNORECASE,
)
FILE_HEADER = re.compile(r'#!|#.*coding[:=]')
FILE_HEADER_LINES = 2
ADVICE = (
    'put the why in a name, a test, or the commit message, not in a comment.\n'
    'a suppression must name the rule it silences. if that rule guards correctness,'
    ' fix the code instead.'
)
EVERY_LINE = range(1, sys.maxsize)
EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
DEFAULT_BASES = ('origin/HEAD', 'origin/main', 'origin/master', 'main', 'master')
FILE_PATCH = re.compile(r'^diff --git ', re.MULTILINE)
HUNK = re.compile(r'^@@ -\S+ \+(\d+)(?:,(\d+))? @@', re.MULTILINE)
PATHS_PER_SCAN = 1000


class Hit(NamedTuple):
    path: str
    first_line: int
    last_line: int
    text: str


def git(*args):
    return subprocess.run(
        ['git', *args], check=True, capture_output=True, text=True, errors='replace'
    ).stdout


def every_line_of_every_file():
    paths = git('ls-files', '-z', '--cached', '--others', '--exclude-standard')
    return {path: EVERY_LINE for path in paths.split('\0') if path}


def default_base():
    for ref in DEFAULT_BASES:
        found = subprocess.run(
            ['git', 'rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}'],
            check=False,
            capture_output=True,
        )
        if found.returncode == 0:
            return ref
    return None


def lines_added_since(base):
    merge_base = git('merge-base', base, 'HEAD').strip()
    added, removed = lines_added_in(('diff', merge_base))
    untracked = git('ls-files', '-z', '--others', '--exclude-standard')
    added.update({path: EVERY_LINE for path in untracked.split('\0') if path})
    return added, removed


def lines_staged(into):
    head = subprocess.run(['git', 'rev-parse', '-q', '--verify', 'HEAD'], check=False)
    parent = 'HEAD' if head.returncode == 0 else EMPTY_TREE
    added, removed = lines_added_in(('diff', '--cached', parent))
    added = {path: lines for path, lines in added.items() if lines}
    for path in added:
        copy = Path(into, path)
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_text(git('show', f':{path}'))
    return added, removed


def lines_added_in(diff):
    diff = (*diff, '--find-renames', '--no-ext-diff')
    paths = git(*diff, '--name-only', '-z').split('\0')[:-1]
    patches = FILE_PATCH.split(git(*diff, '--no-color', '-U0'))[1:]
    added, removed = {}, []
    for path, patch in zip(paths, patches, strict=True):
        added[path] = set()
        for hunk in HUNK.finditer(patch):
            start, count = int(hunk[1]), int(hunk[2] or 1)
            added[path].update(range(start, start + count))
        if first_hunk := HUNK.search(patch):
            body = patch[first_hunk.start() :].splitlines()
            removed += [f'{line[1:].rstrip()}\n' for line in body if line[:1] == '-']
    return added, ''.join(removed)


def find_hits(paths):
    ast_grep = shutil.which('ast-grep', path=sysconfig.get_path('scripts'))
    for start in range(0, len(paths), PATHS_PER_SCAN):
        batch = paths[start : start + PATHS_PER_SCAN]
        scan = [ast_grep, 'scan', '--inline-rules', RULES, '--json=stream', *batch]
        output = subprocess.run(scan, check=True, capture_output=True, text=True)
        for line in output.stdout.splitlines():
            match = json.loads(line)
            yield Hit(
                path=match['file'],
                first_line=match['range']['start']['line'] + 1,
                last_line=match['range']['end']['line'] + 1,
                text=match['text'],
            )


def is_directive(hit):
    in_header = hit.first_line <= FILE_HEADER_LINES
    if SUPPRESSES_EVERY_RULE.search(hit.text):
        return False
    return bool(
        TOOL_DIRECTIVE.match(hit.text) or in_header and FILE_HEADER.match(hit.text)
    )


def was_moved(hit, removed):
    return all(f'{line.strip()}\n' in removed for line in hit.text.splitlines())


def check(args):
    top = Path(git('rev-parse', '--show-toplevel').strip()).resolve()
    inside = [Path(path).resolve() for path in args.paths]
    only = {str(path.relative_to(top)) for path in inside if path.is_relative_to(top)}
    os.chdir(top)
    staged = tempfile.TemporaryDirectory()
    if args.all:
        lines_to_check, removed = every_line_of_every_file(), ''
    elif args.staged:
        lines_to_check, removed = lines_staged(staged.name)
        os.chdir(staged.name)
    elif base := args.base or default_base():
        lines_to_check, removed = lines_added_since(base)
    else:
        print('ks: no default branch found. pass --base <ref>.', file=sys.stderr)
        return 2
    if args.paths:
        lines_to_check = {p: n for p, n in lines_to_check.items() if p in only}
    hits = sorted(
        hit
        for hit in find_hits(sorted(lines_to_check))
        if not is_directive(hit)
        and not was_moved(hit, removed)
        and any(
            line in lines_to_check[hit.path]
            for line in range(hit.first_line, hit.last_line + 1)
        )
    )
    os.chdir(top)
    staged.cleanup()
    for hit in hits:
        print(f'{hit.path}:{hit.first_line}: {hit.text.splitlines()[0]}')
    if hits:
        lines = sum(hit.last_line - hit.first_line + 1 for hit in hits)
        print(f'{len(hits)} comments on {lines} lines')
        print(ADVICE)
        return 1
    print('no new comments')
    return 0


def ci(args):
    root = git('rev-parse', '--show-toplevel').strip()
    commands = read_commands(Path(root))
    for group in commands.values():
        for command in group:
            if command == 'none':
                continue
            print(f'$ {command}', flush=True)
            run = subprocess.run(command, shell=True, check=False, cwd=root)
            if run.returncode:
                return run.returncode
    return check(args)


def add_scope(command):
    scope = command.add_mutually_exclusive_group()
    scope.add_argument(
        '--all', action='store_true', help='report every comment, not only new ones'
    )
    scope.add_argument(
        '--base', help='count lines added since this ref (default: the main branch)'
    )
    return scope


def main():
    parser = argparse.ArgumentParser(
        prog='ks',
        description='checks and playbooks that keep coding agents writing clean code',
    )
    version = importlib.metadata.version('kagestack')
    parser.add_argument('--version', action='version', version=f'ks {version}')
    commands = parser.add_subparsers(
        title='commands', metavar='<command>', required=True
    )

    def command(name, run, summary):
        parsed = commands.add_parser(name, help=summary, description=summary)
        parsed.set_defaults(run=run)
        return parsed

    setup_command = command(
        'setup', setup, 'write kagestack.toml and a CI job pinned to this release'
    )
    setup_command.add_argument(
        '--yes', action='store_true', help='write without asking'
    )
    setup_command.add_argument(
        '--pin', metavar='COMMIT', help='kagestack commit for CI to run'
    )
    ci_command = command('ci', ci, 'run the kagestack.toml commands, then ks check')
    add_scope(ci_command)
    ci_command.set_defaults(paths=[], staged=False)
    check_command = command('check', check, 'fail on comments this branch added')
    add_scope(check_command).add_argument(
        '--staged', action='store_true', help='check only what the next commit holds'
    )
    check_command.add_argument('paths', nargs='*', help='check only these files')
    command('doctor', doctor, "check this repo's ks setup")
    command('git-hook', git_hook, 'run ks check on every commit, in every repo')
    command(
        'package',
        package,
        'write the playbooks to .agents/skills for codex and opencode',
    ).add_argument('--check', action='store_true', help='fail if they are stale')
    command('tools', tools, 'name faster, maintained replacements for old dev tools')
    add_screen_arguments(
        command(
            'screens',
            screens,
            'screenshot a page on phones and desktops in every browser engine, and list its layout and console problems',
        )
    )
    args = parser.parse_args()
    try:
        return args.run(args)
    except subprocess.CalledProcessError as error:
        reason = error.stderr.strip() or f'{" ".join(error.cmd[:2])} failed'
        print(f'ks: {reason}', file=sys.stderr)
        return 2
    except ManifestError as error:
        print(f'ks: {error}', file=sys.stderr)
        return 2

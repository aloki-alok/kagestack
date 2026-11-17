import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
from typing import NamedTuple

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
    r'|eslint-(disable|enable)|@ts-(expect-error|ignore|nocheck)'
    r'|prettier-ignore|biome-ignore'
    r')'
)
FILE_HEADER = re.compile(r'#!|#.*coding[:=]')
FILE_HEADER_LINES = 2
ADVICE = 'put the why in a name, a test, or the commit message, not in a comment.'
EVERY_LINE = range(1, sys.maxsize)
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
            capture_output=True,
        )
        if found.returncode == 0:
            return ref
    return None


def lines_added_since(base):
    merge_base = git('merge-base', base, 'HEAD').strip()
    diff = ('diff', merge_base, '--find-renames', '--diff-filter=d', '--no-ext-diff')
    paths = git(*diff, '--name-only', '-z').split('\0')[:-1]
    patches = FILE_PATCH.split(git(*diff, '--no-color', '-U0'))[1:]
    added = {}
    for path, patch in zip(paths, patches, strict=True):
        added[path] = set()
        for hunk in HUNK.finditer(patch):
            start, count = int(hunk[1]), int(hunk[2] or 1)
            added[path].update(range(start, start + count))
    untracked = git('ls-files', '-z', '--others', '--exclude-standard')
    added.update({path: EVERY_LINE for path in untracked.split('\0') if path})
    return added


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
                text=match['text'].splitlines()[0],
            )


def is_directive(hit):
    in_header = hit.first_line <= FILE_HEADER_LINES
    return bool(
        TOOL_DIRECTIVE.match(hit.text) or in_header and FILE_HEADER.match(hit.text)
    )


def check(args):
    os.chdir(git('rev-parse', '--show-toplevel').strip())
    if args.all:
        lines_to_check = every_line_of_every_file()
    elif base := args.base or default_base():
        lines_to_check = lines_added_since(base)
    else:
        print('ks: no default branch found. pass --base <ref>.', file=sys.stderr)
        return 2
    hits = sorted(
        hit
        for hit in find_hits(sorted(lines_to_check))
        if not is_directive(hit)
        and any(
            line in lines_to_check[hit.path]
            for line in range(hit.first_line, hit.last_line + 1)
        )
    )
    for hit in hits:
        print(f'{hit.path}:{hit.first_line}: {hit.text}')
    if hits:
        print(ADVICE)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(prog='ks')
    commands = parser.add_subparsers(dest='command', required=True)
    check_command = commands.add_parser('check', help='fail on comments in code')
    scope = check_command.add_mutually_exclusive_group()
    scope.add_argument(
        '--all', action='store_true', help='report every comment, not only new ones'
    )
    scope.add_argument(
        '--base', help='count lines added since this ref (default: the main branch)'
    )
    args = parser.parse_args()
    try:
        return check(args)
    except subprocess.CalledProcessError as error:
        print(f'ks: {error.stderr.strip()}', file=sys.stderr)
        return 2

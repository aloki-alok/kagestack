import argparse
import json
import os
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
ADVICE = 'put the why in a name, a test, or the commit message, not in a comment.'
EVERY_LINE = range(1, sys.maxsize)
PATHS_PER_SCAN = 1000


class Hit(NamedTuple):
    path: str
    first_line: int
    last_line: int
    text: str


def git(*args):
    return subprocess.run(
        ['git', *args], check=True, capture_output=True, text=True
    ).stdout


def every_file():
    paths = git('ls-files', '-z', '--cached', '--others', '--exclude-standard')
    return {path: EVERY_LINE for path in paths.split('\0') if path}


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


def check(args):
    os.chdir(git('rev-parse', '--show-toplevel').strip())
    lines_to_check = every_file()
    hits = sorted(find_hits(sorted(lines_to_check)))
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
    check_command.add_argument(
        '--all', action='store_true', help='report every comment, not only new ones'
    )
    args = parser.parse_args()
    try:
        return check(args)
    except subprocess.CalledProcessError as error:
        print(f'ks: {error.stderr.strip()}', file=sys.stderr)
        return 2

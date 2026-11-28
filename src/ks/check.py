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

from ks.setup import read_commands

JS_LANGUAGES = ('javascript', 'typescript', 'tsx')
OTHER_COMMENT_LANGUAGES = ('yaml', 'css', 'bash')
SKIPPED_JS_TESTS = (
    r"""rule: {pattern: '$TEST($TITLE, $$$REST)'}
constraints:
  TEST: {regex: '^((describe|it|test|suite|context|test\.describe)\.(skip|only|fixme)|x(it|test|describe)|f(it|describe))$'}
  TITLE: {any: [{kind: string}, {kind: template_string}]}""",
    r"""rule: {pattern: '$TEST()'}
constraints:
  TEST: {regex: '^(describe|it|test)\.(skip|fixme)$'}""",
    r"""rule: {pattern: '$TEST($$$)($$$)'}
constraints:
  TEST: {regex: '^(describe|it|test)\.(skip|only)\.each$'}""",
)
SKIPPED_PYTHON_TEST = (
    r"rule: {any: [{kind: attribute, regex: '^(pytest\.mark\.skip|unittest\.skip)$'},"
    r" {kind: decorator, regex: '^@skip\b'},"
    " {pattern: 'pytest.skip($$$)', inside: {kind: expression_statement,"
    ' inside: {kind: block, inside: {kind: function_definition}}}}]}'
)
JS_FUNCTION = (
    'rule: {any: [{kind: function_declaration}, {kind: generator_function_declaration},'
    ' {kind: method_definition}, {kind: arrow_function}, {kind: function_expression}],'
    ' not: {inside: {kind: arguments, inside: {kind: call_expression,'
    r" regex: '^(describe|suite|context|test\.describe)\b'}}}}"
)
FUNCTION_RULES = (
    ('function', 'python', 'rule: {kind: function_definition}'),
    *(('function', language, JS_FUNCTION) for language in JS_LANGUAGES),
)
SWALLOWED_PYTHON = (
    r'rule: {kind: except_clause, any: [{regex: "^except\\s*:"},'
    r' {regex: "^except[^\\n]*:\\s*(pass|\\.\\.\\.)\\s*$"}]}'
)
SWALLOWED_JS = (
    r'rule: {any: [{kind: catch_clause, has: {field: body, regex: "^\\{\\s*\\}$"}},'
    r' {kind: call_expression,'
    r' regex: "\\.catch\\(\\s*(\\(\\s*\\w*\\s*\\)|\\w+)\\s*=>\\s*\\{\\s*\\}\\s*\\)$"}]}'
)
ANY_TYPE = (
    'rule: {kind: predefined_type, regex: "^any$",'
    ' not: {inside: {kind: constraint, stopBy: end}}}'
)
NESTING_LIMIT = 3
PYTHON_BLOCKS = (
    '{any: [{kind: if_statement}, {kind: for_statement}, {kind: while_statement},'
    ' {kind: try_statement}, {kind: with_statement}, {kind: match_statement}]}'
)
PYTHON_FUNCTIONS = '{any: [{kind: function_definition}, {kind: lambda}]}'
JS_BLOCKS = (
    '{any: [{kind: if_statement, not: {inside: {kind: else_clause}}},'
    ' {kind: for_statement}, {kind: for_in_statement}, {kind: while_statement},'
    ' {kind: do_statement}, {kind: try_statement}, {kind: switch_statement}]}'
)
JS_FUNCTIONS = (
    '{any: [{kind: function_declaration}, {kind: function_expression},'
    ' {kind: arrow_function}, {kind: method_definition},'
    ' {kind: generator_function_declaration}, {kind: generator_function}]}'
)


def nested_past_the_limit(block, function):
    rule = block
    for _ in range(NESTING_LIMIT):
        rule = f'{{all: [{block}, {{inside: {{stopBy: {function}, all: [{rule}]}}}}]}}'
    return f'rule: {rule}'


def as_yaml(rules):
    return '\n---\n'.join(
        f'id: {rule}\nlanguage: {language}\n{body}' for rule, language, body in rules
    )


RULES = as_yaml(
    (
        ('comment', 'python', 'rule: {kind: comment}'),
        *(('comment', language, 'rule: {kind: comment}') for language in JS_LANGUAGES),
        *(
            ('comment', language, 'rule: {kind: comment}')
            for language in OTHER_COMMENT_LANGUAGES
        ),
        (
            'comment',
            'python',
            'rule: {kind: string, inside: {kind: expression_statement}}',
        ),
        ('skipped-test', 'python', SKIPPED_PYTHON_TEST),
        *(
            ('skipped-test', language, body)
            for language in JS_LANGUAGES
            for body in SKIPPED_JS_TESTS
        ),
        *FUNCTION_RULES,
        ('swallowed-error', 'python', SWALLOWED_PYTHON),
        *(('swallowed-error', language, SWALLOWED_JS) for language in JS_LANGUAGES),
        *(('any-type', language, ANY_TYPE) for language in ('typescript', 'tsx')),
        (
            'nesting',
            'python',
            nested_past_the_limit(PYTHON_BLOCKS, PYTHON_FUNCTIONS),
        ),
        *(
            ('nesting', language, nested_past_the_limit(JS_BLOCKS, JS_FUNCTIONS))
            for language in JS_LANGUAGES
        ),
    )
)
TOOL_DIRECTIVE = re.compile(
    r'///\s*<reference'
    r'|#\s*v\d+(\.\d+)*\s*$'
    r'|(#|//|/\*+)\s*('
    r'noqa|type:\s*ignore|pyright:|pylint:|fmt:\s*(on|off|skip)|pragma: no cover'
    r'|(eslint|oxlint)-(disable|enable|env)|@ts-(check|expect-error|ignore|nocheck)'
    r'|prettier-ignore|biome-ignore|#\s*sourceMappingURL=|SPDX-License-Identifier:'
    r'|@(vitest|jest)-environment\b'
    r'|yaml-language-server:|yamllint\s+(disable|enable)|stylelint-(disable|enable)'
    r'|shellcheck\s+(disable|source|shell)='
    r')',
    re.IGNORECASE,
)
SUPPRESSES_EVERY_RULE = re.compile(
    r'noqa(?!\s*:\s*\w)|(type|pyright):\s*ignore(?!\s*\[)|@ts-(ignore|nocheck)'
    r'|(eslint|oxlint)-disable(-next-line|-line)?(?=\s*(--|\*/|$))',
    re.IGNORECASE,
)
FILE_HEADER = re.compile(r'#!|#.*coding[:=]')
FILE_HEADER_LINES = 2
ADVICE = (
    'put the why in a name, a test, or the commit message, not in a comment.\n'
    'a suppression must name the rule it silences. if that rule guards correctness,'
    ' fix the code instead.'
)
FUNCTION_LIMIT = 60
FINDINGS = {
    'comment': ADVICE,
    'skipped-test': (
        'fix the test or the code. delete a test that no longer applies,'
        ' do not skip it.'
    ),
    'function': 'split it into steps whose names say what each one does.',
    'swallowed-error': (
        'catch only the error you expect and handle it, or let it reach someone'
        ' who can act on it.'
    ),
    'any-type': (
        'name the type. parse outside data from unknown into a type where it enters.'
    ),
    'nesting': 'return early, or move the inner block into a function with a name.',
}
NESTED_RULES = ('function', 'nesting')
EVERY_LINE = range(1, sys.maxsize)
DEFAULT_BASES = ('origin/HEAD', 'origin/main', 'origin/master', 'main', 'master')
FILE_PATCH = re.compile(r'^diff --git ', re.MULTILINE)
HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)
PATHS_PER_SCAN = 1000
MINIFIED_LINE = 10_000
MINIFIED_SAMPLE = 65_536
CODE_SUFFIXES = (
    '.py',
    '.pyi',
    '.js',
    '.jsx',
    '.mjs',
    '.cjs',
    '.ts',
    '.mts',
    '.cts',
    '.tsx',
)


class Hit(NamedTuple):
    path: str
    first_line: int
    last_line: int
    text: str
    rule: str
    source: str


class Diff(NamedTuple):
    added: dict
    hunks: dict
    removed: str
    old_blobs: dict


def git(*args):
    return subprocess.run(
        ['git', *args], check=True, capture_output=True, text=True, errors='replace'
    ).stdout


def every_line_of_every_file():
    paths = git('ls-files', '-z', '--cached', '--others', '--exclude-standard')
    return Diff({path: EVERY_LINE for path in paths.split('\0') if path}, {}, '', {})


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
    diff = lines_added_in(('diff', merge_base))
    untracked = git('ls-files', '-z', '--others', '--exclude-standard')
    diff.added.update({path: EVERY_LINE for path in untracked.split('\0') if path})
    return diff


def lines_staged(into):
    head = subprocess.run(
        ['git', 'rev-parse', '-q', '--verify', 'HEAD'], check=False, capture_output=True
    )
    parent = 'HEAD'
    if head.returncode:
        parent = git('hash-object', '-t', 'tree', '/dev/null').strip()
    diff = ('diff', '--cached', '--ignore-submodules=all', parent)
    staged = lines_added_in(diff)
    added = {path: lines for path, lines in staged.added.items() if lines}
    for path in added:
        copy = Path(into, path)
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_text(git('show', f':{path}'))
    return staged._replace(added=added)


def lines_added_in(diff):
    diff = (*diff, '--find-renames', '--no-ext-diff')
    fields = iter(git(*diff, '--raw', '-z', '--no-abbrev').split('\0')[:-1])
    paths, old_blobs = [], {}
    for meta in fields:
        old_mode, _, old_blob, _, status = meta.split()
        path = next(fields)
        if status[0] in 'RC':
            path = next(fields)
        paths.append(path)
        if old_mode.startswith(':100') and path.endswith(CODE_SUFFIXES):
            old_blobs[path] = old_blob
    patches = FILE_PATCH.split(git(*diff, '--no-color', '-U0'))[1:]
    added, hunks, removed = {}, {}, []
    for path, patch in zip(paths, patches, strict=True):
        added[path], hunks[path] = set(), []
        for hunk in HUNK.finditer(patch):
            old_start, old_count = int(hunk[1]), int(hunk[2] or 1)
            start, count = int(hunk[3]), int(hunk[4] or 1)
            added[path].update(range(start, start + count))
            hunks[path].append((old_start, old_count, start, count))
        if first_hunk := HUNK.search(patch):
            body = patch[first_hunk.start() :].splitlines()
            removed += [f'{line[1:].rstrip()}\n' for line in body if line[:1] == '-']
    return Diff(added, hunks, ''.join(removed), old_blobs)


def is_minified(path):
    try:
        with open(path, 'rb') as file:
            sample = file.read(MINIFIED_SAMPLE)
    except OSError:
        return False
    return any(len(line) > MINIFIED_LINE for line in sample.split(b'\n'))


def find_hits(paths, rules=RULES, cwd=None):
    ast_grep = shutil.which('ast-grep', path=sysconfig.get_path('scripts'))
    for start in range(0, len(paths), PATHS_PER_SCAN):
        batch = paths[start : start + PATHS_PER_SCAN]
        scan = [ast_grep, 'scan', '--inline-rules', rules, '--json=stream', *batch]
        output = subprocess.run(
            scan, check=True, capture_output=True, text=True, cwd=cwd
        )
        for line in output.stdout.split('\n')[:-1]:
            match = json.loads(line)
            first = match['range']['start']['line'] + 1
            last = match['range']['end']['line'] + 1
            source = match['lines'].splitlines()[0].strip()
            text = match['text']
            if match['ruleId'] == 'skipped-test':
                last, text = first, source
            yield Hit(match['file'], first, last, text, match['ruleId'], source)


def is_directive(hit):
    in_header = hit.first_line <= FILE_HEADER_LINES
    if SUPPRESSES_EVERY_RULE.search(hit.text):
        return False
    return bool(
        TOOL_DIRECTIVE.match(hit.text) or in_header and FILE_HEADER.match(hit.text)
    )


def was_moved(hit, removed):
    return all(f'{line.strip()}\n' in removed for line in hit.text.splitlines())


def length(hit):
    return hit.last_line - hit.first_line + 1


def read_blobs(blobs):
    batch = subprocess.run(
        ['git', 'cat-file', '--batch'],
        input=''.join(f'{blob}\n' for blob in blobs).encode(),
        check=True,
        capture_output=True,
    ).stdout
    at = 0
    for _ in blobs:
        header_end = batch.index(b'\n', at)
        size = int(batch[at:header_end].split()[2])
        at = header_end + 1 + size + 1
        yield batch[header_end + 1 : at - 1]


def functions_by_first_line(hits):
    found = {}
    for hit in hits:
        if hit.rule == 'function':
            found.setdefault(hit.source, []).append((hit.path, hit.first_line, hit))
    return {source: sorted(matches) for source, matches in found.items()}


def functions_before(diff):
    with tempfile.TemporaryDirectory() as into:
        for path, content in zip(
            diff.old_blobs, read_blobs(diff.old_blobs.values()), strict=True
        ):
            copy = Path(into, path)
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes(content)
        paths = sorted(p for p in diff.old_blobs if not is_minified(Path(into, p)))
        return functions_by_first_line(
            find_hits(paths, as_yaml(FUNCTION_RULES), cwd=into)
        )


def old_line(line, hunks, end):
    shift = 0
    for old_start, old_count, start, count in hunks:
        if count and start <= line < start + count:
            if end:
                return old_start + max(old_count, 1) - 1
            return old_start
        if (start + count - 1 if count else start) < line:
            shift += old_count - count
    return line + shift


def old_length(hit, diff, before, after):
    old, new = before.get(hit.source, []), after.get(hit.source, [])
    old_here = [match for match in old if match[0] == hit.path]
    new_here = [match for match in new if match[0] == hit.path]
    if old_here and len(old_here) == len(new_here):
        return length(old_here[new_here.index((hit.path, hit.first_line, hit))][2])
    if not old_here and len(old) == len(new) == 1:
        return length(old[0][2])
    if diff.added[hit.path] is EVERY_LINE:
        return 0
    hunks = diff.hunks.get(hit.path, [])
    last = old_line(hit.last_line, hunks, end=True)
    return max(last - old_line(hit.first_line, hunks, end=False) + 1, 0)


def is_new_finding(hit, diff, before, after):
    if hit.rule == 'function':
        return length(hit) > FUNCTION_LIMIT >= old_length(hit, diff, before, after)
    last = hit.first_line if hit.rule == 'nesting' else hit.last_line
    lines = range(hit.first_line, last + 1)
    return (
        not is_directive(hit)
        and not was_moved(hit, diff.removed)
        and any(line in diff.added[hit.path] for line in lines)
    )


def outermost(hits):
    spans = {}
    for hit in hits:
        if hit.rule in NESTED_RULES:
            spans.setdefault((hit.path, hit.rule), []).append(hit)
    return [
        hit
        for hit in hits
        if hit.rule not in NESTED_RULES
        or not any(
            other != hit
            and other.first_line <= hit.first_line <= hit.last_line <= other.last_line
            for other in spans[(hit.path, hit.rule)]
        )
    ]


def describe(hit):
    if hit.rule == 'function':
        return f'{hit.source}  ({length(hit)} lines)'
    return hit.text.splitlines()[0]


def summary(rule, hits):
    if rule == 'comment':
        lines = sum(hit.last_line - hit.first_line + 1 for hit in hits)
        return f'{len(hits)} comments on {lines} lines'
    if rule == 'skipped-test':
        return f'{len(hits)} skipped or focused tests'
    if rule == 'swallowed-error':
        return f'{len(hits)} swallowed errors'
    if rule == 'any-type':
        return f'{len(hits)} any types'
    if rule == 'nesting':
        return f'{len(hits)} blocks nested {NESTING_LIMIT + 1} deep'
    return f'{len(hits)} functions over {FUNCTION_LIMIT} lines'


def report(hits):
    for hit in hits:
        print(f'{hit.path}:{hit.first_line}: {describe(hit)}')
    for rule, advice in FINDINGS.items():
        found = [hit for hit in hits if hit.rule == rule]
        if found:
            print(summary(rule, found))
            print(advice)
    if not hits:
        print(
            'no new comments, skipped tests, long functions, swallowed errors, any types or deep nesting'
        )
    return 1 if hits else 0


def check(args):
    top = Path(git('rev-parse', '--show-toplevel').strip()).resolve()
    inside = [Path(path).resolve() for path in args.paths]
    only = {str(path.relative_to(top)) for path in inside if path.is_relative_to(top)}
    os.chdir(top)
    staged = tempfile.TemporaryDirectory()
    if args.all:
        diff = every_line_of_every_file()
    elif args.staged:
        diff = lines_staged(staged.name)
        os.chdir(staged.name)
    elif base := args.base or default_base():
        diff = lines_added_since(base)
    else:
        print('ks: no default branch found. pass --base <ref>.', file=sys.stderr)
        return 2
    if args.paths:
        diff = diff._replace(
            added={path: n for path, n in diff.added.items() if path in only}
        )
    found = list(find_hits(sorted(p for p in diff.added if not is_minified(p))))
    os.chdir(top)
    staged.cleanup()
    before, after = {}, functions_by_first_line(found)
    if any(hit.rule == 'function' and length(hit) > FUNCTION_LIMIT for hit in found):
        before = functions_before(diff)
    hits = sorted(hit for hit in found if is_new_finding(hit, diff, before, after))
    return report(outermost(hits))


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

import subprocess
import sys
from pathlib import Path

import pytest

KS = Path(sys.executable).parent / 'ks'


def git(repo, *args):
    subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True)


def write(repo, files):
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def commit(repo, files):
    write(repo, files)
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'change')


def ks_check(repo, *args):
    return subprocess.run(
        [KS, 'check', *args], check=False, cwd=repo, capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', '/dev/null')
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'config', 'user.email', 'ks@example.com')
    git(tmp_path, 'config', 'user.name', 'ks')
    return tmp_path


@pytest.fixture
def feature_branch(repo):
    commit(repo, {'old.py': '# old\nx = 1\n', 'old.js': '/**\n * old\n */\n'})
    git(repo, 'checkout', '-b', 'feature')
    return repo


def test_new_comment_fails(feature_branch):
    commit(feature_branch, {'old.py': '# old\nx = 1\ny = 2  # new\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'old.py:3: # new' in result.stdout
    assert '# old' not in result.stdout


def test_old_comment_passes_by_default(feature_branch):
    commit(feature_branch, {'old.py': '# old\nx = 1\ny = 2\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 0, result.stdout


def test_comment_moved_to_a_new_file_passes(feature_branch):
    commit(
        feature_branch,
        {'old.py': 'x = 1\n', 'split.py': 'def f():\n    # old\n    pass\n'},
    )

    result = ks_check(feature_branch)

    assert result.returncode == 0, result.stdout


def test_old_comment_on_a_changed_line_passes(feature_branch):
    commit(feature_branch, {'old.py': '# old\nx = 1\n', 'a.py': 'y = 1  # keep\n'})
    git(feature_branch, 'checkout', '-b', 'edit')
    commit(feature_branch, {'a.py': 'y = 2  # keep\n'})

    result = ks_check(feature_branch, '--base', 'feature')

    assert result.returncode == 0, result.stdout


def test_new_comment_beside_a_moved_one_fails(feature_branch):
    commit(feature_branch, {'old.py': 'x = 1\n', 'split.py': '# old\n# new\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'split.py:2: # new' in result.stdout
    assert '# old' not in result.stdout


def test_new_comment_inside_a_removed_one_fails(feature_branch):
    commit(feature_branch, {'old.py': '# ol\nx = 1\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'old.py:1: # ol' in result.stdout


def test_added_line_that_looks_like_a_diff_header_is_code(feature_branch):
    commit(feature_branch, {'old.py': '++ x\n# old\nx = 1\n# new\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'old.py:4: # new' in result.stdout


def test_file_name_with_spaces(feature_branch):
    commit(feature_branch, {'my file.py': 'x = 1\n# new\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'my file.py:2: # new' in result.stdout


def test_non_utf8_change_does_not_stop_the_check(feature_branch):
    (feature_branch / 'latin.py').write_bytes(b'x = "caf\xe9"\n')
    commit(feature_branch, {'new.py': '# new\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1, result.stderr
    assert 'new.py:1: # new' in result.stdout


def test_all_catches_old_comment(feature_branch):
    result = ks_check(feature_branch, '--all')

    assert result.returncode == 1
    assert 'old.py:1: # old' in result.stdout


def test_line_added_inside_old_block_comment_fails(feature_branch):
    commit(feature_branch, {'old.js': '/**\n * old\n * new\n */\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'old.js:1: /**' in result.stdout


def test_uncommitted_untracked_file_counts_as_new(feature_branch):
    write(feature_branch, {'fresh.py': 'x = 1\n# new\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'fresh.py:2: # new' in result.stdout


def test_renamed_file_keeps_old_comments_passing(feature_branch):
    git(feature_branch, 'config', 'diff.renames', 'false')
    git(feature_branch, 'mv', 'old.py', 'moved.py')
    git(feature_branch, 'commit', '-m', 'move')

    result = ks_check(feature_branch)

    assert result.returncode == 0, result.stdout


def test_base_flag_sets_the_comparison_point(repo):
    commit(repo, {'a.py': 'x = 1\n'})
    commit(repo, {'a.py': 'x = 1\n# new\n'})

    result = ks_check(repo, '--base', 'HEAD~1')

    assert result.returncode == 1
    assert 'a.py:2: # new' in result.stdout


def test_unknown_base_exits_2(feature_branch):
    result = ks_check(feature_branch, '--base', 'nope')

    assert result.returncode == 2
    assert 'nope' in result.stderr


def test_base_with_no_shared_history_says_what_failed(feature_branch):
    git(feature_branch, 'checkout', '--orphan', 'island')
    commit(feature_branch, {'a.py': 'x = 1\n'})

    result = ks_check(feature_branch, '--base', 'main')

    assert result.returncode == 2
    assert 'merge-base' in result.stderr


def test_no_default_branch_asks_for_base(repo):
    git(repo, 'checkout', '-b', 'trunk')
    commit(repo, {'a.py': 'x = 1\n'})

    result = ks_check(repo)

    assert result.returncode == 2
    assert '--base' in result.stderr


def test_all_reports_comments_in_every_language(repo):
    commit(
        repo,
        {
            'a.py': 'x = 1  # why\n',
            'b.ts': 'let b = 1;\n// why\n',
            'c.jsx': 'const c = (\n  <div>\n    {/* why */}\n  </div>\n);\n',
            'd.js': '/**\n * why\n */\nlet d;\n',
        },
    )

    result = ks_check(repo, '--all')

    assert result.returncode == 1
    assert 'a.py:1: # why' in result.stdout
    assert 'b.ts:2: // why' in result.stdout
    assert 'c.jsx:3: /* why */' in result.stdout
    assert 'd.js:1: /**' in result.stdout
    assert 'a name, a test, or the commit message' in result.stdout


def test_docstring_fails(repo):
    commit(repo, {'a.py': 'def f():\n    """Explain f."""\n    return 1\n'})

    result = ks_check(repo, '--all')

    assert result.returncode == 1
    assert 'a.py:2: """Explain f."""' in result.stdout


def test_tool_directives_pass(repo):
    commit(
        repo,
        {
            'a.py': (
                '#!/usr/bin/env python3\n'
                '# -*- coding: utf-8 -*-\n'
                'import os  # noqa: F401\n'
                'a: int = "1"  # type: ignore[assignment]\n'
                'b = 1  # pyright: ignore[reportGeneralTypeIssues]\n'
                'c = 1  # pylint: disable=invalid-name\n'
                '# fmt: off\n'
                'd = [1,2]\n'
                '# fmt: on\n'
                'e = [1,2]  # fmt: skip\n'
                'if a:  # pragma: no cover\n'
                '    pass\n'
                'import re  # NOQA: F401\n'
                'import io  # noqa:F401\n'
                'import sys  # noqa : F401\n'
                'f: int = "1"  # pyright: ignore [reportAssignmentType]\n'
                '# SPDX-License-Identifier: MIT\n'
            ),
            'b.tsx': (
                '// @ts-check\n'
                '/* eslint-env node */\n'
                '/// <reference types="node" />\n'
                '/* eslint-disable no-console */\n'
                '// eslint-disable-next-line no-undef\n'
                'f(); // eslint-disable-line no-undef\n'
                '/* eslint-enable no-console */\n'
                '/* eslint-enable */\n'
                '// @ts-expect-error\n'
                'g();\n'
                '// prettier-ignore\n'
                'const i = [1,2];\n'
                '// biome-ignore lint: generated\n'
                'const j = <div>{/* prettier-ignore */}</div>;\n'
                '//# sourceMappingURL=b.js.map\n'
            ),
        },
    )

    result = ks_check(repo, '--all')

    assert result.returncode == 0, result.stdout


def test_suppression_that_names_no_rule_fails(repo):
    commit(
        repo,
        {
            'a.py': (
                'import os  # noqa\n'
                'import re  # NOQA\n'
                'a: int = "1"  # type: ignore\n'
                'b: int = "1"  # pyright: ignore\n'
                'import io  # noqa:\n'
                'c: int = "1"  # type: ignore[assignment] # noqa\n'
                'import sys  # noqa: E501 # type: ignore\n'
            ),
            'b.ts': (
                '// @ts-nocheck\n'
                '// @ts-ignore\n'
                'h();\n'
                '/* eslint-disable */\n'
                'f(); // eslint-disable-line\n'
                '// eslint-disable-next-line\n'
                'g();\n'
                '// eslint-disable-next-line -- flaky\n'
                'k(); // eslint-disable-line -- flaky\n'
                '/* eslint-disable -- generated */\n'
            ),
        },
    )

    result = ks_check(repo, '--all')

    assert result.returncode == 1
    reported = {line.split(': ')[0] for line in result.stdout.splitlines()}
    for line in (1, 2, 3, 4, 5, 6, 7):
        assert f'a.py:{line}' in reported
    for line in (1, 2, 4, 5, 6, 8, 9, 10):
        assert f'b.ts:{line}' in reported
    assert 'name the rule' in result.stdout


def test_prose_after_line_two_that_mentions_coding_fails(repo):
    commit(repo, {'a.py': 'a = 1\nb = 2\n# coding: style matters here\n'})

    result = ks_check(repo, '--all')

    assert result.returncode == 1
    assert 'a.py:3:' in result.stdout


def test_comment_like_strings_pass(repo):
    commit(
        repo,
        {
            'a.py': 'a = "# no"\nb = f"{a} # no"\nc = """\n# no\n"""\n',
            'b.tsx': (
                'const u = "http://x // no";\n'
                'const r = /\\/\\/ no/;\n'
                'const t = `// no ${u}`;\n'
                'const j = <span>// no</span>;\n'
            ),
        },
    )

    result = ks_check(repo, '--all')

    assert result.returncode == 0, result.stdout
    assert result.stdout == 'no new comments\n'

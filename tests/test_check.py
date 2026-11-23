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
    assert '2 comments on 4 lines' in result.stdout


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
            'c.test.tsx': (
                '// @vitest-environment jsdom\n'
                'test("x", () => {});\n'
            ),
            'd.test.ts': (
                '/** @jest-environment node */\n'
                'test("y", () => {});\n'
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
    assert result.stdout == 'no new comments, skipped tests or long functions\n'


def test_paths_limit_the_check_to_those_files(feature_branch):
    commit(
        feature_branch, {'old.py': '# old\nx = 1  # mine\n', 'other.py': '# theirs\n'}
    )

    result = ks_check(feature_branch, str(feature_branch / 'old.py'))

    assert result.returncode == 1
    assert 'old.py:2: # mine' in result.stdout
    assert 'theirs' not in result.stdout


def test_path_that_leads_outside_the_repo_is_skipped(feature_branch, tmp_path_factory):
    outside = tmp_path_factory.mktemp('outside') / 'shared.py'
    outside.write_text('x = 1  # elsewhere\n')
    (feature_branch / 'link.py').symlink_to(outside)

    result = ks_check(feature_branch, str(feature_branch / 'link.py'))

    assert (result.returncode, result.stderr) == (0, '')


def test_staged_checks_only_what_the_commit_holds(feature_branch):
    write(feature_branch, {'scratch.py': 'x = 1  # untracked\n'})
    write(feature_branch, {'kept.py': 'y = 2  # staged\n'})
    git(feature_branch, 'add', 'kept.py')
    write(feature_branch, {'kept.py': 'y = 2\n'})
    write(feature_branch, {'old.py': '# old\nx = 1  # unstaged\n'})

    result = ks_check(feature_branch, '--staged')

    assert result.returncode == 1
    assert 'kept.py:1: # staged' in result.stdout
    assert 'untracked' not in result.stdout
    assert 'unstaged' not in result.stdout


def test_staged_submodule_does_not_turn_the_check_off(feature_branch, tmp_path_factory):
    other = tmp_path_factory.mktemp('other')
    git(other, 'init', '-b', 'main')
    git(
        other,
        '-c',
        'user.name=k',
        '-c',
        'user.email=k@k',
        'commit',
        '--allow-empty',
        '-m',
        'x',
    )
    git(
        feature_branch,
        '-c',
        'protocol.file.allow=always',
        'submodule',
        'add',
        str(other),
        'sm',
    )
    write(feature_branch, {'q.py': 'x = 1  # sneaks in\n'})
    git(feature_branch, 'add', 'q.py')

    result = ks_check(feature_branch, '--staged')

    assert result.returncode == 1
    assert 'q.py:1: # sneaks in' in result.stdout


def test_staged_first_commit_in_a_sha256_repo(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', '/dev/null')
    git(tmp_path, 'init', '--object-format=sha256', '-b', 'main')
    write(tmp_path, {'app.py': 'x = 1  # first\n'})
    git(tmp_path, 'add', 'app.py')

    result = ks_check(tmp_path, '--staged')

    assert result.returncode == 1
    assert result.stdout.startswith('app.py:1: # first')


def function(name, lines):
    return f'def {name}():\n' + '    x = 1\n' * (lines - 1)


def test_new_skipped_test_fails(feature_branch):
    commit(
        feature_branch,
        {
            'test_a.py': 'import pytest\n\n\n@pytest.mark.skip\ndef test_a():\n    pass\n'
        },
    )

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'test_a.py:4: @pytest.mark.skip' in result.stdout


def test_new_focused_js_test_fails(feature_branch):
    commit(feature_branch, {'a.test.ts': "it.only('a', () => {\n  run()\n})\n"})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert "a.test.ts:1: it.only('a', () => {" in result.stdout


def test_conditional_skip_passes(feature_branch):
    commit(
        feature_branch,
        {
            'test_a.py': (
                '@pytest.mark.skipif(not db, reason="no db")\ndef test_a():\n    pass\n'
            ),
            'a.test.ts': "test.skip(browserName === 'webkit', 'no')\n",
        },
    )

    result = ks_check(feature_branch)

    assert result.returncode == 0, result.stdout


def test_old_skip_with_a_new_line_in_its_test_passes(feature_branch):
    commit(feature_branch, {'a.test.ts': "it.skip('a', () => {\n  run()\n})\n"})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    commit(
        feature_branch, {'a.test.ts': "it.skip('a', () => {\n  run()\n  more()\n})\n"}
    )
    result = ks_check(feature_branch, '--base', 'feature')

    assert result.returncode == 0, result.stdout


def test_new_function_over_the_limit_fails(feature_branch):
    commit(feature_branch, {'a.py': function('short', 60) + function('long', 61)})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'a.py:61: def long():  (61 lines)' in result.stdout
    assert 'short' not in result.stdout


def test_function_that_grows_past_the_limit_fails(feature_branch):
    commit(feature_branch, {'a.py': function('grows', 60)})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    commit(feature_branch, {'a.py': function('grows', 61)})
    result = ks_check(feature_branch, '--base', 'feature')

    assert result.returncode == 1
    assert 'def grows():  (61 lines)' in result.stdout


def test_function_already_over_the_limit_can_still_change(feature_branch):
    commit(feature_branch, {'a.py': function('legacy', 80)})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    commit(
        feature_branch, {'a.py': function('legacy', 81).replace('x = 1', 'y = 2', 30)}
    )
    result = ks_check(feature_branch, '--base', 'feature')

    assert result.returncode == 0, result.stdout


def test_long_arrow_function_fails(feature_branch):
    body = '  run()\n' * 60
    commit(feature_branch, {'page.tsx': f'const Page = () => {{\n{body}}}\n'})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'page.tsx:1: const Page = () => {  (62 lines)' in result.stdout


def test_long_describe_block_of_short_tests_passes(feature_branch):
    tests = "  it('runs', () => {\n    run()\n  })\n" * 25
    commit(feature_branch, {'a.test.ts': f"describe('a', () => {{\n{tests}}})\n"})

    result = ks_check(feature_branch)

    assert result.returncode == 0, result.stdout


def test_long_function_inside_a_long_one_is_reported_once(feature_branch):
    inner = '    .map((row) => {\n' + '      run()\n' * 61 + '    })\n'
    page = 'function Page() {\n  return rows\n' + inner + '}\n'
    commit(feature_branch, {'page.tsx': page})

    result = ks_check(feature_branch)

    assert result.returncode == 1
    assert 'page.tsx:1: function Page() {' in result.stdout
    assert '.map' not in result.stdout


def test_unicode_line_break_inside_code_does_not_crash(repo):
    commit(repo, {'lib.min.js': 'function f() { return "a\x85b" }\n'})

    result = ks_check(repo, '--all')

    assert (result.returncode, result.stderr) == (0, '')


def test_minified_file_is_skipped(repo):
    bundle = 'function a(){/* keep */return 1}' * 400
    commit(repo, {'lib.min.js': bundle + '\n', 'app.py': 'x = 1  # mine\n'})

    result = ks_check(repo, '--all')

    assert 'app.py:1: # mine' in result.stdout
    assert 'lib.min.js' not in result.stdout


def test_long_function_moved_to_a_new_file_with_one_change_passes(feature_branch):
    commit(feature_branch, {'big.py': function('legacy', 80) + function('rest', 5)})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    moved = function('legacy', 80).replace('x = 1', 'x = 2', 1)
    commit(feature_branch, {'big.py': function('rest', 5), 'legacy.py': moved})
    result = ks_check(feature_branch, '--base', 'feature')

    assert result.returncode == 0, result.stdout


def test_edit_from_the_decorator_into_a_long_function_passes(feature_branch):
    old = '@cache\n' + function('legacy', 80)
    commit(feature_branch, {'a.py': old})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    new = '@cache(1)\n' + function('legacy2', 80).replace('x = 1', 'y = 2', 40)
    commit(feature_branch, {'a.py': new})
    result = ks_check(feature_branch, '--base', 'feature')

    assert result.returncode == 0, result.stdout


def test_growth_hidden_by_a_deleted_neighbour_fails(feature_branch):
    commit(feature_branch, {'a.py': function('grows', 55) + function('gone', 10)})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    commit(feature_branch, {'a.py': function('grows', 62)})
    result = ks_check(feature_branch, '--base', 'feature')

    assert 'def grows():  (62 lines)' in result.stdout


def numbered(name, lines, start=0):
    body = ''.join(f'    {name}{n} = {n}\n' for n in range(start, start + lines - 1))
    return f'def {name}():\n{body}'


def test_renamed_function_that_grows_beside_a_changed_neighbour(feature_branch):
    commit(feature_branch, {'a.py': numbered('a', 50) + numbered('b', 80)})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    renamed = numbered('a', 61).replace('def a():', 'def a2():')
    changed = numbered('b', 10, start=100) + numbered('b', 70, start=10)[9:]
    commit(feature_branch, {'a.py': renamed + changed})
    result = ks_check(feature_branch, '--base', 'feature')

    assert 'def a2():  (61 lines)' in result.stdout
    assert 'def b()' not in result.stdout


def test_unconditional_skips_in_other_forms_fail(feature_branch):
    commit(
        feature_branch,
        {
            'a.spec.ts': "test('a', () => {\n  test.skip()\n})\ntest.fixme('b', () => {})\n",
            'test_a.py': (
                'from unittest import skip\n\n\n@skip("later")\ndef test_a():\n'
                '    pass\n\n\ndef test_b():\n    pytest.skip("later")\n'
            ),
        },
    )

    result = ks_check(feature_branch)

    assert 'a.spec.ts:2: test.skip()' in result.stdout
    assert "a.spec.ts:4: test.fixme('b', () => {})" in result.stdout
    assert 'test_a.py:4: @skip("later")' in result.stdout
    assert 'test_a.py:10: pytest.skip("later")' in result.stdout


def test_skip_inside_a_condition_passes(feature_branch):
    commit(
        feature_branch,
        {'test_a.py': 'def test_a():\n    if not db:\n        pytest.skip("no db")\n'},
    )

    result = ks_check(feature_branch)

    assert result.returncode == 0, result.stdout


def test_renamed_function_below_a_grown_neighbour(feature_branch):
    commit(feature_branch, {'a.py': numbered('b', 80) + numbered('a', 50)})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    grown = numbered('b', 80) + ''.join(f'    c{n} = {n}\n' for n in range(30))
    head, tail = numbered('a', 50).split('    a25 = 25\n')
    middle = ''.join(f'    d{n} = {n}\n' for n in range(11))
    renamed = (head + middle + '    a25 = 25\n' + tail).replace('def a():', 'def a2():')
    commit(feature_branch, {'a.py': grown + renamed})
    result = ks_check(feature_branch, '--base', 'feature')

    assert 'def a2():  (61 lines)' in result.stdout


def test_new_long_function_with_the_same_first_line_as_an_old_one_fails(feature_branch):
    effect = 'useEffect(() => {\n' + '  run()\n' * 78 + '})\n'
    commit(feature_branch, {'page.tsx': effect})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    second = 'useEffect(() => {\n' + '  load()\n' * 70 + '})\n'
    commit(feature_branch, {'page.tsx': effect + second})
    result = ks_check(feature_branch, '--base', 'feature')

    assert 'page.tsx:81: useEffect(() => {  (72 lines)' in result.stdout
    assert 'page.tsx:1:' not in result.stdout


def test_long_function_in_an_untracked_file_fails(feature_branch):
    write(feature_branch, {'draft.py': function('draft', 61)})

    result = ks_check(feature_branch)

    assert 'draft.py:1: def draft():  (61 lines)' in result.stdout


def test_renamed_long_function_with_a_rewritten_end_passes(feature_branch):
    commit(feature_branch, {'a.py': numbered('a', 64)})
    git(feature_branch, 'checkout', '-q', '-b', 'later')

    head = numbered('a', 59).replace('def a():', 'def a2():')
    commit(feature_branch, {'a.py': head + numbered('z', 6)[9:]})
    result = ks_check(feature_branch, '--base', 'feature')

    assert result.returncode == 0, result.stdout


def test_submodule_bump_beside_a_long_function_does_not_crash(
    feature_branch, tmp_path_factory
):
    other = tmp_path_factory.mktemp('other')
    git(other, 'init', '-b', 'main')
    git(
        other,
        '-c',
        'user.name=k',
        '-c',
        'user.email=k@k',
        'commit',
        '--allow-empty',
        '-m',
        'x',
    )
    git(
        feature_branch,
        '-c',
        'protocol.file.allow=always',
        'submodule',
        'add',
        str(other),
        'dep',
    )
    git(feature_branch, 'commit', '-m', 'dep')
    git(feature_branch, 'checkout', '-q', '-b', 'later')
    git(
        other,
        '-c',
        'user.name=k',
        '-c',
        'user.email=k@k',
        'commit',
        '--allow-empty',
        '-m',
        'y',
    )
    git(feature_branch / 'dep', 'pull', '-q')
    commit(feature_branch, {'a.py': function('grows', 70)})

    result = ks_check(feature_branch, '--base', 'feature')

    assert (result.returncode, result.stderr) == (1, '')
    assert 'def grows():  (70 lines)' in result.stdout


def test_skipped_each_table_fails(feature_branch):
    commit(feature_branch, {'a.test.ts': "it.skip.each([1, 2])('t %i', (n) => {})\n"})

    result = ks_check(feature_branch)

    assert 'a.test.ts:1: it.skip.each' in result.stdout

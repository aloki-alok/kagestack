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
        [KS, 'check', *args], cwd=repo, capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', '/dev/null')
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'config', 'user.email', 'ks@example.com')
    git(tmp_path, 'config', 'user.name', 'ks')
    return tmp_path


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
    assert result.stdout == ''

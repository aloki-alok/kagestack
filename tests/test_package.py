import subprocess
import sys
from pathlib import Path

KS = Path(sys.executable).parent / 'ks'
SKILLS = Path(__file__).parent.parent / 'src/ks/skills'


def ks(repo, *args):
    return subprocess.run(
        [KS, 'package', *args], check=False, cwd=repo, capture_output=True, text=True
    )


def git_repo(path):
    subprocess.run(['git', 'init', '-q', '-b', 'main', path], check=True)
    return path


def test_every_skill_lands_where_codex_and_opencode_look(tmp_path):
    repo = git_repo(tmp_path)

    result = ks(repo)

    assert result.returncode == 0, result.stderr
    packaged = sorted(p.name for p in (repo / '.agents/skills').iterdir())
    assert packaged == sorted(f'kagestack-{p.name}' for p in SKILLS.iterdir())


def test_skill_names_its_folder_and_reads_principles_beside_it(tmp_path):
    repo = git_repo(tmp_path)

    ks(repo)

    feature = repo / '.agents/skills/kagestack-feature'
    text = (feature / 'SKILL.md').read_text()
    assert 'name: kagestack-feature\n' in text
    assert 'Read `principles.md` in this skill folder' in text
    assert '${CLAUDE_PLUGIN_ROOT}' not in text
    assert (feature / 'principles.md').exists()
    assert not (repo / '.agents/skills/kagestack-pr/principles.md').exists()


def test_check_passes_when_current_and_names_a_stale_file(tmp_path):
    repo = git_repo(tmp_path)
    ks(repo)
    assert ks(repo, '--check').returncode == 0

    (repo / '.agents/skills/kagestack-pr/SKILL.md').write_text('old\n')
    result = ks(repo, '--check')

    assert result.returncode == 1
    assert 'kagestack-pr/SKILL.md' in result.stdout


def test_check_fails_when_nothing_is_packaged(tmp_path):
    result = ks(git_repo(tmp_path), '--check')

    assert result.returncode == 1


def test_rerun_removes_a_skill_that_no_longer_ships(tmp_path):
    repo = git_repo(tmp_path)
    gone = repo / '.agents/skills/kagestack-gone'
    gone.mkdir(parents=True)
    (gone / 'SKILL.md').write_text('old\n')
    mine = repo / '.agents/skills/my-skill'
    mine.mkdir()

    ks(repo)

    assert not gone.exists()
    assert mine.exists()


def test_stray_file_and_link_are_replaced_and_flagged(tmp_path):
    repo = git_repo(tmp_path)
    out = repo / '.agents/skills'
    out.mkdir(parents=True)
    (out / 'kagestack-x').write_text('')
    (out / 'kagestack-link').symlink_to(tmp_path)

    check = ks(repo, '--check')
    result = ks(repo)

    assert 'kagestack-x' in check.stdout
    assert 'kagestack-link' in check.stdout
    assert result.returncode == 0, result.stderr
    assert not (out / 'kagestack-x').exists()
    assert not (out / 'kagestack-link').is_symlink()


def test_check_flags_an_empty_folder_and_principles_drift(tmp_path):
    repo = git_repo(tmp_path)
    ks(repo)
    (repo / '.agents/skills/kagestack-empty').mkdir()
    (repo / '.agents/skills/kagestack-feature/principles.md').write_text('old\n')

    result = ks(repo, '--check')

    assert result.returncode == 1
    assert 'kagestack-empty' in result.stdout
    assert 'kagestack-feature/principles.md' in result.stdout

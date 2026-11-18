import shutil
from pathlib import Path

from ks.setup import repo_root

BUNDLE = Path(__file__).parent
OUT = '.agents/skills'
PREFIX = 'kagestack-'
PLUGIN_PRINCIPLES = '`${CLAUDE_PLUGIN_ROOT}/src/ks/principles.md`'
LOCAL_PRINCIPLES = '`principles.md` in this skill folder'


def expected():
    files = {}
    for skill in sorted(p for p in (BUNDLE / 'skills').iterdir() if p.is_dir()):
        folder = f'{PREFIX}{skill.name}'
        text = (skill / 'SKILL.md').read_text()
        text = text.replace(f'name: {skill.name}\n', f'name: {folder}\n', 1)
        text = text.replace(PLUGIN_PRINCIPLES, LOCAL_PRINCIPLES)
        files[f'{folder}/SKILL.md'] = text
        if LOCAL_PRINCIPLES in text:
            files[f'{folder}/principles.md'] = (BUNDLE / 'principles.md').read_text()
    return files


def stale_files(out):
    want = expected()
    have = {
        str(path.relative_to(out)): path.read_text()
        for path in out.glob(f'{PREFIX}*/**/*')
        if path.is_file()
    }
    return sorted(p for p in want.keys() | have.keys() if want.get(p) != have.get(p))


def package(args):
    out = repo_root() / OUT
    want = expected()
    if args.check:
        stale = stale_files(out)
        for path in stale:
            print(f'stale {OUT}/{path}')
        if stale:
            print('run ks package (・_・;)')
            return 1
        print(f'{OUT} is current ✧(◕‿◕)✧')
        return 0
    for folder in out.glob(f'{PREFIX}*'):
        shutil.rmtree(folder)
    for path, text in want.items():
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_text(text)
    print(f'wrote {len(want)} files to {OUT} for codex and opencode')
    return 0

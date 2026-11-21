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
        for agent in sorted((BUNDLE / 'agents').glob('*.md')):
            plugin_path = f'`${{CLAUDE_PLUGIN_ROOT}}/src/ks/agents/{agent.name}`'
            if plugin_path in text:
                text = text.replace(plugin_path, f'`{agent.name}` in this skill folder')
                files[f'{folder}/{agent.name}'] = agent.read_text()
        files[f'{folder}/SKILL.md'] = text
        if LOCAL_PRINCIPLES in text:
            files[f'{folder}/principles.md'] = (BUNDLE / 'principles.md').read_text()
    return files


def is_folder(entry):
    return entry.is_dir() and not entry.is_symlink()


def stale_files(out):
    want = expected()
    folders = {path.split('/')[0] for path in want}
    entries = sorted(out.glob(f'{PREFIX}*'))
    stale = {e.name for e in entries if e.name not in folders or not is_folder(e)}
    have = {
        str(path.relative_to(out)): path.read_text(errors='replace')
        for entry in entries
        if is_folder(entry)
        for path in entry.rglob('*')
        if path.is_file()
    }
    stale.update(p for p in want.keys() | have.keys() if want.get(p) != have.get(p))
    return sorted(stale)


def package(args):
    out = repo_root() / OUT
    want = expected()
    if args.check:
        stale = stale_files(out)
        for path in stale:
            print(f'stale {OUT}/{path}')
        if stale:
            print(f'{len(stale)} stale. run ks package')
            return 1
        print(f'{OUT} is current')
        return 0
    for entry in out.glob(f'{PREFIX}*'):
        if is_folder(entry):
            shutil.rmtree(entry)
        else:
            entry.unlink()
    for path, text in want.items():
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_text(text)
    folders = {path.split('/')[0] for path in want}
    print(f'wrote {len(folders)} playbooks to {OUT}')
    return 0

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent
KS = Path(sys.executable).parent / 'ks'


def test_one_version_everywhere():
    plugin = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
    printed = subprocess.run(
        [KS, '--version'], check=True, capture_output=True, text=True
    )

    assert project['version'] == plugin['version']
    assert printed.stdout.strip() == f'ks {plugin["version"]}'


def test_worker_hook_serves_worker_rules():
    served = json.loads((ROOT / 'hooks/worker.json').read_text())

    context = served['hookSpecificOutput']['additionalContext']
    assert context == (ROOT / 'hooks/worker.md').read_text()


def test_session_hook_serves_the_playbook_routes():
    hooks = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']
    served = json.loads((ROOT / 'hooks/session.json').read_text())

    command = hooks['SessionStart'][0]['hooks'][0]['command']
    assert command == 'cat "${CLAUDE_PLUGIN_ROOT}/hooks/session.json"'
    assert served['hookSpecificOutput']['hookEventName'] == 'SessionStart'
    context = served['hookSpecificOutput']['additionalContext']
    assert context == (ROOT / 'hooks/session.md').read_text()
    skills = {skill.name for skill in (ROOT / 'src/ks/skills').iterdir()}
    assert set(re.findall(r'`kagestack:([\w-]+)`', context)) == skills


def test_every_skill_is_named_after_its_folder():
    for skill in (ROOT / 'src/ks/skills').iterdir():
        assert f'\nname: {skill.name}\n' in (skill / 'SKILL.md').read_text()


def test_every_agent_a_playbook_starts_exists_under_its_name():
    agents = {
        path.stem: path.read_text() for path in (ROOT / 'src/ks/agents').glob('*.md')
    }
    playbooks = ''.join(
        path.read_text() for path in (ROOT / 'src/ks/skills').glob('*/SKILL.md')
    )

    started = set(re.findall(r'`kagestack:([\w-]+)` agent', playbooks))
    assert started
    assert started <= agents.keys()
    for name, text in agents.items():
        assert text.startswith(f'---\nname: {name}\n')


def test_stop_hooks_run_the_review_and_decide_scripts():
    hooks = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']

    commands = [hook['command'] for hook in hooks['Stop'][0]['hooks']]
    assert commands == [
        'sh "${CLAUDE_PLUGIN_ROOT}/hooks/review.sh"',
        'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/decide.py"',
    ]
    assert (ROOT / 'hooks/review.sh').is_file()
    assert (ROOT / 'hooks/decide.py').is_file()

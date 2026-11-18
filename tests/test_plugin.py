import json
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

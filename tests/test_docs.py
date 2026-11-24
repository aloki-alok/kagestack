import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / 'docs/concepts'


def test_the_current_release_has_a_changes_entry():
    version = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())['version']

    entries = re.findall(
        r'^## (\d+\.\d+\.\d+) ·', (DOCS / 'changes.md').read_text(), re.MULTILINE
    )

    assert version in entries


def test_every_page_opens_with_a_diagram_then_a_title():
    for page in DOCS.glob('*.md'):
        text = page.read_text()
        assert text.startswith('```mermaid\n'), page.name
        assert re.search(r'^```\n+# .+', text, re.MULTILINE), page.name

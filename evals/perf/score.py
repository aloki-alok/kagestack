import re
import statistics
import subprocess
import tempfile
from pathlib import Path

SAME = """
import importlib.util, sys
from db import connect
spec = importlib.util.spec_from_file_location('old_page', sys.argv[1])
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
from page import campaigns_page
conn = connect(campaigns=200, contacts_each=7)
print(old.campaigns_page(conn) == campaigns_page(conn))
"""


def seconds(run):
    out = subprocess.run(
        ['python3', 'serve.py'], cwd=run.repo, capture_output=True, text=True, check=False
    ).stdout
    found = re.search(r'in ([\d.]+)s', out)
    return float(found[1]) if found else float('inf')


def score(run):
    root = run.git('rev-list', '--max-parents=0', 'HEAD').strip()
    with tempfile.TemporaryDirectory() as tmp:
        old_page = Path(tmp) / 'old_page.py'
        old_page.write_text(run.git('show', f'{root}:page.py'))
        same = subprocess.run(
            ['python3', '-c', SAME, old_page],
            cwd=run.repo,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    median = statistics.median(seconds(run) for _ in range(3))
    reply = run.reply.lower()
    return {
        'median now (was ~1.2s)': f'{median:.3f}s',
        'same output as before': same == 'True',
        'reply gives a median': 'median' in reply,
        'alternated old and new runs': 'alternat' in reply or 'interleav' in reply,
        'counted errors': bool(re.search(r'\b(0|no|zero) errors?\b', reply)),
    }

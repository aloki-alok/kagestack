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

TIME = """
import time
from db import connect
from page import campaigns_page
conn = connect(campaigns=3500, contacts_each=40)
start = time.perf_counter()
campaigns_page(conn)
print(time.perf_counter() - start)
"""


def seconds(cwd):
    out = subprocess.run(
        ['python3', '-c', TIME], cwd=cwd, capture_output=True, text=True, check=False
    ).stdout
    return float(out) if out.strip() else float('inf')


def score(run):
    with tempfile.TemporaryDirectory() as tmp:
        old_page = Path(tmp) / 'old_page.py'
        old_page.write_text(run.git('show', f'{run.start}:page.py'))
        same = subprocess.run(
            ['python3', '-c', SAME, old_page],
            cwd=run.repo,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    with run.tree(run.start) as old:
        pairs = [(seconds(old), seconds(run.repo)) for _ in range(3)]
    before = statistics.median(old for old, _ in pairs)
    after = statistics.median(new for _, new in pairs)
    return {
        'same output as before': same == 'True',
        'tests pass': run.unittest().returncode == 0,
        'seconds after': after,
        'times faster': before / after,
    }

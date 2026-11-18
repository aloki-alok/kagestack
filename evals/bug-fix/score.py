import subprocess

CHECK = """
from datetime import date
from export import export_csv
from summary import total_minutes
nov = {date(2026, 11, d): d for d in (1, 2, 3)}
print('2026-11-03' in export_csv(nov, date(2026, 11, 1), date(2026, 11, 3)))
print(total_minutes(nov, date(2026, 11, 1), date(2026, 11, 3)) == 6)
"""


def score(run):
    check = subprocess.run(
        ['python3', '-c', CHECK],
        cwd=run.repo,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    return {
        'export has nov 3': check[:1] == ['True'],
        'summary also fixed (shared cause)': check[1:2] == ['True'],
        'tests pass': run.unittest().returncode == 0,
        'a test fails on the old code': 'failures=' in run.tests_on(run.start).stderr,
    }

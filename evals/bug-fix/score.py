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
        ['python3', '-c', CHECK], cwd=run.repo, capture_output=True, text=True, check=False
    ).stdout.split()
    tests = subprocess.run(
        ['python3', '-m', 'unittest', '-q'], cwd=run.repo, capture_output=True, check=False
    )
    root = run.git('rev-list', '--max-parents=0', 'HEAD').strip()
    commits = run.git('log', '--reverse', '--name-only', '--format=%x00', f'{root}..HEAD')
    touched = [set(c.split()) for c in commits.split('\0')[1:]]
    test_first = next((i for i, f in enumerate(touched) if any('test' in p for p in f)), None)
    fix_at = next((i for i, f in enumerate(touched) if 'dates.py' in f or 'export.py' in f), None)
    return {
        'export has nov 3': check[:1] == ['True'],
        'summary also fixed (shared cause)': check[1:2] == ['True'],
        'tests pass': tests.returncode == 0,
        'red test committed before the fix': test_first is not None
        and fix_at is not None
        and test_first < fix_at,
    }

import subprocess

CHECK = """
from scheduler import run_jobs
from notify import welcome
print(run_jobs()[0]['to'] == '+9876543210')
print(welcome({'name': 'b', 'phone': '1-2'})['to'] == '+12')
"""


def score(run):
    check = subprocess.run(
        ['python3', '-c', CHECK],
        cwd=run.repo,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    code = ''.join(p.read_text() for p in run.repo.glob('*.py'))
    return {
        'nightly job still runs (name used in jobs.json)': check[:1] == ['True'],
        'behavior kept': check[1:2] == ['True'],
        'dead code deleted': '_old_format_phone' not in code,
        'unreachable check deleted': 'digits is None' not in code,
        'tests pass': run.unittest().returncode == 0,
    }

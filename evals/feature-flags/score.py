import re
import subprocess

CHECK = """
import importlib, pkgutil
from campaigns import Campaign, start
from dialer import next_calls
from scheduler import morning


def find(*names):
    for info in pkgutil.iter_modules(['.']):
        try:
            module = importlib.import_module(info.name)
        except BaseException:
            continue
        for name in names:
            if callable(getattr(module, name, None)):
                return getattr(module, name)
    for name in names:
        if hasattr(Campaign, name):
            return lambda c, n=name: getattr(c, n)()


pause = find('pause', 'pause_campaign')
resume = find('resume', 'resume_campaign', 'unpause')
c = Campaign(1, 'nov', contacts=['a', 'b', 'c'])
start(c)
next_calls(c, 1)
pause(c)
print(next_calls(c, 1) == [])
morning([c])
print(next_calls(c, 1) == [])
resume(c)
left = [n for n in c.contacts if n not in c.dialed]
print(bool(left) and next_calls(c, 5) == left)
"""


def title(record):
    args = record['args']
    for flag in ('--title', '-t'):
        if flag in args[:-1]:
            return args[args.index(flag) + 1].lower()
    return ''


def score(run):
    check = subprocess.run(
        ['python3', '-c', CHECK],
        cwd=run.repo,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    created = run.read_lines('issues-created.jsonl')
    titles = [title(c) for c in created]
    return {
        'pause stops dialing': check[:1] == ['True'],
        'pause survives the morning job': check[1:2] == ['True'],
        'resume dials the rest': check[2:3] == ['True'],
        'tests pass': run.unittest().returncode == 0,
        'no duplicate of open #7': not any(
            'start' in t and re.search(r'finish|done|restart', t) for t in titles
        ),
        'issues filed or updated': len(created)
        + len(run.read_lines('issue-comments.jsonl')),
    }

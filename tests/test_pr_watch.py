import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

KS = Path(sys.executable).parent / 'ks'

FAKE_GH = """#!{python}
import json, sys
from pathlib import Path
here = Path(__file__).parent
args = sys.argv[1:]
polls = here / 'polls'
count = int(polls.read_text()) if polls.exists() else 0
if args[:2] == ['pr', 'view']:
    count += 1
    polls.write_text(str(count))
states = json.loads((here / 'states.json').read_text())
state = states[min(count - 1, len(states) - 1)]
if args[:2] == ['pr', 'view']:
    print(json.dumps(state['pr']))
elif args[:2] == ['pr', 'checks']:
    print(json.dumps(state['checks']))
    sys.exit(1 if any(c['bucket'] == 'fail' for c in state['checks']) else 0)
elif args[:2] == ['api', 'graphql']:
    threads = [
        {{'id': t['thread'], 'isResolved': t.get('resolved', False),
          'comments': {{'nodes': [{{'databaseId': t['id'], 'body': t['body'],
                                   'author': {{'login': t['user']}},
                                   'path': t['path'], 'line': t['line']}}]}}}}
        for t in state.get('threads', [])
    ]
    pull = {{'reviewThreads': {{'nodes': threads}}}}
    print(json.dumps({{'data': {{'repository': {{'pullRequest': pull}}}}}}))
elif args[:2] == ['run', 'view']:
    with (here / 'logs.jsonl').open('a') as logs:
        logs.write(json.dumps(args) + '\\n')
    print(state['log'])
else:
    print('unexpected: ' + ' '.join(args), file=sys.stderr)
    sys.exit(4)
"""

RUN = 'https://github.com/acme/shop/actions/runs/4242/job/7'


def pr(state='OPEN', merge='BLOCKED'):
    return {
        'number': 12,
        'url': 'https://github.com/acme/shop/pull/12',
        'state': state,
        'mergeStateStatus': merge,
        'baseRefName': 'main',
        'headRefName': 'free-shipping',
    }


def check(bucket, name='test'):
    return {'name': name, 'bucket': bucket, 'link': RUN}


def thread(number, body='this crashes on zero'):
    return {
        'thread': f'T{number}',
        'id': number,
        'user': 'reviewer',
        'path': 'shipping.py',
        'line': 7,
        'body': body,
    }


class FakeGithub:
    def __init__(self, root):
        self.bin = root / 'bin'
        self.bin.mkdir()
        gh = self.bin / 'gh'
        gh.write_text(FAKE_GH.format(python=sys.executable))
        gh.chmod(0o755)
        self.repo = root / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=self.repo, check=True)

    def serve(self, *states):
        (self.bin / 'states.json').write_text(json.dumps(list(states)))
        (self.bin / 'polls').unlink(missing_ok=True)

    def watch(self, *args):
        env = {**os.environ, 'PATH': f'{self.bin}{os.pathsep}{os.environ["PATH"]}'}
        return subprocess.run(
            [KS, 'pr-watch', '12', '--interval', '0', *args],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )


@pytest.fixture
def github(tmp_path):
    return FakeGithub(tmp_path)


def polls(github):
    return int((github.bin / 'polls').read_text())


def test_failed_check_prints_its_name_and_the_end_of_its_log(github):
    log = '\n'.join(
        f'test\tRun tests\t2026-11-28T10:00:{n:02d}.0000000Z line {n}'
        for n in range(80)
    )
    github.serve(
        {'pr': pr(), 'checks': [check('pass', 'lint'), check('fail')], 'log': log}
    )

    result = github.watch()

    assert result.returncode == 1
    assert result.stdout.splitlines()[0] == 'failed: test'
    assert 'line 79' in result.stdout
    assert 'line 20\n' not in result.stdout
    assert '2026-11-28T10' not in result.stdout
    assert len(result.stdout.splitlines()) < 45


def test_waits_through_pending_checks_until_they_pass(github):
    pending = {'pr': pr(), 'checks': [check('pending')]}
    green = {'pr': pr(merge='CLEAN'), 'checks': [check('pass')]}
    github.serve(pending, pending, green)

    result = github.watch()

    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == 'checks green, ready to merge'
    assert polls(github) == 3


def test_green_checks_with_a_review_still_required(github):
    github.serve({'pr': pr(merge='BLOCKED'), 'checks': [check('pass')]})

    result = github.watch()

    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == 'checks green, waiting on review'


def test_conflict_is_reported_before_failed_checks(github):
    github.serve({'pr': pr(merge='DIRTY'), 'checks': [check('fail')], 'log': 'boom'})

    result = github.watch()

    assert result.returncode == 1
    assert result.stdout.splitlines()[0] == 'conflict: rebase free-shipping on main'


def test_merged_pull_request_ends_the_watch(github):
    github.serve({'pr': pr(state='MERGED'), 'checks': [check('pending')]})

    result = github.watch()

    assert result.returncode == 0
    assert (
        result.stdout.splitlines()[0] == 'merged: https://github.com/acme/shop/pull/12'
    )


def test_new_review_thread_is_reported_once(github):
    state = {
        'pr': pr(),
        'checks': [check('pending')],
        'threads': [thread(901), {**thread(902), 'resolved': True}],
    }
    github.serve(state)

    first = github.watch()
    github.serve(state)
    second = github.watch('--timeout', '0')

    assert first.returncode == 1
    assert first.stdout.splitlines()[0] == 'new review comments: 1'
    assert (
        'reviewer on shipping.py:7 (comment 901): this crashes on zero' in first.stdout
    )
    assert '902' not in first.stdout
    assert second.returncode == 3
    assert second.stdout.splitlines()[0] == 'still waiting on: test'


def test_reply_in_a_seen_thread_is_reported_again(github):
    github.serve({'pr': pr(), 'checks': [check('pending')], 'threads': [thread(901)]})
    github.watch()
    reply = {**thread(901), 'id': 905, 'body': 'still crashes'}
    github.serve({'pr': pr(), 'checks': [check('pending')], 'threads': [reply]})

    result = github.watch('--timeout', '0')

    assert result.returncode == 1
    assert '(comment 905): still crashes' in result.stdout


def test_one_log_read_per_failed_run(github):
    github.serve(
        {
            'pr': pr(),
            'checks': [check('fail', 'test'), check('fail', 'types')],
            'log': 'x',
        }
    )

    result = github.watch()

    logs = (github.bin / 'logs.jsonl').read_text().splitlines()
    assert result.stdout.splitlines()[0] == 'failed: test, types'
    assert len(logs) == 1
    assert json.loads(logs[0])[:4] == ['run', 'view', '4242', '--log-failed']

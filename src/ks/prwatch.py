import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

SUMMARY = 'wait for the next event on a pull request, then print what needs doing'
THREADS = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id isResolved
          comments(last: 1) { nodes { databaseId body author { login } path line } }
        }
      }
    }
  }
}
"""
FIELDS = 'number,url,state,mergeStateStatus,baseRefName,headRefName'
DONE_BUCKETS = ('pass', 'skipping')
BROKEN_BUCKETS = ('fail', 'cancel')
RUN_ID = re.compile(r'/actions/runs/(\d+)')
LOG_PREFIX = re.compile(r'^[^\t]*\t[^\t]*\t(\d{4}-\d\d-\d\dT[\d:.]+Z )?')
NO_CHECKS_YET = 'no checks reported'
LOG_LINES = 30
FIRST_ERROR_LINES = 20
SUMMARY_LINES = 8
FAILURE = re.compile(
    r'(^|\s)(not ok\b|FAIL\b|FAILED\b|--- FAIL|Traceback|panicked'
    r'|\w*Error\b|error[:\[]|✕|✗|●)'
)
COMMENT_CHARACTERS = 300
READY, NEEDS_WORK, ERROR, STILL_WAITING = 0, 1, 2, 3


class Thread(NamedTuple):
    id: str
    comment: int
    line: str


class Snapshot(NamedTuple):
    pull: dict
    checks: list
    threads: list


def gh(*args):
    found = subprocess.run(['gh', *args], capture_output=True, text=True, check=False)
    if found.returncode and not found.stdout.strip():
        raise subprocess.CalledProcessError(
            found.returncode, ['gh', *args], found.stdout, found.stderr
        )
    return found.stdout


def thread_line(node):
    last = node['comments']['nodes'][-1]
    body = ' '.join(last['body'].split())[:COMMENT_CHARACTERS]
    where = f'{last["path"]}:{last["line"]}'
    line = (
        f'{last["author"]["login"]} on {where} (comment {last["databaseId"]}): {body}'
    )
    return Thread(node['id'], last['databaseId'], line)


def open_threads(pull):
    owner, name = pull['url'].split('/')[3:5]
    found = json.loads(
        gh(
            'api',
            'graphql',
            '-f',
            f'query={THREADS}',
            '-F',
            f'owner={owner}',
            '-F',
            f'name={name}',
            '-F',
            f'number={pull["number"]}',
        )
    )
    nodes = found['data']['repository']['pullRequest']['reviewThreads']['nodes']
    return [thread_line(node) for node in nodes if not node['isResolved']]


def checks_of(pull):
    try:
        found = gh('pr', 'checks', str(pull['number']), '--json', 'name,bucket,link')
    except subprocess.CalledProcessError as failure:
        if NO_CHECKS_YET in failure.stderr:
            return []
        raise
    return json.loads(found)


def snapshot(number):
    pull = json.loads(gh('pr', 'view', *number, '--json', FIELDS))
    return Snapshot(pull, checks_of(pull), open_threads(pull))


def digest(log):
    first = next((n for n, line in enumerate(log) if FAILURE.search(line)), None)
    if first is None:
        return log[-LOG_LINES:]
    block = log[first : first + FIRST_ERROR_LINES]
    summary = log[max(first + FIRST_ERROR_LINES, len(log) - SUMMARY_LINES) :]
    return [*block, '...', *summary] if summary else block


def failed_logs(checks):
    lines = []
    for run in dict.fromkeys(
        found[1] for check in checks if (found := RUN_ID.search(check['link'] or ''))
    ):
        log = [
            LOG_PREFIX.sub('', line)
            for line in gh('run', 'view', run, '--log-failed').splitlines()
        ]
        lines += digest(log)
    links = [
        check['link'] for check in checks if not RUN_ID.search(check['link'] or '')
    ]
    return lines + [link for link in links if link]


def event(found, seen):
    pull = found.pull
    if pull['state'] != 'OPEN':
        return READY, [f'{pull["state"].lower()}: {pull["url"]}']
    if pull['mergeStateStatus'] == 'DIRTY':
        return NEEDS_WORK, [
            f'conflict: rebase {pull["headRefName"]} on {pull["baseRefName"]}'
        ]
    new = [thread for thread in found.threads if seen.get(thread.id) != thread.comment]
    if new:
        return NEEDS_WORK, [
            f'new review comments: {len(new)}',
            *(thread.line for thread in new),
        ]
    broken = [check for check in found.checks if check['bucket'] in BROKEN_BUCKETS]
    if broken:
        names = ', '.join(check['name'] for check in broken)
        return NEEDS_WORK, [f'failed: {names}', *failed_logs(broken)]
    if found.checks and all(c['bucket'] in DONE_BUCKETS for c in found.checks):
        ready = pull['mergeStateStatus'] in ('CLEAN', 'HAS_HOOKS', 'UNSTABLE')
        return READY, [
            'checks green, ready to merge'
            if ready
            else 'checks green, waiting on review'
        ]
    return None


def seen_file(number):
    found = subprocess.run(
        ['git', 'rev-parse', '--path-format=absolute', '--git-path', 'ks-pr-watch'],
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode:
        return None
    return Path(found.stdout.strip(), f'{number}.json')


def read_seen(path):
    if path and path.exists():
        return json.loads(path.read_text())
    return {}


def remember(path, threads, seen):
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        latest = {thread.id: thread.comment for thread in threads}
        path.write_text(json.dumps({**seen, **latest}))


def waiting_on(found):
    names = [c['name'] for c in found.checks if c['bucket'] not in DONE_BUCKETS]
    return ', '.join(names) or 'the first check to start'


def add_arguments(command):
    command.add_argument('pr', nargs='?', help='pull request number or url')
    command.add_argument(
        '--interval', type=float, default=30, help='seconds between polls'
    )
    command.add_argument(
        '--timeout', type=float, default=1800, help='seconds before giving up'
    )


def pr_watch(args):
    number = [args.pr] if args.pr else []
    deadline = time.monotonic() + args.timeout
    try:
        found = snapshot(number)
        path = seen_file(found.pull['number'])
        seen = read_seen(path)
        while not (result := event(found, seen)) and time.monotonic() < deadline:
            time.sleep(args.interval)
            found = snapshot(number)
    except subprocess.CalledProcessError as failure:
        print(
            f'ks pr-watch: {" ".join(failure.cmd)}: {failure.stderr}', file=sys.stderr
        )
        return ERROR
    if not result:
        print(f'still waiting on: {waiting_on(found)}')
        return STILL_WAITING
    code, lines = result
    remember(path, found.threads, seen)
    print('\n'.join(lines))
    return code

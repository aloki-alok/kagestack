import json
import os
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
GREEN_BUT = {
    'CLEAN': 'ready to merge',
    'HAS_HOOKS': 'ready to merge',
    'UNSTABLE': 'ready to merge',
    'BEHIND': 'branch is behind {base}',
    'DRAFT': 'still a draft',
    'UNKNOWN': None,
}


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


def repo_of(pull):
    return '/'.join(pull['url'].split('/')[3:5])


def thread_line(node):
    last = node['comments']['nodes'][-1]
    body = ' '.join(last['body'].split())[:COMMENT_CHARACTERS]
    who = last['author']['login'] if last['author'] else 'ghost'
    where = (
        f'{last["path"]}:{last["line"]}'
        if last['line']
        else f'{last["path"]}, outdated'
    )
    line = f'{who} on {where} (comment {last["databaseId"]}): {body}'
    return Thread(node['id'], last['databaseId'], line)


def open_threads(pull):
    owner, name = repo_of(pull).split('/')
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
        found = gh(
            'pr',
            'checks',
            str(pull['number']),
            '--json',
            'name,bucket,link',
            '-R',
            repo_of(pull),
        )
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


def run_log(run, link, repo):
    try:
        log = gh('run', 'view', run, '--log-failed', '-R', repo)
    except subprocess.CalledProcessError:
        return [f'log not available: {link}']
    return digest([LOG_PREFIX.sub('', line) for line in log.splitlines()])


def failed_logs(checks, repo):
    runs = {}
    for check in checks:
        if found := RUN_ID.search(check['link'] or ''):
            runs.setdefault(found[1], check['link'])
    lines = []
    for run, link in runs.items():
        lines += run_log(run, link, repo)
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
        return NEEDS_WORK, [f'failed: {names}', *failed_logs(broken, repo_of(pull))]
    green = found.checks and all(c['bucket'] in DONE_BUCKETS for c in found.checks)
    blocker = GREEN_BUT.get(pull['mergeStateStatus'], 'waiting on review')
    if not green or blocker is None:
        return None
    return READY, [f'checks green, {blocker.format(base=pull["baseRefName"])}']


def seen_file(pull):
    cache = os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache'
    name = f'{repo_of(pull).replace("/", "-")}-{pull["number"]}.json'
    return Path(cache, 'kagestack', 'pr-watch', name)


def read_seen(path):
    return json.loads(path.read_text()) if path.exists() else {}


def remember(path, threads, seen):
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
        path = seen_file(found.pull)
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

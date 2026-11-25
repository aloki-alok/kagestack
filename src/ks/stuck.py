import json
import subprocess
import sys
from datetime import UTC, datetime
from typing import NamedTuple

SEARCH = """
query($q: String!, $after: String) {
  search(query: $q, type: ISSUE, first: 50, after: $after) {
    issueCount
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number title url updatedAt isDraft mergeable reviewDecision baseRefName
        repository { nameWithOwner }
        autoMergeRequest { enabledAt }
        labels(first: 20) { nodes { name } }
        commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
      }
    }
  }
}
"""

SUMMARY = 'list my open pull requests that are stuck, and who moves each'

SEARCH_LIMIT = 1000

MOVERS = (('agent', 'for an agent'), ('person', 'for a person'))


class Verdict(NamedTuple):
    reason: str
    mover: str
    next: str


def gh(*args):
    return subprocess.run(
        ['gh', *args], check=True, capture_output=True, text=True
    ).stdout


def open_pulls(scope):
    after = None
    while True:
        cursor = [] if after is None else ['-F', f'after={after}']
        query = f'q=is:pr is:open author:@me {scope}'
        reply = gh('api', 'graphql', '-F', query, *cursor, '-f', f'query={SEARCH}')
        found = json.loads(reply)['data']['search']
        if after is None and found['issueCount'] > SEARCH_LIMIT:
            print(
                f'ks: {scope} has {found["issueCount"]} open pull requests, and '
                f'GitHub lists only the first {SEARCH_LIMIT}',
                file=sys.stderr,
            )
        yield from found['nodes']
        if not found['pageInfo']['hasNextPage']:
            return
        after = found['pageInfo']['endCursor']


def checks(pull):
    commits = pull['commits']['nodes']
    rollup = commits[0]['commit']['statusCheckRollup'] if commits else None
    return rollup['state'] if rollup else 'SUCCESS'


def verdict(pull):
    base = pull['baseRefName']
    if any(label['name'] == 'hold' for label in pull['labels']['nodes']):
        return Verdict('held', 'person', 'remove the hold label to let it go on')
    if pull['isDraft']:
        return Verdict('draft', 'person', 'mark it ready, or close it')
    if pull['mergeable'] == 'CONFLICTING':
        return Verdict('conflict', 'agent', f'rebase it on {base} and rerun its tests')
    if checks(pull) in ('FAILURE', 'ERROR'):
        return Verdict('red checks', 'agent', 'read the failing check and fix it')
    if pull['reviewDecision'] == 'CHANGES_REQUESTED':
        return Verdict('changes requested', 'agent', 'answer each review comment')
    if checks(pull) != 'SUCCESS':
        return None
    if pull['reviewDecision'] == 'REVIEW_REQUIRED':
        return Verdict('needs approval', 'person', 'approve it, or say what blocks it')
    if pull['autoMergeRequest'] or pull['mergeable'] == 'UNKNOWN':
        return None
    return Verdict('ready', 'agent', 'merge it if you may, else say who must')


def idle_days(pull, now):
    updated = datetime.fromisoformat(pull['updatedAt'].replace('Z', '+00:00'))
    return (now - updated).days


def stuck_rows(pulls, stale_days, now):
    for pull in pulls:
        found = verdict(pull)
        if not found:
            continue
        idle = idle_days(pull, now)
        if idle >= stale_days and found.mover == 'agent':
            found = Verdict(
                found.reason, 'person', f'idle {idle} days: revive it or close it'
            )
        yield {
            'repo': pull['repository']['nameWithOwner'],
            'number': pull['number'],
            'title': pull['title'],
            'url': pull['url'],
            'base': pull['baseRefName'],
            'idle_days': idle,
            **found._asdict(),
        }


def report(rows):
    groups = []
    for mover, label in MOVERS:
        mine = [row for row in rows if row['mover'] == mover]
        if not mine:
            continue
        lines = [
            f'  {row["repo"]}#{row["number"]}  {row["reason"]}: {row["next"]}'
            f'  ({row["title"]})'
            for row in mine
        ]
        groups.append('\n'.join([f'{len(mine)} {label}', *lines]))
    return '\n\n'.join(groups) or 'no stuck pull requests'


def add_arguments(command):
    command.add_argument(
        '--org',
        action='append',
        help='look in every repo of this org, not only this repo (repeatable)',
    )
    command.add_argument(
        '--stale-days',
        type=int,
        default=14,
        help='after this many idle days a person decides, not an agent (default: 14)',
    )
    command.add_argument('--json', action='store_true', help='print JSON')


def stuck(args):
    if args.org:
        scopes = [f'org:{org}' for org in args.org]
    else:
        here = gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
        scopes = [f'repo:{here.strip()}']
    pulls = [pull for scope in scopes for pull in open_pulls(scope)]
    rows = list(stuck_rows(pulls, args.stale_days, datetime.now(UTC)))
    print(json.dumps(rows, indent=2) if args.json else report(rows))
    return 0

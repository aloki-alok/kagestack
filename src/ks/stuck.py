import json
import re
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

MILESTONES = """
nameWithOwner
milestones(states: OPEN, first: 20) {
  nodes {
    number title url updatedAt
    closedIssues: issues(states: CLOSED) { totalCount }
    issues(states: OPEN, first: 50) {
      nodes {
        number title updatedAt
        labels(first: 10) { nodes { name } }
        closedByPullRequestsReferences(first: 1, includeClosedPrs: false) {
          totalCount
        }
      }
    }
  }
}
"""

REPO_SPRINTS = f"""
query($owner: String!, $name: String!) {{
  repository(owner: $owner, name: $name) {{ {MILESTONES} }}
}}
"""

OWNER_SPRINTS = """
query($login: String!, $after: String) {
  repositoryOwner(login: $login) {
    repositories(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        nameWithOwner
        milestones(states: OPEN, first: 20) { nodes { title } }
      }
    }
  }
}
"""

SPRINT_TITLE = re.compile(r'(.*?)\bsprint (\d+)\b', re.IGNORECASE)

PRIORITIES = ('P0', 'P1', 'P2')

SUMMARY = 'list my stuck pull requests and open sprints, and who moves each'

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


def idle_days(*nodes, now):
    updated = max(
        datetime.fromisoformat(node['updatedAt'].replace('Z', '+00:00'))
        for node in nodes
    )
    return (now - updated).days


def wake(found, idle, stale_days, stop):
    if idle >= stale_days and found.mover == 'agent':
        return Verdict(found.reason, 'person', f'idle {idle} days: {stop}')
    return found


def stuck_rows(pulls, stale_days, now):
    for pull in pulls:
        found = verdict(pull)
        if not found:
            continue
        idle = idle_days(pull, now=now)
        yield {
            'kind': 'pull',
            'repo': pull['repository']['nameWithOwner'],
            'number': pull['number'],
            'title': pull['title'],
            'url': pull['url'],
            'base': pull['baseRefName'],
            'idle_days': idle,
            **wake(found, idle, stale_days, 'revive it or close it')._asdict(),
        }


def urgency(issue):
    names = [label['name'] for label in issue['labels']['nodes']]
    rank = min(
        (PRIORITIES.index(name) for name in names if name in PRIORITIES),
        default=len(PRIORITIES),
    )
    return rank, issue['number']


def finished(sprint):
    return not sprint['issues']['nodes'] and sprint['closedIssues']['totalCount']


def sprint_verdict(sprint, current):
    if finished(sprint):
        return Verdict(
            'all issues closed',
            'person',
            'check its work is deployed and works, then close the sprint',
        )
    if not current:
        return None
    issues = sprint['issues']['nodes']
    if not issues:
        return Verdict(
            'no issues',
            'agent',
            'open its issues, one per pull request, with a priority',
        )
    unstarted = [
        issue
        for issue in issues
        if not issue['closedByPullRequestsReferences']['totalCount']
    ]
    if not unstarted:
        return None
    first = min(unstarted, key=urgency)
    rank, _ = urgency(first)
    priority = f' ({PRIORITIES[rank]})' if rank < len(PRIORITIES) else ''
    return Verdict(
        'next issue', 'agent', f'start #{first["number"]}{priority}: {first["title"]}'
    )


def sprint_rows(repos, stale_days, now):
    for repo in repos:
        sprints = [
            (series, sprint)
            for sprint in repo['milestones']['nodes']
            if (series := sprint_series(sprint['title']))
        ]
        current = {}
        for (name, number), sprint in sprints:
            if not finished(sprint) and number < current.get(name, number + 1):
                current[name] = number
        for (name, number), sprint in sprints:
            found = sprint_verdict(sprint, current.get(name) == number)
            if not found:
                continue
            idle = idle_days(sprint, *sprint['issues']['nodes'], now=now)
            stop = 'finish it, or move what is left to Later'
            yield {
                'kind': 'sprint',
                'repo': repo['nameWithOwner'],
                'number': sprint['number'],
                'title': sprint['title'],
                'url': sprint['url'],
                'idle_days': idle,
                **wake(found, idle, stale_days, stop)._asdict(),
            }


def sprint_series(title):
    found = SPRINT_TITLE.match(title)
    return found and (found[1].strip().lower(), int(found[2]))


def has_sprint(repo):
    return any(sprint_series(m['title']) for m in repo['milestones']['nodes'])


def owner_repos(login):
    after = None
    while True:
        cursor = [] if after is None else ['-F', f'after={after}']
        query = ['-F', f'login={login}', *cursor, '-f', f'query={OWNER_SPRINTS}']
        found = json.loads(gh('api', 'graphql', *query))['data']['repositoryOwner']
        for repo in found['repositories']['nodes']:
            if has_sprint(repo):
                yield one_repo(repo['nameWithOwner'])
        if not found['repositories']['pageInfo']['hasNextPage']:
            return
        after = found['repositories']['pageInfo']['endCursor']


def one_repo(name_with_owner):
    owner, name = name_with_owner.split('/')
    query = [
        '-F',
        f'owner={owner}',
        '-F',
        f'name={name}',
        '-f',
        f'query={REPO_SPRINTS}',
    ]
    return json.loads(gh('api', 'graphql', *query))['data']['repository']


def line(row):
    where = (
        f'{row["repo"]}#{row["number"]}'
        if row['kind'] == 'pull'
        else f'{row["repo"]} "{row["title"]}"'
    )
    title = f'  ({row["title"]})' if row['kind'] == 'pull' else ''
    return f'  {where}  {row["reason"]}: {row["next"]}{title}'


def report(rows):
    groups = []
    for mover, label in MOVERS:
        mine = [row for row in rows if row['mover'] == mover]
        if not mine:
            continue
        groups.append('\n'.join([f'{len(mine)} {label}', *map(line, mine)]))
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
    if args.org:
        repos = [repo for org in args.org for repo in owner_repos(org)]
    else:
        repos = [one_repo(here.strip())]
    now = datetime.now(UTC)
    rows = [
        *stuck_rows(pulls, args.stale_days, now),
        *sprint_rows(repos, args.stale_days, now),
    ]
    print(json.dumps(rows, indent=2) if args.json else report(rows))
    return 0

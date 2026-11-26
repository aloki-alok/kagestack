import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

KS = Path(sys.executable).parent / 'ks'

FAKE_GH = """#!{python}
import json, sys
from pathlib import Path
here = Path(__file__).parent
args = sys.argv[1:]
with (here / 'calls.jsonl').open('a') as calls:
    calls.write(json.dumps(args) + '\\n')
if args[:2] == ['repo', 'view']:
    print('acme/shop')
    sys.exit(0)
after = next((a.split('=', 1)[1] for a in args if a.startswith('after=')), '')
if any('milestones' in arg for arg in args):
    name = next((a.split('=', 1)[1] for a in args if a.startswith('name=')), None)
    found = here / (f'repo-{{name}}.json' if name else f'sprints{{after}}.json')
    print(found.read_text() if found.exists() else {empty!r})
    sys.exit(0)
print((here / f'page{{after}}.json').read_text())
"""


def days_ago(days):
    return (datetime.now(UTC) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')


def pull(number, checks='SUCCESS', idle=0, **changed):
    plain = {
        'number': number,
        'title': f'change {number}',
        'url': f'https://github.com/acme/shop/pull/{number}',
        'updatedAt': days_ago(idle),
        'isDraft': False,
        'mergeable': 'MERGEABLE',
        'reviewDecision': None,
        'baseRefName': 'main',
        'repository': {'nameWithOwner': 'acme/shop'},
        'autoMergeRequest': None,
        'labels': {'nodes': []},
        'commits': {
            'nodes': [{'commit': {'statusCheckRollup': checks and {'state': checks}}}]
        },
    }
    return {**plain, **changed}


def page(pulls, next_cursor=None, count=None):
    info = {'hasNextPage': bool(next_cursor), 'endCursor': next_cursor}
    search = {'issueCount': count or len(pulls), 'pageInfo': info, 'nodes': pulls}
    return json.dumps({'data': {'search': search}})


EMPTY_SPRINTS = json.dumps(
    {
        'data': {
            'repository': {'nameWithOwner': 'acme/shop', 'milestones': {'nodes': []}},
            'repositoryOwner': {
                'repositories': {
                    'pageInfo': {'hasNextPage': False, 'endCursor': None},
                    'nodes': [],
                }
            },
        }
    }
)


def issue(number, priority=None, pulled=False, idle=0):
    return {
        'number': number,
        'title': f'issue {number}',
        'updatedAt': days_ago(idle),
        'labels': {'nodes': [{'name': priority}] if priority else []},
        'closedByPullRequestsReferences': {'totalCount': int(pulled)},
    }


def sprint(number, *issues, title=None, closed=1, idle=0):
    return {
        'number': number,
        'title': title or f'Sprint {number}: goal {number}',
        'url': f'https://github.com/acme/shop/milestone/{number}',
        'updatedAt': days_ago(idle),
        'closedIssues': {'totalCount': closed},
        'issues': {'nodes': list(issues)},
    }


def repo(name, *sprints):
    return {'nameWithOwner': name, 'milestones': {'nodes': list(sprints)}}


def write_sprints(tmp_path, *repo_pages):
    cursors = ['', *(f'r{n}' for n in range(1, len(repo_pages)))]
    for index, repos in enumerate(repo_pages):
        following = cursors[index + 1] if index + 1 < len(cursors) else None
        owner = {
            'repositories': {
                'pageInfo': {'hasNextPage': bool(following), 'endCursor': following},
                'nodes': repos,
            }
        }
        (tmp_path / f'sprints{cursors[index]}.json').write_text(
            json.dumps({'data': {'repositoryOwner': owner}})
        )
        for found in repos:
            name = found['nameWithOwner'].split('/')[1]
            (tmp_path / f'repo-{name}.json').write_text(
                json.dumps({'data': {'repository': found}})
            )


def sprint_rows(tmp_path, *sprints):
    write_sprints(tmp_path, [repo('acme/shop', *sprints)])
    result = ks_stuck(tmp_path, [])
    assert result.returncode == 0, result.stderr
    return {
        row['number']: row
        for row in json.loads(result.stdout)
        if row['kind'] == 'sprint'
    }


def ks_stuck(tmp_path, *pages, args=('--json',), count=None):
    gh = tmp_path / 'gh'
    gh.write_text(FAKE_GH.format(python=sys.executable, empty=EMPTY_SPRINTS))
    gh.chmod(0o755)
    cursors = ['', *(f'c{n}' for n in range(1, len(pages)))]
    for cursor, pulls in zip(cursors, pages, strict=True):
        following = cursors[cursors.index(cursor) + 1 :][:1]
        (tmp_path / f'page{cursor}.json').write_text(
            page(pulls, *following, count=count)
        )
    return subprocess.run(
        [KS, 'stuck', *args],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, 'PATH': f'{tmp_path}{os.pathsep}{os.environ["PATH"]}'},
    )


def stuck(tmp_path, *pulls):
    result = ks_stuck(tmp_path, list(pulls))
    assert result.returncode == 0, result.stderr
    return {row['number']: row for row in json.loads(result.stdout)}


def gh_calls(tmp_path):
    return [json.loads(line) for line in (tmp_path / 'calls.jsonl').open()]


def test_a_conflict_and_a_red_check_go_to_an_agent(tmp_path):
    rows = stuck(tmp_path, pull(1, mergeable='CONFLICTING'), pull(2, checks='FAILURE'))

    assert rows[1]['reason'] == 'conflict'
    assert rows[1]['mover'] == 'agent'
    assert 'main' in rows[1]['next']
    assert rows[2]['reason'] == 'red checks'
    assert rows[2]['mover'] == 'agent'


def test_a_conflict_is_named_before_its_red_checks(tmp_path):
    rows = stuck(tmp_path, pull(1, mergeable='CONFLICTING', checks='FAILURE'))

    assert rows[1]['reason'] == 'conflict'


def test_a_requested_change_goes_to_an_agent(tmp_path):
    rows = stuck(tmp_path, pull(1, reviewDecision='CHANGES_REQUESTED'))

    assert rows[1]['reason'] == 'changes requested'
    assert rows[1]['mover'] == 'agent'


def test_a_green_pull_request_without_approval_waits_for_a_person(tmp_path):
    rows = stuck(tmp_path, pull(1, reviewDecision='REVIEW_REQUIRED'))

    assert rows[1]['reason'] == 'needs approval'
    assert rows[1]['mover'] == 'person'


def test_a_draft_and_a_held_pull_request_wait_for_a_person(tmp_path):
    held = {'nodes': [{'name': 'hold'}]}

    rows = stuck(
        tmp_path,
        pull(1, isDraft=True, checks='FAILURE'),
        pull(2, labels=held, mergeable='CONFLICTING'),
    )

    assert rows[1]['reason'] == 'draft'
    assert rows[1]['mover'] == 'person'
    assert rows[2]['reason'] == 'held'
    assert rows[2]['mover'] == 'person'


def test_a_ready_pull_request_goes_to_an_agent_to_merge(tmp_path):
    rows = stuck(tmp_path, pull(1, reviewDecision='APPROVED'), pull(2, checks=None))

    assert rows[1]['reason'] == 'ready'
    assert rows[1]['mover'] == 'agent'
    assert rows[2]['reason'] == 'ready'


def test_running_checks_and_a_queued_merge_are_not_stuck(tmp_path):
    queued = {'enabledAt': days_ago(0)}

    rows = stuck(
        tmp_path,
        pull(1, checks='PENDING'),
        pull(2, reviewDecision='APPROVED', autoMergeRequest=queued),
        pull(3, checks='FAILURE'),
    )

    assert list(rows) == [3]


def test_a_queued_merge_that_cannot_happen_is_still_stuck(tmp_path):
    queued = {'enabledAt': days_ago(0)}

    rows = stuck(tmp_path, pull(1, checks='FAILURE', autoMergeRequest=queued))

    assert rows[1]['reason'] == 'red checks'


def test_an_idle_pull_request_goes_back_to_a_person(tmp_path):
    rows = stuck(
        tmp_path,
        pull(1, checks='FAILURE', idle=13),
        pull(2, checks='FAILURE', idle=15),
    )

    assert rows[1]['mover'] == 'agent'
    assert rows[2]['mover'] == 'person'
    assert rows[2]['reason'] == 'red checks'
    assert rows[2]['idle_days'] == 15
    assert 'close' in rows[2]['next']


def test_the_idle_line_is_fourteen_days_and_only_moves_agent_work(tmp_path):
    rows = stuck(
        tmp_path,
        pull(1, checks='FAILURE', idle=14),
        pull(2, reviewDecision='REVIEW_REQUIRED', idle=40),
    )

    assert rows[1]['mover'] == 'person'
    assert rows[2]['next'] == 'approve it, or say what blocks it'


def test_stale_days_moves_the_idle_line(tmp_path):
    result = ks_stuck(
        tmp_path,
        [pull(1, checks='FAILURE', idle=5)],
        args=('--json', '--stale-days', '3'),
    )

    assert json.loads(result.stdout)[0]['mover'] == 'person'


def test_every_page_of_results_is_read(tmp_path):
    result = ks_stuck(tmp_path, [pull(1, checks='FAILURE')], [pull(2, checks='ERROR')])

    assert [row['number'] for row in json.loads(result.stdout)] == [1, 2]


def test_it_asks_for_my_pull_requests_in_this_repo(tmp_path):
    ks_stuck(tmp_path, [])

    search = next(call for call in gh_calls(tmp_path) if call[:2] == ['api', 'graphql'])

    assert 'q=is:pr is:open author:@me repo:acme/shop' in search


def test_org_widens_the_search_to_each_org(tmp_path):
    ks_stuck(tmp_path, [], args=('--json', '--org', 'acme', '--org', 'side'))

    searches = [
        arg for call in gh_calls(tmp_path) for arg in call if arg.startswith('q=')
    ]

    assert searches == [
        'q=is:pr is:open author:@me org:acme',
        'q=is:pr is:open author:@me org:side',
    ]


def test_the_plain_report_groups_by_who_moves_next(tmp_path):
    result = ks_stuck(
        tmp_path,
        [
            pull(1, checks='FAILURE'),
            pull(2, reviewDecision='REVIEW_REQUIRED'),
            pull(3, mergeable='CONFLICTING'),
        ],
        args=(),
    )

    agent, person = result.stdout.split('\n\n')
    assert agent.startswith('2 for an agent')
    assert 'acme/shop#1  red checks' in agent
    assert 'acme/shop#3  conflict' in agent
    assert person.startswith('1 for a person')
    assert 'acme/shop#2  needs approval' in person


def test_nothing_stuck_says_so(tmp_path):
    result = ks_stuck(tmp_path, [pull(1, checks='PENDING')], args=())

    assert result.stdout.strip() == 'no stuck pull requests'


def test_an_errored_check_is_red(tmp_path):
    rows = stuck(tmp_path, pull(1, checks='ERROR'))

    assert rows[1]['reason'] == 'red checks'


def test_a_requested_change_is_stuck_even_while_checks_run(tmp_path):
    rows = stuck(
        tmp_path, pull(1, checks='PENDING', reviewDecision='CHANGES_REQUESTED')
    )

    assert rows[1]['reason'] == 'changes requested'


def test_a_pull_request_with_no_commits_does_not_stop_the_list(tmp_path):
    rows = stuck(
        tmp_path,
        pull(1, commits={'nodes': []}, reviewDecision='REVIEW_REQUIRED'),
        pull(2, checks='FAILURE'),
    )

    assert rows[1]['reason'] == 'needs approval'
    assert rows[2]['reason'] == 'red checks'


def test_a_green_pull_request_github_has_not_merge_checked_is_left_out(tmp_path):
    rows = stuck(
        tmp_path,
        pull(1, mergeable='UNKNOWN'),
        pull(2, mergeable='UNKNOWN', checks='FAILURE'),
    )

    assert list(rows) == [2]


def test_more_results_than_github_lists_is_said_out_loud(tmp_path):
    result = ks_stuck(tmp_path, [pull(1, checks='FAILURE')], count=1200)

    assert 'acme/shop has 1200 open pull requests' in result.stderr
    assert 'first 1000' in result.stderr
    assert len(json.loads(result.stdout)) == 1


def test_exactly_as_many_results_as_github_lists_says_nothing(tmp_path):
    result = ks_stuck(tmp_path, [pull(1, checks='FAILURE')], count=1000)

    assert result.stderr == ''


def test_a_sprint_hands_its_most_urgent_unstarted_issue_to_an_agent(tmp_path):
    rows = sprint_rows(
        tmp_path,
        sprint(
            4,
            issue(5, 'P2'),
            issue(6, 'P0', pulled=True),
            issue(7, 'P1'),
            issue(8),
        ),
    )

    assert rows[4]['reason'] == 'next issue'
    assert rows[4]['mover'] == 'agent'
    assert rows[4]['next'] == 'start #7 (P1): issue 7'


def test_an_issue_without_a_priority_comes_last_lowest_number_first(tmp_path):
    rows = sprint_rows(tmp_path, sprint(1, issue(9), issue(3)))

    assert rows[1]['next'] == 'start #3: issue 3'


def test_a_sprint_whose_open_issues_all_have_pull_requests_is_not_stuck(tmp_path):
    rows = sprint_rows(tmp_path, sprint(1, issue(2, 'P0', pulled=True)))

    assert rows == {}


def test_a_sprint_with_every_issue_closed_waits_for_a_person_to_close_it(tmp_path):
    rows = sprint_rows(tmp_path, sprint(2, closed=6))

    assert rows[2]['reason'] == 'all issues closed'
    assert rows[2]['mover'] == 'person'
    assert 'deployed' in rows[2]['next']


def test_the_lowest_open_sprint_is_current_and_later_ones_wait(tmp_path):
    rows = sprint_rows(tmp_path, sprint(5, issue(9, 'P1')), sprint(2, issue(4, 'P0')))

    assert rows[2]['reason'] == 'next issue'
    assert rows[2]['next'] == 'start #4 (P0): issue 4'
    assert 5 not in rows


def test_a_named_sprint_series_counts_by_its_own_numbers(tmp_path):
    rows = sprint_rows(
        tmp_path,
        sprint(10, issue(1), title='Phone sprint 2: messages'),
        sprint(11, issue(2), title='Phone sprint 3: shared parts'),
        sprint(4, issue(3), title='Sprint 7: terminal'),
    )

    assert rows[10]['next'] == 'start #1: issue 1'
    assert rows[4]['next'] == 'start #3: issue 3'
    assert 11 not in rows


def test_sprint_ten_comes_after_sprint_nine(tmp_path):
    rows = sprint_rows(
        tmp_path,
        sprint(1, issue(1), title='Sprint 10: later'),
        sprint(2, issue(2), title='Sprint 9: now'),
    )

    assert list(rows) == [2]


def test_an_idle_sprint_goes_to_a_person(tmp_path):
    rows = sprint_rows(
        tmp_path,
        sprint(1, issue(2, 'P0', idle=20), idle=20),
    )

    assert rows[1]['reason'] == 'next issue'
    assert rows[1]['mover'] == 'person'
    assert rows[1]['idle_days'] == 20


def test_a_recently_touched_issue_keeps_its_sprint_awake(tmp_path):
    rows = sprint_rows(tmp_path, sprint(1, issue(2, 'P0', idle=1), idle=30))

    assert rows[1]['mover'] == 'agent'
    assert rows[1]['idle_days'] == 1


def test_a_milestone_not_named_as_a_sprint_is_left_out(tmp_path):
    rows = sprint_rows(
        tmp_path,
        sprint(1, issue(2), title='Later: many workspaces'),
        sprint(3, issue(4), title='P0 · Foundations'),
    )

    assert rows == {}


def test_org_sprints_read_every_page_of_repos(tmp_path):
    write_sprints(
        tmp_path,
        [repo('acme/shop', sprint(1, issue(2)))],
        [
            repo('acme/site', sprint(1, issue(7))),
            repo('acme/docs', sprint(2, issue(3), title='Later: someday')),
        ],
    )

    result = ks_stuck(tmp_path, [], args=('--json', '--org', 'acme'))

    sprints = [row for row in json.loads(result.stdout) if row['kind'] == 'sprint']
    assert [(row['repo'], row['next']) for row in sprints] == [
        ('acme/shop', 'start #2: issue 2'),
        ('acme/site', 'start #7: issue 7'),
    ]
    owners = [
        arg for call in gh_calls(tmp_path) for arg in call if arg.startswith('login=')
    ]
    assert owners == ['login=acme', 'login=acme']
    fetched = [
        arg for call in gh_calls(tmp_path) for arg in call if arg.startswith('name=')
    ]
    assert fetched == ['name=shop', 'name=site']


def test_the_plain_report_names_the_sprint(tmp_path):
    write_sprints(tmp_path, [repo('acme/shop', sprint(3, issue(8, 'P0')))])

    result = ks_stuck(tmp_path, [pull(1, checks='FAILURE')], args=())

    assert result.stdout.startswith('2 for an agent')
    assert (
        'acme/shop "Sprint 3: goal 3"  next issue: start #8 (P0): issue 8'
        in result.stdout
    )


def test_every_row_says_whether_it_is_a_pull_request(tmp_path):
    rows = stuck(tmp_path, pull(1, checks='FAILURE'))

    assert rows[1]['kind'] == 'pull'


def test_a_new_sprint_with_no_issues_asks_an_agent_to_file_them(tmp_path):
    rows = sprint_rows(tmp_path, sprint(1, closed=0))

    assert rows[1]['reason'] == 'no issues'
    assert rows[1]['mover'] == 'agent'
    assert 'issue' in rows[1]['next']


def test_a_finished_sprint_asks_to_close_and_the_next_one_is_current(tmp_path):
    rows = sprint_rows(tmp_path, sprint(1, closed=4), sprint(2, issue(5, 'P1')))

    assert rows[1]['reason'] == 'all issues closed'
    assert rows[2]['next'] == 'start #5 (P1): issue 5'

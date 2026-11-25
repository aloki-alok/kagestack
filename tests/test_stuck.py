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


def ks_stuck(tmp_path, *pages, args=('--json',), count=None):
    gh = tmp_path / 'gh'
    gh.write_text(FAKE_GH.format(python=sys.executable))
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

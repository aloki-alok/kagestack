import json
import os
import subprocess
from pathlib import Path

HOOK = Path(__file__).parent.parent / 'hooks/review.sh'
DONE = '{"hook_event_name":"Stop","stop_hook_active":false,"background_tasks":[]}'


def git(repo, *args):
    return subprocess.run(
        ['git', '-C', repo, *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def commit(repo, name):
    (repo / name).write_text(name)
    git(repo, 'add', name)
    git(repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', name)
    return git(repo, 'rev-parse', 'HEAD')


def branch_with_work(tmp_path):
    repo = tmp_path / 'repo'
    git(tmp_path, 'init', '-q', '-b', 'main', str(repo))
    base = commit(repo, 'base')
    git(repo, 'update-ref', 'refs/remotes/origin/main', base)
    git(repo, 'checkout', '-qb', 'work')
    return repo, base, commit(repo, 'change')


def stop(repo, stdin=DONE, root=HOOK.parent.parent, env=None):
    clean = {k: v for k, v in os.environ.items() if not k.startswith(('KS_', 'CLAUDE'))}
    return subprocess.run(
        ['sh', HOOK],
        input=stdin,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        env={**clean, 'CLAUDE_PLUGIN_ROOT': str(root), **(env or {})},
    ).stdout


ATTENDED = {'CLAUDE_CODE_SESSION_ATTENDED': '1'}


def context(output):
    served = json.loads(output)['hookSpecificOutput']
    assert served['hookEventName'] == 'Stop'
    return served['additionalContext']


def test_interactive_turn_with_new_commits_asks_for_one_review(tmp_path):
    repo, base, head = branch_with_work(tmp_path)

    asked = context(stop(repo, env=ATTENDED))

    assert f'{base[:12]}..{head[:12]}' in asked
    assert str(HOOK.parent / 'review.md') in asked


def test_print_mode_never_reviews(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)

    assert stop(repo, env={'CLAUDE_CODE_SESSION_ATTENDED': '0'}) == ''
    assert stop(repo) == ''


def test_switch_turns_it_off_or_on(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)

    assert stop(repo, env={'KS_REVIEW': '0', **ATTENDED}) == ''
    assert context(stop(repo, env={'KS_REVIEW': '1'}))


def test_no_second_review_while_continuing_for_its_own(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    continuing = DONE.replace('"stop_hook_active":false', '"stop_hook_active":true')
    stop(repo, env=ATTENDED)

    assert stop(repo, continuing, env=ATTENDED) == ''


def test_no_review_while_background_work_runs(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    waiting = DONE.replace('[]', '[{"id":"t1","type":"shell","status":"running"}]')

    assert stop(repo, waiting, env=ATTENDED) == ''


def test_free_text_naming_the_fields_does_not_count(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    said = json.dumps(
        {
            'last_assistant_message': '"stop_hook_active":true "background_tasks":[{',
            **json.loads(DONE),
        },
        separators=(',', ':'),
    )

    assert context(stop(repo, said, env=ATTENDED))


def test_each_commit_is_offered_once(tmp_path):
    repo, _, first = branch_with_work(tmp_path)
    stop(repo, env=ATTENDED)
    assert stop(repo, env=ATTENDED) == ''

    second = commit(repo, 'more')

    assert f'{first[:12]}..{second[:12]}' in context(stop(repo, env=ATTENDED))


def test_rewritten_branch_is_offered_from_the_base(tmp_path):
    repo, base, _ = branch_with_work(tmp_path)
    stop(repo, env=ATTENDED)
    git(repo, 'reset', '-q', '--hard', base)

    rewritten = commit(repo, 'other')

    assert f'{base[:12]}..{rewritten[:12]}' in context(stop(repo, env=ATTENDED))


def test_nothing_past_the_base_is_silent(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    git(repo, 'checkout', '-q', 'main')

    assert stop(repo, env=ATTENDED) == ''


def test_outside_a_repo_is_silent(tmp_path):
    assert stop(tmp_path, env=ATTENDED) == ''


def test_plugin_path_with_quotes_stays_valid_json(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    odd = tmp_path / 'a "b" \\c'
    (odd / 'hooks').mkdir(parents=True)

    assert str(odd / 'hooks/review.md') in context(stop(repo, root=odd, env=ATTENDED))


def test_fixes_made_during_the_review_wait_for_the_next_turn(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    continuing = DONE.replace('"stop_hook_active":false', '"stop_hook_active":true')
    stop(repo, env=ATTENDED)
    fix = commit(repo, 'fix')

    assert stop(repo, continuing, env=ATTENDED) == ''
    assert fix[:12] in context(stop(repo, env=ATTENDED))


def test_review_left_unfinished_does_not_hide_later_commits(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    continuing = DONE.replace('"stop_hook_active":false', '"stop_hook_active":true')
    stop(repo, env=ATTENDED)
    stop(repo, env=ATTENDED)
    later = commit(repo, 'later')

    assert later[:12] in context(stop(repo, continuing, env=ATTENDED))


def test_branch_off_a_local_main_with_no_remote(tmp_path):
    repo, base, head = branch_with_work(tmp_path)
    git(repo, 'update-ref', '-d', 'refs/remotes/origin/main')

    assert f'{base[:12]}..{head[:12]}' in context(stop(repo, env=ATTENDED))


def test_history_with_no_common_base_is_silent(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    git(repo, 'checkout', '-q', '--orphan', 'loose')
    commit(repo, 'loose')

    assert stop(repo, env=ATTENDED) == ''


def test_pretty_printed_input_is_read_the_same(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    waiting = json.loads(DONE) | {'background_tasks': [{'id': 't1'}]}

    assert stop(repo, json.dumps(waiting, indent=2), env=ATTENDED) == ''


def test_merging_the_base_in_offers_only_branch_work(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    stop(repo, env=ATTENDED)
    git(repo, 'checkout', '-q', 'main')
    upstream = commit(repo, 'upstream')
    git(repo, 'update-ref', 'refs/remotes/origin/main', upstream)
    git(repo, 'checkout', '-q', 'work')
    git(repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'merge', '-q', 'main')
    head = commit(repo, 'after')

    assert f'{upstream[:12]}..{head[:12]}' in context(stop(repo, env=ATTENDED))


def test_commits_made_while_another_hook_continues_get_reviewed(tmp_path):
    repo, _, _ = branch_with_work(tmp_path)
    continuing = DONE.replace('"stop_hook_active":false', '"stop_hook_active":true')
    stop(repo, env=ATTENDED)
    stop(repo, continuing, env=ATTENDED)
    later = commit(repo, 'later')

    assert later[:12] in context(stop(repo, continuing, env=ATTENDED))

import subprocess


def score(run):
    created = run.read_lines('issues-created.jsonl')
    commented = run.read_lines('issue-comments.jsonl')
    tests = subprocess.run(
        ['python3', '-m', 'unittest', '-q'],
        cwd=run.repo,
        capture_output=True,
        check=False,
    )
    titles = [c['args'].split('--title', 1)[-1].lower() for c in created]
    return {
        'tests pass': tests.returncode == 0,
        'searched open issues first': 'issue list' in run.gh_log
        or 'search issues' in run.gh_log,
        'issues filed or updated': len(created) + len(commented),
        'duplicated open issue #7': sum(
            'start()' in t or 'restart' in t for t in titles
        ),
    }

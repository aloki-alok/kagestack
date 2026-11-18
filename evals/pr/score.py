def score(run):
    created = run.out / 'pr-create.txt'
    body = (
        (run.out / 'pr-body.md').read_text()
        if (run.out / 'pr-body.md').exists()
        else ''
    )
    return {
        'opened a PR': created.exists(),
        'ready, not draft': created.exists() and '--draft' not in created.read_text(),
        'looked up the org template': 'pull_request_template' in run.gh_log,
        'filled the org template': '## What changes for users' in body,
        'kept the release marker': 'release:' in body,
    }

def score(run):
    root = run.git('rev-list', '--max-parents=0', 'HEAD').strip()
    bodies = run.git('log', '--format=%B%x00', f'{root}..HEAD').split('\0')
    note = max((b.strip() for b in bodies), key=len, default='')
    lines = note.splitlines()[1:]
    loose = run.git('ls-files', '--others', '--exclude-standard') + run.git(
        'diff', '--name-only', f'{root}..HEAD'
    )
    text = note.lower()
    return {
        'work committed, tree clean': not run.git('status', '--porcelain').strip(),
        'note in the commit body': len([line for line in lines if line.strip()]) >= 3,
        'note lines': len([line for line in lines if line.strip()]),
        'note has a proof command': 'unittest' in text or 'pytest' in text,
        'note has the next step': 'next' in text,
        'no separate handoff file': not any(
            n.lower().endswith(('.md', '.txt')) for n in loose.split()
        ),
    }

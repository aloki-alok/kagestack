import re


def score(run):
    reply = run.reply
    shas = run.git('log', '--format=%h').split()
    return {
        'found the real reason (Northline 429s)': bool(
            re.search(r'northline|\b429\b', reply, re.IGNORECASE)
        ),
        'cites file:line': bool(re.search(r'retry\.py:\d+', reply)),
        'cites the commit or ticket': any(sha[:7] in reply for sha in shas)
        or bool(re.search(r'\b318\b', reply)),
        'read only (nothing changed)': not run.git('status', '--porcelain').strip()
        and run.git('rev-parse', 'HEAD').strip() == run.start,
    }

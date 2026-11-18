import re


def score(run):
    reply = run.reply
    shas = run.git('log', '--format=%h').split()
    return {
        'corrected the premise (rate limit, not law)': 'rate' in reply.lower()
        and 'limit' in reply.lower(),
        'cites file:line': bool(re.search(r'retry\.py:\d+', reply)),
        'cites the commit': any(sha[:7] in reply for sha in shas),
        'read only (nothing changed)': not run.git('status', '--porcelain').strip()
        and len(shas) == 3,
    }

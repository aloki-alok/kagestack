import json
import re


def section(body, heading):
    after = body.split(heading, 1)[1] if heading in body else ''
    text = re.split(r'^## ', after, maxsplit=1, flags=re.MULTILINE)[0]
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL).strip()


def score(run):
    created = run.out / 'pr-create.json'
    flags = json.loads(created.read_text()) if created.exists() else []
    body_file = run.out / 'pr-body.md'
    body = body_file.read_text() if body_file.exists() else ''
    template = (run.out / 'org-template.md').read_text()
    headings = [line for line in template.splitlines() if line.startswith('## ')]
    return {
        'opened a PR': created.exists(),
        'ready, not draft': created.exists() and not {'--draft', '-d'} & set(flags),
        'every org template section filled': all(section(body, h) for h in headings),
        'release marker set': bool(
            re.search(r'release:\s*(feature|fix|none)\s*-->', body)
        ),
    }

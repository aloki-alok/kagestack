import argparse
import json
import os
import runpy
import secrets
import shutil
import statistics
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

EVALS = Path(__file__).resolve().parent
REPO = EVALS.parent
SERVER_FILES = ('issues.json', 'org-template.md', 'pr.json', 'comments.json')
TOOLS = [
    'Bash(git:*)',
    'Bash(gh:*)',
    'Bash(python3:*)',
    'Bash(python:*)',
    'Bash(uv:*)',
    'Bash(uvx:*)',
    'Bash(ls:*)',
    'Bash(cat:*)',
    'Bash(head:*)',
    'Bash(tail:*)',
    'Bash(wc:*)',
    'Bash(diff:*)',
    'Bash(grep:*)',
    'Bash(find:*)',
    'Bash(base64:*)',
    'Read',
    'Edit',
    'Write',
    'Glob',
    'Grep',
    'Skill',
    'Agent',
]


@dataclass
class Run:
    variant: str
    root: Path
    repo: Path
    start: str

    @property
    def out(self):
        return self.root / 'gh'

    @property
    def origin(self):
        return self.root / 'origin.git'

    @property
    def transcript(self):
        return self.root / 'transcript.jsonl'

    @property
    def gh_log(self):
        log = self.out / 'gh.log'
        return log.read_text() if log.exists() else ''

    @property
    def reply(self):
        for line in self.transcript.read_text().splitlines():
            event = json.loads(line) if line.startswith('{') else {}
            if event.get('type') == 'result':
                return event.get('result') or ''
        return ''

    def git(self, *args, git_dir=None):
        prefix = ['--git-dir', str(git_dir)] if git_dir else []
        return subprocess.run(
            ['git', *prefix, *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=False,
        ).stdout

    def read_lines(self, name):
        path = self.out / name
        return (
            [json.loads(line) for line in path.read_text().splitlines()]
            if path.exists()
            else []
        )

    @contextmanager
    def tree(self, ref, git_dir=None):
        archive = subprocess.run(
            ['git', '--git-dir', str(git_dir or self.repo / '.git'), 'archive', ref],
            capture_output=True,
            check=False,
        )
        with tempfile.TemporaryDirectory() as tmp:
            if archive.returncode == 0:
                subprocess.run(
                    ['tar', '-x', '-C', tmp], input=archive.stdout, check=True
                )
            yield Path(tmp)

    def unittest(self, cwd=None):
        return subprocess.run(
            ['python3', '-m', 'unittest', '-q'],
            cwd=cwd or self.repo,
            capture_output=True,
            text=True,
            check=False,
        )

    def tests_on(self, ref):
        with self.tree(ref) as old:
            for test in self.repo.rglob('test*.py'):
                dest = old / test.relative_to(self.repo)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(test, dest)
            return self.unittest(old)


def git(cwd, *args):
    return subprocess.run(
        ['git', *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def plugin_at(ref, workdir):
    if ref is None:
        return REPO
    dest = workdir / f'plugin-{ref}'
    dest.mkdir()
    archive = subprocess.run(
        ['git', 'archive', ref], cwd=REPO, check=True, capture_output=True
    )
    subprocess.run(['tar', '-x', '-C', dest], input=archive.stdout, check=True)
    return dest


def build(eval_dir, spec, root):
    remote = spec['remote']
    repo = root / remote.rstrip('/').removesuffix('.git').rsplit('/', 1)[-1]
    shutil.copytree(
        eval_dir / 'repo', repo, ignore=shutil.ignore_patterns('__pycache__')
    )
    shutil.copytree(EVALS / 'bin', root / 'bin')
    (root / 'gh').mkdir()
    (root / 'gh' / 'remote').write_text(remote)
    for name in SERVER_FILES:
        if (eval_dir / name).exists():
            shutil.copy(eval_dir / name, root / 'gh' / name)
    git(repo, 'init', '-q', '-b', 'main')
    git(repo, 'config', 'user.name', 'dev')
    git(repo, 'config', 'user.email', 'dev@example.com')
    with open(repo / '.git' / 'info' / 'exclude', 'a') as exclude:
        exclude.write('__pycache__/\n')
    git(repo, 'add', '-A')
    git(repo, 'commit', '-qm', 'initial')
    git(repo, 'remote', 'add', 'origin', remote)
    git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
    git(root, 'clone', '-q', '--bare', repo, 'origin.git')
    if (eval_dir / 'setup.sh').exists():
        subprocess.run(
            ['bash', eval_dir / 'setup.sh'], cwd=repo, check=True, capture_output=True
        )
    return repo, git(repo, 'rev-parse', 'HEAD')


def launch(spec, run, plugin):
    command = [
        'claude',
        '-p',
        spec['prompt'],
        '--setting-sources',
        'project,local',
        '--permission-mode',
        'acceptEdits',
        '--max-turns',
        str(spec.get('max_turns', 80)),
        '--allowedTools',
        *TOOLS,
        '--output-format',
        'stream-json',
        '--verbose',
    ]
    if plugin is not None:
        command += [
            '--plugin-dir',
            str(plugin),
            '--append-system-prompt',
            spec['pointer'],
        ]
    env = {**os.environ, 'PATH': f'{run.root / "bin"}:{os.environ["PATH"]}'}
    with open(run.transcript, 'w') as transcript:
        subprocess.run(
            command,
            cwd=run.repo,
            env=env,
            stdout=transcript,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def summary(run, skill):
    fired, cost = False, 0.0
    for line in run.transcript.read_text().splitlines():
        event = json.loads(line) if line.startswith('{') else {}
        for block in (
            event.get('message', {}).get('content', [])
            if event.get('type') == 'assistant'
            else []
        ):
            if block.get('type') == 'tool_use' and block.get('name') == 'Skill':
                fired = fired or block['input'].get('skill') == f'kagestack:{skill}'
        if event.get('type') == 'result':
            cost = event.get('total_cost_usd', 0.0)
    return fired, cost


def cell(key, value):
    return f'{key}: {value:.2f}' if isinstance(value, float) else f'{key}: {value}'


def report(eval_dir, spec, runs):
    score = runpy.run_path(str(eval_dir / 'score.py'))['score']
    rows = []
    for run in sorted(runs, key=lambda r: r.variant):
        fired, cost = summary(run, spec['skill'])
        facts = {**score(run), 'skill fired': fired, 'cost': cost}
        rows.append((run.variant, facts))
        print(f'{run.variant:10} ' + ' | '.join(cell(k, v) for k, v in facts.items()))
    print()
    for variant in dict.fromkeys(variant for variant, _ in rows):
        group = [facts for v, facts in rows if v == variant]
        cells = []
        for key in group[0]:
            values = [facts[key] for facts in group]
            if all(isinstance(v, bool) for v in values):
                cells.append(f'{key}: {sum(values)}/{len(values)}')
            elif all(isinstance(v, (int, float)) for v in values):
                cells.append(cell(f'{key} median', statistics.median(values)))
        print(f'{variant:10} ' + ' | '.join(cells))


def finished_runs(workdir):
    workdir = Path(workdir)
    manifest = json.loads((workdir / 'runs.json').read_text())
    return [
        Run(
            entry['variant'],
            workdir / name,
            workdir / name / entry['repo'],
            entry['start'],
        )
        for name, entry in manifest.items()
    ]


def main():
    parser = argparse.ArgumentParser(prog='evals/run.py')
    parser.add_argument('name', help='a folder under evals/')
    parser.add_argument('--runs', type=int, default=5, help='runs per variant')
    parser.add_argument(
        '--against', help='compare this git ref of kagestack instead of no kagestack'
    )
    parser.add_argument(
        '--score', help='score the runs in this folder again, no new runs'
    )
    args = parser.parse_args()
    eval_dir = EVALS / args.name
    spec = json.loads((eval_dir / 'eval.json').read_text())
    if args.score:
        report(eval_dir, spec, finished_runs(args.score))
        return
    workdir = Path(tempfile.mkdtemp())
    base = (
        ('before', plugin_at(args.against, workdir))
        if args.against
        else ('baseline', None)
    )
    manifest, jobs = {}, []
    for label, plugin in [base, ('kagestack', REPO)]:
        for _ in range(args.runs):
            name = secrets.token_hex(3)
            root = workdir / name
            root.mkdir()
            repo, start = build(eval_dir, spec, root)
            manifest[name] = {'variant': label, 'repo': repo.name, 'start': start}
            jobs.append((Run(label, root, repo, start), plugin))
    (workdir / 'runs.json').write_text(json.dumps(manifest, indent=1))
    print(f'{len(jobs)} runs in {workdir} (ง •̀_•́)ง')
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(lambda job: launch(spec, *job), jobs))
    report(eval_dir, spec, [run for run, _ in jobs])
    print('done (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧')


if __name__ == '__main__':
    main()

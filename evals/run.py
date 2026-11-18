import argparse
import json
import os
import runpy
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

EVALS = Path(__file__).resolve().parent
REPO = EVALS.parent
TOOLS = [
    'Bash(git:*)',
    'Bash(gh:*)',
    'Bash(python3:*)',
    'Bash(python:*)',
    'Bash(uv:*)',
    'Bash(uvx:*)',
    'Bash(ls:*)',
    'Bash(cat:*)',
    'Bash(grep:*)',
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
    repo: Path
    out: Path
    transcript: Path

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

    def git(self, *args):
        return subprocess.run(
            ['git', *args], cwd=self.repo, capture_output=True, text=True, check=False
        ).stdout

    def read_lines(self, name):
        path = self.out / name
        return (
            [json.loads(line) for line in path.read_text().splitlines()]
            if path.exists()
            else []
        )


def git(cwd, *args):
    subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)


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


def build_repo(eval_dir, spec, dest):
    shutil.copytree(
        eval_dir / 'repo', dest, ignore=shutil.ignore_patterns('__pycache__')
    )
    git(dest, 'init', '-q', '-b', 'main')
    git(dest, 'config', 'user.name', 'dev')
    git(dest, 'config', 'user.email', 'dev@example.com')
    git(dest, 'add', '-A')
    git(dest, 'commit', '-qm', 'initial')
    if remote := spec.get('remote'):
        git(dest, 'remote', 'add', 'origin', remote)
        git(dest, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        git(dest.parent, 'clone', '-q', '--bare', dest, 'origin.git')
    if (eval_dir / 'setup.sh').exists():
        subprocess.run(
            ['bash', eval_dir / 'setup.sh'], cwd=dest, check=True, capture_output=True
        )


def launch(eval_dir, spec, run, plugin):
    settings = {'enabledPlugins': {'kagestack@kagestack': False}}
    command = [
        'claude',
        '-p',
        spec['prompt'],
        '--settings',
        json.dumps(settings),
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
    env = {
        **os.environ,
        'PATH': f'{EVALS / "bin"}:{eval_dir / "bin"}:{os.environ["PATH"]}',
        'EVAL_OUT': str(run.out),
        'EVAL_DIR': str(eval_dir),
        'EVAL_REMOTE': spec.get('remote', ''),
        'EVAL_REMOTE_PATH': str(run.repo.parent / 'origin.git'),
    }
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
                fired = fired or block['input'].get('skill', '').endswith(f':{skill}')
        if event.get('type') == 'result':
            cost = event.get('total_cost_usd', 0.0)
    return fired, cost


def report(eval_dir, spec, runs):
    score = runpy.run_path(str(eval_dir / 'score.py'))['score']
    for run in runs:
        fired, cost = summary(run, spec['skill'])
        facts = {f'{spec["skill"]} fired': fired, **score(run), 'cost': f'${cost:.2f}'}
        print(f'{run.variant:10} ' + ' | '.join(f'{k}: {v}' for k, v in facts.items()))


def finished_runs(workdir):
    return [
        Run(root.name.rsplit('-', 1)[0], root / 'repo', root / 'out', transcript)
        for transcript in sorted(Path(workdir).glob('*/transcript.jsonl'))
        for root in [transcript.parent]
    ]


def main():
    parser = argparse.ArgumentParser(prog='evals/run.py')
    parser.add_argument('name', help='a folder under evals/')
    parser.add_argument('--runs', type=int, default=2, help='runs per variant')
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
    workdir = Path(tempfile.mkdtemp(prefix=f'kagestack-eval-{args.name}-'))
    base = (
        ('before', plugin_at(args.against, workdir))
        if args.against
        else ('baseline', None)
    )
    variants = [base, ('kagestack', REPO)]
    runs = []
    for label, plugin in variants:
        for i in range(1, args.runs + 1):
            root = workdir / f'{label}-{i}'
            run = Run(label, root / 'repo', root / 'out', root / 'transcript.jsonl')
            run.out.mkdir(parents=True)
            build_repo(eval_dir, spec, run.repo)
            runs.append((run, plugin))
    print(f'{len(runs)} runs in {workdir} (ง •̀_•́)ง')
    with ThreadPoolExecutor(max_workers=len(runs)) as pool:
        list(pool.map(lambda job: launch(eval_dir, spec, *job), runs))
    report(eval_dir, spec, [run for run, _ in runs])
    print('done (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧')


if __name__ == '__main__':
    main()

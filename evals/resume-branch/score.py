import runpy
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HIDDEN = runpy.run_path(str(HERE / 'hidden_tests.py'))
MOVE = 'Store shipping amounts in cents'


def passes(work, module):
    return (
        subprocess.run(
            ['python3', '-m', 'unittest', '-q', module],
            cwd=work,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def score(run):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / 'w'
        shutil.copytree(
            run.repo, work, ignore=shutil.ignore_patterns('.git', '__pycache__')
        )
        shutil.rmtree(work / 'tests', ignore_errors=True)
        (work / 'tests').mkdir()
        (work / 'tests' / '__init__.py').write_text('')
        with run.tree('main', git_dir=run.origin) as main:
            shutil.copy(
                main / 'tests' / 'test_shipping.py', work / 'tests' / 'test_shipping.py'
            )
        (work / 'tests' / 'test_h_many.py').write_text(HIDDEN['MANY'])
        (work / 'tests' / 'test_h_csv.py').write_text(HIDDEN['CSV'])
        facts = {
            'main tests pass': passes(work, 'tests.test_shipping'),
            'many in cents': passes(work, 'tests.test_h_many'),
            'csv in dollars': passes(work, 'tests.test_h_csv'),
        }
    subjects = run.git('log', 'main', '--format=%s', git_dir=run.origin).splitlines()
    facts['remote main untouched'] = bool(subjects) and subjects[0] == MOVE
    return facts

import subprocess
import sys
from pathlib import Path

KS = Path(sys.executable).parent / 'ks'


def test_ks_names_itself_in_its_version_line():
    shown = subprocess.run([KS, '--version'], capture_output=True, text=True, check=True)

    assert shown.stdout.startswith('kagestack ')

import json
import os
import shutil
import subprocess
import sys


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    path = (event.get('tool_input') or {}).get('file_path') or ''
    uv = shutil.which('uv')
    if not uv or not os.path.isfile(path):
        return
    command = [uv, 'run', '--quiet', '--frozen', '--project']
    command += [os.environ['CLAUDE_PLUGIN_ROOT'], 'ks', 'check', path]
    found = subprocess.run(
        command, cwd=os.path.dirname(path), capture_output=True, text=True
    )
    if found.returncode == 1:
        print(json.dumps({'decision': 'block', 'reason': found.stdout.strip()}))


main()

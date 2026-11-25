import argparse
import importlib.metadata
import subprocess
import sys

from ks.check import check, ci
from ks.doctor import doctor
from ks.githook import git_hook
from ks.package import package
from ks.screens import add_arguments as add_screen_arguments
from ks.screens import screens
from ks.setup import ManifestError, setup
from ks.tools import tools


def add_scope(command):
    scope = command.add_mutually_exclusive_group()
    scope.add_argument(
        '--all', action='store_true', help='report every comment, not only new ones'
    )
    scope.add_argument(
        '--base', help='count lines added since this ref (default: the main branch)'
    )
    return scope


def main():
    parser = argparse.ArgumentParser(
        prog='ks',
        description='checks and playbooks that keep coding agents writing clean code',
    )
    version = importlib.metadata.version('kagestack')
    parser.add_argument('--version', action='version', version=f'ks {version}')
    commands = parser.add_subparsers(
        title='commands', metavar='<command>', required=True
    )

    def command(name, run, summary):
        parsed = commands.add_parser(name, help=summary, description=summary)
        parsed.set_defaults(run=run)
        return parsed

    setup_command = command(
        'setup', setup, 'write kagestack.toml and a CI job pinned to this release'
    )
    setup_command.add_argument(
        '--yes', action='store_true', help='write without asking'
    )
    setup_command.add_argument(
        '--pin', metavar='COMMIT', help='kagestack commit for CI to run'
    )
    ci_command = command('ci', ci, 'run the kagestack.toml commands, then ks check')
    add_scope(ci_command)
    ci_command.set_defaults(paths=[], staged=False)
    check_command = command('check', check, 'fail on comments this branch added')
    add_scope(check_command).add_argument(
        '--staged', action='store_true', help='check only what the next commit holds'
    )
    check_command.add_argument('paths', nargs='*', help='check only these files')
    command('doctor', doctor, "check this repo's ks setup")
    command('git-hook', git_hook, 'run ks check on every commit, in every repo')
    command(
        'package',
        package,
        'write the playbooks to .agents/skills for codex and opencode',
    ).add_argument('--check', action='store_true', help='fail if they are stale')
    command('tools', tools, 'name faster, maintained replacements for old dev tools')
    add_screen_arguments(
        command(
            'screens',
            screens,
            'screenshot a page on phones and desktops in every browser engine, and list its layout and console problems',
        )
    )
    args = parser.parse_args()
    try:
        return args.run(args)
    except subprocess.CalledProcessError as error:
        reason = error.stderr.strip() or f'{" ".join(error.cmd[:2])} failed'
        print(f'ks: {reason}', file=sys.stderr)
        return 2
    except ManifestError as error:
        print(f'ks: {error}', file=sys.stderr)
        return 2

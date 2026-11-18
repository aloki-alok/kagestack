# kagestack

checks and playbooks so coding agents write clean code without babysitting. (｀・ω・´)ゞ

- **playbooks**: one per job (bug fix, feature, refactor, perf, investigate, pr, handoff, scout). every step ends in proof.
- **checks**: `ks check` fails a pull request that adds comments to code.

## does it help

agents with kagestack leave tests that prove the change, and agents without it mostly don't. the code itself comes out equally correct, and a run costs about 1.5x as much. three blind evals, 238 runs: [results](evals/RESULTS.md).

## install

in claude code:

```
/plugin marketplace add aloki-alok/kagestack
/plugin install kagestack@kagestack
```

the checks, as a command line tool (python 3.11 or later):

```
uv tool install git+https://github.com/aloki-alok/kagestack
```

## ks setup

```
uvx --from git+https://github.com/aloki-alok/kagestack ks setup
```

writes `kagestack.toml` with the install, lint and test commands it finds in your repo, and a CI job pinned to this release. it shows both files and asks first. it never guesses a test command: if it finds none, you fill it in.

`ks ci` runs those commands in order, then `ks check`. that is the CI job.

`ks doctor` says whether the manifest is complete and whether CI runs a current release.

## playbooks load on their own

each claude code session starts with a short map from kinds of task to playbooks, so claude loads `kagestack:bug-fix` for a bug without being asked.

## review when a turn ends

in an interactive claude code session, when a turn ends with new commits, a fresh agent reviews those commits once. claude fixes what it confirms before the turn ends. `claude -p` runs skip the review. `KS_REVIEW=0` turns it off, and `KS_REVIEW=1` turns it on where claude code can't tell whether the session is interactive.

## codex and opencode

```
uvx --from git+https://github.com/aloki-alok/kagestack ks package
```

writes the playbooks to `.agents/skills`, where codex and opencode find them. `ks package --check` fails when they are stale.

## ks check

fails on comments in python, js, jsx, ts and tsx, docstrings included. tool directives like `noqa`, `eslint-disable` and `@ts-expect-error` pass.

it checks only lines your branch added since it left main, so an old repo can start today. a comment you moved or kept on a changed line is not new. `--all` checks every line, `--base <ref>` picks the starting point.

put the why in a name, a test, or the commit message.

## ks tools

names older tools in a repo and the faster, maintained option for each, like eslint → oxlint or pip → uv. the list is dated. the `scout` playbook rechecks it.

## how it stays honest

1. highest level that works: structure, then a check, then a test. prose is last.
2. a mistake that comes back becomes a check.
3. every playbook change is tested against plain claude before it ships: `python3 evals/run.py <job>`.

## license

[MIT](LICENSE)

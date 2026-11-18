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

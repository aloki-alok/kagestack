# kagestack

checks and skills so coding agents write clean code.

## what it's for

building features and fixing bugs with agents, cleanly, without babysitting them.

## what's in it

- playbooks: how a job gets done. one per job, every step ends in proof.
- checks: what stops a known mistake.

## how it heals

- a check fails: the agent fixes it and proves the fix. still stuck, a fresh agent takes over.
- a mistake comes back: it becomes a new check, so it can't happen again.

## rules for everything here

1. highest level that works: structure, then a check, then a test. prose is last.
2. every rule names what enforces it.
3. nothing loads into a session unless a task needs it.
4. this repo passes its own checks.

## install

in claude code:

```
/plugin marketplace add aloki-alok/kagestack
/plugin install kagestack@kagestack
```

to get new versions when they land, turn on auto-update: `/plugin`, marketplaces, kagestack.

## ks

the checks as a command line tool. needs python 3.11 or later.

```
uv tool install git+https://github.com/aloki-alok/kagestack
```

`ks check` fails on comments in code: python, js, jsx, ts and tsx. docstrings count. tool directives like `noqa`, `eslint-disable` and `@ts-expect-error` pass, because tools read them, not people.

it checks only lines added since your branch left main, so an old repo can start today. `--base <ref>` picks another starting point. `--all` checks every line.

each hit prints as `path:line: text`. put the why in a name, a test, or the commit message.

## evals

every playbook change is tried on a small task first, against no kagestack or an older version:

```
python3 evals/run.py pr
python3 evals/run.py feature-flags --against <ref>
```

scoring is plain code: what the agent ran, what it made, whether the tests pass. no model judges. each run costs real model time, about $0.50 to $1.50.

## status

early. so far: the `bug-fix`, `feature`, `refactor`, `investigate`, `perf`, `eval`, `handoff` and `pr` playbooks, the principles they follow, worker rules every subagent gets when it starts, and `ks check`.

## license

[MIT](LICENSE)

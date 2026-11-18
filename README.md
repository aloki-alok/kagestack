# kagestack

checks and skills so coding agents write clean code. (｀・ω・´)ゞ

## what it's for

building features and fixing bugs with agents, cleanly, without babysitting them.

## what's in it

- playbooks: how a job gets done. one per job, every step ends in proof.
- checks: what stops a known mistake.

## how it heals

- a check fails: the agent fixes it and proves the fix. still stuck, a fresh agent takes over. ٩(ˊᗜˋ*)و
- a mistake comes back: it becomes a new check, so it can't happen again.

## rules for everything here

1. highest level that works: structure, then a check, then a test. prose is last.
2. every rule names what enforces it.
3. nothing loads into a session unless a task needs it.
4. this repo passes its own checks.

## what enforces what

| rule | enforced by |
|---|---|
| no comments in code | `ks check`, in CI on every pull request |
| worker rules reach every subagent | the `SubagentStart` hook |
| principles | the playbooks that load them |

## does it help

the same model on the same clean setup (no personal config, no MCP servers), with and without the plugin, 5 runs each. each task hides a trap. scoring is plain code that checks the outcome, never whether a playbook step was followed. a win needs a gap of 4 runs or more.

| playbook | trap | with kagestack | without | verdict | cost per run |
|---|---|---|---|---|---|
| `bug-fix` | the bug sits in a helper two pages share | both pages fixed 5/5 | 0/5, found the cause and asked first | win | $0.21 vs $0.13 |
| `pr` | the team template lives in the org's `.github` repo | template filled 5/5 | 0/5 | win, tuned on this task | $0.24 vs $0.10 |
| `handoff` | stop mid-task, context only in the prompt, a token in an untracked `.env` | pushed with the full note 5/5 | 2/5 | tie, tuned on this task | $0.12 vs $0.13 |
| `investigate` | the question has a wrong premise | right reason 5/5 | 5/5 | tie | $0.11 vs $0.09 |
| `refactor` | a "dead" function is called by name from config | behavior kept 5/5 | 5/5 | tie | $0.29 vs $0.11 |
| `perf` | the obvious N+1 query is 2% of the time | 45x faster | 95x faster, also fixed the N+1 in 4/5 | loss | $0.24 vs $0.18 |
| `feature` | a morning job undoes a naive pause | works 5/5 | 5/5 | tie | $0.59 vs $0.13 |

rerun a row with `python3 evals/run.py <folder>` (`bug-fix`, `pr`, `handoff`, `investigate`, `refactor`, `perf`, `feature-flags`). measured 2026-11-18. "tuned on this task" means the playbook was fixed after reading this task's runs, so it still needs a second task.

not shipped: `babysit`. `evals/babysit` showed no win over a plain agent yet.

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

scoring is plain code: what the agent made and whether it works. no model judges. each run costs real model time, about $0.15 to $0.60.

## status

early (・ω・). so far: the `bug-fix`, `feature`, `refactor`, `investigate`, `perf`, `eval`, `handoff` and `pr` playbooks, the principles they follow, worker rules every subagent gets when it starts, and `ks check`.

## license

[MIT](LICENSE)

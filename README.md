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

### blind eval (the one to trust)

a fresh agent that never saw this repo built its own tasks and hidden tests. it was told only what the plugin is for and how to load it, and it ran Claude Opus 5.5 with and without the plugin on a clean setup. 2026-11-18, about $16.

| job | runs per side | hidden tests passed | verdict |
|---|---|---|---|
| bug fix | 10 | 10/10 vs 10/10 | hurts: the smaller fix changed the bad-input error in 8/10 runs vs 2/10 |
| refactor | 5 | 5/5 vs 5/5 | helps: adds tests that lock behavior first, 5/5 vs 0/5 |
| feature | 5 | 5/5 vs 5/5 | helps a little: more tests, judge preferred it 8 to 2 |
| perf, investigate, handoff, a second bug | 4 to 5 | all equal | no difference |

the plugin cost 1.4 to 2x as much per run. the tasks were small, so both sides hit the ceiling on correctness. `bug-fix` now keeps the errors and return types callers rely on, and still needs a new blind eval.

### author-built eval

written by the plugin's author, so read it as a regression check. 5 runs per side, clean setup, outcome checks only.

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

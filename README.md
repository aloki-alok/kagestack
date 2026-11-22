# kagestack

checks and playbooks so coding agents write clean code without babysitting. (｀・ω・´)ゞ

- **playbooks**: one per job (bug fix, feature, refactor, clear comments, perf, investigate, explain, pr, handoff, scout). every step ends in proof.
- **checks**: `ks check` fails a pull request that adds comments to code, or a suppression that names no rule.

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

## decides instead of asking

if a reply ends with a question you'd just say yes to, claude goes back, does it, and lists what it decided. it still asks before deploys, production writes, money, migrations, deletes and messages to people. `KS_DECIDE=0` turns it off.

## codex and opencode

```
uvx --from git+https://github.com/aloki-alok/kagestack ks package
```

writes the playbooks to `.agents/skills`, where codex and opencode find them. `ks package --check` fails when they are stale.

## ks check

fails on comments in python, js, jsx, ts and tsx, docstrings included. tool directives that name their rule pass, like `noqa: F401`, `type: ignore[assignment]`, `eslint-disable-next-line no-undef` and `@ts-expect-error`. a bare `noqa`, `type: ignore`, `pyright: ignore`, `eslint-disable`, `@ts-ignore` or `@ts-nocheck` fails, because it silences the checks that catch real bugs too.

it checks only lines your branch added since it left main, so an old repo can start today. a comment you moved or kept on a changed line is not new. `--all` checks every line, `--base <ref>` picks the starting point.

put the why in a name, a test, or the commit message.

in claude code it also runs on each file claude edits, so a new comment goes back to claude in the same turn. it needs `uv` on the path. `ks check <file>` checks only that file.

## clear old comments

`kagestack:clear-comments` hands the comments in the code you changed to a reviewer agent that didn't write them. each comment gets a verdict: delete it, change the code so it says the same thing (or open an issue when that change is too big), move a real decision into an ADR, turn its rule into a test, or keep it with proof (a license, docs for an outside caller, a vendor quirk). `ks check --all` counts the comments and lines first, so you know the size of the job.

## ks tools

names older tools in a repo and the faster, maintained option for each, like eslint → oxlint or pip → uv. the list is dated. the `scout` playbook rechecks it.

## ks screens

```
ks screens localhost:3000 --screens iphone,android
```

opens a page (a url, a host, or an html file) on 7 screens: iphone (webkit), android (chromium), firefox at phone width, ipad, and desktop chrome, safari and firefox. it saves a screenshot of each and lists what's broken: sideways scroll and the elements that cause it, a missing viewport tag, http errors, uncaught errors, console errors. exit 1 means problems.

`--full` captures the whole page, `--out <folder>` picks where screenshots go. the first run pulls playwright through uv and downloads the browsers once.

webkit at iphone size is close to safari on ios for layout, not the same. ios-only bugs (the toolbar jumping `100vh`, safe areas, inputs that zoom) need the ios simulator.

## how it stays honest

1. highest level that works: structure, then a check, then a test. prose is last.
2. a mistake that comes back becomes a check.
3. every playbook change is tested against plain claude before it ships: `python3 evals/run.py <job>`.

## license

[MIT](LICENSE)

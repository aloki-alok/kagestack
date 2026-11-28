# kagestack

checks and playbooks so coding agents write clean code without babysitting. (｀・ω・´)ゞ

how it works, and why each release shipped: [aloki-alok.github.io/kagestack](https://aloki-alok.github.io/kagestack/).

- **playbooks**: one per job (bug fix, feature, refactor, garden, clear comments, perf, investigate, explain, pr, handoff, scout, interrogate, decision log, catch up). every step ends in proof.
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

fails on comments in python, js, jsx, ts, tsx, yaml, css and shell scripts, docstrings included. tool directives that name their rule pass, like `noqa: F401`, `type: ignore[assignment]`, `eslint-disable-next-line no-undef`, `oxlint-disable-next-line no-console`, `@ts-expect-error`, `shellcheck disable=SC2086` and `stylelint-disable-next-line color-no-hex`. a bare `noqa`, `type: ignore`, `pyright: ignore`, `eslint-disable`, `oxlint-disable`, `@ts-ignore` or `@ts-nocheck` fails, because it silences the checks that catch real bugs too.

it also fails on five kinds of new mess:

- a skipped or focused test: `@pytest.mark.skip`, `unittest.skip`, `it.skip(...)`, `it.only(...)`, `xit(...)` and the like. a conditional skip like `skipif` passes. fix the test or the code, or delete a test that no longer applies.
- a function this change pushes past 60 lines. a function that was already longer can still change or move to another file, so a small fix in old code is not blocked. a `describe` block counts as a list of tests, not a function.
- a swallowed error: `except: ...` with no type, `except X: pass`, an empty `catch {}`, or `.catch(() => {})`. catch the error you expect and handle it, or give the handler a name that says why it is safe to drop.
- an `any` type in typescript. `any` inside a generic constraint, like `T extends (...args: any[]) => unknown`, passes.
- a block nested 4 deep inside one function: `if`, loops, `try`, `with`, `match` and `switch` count. an `else if` chain counts as one level, and a function inside starts again at zero. adding a line inside an old deep block passes.

it checks only lines your branch added since it left main, so an old repo can start today. a comment you moved or kept on a changed line is not new. minified files (a line over 10,000 characters) are skipped. `--all` checks every line, `--base <ref>` picks the starting point.

put the why in a name, a test, or the commit message.

## ks git-hook

makes every commit in every repo on this machine run `ks check` on the lines it adds. merges and cherry-picks are skipped. it works the same for claude code, codex, opencode, cursor and people, since they all commit through git. each repo's own hooks still run after it. a repo with its own hooks folder (husky) skips it, so add `ks check --staged` to that repo's pre-commit.

an agent that can run a command after each edit gets the check sooner, on the file it just changed: `ks check <file>`. the claude code plugin does this.

## clear old comments

`kagestack:clear-comments` hands the comments in the code you changed to a reviewer agent that didn't write them. each comment gets a verdict: delete it, change the code so it says the same thing (or open an issue when that change is too big), move a real decision into an ADR, turn its rule into a test, or keep it with proof (a license, docs for an outside caller, a vendor quirk). `ks check --all` counts the comments and lines first, so you know the size of the job.

## ks stuck

`ks stuck` lists your open pull requests that can't move and your open sprints, and says who moves each one next.

```
ks stuck --org acme
```

a conflict, a red check or a requested change goes to an agent. a missing approval, a draft or a `hold` label waits for a person. after 14 idle days a person decides, so an agent never revives work that may be dead.

a sprint is a milestone named `Sprint N: <outcome>`, and the `feature` playbook opens one for work bigger than one pull request. sprints run in number order, so the lowest open one is current and later ones wait their turn. the current sprint hands its most urgent issue with no pull request to an agent. a sprint with every issue closed waits for a person to check the deploy and close it. a title like `Phone sprint 2` is its own series.

## ks pr-watch

`ks pr-watch` waits on one pull request and exits at its next event, printing only what needs doing:

```
ks pr-watch 12
```

| it prints | exit |
|---|---|
| `conflict: rebase <branch> on <base>` | 1 |
| `new review comments: N`, then one line each: who, file:line, comment id, text | 1 |
| `failed: <checks>`, then the first error block and the closing summary of each failed run's log | 1 |
| `checks green, ready to merge` or `checks green, waiting on review` | 0 |
| `merged: <url>` or `closed: <url>` | 0 |
| `still waiting on: <checks>` after `--timeout` (30 minutes) | 3 |

it reports each review comment once, so starting it again after a reply waits for the next event. an agent runs it in the background, so waiting costs no tokens. the plugin sends a foreground run to the background.

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

# eval results

runs use no personal settings, memory or connectors on either side.

the runs below, all before 2026-11-19, also loaded the author's personal instruction files on both sides: `--setting-sources` does not keep out `~/.claude/CLAUDE.md` or `~/.claude/rules`. those files ask for tests first, so "without" was not plain claude. `run.py` now excludes them.

## blind evals

a fresh agent that never read this repo built the tasks and hidden tests. it was told only what the plugin is for and how to load it.

| date | model | runs | hidden tests, with vs without | tests that catch the change | cost |
|---|---|---|---|---|---|
| 2026-11-18 | Sonnet 5.5, Haiku 5.5 | 80 | 39/40 vs 37/40 | refactor 5/5 vs 0/5, bug fix 5/5 vs 3/5 (Sonnet) | 1.4x |
| 2026-11-18 | Sonnet 5.5 | 80 | 24/40 vs 28/40 | bug fix 39/40 vs 8/40 | 1.6x |
| 2026-11-18 | Opus 5.5 | 78 | equal on every job | refactor 5/5 vs 0/5 | 1.4 to 2x |
| 2026-11-21 | Sonnet 5.5 | 20 | `explain`: all decisions and key facts kept 10/10 vs 10/10 | short page 9/10 vs 0/10 (median 284 vs 1,310 words), one diagram 4/10 vs 0/10 | 1.0 to 1.5x |
| 2026-11-21 | Sonnet 5.5 | 10 | `explain` rows vs 0.24.0: all items kept 5/5 vs 5/5 | outcome phrase on 80% of rows 5/5 vs 0/5, rows of 30 words or fewer 5/5 vs 3/5 | 1.06x |

what changed after each:
- the first one found `bug-fix` changed the bad-input error in 8/10 runs. the playbook now keeps what callers rely on.
- the second found the fix stopped short: BOM fixed, CRLF left, in 6/6 runs. the principle became "fix every form of the fault".
- the third found that loss gone. 76 of 80 runs scored 100%, so these tasks are too small to show a correctness win. Haiku used a skill in 1 of 20 runs.
- the fourth found `explain` pages still put up to 17 labels in a diagram and once skipped looking at the render. a check is the next step, not more text.
- the fifth found two rows of five still added a reasoning line ("Pick: Later, real demand, but..."), and one outcome overclaimed a local measurement as the user's result.

## author-built evals

written by the plugin's author, so read them as regression checks. 5 runs per side.

| playbook | trap | with kagestack | without |
|---|---|---|---|
| `bug-fix` | the bug sits in a helper two pages share | both pages fixed 5/5 | 0/5 |
| `pr` | the team template lives in the org's `.github` repo | filled 5/5 | 0/5 |
| `handoff` | stop mid-task, a token in an untracked `.env` | pushed with the note 5/5 | 2/5 |
| `investigate` | the question has a wrong premise | 5/5 | 5/5 |
| `refactor` | a "dead" function is called by name from config | 5/5 | 5/5 |
| `perf` | the obvious N+1 query is 2% of the time | 45x faster | 95x faster |
| `feature-flags` | a morning job undoes a naive pause | 5/5 | 5/5 |

`pr` and `handoff` were fixed after reading these runs, so they still need a second task. rerun a row with `python3 evals/run.py <folder>`.

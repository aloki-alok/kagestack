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
| 2026-11-21 | Sonnet 5.5 | 10 | `explain` opened rows vs rows only: all tickets and locations kept 5/5 vs 5/5 | Now and Fix steps 5/5 vs 0/5, words per opened row 27 vs 75 | 1.0x |
| 2026-11-21 | Sonnet 5.5 | 10 | `explain` no dropdowns vs 0.24.0: cause, fix and feature visible 4/5 vs 3/5 | nothing hidden 5/5 vs 0/5, no ticket ids or file paths 5/5 vs 0/5, median 172 vs 255 words | 1.0x |
| 2026-11-21 | Sonnet 5.5 | 10 | `explain` form per item vs no-dropdown version: no code names 5/5 vs 5/5 | screen changes as mocks 5/5 vs 0/5, real numbers kept and gaps marked 5/5 vs 0/5, no arrow chains 5/5 vs 0/5 | 1.09x |
| 2026-11-21 | Sonnet 5.5 | 10 | `explain` concept pages built up in steps vs form per item: pictures built up 0/5 vs 0/5 | plain definition first 2/5 vs 0/5, median 850 vs 237 words | 1.4x, not shipped |
| 2026-11-24 | Sonnet 5.5 | 30 | session text that reads the ask first vs 0.29.0: right fix or cause 10/10 vs 10/10, no added work 14/15 vs 13/15 | named its reading 5/10 vs 6/10, expert word glossed 9/10 vs 9/10, raw log quoted 4/5 vs 5/5 | 1.0x, not shipped |
| 2026-11-24 | Sonnet 5.5 | 20 | `garden` vs 0.29.0, asks that name the mistake (money math, timezones): guard catches the old bugs 10/10 vs 10/10, live bugs fixed 10/10 vs 10/10 | cites 2 past fixes 8/10 vs 3/10 | 1.0x |
| 2026-11-24 | Sonnet 5.5 | 20 | `garden` vs 0.29.0, asks that don't name it: "keeps breaking in the same ways" guard catches the old bugs 5/5 vs 2/5, nothing else touched 5/5 vs 3/5; "the old code here is bad" 0/5 vs 0/5 | cites 2 past fixes 5/5 vs 0/5 | 1.16x |
| 2026-11-26 | Sonnet 5.5 | 10 | `bug-fix` that bisects a regression vs 0.35.1 (`regression-cause`): cause fixed 5/5 vs 5/5, decoy kept 5/5 vs 5/5, callers unchanged 5/5 vs 5/5 | none | 0.8x, not shipped |
| 2026-11-26 | Sonnet 5.5 | 10 | same, 27 commits, cause in commit 15, no hint (`regression-cause-hard`): cause fixed 5/5 vs 5/5, retries ignored 5/5 vs 5/5, reminder rules kept 5/5 vs 5/5 | none | 1.04x, not shipped |
| 2026-11-26 | Sonnet 5.5 | 10 | `perf` that reverts changes inside the spread and checks the timed part vs 0.35.1 (`honest-speedup`): 3x faster 5/5 vs 5/5, same output 5/5 vs 5/5, no idle edits 5/5 vs 5/5, honest claim 4/5 vs 5/5 (the miss was the scorer's) | none | 1.1x, not shipped |
| 2026-11-26 | Sonnet 5.5 | 10 | `handoff` with a pick-up half vs 0.35.1 (`resume-branch`): main's tests 5/5 vs 5/5, prices in cents 5/5 vs 5/5, csv right 5/5 vs 5/5 | none | 1.0x, not shipped |
| 2026-11-26 | Sonnet 5.5 | 10 | same, the stale claim hidden behind a clean merge and green tests (`resume-branch-hard`): surcharge carried 5/5 vs 4/5 (the miss renamed the function), csv matches checkout 5/5 vs 5/5 | none | 1.0x, not shipped |
| 2026-11-27 | Sonnet 5.5 | 20 | `ui` playbook vs 0.36.0, tasks with a sibling to copy (mobile nav, card grid): keyboard 5/5 vs 5/5, reduced motion 10/10 vs 10/10, no sideways scroll 10/10 vs 10/10, tokens 10/10 vs 10/10 | hover not stuck after tap 5/5 vs 5/5 | 2.2 to 2.6x, not shipped |
| 2026-11-27 | Sonnet 5.5 | 20 | same, no sibling (demo modal, Monthly/Yearly switch): focus trap 5/5 vs 5/5, keyboard and state 5/5 vs 5/5, fits a phone 5/5 vs 5/5, tokens 10/10 vs 10/10 | reduced motion on the modal 5/5 vs 5/5 and on the switch 3/5 vs 5/5, indicator aligned after resize 5/5 vs 5/5 | 2.1 to 3.7x, not shipped |

what changed after each:
- the first one found `bug-fix` changed the bad-input error in 8/10 runs. the playbook now keeps what callers rely on.
- the second found the fix stopped short: BOM fixed, CRLF left, in 6/6 runs. the principle became "fix every form of the fault".
- the third found that loss gone. 76 of 80 runs scored 100%, so these tasks are too small to show a correctness win. Haiku used a skill in 1 of 20 runs.
- the fourth found `explain` pages still put up to 17 labels in a diagram and once skipped looking at the render. a check is the next step, not more text.
- the fifth found two rows of five still added a reasoning line ("Pick: Later, real demand, but..."), and one outcome overclaimed a local measurement as the user's result.
- the sixth found one run of five still put a sentence above the steps, and code locations ran together with no label.
- the seventh found one page of five gave the bug's cause only as an arrow chain, never as a sentence. the next change picks each item's form from its content instead of one template.
- the eighth found raw codes inside a "today" mock, numbers left as plain text, and "no number" repeated on every card. the next change draws every number, keeps mocks to what the user reads, and shapes concept and comparison pages too.
- the ninth found that change made no picture series in any run and let concept pages grow to 850 words. reverted. building pictures up needs a tool or a check, not a sentence.
- the tenth tied on every outcome: sonnet already picks the likely job and keeps scope on these asks. 8 of 10 runs read "see how we can reuse" as asking for advice, not a build. a retest needs real past asks that agents got wrong.
- the eleventh and twelfth shipped `garden` on its unnamed-mistake win. "the old code here is bad" went to `refactor` in all 10 runs, and none read the history, so that wording is not garden's yet.
- the last five tested lessons from pstack, the Cursor skill pack, and all tied: sonnet already found the real cause, reverted idle tweaks and caught the stale note in 50 of 50 runs on both sides. none shipped. a retest needs a cause that history and grep can't reach, such as one only a failing end-to-end run shows.
- the `ui` rows tied on every outcome but reduced motion on the switch. without the playbook, sonnet already used the project's tokens in 20 of 20 runs and gated hover in 5 of 5. it built a native `<dialog>` and a radio switch unasked. both sides looked at the page, 39 of 40 runs in all. the playbook's extra polish added price motion that ignored reduced motion in 2 of 5 runs. its patterns stay in the author's personal rules. a retest needs an outcome code can see that sonnet misses, such as motion that runs under reduced motion or a first-paint slide.

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

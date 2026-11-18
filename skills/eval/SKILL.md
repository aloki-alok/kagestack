---
name: eval
description: Test whether a skill, playbook, prompt or rule change makes agents better, before shipping it. Use when adding or changing a skill, comparing skills that do the same job, or checking that a rule is followed.
---

# Eval

Read `${CLAUDE_PLUGIN_ROOT}/principles.md` before step 1.

## Who builds the test

If you wrote or changed the thing under test, a fresh agent designs and runs the whole eval blind. You only write its brief and read its report.
- The brief holds: the goal in user terms, the thing's one-line purpose, how to run with it and without it, machine facts it can't find by looking, a budget and its own folder.
- The brief leaves out: the source, the existing evals and results, your hunches and any method. It forbids reading the thing's files.
- A change made after reading its report gets a new blind eval, not the same tasks.

Use the steps below only when the thing can't run as a black box, or to rerun an existing task as a regression check. Label those results author-built.

## Author-built evals

An agent that knows it is being tested behaves differently, so the task must look real.

1. **Write what winning means** before running anything: two to four outcomes a user would check, such as the bug gone, the page faster by the scorer's own clock, or the secret left out of the push. A fact that restates a playbook step only proves the agent read the playbook.
   Done when each fact is checkable by code.
2. **Build the task** as a folder in `evals/`, copying the nearest one: `repo/` holds the files, `eval.json` the prompt, skill and remote, `setup.sh` the git history, `score.py` the facts from step 1. A task that needs GitHub gets `issues.json` or `org-template.md`.
   The world must hold up when the agent looks around: a GitHub remote it can push to, no words like test, eval or candidate, and a trap only where you mean one.
   Done when a scripted good run passes every fact and a scripted bad run fails them.
3. **Run it:** `python3 evals/run.py <name>` compares against no kagestack. `--against <ref>` compares against an older kagestack. Each variant runs five times, in parallel and headless.
4. **Read the runs that lost** before you trust the table. A run that failed for a setup reason, such as a push that could not work, is a bug in the eval. Fix the eval, then rerun, or use `--score <dir>` when only `score.py` changed.
5. **Decide.** Ship only if the variant wins on a fact from step 1 by at least 4 of 5 runs. A smaller gap is a tie. Same result for more cost: do not ship. A change made after reading a task's runs is judged on a second task, not the one that found the problem.

## Reply

The results table, blind or author-built, the decision, and the one fact it rests on.

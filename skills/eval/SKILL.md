---
name: eval
description: Test whether a skill, playbook, prompt or rule change makes agents better, before shipping it. Use when adding or changing a skill, comparing skills that do the same job, or checking that a rule is followed.
---

# Eval

Read `${CLAUDE_PLUGIN_ROOT}/principles.md` before step 1.

An agent that knows it is being tested behaves differently, so the task must look real.

1. **Write what winning means** before running anything: two to four facts you can check in the output, such as a trap avoided, a step done, or a file left working.
   Done when each fact is checkable by code.
2. **Build the task** as a folder in `evals/`, copying the nearest one: `repo/` holds the files, `eval.json` the prompt, skill, pointer and remote, `setup.sh` the git history, `score.py` the facts from step 1. A task that needs GitHub gets `issues.json` or `org-template.md`.
   The world must hold up when the agent looks around: a GitHub remote it can push to, no words like test, eval or candidate, and a trap only where you mean one.
   Done when you have run the trap yourself and know the right answer.
3. **Run it:** `python3 evals/run.py <name>` compares against no kagestack. `--against <ref>` compares against an older kagestack. Each variant runs twice by default, in parallel and headless.
4. **Read the runs that lost** before you trust the table. A run that failed for a setup reason, such as a push that could not work, is a bug in the eval. Fix the eval, then rerun, or use `--score <dir>` when only `score.py` changed.
5. **Decide.** Ship only if the variant wins on a fact from step 1. Same result for more cost: do not ship.

## Reply

The table the runner printed, the decision, and the one fact it rests on.

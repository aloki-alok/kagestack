---
name: eval
description: Test whether a skill, playbook, prompt or rule change makes agents better, before shipping it. Use when adding or changing a skill, comparing skills that do the same job, or checking that a rule is followed.
---

# Eval

Read `${CLAUDE_PLUGIN_ROOT}/principles.md` before step 1.

An agent that knows it is being tested behaves differently, so the task must look real.

1. **Write what winning means** before running anything: two to four facts you can check in the output, such as a trap avoided, a step done, or a file left working.
   Done when each fact is checkable by a command or by reading a diff.
2. **Build the task.** A small repo, or a copy of a real one, with a trap that only the variant should catch. Plain names, no words like test, eval or candidate in any path or prompt the agent sees.
   Done when you have run the trap yourself and know the right answer.
3. **Set up the variants.** The same task, prompt and settings for each. Only the thing under test differs. Switch off any other skill that does the same job.
4. **Run each variant at least twice,** in parallel, each in its own copy, headless. Keep every transcript.
5. **Check it fired.** From the transcript, not the reply: did the skill load, and which steps ran.
   Done when you know the fire rate for each variant.
6. **Score against step 1,** from the diffs, the commands and the transcripts. Add the cost per run.
7. **Decide.** Ship only if the variant wins on a fact from step 1. Same result for more cost: do not ship.

## Reply

A table: each variant against each fact, the fire rate and the cost. Then the decision and the one fact it rests on.

---
name: handoff
description: Pause work so a fresh session can pick it up. Use when stopping mid-task or wrapping up for the day.
---

# Handoff

The branch carries the handoff. The note lives in a commit body, so it travels with the code.

1. **Stop at a safe point.** Finish or back out of the current step. Start nothing new.
2. **Commit everything** as one `wip:` commit on a work branch. If you are on the default branch, create one first. Its body is the note, 10 lines max:
   - the goal, in one line
   - what works, with the command that proves it
   - what was tried and failed, one line each
   - decisions a fresh agent would otherwise undo, with the reason
   - the first next step
   Leave out the session story and anything the diff already shows.
   Done when a fresh agent could start from `git log -1` alone.
3. **Push the branch,** so the next session can fetch it.
   Done when `git ls-remote origin <branch>` shows your commit.

## Reply

Where it stopped, the commit, and the first next step.

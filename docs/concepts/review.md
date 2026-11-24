```mermaid
flowchart TD
  W["Agent commits work"] --> E["Turn ends"]
  E --> R["Fresh reviewer: your request and the commit range, nothing else"]:::check
  R --> F["Findings it proved with a command"]
  F --> FIX["Agent fixes each one with a test"]
  F --> WHY["Or gives a reason to dismiss it"]
  FIX --> DONE["Reply to you"]:::you
  WHY --> DONE
```

# How work gets reviewed

When you write something important, you ask a friend to read it, and you don't hand them your notes first. Same idea here. Every commit an agent makes in a session you watch gets read by a second agent before the turn ends. The reviewer gets your request and the commit range, and none of the first agent's reasoning, so it really does read the work cold.

## What the reviewer looks for

1. Bugs a user would hit: wrong output, a crash, lost data, a security hole, a caller that breaks.
2. Code that already did the job. Two pieces of code for one job is a finding. The fix is to reuse the old code, or to move its callers to the new code and delete the old one.
3. Weak tests. Each new test has to fail when the behavior breaks, and still pass when the code is restructured with the same output.
4. The one fact the change is safe because of, and how far that fact is proven.

It only reports findings it confirmed by running something. Guesses don't count.

## When it runs, and when it doesn't

It runs once per turn that adds commits, after the work rather than alongside it, because it's judging the finished commits. It skips headless runs and turns that still have background work going. There's one gap, though: replies, messages and uncommitted edits get no reviewer at all. `KS_REVIEW=0` turns it off, and `KS_REVIEW=1` turns it on where Claude Code can't tell whether you're watching.

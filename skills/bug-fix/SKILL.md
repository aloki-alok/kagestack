---
name: bug-fix
description: Fix a bug from a red repro to a proven fix. Use when something is broken, failing, or wrong.
---

# Bug fix

Read `${CLAUDE_PLUGIN_ROOT}/principles.md` before step 1.

1. **Get it red.** Build one command that fails on the symptom the user sees, on the real surface. Fast, deterministic, unattended.
   Done when it goes red for that symptom twice in a row. A flaky bug must go red at least half the time.
2. **Find the root cause.** Rank three to five candidate causes. Rule each out with a run or a log line until one survives.
   Done when you can write `Root cause: <X> because <Y>`, where Y is a mechanism you observed.
3. **Fix at the cause.** List every caller of the code you will change. Fix where they all route through.
   Done when every line of the diff is justified by the root-cause line.
4. **Go green.** Rerun the command from step 1.
   Done when it passes, and the tests around the change pass.
5. **Commit red before green.** The failing test lands in its own commit, then the fix.
6. **Close the class.** Search history for the same kind of bug. On its second appearance, add a check that fails on it, in the same PR.

## Symptom fixes

These move the symptom and keep the cause. Each needs the root-cause line to justify it:
a null guard where the crash was, a caught and dropped error, a retry, sleep or longer timeout,
a skipped or weakened test, a special case for the failing input.

## Stuck

- Two fixes failed on one premise: write the premise in one sentence, then run one experiment that comes out differently if it is false.
- Third failure: hand off to a fresh agent with the repro command, the evidence, and the causes ruled out.

## Reply

What the user would see, the root-cause line, the fix, then the red output and the green output pasted.

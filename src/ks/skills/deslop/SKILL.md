---
name: deslop
description: Strip agent slop out of code without changing what it does, after a harsh audit by a reviewer who did not write it. Slop is comments, swallowed errors, guards for states that can't happen, untyped data, deep nesting, one-caller layers and dead code. Use when asked to deslop, clean up, tighten or harshly review code, or after a large agent-written change.
---

# Deslop

Read `${CLAUDE_PLUGIN_ROOT}/src/ks/principles.md` before step 1.

Structure changes. Behavior does not. A bug or a missing feature you find goes to `bug-fix` or `feature` after this ships.

1. **Fix the scope.** The files the user named. Otherwise the lines this branch changed since main.
2. **Pin the behavior.** Find the tests that cover the scope. If breaking the scope's behavior on purpose fails none of them, write one that does first.
   Done when the pin passes now and fails on a deliberate break.
3. **Run the machines.** `ks check` on the scope, then the repo's linter and type checker on the scope's files. Each hit is a finding.
4. **Start the `kagestack:deslop-reviewer` agent** with the scope and the machine hits. It reports and never edits. If your harness has no such agent, start a fresh subagent and give it `${CLAUDE_PLUGIN_ROOT}/src/ks/agents/deslop-reviewer.md` as its brief.
5. **Check the report.** Reject a finding outside the scope, one whose change alters behavior, and one without proof. Rejecting needs a reason.
   Done when each finding is accepted or rejected with a reason.
6. **Delete first,** in its own commit: dead code, comments, guards for states that can't happen.
7. **Reshape in small steps,** one kind of slop per commit: errors, then types, then nesting and layers, then names. The pin stays green after each.
   For comments that record a decision or a rule, follow `clear-comments` steps 5 to 7.
8. **Prove nothing changed.** Run the pin, the repo's tests for the scope, `ks check`, and the type checker. Count before and after: lines, comments, catches, `any` and casts, deepest nesting.

## Reply

One to three lines: what got smaller, with the before and after counts, and the proof. Then each rejected finding and each behavior change the reviewer found, one line each.

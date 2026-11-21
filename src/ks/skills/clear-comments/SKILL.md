---
name: clear-comments
description: Clear comments out of code by making the code say what they said. Use when asked to remove, review or clean up comments or lint suppressions, or when `ks check` fails on them.
---

# Clear comments

Read `${CLAUDE_PLUGIN_ROOT}/src/ks/principles.md` before step 1.

The author of a comment defends it, so a reviewer who didn't write it judges it.

1. **Fix the scope.** The files or range the user named. Otherwise the functions and blocks this branch changed since main. Comments outside the scope stay.
2. **Start the `kagestack:comment-reviewer` agent** with the scope. It reports and never edits. If your harness has no such agent, start a fresh subagent and give it `${CLAUDE_PLUGIN_ROOT}/src/ks/agents/comment-reviewer.md` as its brief.
   Done when every comment in the scope has a verdict.
3. **Check the report.** Reject a flag outside the scope, a flag on code that isn't a comment, and a keep without proof. Turn a rejected keep into delete.
   Done when each verdict is accepted or rejected with a reason.
4. **Delete,** in its own commit.
5. **Reshape.** Make each named change, then delete its comment. Behavior must not change: follow the `refactor` playbook for anything beyond a rename. If a reshape reaches outside the scope, delete the comment and list the reshape as open.
6. **Encode.** Write each named check and watch it fail when you break the rule on purpose. Then delete the comment.
   Done when every encoded rule has a check that went red, then green.
7. **Prove it.** Run `ks check` on the scope and the repo's tests.

## Reply

The counts per verdict, each reshape and check in one line, and what stays open.

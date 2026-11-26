---
name: interrogate
description: Have reviewers on two different models try to break a risky change, and keep only the findings a rerun proves. Use for a diff that touches money, auth, permissions, call dispatch, data writes or a migration, when two reviews disagree, or when asked to interrogate or stress test a change.
---

# Interrogate

Reviewers on one model share its blind spots. A second vendor's model catches different bugs, and a rerun throws out the findings that only sound right.

1. **Fix the scope and the intent.** Commit first: the reviewers read commits. The scope is the range the user named, else the branch since its merge base with main. Write the intent in one sentence from the request, the commits and the PR body.
2. **Give each reviewer its own worktree** at the head: `git worktree add <tmp>/claude HEAD` and `git worktree add <tmp>/codex HEAD`.
3. **Start both reviewers at once, in the background.** Each gets the same brief: read `${CLAUDE_PLUGIN_ROOT}/hooks/review.md` and follow it, the intent, the range, and its worktree as the place to run experiments.
   - A fresh Claude subagent.
   - Codex: `codex exec --ephemeral -s workspace-write -C <tmp>/codex -o <tmp>/codex.md "<brief>"`. Codex sends the code to OpenAI.
   If `codex` is not installed, or the repo's rules keep its code away from other vendors, run the second reviewer as a Claude subagent on another model, and say so.
4. **Rerun every finding's command yourself** in a worktree at the head. Keep a finding when the output shows the failure and the failure breaks the intent. Drop the rest. Merge findings that share a root cause.
   Done when every kept finding has its command and the output you saw.
5. **Remove both worktrees,** and mark the head reviewed so the turn-end review doesn't run a third reviewer: `git rev-parse HEAD > "$(git rev-parse --path-format=absolute --git-path kagestack-reviewed)"`.

Report the findings. The playbook that called this one fixes them.

## Reply

The intent. Each kept finding: the command, its output, how it breaks the intent, and which reviewers found it. For each reviewer, how many findings you dropped and why. "No verified findings" is a valid result.

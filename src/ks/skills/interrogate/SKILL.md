---
name: interrogate
description: Have reviewers on two different models try to break a risky change, and keep only the findings a rerun proves. Use for a diff that touches money, auth, permissions, call dispatch, data writes or a migration, when two reviews disagree, or when asked to interrogate or stress test a change.
---

# Interrogate

Reviewers on one model share its blind spots. A second vendor's model catches different bugs, and a rerun throws out the findings that only sound right.

1. **Fix the scope and the intent.** The scope is the diff the user named, else the branch since its merge base with main, plus uncommitted changes. Write the intent in one sentence from the request, the commits and the PR body.
2. **Give each reviewer its own worktree** at the head: `git worktree add <tmp>/claude HEAD` and `git worktree add <tmp>/codex HEAD`. Copy uncommitted changes into both.
3. **Start both reviewers at once, in the background.** Each gets the same brief: read `${CLAUDE_PLUGIN_ROOT}/hooks/review.md` and follow it, the intent, the range, and its worktree as the place to run experiments.
   - A fresh Claude subagent.
   - Codex: `codex exec --ephemeral -s workspace-write -C <tmp>/codex -o <tmp>/codex.md "<brief>"`.
   If `codex` is not installed, run the second reviewer as a Claude subagent on another model, and say so.
4. **Rerun every finding's command yourself** in a worktree at the head. Keep a finding when the output shows the failure and the failure breaks the intent. Drop the rest. Merge findings that share a root cause.
   Done when every kept finding has its command and the output you saw.
5. **Remove both worktrees.**

Report the findings. The playbook that called this one fixes them.

## Reply

The intent. Each kept finding: the command, its output, how it breaks the intent, and which reviewers found it. For each reviewer, how many findings you dropped and why. "No verified findings" is a valid result.

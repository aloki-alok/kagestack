---
name: garden
description: Find the mistakes a repo keeps repeating and make each one impossible to write again. Use when the same kind of bug keeps coming back, when asked to improve a repo's health, or when the old code is bad and should get better.
---

# Garden

Read `${CLAUDE_PLUGIN_ROOT}/src/ks/principles.md` before step 1.

Fix the kind of mistake, not one more case of it. Each fix is a check that fails on the mistake, so nobody has to remember it.

1. **Read the history.** Read the fix and revert commits with their diffs: `git log -i -E --grep='fix|bug|revert|hotfix' -p -n 200`. If the repo is on GitHub, read review comments on merged pull requests: `gh api 'repos/{owner}/{repo}/pulls/comments?per_page=100'`. Group what you find by the mistake behind it, not by file.
   Done when each mistake cites two or more past commits or comments. Drop the ones seen only once.
2. **Rank them** by how often each came back and what it cost: an outage beats a typo. Take the top three.
3. **Pick the strongest check that holds** for each one, in this order:
   1. A code structure that makes the mistake impossible to write.
   2. A type.
   3. A lint rule whose error message names the fix.
   4. A test.

   Use a line of docs only when none of these can hold, and say why.
4. **Prove each check on the real past mistake.** In a `git worktree` at the commit before a past fix, or with the bad diff applied again, the check must fail. On the current commit, it must pass.
   Done when each check has both runs.
5. **Delete what the check replaces:** comments, docs and review checklist items that asked people to remember the rule. Keep every test that guards security or legal behavior.
6. **Open one pull request per mistake.** Its body lists the past commits and the two proof runs.

## Reply

A table with one row per mistake: what it is, the past commits, the check, the proof (fails at the old commit, passes now), and the pull request. Then each mistake you dropped, with the reason, one line each.

---
name: pr
description: Open a pull request a reviewer can read in a minute. Use when opening a pull request or rewriting its description.
---

# Pull request

1. **Clean the branch.** Only this change, rebased on the base, in small commits that each pass the checks.
   If no test fails without the change, add one that does, as its own commit.
   Done when the repo's checks and tests pass at the last commit.
2. **Title:** `type(scope): subject`, naming the real symbol the change is about.
3. **Find the template.** The repo's own `.github/pull_request_template.md`, else the org default:
   `gh api repos/<owner>/.github/contents/.github/pull_request_template.md --jq .content | base64 -d`.
   Done when you have the template, or both lookups came back empty.
4. **Body.** Fill in the template, keeping its markers. No template: under 40 lines, these headings in order, dropping empty ones:
   - `## Why`: the problem in the user's terms.
   - `## What changed`: the smallest view: a file tree, a call tree or pseudocode.
   - `## Proof`: the command, red before and green after. Link long logs.
   - `## Tradeoffs`: only alternatives a reviewer would ask about.
   - `## Merge danger`: one-way or two-way door, and the widest blast radius.
5. **Open it ready for review,** not as a draft.

## Reply

The link and the merge danger in one line.

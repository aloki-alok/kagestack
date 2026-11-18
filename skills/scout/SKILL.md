---
name: scout
description: Find the modern, faster option before picking or keeping a dev tool or library. Use when choosing a linter, formatter, type checker, package manager, test runner, bundler, git hooks or a library, or when `ks tools` names a swap.
---

# Scout

Five minutes, then a verdict. Newer wins only when it is maintained, adopted and faster on this repo.

1. **Name the job.** One line: "tool X does job Y in language Z." Run `ks tools` first: it names the known swaps.
2. **Find candidates.** Search "<old tool> alternative <this year>" and "<old tool> vs". Keep names that appear on two independent pages.
3. **Check maintenance** with `gh api repos/OWNER/REPO` (archived, license, pushed_at) and `gh api repos/OWNER/REPO/releases/latest`.
   Done when each candidate has its last release date, license and archive status.
4. **Check adoption.** The defaults of the frameworks this repo uses, and the configs of three large repos in the same stack.
5. **Find the gaps.** Read its "differences", "compatibility" or "limitations" page. List the old plugins or rules this repo uses that the new tool lacks.
6. **Stop on a red flag:** no release in 6 months, one maintainer, an unclear license, archived with no successor, or 0.x with no stable API.
7. **Measure on this repo.** Run old and new with `hyperfine`, at least 5 runs, and compare their output.
   Done when you have both medians and the output differences.

## Reply

The verdict per tool (adopt, adopt with the old one kept in CI, or wait), the measured gain on this repo, and the gaps. If the list in `ks tools` is wrong or stale, say which line to change.

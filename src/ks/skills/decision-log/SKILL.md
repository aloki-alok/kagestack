---
name: decision-log
description: Keep a log of each decision in a long or unattended run, with the proof behind it, so a person can trust work they did not watch. Use for work that outlasts one sitting, overnight or loop runs, or when asked to show your work.
---

# Decision log

A person who comes back to a long run trusts it only when each decision points at its proof.

1. **Open the log** at `log=$(git rev-parse --path-format=absolute --git-path kagestack-decisions.tsv 2>/dev/null || echo "$PWD/kagestack-decisions.tsv")`. In a repo it sits inside `.git`, so it is never committed and each worktree keeps its own. On first use, write the header: `time	decision	why	proof	result`.
2. **Add a row at each decision point:** a fork you chose, a step finished with its check, a revert and what set it off, a blocker. Skip routine actions.
   `printf '%s\t%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "<decision>" "<why>" "<proof>" "<result>" >> "$log"`
   - Each cell is one line with no tabs, written the way you would tell a teammate.
   - The proof is a pointer: a commit, a file:line, a command, or the path of a screenshot or log. Never a paragraph.
   - The result is what happened: `tests pass`, `reverted`, `inconclusive`, `open`.
3. **Never edit a row.** A wrong call gets a new row that replaces it and says so.
4. **Audit the log before you hand back.** Walk your rows against what you did. Each proof must open and show what its row claims. A fork or a revert that shaped the work but has no row is a gap: add it now.
   Done when every row's proof resolves and no decision is missing.

## Reply

The log path, the command that prints it as a table (`column -s$'\t' -t <log>`), and the rows a person should check first: reverts, inconclusive results and open blockers.

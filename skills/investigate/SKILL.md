---
name: investigate
description: Answer how something works or why it was built this way, without changing code. Use for how, why, where does this live, are we sure, or what would break questions.
---

# Investigate

Read only. The output is an answer, not a change. If the answer calls for a change, end with it as a next step for `bug-fix`, `feature` or `refactor`.

1. **Restate the question** as one sentence that has a checkable answer.
   Done when you could tell a right answer from a wrong one.
2. **How: trace the real path.** Follow one concrete input through the code, hop by hop, to the output. Run it when you can.
   Done when every hop cites a file:line.
3. **Why: read the record, not the code.** The commits, PRs and issues that introduced the code and each later change to it.
   Done when each reason quotes or links its source. Your own guesses are marked as guesses.
4. **Say what you could not answer,** and what would answer it.

## Reply

The answer first, in one or two sentences. Then the path or the record behind it, with citations.
If the question rests on a wrong premise, say so first.

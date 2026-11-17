---
name: feature
description: Build a new feature or change what the product does. Use when adding, extending, or changing behavior.
---

# Feature

Read `${CLAUDE_PLUGIN_ROOT}/principles.md` before step 1.

1. **Restate.** Write the goal, the smallest change that meets it, and how you will know it works.
   Done when "how you will know" is one outcome a user could observe.
2. **Find what exists.** Search for code that already does this, and for the nearest sibling, then judge it.
   Done when you cite file:line for what exists, or list the searches that found nothing.
3. **Name the data shape.** States, fields, and legal moves between states, before any logic.
   Done when the shape is written down.
4. **Check the consequences.**
   - Every caller of what you change.
   - The one fact the change is safe because of, shown by a run.
   - Where it stops scaling: the limit in real units, and what happens at ten times that.
   Done when all three are written with evidence.
5. **Sign-off on big changes only.** Schema, billing, auth, many modules, or anything one-way: show steps 1 to 4 and wait. Everything else: go on, and show them in the reply.
6. **Build in slices.** Per slice: a failing test for the behavior, the minimal code, the repo's checks pass, one commit.
   Done when every slice is green and committed.
7. **Prove it on the real app.** Drive the feature the way a user does. Save the output or a screenshot.
   Done when the proof comes from the final commit.
8. **Fresh review.** An agent with none of your reasoning reviews the plan and the diff. Fix what it shows with a run.
9. **Flag what you passed.** Bad code you saw and did not fix becomes an issue: what is wrong (file:line), the wrong lesson it teaches the next agent, the right shape, what it touches, and which work found it. Search open issues first. If one covers it, add to that one.
   Done when every flag is a new or updated issue, linked in your reply.

## Reply

What you built, the shape and why, the evidence from steps 2 and 4, the proof, and any open decisions.

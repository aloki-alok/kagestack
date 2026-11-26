---
name: catch-up
description: Tell the user what changed in this session since their last message, and every call that waits on them, so they can decide from the reply alone. Use when they come back to a long run, or ask what happened while they were away.
---

# Catch up

The user remembers their last message and nothing after it. Notifications and subagent reports are not their messages. Keep this turn read only.

1. **Gather what changed:** your work since their last message, subagent reports, and the current state of each pull request, check run and agent this session touched. Check each number against its source.
2. **List the calls that wait on them:** a product choice, an approval, an irreversible step, or access you lack. Include calls raised earlier that are still open. Work you can still do yourself is not a call. Never invent one.
3. **Write it.**
   - Line one names what waits on them, or says nothing does.
   - A picture next, when a change is easier to see than read: a screenshot the work produced, or a diagram of how things now connect, at most six boxes. Never a picture of a status list.
   - One line per thing they asked for: what came of it, and whether it is done, running, failed or not checked. Say it the way you would out loud. Leave out hashes, paths and commands they don't need to act.
   - Each call: the question, your pick, what it changes for users, the evidence, and its risk, even when low. When many items share one call, write the call once, then one line per item, riskiest first.
   Done when they could make every call from the reply alone.

## Reply

Under 100 words for what happened, and about 30 words per call. Never cut a call to fit.

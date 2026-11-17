# kagestack

checks and skills so coding agents write clean code.

## what it's for

building features and fixing bugs with agents, cleanly, without babysitting them.

## what's in it

- playbooks: how a job gets done. one per job, every step ends in proof.
- checks: what stops a known mistake.

## how it heals

- a check fails: the agent fixes it and proves the fix. still stuck, a fresh agent takes over.
- a mistake comes back: it becomes a new check, so it can't happen again.

## rules for everything here

1. highest level that works: structure, then a check, then a test. prose is last.
2. every rule names what enforces it.
3. nothing loads into a session unless a task needs it.
4. this repo passes its own checks.

## install

in claude code:

```
/plugin marketplace add aloki-alok/kagestack
/plugin install kagestack@kagestack
```

## status

early. so far: the `bug-fix` and `feature` playbooks, and worker rules every subagent gets when it starts.

## license

[MIT](LICENSE)

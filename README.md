# kagestack

checks and skills so coding agents write clean code.

agents copy what they see in a repo. so the fix for bad agent code is a better repo, not a longer prompt.

## the bar

nothing gets in unless:

1. it answers a mistake we saw twice.
2. it sits at the highest level that works: structure, then a check, then a test. prose is last.
3. every rule names what enforces it.
4. every check is proven to fail on a real past mistake.
5. nothing loads into a session unless a task needs it.
6. this repo passes its own checks.

## install

in claude code:

```
/plugin marketplace add aloki-alok/kagestack
/plugin install kagestack@kagestack
```

## status

foundation only. skills and checks land one at a time.

## credit

the method is from [poteto](https://x.com/poteto)'s talk "all code is slop (except mine)" and her [pstack](https://github.com/cursor/plugins/tree/main/pstack).

## license

MIT

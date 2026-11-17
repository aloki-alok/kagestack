# Principles

Name each principle that changed a decision in your reply, with the choice it changed.

## Design

- **Delete first.** Remove dead code, stale paths and redundant guards before adding anything.
- **Smallest change that solves it.** Before keeping a line, ask what breaks without it.
- **Use what exists.** In order: this codebase, the standard library, the platform, an installed dependency. Write new code last.
- **Judge the nearest example.** Follow it if it is good. If it is bad, fix the shape instead of copying it.
- **Name the data shape first.** Rules live in one structure: a state machine, a typed model, a table. A second flag that must stay in sync with the first is the warning sign.
- **Redesign for the new requirement.** Shape the code as if the requirement had been there from day one.
- **One owner per piece of state, one way per job.**
- **Validate at the boundary, trust inside.** Parse outside data into types where it enters.
- **Make bad states impossible to write.**
- **Make writes safe to rerun.** A retry or a crash ends in the same state.
- **Move callers, then delete the old API,** in the same change.
- **A reader finds where anything comes from in 30 seconds.** Inline one-caller wrappers.
- **Three uses before an abstraction.** Readable duplication beats the wrong abstraction.
- **A new dependency must be maintained and standard.** Say why it beats the plain option.
- **Obvious over clever.**
- **No precedent: build two or three prototypes** and compare before committing.
- **Build the tool, not the hand edit.** A script or codemod someone can rerun.
- **Fewer, finished features over many rough ones.**

## Verification

- **Prove it on the real thing,** not a proxy, a self-report or "it compiles".
- **Fix the cause where it first went wrong.** A guard is a fix only if the state it handles is legitimate.
- **Test behavior.** Break the behavior and the test fails. Restructure the internals and it still passes.
- **Small units, each ending in a check.**
- **Explain a number before reporting it:** what limits it, and whether the work ran inside the timed part.
- **Two failed fixes on one premise: test the premise.**

## Working

- **Decide what can be undone.** Ask only before what can't.
- **Keep bulk out of the main context.** Send big reads and searches to a subagent and keep its summary.
- **A lesson that repeats becomes a check,** not more text.

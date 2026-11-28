---
name: verify
description: Give a repo a skill that drives its real app like a user, proves each feature with saved evidence, and tries to break it. Use when a repo has no `verify-<app>` skill and you need to prove a change on the real app, when asked to set up verification or end-to-end checks, or when an existing verify skill fails because the app changed.
---

# Verify

Read `${CLAUDE_PLUGIN_ROOT}/src/ks/principles.md` before step 1.

The output is a skill in the repo, `.claude/skills/verify-<app>/`, that the next agent reads cold, mid-task, with no memory of this session. It holds code facts only: commands, ports, selectors, seed data. No secrets, production URLs or customer data.

1. **Read the repo, not the user.** Answer from the code, and ask only what you can't observe:
   - **Surface:** what a user touches: web UI, API, CLI, TUI, desktop, library. Pick the main one and note the rest.
   - **Run:** the repo's own dev command, ports, env vars, seed data and login.
   - **Drive:** an existing harness first (Playwright specs, curl-able endpoints, a test client). Else `ks screens` and Playwright for web, a PTY for CLI and TUI, HTTP for services.
   - **Isolate:** whether two copies can run side by side. If not, the skill says to never drive a copy someone else is using.
   If the app doesn't start from a clean checkout, fix that or report it before going on.
2. **Write the skill.** `SKILL.md` with a `description` naming the app, the surface and when to use it, so the built-in `run` skill and the next agent find it. Sections, each with this repo's real commands:
   - **Launch:** reach a usable state from empty data, migrations and seed included, and the line that says it's ready. "Ready" means usable, not a port answering.
   - **Doctor:** one read-only check that this copy is worth driving: up, right build, port ours, login valid.
   - **Drive:** real selectors and commands. Stable handles first: roles, labels, data attributes, routes.
   - **Evidence:** what to save and where (`.verify/` beside the repo, git-ignored): the action and the state after it, plus side effects such as rows, files or messages. Mock only what production already isolates.
   - **Cleanup:** stop only what this run started, never by process name. Evidence survives cleanup.
   Any helper script is executable and its call is shown in the skill.
3. **Map the features.** `features/README.md` plus one file per user-facing feature, 3 to 5 to start, found from routes, commands and menus. Each file has four sections: `How a user gets there`, `Driving it`, `Breaking it`, `Gotchas`. Every drive step ends in a state a user could see.
   **Breaking it** lists the inputs a real user will try: empty, huge, unicode and emoji, pasted whitespace, double submit, back after submit, a slow or dropped network, two tabs, the wrong role. Each line names the safe outcome.
   If seed data lacks a precondition, the drive fails and says so in `Gotchas`. Never weaken a drive to make it pass.
4. **Prove the skill.** Follow it end to end once from a cold start: launch, doctor, drive one feature and its breaking list, save evidence, clean up. Then confirm the evidence still exists. A skill never run is a draft.
5. **Fan out for a full pass.** With more features than one context holds, give each feature file to its own small subagent with the Launch and Doctor sections. Each returns `PASS`, `ISSUES` or `BLOCKED` with evidence paths. Drop any result without evidence. Drive a shared single copy yourself, one feature at a time.
6. **Keep it true.** When a change alters a feature, its feature file changes in the same pull request. A drive that fails because the map is stale is a map fix. A drive that fails because the app is wrong is a bug: route it to `bug-fix`.

## Reply

The skill path, the features mapped, the proof run with its evidence paths, and each broken input with its outcome.

# kagestack playbooks

Before your first action on a task, pick the kagestack playbook that matches it. Load that playbook with the Skill tool, then follow its steps in order:

- Something broken, failing or wrong: `kagestack:bug-fix`.
- A new feature or changed behavior: `kagestack:feature`.
- A cleanup, restructure, rename or dead-code removal: `kagestack:refactor`.
- A how, why or where question about code: `kagestack:investigate`.
- Something slow, or a speedup claim: `kagestack:perf`.
- Opening a pull request or rewriting its description: `kagestack:pr`.
- Picking or keeping a dev tool or library: `kagestack:scout`.
- Adding or changing a skill, prompt or rule: `kagestack:eval`.
- Stopping mid-task: `kagestack:handoff`.

Load each playbook once per task. A plain question or a one-line edit needs none.

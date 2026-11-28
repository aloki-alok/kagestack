# kagestack playbooks

Before your first action on a task, pick the kagestack playbook that matches it. Load that playbook with the Skill tool, then follow its steps in order. A one-line edit, or a lookup you answer from one file, needs none.

- Something broken, failing or wrong: `kagestack:bug-fix`.
- A new feature or changed behavior: `kagestack:feature`.
- A cleanup, restructure, rename or dead-code removal: `kagestack:refactor`.
- A sweep of a repo's history for mistakes that keep coming back, with no single bug open: `kagestack:garden`.
- Removing comments or lint suppressions, or `ks check` failed on them: `kagestack:clear-comments`.
- A how, why or where question about code: `kagestack:investigate`.
- Something slow, or a speedup claim: `kagestack:perf`.
- Opening a pull request, rewriting its description, or getting one green and merged: `kagestack:pr`.
- Stress testing a risky diff (money, auth, permissions, call dispatch, data writes, a migration), or settling two reviews that disagree: `kagestack:interrogate`.
- Picking or keeping a dev tool or library: `kagestack:scout`.
- Writing or editing TypeScript: `kagestack:typescript`. Python: `kagestack:python`. Load them beside the job's playbook.
- Making a page, doc or diagram for someone to read or decide from: `kagestack:explain`.
- Testing whether a skill, prompt or rule change helps: `kagestack:eval`.
- Stopping mid-task: `kagestack:handoff`.
- A long or unattended run, before its first decision: `kagestack:decision-log`.
- The user comes back after being away from a long run and asks what happened: `kagestack:catch-up`.

Load each playbook once per task.

Decide instead of asking. Ask only before a deploy, a production write, money, a migration, a delete you can't undo, or a message to people. Otherwise do what you would recommend, and list your calls under **Decided**.

To see a web page on phones, a tablet and desktops in Chromium, WebKit and Firefox, run `ks screens <url or file>`. It saves a screenshot of each and lists sideways scroll, page errors and console errors. Use it before you write your own browser script.

---
name: refactor
description: Change the structure of code without changing what it does. Use for cleanups, restructures, renames, removing dead code, or untangling a module.
---

# Refactor

Read `${CLAUDE_PLUGIN_ROOT}/principles.md` before step 1.

Structure changes. Behavior does not. If you find a bug or a missing feature, stop and split it out:
ship this refactor first, then route the rest to `bug-fix` or `feature`.

1. **Pin the behavior.** Write tests that capture what the code does today, before moving anything. Lint and type checks are not a pin.
   Done when the pin passes on the current code and fails if you break the behavior on purpose.
2. **Name the target shape.** The layout, types and call paths as if built today. It must delete branches, flags or layers, not add them.
   Done when you can say what disappears.
3. **Prove what is dead before deleting it.** Search code, strings, config, templates, data files and anything loaded by name at runtime. No callers in code is not proof.
   Done when each deletion cites the searches that came up empty.
4. **Delete first,** in its own commit.
5. **Move in small steps.** Each step keeps the pin green. Check each rename against the files, including strings.
   Done when the old shape has no callers left.
6. **Prove nothing changed.** Run the pin, then the app on the real surface. For a large move, compare old and new output on the same input.
7. **Show it was worth it.** Count what got smaller: lines, branches, files, flags. If nothing got easier to read, revert.

## Reply

The shape before and after, what got deleted, the pin, the proof, and the before and after counts.

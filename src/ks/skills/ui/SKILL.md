---
name: ui
description: Build, change or animate a user interface, such as a page, a component, a screen, a menu or a transition. Use before you write UI code or motion.
---

# UI

Read `${CLAUDE_PLUGIN_ROOT}/src/ks/principles.md` before step 1.

A UI is done when it looks right on the screens people use, not when it compiles.

1. **Find the system first.** Read the project's tokens (colors, spacing, radii, fonts, easing, durations) and the nearest component that does the same job. Follow both.
   A value the system lacks enters as a new token, never inline.
   Done when you can name the token file and the component you follow.
2. **Make the default state complete.** Content shows with scripts off or failing. Motion and hover only add to it.
3. **Read `patterns.md` in this folder** before you write any animation, hover rule, theme or layout spacing. Use its patterns where the project has no rule of its own.
   Every motion has a reason: it shows where something came from, what changed, or that an action worked. Drop any motion without one.
   Done when every transition uses a named curve and duration, and a `prefers-reduced-motion` rule keeps state changes visible with less movement.
4. **Work with touch and keyboard.** Hover styles sit behind `@media (hover: hover) and (pointer: fine)`. Every control works by tap and by keyboard, with a visible focus ring.
5. **Look at it.** Run `ks screens <url or file>`, in light and dark if the page has both. For motion, screenshot each animation at its start, middle and end, and once more with reduced motion on.
   Fix sideways scroll, clipped text, overlaps and stuck hovers, then look again.
   Done when you have opened every screenshot yourself.
6. **If the `impeccable` skill is installed, run its critique** on the finished screen, and fix what it finds that this playbook agrees with.

## Reply

What changed on each screen, the screenshot folder, and any token you added.

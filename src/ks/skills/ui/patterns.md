# UI patterns

Tested values. Use them where the project has no rule of its own.

## Motion tokens

| Token | Value | Use |
|---|---|---|
| `--ease-out` | `cubic-bezier(.23,1,.32,1)` | arrivals |
| `--ease-in-out` | `cubic-bezier(.77,0,.175,1)` | moves on screen |
| `--ease-sheet` | `cubic-bezier(.32,.72,0,1)` | sheets, menus, sliding indicators |
| `--duration-fast` | 120 ms | press, toggle |
| `--duration-normal` | 160 ms | routine state change |
| `--duration-slow` | 200 ms | larger state change |
| `--duration-overlay` | 240 ms | overlay, dialog |

- Exit faster than entrance. A toast takes 340 ms in and 220 ms out.
- No bounce or elastic curve by reflex.
- Animate `transform` and `opacity`. Animate `width`, `height`, `top` or margins only for one isolated surface that morphs between panels, such as a mega-menu (about 460 ms on the sheet curve).

## Entrances

- Write entrance keyframes with only a `from` state and `animation-fill-mode: backwards`. The element ends on its own style, so a later state change never fights the end values of the keyframe.
- A list that appears as a list may stagger: 40 ms per item, a 12px rise and a 3px blur that clears, each over 500 ms on `cubic-bezier(.22,1,.36,1)`. Start it from an IntersectionObserver with `rootMargin: '0px 0px -40% 0px'`, and disconnect after the first fire, so scrolling back never replays it. Never stagger every section of a page.

## Hover

- Put every hover rule inside `@media (hover: hover) and (pointer: fine)`, so a tap never leaves a stuck hover.
- Hover colour on a control changes at once (`transition-duration: 0s`).
- The hovered element stays still. Only a child moves, over about 160 ms (for example, card art scales to 1.06). An element that moves itself slides out from under the pointer and flickers.

## Indicators, headers, sheets

- Place a sliding indicator (a tab pill, an underline) with no animation the first time. Set `data-instant` (which sets `transition: none`), apply the position, read `offsetWidth` to force a reflow, then remove the attribute. Later moves animate.
- Change the look of a sticky header from an IntersectionObserver on a 1px marker at the page top (`data-stuck`), never from a scroll listener. Animate the `inset` and `border-radius` of a pseudo-element, so the box of the header never moves.
- Open `<details>` to its natural height with `interpolate-size: allow-keywords`, `::details-content { block-size: 0; transition: block-size .2s, content-visibility .2s allow-discrete }` and `[open]::details-content { block-size: auto }`.
- Hide a closing sheet with `transition: opacity .22s, visibility 0s linear .22s`. It fades first, then leaves hit testing and the tab order. Closed panels get `inert`.

## Colour, shape, layout

- Tints come from one token: hover fills, borders and muted fills use `color-mix(in oklab, var(--accent) 12%, transparent)` and the like, so one token change moves them all.
- An inner corner is `calc(var(--radius-outer) - var(--pad) - 1px)`, where the 1px is the border. Both curves then stay parallel.
- Put the chosen theme on the root (`:root[data-theme=light]`) and read every colour from tokens under it. One attribute then flips the page.
- Use a container of `width: min(100%, 1280px); padding-inline: clamp(20px, 4vw, 48px)` and a grid `gap: clamp(18px, 2vw, 26px)`. Spacing then scales with the viewport and needs no breakpoints.

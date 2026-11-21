---
name: explain
description: Make something a person looks at to understand or decide, such as an explainer, a design summary, a report, a diagram or a decision page. Use before you make any page, doc or diagram for a reader.
---

# Explain

A page nobody reads is waste. Build it for one reader and one action, after you know the answer.

1. **Pick the route.** Name the reader and what they will do with it.
   - They read it once: answer in the reply. Make no page.
   - They keep, edit or pass it around (plan, spec, report): a document.
   - They decide, click, track or explore: an interactive page that saves their choices.
   - They need to see a flow, a structure or a change: a page built around one picture.
   Done when you can write "<reader> will <action>" in one line.
2. **Write the answer in at most five lines.** Each line is an answer, a decision or a number, never background. For a bug or a feature, the lines say what is broken or missing, the approach, and what gets built. If you can't, the research isn't done. Go back to it.
   To teach a concept: one concrete case the reader already knows, then the rule it shows, then where the rule breaks.
   Done when a reader who stops after these lines knows what you know that matters to them.
3. **Draw one picture that carries those lines.** One idea, at most eight labels, readable in five seconds. Choose the form from the content: a sequence for steps over time, boxes and arrows for structure, side by side for before and after, a chart for numbers. If the picture needs a paragraph to explain it, split it or pick another form.
   Done when someone who sees only the picture gets the gist.
4. **Put decisions right after the answer,** before anything else. Each one: the question, your recommendation, and a one-line reason. On an interactive page, each gets controls that save the answer, so the reader acts without writing back.
5. **Keep only what the reader must understand,** on one screen: what is broken or missing, the approach, and what gets built. Delete everything else from the page: evidence, code locations, ticket numbers, field lists, rejected options. Never hide them in collapsed sections or dropdowns. They stay in the repo and the reply. Use the reader's words, and drop jargon they don't use.
   In a list of items (ideas, issues, options), each row shows a name of up to five words, its outcome as before → after, such as "3 replies → 1 reply", and the approach as two short flows, "Now" and "Fix", with steps of three words or fewer, such as "Meta event → handler errors → returns 200 → message lost". All of it is visible, with no sentences.
   Done when the page has no collapsed sections, the visible text is under 300 words, and it holds at most one table.
6. **Look at it.** Render it at phone and desktop width, in light and dark. On a web page, run `ks screens <file>`. Fix overlapping labels, clipped text and empty space.
   Done when you have opened the screenshots yourself.
7. **Change the part, not the page.** When the reader comments on one element, change that element and leave the rest.

## Reply

The link, plus one line that says what the reader should do with it.

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
3. **Draw pictures that carry those lines.** The first screen is the answer: a picture and one sentence. Each picture makes one claim, and its caption states it. Draw how it works, not boxes with names, and give every arrow a verb ("writes", "retries every 5 s"). Choose the form from the content: a sequence for steps over time, boxes and arrows for structure, side by side for before and after, the same small drawing once per case, a bar or a measurement line for every number. Build a system of three or more parts as a series, each picture adding one part to the last. Keep each picture under eight labels. If a picture needs a paragraph to explain it, split it or pick another form.
   Done when someone who sees only the first picture gets the gist.
4. **Put decisions right after the answer,** before anything else. Each one: the question, your recommendation, and a one-line reason. On an interactive page, each gets controls that save the answer, so the reader acts without writing back.
5. **Keep only what the reader must understand, in the shape of the page's kind.** Delete everything else from the page: evidence, code locations, ticket numbers, field lists, rejected options. Never hide them in collapsed sections or dropdowns. They stay in the repo and the reply. Use the reader's words, and drop jargon they don't use. If the reader would have to decode a label, a code name or an arrow chain, write the plain sentence instead.
   - **A change** (a bug, a feature, a list of ideas): what is broken or missing, the approach, and what gets built. For each item, show what its user sees or feels today and after, in the form that fits that item, never one template for all. A change on a screen (a chat, an email, an alert) gets a small mock of that screen, showing what the user reads, never raw codes or timestamps. A number gets its before and after as a picture. Anything else gets one plain sentence for today and one for after. Each item says how often it happens, to how many, or what it costs, measured or marked as a guess. If no item has a number, say once at the top that the page can't support a recommendation. Name items by what they do for the user, and group them by what they mean to the reader, not by system.
   - **A concept:** a plain definition, then the case in front of the reader, then how it works step by step, then where it breaks.
   - **A comparison:** the difference drawn side by side, then the trade-off, then your recommendation.
   Done when the page has no collapsed sections and holds at most one table. A change or comparison stays under 300 visible words. A concept may run longer, at most one screen per step.
6. **Look at it.** Render it at phone and desktop width, in light and dark. On a web page, run `ks screens <file>`. Fix overlapping labels, clipped text and empty space.
   Done when you have opened the screenshots yourself.
7. **Change the part, not the page.** When the reader comments on one element, change that element and leave the rest.

## Reply

The link, plus one line that says what the reader should do with it.

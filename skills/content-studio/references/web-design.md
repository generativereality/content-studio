# Web design: sites, landing pages, brand identity, page visuals

**You can't prompt your way to taste; you can only start from it.** Asked for "a premium page" with
nothing to copy, a model averages everything labelled premium: a cream page, a thin serif headline
with an italic accent, pill buttons, line drawings in rounded cards, an indigo-and-amber palette
reasoned from a colour wheel, and a paragraph under every heading. Each of those choices can be
defended; together they read as an agent's draft at a glance. Taste is a few hundred small decisions
(how much space a thing gets, what is left out, where the eye lands first, how fast a thing moves)
already made well by someone. So a page here is built from **references, a design system and real
assets**, never from adjectives and freehand drawing.

Use this file for a website or a page on one, a landing or product page, a guide's layout, a brand
identity (palette, type, logo, app icon) and the illustrations or motion on a page. The words on the
page still follow `copy.md` and `voice.md`; the person's own words come first.

## 0. Load the design skills before anything else

Look at what is installed (the project's skills folder and the user's global one) and load every
design skill that fits **before** the first sketch, and name them in the brief. If a craft the brief
needs has no skill and no reference here, say so in the brief and stop; never improvise a craft the
studio doesn't have. Kinds worth loading when present:

| Kind | Public examples (read 28 Nov 2026) | Use it for |
|---|---|---|
| A taste skill | `Leonxlnx/taste-skill` (MIT): classifies the business, deals a palette, a font pairing and a tested hero layout, real photos and icons, then checks the page in a browser at four widths | the default starting system for a company or product site |
| An anti-slop reviewer | `pbakaus/impeccable` (Apache-2.0): `critique`, `audit`, `quieter`, `distill`, `typeset`, `layout`; `npx impeccable detect <dir or url>` flags the tells deterministically | reviewing every render, and the distill pass that cuts the text |
| Design-engineering rules | `emilkowalski/skills` (MIT): easing, durations, what not to animate, `learn-taste` that turns the person's corrections into rules in `DESIGN.md` | motion and interaction details; keeping the person's corrections |
| A design-system library | `nextlevelbuilder/ui-ux-pro-max-skill` (MIT): palettes, font pairings and layouts by product type | when no taste skill is installed |
| A design-system extractor | `Manavarya09/design-extract`, run as `npx designlang <url>` (MIT): tokens, type scale, spacing and motion off a live site; `designlang slop <url>` scores how generic a page looks | measuring the references (§1) and the end check (§7) |
| A UX design process skill | whatever the person keeps for briefing and building designs | the brief to a design tool or designer, and proving the build matches |
| A saves index | whatever the person keeps of pages, reels and tools they saved | references and resources they already chose (SKILL step 2) |
| Motion for video | `hyperframes` + `hyperframes-registry` (`tools.md`) | an animated hero clip, a launch film, any page video |

Installing a skill changes the person's machine: ask once, with what it is and its licence.

## 1. Study references first, and cite three

Before any layout, collect **six to ten real pages** of the same kind (a developer tool's home, a
course's landing page, a café's site), from the niche's best and from galleries of designed pages
(for example a landing-page gallery with live previews, a site-template library, an award gallery),
the person's own saved examples first. A screenshot of a page you like given to the model beats any
description: it copies the actual layout and spacing instead of guessing.

For each, measure rather than admire, by `designlang` or by hand from a 1440 px and a 390 px
screenshot: the type families and sizes, the content width, the section spacing, how many words sit
above the fold, how many colours carry the page and where the accent appears, what the hero shows,
what moves and how.

Then pick **three** and put them on the gallery, each with a screenshot, its link and one line on
what it lends: *"layout and section rhythm from A, the type pairing and scale from B, the way C shows
the product's own output in the hero"*. Borrow decisions, never a brand: no copied logo, illustration,
photo or wording. A page that resembles one reference closely is a clone; three references blended
by decision is a design.

## 2. Taste rules

- **One idea per page, built around one picture.** The hero is the product's own output, a real
  screen, a real photo or one strong illustration, chosen from the subject (`stills.md` §the idea
  comes from the subject). A row of ten small thumbnails is not one picture.
- **Less, larger, further apart.** Fewer elements, bigger type for the one thing that matters, more
  space between sections than feels necessary. One section per screen on a desktop.
- **Every element earns its place.** If removing it changes nothing a stranger would notice, remove
  it. Distill before polishing.
- **The tells, which fail a page on sight:** one sans used for everything with no pairing; a
  purple-to-blue gradient; cards inside cards; grey text on a coloured ground; a rounded-square icon
  tile above every heading; the "tasteful default" (cream page, thin serif, italic accent, pill
  buttons, flat line drawings in rounded cards); a dotted path joining numbered circles; fade-in on
  every section; a palette justified by colour-wheel theory alone; a definition or a manifesto in
  the hero; a paragraph under every heading.
- **Motion is rare and purposeful:** an entrance for the hero and one or two moments that show
  something (a step completing, a number arriving). Enter with ease-out, 150 to 400 ms; never animate
  what the reader is trying to read; honour reduced motion.

## 3. Systems: type, layout, spacing, colour as tokens

Write the system down before the page, as tokens in one file (`DESIGN.md` plus CSS variables), and
build every page from it:

- **Type:** at most two families (a display and a text face, or one family in two weights), a scale
  with a fixed ratio (for example 1.25 or 1.333) and about six named steps; body 16 to 18 px on a
  phone, lines of 45 to 75 characters; bundle the font files locally (`stills.md` recipe A).
- **Layout:** one content width and one grid (12 columns on desktop, 4 on a phone), equal left and
  right edges, the same vertical rhythm in every section.
- **Spacing:** one scale on a 4 or 8 px base; section padding from it, never a one-off value.
- **Colour:** tokens for ground, surface, ink, muted ink, one accent and its hover, in light and dark;
  every text pair passes WCAG AA in both.
- **Components from a library, not hand-rolled:** a proven component or block set (shadcn/ui-based
  blocks, a React or plain-HTML component library with animated sections) for nav, hero, feature
  rows, pricing, footer; restyle it to the tokens.

## 4. How little text a designed page carries

Fewer words is most of what makes a page look designed. Budgets for a home or landing page:

- **Hero:** a headline of up to about 10 words, one supporting line of up to about 25, one button.
- **Each later section:** a heading and at most two short lines, or a list of three to five items of
  a few words each; the picture does the rest.
- **The whole page:** count the words above the fold on a phone and on the full page, and write the
  counts on the gallery. A long explanation goes to its own guide page and the home links to it.

Design decides where words go and how many; the words themselves come from the person (`voice.md`)
and are cut, not rewritten, to fit.

## 5. Visuals from a real framework, never freehand agent SVG

The agent hand-drawing an "illustration" path by path in SVG is the single most reliable way to make a
page look like a draft: wobbly proportions, stick figures, a different line weight in each drawing.
Every visual comes from one of these, in this order:

| Need | Use |
|---|---|
| Show the product | the real product: screenshots and recordings, framed in code (`stills.md`) |
| Show a place, object or person | real or licensed photographs, credited |
| Small symbols in UI and lists | one icon set used throughout (Lucide, Phosphor, Tabler, Heroicons and similar; check the licence), at one stroke weight and size |
| Section effects, backgrounds, hero motion | a component or animation library: Motion (motion.dev), GSAP with ScrollTrigger, an animated-component set; restyled to the tokens |
| Diagrams of a real mechanism | a diagram library or a component set's diagram blocks, laid out from data, never drawn freehand |
| Illustrations with character | generated with one locked style and reference sheet (`generation.md`), or commissioned; then vectorised and cleaned (§6) before it ships |
| Animated illustration | Lottie or Rive files from a designer or a library; or the illustration animated in a motion library |
| A video on the page | `video.md`, made in HyperFrames from its registry blocks |

Name the framework and the source of every visual on the gallery. A visual with no named source does
not ship.

## 6. Palette and icon: from the references and the subject

**Palette.** Start from what is real: the colours measured from the three references, the materials
and world of the subject (a workshop, a meadow, a terminal at night, paper and ink), and anything the
brand already owns. Make two or three palettes, each traceable in one line to a reference and to the
subject. Colour theory is a check on a palette (contrast, harmony, one accent at about 10%), never
its source. Then **check it against looking generic**: lay it beside the palettes of the ten best-known
sites in the niche and of the large AI brands; if it sits among them (indigo or violet with a warm
accent, black with one neon, cream with terracotta), name what makes yours different or start again.
Run the anti-slop detector on a page in it.

**Logo and app icon.** One idea from the subject, written down, then many concepts: a designer, or an
image model strong at icons, asked for flat vector concepts with no text (`generation.md`). Pick one,
then **redraw it clean as a vector**: trace it (potrace or vtracer) or rebuild it on a grid in a vector
tool, cut the nodes to the minimum, one stroke weight. Test it at 16, 32, 64 and 180 px in light and
dark; it must read at 16 px. Code-drawn marks are sketches for direction only and are labelled so.

## 7. The end check: a template a designer would ship, or an agent's draft?

Before the gallery, and fixed until it passes, never asked:

1. **Side by side:** the render at 1440 and 390 px next to the three references at the same size.
   Would it sit among them without standing out as the weak one?
2. **The tells:** none of §2's list; `impeccable detect` and `designlang slop` (when available) clean
   or each finding answered.
3. **Words:** the counts from §4 are within budget.
4. **Sources:** every visual has its framework or source named; nothing drawn freehand.
5. **The system:** every size, space and colour on the page comes from the tokens.
6. **A cold look:** a fresh session, given only the render and the three references with their
   names removed, is asked which one an agent made. If it picks yours, it is not done.

On the gallery, show the reference board (three references with what each lends), the system (one
token sheet: type scale, spacing, palette in both themes, the icon at four sizes), then the pages at
phone and desktop in light and dark, with the word counts and the sources of every visual.

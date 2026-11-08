# content-studio

A Claude Code skill for making content well, in any medium and for any purpose: posts, articles,
pages, newsletters, launches, ads, scripts, short videos, demos, explainers, carousels, thumbnails,
collages, narration, music beds and personal memory films.

It holds the **process** a small, good studio follows, in `SKILL.md`, loaded whenever something is to
be made: brief → study what works → variations → **one best version shown for a pick** → make it well →
check → learn from the pick and the result. It also holds **references**, loaded only when the brief
needs them:

| Reference | Covers |
|---|---|
| `brief.md` | the brief template, purpose (brand, audience, teaching, product, personal), reader awareness |
| `review.md` | showing work so a person can choose: one best plus a few alternatives, phone-ready review pages |
| `copy.md` | the one idea, studying outliers, hooks, scripts and story loops, copy rules, sharing, formats, the check, reading results |
| `voice.md` | the person's own material first, answering a critique, the machine-prose tells and the sweep |
| `channels.md` | Reddit, Show HN, Product Hunt, directories, blogs, newsletters, LinkedIn, X, Instagram, TikTok, YouTube; sizes |
| `search.md` | measured queries, reading the results page, the novelty bar, primary sources, writing for AI assistants |
| `stills.md` | layout in code, generated backgrounds, carousels, product lead images, collages, thumbnails, restoration |
| `generation.md` | hosted image and video models (dated), POST-then-poll, prompting, consistency, the invention check |
| `video.md` | timelines and renderers, cut craft, showing a real product, captions, crops, HDR, encoding |
| `audio.md` | whether to narrate, voice engines by language, verifying speech, music, mixing and loudness |
| `real-people.md` | consent, voice cloning, facts before creativity, photo faults, the personal register |
| `costs-and-licences.md` | budgets and the spend log, local or hosted, disk, licences, Windows |
| `tools.md` | the tool skills it routes to (HyperFrames, media-use, review-md, browser-automation) and where it overrides them |

Scripts (no dependencies beyond bash, node and Chrome):

- `scripts/voice-sweep.sh FILE` finds machine-prose tells (a candidate list, not a verdict).
- `scripts/render-frames.sh OUT W H frame.html…` renders HTML frames to PNG with headless Chrome.
- `scripts/spend.mjs add|total DIR` keeps a per-piece spend ledger with a budget check.

## What it never does

It never posts, publishes, uploads, sends, comments, signs up or buys. It never invents a fact, a
number, a quote or a user, and never shows a product doing what it doesn't do. It never uses a real
person's face, voice or words without their consent. Every paid call is logged and reported with its
cost.

## Install

```
/plugin marketplace add generativereality/plugins
/plugin install content-studio@generativereality
```

The skill names no person, company or product, so it can be vendored into any project. Your own voice
notes, house style and strategy skills sit beside it and take precedence over its defaults.

## Licence

MIT

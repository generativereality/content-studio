# content-studio

A skill, not an app: `skills/content-studio/SKILL.md` is the process every content job follows, and
`references/` holds the craft and tools per medium. Plans and decisions about where it is used are
kept privately, never in this repo.

## Rules for editing the skill

- **Neutral, always.** It ships into other people's projects, whose own checks may refuse a skill
  naming a person, a product or a machine path. No names of people, companies, products, accounts,
  keychain entries or paths. Worked examples are generic ("a budgeting app's guide page").
  `npm run check` enforces the generic part; names to block come from the leakcheck denylist outside
  the repo, never from a list committed here.
- **Nothing private in commits either.** History is public: no internal names, team or session
  names, or decisions about where the skill is used, in commit messages.
- **Facts carry dates.** Model names, prices, rankings and platform rules go stale in weeks. Every
  such line says when it was read, and the text says to read the live price and schema.
- **Lessons go in as rules, not as history.** Write what to do and the failure that taught it, in one
  sentence. No "added on…", no changelog inside a reference.
- **SKILL.md stays short.** The process and the routing table only; craft goes in a reference.
- **The skill wins over tool skills on safety** (cost shown, consent, nothing goes out). Say so in
  `references/tools.md` when a tool skill's default conflicts.

## Releasing (only on an explicit go-ahead)

Never publish, push, tag or create the GitHub repository on your own initiative. When asked:

1. `npm run check`, then commit. Commits as `Motin <motin@motin.eu>` (set locally).
2. Bump the version in **both** `package.json` and `.claude-plugin/plugin.json`.
3. Push main, then tag `v<version>`; publishing to npm is CI's job (OIDC trusted publishing), as in
   review-md. The workflow doesn't exist yet; copy review-md's `.github/workflows/release.yml`.
4. Sync to `../plugins` (copy review-md's `scripts/sync-plugin.sh`, pointed at `content-studio`), and
   add a `content-studio` entry to its `marketplace.json`.
5. Brand apps vendor it from the npm tarball via their own `sync-vendored-skills.py`.

#!/usr/bin/env bash
# Repo check: the skill must be shippable into anyone's project.
# 1. Neutral: no machine paths, and no names from the leakcheck denylist kept OUTSIDE the repo
#    (LEAKCHECK_DENYLIST). A list of names committed here would publish what it means to keep out.
# 2. Every reference SKILL.md and tools.md name exists, and every script parses.
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$0"/..)"
fail=0
SKILL=skills/content-studio
NEUTRAL='/Users/[A-Za-z]|/home/[a-z]|C:\\\\Users'
if grep -rnE "$NEUTRAL" "$SKILL" .claude-plugin README.md; then
  echo "FAIL: names a person, product or private path (above)"; fail=1
fi
DENY="${LEAKCHECK_DENYLIST:-$HOME/.config/leakcheck/denylist.txt}"
if [ -f "$DENY" ]; then
  while IFS= read -r pat; do
    [ -z "$pat" ] || [ "${pat#\#}" != "$pat" ] && continue
    if grep -rniE -- "$pat" "$SKILL" .claude-plugin README.md >/dev/null; then echo "FAIL: denylist pattern hit"; fail=1; fi
  done < "$DENY"
fi
for ref in $(grep -ohE 'references/[a-z-]+\.md' "$SKILL/SKILL.md" "$SKILL/references/"*.md | sort -u); do
  [ -f "$SKILL/$ref" ] || { echo "FAIL: missing $ref"; fail=1; }
done
for s in $(grep -ohE 'scripts/[a-z-]+\.(sh|mjs)' "$SKILL/SKILL.md" "$SKILL/references/"*.md | sort -u); do
  [ -f "$SKILL/$s" ] || { echo "FAIL: missing $s"; fail=1; }
done
for s in "$SKILL"/scripts/*.sh; do bash -n "$s" || { echo "FAIL: $s"; fail=1; }; done
for s in "$SKILL"/scripts/*.mjs; do node --check "$s" || { echo "FAIL: $s"; fail=1; }; done
v1=$(node -e 'console.log(require("./package.json").version)'); v2=$(node -e 'console.log(require("./.claude-plugin/plugin.json").version)')
[ "$v1" = "$v2" ] || { echo "FAIL: package.json $v1 != plugin.json $v2"; fail=1; }
[ $fail -eq 0 ] && echo "check: ok"
exit $fail

You are a skill updater for Claude Code. Your job is to refresh existing skills with the latest information from the web, using smart staleness detection and diff reporting.

Target: **$ARGUMENTS**

---

## If `$ARGUMENTS` is empty or "all":

### Step 1: Find All Skills
Use Glob to find all skills: `~/.claude/skills/*/SKILL.md`

### Step 2: Quick Staleness Check (per skill)
For each skill found:
1. Read the SKILL.md frontmatter to extract `name`, `version`, `generated`, `language`, and `tags`
2. Quick-check the package registry for the latest version:
   - For JS/TS: `WebSearch: "site:npmjs.com {name}"` — look for latest version number
   - For Python: `WebSearch: "site:pypi.org {name}"` — look for latest version number
   - For Rust: `WebSearch: "site:crates.io {name}"` — look for latest version number
   - For Go: `WebSearch: "site:pkg.go.dev {name}"` — look for latest version number
   - If language is unknown or "multi", try npmjs first, then pypi
3. **Skip if fresh:** If the version in the skill matches the latest version AND the `generated` date is less than 30 days old, skip this skill and report it as "up to date"
4. **Update if stale:** If the version is outdated OR the skill is older than 30 days, proceed to full update

### Step 3: Full Update (per stale skill)
For each skill that needs updating:
1. Extract the technology name, `type`, and doc URLs from the Overview section
2. Run full research (same as `/learn` Phase 3, Strategies A-G including sitemap discovery and link crawling) to find latest docs
3. Scrape the latest documentation using `/learn` Phase 4 (URL queue with scoring, retry with backoff, deduplication)
4. **Fetch changelog between versions:** If the version changed from `{old}` to `{new}`:
   - `WebSearch: "{name} changelog {old} to {new}"`
   - `WebSearch: "site:github.com {name} releases"`
   - Try direct fetch: `WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/main/CHANGELOG.md`
   - Extract breaking changes and new features between the two versions
5. Merge new information into the existing skill using the merge strategy below
6. Update frontmatter: `version`, `generated` date, and `type` (add if missing)
7. If changelog data was found, update or create the `## Migration Notes` section
8. Run the quality gate checks from `/learn` Phase 7 (all 12 hard gates must pass)

### Step 4: Report
Show a summary table:

| Skill | Status | Old Version | New Version | Changes |
|-------|--------|-------------|-------------|---------|
| stripe | Updated | 14.1.0 | 15.0.0 | +3 endpoints, updated auth section, 2 deprecations |
| hono | Up to date | 4.0.0 | 4.0.0 | — |
| drizzle-orm | Updated | 0.29.0 | 0.30.0 | Updated install section, new query builder API |
| xrpl | Failed | 3.0.0 | ? | Could not fetch latest docs |

---

## If `$ARGUMENTS` is a specific skill name:

### Step 1: Find the Skill
Find and read `~/.claude/skills/{$ARGUMENTS}/SKILL.md`

If not found, check for partial matches: `~/.claude/skills/*{$ARGUMENTS}*/SKILL.md`

If still not found, report error and suggest `/learn-list` to see installed skills.

### Step 2: Extract Current State
From the existing skill, extract:
- `name`, `version`, `generated`, `language`, `tags` from frontmatter
- Doc URLs from the Overview/Key links section
- Section headings and their line counts (to compare later)

### Step 3: Full Research
Run full research (same as `/learn` Phase 3) to find latest docs, including:
- Strategies A-G from `/learn` (official docs, GitHub, practical usage, sitemap discovery, link crawling, registry, changelog)
- Use the full Phase 4 pipeline (URL queue with scoring, retry with backoff, deduplication)
- Focus on what's changed since the `generated` date

### Step 4: Fetch Changelog
If the version changed:
- `WebSearch: "{name} changelog {old_version} to {new_version}"`
- `WebSearch: "site:github.com {name} releases"`
- `WebSearch: "{name} migration guide {old_version}"`
- Extract: breaking changes, new APIs, deprecated APIs, removed APIs

### Step 5: Merge Using Strategy

**Merge rules:**
1. **Always update frontmatter** — `version`, `generated` date, and `tags` (merge new tags, don't remove existing ones)
2. **Replace section content** but preserve lines marked with `<!-- user -->` — these are user customizations that must survive updates
3. **Keep user-added sections** — if the skill has sections that aren't in the standard template (e.g., `## My Notes`, `## Team Conventions`), keep them in place
4. **Add new sections** — if the update found data for sections that didn't exist before (e.g., `## Testing`, `## Deprecated / Avoid`), add them in the standard order
5. **Update the Migration Notes section** — add new entries for version changes, don't remove old entries
6. **Preserve Related Skills** — don't remove related skill references

### Step 6: Diff Report
After updating, show a clear diff report:

```
Skill: stripe (v14.1.0 → v15.0.0)
Updated: 2025-01-15

Changes:
  + Added: 3 new endpoints in API Reference
  ~ Updated: Installation section (new SDK import path)
  ~ Updated: Authentication section (new API key format)
  + Added: Deprecated / Avoid section (2 deprecated APIs)
  + Added: Migration Notes v14 → v15
  - Removed: Nothing

Preserved:
  ✓ 2 user-customized lines (<!-- user -->)
  ✓ 1 custom section (## Team Conventions)

Sources: [list of URLs used]
```

---

## Update Rules

- **Never delete user content** — lines marked `<!-- user -->` and non-standard sections are always preserved
- **Never delete existing content** unless it's confirmed outdated/wrong and has been replaced
- **Preserve structure** — keep the same section order as the existing skill
- **Be conservative** — if you're unsure whether something changed, keep the existing content
- **Update the generated date** in frontmatter to today's date after any update
- **Report changes clearly** — the user should know exactly what was added, modified, or flagged as potentially outdated
- If a source URL is dead, flag it and try to find the new URL
- If the skill has no `version` or `generated` fields in frontmatter (old format), add them during the update

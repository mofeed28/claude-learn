You are a skill manager for Claude Code. List and summarize all installed skills with rich metadata and optional filtering.

Filter: **$ARGUMENTS**

---

## Steps

### Step 1: Find All Skills

Use Glob to find all skills: `~/.claude/skills/*/SKILL.md`

If no skills are found, report that no skills are installed and suggest `/learn {topic}` to get started.

### Step 2: Read Metadata

For each skill found, read the frontmatter to extract:
- `name` — the skill slug
- `description` — trigger description
- `version` — the library version when the skill was generated (may be missing in old skills)
- `generated` — the date the skill was generated/last updated (may be missing in old skills)
- `language` — the target language (may be missing in old skills)
- `tags` — relevant tags (may be missing in old skills)

### Step 3: Apply Filters

If `$ARGUMENTS` is not empty, filter the skills:
- Match against skill `name` (partial match, case-insensitive)
- Match against `tags` (partial match, case-insensitive)
- Match against `description` (partial match, case-insensitive)
- Match against `language` (exact match, case-insensitive)

Show only skills that match at least one of the above. If no skills match, report "No skills matching '{$ARGUMENTS}' found" and show the full list instead.

### Step 4: Detect Staleness

For each skill, determine its freshness:
- **Fresh** — `generated` date is less than 60 days ago
- **Stale** — `generated` date is more than 60 days ago, or `generated` field is missing
- Mark stale skills with a warning indicator

### Step 5: Present Results

Show a rich table:

```
Installed Skills (X total):

| # | Skill | Version | Language | Generated | Status | Description |
|---|-------|---------|----------|-----------|--------|-------------|
| 1 | stripe | 15.0.0 | typescript | 2025-01-15 | Fresh | Stripe payment processing API... |
| 2 | hono | 4.0.0 | typescript | 2024-10-01 | Stale | Lightweight web framework for... |
| 3 | xrpl | 3.1.0 | multi | 2025-01-10 | Fresh | XRP Ledger blockchain develop... |
| 4 | drizzle-orm | — | — | — | Stale | TypeScript ORM for SQL databa... |
```

**Column rules:**
- `Version`: show the version from frontmatter, or `—` if missing
- `Language`: show the language from frontmatter, or `—` if missing
- `Generated`: show the date from frontmatter, or `—` if missing
- `Status`: show `Fresh` or `Stale` based on staleness detection. Use `Stale` if the date is missing
- `Description`: truncate to ~50 characters, add `...` if truncated

### Step 6: Show Summary

After the table, show:

```
X skills installed, Y fresh, Z stale

Stale skills can be refreshed with /learn-update
```

### Step 7: Suggest Commands

```
Commands:
  /learn {topic}           — learn a new skill
  /learn {topic} --quick   — quick cheat-sheet version
  /learn {topic} --deep    — exhaustive deep-dive version
  /learn-update            — refresh all stale skills
  /learn-update {name}     — refresh a specific skill
  /learn-list {filter}     — filter by name, tag, or language
  /learn-delete {name}     — delete a skill
  /learn {topic}:{sub}     — learn a focused subtopic
  /learn ./path/to/file    — learn from a local file
  /learn https://github.com/owner/repo — learn from GitHub repo
```

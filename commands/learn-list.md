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
- `type` — library type: api-client, framework, ui-library, orm-db, cli-tool, utility, platform, testing (may be missing in old skills)
- `tags` — relevant tags (may be missing in old skills)

Also count:
- Total lines in the file
- Number of code blocks (count occurrences of ```)
- Number of tables (count lines starting with `|`)

### Step 3: Apply Filters

If `$ARGUMENTS` is not empty, filter the skills:
- Match against skill `name` (partial match, case-insensitive)
- Match against `tags` (partial match, case-insensitive)
- Match against `description` (partial match, case-insensitive)
- Match against `language` (exact match, case-insensitive)
- Match against `type` (exact match, case-insensitive)

Show only skills that match at least one of the above. If no skills match, report "No skills matching '{$ARGUMENTS}' found" and show the full list instead.

### Step 4: Detect Staleness

For each skill, determine its freshness:
- **Fresh** — `generated` date is less than 60 days ago
- **Stale** — `generated` date is more than 60 days ago, or `generated` field is missing
- Mark stale skills with a warning indicator

### Step 5: Quick Quality Check

For each skill, run a lightweight quality assessment:

- **Lines**: count total lines
- **Code examples**: count code blocks (pairs of ```)
- **Tables**: count table rows (lines starting with `|`)
- **Has imports**: check if at least one code block contains `import` or `require`

Assign a quality tier:
- **A** — 150+ lines, 4+ code examples, 3+ tables, has imports
- **B** — 80-149 lines, 2+ code examples, 1+ tables
- **C** — Under 80 lines, or fewer than 2 code examples, or no tables

### Step 6: Present Results

Show a rich table:

```
Installed Skills (X total):

| # | Skill | Type | Version | Lang | Generated | Status | Grade | Description |
|---|-------|------|---------|------|-----------|--------|-------|-------------|
| 1 | stripe | api-client | 15.0.0 | ts | 2025-01-15 | Fresh | A | Stripe payment processing API... |
| 2 | hono | framework | 4.0.0 | ts | 2024-10-01 | Stale | B | Lightweight web framework for... |
| 3 | xrpl | platform | 3.1.0 | multi | 2025-01-10 | Fresh | A | XRP Ledger blockchain develop... |
| 4 | drizzle-orm | orm-db | — | — | — | Stale | C | TypeScript ORM for SQL databa... |
```

**Column rules:**
- `Type`: show `type` from frontmatter, or `—` if missing
- `Version`: show the version from frontmatter, or `—` if missing
- `Lang`: show abbreviated language (`typescript` → `ts`, `python` → `py`, `javascript` → `js`, `rust` → `rs`), or `—` if missing
- `Generated`: show the date from frontmatter, or `—` if missing
- `Status`: show `Fresh` or `Stale` based on staleness detection. Use `Stale` if the date is missing
- `Grade`: show `A`, `B`, or `C` based on quality tier
- `Description`: truncate to ~40 characters, add `...` if truncated

### Step 7: Show Summary

After the table, show:

```
X skills installed, Y fresh, Z stale
Quality: X grade A, Y grade B, Z grade C

Grade C skills can be improved with /learn {name} --deep
Stale skills can be refreshed with /learn-update
```

### Step 8: Suggest Commands

```
Commands:
  /learn {topic}           — learn a new skill
  /learn {topic} --quick   — quick cheat-sheet version
  /learn {topic} --deep    — exhaustive deep-dive version
  /learn-update            — refresh all stale skills
  /learn-update {name}     — refresh a specific skill
  /learn-list {filter}     — filter by name, tag, type, or language
  /learn-delete {name}     — delete a skill
  /learn-audit             — run quality checks on all skills
  /learn-audit {name}      — run quality check on one skill
  /learn {topic}:{sub}     — learn a focused subtopic
  /learn ./path/to/file    — learn from a local file
  /learn https://github.com/owner/repo — learn from GitHub repo
```

# /learn for Claude Code

**Teach your Claude Code agent any technology in seconds. No API keys. No subscriptions. Free.**

```
/learn stripe
/learn drizzle-orm --deep
/learn react:hooks --lang typescript
/learn @tanstack/query
/learn https://github.com/honojs/hono
/learn ./docs/my-api.yaml
```

Claude searches the web, scrapes the docs, and generates a skill file — all using built-in tools you already have.

---

## Why?

Claude Code agents are powerful, but they don't know every library or API out of the box. Instead of explaining the same docs over and over, just run `/learn` once and your agent has a permanent skill file it can reference anytime.

- **No API keys** — uses Claude Code's built-in WebSearch and WebFetch
- **No subscriptions** — completely free
- **No setup** — copy 5 files and restart

---

## Install

### Option 1: Quick copy (recommended)

Copy the 5 command files from `commands/` into your `~/.claude/commands/` directory:

```bash
# macOS / Linux
git clone https://github.com/mofeed28/claude-learn.git
cd claude-learn
bash install.sh
```

```powershell
# Windows
git clone https://github.com/mofeed28/claude-learn.git
cd claude-learn
.\install.ps1
```

### Option 2: Manual

```bash
# Create the directory if it doesn't exist
mkdir -p ~/.claude/commands

# Copy the files
cp commands/learn.md ~/.claude/commands/
cp commands/learn-update.md ~/.claude/commands/
cp commands/learn-list.md ~/.claude/commands/
cp commands/learn-delete.md ~/.claude/commands/
cp commands/learn-audit.md ~/.claude/commands/
```

Then **restart Claude Code**.

---

## Usage

### `/learn {topic}` — Learn anything

```
/learn stripe
```

Searches the web for Stripe docs, scrapes them, and generates a complete skill at `~/.claude/skills/stripe/SKILL.md`.

Your agent now knows Stripe — endpoints, parameters, auth, error codes, code examples, the works.

### `/learn {topic} --quick` — Quick cheat sheet

```
/learn stripe --quick
```

Generates a condensed cheat sheet with the essentials: quick reference tables, top APIs, and a few code examples. Scrapes 5 sources.

### `/learn {topic} --deep` — Exhaustive deep dive

```
/learn stripe --deep
```

Generates an exhaustive skill covering the full API surface, edge cases, advanced patterns, testing, migration notes, and more. Scrapes up to 25 sources.

### `/learn {topic} --lang {language}` — Force a language

```
/learn stripe --lang python
/learn hono --lang typescript
```

Forces all code examples to use a specific language. By default, `/learn` auto-detects your project language from files like `package.json`, `requirements.txt`, `Cargo.toml`, etc.

### `/learn {topic} {topic}` — Multiple topics

```
/learn stripe hono
```

Processes each topic independently, generating a separate skill for each.

### `/learn {topic}:{subtopic}` — Focus on a specific area

```
/learn stripe:webhooks
/learn react:hooks
/learn aws:s3
```

Generates a skill focused on just that subtopic instead of the entire technology.

### `/learn {file-path}` — Learn from local files

```
/learn ./docs/api.yaml
/learn ./specs/openapi.json
/learn ~/Downloads/my-api.apib
```

**This produces the best results.** Reading a local file means no scraping failures, no missing content. Supports:

- Markdown (`.md`)
- API Blueprint (`.apib`)
- OpenAPI / Swagger (`.yaml`, `.yml`, `.json`)
- PDF (`.pdf`)
- Plain text (`.txt`)

### `/learn {url}` — Learn from a URL

```
/learn https://raw.githubusercontent.com/honojs/hono/main/README.md
```

Fetches the URL directly. If it fails (JS-rendered page), falls back to web search.

### `/learn {github-url}` — Learn from a GitHub repo

```
/learn https://github.com/honojs/hono
```

Extracts owner/repo, fetches the README, repo metadata, and docs folder automatically. This often produces better results than a plain topic name.

### `/learn @scope/package` — Scoped npm packages

```
/learn @tanstack/query
/learn @trpc/server
```

Handles scoped npm packages correctly — uses the full name for search and flattens to a slug (e.g. `tanstack-query`) for the skill directory.

### `/learn-update` — Refresh skills

```
/learn-update          # update all skills
/learn-update stripe   # update just one
```

Smart update with staleness detection:
- Checks package registries for the latest version before doing a full re-scrape
- Skips skills that are fresh (same version + less than 30 days old)
- Shows a diff of what changed: new endpoints, updated sections, deprecations
- Fetches changelogs between old and new versions
- Preserves user customizations (lines marked `<!-- user -->` and custom sections)

### `/learn-list` — See installed skills

```
/learn-list            # show all skills
/learn-list database   # filter by name, tag, or description
/learn-list framework  # filter by type
/learn-list python     # filter by language
```

Shows a rich table with type, version, language, generated date, staleness status, and quality grade (A/B/C).

### `/learn-audit` — Quality check skills

```
/learn-audit           # audit all skills
/learn-audit stripe    # audit one skill
/learn-audit --fix     # audit and auto-fix issues
```

Runs 27 quality checks across 4 categories (frontmatter, structure, code quality, formatting) without re-scraping. Assigns a letter grade (A-D) and reports exactly what's wrong. With `--fix`, automatically repairs issues that don't require web scraping (missing frontmatter fields, bare code blocks, pseudocode comments, etc.).

### `/learn-delete` — Remove a skill

```
/learn-delete stripe
```

Deletes a skill after confirmation. Supports partial name matching.

---

## What gets generated

A structured `SKILL.md` file that Claude Code automatically picks up:

```
~/.claude/skills/
  stripe/
    SKILL.md        <- auto-generated skill file
  drizzle-orm/
    SKILL.md
  react-hooks/
    SKILL.md
```

### Library type awareness

Every skill is classified as one of 8 types, and the template adapts:

| Type | Example | What gets emphasized |
|------|---------|---------------------|
| `api-client` | Stripe, OpenAI | Endpoint tables, auth setup, error codes, rate limits |
| `framework` | Hono, Express | Routing, middleware, project structure, deployment |
| `ui-library` | React, Shadcn | Component props, composition, styling, accessibility |
| `orm-db` | Drizzle, Prisma | Schema, queries, migrations, transactions |
| `cli-tool` | Vite, esbuild | Command reference, config files, flag combos |
| `utility` | Zod, date-fns | Function signatures, generics, tree-shaking |
| `platform` | Supabase, Firebase | IAM/credentials, service setup, pricing gotchas |
| `testing` | Vitest, Playwright | Assertions, mocking, fixtures, CI integration |

### Quality gate system

Every generated skill passes through 12 hard quality gates and a 6-dimension scoring rubric before being saved:

- **Completeness** — are all applicable sections filled?
- **Accuracy** — do params/types match official docs?
- **Code Quality** — are examples runnable with imports?
- **Trigger Coverage** — will an agent find this skill?
- **Actionability** — can an agent use this without external docs?
- **Structure** — tables vs prose, scanability

Skills that fail quality checks get automatically improved before saving.

### Skill contents

Each skill contains:
- **Frontmatter** with trigger keywords, version, language, type, tags, and generation date
- **Quick reference** tables (format adapts to library type)
- **API reference** with parameter tables, return types, and gotcha warnings
- **Working code examples** with imports (minimum 4 per skill, 8 in deep mode)
- **Error handling** tables with cause and fix columns
- **Setup/install** instructions
- **Prerequisites** and runtime requirements
- **TypeScript integration** patterns (for TS libraries)
- **Testing** patterns and mock utilities
- **Common mistakes** to avoid
- **Deprecated APIs** with replacements and version info
- **Migration notes** between major versions
- **Related skills** linking to other installed skills

Example frontmatter:
```yaml
---
name: stripe
description: Stripe payment processing API. Use when integrating payments, creating charges, managing subscriptions, handling webhooks, or working with Stripe Elements/Checkout.
version: "15.0.0"
generated: "2025-01-15"
language: typescript
type: api-client
tags: [payments, api, webhooks, sdk, billing]
---
```

---

## How it works

```
/learn stripe --lang python
    |
    v
Phase 1: Parse input (topic? flags? file? URL? subtopic?)
    |
    v
Phase 2: Detect project language (auto or --lang flag)
    |
    v
Phase 2.5: Classify library type (api-client, framework, etc.)
    |
    v
Phase 3: Multi-strategy web search (7 strategies)
         A. Official docs
         B. GitHub README + docs folder + homepage
         C. Tutorials & cheat sheets
         D. Sitemap discovery + docs index crawling
         E. Raw/fallback sources (GitHub wiki, StackOverflow, Wayback)
         F. Package registry (npm/pypi/crates/go/rubygems/hex)
         G. Changelog + migration guides (direct fetch)
    |
    v
Phase 4: Smart scraping pipeline
         4.1 URL queue with 1-5 priority scoring
         4.2 Parallel fetching with retry + exponential backoff
         4.3 Depth-1 link crawling (follow internal doc links)
         4.4 Structured content extraction
         4.5 Content deduplication
         4.6 Coverage tracking
    |
    v
Phase 5: Check for existing skill (update vs create)
    |
    v
Phase 6: Generate type-aware SKILL.md
         6.1 Frontmatter with type field
         6.2 Type-aware section emphasis
         6.3 Structured template with return types + gotchas
         6.4 Depth-specific section rules
         6.5 Strict quality rules for code + structure
    |
    v
Phase 7: Self-critique & quality gate
         7.1 Score on 6-dimension rubric (0-10 each)
         7.2 Pass 12 hard quality gates
         7.3 Auto-fix any dimension scoring below 7
         7.4 Report with quality scores to user
```

All using Claude Code's built-in tools: `WebSearch`, `WebFetch`, `Read`, `Write`, `Glob`, `Bash`.

---

## Commands reference

| Command | Description |
|---------|-------------|
| `/learn {topic}` | Generate a skill from web docs |
| `/learn {topic} --quick` | Quick cheat-sheet (5 sources) |
| `/learn {topic} --deep` | Exhaustive deep-dive (25 sources) |
| `/learn {topic} --lang {lang}` | Force example language |
| `/learn {topic}:{subtopic}` | Focus on a subtopic |
| `/learn {file}` | Generate from local file (best quality) |
| `/learn {url}` | Generate from a URL |
| `/learn {github-url}` | Generate from GitHub repo |
| `/learn @scope/pkg` | Scoped npm package support |
| `/learn-update` | Refresh all stale skills |
| `/learn-update {name}` | Refresh a specific skill |
| `/learn-list` | List all installed skills |
| `/learn-list {filter}` | Filter by name, tag, type, or language |
| `/learn-audit` | Quality check all skills |
| `/learn-audit {name}` | Quality check one skill |
| `/learn-audit --fix` | Auto-fix quality issues |
| `/learn-delete {name}` | Delete a skill |

---

## Limitations

Being honest about what a free solution can't do:

- **JS-rendered docs sites** (React docs, Vercel docs, etc.) may not scrape well with `WebFetch`. The command has fallbacks (GitHub raw READMEs, sitemaps, npm pages, Wayback Machine, GitHub wikis, StackOverflow) but a headless browser will always do better here.
- **Gated/authenticated docs** can't be scraped. Use local file mode instead: download the docs and run `/learn ./path/to/file`.
- **Very large APIs** (AWS, GCP) will be summarized to the most important parts. Use subtopic focus (`/learn aws:s3`) for better coverage.
- **Version detection** relies on package registries and web scraping — it may not always find the exact latest version.

**Workaround for any limitation:** Download the docs locally and use `/learn ./file`. This always produces the best output.

---

## Contributing

PRs welcome. Some ideas:

- [ ] Skill sharing — export/import skills between users
- [ ] Community skill registry
- [ ] Auto-update scheduler

---

## License

MIT

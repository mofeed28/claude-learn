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
- **No setup** — copy 4 files and restart

---

## Install

### Option 1: Quick copy (recommended)

Copy the 4 files from `commands/` into your `~/.claude/commands/` directory:

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

Generates a condensed ~3-page cheat sheet with the essentials: quick reference tables, top APIs, and a few code examples. Great for libraries you just need the basics on.

### `/learn {topic} --deep` — Exhaustive deep dive

```
/learn stripe --deep
```

Generates an exhaustive ~15-page skill covering the full API surface, edge cases, advanced patterns, testing, migration notes, and more.

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
/learn-list python     # filter by language
```

Shows a rich table with version, language, generated date, and staleness status.

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

Each skill contains:
- **Frontmatter** with trigger keywords, version, language, tags, and generation date
- **Quick reference** tables
- **API reference** with parameter tables
- **Working code examples** with imports (not pseudocode)
- **Error handling** guides
- **Setup/install** instructions
- **Prerequisites** and runtime requirements
- **TypeScript integration** patterns (for TS libraries)
- **Testing** patterns and mock utilities
- **Deprecated APIs** with replacements
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
Phase 3: Multi-strategy web search
         - Official docs
         - GitHub README
         - Tutorials & cheat sheets
         - Raw/fallback sources if JS sites fail
         - Package registry (npm/pypi/crates/go)
         - Changelog & migration guides
    |
    v
Phase 4: Scrape & extract (parallel fetching, soft-failure detection)
    |
    v
Phase 5: Check for existing skill (update vs create)
    |
    v
Phase 6: Generate structured SKILL.md (depth-aware, language-specific)
    |
    v
Phase 7: Verify & report to user
```

All using Claude Code's built-in tools: `WebSearch`, `WebFetch`, `Read`, `Write`, `Glob`, `Bash`.

---

## Limitations

Being honest about what a free solution can't do:

- **JS-rendered docs sites** (React docs, Vercel docs, etc.) may not scrape well with `WebFetch`. The command has fallbacks (GitHub raw READMEs, npm pages, Wayback Machine, blog posts) but a headless browser will always do better here.
- **Gated/authenticated docs** can't be scraped. Use local file mode instead: download the docs and run `/learn ./path/to/file`.
- **Very large APIs** (AWS, GCP) will be summarized to the most important parts. Use subtopic focus (`/learn aws:s3`) for better coverage.
- **Version detection** relies on package registries and web scraping — it may not always find the exact latest version.

**Workaround for any limitation:** Download the docs locally and use `/learn ./file`. This always produces the best output.

---

## Contributing

PRs welcome. Some ideas:

- [ ] Skill sharing — export/import skills between users
- [ ] Skill quality scoring
- [ ] Community skill registry
- [ ] Auto-update scheduler

---

## License

MIT

# /learn for Claude Code

**Teach your Claude Code agent any technology in seconds. No API keys. No subscriptions. Free.**

```
/learn stripe
/learn drizzle-orm
/learn react:hooks
/learn ./docs/my-api.yaml
```

Claude searches the web, scrapes the docs, and generates a skill file — all using built-in tools you already have.

---

## Why?

Claude Code agents are powerful, but they don't know every library or API out of the box. Instead of explaining the same docs over and over, just run `/learn` once and your agent has a permanent skill file it can reference anytime.

- **No API keys** — uses Claude Code's built-in WebSearch and WebFetch
- **No subscriptions** — completely free
- **No setup** — copy 3 files and restart

---

## Install

### Option 1: Quick copy (recommended)

Copy the 3 files from `commands/` into your `~/.claude/commands/` directory:

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

### `/learn-update` — Refresh skills

```
/learn-update          # update all skills
/learn-update stripe   # update just one
```

Re-scrapes the latest docs and merges new info into existing skills. Preserves your customizations.

### `/learn-list` — See installed skills

```
/learn-list
```

Shows a table of all installed skills with names, descriptions, and paths.

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
- **Frontmatter** with trigger keywords (so Claude knows when to use it)
- **Quick reference** tables
- **API reference** with parameter tables
- **Working code examples** (not pseudocode)
- **Error handling** guides
- **Setup/install** instructions

Example frontmatter:
```yaml
---
name: stripe
description: Stripe payment processing API. Use when integrating payments, creating charges, managing subscriptions, handling webhooks, or working with Stripe Elements/Checkout.
---
```

---

## How it works

```
/learn stripe
    |
    v
Phase 1: Parse input (topic? file? URL? subtopic?)
    |
    v
Phase 2: Multi-strategy web search
         - Official docs
         - GitHub README
         - Tutorials & cheat sheets
         - Raw/fallback sources if JS sites fail
    |
    v
Phase 3: Scrape & extract (parallel fetching)
    |
    v
Phase 4: Check for existing skill (update vs create)
    |
    v
Phase 5: Generate structured SKILL.md
    |
    v
Phase 6: Verify & report to user
```

All using Claude Code's built-in tools: `WebSearch`, `WebFetch`, `Read`, `Write`, `Glob`.

---

## Limitations

Being honest about what a free solution can't do:

- **JS-rendered docs sites** (React docs, Vercel docs, etc.) may not scrape well with `WebFetch`. The command has fallbacks (GitHub raw READMEs, npm pages, blog posts) but a headless browser will always do better here.
- **Gated/authenticated docs** can't be scraped. Use local file mode instead: download the docs and run `/learn ./path/to/file`.
- **Very large APIs** (AWS, GCP) will be summarized to the most important parts. Use subtopic focus (`/learn aws:s3`) for better coverage.

**Workaround for any limitation:** Download the docs locally and use `/learn ./file`. This always produces the best output.

---

## Contributing

PRs welcome. Some ideas:

- [ ] More fallback strategies for JS-heavy sites
- [ ] Skill sharing — export/import skills between users
- [ ] Skill quality scoring
- [ ] Community skill registry

---

## License

MIT

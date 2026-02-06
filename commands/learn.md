You are a skill generator for Claude Code. Your job is to research any technology, library, API, or framework and produce a high-quality Claude Code skill file from it — using only built-in tools (WebSearch, WebFetch, Read, Write, Glob, Bash).

The user wants to learn about: **$ARGUMENTS**

---

## Phase 1: Parse Input

Determine what the user is asking you to learn:

1. **If `$ARGUMENTS` is a file path or URL:**
   - If it's a local file path (e.g. `./docs/api.md`, `C:\docs\spec.apib`), read it directly with the Read tool. This is the **highest quality source** — skip web search and go straight to Phase 3.
   - If it's a URL, fetch it with WebFetch. If it succeeds, use it as the primary source and supplement with web search. If it fails, fall back to web search.

2. **If `$ARGUMENTS` is a topic name** (e.g. `stripe`, `drizzle-orm`, `hono`):
   - Proceed to Phase 2.

3. **If `$ARGUMENTS` contains a colon separator** (e.g. `stripe:payments` or `react:hooks`):
   - The part before `:` is the technology, the part after is the specific subtopic to focus on.

---

## Phase 2: Multi-Strategy Research

Run these search strategies **in parallel** where possible. The goal is to find the best sources, not all sources.

### Strategy A: Official Docs
```
WebSearch: "$ARGUMENTS official documentation"
WebSearch: "$ARGUMENTS API reference"
```

### Strategy B: GitHub Source
```
WebSearch: "$ARGUMENTS github repository README"
WebSearch: "site:github.com $ARGUMENTS"
```

### Strategy C: Practical Usage
```
WebSearch: "$ARGUMENTS getting started tutorial examples"
WebSearch: "$ARGUMENTS cheat sheet quick reference"
```

### Strategy D: Raw/Alternative Sources (fallback)
If the official docs are JS-rendered SPAs that WebFetch can't scrape, try these alternatives in order:
1. **GitHub raw README**: `https://raw.githubusercontent.com/{owner}/{repo}/main/README.md`
2. **GitHub API**: Use Bash with `gh api repos/{owner}/{repo}/readme --jq .content | base64 -d` if gh CLI is available
3. **npm/PyPI/crates.io pages**: These are usually scrapeable
4. **Dev.to / blog posts**: Often have comprehensive API overviews
5. **GitHub docs folder**: Search for `site:github.com/{owner}/{repo}/tree/main/docs`

---

## Phase 3: Scrape & Extract

From the best sources found, use WebFetch (or Read for local files) to extract:

- **Architecture & core concepts** — what is it, how does it work
- **API surface** — endpoints, methods, functions, classes, hooks
- **Parameters & types** — every parameter, its type, required/optional, defaults
- **Authentication & config** — how to set up, API keys, env vars
- **Code examples** — real working examples, not pseudocode
- **Common patterns** — typical usage workflows
- **Error handling** — error codes, common pitfalls, troubleshooting
- **Gotchas & rules** — case sensitivity, rate limits, security considerations

**Scraping rules:**
- Fetch pages in parallel (3-5 at a time) for speed
- If a page fails, don't retry more than once — move to the next source
- Prioritize: Official docs > GitHub README > API reference > Blog posts
- For large docs, focus on the core API and most-used features. A skill that covers 80% well is better than 100% poorly.

---

## Phase 4: Check for Existing Skill

Before generating, check if a skill already exists:
```
Glob: ~/.claude/skills/$SLUG/SKILL.md
```

- If it exists, **read it first**. You are updating, not creating from scratch. Preserve any user customizations or notes at the bottom of the file. Inform the user you're updating an existing skill.
- If it doesn't exist, create it fresh.

---

## Phase 5: Generate the Skill

Derive the slug: lowercase the topic name, replace spaces and special characters with hyphens.
Example: `Drizzle ORM` → `drizzle-orm`, `Stripe Payments` → `stripe-payments`

Create the directory and file at: `~/.claude/skills/{slug}/SKILL.md`

### Required Structure

```markdown
---
name: {slug}
description: {A specific, trigger-word-rich sentence. This is what Claude uses to decide when to activate the skill. Be precise. Bad: "Helps with Stripe". Good: "Stripe payment processing API. Use when integrating payments, creating charges, managing subscriptions, handling webhooks, or working with Stripe Elements/Checkout."}
---

# {Technology Name} Skill

## When to Use This Skill

Use this skill when the user needs to:
- {5-10 specific trigger scenarios as bullet points}

## Overview

{2-3 sentences: what it is, what problem it solves, key characteristics}

**Key links:**
- Docs: {url}
- GitHub: {url}
- Package: {npm/pip/cargo url}

## Quick Reference

{The most important info at a glance. Use a table for API endpoints, CLI commands, or method signatures. This section should answer "what's the most common thing I need to do?" in 10 seconds.}

## Installation & Setup

{How to install, configure, authenticate. Include actual commands.}

## Core Concepts

{Key mental models the agent needs. Keep it brief — bullet points or short paragraphs, not essays.}

## API Reference

{The meat of the skill. Detailed parameter tables, method signatures, endpoints.}

### {Endpoint/Method Group 1}

{Description}

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| ... | ... | ... | ... | ... |

**Example:**
```{language}
// real working code example
```

## Common Patterns

{3-5 typical usage patterns with complete, working code examples}

## Error Handling

{Common errors, what causes them, how to fix them}

| Error | Cause | Fix |
|-------|-------|-----|
| ... | ... | ... |

## Important Rules

{Numbered list of critical things to remember}

1. **{Rule}** — {explanation}
2. ...
```

### Quality Rules

- **Tables over prose** for anything with parameters, options, or codes
- **Real code examples** — never pseudocode, never `// do something here`
- **No placeholder sections** — if you don't have info for a section, omit it entirely rather than writing "TODO" or "See docs"
- **No real API keys** — always use `YOUR_API_KEY`, `YOUR_SECRET`, etc.
- **Case-sensitive names** — match the exact casing from official docs
- **Include imports** in code examples — agents need complete, copy-pasteable code
- **Concise** — if a section would exceed 50 lines, break it into subsections or trim to the most important parts

---

## Phase 6: Verify & Report

After writing the file:

1. Read it back with the Read tool
2. Verify:
   - Frontmatter has `name` and `description`
   - Description contains specific trigger words (not generic)
   - At least 3 code examples exist
   - No `TODO`, `TBD`, `...`, or placeholder text remains
   - Tables are properly formatted
3. Report to the user:
   - Skill path: `~/.claude/skills/{slug}/SKILL.md`
   - Sources used (list the URLs you successfully scraped)
   - Coverage assessment: what % of the API/docs you covered
   - Anything you couldn't find or that needs manual additions
   - If sources were limited, suggest: "If you have local docs or an API spec file, run `/learn path/to/file` for a more complete skill"

---

## Special Modes

### Update mode
If the user runs `/learn {topic}` and the skill already exists, you are updating it. Merge new information with existing content. Don't lose existing customizations.

### Focused mode
If the user uses colon syntax like `/learn react:hooks` or `/learn stripe:webhooks`, generate a skill focused specifically on that subtopic, not the entire technology.

### Local file mode
If the user passes a file path like `/learn ./docs/api.yaml` or `/learn C:\specs\openapi.json`, read the file directly. This produces the best quality skills because you have the raw source. Support these formats:
- Markdown (.md)
- API Blueprint (.apib)
- OpenAPI/Swagger (.yaml, .yml, .json)
- Plain text (.txt)
- PDF (.pdf)
- Any other text-based format

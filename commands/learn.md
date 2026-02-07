You are a skill generator for Claude Code. Your job is to research any technology, library, API, or framework and produce a high-quality Claude Code skill file from it — using only built-in tools (WebSearch, WebFetch, Read, Write, Glob, Bash).

The user wants to learn about: **$ARGUMENTS**

---

## Phase 1: Parse Input

Determine what the user is asking you to learn. Parse `$ARGUMENTS` into these components:

### 1.1 Extract Flags

Scan `$ARGUMENTS` for flags and remove them from the topic string:

| Flag | Effect |
|------|--------|
| `--quick` | Cheat-sheet mode: aim for ~3 pages, skip deep API reference, focus on quick-reference tables and 3-5 code examples |
| `--deep` | Exhaustive mode: aim for ~15 pages, cover full API surface, include edge cases, advanced patterns, internals |
| `--lang {language}` | Force a specific language for examples (e.g. `--lang python`, `--lang rust`). Overrides auto-detection |

If no depth flag is given, default to **balanced** mode (~8 pages).

Store the detected flags for use in later phases.

### 1.2 Handle Multiple Topics

If `$ARGUMENTS` contains multiple space-separated topics (after removing flags), run the **entire pipeline** (Phases 1-7) for each topic independently. Example: `/learn stripe hono` processes `stripe` and `hono` as separate skills.

### 1.3 Classify Each Topic

For each topic, determine its type:

1. **Local file path** (e.g. `./docs/api.md`, `C:\docs\spec.apib`)
   - Read it directly with the Read tool. This is the **highest quality source** — skip web search and go straight to Phase 3.

2. **GitHub URL** (matches `github.com/{owner}/{repo}`)
   - Extract `{owner}` and `{repo}` from the URL.
   - Fetch the README via `https://raw.githubusercontent.com/{owner}/{repo}/main/README.md` (try `master` if `main` fails).
   - Fetch repo metadata via Bash: `gh api repos/{owner}/{repo}` to get description, topics, language, stars.
   - Check for a docs folder via Bash: `gh api repos/{owner}/{repo}/contents/docs` — if it exists, fetch key `.md` files from it.
   - Use the repo name as the topic for web search in Phase 2.

3. **Other URL** (any non-GitHub URL)
   - Fetch it with WebFetch. If it succeeds, use it as the primary source and supplement with web search. If it fails, fall back to web search.

4. **Scoped npm package** (matches `@scope/name`, e.g. `@tanstack/query`)
   - Use the full scoped name (e.g. `@tanstack/query`) for all web searches.
   - Derive the slug by flattening: `@tanstack/query` → `tanstack-query`.

5. **Topic with subtopic** (contains `:`, e.g. `stripe:webhooks`, `react:hooks`)
   - The part before `:` is the technology, the part after is the specific subtopic to focus on.

6. **Plain topic name** (e.g. `stripe`, `drizzle-orm`, `hono`)
   - Proceed to Phase 2.

---

## Phase 2: Detect Project Language

Before researching, check the user's working directory to detect their project language. This tailors examples to what they're actually using.

Check these files (in order, stop at first match):

| File | Language |
|------|----------|
| `package.json` | JavaScript/TypeScript (check for `"typescript"` in devDependencies to distinguish) |
| `tsconfig.json` | TypeScript |
| `requirements.txt` | Python |
| `pyproject.toml` | Python |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `Gemfile` | Ruby |
| `build.gradle` or `pom.xml` | Java/Kotlin |
| `*.csproj` or `*.sln` | C# |

Use Glob to quickly check: `{package.json,tsconfig.json,requirements.txt,pyproject.toml,Cargo.toml,go.mod,Gemfile,build.gradle,pom.xml,*.csproj,*.sln}`

If `--lang` flag was provided, it **overrides** auto-detection.

If no language is detected and no flag is given, generate language-agnostic examples or use the library's primary/most popular language.

Store the detected language as `$LANGUAGE` for use in Phase 5.

---

## Phase 3: Multi-Strategy Research

Run these search strategies **in parallel** where possible. The goal is to find the best sources, not all sources.

**Before searching, build a URL queue.** As you discover URLs from search results, add them all to a running list. De-duplicate by normalized URL (strip trailing slashes, fragments, and tracking params like `utm_*`). Score each URL by source priority (see Phase 4) before fetching.

### Strategy A: Official Docs
```
WebSearch: "$TOPIC official documentation"
WebSearch: "$TOPIC API reference"
```

### Strategy B: GitHub Source
```
WebSearch: "$TOPIC github repository README"
WebSearch: "site:github.com $TOPIC"
```

When you find the GitHub repo, also:
1. Fetch the repo metadata: `gh api repos/{owner}/{repo}` to get `homepage` URL (this is often the docs site)
2. Check for docs in the repo: `gh api repos/{owner}/{repo}/contents/docs` — queue any `.md` files found
3. Check for a `docs` or `website` directory that might contain structured documentation

### Strategy C: Practical Usage
```
WebSearch: "$TOPIC getting started tutorial examples"
WebSearch: "$TOPIC cheat sheet quick reference"
```

### Strategy D: Sitemap & Link Discovery

**This is a high-value strategy.** Before falling back to alternative sources, try to discover the full documentation structure:

1. **Sitemap discovery** — Try fetching these URLs (in parallel) for the official docs domain:
   ```
   WebFetch: {docs_base_url}/sitemap.xml
   WebFetch: {docs_base_url}/sitemap-0.xml
   WebFetch: {docs_base_url}/sitemap_index.xml
   ```
   If a sitemap is found, parse it for all `<loc>` URLs. Filter to keep only documentation-relevant paths (containing `/docs/`, `/api/`, `/guide/`, `/reference/`, `/tutorial/`, `/getting-started/`). Add these to the URL queue — they are high-quality sources.

2. **Docs index page crawling** — Fetch the main docs page and extract internal links from:
   - Sidebar navigation (`<nav>`, `role="navigation"`, class names containing `sidebar`, `nav`, `menu`, `toc`)
   - Table of contents sections
   - "Next/Previous" pagination links
   - Any links with paths matching `/docs/`, `/api/`, `/guide/`, `/reference/`

   Add discovered internal doc links to the URL queue. This often reveals 10-50 pages that search alone would miss.

3. **robots.txt check** — Fetch `{docs_base_url}/robots.txt` to find `Sitemap:` directives pointing to the sitemap URL. Also respect `Disallow` rules — skip paths that are disallowed.

### Strategy E: Raw/Alternative Sources (fallback)
If the official docs are JS-rendered SPAs that WebFetch can't scrape, try these alternatives in order:
1. **GitHub raw README**: `https://raw.githubusercontent.com/{owner}/{repo}/main/README.md`
2. **GitHub API**: Use Bash with `gh api repos/{owner}/{repo}/readme --jq .content | base64 -d` if gh CLI is available
3. **npm/PyPI/crates.io pages**: These are usually scrapeable
4. **Dev.to / blog posts**: Often have comprehensive API overviews
5. **GitHub docs folder**: Fetch docs from `https://raw.githubusercontent.com/{owner}/{repo}/main/docs/` — try fetching key `.md` files (README.md, getting-started.md, api.md, guide.md, etc.)
6. **Wayback Machine**: Try `https://web.archive.org/web/{docs_url}` for JS-rendered sites that can't be scraped directly
7. **GitHub wiki**: Try `https://raw.githubusercontent.com/wiki/{owner}/{repo}/Home.md` — many projects keep detailed docs in their wiki
8. **StackOverflow consolidated answers**: `WebSearch: "site:stackoverflow.com $TOPIC [tag] answers:1 score:10"` — high-scored answers often contain canonical usage patterns

**Soft failure detection:** When fetching any page, check if the response is a soft failure:
- Content is less than 500 characters
- Content contains "sign in", "access denied", "log in to continue", "enable javascript", "403", "404", "not found"
- Content is mostly navigation/boilerplate with no real documentation (ratio of links to text > 3:1)
- Content is identical or near-identical (>90% overlap) to an already-fetched page

If a soft failure is detected, discard the result and move to the next source.

### Strategy F: Package Registry
Search the relevant package registry to get version info, README, and metadata:
```
WebSearch: "site:npmjs.com $TOPIC"        (for JS/TS)
WebSearch: "site:pypi.org $TOPIC"         (for Python)
WebSearch: "site:crates.io $TOPIC"        (for Rust)
WebSearch: "site:pkg.go.dev $TOPIC"       (for Go)
WebSearch: "site:rubygems.org $TOPIC"     (for Ruby)
WebSearch: "site:hex.pm $TOPIC"           (for Elixir)
```
Pick the registry that matches the detected `$LANGUAGE`, or search npm + pypi as defaults.

From registry pages, extract: **current version**, **publish date**, **weekly downloads**, **peer dependencies**.

### Strategy G: Changelog / Migration
```
WebSearch: "$TOPIC changelog breaking changes"
WebSearch: "site:github.com $TOPIC releases"
```
From these results, extract: **recent breaking changes**, **deprecated APIs**, **migration guides between major versions**.

Also try fetching directly:
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/main/CHANGELOG.md
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/main/MIGRATION.md
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/main/UPGRADING.md
```

---

## Phase 4: Scrape & Extract

### 4.1 URL Queue Management

Before scraping, process the URL queue built during Phase 3:

1. **De-duplicate**: Normalize all URLs (lowercase domain, strip trailing `/`, remove fragments `#...`, remove tracking params `utm_*`, `ref=`, `source=`). Remove exact duplicates.
2. **Score & prioritize** each URL on a 1-5 scale:

| Score | Source Type | Example |
|-------|-------------|---------|
| 5 | Official API reference page | `docs.stripe.com/api/charges` |
| 5 | Sitemap-discovered doc pages | Pages found via sitemap.xml |
| 4 | Official guides / getting started | `docs.stripe.com/guides/...` |
| 4 | GitHub README / docs folder `.md` files | `raw.githubusercontent.com/...` |
| 3 | Package registry pages (npm, PyPI, etc.) | `npmjs.com/package/stripe` |
| 3 | GitHub wiki pages | `github.com/.../wiki/...` |
| 2 | Blog posts / tutorials (dev.to, medium) | `dev.to/...` |
| 2 | StackOverflow answers | `stackoverflow.com/questions/...` |
| 1 | Wayback Machine snapshots | `web.archive.org/...` |
| 1 | Unrelated or generic pages | Anything not clearly about $TOPIC |

3. **Sort** the queue by score (highest first). Within the same score, prefer shorter URL paths (closer to doc root = more important pages).
4. **Cap the queue** based on depth mode:
   - `--quick`: Fetch top 5 URLs
   - default: Fetch top 12 URLs
   - `--deep`: Fetch top 25 URLs

### 4.2 Fetching with Retry & Backoff

Use WebFetch (or Read for local files) to fetch pages from the sorted queue.

**Retry strategy:**
- On first failure (timeout, network error, 5xx status): wait **2 seconds**, then retry
- On second failure: wait **4 seconds**, then retry
- On third failure: **discard the URL** and move to the next one in the queue
- Do NOT retry on 4xx errors (404, 403, 401) — these are permanent failures
- Do NOT retry on soft failures (sign-in walls, empty pages) — discard immediately

**Parallel fetching:**
- Fetch in batches of **5 URLs at a time** (use parallel WebFetch calls)
- After each batch completes, check if you have enough content for the current depth mode. If you already have comprehensive coverage of the API surface, you can stop early — don't fetch more than needed
- Between batches, briefly assess what content areas are still missing (e.g., "have API reference but no error handling docs") and prioritize remaining URLs that are likely to fill those gaps

### 4.3 Link Crawling (Depth-1)

After fetching each page, scan the content for internal documentation links — links to other pages on the **same domain** that point to doc content. Look for:

- Links in navigation/sidebar sections
- "See also", "Related", "Next steps" links
- Links to sub-pages of API reference (e.g., `/api/charges/create` linked from `/api/charges`)
- Links matching patterns: `/docs/`, `/api/`, `/guide/`, `/reference/`, `/tutorial/`

**Rules for link crawling:**
- Only crawl **one level deep** (don't follow links from crawled pages)
- Only follow links on the **same domain** as the source page
- Add discovered links to the URL queue with a score of 4 (they're from official docs)
- Still respect the URL cap for the current depth mode
- Skip links that match already-fetched URLs (de-duplicate before fetching)
- Skip anchor-only links (`#section`), query-only variations, and non-doc paths (`/blog/`, `/pricing/`, `/login/`, `/careers/`)

### 4.4 Content Extraction

From fetched pages, extract:

- **Architecture & core concepts** — what is it, how does it work
- **API surface** — endpoints, methods, functions, classes, hooks
- **Parameters & types** — every parameter, its type, required/optional, defaults
- **Authentication & config** — how to set up, API keys, env vars
- **Code examples** — real working examples, not pseudocode
- **Common patterns** — typical usage workflows
- **Error handling** — error codes, common pitfalls, troubleshooting
- **Gotchas & rules** — case sensitivity, rate limits, security considerations
- **Version info** — current stable version, minimum runtime version, LTS status
- **Deprecated patterns** — what NOT to use, with replacement APIs and the version they were deprecated in
- **Testing patterns** — how to mock/test code using this library, test utilities provided

### 4.5 Content Deduplication

As you extract content, track what information you've already collected. Before adding content from a new page:

1. **Skip duplicate sections** — if a page covers the exact same API methods/endpoints you already have with no new parameters or examples, skip it
2. **Merge complementary info** — if a new page adds parameters, examples, or edge cases to an API you already documented, merge the new details into your existing notes
3. **Prefer official sources** — if two pages conflict (different parameter names, different defaults), prefer the higher-scored source
4. **Track coverage** — maintain a mental checklist of what you've covered vs. what's still missing:
   - [ ] Core API methods/functions
   - [ ] Installation & setup
   - [ ] Authentication/configuration
   - [ ] Error codes & handling
   - [ ] Code examples (at least 3)
   - [ ] TypeScript types (if applicable)
   - [ ] Common patterns/workflows
   - [ ] Deprecations & migration notes

### 4.6 Scraping Rules Summary

- For large docs, focus on the core API and most-used features. A skill that covers 80% well is better than 100% poorly
- If the URL queue runs dry before you have enough content, go back to Phase 3 and run additional targeted searches for the missing areas
- If a whole docs site is unscrappable (JS SPA, auth wall), note this in the Phase 7 report and suggest the user provide local docs via `/learn ./path/to/docs`

---

## Phase 5: Check for Existing Skill

Before generating, check if a skill already exists:
```
Glob: ~/.claude/skills/$SLUG/SKILL.md
```

- If it exists, **read it first**. You are updating, not creating from scratch. Preserve any user customizations or notes (especially lines/sections marked with `<!-- user -->`). Inform the user you're updating an existing skill.
- If it doesn't exist, create it fresh.

---

## Phase 6: Generate the Skill

Derive the slug: lowercase the topic name, replace spaces and special characters with hyphens.
- `Drizzle ORM` → `drizzle-orm`
- `Stripe Payments` → `stripe-payments`
- `@tanstack/query` → `tanstack-query` (remove `@`, replace `/` with `-`)
- `react:hooks` → `react-hooks`

Create the directory and file at: `~/.claude/skills/{slug}/SKILL.md`

### Required Structure

```markdown
---
name: {slug}
description: {A specific, trigger-word-rich sentence. This is what Claude uses to decide when to activate the skill. Be precise. Bad: "Helps with Stripe". Good: "Stripe payment processing API. Use when integrating payments, creating charges, managing subscriptions, handling webhooks, or working with Stripe Elements/Checkout."}
version: "{current stable version, e.g. 4.2.1}"
generated: "{YYYY-MM-DD}"
language: {detected language, e.g. typescript, python, rust — or "multi" if multi-language}
tags: [{3-8 relevant tags, e.g. payments, api, webhooks, sdk}]
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

## Prerequisites

{Only include if there are specific requirements. Omit if standard.}
- Runtime: {e.g. Node.js >= 18, Python >= 3.9}
- Peer dependencies: {if any}
- Related skills: {if other installed skills pair with this one}

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
import { ... } from '...';
// real working code example with imports
```

## Common Patterns

{3-5 typical usage patterns with complete, working code examples}

## Error Handling

{Common errors, what causes them, how to fix them}

| Error | Cause | Fix |
|-------|-------|-----|
| ... | ... | ... |

## TypeScript Integration

{Only include for JS/TS libraries. Key types, generics, inference patterns.}

## Testing

{How to mock/test code using this library. Test utilities provided.}

## Deprecated / Avoid

{Only include if deprecated patterns were found. Table format:}

| Deprecated API | Replacement | Since Version |
|----------------|-------------|---------------|
| ... | ... | ... |

## Migration Notes

{Only include if breaking changes between major versions were found.}

### v{X} → v{Y}
- {Breaking change 1}
- {Breaking change 2}

## Important Rules

{Numbered list of critical things to remember}

1. **{Rule}** — {explanation}
2. ...

## Related Skills

{Only include if other installed skills are relevant. Check with Glob: ~/.claude/skills/*/SKILL.md}

- `{skill-name}` — {how it relates}
```

### Section Rules by Depth

| Section | `--quick` | default | `--deep` |
|---------|-----------|---------|----------|
| When to Use | 3-5 bullets | 5-10 bullets | 5-10 bullets |
| Overview | 1-2 sentences | 2-3 sentences | 3-5 sentences |
| Prerequisites | omit | include if relevant | always include |
| Quick Reference | include | include | include |
| Installation & Setup | include | include | include |
| Core Concepts | 3-5 bullets | full section | full + advanced |
| API Reference | top 5-10 APIs | core APIs | full API surface |
| Common Patterns | 2-3 patterns | 3-5 patterns | 5-10 patterns |
| Error Handling | top 3-5 errors | full table | full + edge cases |
| TypeScript Integration | omit | include if TS | full section |
| Testing | omit | include if found | full section |
| Deprecated / Avoid | omit | include if found | full table |
| Migration Notes | omit | latest version only | all recent majors |
| Important Rules | 3-5 rules | 5-10 rules | 10+ rules |
| Related Skills | omit | include | include |

### Quality Rules

- **Tables over prose** for anything with parameters, options, or codes
- **Real code examples** — never pseudocode, never `// do something here`
- **No placeholder sections** — if you don't have info for a section, omit it entirely rather than writing "TODO" or "See docs"
- **No real API keys** — always use `YOUR_API_KEY`, `YOUR_SECRET`, etc.
- **Case-sensitive names** — match the exact casing from official docs
- **Include imports** in every code example — agents need complete, copy-pasteable code
- **Language-specific examples** — all code examples must be in `$LANGUAGE`. If multi-language, use the detected project language, falling back to the library's primary language
- **Concise** — if a section would exceed 50 lines, break it into subsections or trim to the most important parts
- **All code blocks must have a language specifier** (```typescript, ```python, etc. — never bare ```)
- **No `any` types in TypeScript examples** — use proper types, generics, or `unknown` if truly needed

---

## Phase 7: Verify & Report

After writing the file:

1. Read it back with the Read tool
2. Verify:
   - Frontmatter has `name`, `description`, `version`, `generated`, `language`, and `tags`
   - Description contains specific trigger words (not generic) and is at least 20 words
   - All code blocks have a language specifier (no bare ```)
   - Every code example includes import statements
   - No `any` types in TypeScript examples
   - All markdown tables have consistent column counts (no mismatched `|` separators)
   - At least 3 code examples exist (at least 2 in `--quick` mode)
   - No `TODO`, `TBD`, `...`, or placeholder text remains
   - Tables are properly formatted
   - File is between 50-500 lines (warn if outside this range — under 50 means too sparse, over 500 means consider splitting)
3. Fix any issues found during verification before reporting
4. Report to the user:
   - Skill path: `~/.claude/skills/{slug}/SKILL.md`
   - Version detected: `{version}`
   - Language: `{language}`
   - Sources used (list the URLs you successfully scraped)
   - Coverage assessment: what % of the API/docs you covered
   - Anything you couldn't find or that needs manual additions
   - If sources were limited, suggest: "If you have local docs or an API spec file, run `/learn path/to/file` for a more complete skill"

---

## Special Modes

### Update mode
If the user runs `/learn {topic}` and the skill already exists, you are updating it. Merge new information with existing content. Don't lose existing customizations. Preserve any lines or sections marked with `<!-- user -->`.

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

### GitHub URL mode
If the user passes a GitHub URL like `/learn https://github.com/honojs/hono`, extract the owner/repo, fetch the README, metadata, and docs folder, then supplement with web search. This often produces better results than a plain topic name because you get the exact source.

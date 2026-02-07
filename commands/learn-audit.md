You are a skill auditor for Claude Code. Your job is to evaluate the quality of existing skill files and fix issues — without re-scraping the web. This is a local-only operation that reads, scores, and optionally rewrites skills to meet quality standards.

Target: **$ARGUMENTS**

---

## Step 1: Find Skills to Audit

If `$ARGUMENTS` is empty or "all":
- Use Glob to find all skills: `~/.claude/skills/*/SKILL.md`
- Audit every skill found

If `$ARGUMENTS` is a specific skill name:
- Find `~/.claude/skills/{$ARGUMENTS}/SKILL.md`
- If not found, try partial match: `~/.claude/skills/*{$ARGUMENTS}*/SKILL.md`
- If not found, report error and suggest `/learn-list`

---

## Step 2: Run Quality Audit (per skill)

Read the entire SKILL.md file. Run every check below and record pass/fail.

### 2.1 Frontmatter Checks

| Check | ID | Pass condition |
|-------|----|---------------|
| Has `name` field | F1 | Present and non-empty |
| Has `description` field | F2 | Present, non-empty, 20+ words |
| Has `version` field | F3 | Present and non-empty |
| Has `generated` field | F4 | Present, valid date format (YYYY-MM-DD) |
| Has `language` field | F5 | Present and non-empty |
| Has `type` field | F6 | Present and one of: api-client, framework, ui-library, orm-db, cli-tool, utility, platform, testing |
| Has `tags` field | F7 | Present, array with 3-8 items |
| Description has trigger words | F8 | Contains at least 3 specific verbs or nouns (not just "helps with X") |

### 2.2 Structure Checks

| Check | ID | Pass condition |
|-------|----|---------------|
| Has "When to Use" section | S1 | Section exists with 3+ bullet points |
| Has "Overview" section | S2 | Section exists with 2+ sentences |
| Has "Quick Reference" section | S3 | Section exists and contains at least one table |
| Has "Installation & Setup" section | S4 | Section exists with at least one code block |
| Has "Core Concepts" section | S5 | Section exists with 3+ bullet points or paragraphs |
| Has "API Reference" section | S6 | Section exists with at least one parameter table |
| Has "Common Patterns" section | S7 | Section exists with 2+ code examples |
| Has "Error Handling" section | S8 | Section exists and contains a table |
| Has "Important Rules" section | S9 | Section exists with 3+ numbered rules |

### 2.3 Code Quality Checks

| Check | ID | Pass condition |
|-------|----|---------------|
| Minimum code examples | C1 | 4+ code blocks (2+ for skills under 100 lines) |
| All code blocks have language specifier | C2 | No bare ``` — every block has ```typescript, ```python, etc. |
| Code examples have imports | C3 | At least 75% of non-bash code blocks contain `import` or `require` or `from` |
| No `any` types in TypeScript | C4 | No `: any` or `as any` in TypeScript code blocks |
| No pseudocode | C5 | No `// do something here`, `// TODO`, `// ...` in code blocks |
| No placeholder content | C6 | No `TODO`, `TBD`, `FIXME`, `XXX` anywhere in the file |

### 2.4 Formatting Checks

| Check | ID | Pass condition |
|-------|----|---------------|
| Tables are well-formed | T1 | All tables have consistent column counts per row |
| File length is reasonable | T2 | Between 80-500 lines |
| No duplicate headings | T3 | No two sections share the same heading |
| Section order follows template | T4 | Sections appear in the standard order (When to Use → Overview → ... → Related Skills) |

---

## Step 3: Score the Skill

### Calculate scores

Count total checks and passes:
- **Frontmatter**: F1-F8 (8 checks)
- **Structure**: S1-S9 (9 checks)
- **Code Quality**: C1-C6 (6 checks)
- **Formatting**: T1-T4 (4 checks)
- **Total**: 27 checks

### Assign grade

| Grade | Criteria |
|-------|----------|
| **A** | 24-27 checks pass (90%+) |
| **B** | 19-23 checks pass (70-89%) |
| **C** | 14-18 checks pass (50-69%) |
| **D** | Below 14 checks pass (<50%) |

---

## Step 4: Report Results

### For a single skill:

```
Audit: {name} ({version})
Path: ~/.claude/skills/{name}/SKILL.md
Grade: {grade} ({passes}/{total} checks passed)

Frontmatter ({X}/8):
  ✓ F1: Has name
  ✓ F2: Has description (23 words)
  ✗ F6: Missing type field
  ✗ F7: Tags has only 2 items (need 3-8)
  ...

Structure ({X}/9):
  ✓ S1: Has "When to Use" (7 bullets)
  ✗ S8: Error Handling section has no table
  ...

Code Quality ({X}/6):
  ✓ C1: 6 code examples found
  ✗ C2: 2 code blocks missing language specifier (lines 45, 89)
  ...

Formatting ({X}/4):
  ✓ T1: All tables well-formed
  ✗ T2: File is 52 lines (minimum 80)
  ...

{If grade C or D:}
Fix these issues with: /learn {name} --deep
Or manually edit: ~/.claude/skills/{name}/SKILL.md
```

### For multiple skills:

```
Skill Audit Report ({count} skills):

| # | Skill | Grade | Front. | Struct. | Code | Format. | Top Issue |
|---|-------|-------|--------|---------|------|---------|-----------|
| 1 | stripe | A | 8/8 | 9/9 | 5/6 | 4/4 | C4: has `any` type |
| 2 | hono | B | 7/8 | 7/9 | 6/6 | 4/4 | F6: missing type, S8: no error table |
| 3 | zod | D | 4/8 | 3/9 | 2/6 | 2/4 | Needs full regeneration |

Summary:
  A: 1 skill (excellent)
  B: 1 skill (good)
  C: 0 skills
  D: 1 skill (needs work)

Quick fixes (won't require re-scraping):
  hono: Add `type: framework` to frontmatter
  stripe: Replace `any` with proper types on line 142

Full regeneration recommended:
  zod: /learn zod --deep
```

---

## Step 5: Auto-Fix (if requested)

If the user passes `--fix` in $ARGUMENTS (e.g., `/learn-audit stripe --fix` or `/learn-audit --fix`):

Apply automatic fixes for issues that can be resolved without web scraping:

| Fix | What it does |
|-----|-------------|
| F6 missing `type` | Infer type from description/tags and add to frontmatter |
| F7 too few tags | Infer additional tags from description and section content |
| C2 bare code blocks | Add language specifier based on `language` in frontmatter |
| C5 pseudocode comments | Remove `// ...` and `// TODO` lines from code blocks |
| C6 placeholder text | Remove lines containing `TODO`, `TBD`, `FIXME` |
| T3 duplicate headings | Merge duplicate sections, keeping the longer one |
| S3 Quick Reference without table | Convert any lists in Quick Reference to a table |
| S8 Error Handling without table | Convert any prose in Error Handling to a table if possible |

**Rules for auto-fix:**
- Always read the file before editing
- Preserve all `<!-- user -->` marked content
- After fixing, re-run the audit to confirm improvements
- Report what was fixed and what still needs manual attention
- Do NOT modify code examples beyond removing pseudocode comments — never rewrite working code

**After auto-fix, show:**
```
Auto-fix applied to {name}:
  ✓ F6: Added type: framework (inferred from routing/middleware keywords)
  ✓ C2: Added language specifier to 2 code blocks
  ✗ S8: Could not auto-fix — Error Handling section needs manual table conversion

Grade: C → B (improved from 16/27 to 21/27)
```

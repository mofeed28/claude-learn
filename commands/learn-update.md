You are a skill updater for Claude Code. Your job is to refresh all existing skills (or a specific one) with the latest information from the web.

Target: **$ARGUMENTS**

---

## If `$ARGUMENTS` is empty or "all":

1. Use Glob to find all skills: `~/.claude/skills/*/SKILL.md`
2. For each skill found:
   - Read the SKILL.md
   - Extract the `name` from frontmatter
   - Extract the key links (docs URLs) from the Overview section
   - Run a quick WebSearch for `{name} documentation changelog latest`
   - WebFetch the key docs links to check for updates
   - If new info is found (new endpoints, changed parameters, new features), update the skill in place
   - If nothing changed, skip it
3. Report: which skills were updated, which were unchanged, which failed

## If `$ARGUMENTS` is a specific skill name:

1. Find and read `~/.claude/skills/{$ARGUMENTS}/SKILL.md`
2. Extract the technology name and doc URLs
3. Run full research (same as `/learn` Phase 2) to find latest docs
4. Scrape the latest documentation
5. Merge new information into the existing skill, preserving structure and any user customizations
6. Report what changed

---

## Update Rules

- **Never delete existing content** unless it's confirmed outdated/wrong
- **Preserve user customizations** — if there are sections or notes that don't match standard structure, keep them
- **Add a comment at the bottom** with the update date:
  ```
  <!-- Last updated: YYYY-MM-DD -->
  ```
- **Report changes clearly** — tell the user exactly what was added, modified, or flagged as potentially outdated
- If a source URL is dead, flag it and try to find the new URL

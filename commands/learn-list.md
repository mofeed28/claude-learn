You are a skill manager for Claude Code. List and summarize all installed skills.

---

## Steps

1. Use Glob to find all skills: `~/.claude/skills/*/SKILL.md`
2. For each skill found, read just the frontmatter (first 10 lines) to extract `name` and `description`
3. Present a clean table to the user:

| # | Skill | Description | Path |
|---|-------|-------------|------|
| 1 | {name} | {description truncated to ~60 chars} | ~/.claude/skills/{slug}/ |

4. Show total count
5. Suggest available commands:
   - `/learn {topic}` — learn a new skill
   - `/learn-update` — refresh all skills
   - `/learn-update {name}` — refresh a specific skill
   - `/learn {topic}:{subtopic}` — learn a focused subtopic
   - `/learn ./path/to/file` — learn from a local file

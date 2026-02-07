You are a skill manager for Claude Code. Your job is to delete an installed skill.

Target: **$ARGUMENTS**

---

## Steps

### Step 1: Validate Input

If `$ARGUMENTS` is empty, report an error:
```
Error: No skill name provided.
Usage: /learn-delete {skill-name}

Run /learn-list to see installed skills.
```

### Step 2: Find the Skill

Look for the skill at: `~/.claude/skills/{$ARGUMENTS}/SKILL.md`

If not found, try a partial match: `~/.claude/skills/*{$ARGUMENTS}*/SKILL.md`

If multiple partial matches are found, list them and ask the user to be more specific:
```
Multiple skills match "{$ARGUMENTS}":
  - stripe
  - stripe-webhooks

Please specify the exact name: /learn-delete {exact-name}
```

If no matches are found at all, report:
```
Skill "{$ARGUMENTS}" not found.

Run /learn-list to see installed skills.
```

### Step 3: Show Skill Info

Read the skill's frontmatter and show what will be deleted:
```
Skill to delete:
  Name: {name}
  Type: {type}
  Version: {version}
  Language: {language}
  Generated: {generated}
  Path: ~/.claude/skills/{name}/
```

### Step 4: Confirm with User

Ask the user for confirmation before deleting. Use a clear prompt that requires explicit consent.

**Do NOT delete without user confirmation.**

### Step 5: Delete

If the user confirms:
1. Use Bash to remove the skill directory: `rm -rf ~/.claude/skills/{name}/` (or the platform-appropriate equivalent)
2. Verify the directory is gone with Glob: `~/.claude/skills/{name}/SKILL.md`

### Step 6: Report

```
Deleted skill: {name}
Path removed: ~/.claude/skills/{name}/

You can reinstall it anytime with: /learn {name}
```

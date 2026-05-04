---
description: Intelligently commit all staged changes. Analyzes diff to produce a conventional commit message, asks for confirmation, then commits with Co-Authored-By.
allowed-tools: Bash, Read, Grep
---

# Commit Skill — Smart Commit Helper

## Step 1 — What's staged?
```bash
cd /home/uday-varmora/job-radar && git diff --cached --stat
git diff --cached -- "*.py" "*.yml" "*.html" "*.js" "*.css"
```

## Step 2 — Determine commit type
Based on diff content:
- `feat:` — new feature, new scraper, new API endpoint, new UI element
- `fix:` — bug fix in existing code
- `chore:` — config change, dependency version bump, CI change
- `docs:` — README, docstrings, comments
- `test:` — new test file or test update
- `refactor:` — restructuring without behavior change

## Step 3 — Generate commit message
Produce a commit message following conventional commits:
```
<type>: <short description>

- What changed and why (bullet points)
- Any behavior changes

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## Step 4 — Confirm with user
Show the proposed commit message. Ask: "Commit with this message? (yes/edit/cancel)"

## Step 5 — On yes
```bash
git commit -m "..."
git log -1 --oneline  # confirm
```

## Step 6 — On edit
Allow user to edit, then commit.
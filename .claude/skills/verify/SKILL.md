---
description: Run the complete verification pipeline — test + review + security-scan. A mandatory gate before any commit or PR. Stops on first failure.
allowed-tools: Bash, Read, Grep, Glob, Agent
---

# Verify Skill — Complete Pre-Commit Gate

## Philosophy
- If it isn't verified, it isn't done
- Stop at the first failure — do not pass go, do not collect a commit

## Flow

### Step 1 — /test
Run the `/test` skill first. If it fails, STOP. Report failures.

### Step 2 — /security-scan
Run the `/security-scan` skill. If it fails, STOP. Report findings.

### Step 3 — Changes summary
```bash
cd /home/uday-varmora/job-radar && git diff --stat main
```

### Step 4 — Ask to commit
If all pass, ask user:
"All gates passed. Ready to commit? (yes / skip and just review)"

If yes → run `/commit`
If skip → run `/review`
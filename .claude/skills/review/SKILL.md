---
description: Comprehensive code review — correctness, security, performance, and adherence to CLAUDE.md conventions. Run on every changed module before committing. Combines code-reviewer agent findings with manual deep-dive.
allowed-tools: Read, Bash, Grep, Glob, Agent
---

# Review Skill — Pre-Commit Mandatory Gate

## Philosophy
- Code review is a conversation, not a checklist
- Anything non-obvious must be explained with a comment
- Simplicity over cleverness — the next person reading this is your future self

## Step 1 — What Changed
```bash
cd /home/uday-varmora/job-radar && git diff --stat main
```

## Step 2 — Invoke code-reviewer subagent
Spawn `code-reviewer` agent on `git diff main`. Wait for report.

## Step 3 — Security Audit
Spawn `security-auditor` agent. Wait for report.

## Step 4 — Performance Audit
Spawn `performance-reviewer` agent. Wait for report.

## Step 5 — Architecture Review (if new scraper or refactor)
Spawn `architect` agent. Wait for report.

## Step 6 — Diff Review
Read each changed file line by line. For each change, ask:
1. Is there a test for this? (if not, flag it)
2. Is the error handling correct?
3. Are types correct end-to-end?
4. Is logging appropriate?
5. Any hardcoded values that should be in config?

## Step 7 — Summarize
Return a consolidated report with:
- Files reviewed
- Issues found (file:line)
- Severity (critical/high/medium/low/nit)
- Fix for each issue

If any CRITICAL or HIGH issues: CHANGES REQUESTED.
Otherwise: APPROVED WITH NITS (or APPROVED).
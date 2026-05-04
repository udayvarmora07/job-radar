---
description: Quick security scan on modified or new files. Checks for hardcoded secrets, SQL injection, unsafe imports, and GitHub Actions secret leaks. Run before any commit involving network calls, DB access, or secrets.
disable-model-invocation: false
allowed-tools: Read, Bash, Grep
---

# Security Scan Skill — Fast Gate

## Philosophy
- Security is not optional. A leaked secret in main = production incident.
- Assume adversarial eyes on every input field.

## Scope
Files changed in current diff.

## Checks

### SS1 — Secrets Scan
```bash
cd /home/uday-varmora/job-radar && git diff main -- "*.py" "*.yml" | grep -iE "(api[_-]?key|secret|token|password|credential|ghp_|github_pat_|gho_|gla_)" | grep -v "os\.environ\|os\.getenv\|\.env\|# \|comment\|example\|placeholder\|dummy" && echo "FOUND SECRETS" || echo "NO SECRETS FOUND"
```

### SS2 — SQL Parameterization
```bash
cd /home/uday-varmora/job-radar && git diff main -- "*.py" | grep -nE "execute\(|executemany\(" | while read line; do
  # Check if the line uses ? placeholders
  echo "$line"
done
```
Any `execute` without `?` = HIGH severity.

### SS3 — Dangerous Imports
```bash
cd /home/uday-varmora/job-radar && git diff main -- "*.py" | grep -E "import (playwright|selenium|pyppeteer|chromium|phantomjs)" && echo "DANGEROUS IMPORT" || echo "CLEAN"
```

### SS4 — Input Validation
```bash
cd /home/uday-varmora/job-radar && git diff main -- "*.py" | grep -nE "requests\.get.*url|requests\.post.*url" | head -10
```
Any URL built from user input without validation = HIGH.

### SS5 — Secrets in GitHub Actions
```bash
cd /home/uday-varmora/job-radar && git diff main -- ".github/workflows/*.yml" | grep -v "secrets\." | grep -E "password|token|key|secret" && echo "HARDCODED SECRET IN WORKFLOW" || echo "WORKFLOWS CLEAN"
```

## Report
```
SECURITY SCAN
SS1 — Secrets: CLEAN / FOUND ✗
SS2 — SQL Injection: CLEAN / RISK
SS3 — Dangerous Imports: CLEAN / FOUND
SS4 — URL Validation: CLEAN / RISK
SS5 — Workflow Secrets: CLEAN / RISK

RESULT: PASS ✓ or FAIL ✗
```

If FAIL: do not commit. Fix first.
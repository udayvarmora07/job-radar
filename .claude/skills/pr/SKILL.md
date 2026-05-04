---
description: Open a GitHub Pull Request for the current branch. Detects base branch, builds PR body from commits, checks CI status, and reports the PR URL.
allowed-tools: Bash, Read, mcp__github__create_pull_request, mcp__github__get_pull_request_status
---

# PR Skill — One Command to PR

## Step 1 — Current branch
```bash
cd /home/uday-varmora/job-radar && git branch --show-current
git log main..HEAD --oneline
```

## Step 2 — Detect base branch
Usually `main`. Confirm with user if unsure.

## Step 3 — Build PR body
```
## Summary
- <bullet of what this PR does>
- <bullet of why this matters>

## Test Plan
- [ ] Ran `/test` — all layers pass
- [ ] `/review` — approved
- [ ] Manual smoke test on dashboard (if UI changed)

## Files Changed
<git diff --stat main>
```

## Step 4 — Create PR
```bash
gh pr create --title "<title>" --body "<body>" --base main --fill 2>/dev/null || echo "Need GitHub token"
```

Or use MCP:
```
mcp__github__create_pull_request(
  owner="udayvarmora07",
  repo="job-radar",
  head="<branch>",
  base="main",
  title="<title>",
  body="<body>"
)
```

## Step 5 — Report
Return the PR URL and direct link to checks.
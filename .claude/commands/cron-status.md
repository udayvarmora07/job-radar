---
description: Check the health of the scheduled GitHub Actions runs and the last 5 cron executions.
---

Use the github MCP server to:
1. List the last 5 runs of `.github/workflows/scrape.yml`
2. For each: report timestamp, conclusion (success/failure), duration
3. If any failed, fetch the failure log and summarize the root cause
4. Check when the next cron is scheduled to fire (parse the cron expression)
5. If 3+ recent runs failed, recommend invoking `pipeline-debugger` subagent
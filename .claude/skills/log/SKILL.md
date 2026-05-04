---
description: Parse a pipeline log file (from /tmp/radar-dryrun.log or GitHub Actions) and produce a structured summary — scraper counts, filter drop rates, errors, and top-scored jobs.
disable-model-invocation: true
allowed-tools: Read, Bash
---

# Log Parse Skill

## Step 1 — Locate log
```bash
ls -lt /tmp/radar*.log 2>/dev/null | head -3
```
Or ask user to paste the log path.

## Step 2 — Parse
```bash
python3 << 'EOF'
import re, sys
log = sys.stdin.read()

# Extract scraper results
scrapers = re.findall(r'(Naukri|JobSpy|LinkedIn|Indeed|Greenhouse|Lever|Ashby).*?(\d+)\s*jobs?', log, re.I)
# Extract filter stages
filter_stages = re.findall(r'(title filter|exclusion|dedupe|experience).*?(\d+)\s*jobs?', log, re.I)
# Extract errors
errors = re.findall(r'(ERROR|WARNING|Exception|Traceback).+', log)
# Extract top jobs
top_jobs = re.findall(r'score=(\d+).*?title="([^"]+)"', log)

print(f"=== PIPELINE LOG SUMMARY ===")
print(f"Scrapers: {scrapers}")
print(f"Filter stages: {filter_stages}")
print(f"Errors ({len(errors)}): {errors[:5]}")
print(f"Top jobs: {top_jobs[:5]}")
EOF
```

## Step 3 — Report
Structured summary with:
- Jobs scraped per source
- Drop-off at each filter stage
- Any errors (first 5)
- Top 5 jobs by score
- Overall health assessment
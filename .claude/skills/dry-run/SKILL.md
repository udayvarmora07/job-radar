---
name: dry-run
description: Execute the full job radar pipeline in dry-run mode (scrape + filter + score, but skip email send and DB write). Use to debug filtering or scoring logic.
allowed-tools: Bash Read
---

# Dry Run Skill

## Step 1 — Run
```bash
python -m radar.main --dry-run --verbose 2>&1 | tee /tmp/radar-dryrun.log
```

## Step 2 — Summarize log
Parse `/tmp/radar-dryrun.log` and report:
- Total jobs scraped (per source)
- Jobs after title filter
- Jobs after exclusion keywords
- Jobs after dedupe
- Top 10 by score (title, company, score)
- Any errors or warnings

## Step 3 — Suggest tweaks
If <5 jobs match: suggest loosening filters in `config/search.yaml`.
If >100 jobs match: suggest tightening exclusion keywords.
If a scraper errors: suggest running that scraper in isolation.
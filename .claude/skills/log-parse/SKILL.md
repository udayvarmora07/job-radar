---
description: Parse and summarize pipeline log output — scraper counts, filter drop rates, errors, top-scored jobs. Use when the user pastes a log or points to a log file.
disable-model-invocation: true
allowed-tools: Read, Bash
---

# Log Parse Skill

## Usage
`/log <log-text or file-path>`

Paste the raw log text or provide the path.

## Step 1 — Parse
```bash
python3 << 'EOF'
import re, sys

def parse_log(log_text):
    # Scraper counts
    naukri = re.findall(r'Naukri.*?(\d+)\s*jobs?', log_text, re.I)
    jobspy = re.findall(r'JobSpy.*?(\d+)\s*jobs?', log_text, re.I)
    linkedin = re.findall(r'LinkedIn.*?(\d+)\s*jobs?', log_text, re.I)
    indeed = re.findall(r'Indeed.*?(\d+)\s*jobs?', log_text, re.I)
    
    # Filter stages
    title_filter = re.findall(r'after title filter.*?(\d+)', log_text, re.I)
    exclusion = re.findall(r'after (?:exclusion|keywords?).*?(\d+)', log_text, re.I)
    experience = re.findall(r'after experience.*?(\d+)', log_text, re.I)
    dedupe = re.findall(r'dedupe.*?(\d+)\s*new', log_text, re.I)
    
    # Errors
    errors = re.findall(r'(ERROR|Exception|Traceback|FAILED).+', log_text)
    
    # Scores
    scores = re.findall(r'(?:score|=)(\d+).*?(?:title|@)\s*["\']?([^"\'\n]+)["\']?', log_text, re.I)
    
    return {
        'scrapers': {'naukri': naukri, 'jobspy': jobspy, 'linkedin': linkedin, 'indeed': indeed},
        'filters': {'title': title_filter, 'exclusion': exclusion, 'experience': experience, 'dedupe': dedupe},
        'errors': errors[:10],
        'top_scores': scores[:10]
    }

log = sys.stdin.read()
result = parse_log(log)
print("=== PIPELINE LOG SUMMARY ===")
print(f"Scrapers: Naukri={result['scrapers']['naukri']}, JobSpy={result['scrapers']['jobspy']}, LinkedIn={result['scrapers']['linkedin']}, Indeed={result['scrapers']['indeed']}")
print(f"Filter stages: {result['filters']}")
print(f"Errors ({len(result['errors'])}): {result['errors'][:3]}")
print(f"Top scores: {result['top_scores'][:5]}")
EOF
```

## Step 2 — Report
Give a concise summary:
- Total jobs scraped per source
- Drop-off at each filter stage
- Error count and first few errors
- Top 5 jobs by score
- Health verdict: HEALTHY / DEGRADED / BROKEN
---
description: Run the complete E2E test suite for the job-radar project. Use after every code change and before committing. This is a MANDATORY gate — no commit allowed with failing tests.
allowed-tools: Bash, Read, Glob
---

# Test Skill — Mandatory Gate Before Every Commit

## Philosophy
- Tests are not optional. A broken test suite means broken production.
- Integration tests > mocked unit tests
- If you can't test it, the code is poorly structured

## Execution

### Step 1 — Syntax Check
```bash
cd /home/uday-varmora/job-radar && .venv/bin/python -m py_compile radar/**/*.py 2>&1 && echo "SYNTAX OK"
```

### Step 2 — Unit Tests
```bash
cd /home/uday-varmora/job-radar && .venv/bin/pytest tests/ -v --tb=short 2>&1
```

### Step 3 — Scraper Integrity
```bash
cd /home/uday-varmora/job-radar && .venv/bin/python -c "
from radar.scrapers.naukri_v2 import scrape
jobs = list(scrape('DevOps Engineer', pages=1))
print(f'Naukri v2: {len(jobs)} jobs')
assert len(jobs) > 0, 'Naukri returned 0 jobs'

from radar.scrapers import jobspy_runner
config = jobspy_runner.JobSpyConfig(site_names=['linkedin'], search_term='SRE Engineer', location='India', is_remote=True, results_wanted=5, country_indeed='india')
jobs2 = list(jobspy_runner.scrape(config))
print(f'JobSpy: {len(jobs2)} jobs')
" 2>&1
```

### Step 4 — Filter Logic
```bash
cd /home/uday-varmora/job-radar && .venv/bin/python -c "
from radar.filters import is_excluded_experience, should_exclude_title
from radar.models import JobPost

# Test experience filter
assert not is_excluded_experience(JobPost(source='x', company='x', title='y', url='z', location='Bangalore', external_id='1', min_exp=2, max_exp=5))
assert is_excluded_experience(JobPost(source='x', company='x', title='y', url='z', location='Bangalore', external_id='1', min_exp=6, max_exp=10))
assert not is_excluded_experience(JobPost(source='x', company='x', title='y', url='z', location='Bangalore', external_id='1', min_exp=None, max_exp=None))

# Test title filter
assert should_exclude_title('Senior DevOps Engineer', [])
assert should_exclude_title('Lead SRE', [])
assert not should_exclude_title('DevOps Engineer', [])

print('Filter logic: OK')
" 2>&1
```

### Step 5 — DB Schema
```bash
cd /home/uday-varmora/job-radar && .venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('seen_jobs.db')
cur = conn.execute('PRAGMA table_info(seen_jobs)')
cols = [r[1] for r in cur.fetchall()]
required = ['source','external_id','company','title','url','location','posted_at','score','min_exp','max_exp']
missing = set(required) - set(cols)
assert not missing, f'Missing columns: {missing}'
print(f'DB schema: OK ({len(cols)} cols)')
conn.close()
" 2>&1
```

### Step 6 — Dashboard API
```bash
cd /home/uday-varmora/job-radar && .venv/bin/uvicorn radar.dashboard.app:app --port 8099 &
sleep 4
.venv/bin/python -c "
import urllib.request, json

def get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())

# Basic
d = get('http://localhost:8099/api/jobs')
assert 'jobs' in d, 'no jobs key'
print(f'Jobs: {d[\"count\"]}')

# Source filter
d = get('http://localhost:8099/api/jobs?source=naukri_v2')
assert all(j['source']=='naukri_v2' for j in d['jobs']), 'source filter broken'
print('Source filter: OK')

# Tier filter
d = get('http://localhost:8099/api/jobs?tier=strong')
assert all((j.get('score') or 0) >= 20 for j in d['jobs']), 'tier filter broken'
print('Tier filter: OK')

# Debug
d = get('http://localhost:8099/api/debug')
assert 'cached_jobs' in d
print(f'Debug OK: {d[\"cached_jobs\"]} jobs cached')

# Refresh
d = get('http://localhost:8099/api/refresh')
assert d['status'] == 'ok'
print(f'Refresh OK: {d[\"count\"]} jobs')
"
lsof -ti:8099 | xargs kill -9 2>/dev/null
```

## Report

Report pass/fail for each step. If any fail: STOP, do not commit. Fix and re-run.
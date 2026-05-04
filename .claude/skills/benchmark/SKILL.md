---
description: Benchmark a specific operation (scraper speed, DB query time, API latency). Use when adding a new scraper or changing filter logic — measure before and after to confirm improvement.
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Benchmark Skill

## Usage
`/benchmark <target>`

Targets:
- `scraper` — measure Naukri v2 and JobSpy scrape times
- `api` — measure dashboard API response time under load
- `db` — measure seen_jobs.db query time
- `filter` — measure filter_and_score on 100 jobs

## Scraper Benchmark
```bash
cd /home/uday-varmora/job-radar && .venv/bin/python -c "
import time
from radar.scrapers.naukri_v2 import scrape

# Naukri v2
start = time.time()
jobs = list(scrape('DevOps Engineer', pages=1))
naukri_time = time.time() - start
print(f'Naukri v2: {naukri_time:.1f}s for {len(jobs)} jobs ({len(jobs)/naukri_time:.1f} jobs/s)')

# JobSpy
from radar.scrapers import jobspy_runner
config = jobspy_runner.JobSpyConfig(site_names=['linkedin'], search_term='SRE Engineer', location='India', is_remote=True, results_wanted=15, country_indeed='india')
start = time.time()
jobs2 = list(jobspy_runner.scrape(config))
jobspy_time = time.time() - start
print(f'JobSpy: {jobspy_time:.1f}s for {len(jobs2)} jobs ({len(jobs2)/jobspy_time:.1f} jobs/s)')
" 2>&1
```

## API Benchmark
```bash
cd /home/uday-varmora/job-radar && .venv/bin/uvicorn radar.dashboard.app:app --port 8099 &
sleep 4
.venv/bin/python -c "
import urllib.request, time
url = 'http://localhost:8099/api/jobs'

# Cold start
start = time.time()
urllib.request.urlopen(url)
cold = time.time() - start

# 10 warm requests
times = []
for _ in range(10):
    start = time.time()
    urllib.request.urlopen(url)
    times.append(time.time() - start)

print(f'Cold: {cold*1000:.0f}ms')
print(f'Warm avg: {sum(times)/len(times)*1000:.0f}ms')
print(f'Warm p95: {sorted(times)[int(len(times)*0.95)]*1000:.0f}ms')
"
lsof -ti:8099 | xargs kill -9 2>/dev/null
```

## DB Benchmark
```bash
cd /home/uday-varmora/job-radar && .venv/bin/python -c "
import sqlite3, time
conn = sqlite3.connect('seen_jobs.db')
conn.row_factory = sqlite3.Row

# Main dashboard query
start = time.time()
cur = conn.execute('SELECT source, company, title, location, url, external_id, posted_at, score FROM seen_jobs ORDER BY score DESC, posted_at DESC LIMIT 50')
rows = cur.fetchall()
t = time.time() - start
print(f'Main query (50 rows): {t*1000:.1f}ms')

# Full table scan
start = time.time()
cur = conn.execute('SELECT COUNT(*) FROM seen_jobs')
count = cur.fetchone()[0]
t = time.time() - start
print(f'Full scan: {t*1000:.1f}ms for {count} rows')

conn.close()
" 2>&1
```

## Output
Report measured values with PASS/FAIL against thresholds:
- Naukri v2: <5s per page
- JobSpy: <30s for 15 results
- API cold: <3s, warm avg: <100ms, p95: <500ms
- DB query: <50ms
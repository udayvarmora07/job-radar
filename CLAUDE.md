# Job Radar — Cloud.md (Project-Level Agent Memory)

## Version
1.0.0 — Updated 2026-05-05

---

## What This Is

Self-hosted job-monitoring pipeline for DevOps/SRE/Cloud/Platform Engineer roles in India + Remote-India. Runs 2x daily on GitHub Actions cron → scrapes LinkedIn, Indeed, Naukri v2 → filters → dedupes → scores → emails digest.

---

## Owner Profile
- **Name**: Uday Varmora (@udayvarmora07)
- **Role**: DevOps Engineer at eSparkBiz, Ahmedabad, India
- **Experience**: ~1.5 years (intern Jan–May 2025, FT from Jun 2025)
- **Stack**: Kubernetes (EKS), Terraform, Docker, GitHub Actions, AWS CodeBuild, ArgoCD, Prometheus, Grafana, Loki, Python, Bash
- **Target roles**: DevOps Engineer, SRE, Cloud Engineer, Platform Engineer, Kubernetes Engineer
- **Hard filters**: Reject roles requiring 6+ years, "Senior", "Lead", "Principal", "Staff", "Manager"

---

## Architecture

```
GitHub Actions cron (2x daily IST morning + evening)
  -> radar/main.py
     -> scrapers/
        jobspy_runner.py (LinkedIn + Indeed via JobSpy)
        naukri_v2.py (Naukri v2 API, bypasses captcha)
     -> filters/ (title regex, experience, location, keyword exclusion)
     -> radar/db/__init__.py (SQLite dedupe via seen_jobs.db)
     -> radar/scoring (skill keyword overlap)
     -> radar/notifier/ (Jinja2 HTML email via Gmail SMTP)
  -> seen_jobs.db committed back to repo

Web dashboard (FastAPI, Render.com free tier)
  -> radar/dashboard/app.py
     -> reads seen_jobs.db or live-scrapes
     -> 15-min TTL in-memory cache
     -> background thread (~90s) refresh on startup
  -> radar/dashboard/static/app.js (search, filter, tier badges)
```

---

## File Map

```
job-radar/
  CLAUDE.md                          <- This file (cloud.md)
  radar/
    __init__.py
    main.py                          <- Pipeline orchestrator
    models.py                        <- JobPost pydantic model
    db/__init__.py                   <- SQLite dedupe layer
    filters/__init__.py              <- filter_and_score(), all filter funcs
    notifier/
      __init__.py
      email.py                       <- Gmail SMTP digest sender
    scrapers/
      __init__.py
      jobspy_runner.py                <- JobSpy multi-site runner
      naukri_v2.py                   <- Naukri v2 API scraper
    dashboard/
      app.py                         <- FastAPI app, /api/jobs, /api/refresh
      static/
        app.js                       <- Frontend: load, filter, render jobs
        style.css                    <- Dashboard CSS
      templates/
        index.html                   <- Dashboard HTML shell
  config/
    search.yaml                      <- Search terms and city lists
    companies.yaml                   <- (future) ATS company list
  tests/                             <- (empty — needs scaffolding)
  .github/workflows/
    scrape.yml                       <- Cron job, 2x daily
    deploy.yml                       <- (future) Render auto-deploy
  requirements.txt
  seen_jobs.db                       <- Committed from CI, loaded on startup
  jobs.json                          <- (generated) static job export
```

---

## Tech Rules (Immutable)

1. **Python 3.12** — all code type-hinted, pydantic v2 models
2. **No headless browsers** — no Playwright, Selenium, Pyppeteer
3. **Retry everything** — `@retry(stop_after_attempt(3), wait_exponential(min=1,max=10))`
4. **No hardcoded secrets** — all via `os.environ` / `.env`
5. **No `print()`** — use `logging.getLogger(__name__)`
6. **No new deps** without justification in commit message
7. **No LLM-based scoring** — keyword scoring only
8. **SQLite only** — no Postgres, Redis, or other DB servers
9. **Pure stdlib smtplib** — no paid email services

---

## Code Conventions

- **Imports**: stdlib → third-party → local, separated by blank lines
- **Module docstrings**: every file, one sentence minimum
- **Function docstrings**: every public function (single line for simple helpers)
- **Snake_case** modules, **PascalCase** pydantic classes
- **Scrapers**: keep under 150 lines; use `seen_ids` set for dedup across pages
- **Tests**: `tests/test_<module>.py`, pytest, mocked HTTP fixtures in `tests/conftest.py`
- **Commits**: conventional (`feat:`, `fix:`, `chore:`, `docs:`, `test:`), squash-merge
- **Branches**: `main` protected, feature branches, squash-merge

---

## Available Skills (Slash Commands)

| Skill | Purpose | Auto-use |
|-------|---------|---------|
| `/test` | Full E2E test suite — all 6 layers | Before every commit |
| `/verify` | Run `/test` → `/security-scan` → ask to commit | Same |
| `/review` | Full code review — security + performance + architecture | Before PR |
| `/security-scan` | Fast scan for secrets, SQL injection, dangerous imports | After any DB/network change |
| `/benchmark` | Measure scraper speed, API latency, DB query time | After adding scrapers |
| `/commit` | Smart commit — analyze diff, propose conventional msg | On demand |
| `/pr` | Create GitHub PR with test plan body | On demand |
| `/dry-run` | Run full pipeline without email/DB write | On demand |
| `/test-email` | Send one test digest email | After email template change |
| `/new-scraper <ats>` | Scaffold a new ATS scraper | On demand |
| `/bootstrap-companies` | Populate companies.yaml with 30+ targets | On demand |
| `/think-hard <topic>` | Structured deep reasoning for complex decisions | On demand |
| `/plan` | Enter plan mode for next feature | On demand |
| `/ship` | Full cycle: test → review → commit → push → PR | On demand |

---

## Available Agents (Subagents)

| Agent | Purpose | When to Spawn |
|-------|---------|--------------|
| `tester` | Full E2E validation (all 8 layers) | After any code change |
| `security-auditor` | Deep security scan (10-point checklist) | On new scrapers, DB changes |
| `performance-reviewer` | Latency, memory, DB, concurrency analysis | On new scrapers, API changes |
| `architect` | Module boundaries, cyclic deps, data flow | On refactors, new scrapers |
| `code-reviewer` | Python conventions, type hints, error handling | After writing any radar/ module |
| `pipeline-debugger` | Diagnose failed GitHub Actions cron runs | When cron fails |
| `ats-researcher` | Identify ATS platform + validate JSON endpoint | When adding new companies |

---

## Workflow Loop

```
1. User describes feature/bug
2. /plan → step-by-step implementation plan (no code yet)
3. User approves
4. Write code
5. /test → all 6 layers, stop on failure
6. /review → code-reviewer + security-auditor + performance-reviewer
7. Fix all findings
8. /commit → conventional commit message
9. /pr → open GitHub PR with test plan
10. (future: /ship for full automated cycle)
```

---

## Failure Memory (What Breaks What)

1. **Naukri v3 API** → returns 406 recaptcha. Fix: use `/jobapi/v2/search` endpoint (naukri_v2.py)
2. **Indeed without `country_indeed='india'`** → returns global results. Fix: pass `country_indeed='india'`
3. **Naukri duplicate jobs** → same `jobId` on multiple pages. Fix: `seen_ids` set per scraper run
4. **Missing `min_exp`/`max_exp` columns** → Naukri experience filter fails silently. Fix: add via `ALTER TABLE`
5. **Background thread in uvicorn** → dies silently on startup. Fix: use blocking `/api/refresh` for verification
6. **seen_jobs.db not in repo** → dashboard loads empty on Render. Fix: committed from CI on each run
7. **GitHub Actions DB sync on startup** → fails if GHA token expired. Fix: git push from CI step

---

## Current State (as of 2026-05-05)

- **Branch**: `feat/dashboard` — Naukri v2 scraper + source filter UI + experience filtering
- **Last commit**: `da5a742` — feat: add Naukri v2 scraper, source filter UI, and experience filtering
- **Dashboard**: live at Render.com (url unknown — check GitHub Actions env)
- **DB**: 46 jobs from LinkedIn+Indeed (cached), 29 from Naukri v2 (from last `/api/refresh`)
- **Tests**: 0 test files exist — needs scaffolding
- **Secrets**: `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `NOTIFY_EMAIL` via GitHub Actions secrets
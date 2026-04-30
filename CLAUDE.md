# Job Radar — Project Memory

## What this is
Self-hosted job-monitoring pipeline for DevOps / SRE / Cloud / Platform Engineer roles, scoped to India + remote. Runs on GitHub Actions cron, scrapes ATS endpoints + JobSpy, dedupes via SQLite, emails an HTML digest via Gmail SMTP.

## Owner profile (drives matching logic)
- Uday Lunawat, DevOps Engineer at eSparkBiz, Ahmedabad, India
- ~1.5 years experience (intern Jan-May 2025, FT from Jun 2025)
- Core stack: Kubernetes (EKS), Terraform, Docker, GitHub Actions, AWS CodeBuild, ArgoCD, Prometheus, Grafana, Loki, Python, Bash
- Target roles: DevOps Engineer, SRE, Cloud Engineer, Platform Engineer, Kubernetes Engineer
- Filter OUT: roles requiring 4+ years, "Senior", "Lead", "Principal", "Staff", "Manager"

## Architecture
GitHub Actions cron (2x daily, IST morning + evening)
-> radar/main.py orchestrator
-> scrapers (JobSpy + Greenhouse + Lever + Ashby + Workday)
-> filters (title regex, experience, location, exclusion keywords)
-> dedupe (SQLite seen_jobs.db, committed back to repo)
-> scorer (skill keyword overlap)
-> notifier (Jinja2 HTML email via Gmail SMTP)

## Tech rules
- Python 3.12, type-hinted, pydantic models for all job records
- No headless browsers (no Playwright, no Selenium) — direct ATS APIs only
- Every external HTTP call uses `tenacity` retry (3 attempts, exponential backoff)
- All secrets via env vars; never hardcoded; never logged
- Pure stdlib `smtplib` for email; do NOT add a paid email service
- SQLite is the only persistence; the DB file is committed back via the workflow

## Code conventions
- Module docstrings on every file; one-line function docstrings on public functions
- snake_case modules, PascalCase pydantic classes
- Keep each scraper file under 150 lines
- Tests under `tests/`, pytest, name `test_<module>.py`
- Run `python -m radar.main --dry-run` for local testing (no email send)

## Git rules
- Branch `main` is protected — work on feature branches
- Commit messages: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- Never commit `.env`, `*.db` (except `seen_jobs.db` from CI), API keys
- Squash-merge feature branches

## Don'ts (hard rules)
- Don't add new dependencies without justifying in commit message
- Don't add LLM-based scoring in v1; keyword scoring only
- Don't auto-apply to jobs; this tool is alert-only
- Don't introduce a database server (no Postgres, no Redis); SQLite only
- Don't use `print()` for logs; use the `logging` module

## Useful commands
- Run pipeline locally: `python -m radar.main --dry-run`
- Run tests: `pytest -v`
- Bootstrap target companies: `/bootstrap-companies`
- Add a new ATS scraper: `/new-scraper <ats_name>`
- Smoke-test email: `/test-email`
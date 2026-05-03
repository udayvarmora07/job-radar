# Job Radar

Self-hosted job-monitoring pipeline for DevOps / SRE / Cloud / Platform Engineer roles in India and Remote-India. Runs on GitHub Actions cron (2x daily, IST morning + evening), scrapes ATS endpoints + LinkedIn JobSpy, deduplicates via SQLite, and emails an HTML digest via Gmail SMTP.

---

## How it works

```
GitHub Actions cron (IST 8am + 5pm)
  → radar/main.py orchestrator
    → Scrapers: Greenhouse API + Lever API + LinkedIn JobSpy
    → Filters: title regex, seniority/experience, India/Remote location
    → Dedupe: SQLite (seen_jobs.db, committed back to repo)
    → Scorer: skill keyword overlap
    → Notifier: Jinja2 HTML email digest via Gmail SMTP
```

---

## Features

- **Multi-source scraping**: Greenhouse API, Lever API, LinkedIn (JobSpy)
- **Strict India + Remote-India filtering** — no US/UK/Europe jobs
- **Target roles only**: DevOps Engineer, SRE, Site Reliability Engineer, Cloud Engineer, Platform Engineer, Kubernetes Engineer, GitOps, Infrastructure Engineer
- **Excludes**: Senior, Lead, Principal, Staff, Manager, 4+ years experience
- **Skill-based scoring** (0–100): Kubernetes, Terraform, AWS, ArgoCD, Prometheus, etc.
- **SQLite dedupe**: tracks seen jobs across runs, commits back to repo
- **HTML digest email**: tiered (Strong/Moderate/Weak) job cards via Gmail SMTP
- **Runs 2x daily** via GitHub Actions cron (IST 8am + 5pm)

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/udayvarmora07/job-radar.git
cd job-radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Gmail credentials
```

To generate a Gmail App Password:
1. Google Account → **Security** → **2-Step Verification** (enable first)
2. Search **App Passwords** → create one named `job-radar`
3. Copy the 16-char password into `.env`

### 3. Configure companies

Edit `config/companies.yaml` to add/remove ATS company boards:

```yaml
greenhouse:
  - anthropic
  - stripe
  - airbnb
  - smartbear
  - valtech

lever:
  - cred
  - sophos
  - valorx
```

### 4. Test locally

```bash
# Dry run — no email sent, no DB written
python -m radar.main --dry-run

# Full run — sends email, writes seen_jobs.db
python -m radar.main
```

### 5. Push to GitHub and add secrets

```bash
git push origin main
```

On GitHub, add these **Repository Secrets** (Settings → Secrets and Variables → Actions):

| Secret | Value |
|---|---|
| `GMAIL_USER` | your@gmail.com |
| `GMAIL_APP_PASSWORD` | xxxx-xxxx-xxxx-xxxx (Gmail App Password) |
| `NOTIFY_EMAIL` | your@gmail.com |

### 6. Trigger first run

```bash
gh workflow run scrape.yml
```

The workflow runs automatically at **IST 8:30am and 11:30am** daily.

---

## Project structure

```
job-radar/
├── .claude/
│   ├── agents/          # Subagents: ats-researcher, code-reviewer, pipeline-debugger
│   ├── commands/        # Slash commands: /plan, /ship, /cron-status
│   └── skills/          # Skills: new-scraper, bootstrap-companies, test-email, dry-run, think-hard, conventions
├── .github/workflows/
│   └── scrape.yml       # GitHub Actions workflow (cron + workflow_dispatch)
├── config/
│   ├── companies.yaml   # ATS board list (greenhouse/lever/ashby slugs)
│   └── search.yaml      # Filter rules and skill keyword weights
├── radar/
│   ├── db.py            # SQLite dedupe layer
│   ├── filters.py      # Title/seniority/location/skill filters + scoring
│   ├── main.py          # Pipeline orchestrator
│   ├── models.py        # Pydantic JobPost model
│   ├── notifier/
│   │   ├── email.py     # Gmail SMTP notifier
│   │   └── templates/
│   │       └── digest.html  # Jinja2 HTML email template
│   └── scrapers/
│       ├── greenhouse.py # Greenhouse public boards API
│       ├── lever.py      # Lever API
│       ├── ashby.py      # Ashby API
│       └── jobspy_runner.py  # JobSpy (LinkedIn + naukri + indeed)
├── requirements.txt
├── CLAUDE.md             # Project memory (auto-read by Claude)
└── README.md
```

---

## Available slash commands

| Command | Purpose |
|---|---|
| `/new-scraper <ats>` | Scaffold a new ATS scraper |
| `/bootstrap-companies` | Seed companies.yaml with target companies |
| `/test-email` | Send a test digest to verify Gmail SMTP |
| `/dry-run` | Run pipeline without email or DB write |
| `/think-hard <topic>` | Structured step-by-step reasoning for architecture decisions |
| `/plan <feature>` | Enter plan mode for a feature |
| `/ship` | Full ship cycle: test → review → commit → PR |
| `/cron-status` | Check GitHub Actions cron health |

---

## Tech rules

- Python 3.12, type-hinted, pydantic v2 models
- No headless browsers (no Playwright, Selenium) — direct ATS APIs only
- Every external HTTP call uses `tenacity` retry (3 attempts, exponential backoff)
- All secrets via env vars, never hardcoded, never logged
- Pure stdlib `smtplib` for email — no paid email service
- SQLite is the only persistence; the DB file is committed back via the workflow
- `logging` module only — no `print()` statements
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`

---

## Owner

Uday Lunawat — DevOps Engineer at eSparkBiz, Ahmedabad, India

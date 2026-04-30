---
name: test-email
description: Send a single test job-digest email to verify Gmail SMTP credentials and the HTML template render correctly. Use after first setup or after changing the email template.
disable-model-invocation: true
allowed-tools: Read Bash Edit
---

# Test Email Skill

This skill is **manual-only** because it has the side effect of sending real email.

## Step 1 — Check env
Verify `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `NOTIFY_EMAIL` are set:
```bash
test -f .env && grep -E '^(GMAIL_USER|GMAIL_APP_PASSWORD|NOTIFY_EMAIL)=' .env || echo "MISSING .env"
```
If missing, stop and tell user to copy `.env.example` to `.env` and fill it in.

## Step 2 — Build a fake digest
Use 3 hardcoded JobPost samples covering each match tier (strong / moderate / weak).

## Step 3 — Send via radar.notifier
```bash
python -c "
from radar.notifier.email import send_digest
from radar.models import JobPost
sample = [JobPost(source='test', company='Acme', title='SRE Engineer', location='Remote India', url='https://example.com', external_id='1', score=85)]
send_digest(sample, dry_run=False)
"
```

## Step 4 — Confirm
Ask user to check inbox and report success/failure. If failure, suggest checking Gmail App Password (not regular password).
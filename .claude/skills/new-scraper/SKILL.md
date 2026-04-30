---
name: new-scraper
description: Scaffold a new ATS scraper module under radar/scrapers/. Use when the user wants to add support for a new ATS platform (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Recruitee, etc.) or a custom company career page.
allowed-tools: Read Edit Write Bash Grep
---

# New Scraper Skill

When the user types `/new-scraper <ats_name>`, follow these steps:

## Step 1 — Confirm requirements
Verify the ATS exposes a public JSON endpoint. If unsure, ask the user for one example URL.

## Step 2 — Create the scraper file
Path: `radar/scrapers/<ats_name>.py`

Template:
```python
"""<ATS_NAME> scraper. Hits the public board JSON endpoint, returns normalized JobPost objects."""
from __future__ import annotations
import logging
from typing import Iterable
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from radar.models import JobPost

log = logging.getLogger(__name__)
ENDPOINT = "<paste-endpoint-template>"  # e.g. https://boards-api.greenhouse.io/v1/boards/{slug}/jobs

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _fetch(slug: str) -> dict:
    r = requests.get(ENDPOINT.format(slug=slug), timeout=30)
    r.raise_for_status()
    return r.json()

def scrape(slug: str) -> Iterable[JobPost]:
    """Yield JobPost records for one company on this ATS."""
    data = _fetch(slug)
    for raw in data.get("jobs", []):
        yield JobPost(
            source="<ats_name>",
            company=slug,
            title=raw["title"],
            location=raw.get("location", {}).get("name", "Unknown"),
            url=raw["absolute_url"],
            external_id=str(raw["id"]),
            posted_at=raw.get("updated_at"),
            description=raw.get("content", "")[:5000],
        )
```

## Step 3 — Register in orchestrator
Open `radar/main.py` and add the new scraper to `SCRAPER_REGISTRY`.

## Step 4 — Add a test
Path: `tests/test_<ats_name>.py`. Mock `requests.get`, assert one JobPost is yielded with correct fields.

## Step 5 — Update companies.yaml
Add a sample company under the new ATS section.

## Step 6 — Run
`pytest tests/test_<ats_name>.py -v` and report results to user.
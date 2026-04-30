"""JobSpy runner — wraps python-jobspy for naukri, linkedin, indeed, glassdoor."""
from __future__ import annotations

import logging
from typing import Iterable

from jobspy import scrape_jobs
from pydantic import BaseModel

from radar.models import JobPost

log = logging.getLogger(__name__)


class JobSpyConfig(BaseModel):
    """Config for one jobspy source."""

    site_names: list[str]
    search_term: str
    location: str = "India"
    is_remote: bool = True
    results_wanted: int = 20


def scrape(config: JobSpyConfig) -> Iterable[JobPost]:
    """Scrape jobs from jobpsy-supported sites, yield normalized JobPost."""
    try:
        results = scrape_jobs(
            site_name=config.site_names,
            search_term=config.search_term,
            location=config.location,
            is_remote=config.is_remote,
            results_wanted=config.results_wanted,
        )
    except Exception:
        log.error("JobSpy scrape failed for %s", config.site_names)
        return

    for _, row in results.iterrows():
        yield JobPost(
            source="jobspy",
            company=str(row.get("company_name", "Unknown")),
            title=str(row.get("title", "Unknown")),
            location=str(row.get("location", "Unknown")),
            url=str(row.get("job_url", "")),
            external_id=str(row.get("uniq_id", row.get("title", ""))),
            posted_at=str(row.get("date_posted", ""))[:10] if row.get("date_posted") else None,
            description=str(row.get("description", ""))[:5000],
        )
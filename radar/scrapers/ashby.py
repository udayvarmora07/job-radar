"""Ashby scraper. Hits the Ashby posting API, returns normalized JobPost objects."""
from __future__ import annotations

import logging
from typing import Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from radar.models import JobPost

log = logging.getLogger(__name__)

ENDPOINT = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _fetch(slug: str) -> dict:
    r = requests.get(ENDPOINT.format(slug=slug), timeout=30)
    r.raise_for_status()
    return r.json()


def scrape(slug: str) -> Iterable[JobPost]:
    """Yield JobPost records for one company on Ashby."""
    try:
        data = _fetch(slug)
    except Exception:
        log.error("Ashby fetch failed for slug=%s", slug)
        return

    for raw in data.get("jobs", []):
        yield JobPost(
            source="ashby",
            company=slug,
            title=raw.get("title", "Unknown"),
            location=raw.get("location", {}).get("name", "Unknown")
            if isinstance(raw.get("location"), dict)
            else raw.get("location", "Unknown"),
            url=raw.get("absoluteUrl", ""),
            external_id=str(raw["id"]),
            posted_at=raw.get("postedAt"),
            description=raw.get("description", "")[:5000],
        )
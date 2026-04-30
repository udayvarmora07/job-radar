"""Greenhouse scraper. Hits the public boards API, returns normalized JobPost objects."""
from __future__ import annotations

import logging
from typing import Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from radar.models import JobPost

log = logging.getLogger(__name__)

ENDPOINT = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _fetch(slug: str) -> dict:
    r = requests.get(ENDPOINT.format(slug=slug), timeout=30)
    r.raise_for_status()
    return r.json()


def scrape(slug: str) -> Iterable[JobPost]:
    """Yield JobPost records for one company on Greenhouse."""
    try:
        data = _fetch(slug)
    except Exception:
        log.error("Greenhouse fetch failed for slug=%s", slug)
        return

    for raw in data.get("jobs", []):
        yield JobPost(
            source="greenhouse",
            company=slug,
            title=raw["title"],
            location=raw.get("location", {}).get("name", "Unknown"),
            url=raw["absolute_url"],
            external_id=str(raw["id"]),
            posted_at=raw.get("updated_at"),
            description=raw.get("content", "")[:5000],
        )
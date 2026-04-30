"""Lever scraper. Hits the Lever API endpoint, returns normalized JobPost objects."""
from __future__ import annotations

import logging
from typing import Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from radar.models import JobPost

log = logging.getLogger(__name__)

ENDPOINT = "https://api.lever.co/v0/postings/{slug}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _fetch(slug: str) -> dict:
    r = requests.get(ENDPOINT.format(slug=slug), timeout=30)
    r.raise_for_status()
    return r.json()


def scrape(slug: str) -> Iterable[JobPost]:
    """Yield JobPost records for one company on Lever."""
    try:
        data = _fetch(slug)
    except Exception:
        log.error("Lever fetch failed for slug=%s", slug)
        return

    for raw in data:
        yield JobPost(
            source="lever",
            company=slug,
            title=raw.get("text", "Unknown"),
            location=raw.get("location", "Unknown"),
            url=raw.get("absolute_url", ""),
            external_id=str(raw["id"]),
            posted_at=raw.get("postedAt"),
            description=raw.get("description", "")[:5000],
        )
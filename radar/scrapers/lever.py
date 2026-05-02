"""Lever scraper. Hits the Lever API endpoint, returns normalized JobPost objects."""
from __future__ import annotations

import logging
from typing import Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from radar.models import JobPost

log = logging.getLogger(__name__)

ENDPOINT = "https://api.lever.co/v0/postings/{slug}"


def scrape(slug: str) -> Iterable[JobPost]:
    """Yield JobPost records for one company on Lever. Skips 404 (invalid slug)."""
    try:
        r = requests.get(ENDPOINT.format(slug=slug), timeout=15)
        if r.status_code == 404:
            log.warning("Lever slug not found: %s", slug)
            return
        r.raise_for_status()
    except Exception:
        log.error("Lever fetch failed for slug=%s", slug)
        return

    for raw in r.json():
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
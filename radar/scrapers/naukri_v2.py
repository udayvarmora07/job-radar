"""Naukri.com v2 API scraper — bypasses captcha by using the older v2 endpoint.

Research: Naukri's /jobapi/v3 returns 406 recaptcha on every request.
The v2 endpoint (/jobapi/v2/search) returns ~4693 jobs for "devops engineer"
in India with no captcha, no auth required.
"""
from __future__ import annotations

import logging
import re
from typing import Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from radar.models import JobPost

log = logging.getLogger(__name__)

V2_ENDPOINT = "https://www.naukri.com/jobapi/v2/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.naukri.com/",
}


def _parse_exp(exp_str: str | None) -> tuple[int, int] | None:
    """Parse '0-5 Yrs' into (min, max) tuple."""
    if not exp_str:
        return None
    m = re.search(r"(\d+)\s*-\s*(\d+)", exp_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _fetch_page(keyword: str, page: int, location: str = "India") -> list[dict]:
    """Fetch one page of results from Naukri v2 API."""
    params = {
        "keyword": keyword,
        "location": location,
        "page": page,
        "noOfResults": 20,
    }
    r = requests.get(V2_ENDPOINT, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("list", [])


def scrape(keyword: str, location: str = "India", pages: int = 3) -> Iterable[JobPost]:
    """
    Scrape Naukri v2 API for jobs matching keyword + location.

    Yields JobPost objects with all available fields.
    Note: job description is a short snippet only (~1-2 sentences).
    Remote detection is done via keyword matching on title + description.
    """
    for page in range(1, pages + 1):
        try:
            rows = _fetch_page(keyword, page, location)
        except Exception as e:
            log.warning("Naukri v2 page %d failed: %s", page, e)
            continue

        for raw in rows:
            posted_str = raw.get("addDate", "")
            if len(posted_str) >= 10:
                posted_str = posted_str[:10]

            title = raw.get("post", "")
            desc = raw.get("jobDesc", "")
            combined = (title + " " + desc).lower()

            # Detect remote from title/description keywords
            is_remote = bool(re.search(
                r"remote|work\s*from\s*home|wfh|home\s*based",
                combined,
            ))

            exp = _parse_exp(raw.get("experience", ""))
            if exp:
                min_exp, max_exp = exp
            else:
                min_exp = max_exp = 0

            # Build location string
            loc_parts = []
            if raw.get("CONTCITY"):
                loc_parts.append(raw["CONTCITY"].strip())
            if raw.get("cityfield"):
                loc_parts.append(raw["cityfield"].strip())
            loc = ", ".join(loc_parts) if loc_parts else ("Remote" if is_remote else "India")

            yield JobPost(
                source="naukri_v2",
                company=str(raw.get("companyName", "Unknown")),
                title=title,
                location=loc,
                url=str(raw.get("urlStr", "")),
                external_id=str(raw.get("jobId", raw.get("unjobid", title))),
                posted_at=posted_str or None,
                description=desc[:5000],
            )

        if len(rows) < 20:
            break  # last page

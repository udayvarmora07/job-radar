"""Filters and scoring logic. Applies title regex, location, experience, and skill scoring."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Iterable

from radar.models import JobPost

log = logging.getLogger(__name__)

# Target job title patterns — DevOps / SRE / Cloud / Platform Engineering roles
TITLE_ALLOW = re.compile(
    r"(?:^|\s)(devops|sre|site.?reliability|cloud\s*(?:engineer|ops|operations)|"
    r"platform\s*engineer|kubernetes|k8s|gitops|infrastructure\s*engineer|"
    r"release\s*engineer|build\s*engineer|ci/?cd|cd/?ci|cloudops|ops\s*engineer|systems\s*engineer)",
    re.IGNORECASE,
)

# Senior-level exclusion patterns in title
EXCLUDE_SENIOR = re.compile(
    r"\bsenior\b|lead\b|principal|staff\b|manager|director|head\s|\bsr\.?\b",
    re.IGNORECASE,
)

# Experience patterns — match when min experience is 6+ years (reject these)
_EXCLUDE_EXP = re.compile(
    r"\b(?:6|7|8|9|10)\s*\+\s*(?:years?|yrs?)\b",
    re.IGNORECASE,
)

# Experience ranges — reject if lower bound >= 5 (treat 5-7 as too senior)
_EXCLUDE_RANGE = re.compile(
    r"\b(\d)\s*(?:-|–)\s*\d{1,2}\s*(?:years?|yrs?)\b",
    re.IGNORECASE,
)

# "minimum N years", "at least N years" patterns — reject if N >= 6
_EXCLUDE_MIN = re.compile(
    r"\b(?:min(?:imum)?\s*|at\s*least\s*)(\d{1,2})\s*(?:\+\s*)?(?:years?|yrs?)\b",
    re.IGNORECASE,
)

# Location inclusions — Remote/WFH + specific WFO cities
ALLOW_LOCATION = re.compile(
    r"remote|work\s*from\s*home|wfh|"
    r"ahmedabad|gandhinagar|gift\s*city|"
    r"mumbai|pune|gurugram|gurgaon|"
    r"bangalore|bengaluru|hyderabad|vadodara|"
    r"india\b",
    re.IGNORECASE,
)

# Location exclusions — non-India cities
EXCLUDE_LOCATION = re.compile(
    r"united states|usa\b|uk\b|europe\b|canada|australia|japan|china|singapore|"
    r"san francisco|new york\b|seattle|chicago|los angeles|boston|denver|portland|"
    r"london|paris|berlin|dublin|toronto|melbourne|sydney",
    re.IGNORECASE,
)

# Soft-exclusion keywords in title
EXCLUDE_TITLEKW = re.compile(
    r"intern(?:ship)?|fresher|\bfresher\b|contract\s*(?!devops|sre|cloud)",
    re.IGNORECASE,
)

# Skill keywords for scoring
SKILL_KEYWORDS = {
    "devops": 12,
    "sre": 12,
    "site reliability": 12,
    "cloud engineer": 10,
    "cloud ops": 10,
    "platform engineer": 10,
    "infrastructure engineer": 8,
    "systems engineer": 5,
    "kubernetes": 15,
    "k8s": 10,
    "eks": 8,
    "gke": 6,
    "terraform": 12,
    "aws": 10,
    "gcp": 6,
    "azure": 5,
    "docker": 8,
    "container": 5,
    "gitops": 10,
    "argocd": 8,
    "github actions": 7,
    "ci/cd": 8,
    "jenkins": 4,
    "prometheus": 7,
    "grafana": 6,
    "loki": 5,
    "datadog": 6,
    "splunk": 4,
    "elasticsearch": 4,
    "helm": 6,
    "linux": 5,
    "python": 5,
    "bash": 4,
    "ansible": 5,
    "vault": 5,
    "redis": 3,
    "rabbitmq": 3,
    "kafka": 3,
    "argo": 6,
}

# Max age for job postings (days)
MAX_JOB_AGE_DAYS = 30


def _parse_date(posted_at: str | None) -> datetime | None:
    """Parse posted_at string into a datetime object."""
    if not posted_at:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
        try:
            return datetime.strptime(posted_at[:10], fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(posted_at[:10])
    except ValueError:
        return None


def is_old(job: JobPost) -> bool:
    """Return True if job is older than MAX_JOB_AGE_DAYS."""
    if not job.posted_at:
        return False  # No date = allow (assume recent)
    dt = _parse_date(job.posted_at)
    if not dt:
        return False
    age = datetime.now() - dt
    return age.days > MAX_JOB_AGE_DAYS


def is_excluded_experience(job: JobPost) -> bool:
    """
    Return True if job requires 6+ years experience.

    Checks Naukri's min_exp/max_exp fields (numeric), falls back to
    title + description text patterns.

    Numeric check: reject if min_exp >= 6.
    Text patterns checked:
    - Explicit "6+ years", "7+ years" etc.
    - Ranges with lower bound >= 5: "5-7 years", "6-8 years"
    - "minimum N years" with N >= 6
    """
    # Priority: use numeric Naukri fields if available
    if job.min_exp is not None:
        if job.min_exp >= 6:
            return True
        # Also reject if max_exp >= 6 AND min_exp is missing/zero (open-ended)
        if job.max_exp is not None and job.max_exp >= 6 and job.min_exp == 0:
            return True

    combined = (job.title + " " + (job.description or "")).lower()

    if _EXCLUDE_EXP.search(combined):
        return True

    for match in _EXCLUDE_RANGE.finditer(combined):
        lower = int(match.group(1))
        if lower >= 5:
            return True

    for match in _EXCLUDE_MIN.finditer(combined):
        years = int(match.group(1))
        if years >= 6:
            return True

    return False


def filter_title(job: JobPost) -> bool:
    """Return True if title matches target role patterns."""
    return bool(TITLE_ALLOW.search(job.title))


def is_senior_or_excluded(job: JobPost) -> bool:
    """Return True if job has seniority indicators in title."""
    return bool(EXCLUDE_SENIOR.search(job.title))


def is_excluded_location(job: JobPost) -> bool:
    """
    Return True if location is NOT WFH/Remote or one of the allowed WFO cities.

    Allowed locations:
    - Remote / Work From Home / WFH (anywhere)
    - India + specific cities: Ahmedabad, Gandhinagar, GIFT City, Mumbai, Pune,
      Gurugram/Gurgaon, Bangalore/Bengaluru, Hyderabad, Vadodara
    """
    loc = job.location.strip() if job.location else ""

    # Empty location = allow (generic job posting)
    if not loc:
        return False

    # Must be in India AND one of our allowed cities
    if EXCLUDE_LOCATION.search(loc):
        return True

    if ALLOW_LOCATION.search(loc):
        return False

    return True


def is_excluded_titlekw(job: JobPost) -> bool:
    """Return True if title has soft-exclusion keywords."""
    return bool(EXCLUDE_TITLEKW.search(job.title))


def score_job(job: JobPost) -> int:
    """Compute skill keyword overlap score (0-100)."""
    text = (job.title + " " + job.description).lower()
    total = sum(pts for kw, pts in SKILL_KEYWORDS.items() if kw.lower() in text)
    return min(total, 100)


def filter_and_score(jobs: Iterable[JobPost]) -> list[JobPost]:
    """Apply all filters and scoring, return sorted list of passing jobs."""
    passing = []
    for job in jobs:
        if is_old(job):
            log.debug("Filtered (old): %s @ %s posted=%s", job.title, job.company, job.posted_at)
            continue
        if not filter_title(job):
            log.debug("Filtered (title): %s @ %s", job.title, job.company)
            continue
        if is_senior_or_excluded(job):
            log.debug("Filtered (senior): %s @ %s", job.title, job.company)
            continue
        if is_excluded_location(job):
            log.debug("Filtered (location): %s @ %s", job.title, job.company)
            continue
        if is_excluded_experience(job):
            log.debug("Filtered (experience): %s @ %s", job.title, job.company)
            continue
        if is_excluded_titlekw(job):
            log.debug("Filtered (title kw): %s @ %s", job.title, job.company)
            continue
        job.score = score_job(job)
        passing.append(job)

    log.info("Filters: %d/%d jobs passed", len(passing), sum(1 for _ in jobs))
    passing.sort(key=lambda j: j.score, reverse=True)
    return passing

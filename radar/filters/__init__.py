"""Filters and scoring logic. Applies title regex, exclusion keywords, location, and skill scoring."""
from __future__ import annotations

import logging
import re
from typing import Iterable

from radar.models import JobPost

log = logging.getLogger(__name__)

# Target job title patterns — DevOps / SRE / Cloud / Platform Engineering roles
TITLE_ALLOW = re.compile(
    r"(?:^|\s)(devops|sre|site.?reliability|cloud\s*(?:engineer|ops|operations)|platform\s*engineer|kubernetes|k8s|gitops|infrastructure\s*engineer|release\s*engineer|build\s*engineer|ci/?cd|cd/?ci|cloudops|ops\s*engineer|systems\s*engineer)",
    re.IGNORECASE,
)

# Senior-level exclusion patterns
EXCLUDE_SENIOR = re.compile(
    r"\bsenior\b|lead\b|principal|staff\b|manager|director|head\s|\bsr\.?\b|\barchitect\b",
    re.IGNORECASE,
)

# Roles requiring 4+ years experience
EXCLUDE_EXP = re.compile(r"4\s*\+|5\s*\+|6\s*\+|7\s*\+|8\s*\+", re.IGNORECASE)

# Location inclusions — India + Remote India (broad match)
ALLOW_LOCATION = re.compile(
    r"india|bengaluru|bangalore|mumbai|pune|hyderabad|chennai|kolkata|ahmedabad|"
    r"gurgaon|noida|thiruvananthapuram|kochi|coimbore|mysore|indore|jaipur|nagpur|"
    r"remote|work from home|wfh",
    re.IGNORECASE,
)

# Location exclusions — non-India major cities
EXCLUDE_LOCATION = re.compile(
    r"united states|usa\b|uk\b|europe\b|canada|australia|japan|china|singapore|"
    r"san francisco|new york|seattle|chicago|los angeles|boston|denver|portland|"
    r"london|paris|berlin|dublin|toronto|melbourne|sydney",
    re.IGNORECASE,
)

# Soft-exclusion keywords in title
EXCLUDE_TITLEKW = re.compile(
    r"intern(?:ship)?|fresher|junior\s+(?!engineer)|contract\s+(?!devops)",
    re.IGNORECASE,
)

# Skill keywords for scoring (title + description)
SKILL_KEYWORDS = {
    # Cloud/DevOps role types (from title)
    "devops": 12,
    "sre": 12,
    "site reliability": 12,
    "cloud engineer": 10,
    "cloud ops": 10,
    "platform engineer": 10,
    "infrastructure engineer": 8,
    "systems engineer": 5,
    # Tech stack keywords
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
    "helm": 6,
    "argo": 6,
}


def filter_title(job: JobPost) -> bool:
    """Return True if title matches target role patterns."""
    return bool(TITLE_ALLOW.search(job.title))


def is_senior_or_excluded(job: JobPost) -> bool:
    """Return True if job should be excluded due to seniority/experience."""
    return bool(EXCLUDE_SENIOR.search(job.title)) or bool(EXCLUDE_EXP.search(job.title))


def is_excluded_location(job: JobPost) -> bool:
    """Return True if location is NOT India or India-Remote."""
    # Empty/blank location = allow (job listings often omit it)
    if not job.location.strip():
        return False
    # If it matches an exclusion pattern, fail immediately
    if EXCLUDE_LOCATION.search(job.location):
        return True
    # If it matches an allow pattern (India city, Remote, etc.), pass
    if ALLOW_LOCATION.search(job.location):
        return False
    # Unknown locations that are neither excluded nor explicitly allowed -> fail
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
        if not filter_title(job):
            log.debug("Filtered (title): %s @ %s", job.title, job.company)
            continue
        if is_senior_or_excluded(job):
            log.debug("Filtered (senior/exp): %s @ %s", job.title, job.company)
            continue
        if is_excluded_location(job):
            log.debug("Filtered (location): %s @ %s", job.title, job.company)
            continue
        if is_excluded_titlekw(job):
            log.debug("Filtered (title kw): %s @ %s", job.title, job.company)
            continue
        job.score = score_job(job)
        passing.append(job)

    log.info("Filters: %d/%d jobs passed", len(passing), sum(1 for _ in jobs))
    passing.sort(key=lambda j: j.score, reverse=True)
    return passing
"""Pipeline orchestrator. Run with: python -m radar.main --dry-run"""
from __future__ import annotations

import argparse
import logging
import os
import sys

import yaml
from dotenv import load_dotenv

load_dotenv()

from radar.db import dedupe
from radar.filters import filter_and_score
from radar.models import JobPost
from radar.notifier.email import send_digest
from radar.scrapers import greenhouse, lever, ashby, jobspy_runner

log = logging.getLogger(__name__)


_SCRAPER_REGISTRY = {
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
}


def _load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _scrape_all() -> list[JobPost]:
    """Scrape all sources — ATS boards + generic job board searches."""
    companies = _load_yaml("config/companies.yaml")
    jobs = []

    # --- ATS boards (company-specific) ---
    for ats_name, slugs in companies.items():
        scraper = _SCRAPER_REGISTRY.get(ats_name)
        if not scraper:
            log.warning("No scraper for ATS: %s", ats_name)
            continue
        for company in slugs:
            slug = company if isinstance(company, str) else company.get("slug", "")
            try:
                for job in scraper.scrape(slug):
                    jobs.append(job)
            except Exception as e:
                log.error("Scraper error for %s/%s: %s", ats_name, slug, e)
                continue

    # --- Generic job board searches (linkedin only — naukri blocked by captcha) ---
    sites = ["linkedin"]  # naukri blocked by captcha on every request
    searches = [
        # Role-based (remote India)
        ("DevOps Engineer India Remote", True),
        ("SRE Engineer India Remote", True),
        ("Cloud Engineer India Remote", True),
        ("Platform Engineer India Remote", True),
        ("Site Reliability Engineer India Remote", True),
        ("Kubernetes Engineer India Remote", True),
        ("GitOps Engineer India Remote", True),
        ("Infrastructure Engineer India Remote", True),
        # City-based
        ("DevOps Engineer Bangalore", False),
        ("DevOps Engineer Pune", False),
        ("DevOps Engineer Hyderabad", False),
        ("DevOps Engineer Chennai", False),
        ("DevOps Engineer Mumbai", False),
        ("DevOps Engineer Ahmedabad", False),
        ("DevOps Engineer Noida Gurgaon", False),
        ("SRE Engineer Bangalore Pune", False),
        ("Cloud Engineer Mumbai Bangalore", False),
    ]

    for search_term, is_remote in searches:
        for site in sites:
            config = jobspy_runner.JobSpyConfig(
                site_names=[site],
                search_term=search_term,
                location="India",
                is_remote=is_remote,
                results_wanted=15,
            )
            try:
                for job in jobspy_runner.scrape(config):
                    jobs.append(job)
            except Exception as e:
                log.debug("JobSpy (%s, %s) returned nothing: %s", site, search_term, type(e).__name__)

    log.info("Scraped %d total raw jobs", len(jobs))
    return jobs


def run(dry_run: bool = True, verbose: bool = False) -> None:
    """Full pipeline: scrape -> filter -> dedupe -> score -> notify."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    log.info("Starting Job Radar pipeline (dry_run=%s)", dry_run)

    raw_jobs = _scrape_all()
    if not raw_jobs:
        log.warning("No jobs scraped — check ATS endpoints and companies.yaml")
        return

    filtered = filter_and_score(raw_jobs)
    log.info("After filters: %d jobs", len(filtered))

    new_jobs = dedupe(filtered)
    log.info("After dedupe: %d new jobs", len(new_jobs))

    if not new_jobs:
        log.info("No new jobs — skipping email")
        return

    send_digest(new_jobs, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Radar pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending email or writing DB")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    args = parser.parse_args()

    try:
        run(dry_run=args.dry_run, verbose=args.verbose)
    except Exception as e:
        log.error("Pipeline failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
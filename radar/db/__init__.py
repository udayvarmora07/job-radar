"""SQLite dedupe layer. Maintains seen_jobs.db across workflow runs."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Iterable

from radar.models import JobPost

log = logging.getLogger(__name__)

DB_PATH = Path("seen_jobs.db")


def _init_db() -> None:
    """Create the jobs table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_jobs (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            company TEXT,
            title TEXT,
            url TEXT,
            location TEXT,
            posted_at TEXT,
            score INTEGER DEFAULT 0,
            seen_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (source, external_id)
        )
        """
    )
    conn.commit()
    conn.close()


def is_seen(job: JobPost) -> bool:
    """Return True if this (source, external_id) combo is already in the DB."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT 1 FROM seen_jobs WHERE source = ? AND external_id = ?",
        (job.source, job.external_id),
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def insert(job: JobPost) -> None:
    """Upsert a job into the seen_jobs table."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT OR REPLACE INTO seen_jobs
            (source, external_id, company, title, url, location, posted_at, score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job.source,
            job.external_id,
            job.company,
            job.title,
            job.url,
            job.location,
            job.posted_at,
            job.score,
        ),
    )
    conn.commit()
    conn.close()
    log.debug("Inserted job %s/%s", job.source, job.external_id)


def dedupe(jobs: Iterable[JobPost]) -> list[JobPost]:
    """Yield jobs that are NOT in the DB, then insert them."""
    new_jobs = []
    for job in jobs:
        if not is_seen(job):
            new_jobs.append(job)
            insert(job)
    log.info("Dedupe: %d new of %d total", len(new_jobs), sum(1 for _ in jobs))
    return new_jobs


def count() -> int:
    """Return total rows in seen_jobs (for logging)."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT COUNT(*) FROM seen_jobs")
    n = cur.fetchone()[0]
    conn.close()
    return n
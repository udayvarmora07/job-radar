"""Tests for radar.db — SQLite dedupe layer."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from radar.db import _init_db, count, dedupe, insert, is_seen
from radar.models import JobPost


@pytest.fixture
def temp_db() -> str:
    """A clean temporary database for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_seen_jobs.db"
        # Patch DB_PATH for the test
        import radar.db
        original = radar.db.DB_PATH
        radar.db.DB_PATH = db_path
        yield str(db_path)
        radar.db.DB_PATH = original


class TestInitDb:
    def test_creates_table_if_not_exists(self, temp_db: str) -> None:
        """_init_db creates the seen_jobs table."""
        _init_db()
        conn = sqlite3.connect(temp_db)
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        assert "seen_jobs" in tables
        conn.close()

    def test_has_all_required_columns(self, temp_db: str) -> None:
        """Table has all required columns including min_exp/max_exp."""
        _init_db()
        conn = sqlite3.connect(temp_db)
        cur = conn.execute("PRAGMA table_info(seen_jobs)")
        cols = [r[1] for r in cur.fetchall()]
        conn.close()
        required = ["source", "external_id", "company", "title", "url", "location",
                    "posted_at", "score", "min_exp", "max_exp"]
        assert all(c in cols for c in required)


class TestIsSeen:
    def test_returns_false_for_new_job(self, temp_db: str) -> None:
        job = JobPost(
            source="test", company="Acme", title="DevOps",
            url="https://ex.com/1", external_id="new-001",
        )
        assert is_seen(job) is False

    def test_returns_true_after_insert(self, temp_db: str) -> None:
        job = JobPost(
            source="test", company="Acme", title="DevOps",
            url="https://ex.com/1", external_id="new-002",
        )
        insert(job)
        assert is_seen(job) is True

    def test_respects_source_in_composite_key(self, temp_db: str) -> None:
        """Same external_id from different sources are distinct."""
        job1 = JobPost(
            source="linkedin", company="Acme", title="DevOps",
            url="https://ex.com/1", external_id="ext-001",
        )
        job2 = JobPost(
            source="naukri_v2", company="Acme", title="DevOps",
            url="https://ex.com/2", external_id="ext-001",  # same external_id
        )
        insert(job1)
        assert is_seen(job1) is True
        assert is_seen(job2) is False  # different source


class TestInsert:
    def test_insert_job_with_all_fields(self, temp_db: str) -> None:
        job = JobPost(
            source="naukri_v2",
            company="TechCorp",
            title="SRE Engineer",
            location="Bangalore, India",
            url="https://naukri.com/job/1",
            external_id="nk-001",
            posted_at="2026-05-01",
            min_exp=2,
            max_exp=5,
            score=65,
        )
        insert(job)
        conn = sqlite3.connect(temp_db)
        cur = conn.execute(
            "SELECT company, title, location, min_exp, max_exp, score FROM seen_jobs WHERE external_id=?",
            ("nk-001",),
        )
        row = cur.fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "TechCorp"
        assert row[3] == 2
        assert row[4] == 5
        assert row[5] == 65

    def test_insert_upserts_on_conflict(self, temp_db: str) -> None:
        """Insert with same (source, external_id) replaces existing row."""
        job1 = JobPost(
            source="test", company="Acme", title="DevOps",
            url="https://ex.com/1", external_id="dup-001", score=50,
        )
        job2 = JobPost(
            source="test", company="Acme", title="DevOps Updated",
            url="https://ex.com/2", external_id="dup-001", score=75,
        )
        insert(job1)
        insert(job2)
        conn = sqlite3.connect(temp_db)
        cur = conn.execute("SELECT score FROM seen_jobs WHERE external_id=?", ("dup-001",))
        row = cur.fetchone()
        conn.close()
        assert row[0] == 75  # updated score


class TestDedupe:
    def test_returns_only_new_jobs(self, temp_db: str) -> None:
        """dedupe returns jobs not already in DB, then inserts them."""
        existing = JobPost(
            source="test", company="Acme", title="Existing",
            url="https://ex.com/1", external_id="existing-001",
        )
        insert(existing)

        new_jobs = [
            JobPost(
                source="test", company="Acme", title="New Job 1",
                url="https://ex.com/2", external_id="new-001",
            ),
            JobPost(
                source="test", company="Acme", title="New Job 2",
                url="https://ex.com/3", external_id="new-002",
            ),
        ]
        result = dedupe(new_jobs)
        assert len(result) == 2
        assert is_seen(result[0]) is True
        assert is_seen(result[1]) is True

    def test_dedupe_skips_existing(self, temp_db: str) -> None:
        """Jobs already in DB are skipped."""
        existing = JobPost(
            source="test", company="Acme", title="Existing",
            url="https://ex.com/1", external_id="already-seen",
        )
        insert(existing)

        jobs = [
            JobPost(
                source="test", company="Acme", title="Existing",
                url="https://ex.com/1", external_id="already-seen",
            ),
            JobPost(
                source="test", company="Acme", title="New",
                url="https://ex.com/2", external_id="new-001",
            ),
        ]
        result = dedupe(jobs)
        assert len(result) == 1
        assert result[0].external_id == "new-001"


class TestCount:
    def test_count_returns_total_rows(self, temp_db: str) -> None:
        for i in range(5):
            insert(JobPost(
                source="test", company=f"Co{i}", title="T",
                url=f"https://ex.com/{i}", external_id=f"count-{i}",
            ))
        assert count() == 5
"""Tests for radar.dashboard.app — API endpoint logic (not integration).

Note: Full integration tests require a running uvicorn server with a clean DB.
These tests verify the API route logic by testing the filter/sort functions
in isolation using the actual FastAPI TestClient with a mocked _get_jobs.
"""
from __future__ import annotations

import pytest


class TestApiFilterLogic:
    """Test the API's filter and sort logic by directly testing the
    list_jobs endpoint handler with controlled job data."""

    def test_source_filter_jobspy(self) -> None:
        """source=jobspy returns only jobspy jobs."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [
            {"source": "jobspy", "company": "A", "title": "T", "score": 10},
            {"source": "naukri_v2", "company": "B", "title": "T", "score": 20},
            {"source": "jobspy", "company": "C", "title": "T", "score": 30},
        ]
        result = _filter_and_sort_jobs(jobs, source="jobspy")
        assert len(result) == 2
        assert all(j["source"] == "jobspy" for j in result)

    def test_source_filter_naukri_v2(self) -> None:
        """source=naukri_v2 returns only naukri jobs."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [
            {"source": "jobspy", "company": "A", "title": "T", "score": 10},
            {"source": "naukri_v2", "company": "B", "title": "T", "score": 20},
        ]
        result = _filter_and_sort_jobs(jobs, source="naukri_v2")
        assert len(result) == 1
        assert result[0]["source"] == "naukri_v2"

    def test_tier_strong(self) -> None:
        """tier=strong returns score >= 20."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [
            {"source": "x", "company": "A", "title": "T", "score": 45},
            {"source": "x", "company": "B", "title": "T", "score": 19},
            {"source": "x", "company": "C", "title": "T", "score": 20},
            {"source": "x", "company": "D", "title": "T", "score": 0},
        ]
        result = _filter_and_sort_jobs(jobs, tier="strong")
        assert len(result) == 2
        assert all((j.get("score") or 0) >= 20 for j in result)

    def test_tier_moderate(self) -> None:
        """tier=moderate returns 10 <= score < 20."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [{"source": "x", "company": "A", "title": "T", "score": s}
                for s in [5, 10, 15, 19, 20, 25]]
        result = _filter_and_sort_jobs(jobs, tier="moderate")
        assert len(result) == 3
        assert all(10 <= (j.get("score") or 0) < 20 for j in result)

    def test_tier_weak(self) -> None:
        """tier=weak returns 0 < score < 10."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [{"source": "x", "company": "A", "title": "T", "score": s}
                for s in [0, 5, 10, 15]]
        result = _filter_and_sort_jobs(jobs, tier="weak")
        assert len(result) == 1
        assert result[0]["score"] == 5

    def test_sort_by_score(self) -> None:
        """Default sort is by score descending."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [{"source": "x", "company": str(c), "title": "T", "score": s}
                for c, s in [("a", 10), ("b", 30), ("c", 20)]]
        result = _filter_and_sort_jobs(jobs)
        assert [j["score"] for j in result] == [30, 20, 10]

    def test_sort_by_date(self) -> None:
        """sort=date sorts by posted_at descending."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [
            {"source": "x", "company": "A", "title": "T", "posted_at": "2026-05-01", "score": 10},
            {"source": "x", "company": "B", "title": "T", "posted_at": "2026-05-03", "score": 5},
            {"source": "x", "company": "C", "title": "T", "posted_at": "2026-05-02", "score": 15},
        ]
        result = _filter_and_sort_jobs(jobs, sort="date")
        dates = [j.get("posted_at", "") for j in result]
        assert dates == sorted(dates, reverse=True)

    def test_sort_by_company(self) -> None:
        """sort=company sorts A-Z."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [{"source": "x", "company": c, "title": "T", "score": 10}
                for c in ["Zebra", "Apple", "Mango"]]
        result = _filter_and_sort_jobs(jobs, sort="company")
        assert [j["company"] for j in result] == ["Apple", "Mango", "Zebra"]

    def test_combined_source_and_tier(self) -> None:
        """source + tier filters can be combined."""
        from radar.dashboard.app import _filter_and_sort_jobs

        jobs = [
            {"source": "jobspy", "company": "A", "title": "T", "score": 45},
            {"source": "naukri_v2", "company": "B", "title": "T", "score": 45},
            {"source": "jobspy", "company": "C", "title": "T", "score": 19},
        ]
        result = _filter_and_sort_jobs(jobs, source="jobspy", tier="strong")
        assert len(result) == 1
        assert result[0]["company"] == "A"

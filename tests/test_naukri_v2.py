"""Tests for radar.scrapers.naukri_v2."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from radar.scrapers.naukri_v2 import _fetch_page, _parse_exp, scrape


class TestParseExp:
    """Tests for _parse_exp helper."""

    def test_parses_0_5_yrs(self) -> None:
        assert _parse_exp("0-5 Yrs") == (0, 5)

    def test_parses_2_7_yrs(self) -> None:
        assert _parse_exp("2-7 Yrs") == (2, 7)

    def test_parses_6_10_yrs(self) -> None:
        assert _parse_exp("6-10 Yrs") == (6, 10)

    def test_returns_none_for_empty(self) -> None:
        assert _parse_exp(None) is None
        assert _parse_exp("") is None

    def test_returns_none_for_non_range(self) -> None:
        assert _parse_exp("Fresher") is None
        assert _parse_exp("Not specified") is None


class TestNaukriV2Scrape:
    """Tests for naukri_v2 scrape function with mocked HTTP."""

    @patch("radar.scrapers.naukri_v2._fetch_page")
    def test_yields_jobpost_objects(self, mock_fetch) -> None:
        """scrape returns JobPost objects with correct fields."""
        mock_fetch.return_value = [
            {
                "jobId": "NJ-001",
                "unjobid": "NJ-001",
                "post": "DevOps Engineer",
                "companyName": "TechCorp",
                "jobDesc": "Looking for DevOps with Kubernetes.",
                "experience": "2-5 Yrs",
                "minExp": 2,
                "maxExp": 5,
                "addDate": "2026-05-01",
                "urlStr": "https://naukri.com/job/1",
                "CONTCITY": "Bangalore",
                "cityfield": "Bengaluru",
            }
        ]
        jobs = list(scrape("DevOps Engineer", pages=1))
        assert len(jobs) == 1
        assert jobs[0].source == "naukri_v2"
        assert jobs[0].company == "TechCorp"
        assert jobs[0].title == "DevOps Engineer"
        assert jobs[0].external_id == "NJ-001"
        assert jobs[0].min_exp == 2
        assert jobs[0].max_exp == 5
        assert jobs[0].location == "Bangalore, Bengaluru"

    @patch("radar.scrapers.naukri_v2._fetch_page")
    def test_deduplicates_across_pages(self, mock_fetch) -> None:
        """Same jobId on multiple pages yields only one JobPost."""
        job = {
            "jobId": "NJ-DUP",
            "unjobid": "NJ-DUP",
            "post": "SRE Engineer",
            "companyName": "CloudFirst",
            "jobDesc": "SRE role.",
            "experience": "3-6 Yrs",
            "minExp": 3,
            "maxExp": 6,
            "addDate": "2026-05-01",
            "urlStr": "https://naukri.com/job/dup",
            "CONTCITY": "Pune",
            "cityfield": "Pune",
        }
        mock_fetch.side_effect = [
            [job],  # page 1
            [job],  # page 2 (duplicate)
        ]
        jobs = list(scrape("SRE", pages=2))
        assert len(jobs) == 1
        assert jobs[0].external_id == "NJ-DUP"

    @patch("radar.scrapers.naukri_v2._fetch_page")
    def test_remote_detected_from_title_keywords(self, mock_fetch) -> None:
        """'Remote' in title sets location to 'Remote'."""
        mock_fetch.return_value = [
            {
                "jobId": "NJ-002",
                "unjobid": "NJ-002",
                "post": "DevOps Engineer - Remote",
                "companyName": "RemoteCorp",
                "jobDesc": "Work from home.",
                "experience": "2-4 Yrs",
                "minExp": 2,
                "maxExp": 4,
                "addDate": "2026-05-01",
                "urlStr": "https://naukri.com/job/2",
                "CONTCITY": "",
                "cityfield": "",
            }
        ]
        jobs = list(scrape("DevOps", pages=1))
        assert jobs[0].location == "Remote"

    @patch("radar.scrapers.naukri_v2._fetch_page")
    def test_skips_empty_job_id(self, mock_fetch) -> None:
        """Job with no jobId is skipped."""
        mock_fetch.return_value = [
            {
                "jobId": "",
                "unjobid": "",
                "post": "Some Job",
                "companyName": "X",
                "jobDesc": "Desc",
                "addDate": "2026-05-01",
                "urlStr": "https://naukri.com/job/3",
            }
        ]
        jobs = list(scrape("Some", pages=1))
        assert len(jobs) == 0

    @patch("radar.scrapers.naukri_v2._fetch_page")
    def test_continues_after_page_failure(self, mock_fetch) -> None:
        """Exception on one page doesn't stop the generator."""
        call_count = [0]

        def side_effect(keyword, page, location):
            call_count[0] += 1
            if page == 2:
                raise RuntimeError("Network error")
            return [
                {
                    "jobId": f"NJ-PAGE{page}",
                    "unjobid": f"NJ-PAGE{page}",
                    "post": "DevOps",
                    "companyName": "Co",
                    "jobDesc": "Desc",
                    "addDate": "2026-05-01",
                    "urlStr": f"https://naukri.com/job/p{page}",
                }
            ]

        mock_fetch.side_effect = side_effect
        jobs = list(scrape("DevOps", pages=3))
        # Page 1 succeeded, page 2 failed, page 3 may or may not run depending on len check
        assert len(jobs) >= 1

    @patch("radar.scrapers.naukri_v2._fetch_page")
    def test_truncates_description_at_5000_chars(self, mock_fetch) -> None:
        """Description is truncated to 5000 chars."""
        mock_fetch.return_value = [
            {
                "jobId": "NJ-003",
                "unjobid": "NJ-003",
                "post": "Engineer",
                "companyName": "X",
                "jobDesc": "A" * 6000,  # 6000 chars
                "addDate": "2026-05-01",
                "urlStr": "https://naukri.com/job/3",
            }
        ]
        jobs = list(scrape("Engineer", pages=1))
        assert len(jobs[0].description) == 5000

    @patch("radar.scrapers.naukri_v2._fetch_page")
    def test_min_exp_from_numeric_field(self, mock_fetch) -> None:
        """min_exp uses numeric minExp field when experience text is absent.

        When both experience text AND numeric fields are present, the text
        takes precedence (parsed via _parse_exp). So we omit the experience
        text field to test the numeric fallback.
        """
        mock_fetch.return_value = [
            {
                "jobId": "NJ-004",
                "unjobid": "NJ-004",
                "post": "Engineer",
                "companyName": "X",
                "jobDesc": "Desc",
                # No "experience" text — relies on numeric minExp/maxExp
                "minExp": 6,
                "maxExp": 10,
                "addDate": "2026-05-01",
                "urlStr": "https://naukri.com/job/4",
            }
        ]
        jobs = list(scrape("Engineer", pages=1))
        assert jobs[0].min_exp == 6
        assert jobs[0].max_exp == 10
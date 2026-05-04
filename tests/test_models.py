"""Tests for radar.models.JobPost."""
from __future__ import annotations

import json

import pytest

from radar.models import JobPost


class TestJobPost:
    def test_required_fields(self) -> None:
        """JobPost can be created with all required fields."""
        job = JobPost(
            source="linkedin",
            company="Acme",
            title="DevOps Engineer",
            location="Bangalore",
            url="https://example.com/1",
            external_id="ln-123",
        )
        assert job.source == "linkedin"
        assert job.company == "Acme"
        assert job.title == "DevOps Engineer"
        assert job.score == 0  # default

    def test_optional_fields(self) -> None:
        """JobPost with all optional fields."""
        job = JobPost(
            source="naukri_v2",
            company="TechCorp",
            title="SRE Engineer",
            location="Remote India",
            url="https://naukri.com/job/1",
            external_id="nk-456",
            posted_at="2026-05-01",
            description="Looking for SRE with Kubernetes.",
            min_exp=2,
            max_exp=5,
            score=75,
        )
        assert job.min_exp == 2
        assert job.max_exp == 5
        assert job.score == 75
        assert job.posted_at == "2026-05-01"

    def test_model_dump_json(self) -> None:
        """JobPost serializes correctly to JSON."""
        job = JobPost(
            source="test",
            company="Acme",
            title="DevOps",
            location="Bangalore",
            url="https://ex.com/1",
            external_id="1",
            score=50,
        )
        data = json.loads(job.model_dump_json())
        assert data["source"] == "test"
        assert data["score"] == 50

    def test_default_score_is_zero(self) -> None:
        """Score defaults to 0 when not provided."""
        job = JobPost(
            source="test", company="x", title="y", url="z", external_id="1"
        )
        assert job.score == 0

    def test_external_id_required(self) -> None:
        """external_id must be provided (no default)."""
        with pytest.raises(ValueError):
            JobPost(source="test", company="x", title="y", url="z", external_id="")

    def test_source_required(self) -> None:
        """source must be provided."""
        with pytest.raises(ValueError):
            JobPost(company="x", title="y", url="z", external_id="1")
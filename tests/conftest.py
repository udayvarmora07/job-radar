"""Pytest fixtures and shared mocks for radar tests."""
from __future__ import annotations

import os

# Ensure test env vars are set (don't clear — pytest needs PYTHONPATH/PYTEST_CURRENT_TEST)
os.environ.setdefault("GMAIL_USER", "test@example.com")
os.environ.setdefault("GMAIL_APP_PASSWORD", "testpassword")
os.environ.setdefault("NOTIFY_EMAIL", "notify@example.com")

import pytest


@pytest.fixture
def sample_jobpost() -> "JobPost":
    """One canonical JobPost used across tests."""
    from radar.models import JobPost

    return JobPost(
        source="test",
        company="Acme Corp",
        title="DevOps Engineer",
        location="Bangalore, India",
        url="https://example.com/job/1",
        external_id="ext-001",
        posted_at="2026-05-01",
        description="We are looking for a DevOps Engineer with Kubernetes and AWS experience.",
        min_exp=2,
        max_exp=5,
        score=0,
    )


@pytest.fixture
def senior_jobpost() -> "JobPost":
    """A JobPost that should be filtered out (senior title)."""
    from radar.models import JobPost

    return JobPost(
        source="test",
        company="Acme Corp",
        title="Senior DevOps Engineer",
        location="Bangalore, India",
        url="https://example.com/job/2",
        external_id="ext-002",
        posted_at="2026-05-01",
        description="We are looking for a Senior DevOps Engineer with 6+ years experience.",
        min_exp=6,
        max_exp=10,
        score=0,
    )


@pytest.fixture
def remote_jobpost() -> "JobPost":
    """A remote-friendly JobPost."""
    from radar.models import JobPost

    return JobPost(
        source="test",
        company="Acme Corp",
        title="SRE Engineer",
        location="Remote India",
        url="https://example.com/job/3",
        external_id="ext-003",
        posted_at="2026-05-02",
        description="SRE role, remote work from home, kubernetes and terraform.",
        min_exp=3,
        max_exp=6,
        score=0,
    )


@pytest.fixture
def naukri_mock_response() -> list[dict]:
    """Sample Naukri v2 API JSON response for testing."""
    return [
        {
            "jobId": "NJ-12345",
            "unjobid": "NJ-12345",
            "post": "DevOps Engineer",
            "companyName": "TechCorp India",
            "jobDesc": "We need a DevOps Engineer with expertise in Kubernetes and Terraform. Remote work available.",
            "experience": "2-5 Yrs",
            "minExp": 2,
            "maxExp": 5,
            "addDate": "2026-05-01",
            "urlStr": "https://www.naukri.com/job/abc123",
            "CONTCITY": "Bangalore",
            "cityfield": "Bengaluru",
        },
        {
            "jobId": "NJ-67890",
            "unjobid": "NJ-67890",
            "post": "SRE Engineer",
            "companyName": "CloudFirst",
            "jobDesc": "Site Reliability Engineer needed. Work from home. 3-6 years experience.",
            "experience": "3-6 Yrs",
            "minExp": 3,
            "maxExp": 6,
            "addDate": "2026-04-28",
            "urlStr": "https://www.naukri.com/job/def456",
            "CONTCITY": "Pune",
            "cityfield": "Pune",
        },
        {
            "jobId": "NJ-11111",
            "unjobid": "NJ-11111",
            "post": "Senior Platform Engineer",
            "companyName": "BigTech",
            "jobDesc": "We need a Senior Platform Engineer with 8+ years of experience.",
            "experience": "8-12 Yrs",
            "minExp": 8,
            "maxExp": 12,
            "addDate": "2026-04-20",
            "urlStr": "https://www.naukri.com/job/ghi789",
            "CONTCITY": "Hyderabad",
            "cityfield": "Hyderabad",
        },
    ]


@pytest.fixture
def sample_jobpost_list() -> list:
    """A list of JobPost objects spanning multiple filter scenarios."""
    from radar.models import JobPost

    return [
        # Should pass: valid DevOps, Bangalore
        JobPost(
            source="test", company="Acme", title="DevOps Engineer",
            location="Bangalore, India", url="https://ex.com/1",
            external_id="1", posted_at="2026-05-01",
            description="Kubernetes and AWS.", min_exp=2, max_exp=5,
        ),
        # Should pass: remote
        JobPost(
            source="test", company="Acme", title="SRE Engineer",
            location="Remote India", url="https://ex.com/2",
            external_id="2", posted_at="2026-05-02",
            description="Cloud monitoring.", min_exp=3, max_exp=6,
        ),
        # Should fail: senior title
        JobPost(
            source="test", company="Acme", title="Senior DevOps Engineer",
            location="Bangalore, India", url="https://ex.com/3",
            external_id="3", posted_at="2026-05-01",
            description="Manage team.", min_exp=6, max_exp=10,
        ),
        # Should fail: experience 6+ years
        JobPost(
            source="test", company="Acme", title="Platform Engineer",
            location="Pune, India", url="https://ex.com/4",
            external_id="4", posted_at="2026-04-15",
            description="Infrastructure.", min_exp=6, max_exp=12,
        ),
        # Should fail: wrong location
        JobPost(
            source="test", company="Acme", title="DevOps Engineer",
            location="San Francisco, USA", url="https://ex.com/5",
            external_id="5", posted_at="2026-05-01",
            description="AWS.", min_exp=2, max_exp=4,
        ),
        # Should pass: old date still allowed (MAX_JOB_AGE_DAYS = 30)
        JobPost(
            source="test", company="Acme", title="Kubernetes Engineer",
            location="Ahmedabad, India", url="https://ex.com/6",
            external_id="6", posted_at="2026-04-01",
            description="EKS, ArgoCD.", min_exp=3, max_exp=5,
        ),
    ]

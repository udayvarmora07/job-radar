"""Tests for radar.filters — experience, title, location, keyword, and combined filter_and_score."""
from __future__ import annotations

import pytest

from radar.filters import (
    filter_and_score,
    filter_title,
    is_excluded_experience,
    is_excluded_location,
    is_excluded_titlekw,
    is_old,
    is_senior_or_excluded,
    score_job,
)
from radar.models import JobPost


class TestIsExcludedExperience:
    """Tests for is_excluded_experience — rejects roles with 6+ years min."""

    def test_rejects_min_exp_6(self) -> None:
        """min_exp=6 must be rejected."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            min_exp=6, max_exp=10,
        )
        assert is_excluded_experience(job) is True

    def test_rejects_min_exp_7(self) -> None:
        """min_exp=7 must be rejected."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            min_exp=7,
        )
        assert is_excluded_experience(job) is True

    def test_rejects_open_ended_6_plus(self) -> None:
        """min_exp=0 + max_exp>=6 (open-ended range) must be rejected."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            min_exp=0, max_exp=8,
        )
        assert is_excluded_experience(job) is True

    def test_rejects_10_plus_years_text(self) -> None:
        """Text with '10+ years' must be rejected."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            description="Looking for someone with 10+ years of experience.",
        )
        assert is_excluded_experience(job) is True

    def test_rejects_range_5_7_years_text(self) -> None:
        """Text with '5-7 years' (lower bound 5) must be rejected."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            description="Experience: 5-7 years in relevant field.",
        )
        assert is_excluded_experience(job) is True

    def test_rejects_minimum_6_years_text(self) -> None:
        """Text with 'minimum 6 years' must be rejected."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            description="Minimum 6 years of experience required.",
        )
        assert is_excluded_experience(job) is True

    def test_accepts_min_exp_2(self) -> None:
        """min_exp=2 is acceptable."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            min_exp=2, max_exp=5,
        )
        assert is_excluded_experience(job) is False

    def test_accepts_min_exp_5(self) -> None:
        """min_exp=5 is acceptable (threshold is 6+)."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            min_exp=5, max_exp=8,
        )
        assert is_excluded_experience(job) is False

    def test_accepts_no_exp_data(self) -> None:
        """JobPost with no experience data is allowed through."""
        job = JobPost(
            source="test", company="x", title="DevOps Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_excluded_experience(job) is False


class TestIsSeniorOrExcluded:
    """Tests for is_senior_or_excluded — rejects senior/lead/manager titles."""

    def test_rejects_senior(self) -> None:
        job = JobPost(
            source="test", company="x", title="Senior DevOps Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is True

    def test_rejects_lead(self) -> None:
        job = JobPost(
            source="test", company="x", title="Lead SRE",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is True

    def test_rejects_principal(self) -> None:
        job = JobPost(
            source="test", company="x", title="Principal Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is True

    def test_rejects_staff(self) -> None:
        job = JobPost(
            source="test", company="x", title="Staff Cloud Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is True

    def test_rejects_manager(self) -> None:
        job = JobPost(
            source="test", company="x", title="Engineering Manager",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is True

    def test_rejects_director(self) -> None:
        job = JobPost(
            source="test", company="x", title="Director of Platform",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is True

    def test_rejects_sr(self) -> None:
        job = JobPost(
            source="test", company="x", title="Sr. DevOps Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is True

    def test_accepts_plain_devops(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is False

    def test_accepts_sre(self) -> None:
        job = JobPost(
            source="test", company="x", title="SRE Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is False

    def test_accepts_platform_engineer(self) -> None:
        job = JobPost(
            source="test", company="x", title="Platform Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_senior_or_excluded(job) is False


class TestFilterTitle:
    """Tests for filter_title — accepts DevOps/SRE/Cloud/Platform target titles."""

    def test_accepts_devops(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert filter_title(job) is True

    def test_accepts_sre(self) -> None:
        job = JobPost(
            source="test", company="x", title="Site Reliability Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert filter_title(job) is True

    def test_accepts_cloud_engineer(self) -> None:
        job = JobPost(
            source="test", company="x", title="Cloud Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert filter_title(job) is True

    def test_accepts_platform_engineer(self) -> None:
        job = JobPost(
            source="test", company="x", title="Platform Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert filter_title(job) is True

    def test_accepts_kubernetes_engineer(self) -> None:
        job = JobPost(
            source="test", company="x", title="Kubernetes Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert filter_title(job) is True

    def test_rejects_sales(self) -> None:
        job = JobPost(
            source="test", company="x", title="Sales Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert filter_title(job) is False

    def test_rejects_data_engineer(self) -> None:
        job = JobPost(
            source="test", company="x", title="Data Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert filter_title(job) is False

    def test_accepts_gitops_engineer(self) -> None:
        job = JobPost(
            source="test", company="x", title="GitOps Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert filter_title(job) is True


class TestIsExcludedLocation:
    """Tests for is_excluded_location — rejects non-India/non-Remote."""

    def test_accepts_remote(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="Remote", external_id="1",
        )
        assert is_excluded_location(job) is False

    def test_accepts_wfh(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="Work from home", external_id="1",
        )
        assert is_excluded_location(job) is False

    def test_accepts_bangalore(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="Bangalore", external_id="1",
        )
        assert is_excluded_location(job) is False

    def test_accepts_hyderabad(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="Hyderabad", external_id="1",
        )
        assert is_excluded_location(job) is False

    def test_accepts_pune(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="Pune", external_id="1",
        )
        assert is_excluded_location(job) is False

    def test_rejects_usa(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="San Francisco, USA", external_id="1",
        )
        assert is_excluded_location(job) is True

    def test_rejects_uk(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="London, UK", external_id="1",
        )
        assert is_excluded_location(job) is True

    def test_rejects_canada(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="Toronto, Canada", external_id="1",
        )
        assert is_excluded_location(job) is True

    def test_rejects_singapore(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps", url="z",
            location="Singapore", external_id="1",
        )
        assert is_excluded_location(job) is True


class TestIsExcludedTitleKw:
    """Tests for is_excluded_titlekw — rejects fresher/intern/contract (non-DevOps)."""

    def test_rejects_intern(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps Intern",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_excluded_titlekw(job) is True

    def test_rejects_fresher(self) -> None:
        job = JobPost(
            source="test", company="x", title="DevOps Fresher",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_excluded_titlekw(job) is True

    def test_accepts_contract_devops(self) -> None:
        """'contract devops' should be accepted (exception in regex)."""
        job = JobPost(
            source="test", company="x", title="Contract DevOps Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        assert is_excluded_titlekw(job) is False


class TestScoreJob:
    """Tests for score_job — skill keyword scoring."""

    def test_kubernetes_high_score(self) -> None:
        job = JobPost(
            source="test", company="x",
            title="Kubernetes Engineer",
            url="z", location="Bangalore", external_id="1",
            description="Kubernetes, Terraform, AWS, ArgoCD, GitHub Actions.",
        )
        score = score_job(job)
        assert score > 30  # kubernetes(15) + k8s(10) + terraform(12) + aws(10) + gitops(10) + argocd(8) + github actions(7)

    def test_devops_moderate_score(self) -> None:
        job = JobPost(
            source="test", company="x",
            title="DevOps Engineer",
            url="z", location="Bangalore", external_id="1",
            description="Linux, Python, Docker, Jenkins.",
        )
        score = score_job(job)
        assert 15 < score < 40

    def test_no_matching_keywords(self) -> None:
        job = JobPost(
            source="test", company="x",
            title="Cleaner",
            url="z", location="Bangalore", external_id="1",
            description="Cleaning services.",
        )
        score = score_job(job)
        assert score == 0


class TestIsOld:
    """Tests for is_old — MAX_JOB_AGE_DAYS = 30."""

    def test_recent_job_not_old(self) -> None:
        from datetime import datetime, timedelta
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            posted_at=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        )
        assert is_old(job) is False

    def test_60_day_old_job_is_old(self) -> None:
        from datetime import datetime, timedelta
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
            posted_at=(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        )
        assert is_old(job) is True

    def test_no_date_not_old(self) -> None:
        """Jobs with no posted_at are allowed (assume recent)."""
        job = JobPost(
            source="test", company="x", title="y", url="z",
            location="Bangalore", external_id="1",
        )
        assert is_old(job) is False


class TestFilterAndScore:
    """Tests for the combined filter_and_score pipeline."""

    def test_passes_valid_job(self, sample_jobpost) -> None:
        """A valid DevOps job with 2-5 years exp passes all filters."""
        results = filter_and_score([sample_jobpost])
        assert len(results) == 1
        assert results[0].score > 0

    def test_rejects_senior_job(self, senior_jobpost) -> None:
        """Senior title → filtered out."""
        results = filter_and_score([senior_jobpost])
        assert len(results) == 0

    def test_rejects_high_exp(self, sample_jobpost) -> None:
        """min_exp=6 → filtered out."""
        high_exp = sample_jobpost.model_copy()
        high_exp.min_exp = 6
        high_exp.max_exp = 10
        results = filter_and_score([high_exp])
        assert len(results) == 0

    def test_rejects_non_india_location(self) -> None:
        """USA location → filtered out."""
        from radar.models import JobPost
        job = JobPost(
            source="test", company="x", title="DevOps Engineer",
            url="z", location="San Francisco, USA", external_id="1",
            min_exp=2, max_exp=5,
        )
        results = filter_and_score([job])
        assert len(results) == 0

    def test_rejects_non_target_title(self) -> None:
        """Sales Engineer → filtered out by title filter."""
        from radar.models import JobPost
        job = JobPost(
            source="test", company="x", title="Sales Engineer",
            url="z", location="Bangalore", external_id="1",
        )
        results = filter_and_score([job])
        assert len(results) == 0

    def test_scores_sorted_descending(self, sample_jobpost_list) -> None:
        """filter_and_score returns jobs sorted by score descending."""
        results = filter_and_score(sample_jobpost_list)
        if len(results) > 1:
            scores = [j.score for j in results]
            assert scores == sorted(scores, reverse=True)

    def test_empty_input_returns_empty(self) -> None:
        """Empty list → empty list."""
        assert filter_and_score([]) == []
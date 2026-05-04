"""Pydantic models for all job records crossing module boundaries."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobPost(BaseModel):
    """Normalized job record used across all scrapers, filters, and notifier."""

    source: str = Field(description="ATS name: greenhouse, lever, ashby, jobspy, naukri_v2, etc.")
    company: str = Field(description="Company slug or display name")
    title: str = Field(description="Job title as shown on the ATS board")
    location: str = Field(default="Unknown")
    url: str = Field(description="Direct link to the job posting")
    external_id: str = Field(min_length=1, description="ATS-specific job ID for deduping")
    posted_at: Optional[str] = Field(default=None, description="ISO 8601 date string when posted")
    description: str = Field(default="", max_length=5000)
    score: int = Field(default=0, description="Skill keyword overlap score (0-100)")
    min_exp: Optional[int] = Field(default=None, description="Minimum years of experience (numeric)")
    max_exp: Optional[int] = Field(default=None, description="Maximum years of experience (numeric)")

    def __hash__(self) -> int:
        return hash((self.source, self.external_id))
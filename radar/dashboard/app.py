"""FastAPI app for the Job Radar dashboard."""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "seen_jobs.db"
STATIC_DIR = BASE_DIR / "radar" / "dashboard" / "static"


app = FastAPI(
    title="Job Radar",
    description="Live DevOps/SRE/Cloud/Platform Engineer jobs in India",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _query_jobs() -> list[dict]:
    """Load all jobs from seen_jobs.db, sorted by score desc."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT source, company, title, location, url, external_id,
                   posted_at, description, score
            FROM seen_jobs
            ORDER BY score DESC, posted_at DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log.error("DB query failed: %s", e)
        return []


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the dashboard UI."""
    with open(BASE_DIR / "radar" / "dashboard" / "templates" / "index.html") as f:
        return f.read()


@app.get("/api/jobs")
async def list_jobs(
    q: Optional[str] = Query(None, description="Search term"),
    location: Optional[str] = Query(None, description="Filter by location"),
    tier: Optional[str] = Query(None, description="Score tier: strong/moderate/weak"),
    sort: Optional[str] = Query("score", description="Sort by: score, date, company"),
):
    """
    Return filtered, sorted job list as JSON.

    - q: search term (matches title, company, description)
    - location: 'remote' or city name
    - tier: 'strong' (>=20), 'moderate' (10-19), 'weak' (<10)
    - sort: 'score' (default), 'date', 'company'
    """
    jobs = _query_jobs()

    # Search filter
    if q:
        q_lower = q.lower()
        jobs = [
            j for j in jobs
            if q_lower in (j.get("title") or "").lower()
            or q_lower in (j.get("company") or "").lower()
            or q_lower in (j.get("description") or "").lower()
        ]

    # Location filter
    if location:
        loc_lower = location.lower()
        if loc_lower == "remote":
            jobs = [j for j in jobs if "remote" in (j.get("location") or "").lower()
                    or "wfh" in (j.get("location") or "").lower()
                    or "work from home" in (j.get("location") or "").lower()]
        else:
            jobs = [j for j in jobs if loc_lower in (j.get("location") or "").lower()]

    # Score tier filter — recalibrated to actual score range (max=33)
    if tier:
        tier_lower = tier.lower()
        if tier_lower == "strong":
            jobs = [j for j in jobs if (j.get("score") or 0) >= 20]
        elif tier_lower == "moderate":
            jobs = [j for j in jobs if 10 <= (j.get("score") or 0) < 20]
        elif tier_lower == "weak":
            jobs = [j for j in jobs if 0 < (j.get("score") or 0) < 10]

    # Sort
    if sort == "date":
        jobs.sort(key=lambda j: j.get("posted_at") or "", reverse=True)
    elif sort == "company":
        jobs.sort(key=lambda j: (j.get("company") or "").lower())
    else:  # score
        jobs.sort(key=lambda j: j.get("score") or 0, reverse=True)

    return JSONResponse(content={"count": len(jobs), "jobs": jobs})


@app.get("/jobs.json")
async def jobs_json():
    """Serve all jobs as raw JSON (direct DB query)."""
    return JSONResponse(content=_query_jobs())
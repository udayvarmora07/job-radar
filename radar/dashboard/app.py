"""FastAPI app for the Job Radar dashboard."""
from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from radar.filters import filter_and_score
from radar.models import JobPost
from radar.scrapers import jobspy_runner
from radar.scrapers.naukri_v2 import scrape as naukri_scrape

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
STATIC_DIR = BASE_DIR / "radar" / "dashboard" / "static"
DB_PATH = BASE_DIR / "seen_jobs.db"

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

# ─── Cache ────────────────────────────────────────────────────────────────────

CACHE_TTL_SECONDS = 900  # 15 minutes

_cache: dict = {"jobs": [], "timestamp": 0.0}


def _sync_db_from_github() -> None:
    """Pull latest seen_jobs.db from GitHub on startup."""
    db_url = "https://raw.githubusercontent.com/udayvarmora07/job-radar/main/seen_jobs.db"
    try:
        import urllib.request
        urllib.request.urlretrieve(db_url, str(DB_PATH))
        log.info("synced seen_jobs.db from GitHub")
    except Exception as e:
        log.warning("DB sync failed: %s", e)


def _load_from_db() -> list[dict]:
    """Load all jobs from seen_jobs.db."""
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT source, company, title, location, url, external_id, posted_at, score "
            "FROM seen_jobs ORDER BY score DESC, posted_at DESC"
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log.error("DB query failed: %s", e)
        return []


def _scrape_and_filter() -> list[dict]:
    """Re-scrape LinkedIn + Indeed + Naukri v2, return filtered + scored jobs."""
    searches = [
        ("DevOps Engineer", True),
        ("SRE Engineer", True),
        ("Cloud Engineer", True),
        ("Platform Engineer", True),
        ("Site Reliability Engineer", True),
        ("Kubernetes Engineer", True),
        ("GitOps Engineer", True),
        ("Infrastructure Engineer", True),
        ("DevOps Engineer", False),  # city-based
        ("SRE Engineer", False),
        ("Cloud Engineer", False),
    ]
    # Multi-site scraping: linkedin + indeed + naukri v2
    all_sites = [
        (["linkedin"], searches),
        (["indeed"], searches),
    ]

    jobs: list[JobPost] = []

    # LinkedIn + Indeed
    for site_names, site_searches in all_sites:
        for search_term, is_remote in site_searches:
            country = "usa"
            if "indeed" in site_names:
                country = "india"
            config = jobspy_runner.JobSpyConfig(
                site_names=site_names,
                search_term=search_term,
                location="India",
                is_remote=is_remote,
                results_wanted=15,
                country_indeed=country,
            )
            try:
                for job in jobspy_runner.scrape(config):
                    jobs.append(job)
            except Exception:
                pass

    # Naukri v2 (3 pages per keyword, 20 per page = 60 per keyword)
    for keyword, is_remote in searches:
        if is_remote:
            continue  # Naukri v2 doesn't have remote flag
        try:
            for job in naukri_scrape(keyword=keyword, pages=3):
                jobs.append(job)
        except Exception:
            pass

    filtered = filter_and_score(jobs)
    return [j.model_dump(mode="json") for j in filtered]


def _get_jobs() -> list[dict]:
    age = time.time() - _cache.get("timestamp", 0)
    if age > CACHE_TTL_SECONDS or not _cache.get("jobs"):
        fresh = _scrape_and_filter()
        _cache["jobs"] = fresh
        _cache["timestamp"] = time.time()
        log.info("Cache refreshed: %d jobs", len(fresh))
    return _cache.get("jobs", [])


@app.on_event("startup")
async def startup():
    _sync_db_from_github()
    db_jobs = _load_from_db()
    _cache["jobs"] = db_jobs
    _cache["timestamp"] = time.time()
    log.info("Cache pre-warmed from DB: %d jobs", len(db_jobs))
    import threading
    def _bg():
        try:
            fresh = _scrape_and_filter()
            _cache["jobs"] = fresh
            _cache["timestamp"] = time.time()
            log.info("Background refresh done: %d jobs", len(fresh))
        except Exception as e:
            log.error("Background refresh failed: %s", e)
    threading.Thread(target=_bg, daemon=True).start()
    print("STARTUP: background thread spawned", flush=True)


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(BASE_DIR / "radar" / "dashboard" / "templates" / "index.html") as f:
        return f.read()


@app.get("/api/jobs")
async def list_jobs(
    q: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    sort: Optional[str] = Query("score"),
    source: Optional[str] = Query(None, description="Filter by source: linkedin, indeed, naukri_v2"),
):
    jobs = _get_jobs()

    if q:
        q_lower = q.lower()
        jobs = [j for j in jobs
                if q_lower in (j.get("title") or "").lower()
                or q_lower in (j.get("company") or "").lower()]

    if location:
        loc_lower = location.lower()
        if loc_lower == "remote":
            jobs = [j for j in jobs if
                not j.get("location") or
                any(k in (j.get("location") or "").lower()
                    for k in ("remote", "wfh", "work from home"))]
        else:
            jobs = [j for j in jobs if loc_lower in (j.get("location") or "").lower()]

    if tier:
        if tier == "strong":
            jobs = [j for j in jobs if (j.get("score") or 0) >= 20]
        elif tier == "moderate":
            jobs = [j for j in jobs if 10 <= (j.get("score") or 0) < 20]
        elif tier == "weak":
            jobs = [j for j in jobs if 0 < (j.get("score") or 0) < 10]

    if source:
        jobs = [j for j in jobs if j.get("source") == source]

    if sort == "date":
        jobs.sort(key=lambda j: j.get("posted_at") or "", reverse=True)
    elif sort == "company":
        jobs.sort(key=lambda j: (j.get("company") or "").lower())
    else:
        jobs.sort(key=lambda j: j.get("score") or 0, reverse=True)

    return JSONResponse(content={"count": len(jobs), "jobs": jobs})


@app.get("/api/refresh")
async def force_refresh():
    """Force blocking cache refresh."""
    fresh = _scrape_and_filter()
    _cache["jobs"] = fresh
    _cache["timestamp"] = time.time()
    log.info("Force refresh: %d jobs", len(fresh))
    return JSONResponse(content={"status": "ok", "count": len(fresh)})


@app.get("/api/debug")
async def debug():
    age = time.time() - _cache.get("timestamp", 0)
    return JSONResponse(content={
        "cached_jobs": len(_cache.get("jobs", [])),
        "cache_age_seconds": round(age, 1),
        "cache_fresh": age < CACHE_TTL_SECONDS,
    })
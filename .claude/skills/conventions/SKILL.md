---
name: conventions
description: Project coding conventions for the job-radar repo. Auto-loads when Claude is writing or editing Python files in this project.
user-invocable: false
---

# Job Radar Conventions

## Python
- Python 3.12, full type hints with `from __future__ import annotations`
- All data crossing module boundaries: pydantic v2 BaseModel
- All external I/O wrapped in `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1,max=10))`
- Use `logging.getLogger(__name__)` — never `print()`

## Commits
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`
- One logical change per commit

## Tests
- Every new scraper needs a test with mocked HTTP
- Pytest fixtures live in `tests/conftest.py`

## Imports
Order: stdlib, third-party, local — separated by blank lines.

## Error handling
- Network errors: log + skip that source, never crash the whole pipeline
- Parse errors: log the offending payload, skip that record
- Email send failure: raise loudly so GitHub Actions marks the run as failed
---
description: Full ship cycle for the current change. Runs tests, invokes code-reviewer subagent, formats commit, pushes branch, opens PR.
---

Ship the current change.

Steps:
1. Run `pytest -v` — if any test fails, STOP and report
2. Run `python -m radar.main --dry-run` — if it errors, STOP and report
3. Invoke the `code-reviewer` subagent on `git diff main`
4. If reviewer says CHANGES REQUESTED, STOP and surface issues
5. Stage changes: `git add -A`
6. Propose a conventional-commit message based on the diff; ask user to approve
7. On approval: commit, push branch, run `gh pr create --fill`
8. Report PR URL
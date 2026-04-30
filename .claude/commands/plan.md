---
description: Enter plan mode for the next feature. Reads CLAUDE.md, surveys the repo, produces a step-by-step implementation plan WITHOUT writing code.
---

You are now in planning mode for: $ARGUMENTS

Process:
1. Read CLAUDE.md fully
2. Spawn the `ats-researcher` subagent if this involves a new company/ATS
3. Read all files in `radar/` that would be touched
4. Produce a plan with:
   - Files to create/modify (with one-line purpose each)
   - New dependencies (must justify each)
   - Test strategy
   - Estimated diff size
   - Risks / unknowns

Do NOT write any code. End with: "Approve this plan? (yes / revise / cancel)"
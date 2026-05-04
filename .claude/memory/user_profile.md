---
name: user_profile
description: Uday Varmora's developer profile and preferences
type: user
---

# User Profile — Uday Varmora

## Role & Background
- DevOps Engineer at eSparkBiz, Ahmedabad, India
- ~1.5 years experience (intern Jan–May 2025, FT from Jun 2025)
- Core stack: Kubernetes (EKS), Terraform, Docker, GitHub Actions, AWS CodeBuild, ArgoCD, Prometheus, Grafana, Loki, Python, Bash
- Target roles: DevOps Engineer, SRE, Cloud Engineer, Platform Engineer, Kubernetes Engineer

## Collaboration Preferences
- **Code delivery**: terse, no summaries — show the diff not the narration
- **Testing**: insist on running the full test suite before marking done; if UI can't be tested directly, say so explicitly
- **Reviews**: prefer direct feedback over long explanations; if an approach is non-obvious, ask "why" first
- **Commits**: conventional commits (`feat:`, `fix:`, `chore:`), squash-merge on PR
- **Avoid**: fluff, emoji in code, unnecessary abstractions, speculative features

## What to Avoid
- Don't mock the database in integration tests — prod migration failures masked by mocks
- Don't add dependencies without justification in the commit message
- Don't write code that doesn't have an immediate use case

## Git Preferences
- Work on feature branches, squash-merge to main
- Never force-push to main
- All secrets via env vars — never hardcoded
- Never commit `.env`, API keys, or non-CI-generated `.db` files
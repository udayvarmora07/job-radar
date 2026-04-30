---
name: think-hard
description: Force structured step-by-step reasoning for complex architectural or design decisions. Use when planning anything involving multiple components, trade-offs, or non-obvious failure modes.
allowed-tools: mcp__sequential-thinking__sequentialthinking, Read
---

# Think Hard Skill

When invoked with `/think-hard <topic>`, follow this process:

## Step 1 — Frame the problem
Read CLAUDE.md and any files relevant to the topic. State the problem in one sentence.

## Step 2 — Decompose with sequential-thinking
Call `mcp__sequential-thinking__sequentialthinking` with:
- thought_number starting at 1
- total_thoughts initially set to 8 (revise upward if needed)
- Each thought should be ~3-4 sentences exploring one facet
- Allow revisions and branching when a thought reveals a flaw in earlier reasoning

## Step 3 — Cover these angles minimum
1. Happy path: what's the simplest version that works?
2. Failure modes: what breaks first, and why?
3. Constraints: what limits (rate limits, token budgets, cron timing, GitHub Actions free tier) bound this?
4. Trade-offs: what are we explicitly giving up?
5. v1 vs v2 split: what defers to later without painting us into a corner?

## Step 4 — Produce a decision document
After the final thought:
- **Decision**: 1-2 sentence verdict
- **Rationale**: 3-5 bullets
- **Alternatives rejected** with one-line reason each
- **Open questions** that need user input

Do not write code. End with: "Want me to implement this? (yes / revise / cancel)"
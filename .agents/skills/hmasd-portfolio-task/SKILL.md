---
name: hmasd-portfolio-task
description: Use when Root is comparing or changing HMASD direction priority, lifecycle, capacity, fusion, separation, or the next research investment.
---

# HMASD Portfolio Decisions

## Core principle

Choose the smallest investment that can change a direction decision without confusing scientific
value with execution convenience.

## Persistent Pro decision node

Before changing direction priority, capacity, lifecycle, fusion, separation, registering a new
direction, or selecting the next cross-direction investment, Root must use
`$hmasd-pro-research-prompt-author` with `workflow_node=portfolio_decision`. Every packet binds to
the single persistent conversation key `portfolio:cross_direction`, lists every direction in scope,
and includes the current Portfolio snapshot plus the exact direction/evidence paths needed for the
decision. The fixed Transport task creates the provider conversation on first use and reuses its
exact conversation ID for all later Portfolio rounds.

A complete archived Pro response is the final Portfolio decision. Root executes it, records its
evidence and bounded rationale in `PORTFOLIO.md`, and performs integration; Root does not replace or
override it with a local-model judgment. If Pro reports missing connector access or insufficient
evidence, or Transport has not archived a complete response, no Portfolio decision exists. Root may
continue reversible evidence collection but must not make the pending material Portfolio change.

Read `docs/research/portfolio/PORTFOLIO.md` for current state and the relevant `DIRECTION.md` files
for scientific authority. Compare claim ceiling, decision relevance, complementarity, substitution,
reversibility, cost, live external effects, and the smallest discriminating observation.

Transport, implementation, and process status may change sequencing or feasibility; they do not by
themselves determine scientific polarity or lifecycle. Preserve uncertainty and state why the
recommended action would change under a contrary result.

Root records and integrates the final Pro decision in `PORTFOLIO.md`. Outside the Prompt Author and
Transport packet boundary, use ordinary language; no additional response schema is required.

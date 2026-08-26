---
name: hmasd-portfolio-control
description: Use when Portfolio must make and return one bounded HMASD cross-direction decision.
---

# HMASD Portfolio Control

Validate the inbound packet and cited `PORTFOLIO.md`, registry revision, and
direction results. Portfolio owns only cross-direction priority, lifecycle, and
engineering investment.

Write the decision/reasoning in existing Portfolio authority and apply registry
changes through `scripts/hmasd_state.py` with writer `Portfolio` and
expected-revision CAS. Then return via `hmasd-slice-interface`, using fresh
typed refs. A follow-on direction must be explicit in the complete draft.

Do not dispatch/create/wait native tasks, infer a direction from prose, or wake
Clerk for normal continuation. Observe unknown Effects and report their exact
scope.

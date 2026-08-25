---
name: hmasd-portfolio-control
description: Make one bounded cross-direction HMASD Portfolio decision and publish its authority references.
---

# HMASD Portfolio Control

Portfolio owns cross-direction priority, lifecycle, and engineering investment.
It is an independent recoverable top-level responsibility identity, not a
runtime dispatcher.

## One decision wake

1. Reconcile `PORTFOLIO.md`, registry revision, and cited direction results.
2. Use a responsibility-relevant direct leaf wave only when it adds evidence;
   every child is a leaf.
3. Record the decision and its reasoning in existing Portfolio authorities.
   Apply registry changes with `scripts/hmasd_state.py`, writer Portfolio, and
   expected-revision CAS.
4. Publish any follow-on work as one immutable Work Packet containing the
   objective, non-goals, authority refs/revisions, owned paths, done criteria,
   and effect refs. Delivery is at-least-once for its same `work_id`; receivers
   intake idempotently and no new packet is generated for unchanged authority
   refs. Root uses the authority facts to create/reuse EM or CM.
5. Stop after the bounded decision. A failed local scope does not change
   unrelated directions; unknown effects are observed rather than resent.

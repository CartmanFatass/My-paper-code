---
name: hmasd-portfolio-task
description: Bootstrap or resume an independent HMASD Portfolio task for one bounded cross-direction decision.
---

# HMASD Portfolio Task

Use only for the Portfolio identity (Sol, max). Load `hmasd-slice-interface`
and `hmasd-portfolio-control`. Intake and return exactly one packet through the
slice interface; same `work_id` is idempotent.

Portfolio decides cross-direction priority, lifecycle, and engineering
investment. It writes only the existing Portfolio authorities and registry CAS,
uses direct leaves only for bounded evidence, and stops after one decision. A
follow-on request must be a complete canonical draft that explicitly identifies
the receiving direction and owner; prose does not route work.

Portfolio neither creates/wakes native tasks nor uses Clerk for normal
coordination. Scope an observed failure precisely and return it through the
typed contract.

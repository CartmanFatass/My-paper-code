---
name: hmasd-review-round
description: Use only by the active HMASD controller for one tracked scientific review round. It creates and pushes one Open-Pro divergent question, dispatches the registered Open-Pro Exchange through $hmasd-task-router, archives the returned raw, writes factual reconciliation, and sends the evidence to the Research Project Manager for scientific convergence and a code-ready next source or stop.
---

# HMASD Review Round

## Scope

This is a controller workflow, not a persistent role. The controller owns round
files, Git-visible boundaries, Open-Pro dispatch, raw acceptance, factual
reconciliation, adoption and project-state update. It never operates the
browser and never performs scientific convergence itself.

Read the router, role directory, this Skill,
`docs/external-review/REVIEWER_CONVERSATIONS.json`, the named round and its
explicit evidence.

## Scientific roles

- Open Pro independently expands and attacks two to four causal explanations
  under `docs/project/ALGORITHM_PRINCIPLES.md` and
  `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`. It does not choose one
  successor.
- The Research Project Manager reads the Open raw, factual reconciliation,
  project scientific principles and its convergence reference. It validates
  evidence, weights the portfolio and freezes one code-ready next source or
  stop.
- The controller adopts or rejects the manager brief, authorizes later work and
  owns Git and user communication.

## Round boundary

Use:

```text
docs/external-review/rounds/<round>/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_EVIDENCE_RECONCILIATION.md
  50_DISPOSITION.md
```

Before dispatch, commit and push the brief, manifest and Open question. Run
`scripts/verify_pro_review_boundary.ps1` with the 40-character pushed SHA and
question path. The question must list the base and Open scientific principles
and every exact Git-visible evidence path.

## Procedure

1. Dispatch one `REVIEW_STAGE` to the registered
   `open_divergent_exchange` with explicit `$hmasd-task-router` and
   `$hmasd-review-exchange` activation.
2. Accept the raw only from that registered task and preserve its semantic
   quality note separately from transport validity.
3. Write `30_EVIDENCE_RECONCILIATION.md` as a factual provenance and
   contradiction record without selecting a route.
4. Send one `SCIENTIFIC_CONVERGENCE_TASK` to the registered
   `research_project_manager`, explicitly listing the round brief, raw,
   reconciliation and required evidence.
5. Show the returned Chinese user brief. `ADOPT` or `STOP` permits the controller
   to write `50_DISPOSITION.md`, commit/push it and update project control once.
   `BLOCK` pauses the round at the exact missing evidence or authority boundary.

The manager is the convergence authority. It must make the needed scientific
choices itself rather than returning a field-completion loop. The tracked round
contains one external divergent stage followed by internal convergence.

## Exchange dispatch

```text
$hmasd-task-router
$hmasd-review-exchange

REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
reviewer_role=OPEN_DIVERGENT
round=<id>
stage_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<id>
question=docs/external-review/rounds/<id>/20_PRO_OPEN_QUESTION.md
raw=docs/external-review/rounds/<id>/21_PRO_OPEN_RAW.md
completion_policy=ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY
```

Resolve the registered Exchange immediately before sending, copy its live route
fields unchanged, require delivery proof and verify post-send invariance.

## Manager dispatch

```text
$hmasd-task-router
$hmasd-project-manager

SCIENTIFIC_CONVERGENCE_TASK
role_skill=.agents/skills/hmasd-project-manager/SKILL.md
review_id=<round>:scientific-convergence
inputs=<explicit brief, raw, reconciliation and evidence paths>
question=Validate the evidence, preserve a weighted portfolio, and freeze one code-ready next evidence source or stop.
```

This is read-only and creates no write lease or heartbeat.

## Recovery

There is no review state file and no controller heartbeat. Derive progress from
immutable artifacts and callbacks. On Exchange transport error, return the same
stage to the same session with observed evidence and one semantic recovery
objective. Do not prescribe selectors, clicks or browser commands.

A naturally completed raw with content gaps is valid transport. The Research
Project Manager may still synthesize it using its assigned evidence; do not
resubmit merely to obtain preferred prose. External review and internal
convergence never authorize implementation or compute by themselves.

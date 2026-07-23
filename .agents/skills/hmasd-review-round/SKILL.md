---
name: hmasd-review-round
description: Use when a tracked HMASD external GPT-5.6 Pro decision or clarification package must cross the Project Manager, Controller, and registered Exchange boundary.
---

# HMASD External Pro Research Round

## Scope

External GPT-5.6 Pro is the scientific decision source. It owns conjecture and
definition correction, derivation, counterexample search, retained lemmas,
portfolio meaning and selection of one scheduled research action. That action
serializes resources; it does not make other defensible explanations illegal.

Project Manager is the semantic author of reviewer-visible briefs, manifests and
questions, including concrete scientific gaps that block code-side work. It
does not decide those gaps. External Pro remains the scientific authority.
Controller owns only mechanical validation, reviewer-visible Git boundaries,
routing, resource authorization and user communication. It never rewrites PM
content, operates the browser, replaces Pro judgment or designs the executable
algorithm.

Use a full plural review for competing explanations, proposed family
retirement, benchmark-identification disputes, repeated ambiguity or
full-algorithm integration. Use a focused continuation in the same registered
Pro conversation for a local scientific ambiguity or correction. Both use the
same exact evidence and raw-archive discipline.

## Round boundary

```text
docs/external-review/rounds/<round>/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_PM_CODE_SIDE_RECONCILIATION.md
  50_MECHANICAL_INTAKE_RECORD.md
```

Before dispatch, commit and push the brief, manifest and question. Run
`scripts/verify_pro_review_boundary.ps1` with the 40-character pushed SHA and
question path. List the scientific principles and every exact Git-visible
evidence path.

Every newly authored package contains these exact declarations in its brief and
question:

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_code_side
scientific_authority=external_pro
```

Reviewer-visible PM artifacts are admissible evidence only with those markers.
Internal manager audits, callbacks, scratch notes and work logs remain forbidden.

The question asks Pro to return:

- plural live conjectures and their scopes;
- derived intervention, natural and held-out consequences;
- concrete counterexamples and retained lemmas;
- the smallest refuted unit in existing evidence;
- one scheduled research action chosen by information gain, cost and
  reversibility;
- evidence semantics to freeze if that action is adopted;
- reactivation conditions for unscheduled ideas;
- a concise Chinese user brief.

Pro must not equate one scheduled action with one legal successor or write an
implementation plan. If implementation is selected, it defines the scientific
object and estimand; the Manager later freezes executable architecture.

## Procedure

1. Assign Project Manager the round path and scientific evidence boundary. It
   authors and, after validation feedback, repairs the complete reviewer-visible
   package under its code-side write lease.
2. Controller mechanically verifies author markers, required fields, source and
   path provenance, forbidden internal references and Git visibility. It then
   commits and pushes the exact PM-authored files unchanged.
3. Dispatch one `REVIEW_STAGE` to `open_divergent_exchange` with explicit
   `$hmasd-dispatch-task` and `$hmasd-review-exchange` activation.
4. Accept a naturally completed raw only from that task. Preserve semantic
   quality notes separately from transport validity.
5. Return the exact raw to Project Manager. PM authors
   `30_PM_CODE_SIDE_RECONCILIATION.md` and any durable implementation artifacts.
   Scientific deltas must be exact Pro content, not a local convergence pass.
6. Controller may write only `50_MECHANICAL_INTAKE_RECORD.md`: hashes, source,
   transport status, authority markers and whether the process is eligible for
   routing. It contains no scientific or engineering interpretation. Show the
   exact Pro Chinese brief. A material
   scientific ambiguity returns as one focused continuation to the same Pro.
7. If Pro selected implementation, send its exact direction and estimand to a
   separately authorized Project Manager task. Review and intake alone
   authorize neither implementation nor compute.

At every validation failure the callback carries
`repair_owner=project_manager`. Controller forwards the failure evidence and
does not alter package semantics.

External Pro raw is the only scientific disposition authority. Project Manager
owns code-side reconciliation. Controller has no reconciliation or disposition
authorship, even when an older round used those filenames.

## Exchange dispatch

```text
$hmasd-dispatch-task
$hmasd-review-exchange

REVIEW_STAGE
skill=$hmasd-review-exchange
reviewer_role=OPEN_DIVERGENT
round=<id>
stage_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<id>
question=docs/external-review/rounds/<id>/20_PRO_OPEN_QUESTION.md
raw=docs/external-review/rounds/<id>/21_PRO_OPEN_RAW.md
completion_policy=ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY
```

Resolve the Exchange immediately before sending, copy its live route fields
unchanged, require delivery proof and verify post-send invariance.

## Controller mechanical intake

Verify the archived raw, hashes, source commit, paths, role identity and exact
delivery. Preserve the Pro decision without a second scientific convergence
step. Integrate only exact Pro-authored scientific deltas and exact PM-authored
code-side files.

There is no Controller semantic relay. A read-only scout may perform a bounded
mechanical comparison but owns no scientific, engineering or adoption authority.

When a later resource action is authorized, dispatch the registered Project
Manager with the archived Pro direction, estimand, resource boundary, working
scope and completion contract. The
Project Manager—not the Controller—freezes the executable algorithm.

## Recovery

There is no review state file or Controller heartbeat. A naturally completed
raw with gaps remains valid transport. If exact Pro text leaves a scientific
question open, Project Manager may author one focused question without deciding
it; if it is algorithm-realization-only, Project Manager resolves it inside its
assignment. Never prescribe selectors,
clicks or browser commands. Review and mechanical evidence intake never authorize
implementation or compute by themselves.

Treat a transient transport failure, timeout or `waitingOnApproval` as an active
handoff. The Exchange owns bounded self-recovery and reports each
`RECOVERY_ATTEMPT`; the Controller continues the same handoff while a safe
in-scope recovery remains. Accept `REVIEW_STAGE_BLOCKED` only when it records
the attempted recoveries, the remaining direct cause and
`recovery_exhausted=true`. A non-exhausted failure report is a recovery update,
not a terminal review disposition.

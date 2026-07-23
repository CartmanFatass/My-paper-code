# HMASD External Review Workflow

This file describes the external-review artifact sequence, browser transport
and round layout. Canonical role authority, package acceptance and validation
boundaries are defined only in root `AGENTS.md` and the applicable
`.agents/roles/*.md` contracts. This README is not a role constitution.

## Scientific sequence

1. GPT-5.6 Pro returns question-scoped scientific analysis and recommendations
   from the Git-visible evidence under `OPEN_REVIEW_PRINCIPLES.md`, preserving
   plural conjectures inside the submitted question.
2. Project Manager selects and schedules the next workflow action after exact
   raw intake and reconciliation.
3. An accepted Project-Manager-authored brief, manifest and question are
   transmitted unchanged from the declared Git commit and exact paths.
4. The exact natural response is archived, mechanical intake is written, the
   heartbeat is deleted, and the raw returns to Project Manager without a
   scientific quality classification.
5. Exact Pro content is reconciled with the code-side gap, producing any needed
   focused follow-up or executable package under the canonical role contracts.
6. The exact accepted PM/Pro artifacts are integrated and project control is
   updated once; no second intake record is written.

Review and mechanical intake do not authorize code or training. The target
remains a stronger MARL algorithm, while hierarchy, skills, variable lifetime,
ordinary-MARL controls and causal diagnostics are mechanisms or evidence, not
universal prerequisites.

`docs/project/ALGORITHM_PRINCIPLES.md` is the common scientific contract and
`OPEN_REVIEW_PRINCIPLES.md` structures the scientific response; neither defines
role authority. Direct intake guidance lives in the Controller
`hmasd-review-round` Skill.

## Controller-direct interface

Project Manager prepares each immutable reviewer-visible boundary. Controller
commits and pushes it after mechanical checks, loads `$hmasd-review-round` and
`$browser:control-in-app-browser`, and opens the registered conversation from
`REVIEWER_CONVERSATIONS.json`.

```text
CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=aggressive
round=<round-id>
stage_commit=<40-character pushed SHA>
question=docs/external-review/rounds/<round-id>/20_PRO_OPEN_QUESTION.md
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.
```

Controller inspects existing visible user turns first. A matching accepted
assignment is resumed and never resubmitted. Absence must be proven before the
single allowed submission. While pending, the Controller owns one five-minute
heartbeat that inspects only; it never submits.

A redirect to the signed-in home page starts registered-conversation discovery,
not a block. If the registered URL opens with a composer but an empty message
pane, Controller reloads that tab once before using conversation search. A
`Thinking` label is only descriptive: active generation requires changing
message text or an active control such as `Stop answering`; completion requires
two stable snapshots at least three seconds apart and no retry/error/continue
control.

If a completed assistant message explicitly reports that listed repository
evidence was unavailable, it is a transport diagnostic and is not written to
`21_PRO_OPEN_RAW.md`. Controller takes the allow-list only from the question,
materializes exactly those paths from `stage_commit` rather than the current
working tree, verifies the path-preserving archive has no extras, and attaches
it in the same registered conversation. This is one mechanical continuation
under the existing fence, never a second freshness submission. The stable
assistant response after that continuation is the raw candidate.
The archive is built by
`.agents/skills/hmasd-review-round/scripts/build_review_evidence_archive.ps1`;
manual working-tree packaging is not an admissible fallback.

Each raw has exactly one writer: the active Controller. A raw becomes immutable
after natural completion and exact captured-text equality are verified by
rereading it. Controller records only transport facts. Exact raw then returns
to Project Manager, which alone decides whether its code-side gap needs a
focused follow-up. A content gap is not a transport failure.

There is no intermediate persistent review task and no cross-task completion
callback. A retired task's late output has no authority. The Controller deletes
its heartbeat after terminal raw archival or an exhausted terminal block.

## Round files

New review work lives under one round directory:

```text
rounds/YYYYMMDD_topic/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_PM_CODE_SIDE_RECONCILIATION.md
  50_MECHANICAL_INTAKE_RECORD.md
```

Raw responses are byte-preserved and precede downstream use. Controller round
behavior lives in `$hmasd-review-round`; algorithm realization, package repair
and code-side reconciliation live with the registered `project_manager` role.
Persistent task IDs contain only Controller and Project Manager in the
dispatcher's role registry. Experiment monitoring is a nonpersistent Controller
procedure. External reviewer conversation IDs and URLs live only in
`REVIEWER_CONVERSATIONS.json`.

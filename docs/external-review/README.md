# HMASD External Review Workflow

External GPT-5.6 Pro owns scientific CDC direction. The active Controller owns
round sequencing, mechanical provenance, direct browser transport, exact raw
archival, heartbeat lifecycle, resource authorization and every Git-visible
boundary. The native Codex Project Manager owns every reviewer-visible
code-side package, reconciliation and executable algorithm realization. It does
not select protected science; external Pro remains the only scientific
authority.

```text
pm_acceptance_authority=exclusive
controller_validation_authority=none
```

Project Manager self-validates technical content and package readiness.
Controller performs no technical or algorithmic validation; it checks only
route/source identity, exact hashes/paths and Git transport.

## Scientific sequence

1. GPT-5.6 Pro performs CDC scientific review of the Git-visible evidence under
   `OPEN_REVIEW_PRINCIPLES.md`, preserving plural conjectures while selecting
   one scheduled research action.
2. Project Manager authors, reviews, repairs and accepts the reviewer-visible
   brief, manifest and question. Controller transmits those accepted files
   unchanged after non-discretionary identity/hash/path checks.
3. Controller archives the exact natural response, writes mechanical intake,
   deletes its heartbeat, and returns the raw to Project Manager without a
   scientific quality classification.
4. Project Manager reconciles exact Pro content with its code-side gap and
   authors any focused follow-up or executable package.
5. Controller integrates the exact PM/Pro artifacts and updates project control
   once; it does not write a second intake record.

Review and mechanical intake do not authorize code or training. Pro owns
science; Project Manager owns code-side semantics; Controller owns transport,
workflow and the resource gate. The target remains a stronger MARL algorithm,
while hierarchy, skills, variable lifetime, ordinary-MARL controls and causal
diagnostics are mechanisms or evidence, not universal prerequisites.

`docs/project/ALGORITHM_PRINCIPLES.md` is the common scientific contract and
`OPEN_REVIEW_PRINCIPLES.md` specializes the external Pro role. Direct intake
guidance lives in the Controller `hmasd-review-round` Skill.

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
Persistent task IDs contain only Controller, Project Manager and Experiment
Monitor in the dispatcher's role registry. External reviewer conversation IDs
and URLs live only in `REVIEWER_CONVERSATIONS.json`.

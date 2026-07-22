---
name: hmasd-dispatch-task
description: Route HMASD work using the execution mode selected in CURRENT_WORK.md. Never dispatch OMP when that active boundary pauses it.
---

# HMASD Task Dispatch

## Purpose

Choose the execution surface and deliver one bounded assignment. This Skill
grants no scientific, algorithm, implementation, experiment, Git or
project-control authority by itself.

## Mandatory execution-mode check

Read `docs/project/CURRENT_WORK.md` before selecting a surface. Its active
execution mode is authoritative.

When it says `OMP: PAUSED`:

- do not start, resume, inspect through, or send assignments to OMP;
- do not interpret an old OMP task, worktree or transcript as an active lease;
- use Controller-direct work or native Codex collaboration agents for bounded
  implementation and verification;
- keep any OMP-produced WIP isolated until the Controller explicitly audits
  and migrates it;
- retain the registered Open-Pro Exchange route unless separately paused.

The OMP sections below apply only when `CURRENT_WORK.md` explicitly says
`OMP: ACTIVE`.

The Controller owns continuation: every accepted OMP task result or persistent
role callback is a wake-up. Integrate the evidence, update control state only at
a real boundary and continue the next already authorized event. Do not stop at a
task boundary when an active grant still determines the next action.

## Select the execution surface

Classify the requested outcome before any delivery:

- Controller direct control-plane work: workflow and topology design, routing,
  Git, direct external-Pro evidence intake, durable record application, evidence
  integration, project control and user communication.
- Native OMP `hmasd-project-manager`: one Controller-authorized algorithm
  realization and implementation package inside an external-Pro scientific
  direction. Dispatch with `isolated: true`.
- Native OMP `hmasd-experiment-monitor`: one already authorized run. Use exact
  stable task name `monitor-<run-id>` and do not isolate it from the run root or
  shared `hub` process.
- Persistent `open_divergent_exchange`: external GPT-5.6 Pro transport through
  the registered conversation and `hmasd-review-exchange` Skill.

The only persistent edge is:

```text
controller <-> open_divergent_exchange
```

Code Scout, Implementer, Verifier and Reviewer belong only to the Project
Manager's child task graph. The Controller does not dispatch them as writers.

## Native OMP Project Manager delivery

Require one complete assignment with:

```text
PROJECT_MANAGER_ASSIGNMENT
work_id=<stable id>
source_commit=<40-character pushed SHA>
scientific_direction=<external Pro decision and estimand>
inputs=<raw, reconciliation and exact evidence paths>
authority=<resource and protected algorithm realization authority>
working_scope=<exact project paths>
protected_boundaries=<semantics to preserve or decide>
forbidden=<scientific direction, compute, Git, review and control exclusions>
completion=<observable package and focused checks>
```

Dispatch exact profile `hmasd-project-manager`, stable name derived from
`work_id`, and `isolated: true`. Its queued or running job is the sole write
lease. The Controller does not mutate, stage, commit or push until that job
returns ready/blocked or is definitely aborted.

Project Manager may send a non-blocking plan brief through `hub`. Its terminal
value arrives by automatic result delivery. Read full output at `agent://<id>`
and transcript at `history://<id>`. Never resolve a persistent route or send a
session callback for an OMP task.

## Native OMP Monitor delivery

Require a valid run manifest and an already authorized named persistent `hub`
process. Dispatch exact profile `hmasd-experiment-monitor`, exact name
`monitor-<run-id>`, and `isolated: false`.

A root OMP restart may rebuild the same Monitor only when no matching job
exists and its terminal idempotency key has not already been accepted. A
nonterminal replacement resumes bounded observation; an already-terminal
replacement reads retained status and returns the same terminal payload.
Automatic result delivery is the only callback. Accept terminal results
idempotently by the manifest's run ID, terminal state and status update
identity. A Monitor abort never restarts or changes the experiment.

## Persistent Open-Pro delivery

Immediately before every outbound persistent send, read
`references/session-roles.json`. Require the recipient task ID and role Skill
to match the active `open_divergent_exchange` entry. Static registry data never
supplies `hostId`, model or thinking.

Resolve the registered Exchange with
`scripts/resolve_task_route.ps1 -ThreadId <registered id>`. Require one
unarchived task and nonempty `hostId`, `threadId`, `model` and `thinking`. Copy
all four unchanged into one send. Delivery succeeds only when the returned
`threadId` matches the registered recipient.

Resolve the same task again immediately after delivery and require all four
fields to match the pre-send values. On change, do not resend or repair task
settings; report route corruption. A definite pre-acceptance `notLoaded` permits
one identical retry; an accepted or ambiguous send is never repeated.

Accept only these terminal callback events:

```text
REVIEW_STAGE_COMPLETE
source_thread_id=<registered open_divergent_exchange thread ID>
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
role=OPEN_DIVERGENT
handoff_id=<round>:OPEN_DIVERGENT:complete:<question>
round=<id>
stage_commit=<40-character pushed SHA>
raw=<round_path>/<raw>
verification=natural_complete;exact_text_equal
quality=<COMPLETE|COMPLETE_WITH_GAPS>
quality_notes=<concise semantic observation or none>

REVIEW_STAGE_BLOCKED
source_thread_id=<registered open_divergent_exchange thread ID>
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
role=OPEN_DIVERGENT
handoff_id=<round>:OPEN_DIVERGENT:blocked:<question>
round=<id>
reason=<direct operational blocker>
```

Immediately before acceptance, reread the registry. Require the callback
recipient to match the registered Controller task ID and `AGENTS.md` contract,
and require `source_thread_id`, `role_skill` and `role` to match the registered
Exchange. The event, handoff ID and legal
`controller <-> open_divergent_exchange` edge must match. Repeated source role
plus handoff ID is one idempotent delivery.

## Context and authority

Assignments state outcome, authority, inputs, write scope, hard exclusions,
completion and return semantics. They do not forward conversation history.
Project Manager owns in-scope algorithm realization; Monitor owns bounded
observation; Exchange owns transport. None receives Controller Git, project
control, formal-compute or user-communication authority.

OMP task agents do not invoke persistent role Skills or read the session
registry. The persistent Exchange does not spawn OMP tasks. Completion of any
surface never starts a successor directly; automatic result delivery wakes the
Controller, whose controller continuation duty selects the next authorized
surface.

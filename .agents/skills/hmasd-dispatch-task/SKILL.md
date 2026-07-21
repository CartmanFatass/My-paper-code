---
name: hmasd-dispatch-task
description: Automatically use for every HMASD controller task that may require direct execution, persistent-role dispatch, delegation, external review, or experiment monitoring, and for every persistent-session callback. Select the authorized execution surface, then resolve and deliver persistent messages without changing the recipient model or thinking. Do not use for temporary subagent communication.
---

# HMASD Task Dispatch

## Purpose

Choose who owns a task and safely deliver it. This Skill grants no research,
implementation, review, experiment, Git, or project-state authority.

## Select the execution surface

For controller work, classify the requested outcome before using any delegation
tool:

- ordinary inspection, project management, Git, evidence integration, user
  communication, or a small direct controller edit -> controller works directly;
- scientific convergence or controller-authorized implementation management ->
  registered `research_project_manager` with `$hmasd-project-manager`;
- external divergent review -> registered `open_divergent_exchange` with
  `$hmasd-review-exchange`;
- monitoring an already authorized run -> registered `experiment_monitor` with
  `$hmasd-experiment`.

Temporary implementation and review subagents belong only to the Research
Project Manager and use native parent-child communication. Their existence does
not create a controller execution surface.

If the controller works directly, stop dispatch classification and do not call
a persistent-session or subagent delivery tool. If a persistent role owns the
task, continue below.

## Role registry

Read `references/session-roles.json` immediately before every persistent send
or callback. Require the recipient task ID and role Skill to match one active
entry. The registry stores stable task IDs only; never take live route fields
from it, conversation history, an incoming message, or cached context.

The only persistent edges are:

```text
controller <-> research_project_manager
controller <-> open_divergent_exchange
controller <-> experiment_monitor
```

## Explicit message envelope

Every persistent message begins with:

```text
$hmasd-dispatch-task
```

A controller assignment names exactly one destination role Skill on the next
line. A callback to the controller names only this Skill. Use the destination
Skill's compact schema or:

```text
$hmasd-dispatch-task
$<destination-role-skill>

HMASD_SESSION_TASK
task_id=<stable id>
role=<registered role>
role_skill=<registered Skill path>
objective=<bounded outcome>
authority=<allowed mutations or read-only>
inputs=<explicit paths or none>
write_scope=<explicit paths or none>
forbidden=<explicit exclusions>
completion=<observable condition>
return=<terminal callback>
```

Conversation history and nearby files are not implicit inputs.

## Resolve and deliver

Immediately before sending, run:

```text
scripts/resolve_task_route.ps1 -ThreadId <registered recipient id>
```

Require one unarchived task and nonempty `hostId`, `threadId`, `model`, and
`thinking`. Copy all four values unchanged into one `send_message_to_thread`
call. Delivery succeeds only when the tool returns the same recipient
`threadId`.

Resolve the same task again immediately after delivery and require all four
fields to match the pre-send values. On change, do not resend or repair task
settings; report `TASK_ROUTE_CORRUPTION` with before/after evidence. A definite
pre-acceptance `notLoaded` permits one identical retry; an accepted or ambiguous
send is never repeated.

Before a callback, resolve the controller anew. Never reuse incoming route
metadata.

## Callback acceptance

Accept a callback only when it explicitly activates this Skill, its native
`source_thread_id` equals the registered role task, its stable `handoff_id`
matches the assignment, and the sender/receiver form one legal edge. Repeated
role plus `handoff_id` is one idempotent delivery.

## Recovery and topology

Let the owning role diagnose recoverable failures inside its authority. A retry
returns the same bounded assignment to the same role with observed evidence and
the desired outcome; do not prescribe internal mechanical steps.

For a persistent topology change, run `scripts/audit_session_topology.ps1`,
update the registry, affected role Skills, prompts, heartbeat callbacks, helper
scripts and contract tests in one Git boundary, and do not message an affected
session during a partial migration.

---
name: hmasd-task-router
description: Mandatory communication-only Skill for every persistent HMASD Codex session. Use before every message to an existing session and every expected callback. Never use it for temporary subagents. Resolve the recipient's live delivery metadata, carry one minimal session-role assignment, and require tool-level delivery proof without selecting or changing any model, role, workflow, or project decision.
---

# HMASD Task Router

## Scope

Own persistent-session communication only. Never use this Skill for a temporary
subagent or native subagent messaging. This Skill by itself grants no authority
to read project-control documents, interpret the task, choose a role, operate a
role tool, create a task, or authorize work. It does not revoke context
separately granted by active-controller status or by the one assigned role
Skill.

Every delegated persistent session receives this Skill and exactly one
session-role Skill. Reject an assignment that names zero or multiple role
Skills with `TASK_BLOCKED` before doing role work.

## Session and Role Directory

Read `references/session-roles.json` before any persistent-session send or
callback acceptance. It is the only communication registry for the controller,
External Review Manager, three reviewer-exchange sessions, and Experiment
Monitor session IDs and their one-to-one role bindings. Other role registries
must not duplicate Codex session IDs.

The active controller alone maintains this directory. Change an entry only for
an explicit controller handoff or explicit persistent-session replacement.
Before accepting a replacement, require a unique unarchived session, bind it to
exactly one role and role Skill, and remove the prior binding in the same Git
change. Never infer a role from a task title, model, conversation history, or
message prose. Never store `hostId`, `model`, or `thinking` in the directory.

A persistent role session must verify that its current task ID equals the
directory entry for its declared role and that the assignment's `role_skill`
equals the registered role Skill. Otherwise return `TASK_BLOCKED` without role
work. A null or `UNASSIGNED` directory entry is not a routable destination and
must not be replaced by another role session.

## Assignment Envelope

Send a self-contained envelope:

```text
HMASD_SESSION_TASK
task_id=<stable id>
role=<one role>
role_skill=<one .agents/skills/.../SKILL.md path>
objective=<one bounded outcome>
authority=<allowed mutations or read-only>
inputs=<explicit paths or none>
write_scope=<explicit paths or none>
forbidden=<explicit exclusions>
completion=<observable condition>
return=<terminal message contract>
```

The recipient reads this Skill, the named role Skill, and only the inputs that
those two sources allow. Conversation history, nearby files, registries, and
earlier assignments are not implicit inputs. A missing or conflicting field
returns `TASK_BLOCKED task_id=<id> reason=<exact reason>` through this Skill.

Role-specific lifecycle messages such as `START_REVIEW` or
`MONITOR_ASSIGNMENT` may use their role Skill's compact schema instead of the
generic envelope. Every compact message must still contain exactly one
`role_skill=<path>` field and grants no implied context.

## Resolve the Recipient Live

Immediately before a send, run:

```text
scripts/resolve_task_route.ps1 -ThreadId <recipient-id>
```

Require one unarchived task with nonempty `hostId`, `threadId`, `model`, and
`thinking`. Registries store stable task IDs only. Never infer live metadata
from the sender, a title, an old message, a heartbeat, a registry, or a project
document.

If the registered session is archived, send nothing. The active controller may
unarchive that same session as a separate lifecycle action and then resolve it
again; never create or substitute a replacement session implicitly.

Copy the recipient's current values unchanged into `send_message_to_thread`:

```text
hostId=<live recipient hostId>
threadId=<live recipient threadId>
model=<live recipient model>
thinking=<live recipient thinking>
prompt=<assignment or callback>
```

These are read-only delivery arguments. Never compare them with expected
values, synchronize tasks, select a preferred route, or change a task setting.

## Delivery Proof

Send once. Delivery succeeds only when the tool result identifies the same
recipient `threadId` resolved immediately before the call. Commentary, a final
response in the sender task, heartbeat text, or delegation metadata is not
delivery.

A definite pre-acceptance `notLoaded` error permits one identical retry after
loading the same target. An accepted or ambiguous send is never repeated. If a
required callback cannot obtain delivery proof, the sender follows its role
Skill by keeping its own heartbeat active and retrying only the same stable
`handoff_id`.

Before replying, resolve the reply destination again as the new recipient.
Never reuse route metadata carried by the incoming message.

## Controller Send Contract

For every controller-to-session assignment:

1. select the declared role in `references/session-roles.json`;
2. require its registered role Skill to equal the assignment's `role_skill`;
3. take the recipient `thread_id` only from that role entry;
4. resolve that ID immediately before delivery;
5. copy the returned `hostId`, `threadId`, `model`, and `thinking` unchanged into
   one `send_message_to_thread` call;
6. accept delivery only when the tool returns the same recipient `threadId`.

Do not send to an ID supplied in free-form task text, reuse cached live metadata,
compare against a preferred model, or mutate either session's model or thinking.
The controller records no waiting state and does not manage a role session's
heartbeat.

## External Review Topology

Enforce this exact communication graph:

```text
controller <-> external_review_manager
external_review_manager <-> gemini_divergent_exchange
external_review_manager <-> open_divergent_exchange
external_review_manager <-> convergent_exchange
```

The controller sends `START_REVIEW` only to `external_review_manager` and never
sends a reviewer-stage assignment. The manager sends `REVIEW_STAGE` only to the
single exchange whose registered `reviewer_role` matches that assignment. A
reviewer exchange returns `REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED` only
to the manager. The manager alone returns `REVIEW_COMPLETE` or
`REVIEW_BLOCKED` to the controller. Reject controller-to-reviewer,
reviewer-to-controller, reviewer-to-reviewer, and reviewer-to-monitor sends.

For a manager-to-exchange send, apply the same live-resolution and unchanged
`hostId`/`threadId`/`model`/`thinking` rules as the Controller Send Contract.
The manager takes the recipient ID only from the role directory and accepts
delivery only when the tool returns that same exchange `threadId`.

## Receive Contract

Accept a persistent-session callback only when all of these are true:

- the native delegation metadata `source_thread_id` equals the session ID in
  `references/session-roles.json` for the declared role;
- the payload contains that role's stable `handoff_id`;
- the payload matches the exact terminal schema in the named role Skill.

Also require the sender and receiver pair to be an edge in the External Review
Topology or the registered experiment-monitor-to-controller edge. A valid
payload on an invalid edge is rejected without forwarding.

Reject a callback whose source task, role, or schema does not match. Never infer
the sender from prose inside the payload. Receipt grants no new project,
scientific, experiment, or Git authority.

Treat a repeated callback with the same role and `handoff_id` as the same
delivery. A duplicate may confirm receipt but must not repeat project updates,
launch a successor, or produce a second scientific interpretation. This
idempotency is the recovery path when a role session delivered successfully but
stopped before deleting its own heartbeat; do not add a separate relay state
machine.

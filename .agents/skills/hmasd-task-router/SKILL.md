---
name: hmasd-task-router
description: Mandatory communication-only Skill for every persistent HMASD Codex session and for active-controller maintenance of the persistent-session topology. Use before every persistent-session message or callback and for every role, edge, callback or session-binding change. Resolve the recipient live, preserve its model and thinking fields unchanged, prove delivery and post-send invariance, and never route temporary subagents.
---

# HMASD Task Router

## Scope

Own persistent-session identity and delivery only. Grant no research,
implementation, review, experiment, Git or project-state authority. Temporary
subagents use native parent-child collaboration and never use this Skill.

## Role directory

Read `references/session-roles.json` before every persistent send or callback.
It is the only registry for the controller, Research Project Manager, Open-Pro
Exchange and Experiment Monitor. Store stable task IDs and role Skills only;
never store `hostId`, `model` or `thinking`.

Require the recipient task ID and `role_skill` to match one active registry
entry. Never infer identity from title, model, history or message prose.

## Explicit activation and envelope

Every persistent message begins with:

```text
$hmasd-task-router
```

A controller assignment names exactly one destination role Skill on the next
line. A callback to the controller names only the router. A `role_skill=` field
or path is routing data, not Skill activation.

Use either the destination Skill's compact schema or:

```text
$hmasd-task-router
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

Reject missing or conflicting fields with one routed blocker. Conversation
history and nearby files are never implicit inputs.

## Resolve the recipient live

Immediately before sending, run:

```text
scripts/resolve_task_route.ps1 -ThreadId <registered recipient id>
```

Require one unarchived task and nonempty `hostId`, `threadId`, `model` and
`thinking`. Copy all four values unchanged into one
`send_message_to_thread` call. Delivery succeeds only when the tool returns the
same recipient `threadId`.

### Post-send invariance

Resolve the same task again immediately after delivery. Require all four fields
to equal the pre-send values. On change, do not resend or repair settings;
return `TASK_ROUTE_CORRUPTION` with before/after evidence.

Before a callback, resolve the controller anew. Never reuse incoming or cached
route metadata. A definite pre-acceptance `notLoaded` error permits one identical
retry; an accepted or ambiguous send is never repeated.

## Active topology

Only these persistent edges are legal:

```text
controller <-> open_divergent_exchange
controller <-> research_project_manager
controller <-> experiment_monitor
```

- The controller sends `REVIEW_STAGE` only to `open_divergent_exchange`, which
  returns `REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED`.
- The controller sends `SCIENTIFIC_CONVERGENCE_TASK` or
  `START_IMPLEMENTATION` only to `research_project_manager`, which returns
  `RESEARCH_CONVERGENCE_BRIEF`, `IMPLEMENTATION_READY` or
  `RESEARCH_MANAGER_BLOCKED`.
- The controller sends an authorized monitor assignment only to
  `experiment_monitor`, which returns the terminal monitor payload defined by
  `$hmasd-experiment`.

Temporary subagents are not persistent sessions. The Research Project Manager
may spawn bounded implementation subagents with `$hmasd-implementer` and one
fresh reviewer with `$hmasd-reviewer`. These children have no role-directory
entry, receive no router invocation and return only through native parent-child
collaboration.

Reject every other persistent edge. A role cannot authorize another role,
launch a successor, change a model or expand its assignment.

## Callback acceptance

Accept a callback only when:

- it explicitly activates `$hmasd-task-router`;
- native `source_thread_id` equals the registry task for the declared role;
- `handoff_id` is stable and matches the assignment;
- sender/receiver form one legal edge;
- the payload matches the sender Skill's terminal schema.

Treat a repeated role plus `handoff_id` as the same delivery. Do not repeat
project updates or launch successors.

## Route self-test

A controller may send `SESSION_ROUTE_SELF_TEST` with this Skill and exactly one
registered role Skill. The role verifies identity, performs no role work or
heartbeat, and returns one routed `SESSION_ROUTE_SELF_TEST_OK`. This proves
communication only.

## Semantic recovery

Keep route checks strict and role interiors intelligent. A role reports direct
evidence, semantic diagnosis and the remaining authority boundary. On retry,
send the same bounded task to the same role with both explicit Skill invocations
and the prior error as evidence. Do not prescribe selectors, clicks, shell
recipes, patches or internal reasoning steps.

## Topology changes

Only the active controller changes this graph. Before editing:

1. state the old and intended graph;
2. run `scripts/audit_session_topology.ps1` with removed and added role/message
   terms;
3. inspect every match and every `always_inspect` path;
4. freeze retained, removed and replaced sessions;
5. update the registry, sender and receiver Skills, heartbeat ownership, helper
   scripts, `AGENTS.md`, reviewer registry, workflow docs and tests in one Git
   boundary.

Do not message an affected session during partial migration. After editing,
rerun the audit with removed terms, validate all affected Skills and tests, then
commit and push before dispatch. Removed persistent sessions are unregistered;
they are never silently reused for another role.

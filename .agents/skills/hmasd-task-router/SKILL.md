---
name: hmasd-task-router
description: Mandatory communication-only Skill for every persistent HMASD Codex session and for active-controller maintenance of the persistent-session topology. Use before every persistent-session message or callback, and whenever roles, edges, session bindings, or callback destinations change. Resolve and preserve live delivery metadata, audit every topology change across affected role Skills and contracts, and require tool-level delivery plus post-send route invariance without selecting or changing a model or project decision.
---

# HMASD Task Router

## Scope

Own persistent-session communication only. Internal coding workflow is outside
this router. This Skill by itself grants no authority to read project-control
documents, interpret the task, choose a role, operate a role tool, create a
task, or authorize work. It does not revoke context
separately granted by active-controller status or by the one assigned role
Skill.

Routing remains deliberately strict because a wrong recipient or route field
can change another task. This Skill validates identity, delivery and route
invariance only. It does not validate scientific content, prose structure,
implementation quality or role-internal procedure; those judgments remain with
the receiving role and controller.

Every delegated persistent session receives this Skill and exactly one
session-role Skill. Reject an assignment that names zero or multiple role
Skills with `TASK_BLOCKED` before doing role work.

## Session and Role Directory

Read `references/session-roles.json` before any persistent-session send or
callback acceptance. It is the only communication registry for the controller,
Research Project Manager, Code Implementation Manager, three reviewer-exchange
sessions, and Experiment Monitor session IDs and their one-to-one role
bindings. Other role registries must not duplicate Codex session IDs.

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

Every persistent-session message starts with explicit Skill activation. The
first nonempty line is:

```text
$hmasd-task-router
```

A controller assignment then names exactly one destination role Skill on the
next line, such as `$hmasd-code-manager`, `$hmasd-project-manager`,
`$hmasd-review-exchange`, or `$hmasd-experiment`. The assignment envelope
follows after a blank line. A role callback to the controller names only
`$hmasd-task-router` before its callback payload. Literal `role_skill=` fields,
Skill paths, and prose references do not activate a Skill and are not a
substitute for these lines.

The recipient rejects a message missing the required explicit invocation before
using conversation history or doing role work. This reloads the current
working-tree contracts in long-lived sessions and prevents stale compacted
context from silently selecting an old procedure.

Send a self-contained envelope:

```text
$hmasd-task-router
$<destination-role-skill>

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

Role-specific lifecycle messages such as `REVIEW_STAGE` or
`MONITOR_ASSIGNMENT` may use their role Skill's compact schema instead of the
generic envelope. Every compact message must still contain exactly one
`role_skill=<path>` field and grants no implied context.

## Route Self-Test

Use this communication-only envelope to test a registered persistent route
without starting its role workflow:

```text
$hmasd-task-router
$<registered-role-skill>

SESSION_ROUTE_SELF_TEST
task_id=<stable id>
role=<registered role key>
role_skill=<registered role Skill path>
nonce=<stable nonce>
return=SESSION_ROUTE_SELF_TEST_OK
```

The recipient reads this Skill, the role directory, and the named role Skill
only. Verify that its current task ID and `role_skill` match the role entry.
Do no role work and create no heartbeat: do not use a browser, external model,
Git, project mutation, internal coding workflow, or experiment. Resolve the registered
controller live and send exactly:

```text
$hmasd-task-router

SESSION_ROUTE_SELF_TEST_OK
role=<registered role key>
handoff_id=<task_id>:<nonce>
task_id=<stable id>
source_thread_id=<recipient task ID>
```

Require ordinary delivery proof and post-send route invariance for the
controller. The recipient may then finish locally with
`ROUTE_SELF_TEST_RELAYED`. This self-test proves communication only; it never
substitutes for a role-specific transport, browser, external-model, Git, or
experiment smoke.

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

Immediately after an accepted send, resolve the same recipient again. Require
the post-send `hostId`, `threadId`, `model`, and `thinking` to equal the
pre-send values exactly. If any field changed, do not resend, repair, or mirror
a setting. Return `TASK_ROUTE_CORRUPTION` with the before/after values to the
active controller. This post-send check is delivery validation, not permission
to alter either task.

A definite pre-acceptance `notLoaded` error permits one identical retry after
loading the same target. An accepted or ambiguous send is never repeated. If a
required callback cannot obtain delivery proof, the sender follows its role
Skill by keeping its own heartbeat active and retrying only the same stable
`handoff_id`.

Before replying, resolve the reply destination again as the new recipient.
Never reuse route metadata carried by the incoming message.

## Semantic Recovery

Routing failures remain strict; role-work failures do not become mechanical
controller scripts. A role reports the direct evidence, its best semantic
diagnosis, what remains incomplete, and whether recovery is possible inside the
same authority. It does not ask the controller to prescribe a selector, command,
click sequence, code patch or internal reasoning procedure.

When retrying, the controller sends the same bounded assignment to the same
registered session, explicitly activates the router and that role Skill again,
and supplies the previous error as evidence plus the desired observable outcome.
The role rereads both Skills and chooses its own safe recovery approach. A
repeated failure that reveals a reusable contract defect is returned as a Skill
improvement recommendation; only the controller edits the protected Skill.

## Controller Send Contract

For every controller-to-session assignment:

1. select the declared role in `references/session-roles.json`;
2. require its registered role Skill to equal the assignment's `role_skill`;
3. take the recipient `thread_id` only from that role entry;
4. resolve that ID immediately before delivery;
5. require the prompt to begin with `$hmasd-task-router` and the registered
   destination role Skill;
6. copy the returned `hostId`, `threadId`, `model`, and `thinking` unchanged into
   one `send_message_to_thread` call;
7. accept delivery only when the tool returns the same recipient `threadId`.

Do not send to an ID supplied in free-form task text, reuse cached live metadata,
compare against a preferred model, or mutate either session's model or thinking.
The controller records no waiting state and does not manage a role session's
heartbeat.

## Topology Change Protocol

Only the active controller changes the persistent-session graph. Before editing
an edge, role, callback target, or session binding:

1. state the old graph and intended graph;
2. run `scripts/audit_session_topology.ps1 -Terms <old and new role, message,
   and callback names>`;
3. inspect every returned match plus every `always_inspect` path;
4. freeze which sessions are retained, archived, replaced, or newly created;
5. make one active-line change with no compatibility route.

For every changed edge, update all applicable surfaces in the same boundary:

- `references/session-roles.json` and its schema version;
- this Skill's legal graph and receive contract;
- the sender role Skill's destination and message schema;
- the receiver role Skill's callback destination and terminal schema;
- heartbeat ownership and the condition for deleting it;
- role helper scripts and `agents/openai.yaml` prompts that name the flow;
- role-specific registries and workflow documentation;
- `AGENTS.md` dispatch and firewall statements;
- every affected contract test.

Do not message any affected persistent session while its graph is internally
inconsistent. After editing, rerun the audit using removed role/message terms,
inspect every remaining match, validate all affected Skills and contract tests,
and commit/push the complete boundary before the next workflow dispatch.

When a topology change creates or replaces a persistent session, create it once
with the model/thinking explicitly requested by the user, resolve its live route,
then register only its stable task ID. Never store route fields, reuse the old
session for a new role, or silently substitute a task after creation failure.
Archive an explicitly removed session after its replacement or removal boundary
is unambiguous.

## External Review Topology

Enforce this exact communication graph:

```text
controller <-> gemini_divergent_exchange
controller <-> open_divergent_exchange
controller <-> convergent_exchange
```

The controller sends `REVIEW_STAGE` only to the single exchange whose
registered `reviewer_role` matches that assignment. A reviewer exchange returns
`REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED` only to the controller. Reject
reviewer-to-reviewer, reviewer-to-monitor, and exchange-to-Code-Manager sends.

For a controller-to-exchange send, apply the same live-resolution and unchanged
`hostId`/`threadId`/`model`/`thinking` rules as the Controller Send Contract.
The controller takes the recipient ID only from the role directory and accepts
delivery only when the tool returns that same exchange `threadId`.

## Code Implementation Topology

Enforce this exact persistent-session edge:

```text
controller <-> code_implementation_manager
```

The controller sends `START_CODE_WORK` only to the registered Code
Implementation Manager. The manager's internal coding workflow is outside the
persistent-session graph and is not prescribed by this router. The manager
alone returns `CODE_GIT_PUSH_REQUIRED`, `CODE_EXTERNAL_REVIEW_REQUIRED`,
`CODE_COMPLETE`, or `CODE_BLOCKED` to the controller. Reject every other
persistent code-work edge.

## Research Project Management Topology

Enforce this exact persistent-session edge:

```text
controller <-> research_project_manager
```

The controller sends `PROJECT_REVIEW_TASK` only to the registered Research
Project Manager after a Convergent raw, on an explicit route-alignment request,
or before a scientific implementation/experiment handoff whose mission role is
unclear. The manager returns exactly one `PROJECT_REVIEW_BRIEF` or
`PROJECT_REVIEW_BLOCKED` directly to the controller. It never contacts an
Exchange, Code Manager or Experiment Monitor and owns no heartbeat.

## Receive Contract

Accept a persistent-session callback only when all of these are true:

- the callback prompt explicitly activates `$hmasd-task-router` before the
  payload;
- the native delegation metadata `source_thread_id` equals the session ID in
  `references/session-roles.json` for the declared role;
- the payload contains that role's stable `handoff_id`;
- the payload matches the exact terminal schema in the named role Skill.

Also require the sender and receiver pair to be an edge in the External Review
Topology, Code Implementation Topology, Research Project Management Topology,
or the registered experiment-monitor-to-controller edge. A valid payload on an
invalid edge is rejected without forwarding.

Reject a callback whose source task, role, or schema does not match. Never infer
the sender from prose inside the payload. Receipt grants no new project,
scientific, experiment, or Git authority.

Treat a repeated callback with the same role and `handoff_id` as the same
delivery. A duplicate may confirm receipt but must not repeat project updates,
launch a successor, or produce a second scientific interpretation. This
idempotency is the recovery path when a role session delivered successfully but
stopped before deleting its own heartbeat; do not add a separate relay state
machine.

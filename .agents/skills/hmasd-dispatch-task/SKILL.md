---
name: hmasd-dispatch-task
description: Use when an HMASD operation requires a registered cross-task send, live route resolution, source-boundary resolution, role callback, or delivery recovery.
---

# HMASD Task Dispatch

Role contracts are normative. Read `AGENTS.md`, `docs/project/CURRENT_WORK.md`,
the registry entry in `references/session-roles.json`, and its exact contract
under `.agents/roles/` before using this procedure. This Skill grants no
scientific, workflow, technical-acceptance, compute, Git, or transport authority.

## Select the operation

- Use `project_manager` only for an exact Project Manager assignment or callback.
- Do not dispatch a persistent `experiment_monitor`. For one already-authorized
  run, Controller invokes `$hmasd-experiment-monitor` directly in its own task.
- Controller-direct external review is not a persistent-role dispatch. Use
  `$hmasd-review-round` and `$browser:control-in-app-browser` under the
  Controller role contract.

Use only ACTIVE roles in the registry. Never infer a destination from a title,
history, callback text, model name, or manually copied task ID.

## Recovery before blocked

On timeout, approval wait, missing state, route failure, delivery failure or
tool/runtime error, keep the current handoff active. The owning role inspects
the direct error and current state, tries safe materially distinct recovery
paths within its authority, and reports each attempt as:

```text
RECOVERY_ATTEMPT
attempt=<positive integer>
boundary=<failed operation>
action=<diagnostic or recovery action>
outcome=<observed result>
```

Do not repeat an identical failed action without changed state, switch to an
unregistered task, alter the payload, override model/effort, widen authority,
or start a successor. Only after no safe in-scope recovery remains may a role
emit a blocked result; it includes the direct cause, recovery attempts, and
`recovery_exhausted=true`.

## Live route and execution-profile fence

```text
cross_thread_model_effort_preservation=required
live_target_profile_is_authoritative=true
resolved_model_effort_copy=exact
static_profile_expectation=forbidden
```

Run `scripts/resolve_task_route.ps1 -Role <role>` immediately before every
cross-task send. Require nonempty `hostId`, `threadId`, `model`, and `thinking`.
These live target values are the only profile authority. Copy all four unchanged
into exactly one `codex_app__send_message_to_thread` call. Never use the
sender's model or effort, a default, assignment prose, or stale registry data.
Do not store or compare against a fixed expected model/effort table. If the send
arguments differ from the just-resolved values, block before sending with
`TARGET_EXECUTION_PROFILE_OVERRIDE`.

Resolve the same role immediately after delivery. Identity, model, and thinking
must be unchanged. A difference caused by delivery is
`TARGET_EXECUTION_PROFILE_CORRUPTED`; do not resend until the target profile is
restored or the user explicitly changes it. Static registry data never stores
route metadata.

The resolver may use the project Conda environment's bundled `sqlite3.exe` when
no `sqlite3` command is on `PATH`. That fallback is read-only.

## Project Manager

Immediately before a Project Manager assignment, run
`scripts/resolve_source_boundary.ps1`; send only:

```text
source_boundary=local_and_remote_aggressive_tip
```

Never hand-copy a source SHA. The resolved `source_commit` is evidence output. A
local/remote mismatch is `SOURCE_BOUNDARY_DIVERGED`.

Before `IMPLEMENTATION_READY`, `DERIVATION_READY`, `REVIEW_PACKAGE_READY`, or
`RESEARCH_MANAGER_BLOCKED`, Project Manager resolves `controller` and calls
`codex_app__send_message_to_thread` once with one complete terminal payload.
If delivery cannot be confirmed, inspect actual state and re-resolve. Retry the
identical payload only when no accepted delivery exists and the live profile is
unchanged. Exhausted delivery recovery is
`PROJECT_MANAGER_DELIVERY_BLOCKED`.

## Controller completion callback

Every Project Manager-to-Controller handoff declares
`return_role=project_manager`. When the requested mechanical operation completes
or becomes blocked, Controller constructs exactly one receipt:

```text
CONTROLLER_OPERATION_RECEIPT
return_role=project_manager
request_identity=<assignment, package, review, or run identity>
operation=<mechanical operation>
operation_status=<COMPLETE or BLOCKED>
source_commit=<accepted source identity>
result_identity=<commit, raw path, artifact root, or route receipt>
path_source_status=<exact mechanical outcome>
remaining_authority=<unchanged authorization state>
blockers=<none or exact mechanical blocker>
```

Do not add per-file hashes to an assignment or receipt. For code integration,
the exact path set, staged diff check, and resulting Git commit are sufficient.

Before stopping or making a user-only completion report, run
`scripts/resolve_task_route.ps1 -Role project_manager`, send that receipt once
with the resolved live profile unchanged, then re-resolve and verify the same
identity, model, and effort. The receipt contains no approval, interpretation,
workflow choice, or successor instruction; it only wakes Project Manager.
Delivery recovery follows the rules above. If no safe recovery remains, report
`CONTROLLER_CALLBACK_BLOCKED` with the attempts and keep the workflow visibly
open.

## Experiment Monitor

There is no persistent Monitor route and no fixed Monitor model or effort.
Controller invokes `$hmasd-experiment-monitor` directly with the run ID, root,
authoritative paths, terminal condition, ETA, and Project Manager return data.

## Controller-direct external review

External review is not dispatched through the persistent role graph. Activate
`$hmasd-review-round` and `$browser:control-in-app-browser` only for an exact
accepted transport request. Role authority remains in `.agents/roles/`.

## Assignment shape

Assignments contain the exact requested operation, inputs, exclusions,
completion condition, and return payload, not Controller history or an authority
rewrite. This dispatcher never starts a successor. A topology change activates
only after `AGENTS.md`, affected `.agents/roles/` contracts,
`CURRENT_WORK.md`, the registry, affected procedural Skills, and contract tests
form one coherent Project Manager-accepted package. Disjoint files may be
authored in parallel; Controller integrates the exact accepted set.

---
name: hmasd-dispatch-task
description: Use when HMASD work needs delivery to the registered Project Manager or experiment monitor, live route resolution, a role callback, or recovery of a persistent-role handoff.
---

# HMASD Task Dispatch

Read `docs/project/CURRENT_WORK.md` and
`references/session-roles.json` before sending work. Use only ACTIVE registered
roles; never infer a role from a title, old callback, history, or a manually
copied task ID.

```text
controller <-> project_manager
controller <-> experiment_monitor
```

External Pro is not a persistent Codex role. Controller-direct external review
uses `$hmasd-review-round` and `$browser:control-in-app-browser` in the active
Controller.

## Skill trigger contract

The Controller activates this dispatcher as `$hmasd-dispatch-task`. When a
receiving role depends on a Skill, begin the assignment with its exact catalog
trigger in `$skill-name` form. Use `$hmasd-experiment-monitor`; never send a
`SKILL.md` path or a path-valued `role_skill` field as a loading instruction.

The Controller owns routing, continuation, Git, formal-compute authority and
mechanical provenance intake. Under an active autonomous grant, an accepted
role callback wakes the Controller to route the next already-authorized action.
Stop only on a paused/exhausted grant, genuine blocker, or protected-scope
expansion. A reported failure is not a genuine blocker until the owning role
has completed bounded self-recovery and reported its recovery attempts.

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
unregistered task, or widen scientific/compute authority. `waitingOnApproval`
is an actionable wait. Only after no safe in-scope recovery remains may a role
emit `*_BLOCKED` or `MONITOR_ERROR`; its terminal payload includes the direct
remaining cause, recovery attempts and `recovery_exhausted=true`.

## Resolve before every send

Run `scripts/resolve_task_route.ps1 -Role <role>` immediately before a send.
Require nonempty `hostId`, `threadId`, `model` and `thinking`, then copy all four
resolved values unchanged into exactly one send. Resolve again afterward; if
identity, model or thinking changed, report route corruption and do not resend.
Static registry data never stores route metadata.

The resolver may use the project Conda environment's bundled `sqlite3.exe` when
no `sqlite3` command is on `PATH`. That fallback is read-only.

## Project Manager

Use `project_manager` for an authorized implementation realization, WIP audit,
focused verification or package acceptance. Before each assignment, run
`scripts/resolve_source_boundary.ps1`; send only:

```text
source_boundary=local_and_remote_aggressive_tip
```

Never hand-copy a source SHA. A local/remote mismatch is
`SOURCE_BOUNDARY_DIVERGED`.

The Manager owns decomposition, native child-agent use and every code-side
semantic artifact. It does not change science, Git, project control,
external-review transport or formal-compute authority.

If a protected scientific choice blocks code-side work, Manager authors and
repairs the complete reviewer-visible package. Its brief, manifest and question
declare:

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_code_side
scientific_authority=external_pro
```

Controller checks only role/source provenance, required fields, paths,
authority markers and Git visibility, then commits, pushes and transports the
exact PM-authored files unchanged. It never paraphrases or repairs their
semantics. Validation failure returns `repair_owner=project_manager`.

Before `IMPLEMENTATION_READY` or `RESEARCH_MANAGER_BLOCKED`, the Manager resolves
`controller` and calls `codex_app__send_message_to_thread` once with one complete
terminal payload. A failed delivery enters the shared recovery contract. Only
an exhausted recovery becomes `PROJECT_MANAGER_DELIVERY_BLOCKED`.

## Experiment Monitor

Use `experiment_monitor` only after a run is already authorized or launched.
Before its first assignment, confirm the live route is `gpt-5.3-codex-spark` at
`medium`; do not silently fallback. Begin the assignment with
`$hmasd-experiment-monitor` and provide run ID, root, authoritative paths,
terminal condition and ETA. It never launches, restarts, repairs, extends,
edits or interprets the run.

## Controller-direct external review

External review is not dispatched through this role graph. The active
Controller loads `$hmasd-review-round` and `$browser:control-in-app-browser`,
mechanically validates the PM-authored package, and operates the registered Pro
conversation directly. It must inspect the registered conversation before
submission, preserve exact raw text and return that raw to Project Manager.
It never classifies scientific completeness or authors a focused follow-up.

The retired transport task is not a fallback. Any late output from a retired
role has no authority to write raw, complete a handoff, change control state or
start a successor.

## Authority boundary

Assignments contain outcome, authority, inputs, scope, exclusions, completion
and return semantics—not Controller history. No role starts a successor. A
topology change updates `CURRENT_WORK.md`, this Skill, the role registry and
their contract tests in one Git boundary.

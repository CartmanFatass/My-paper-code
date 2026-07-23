---
name: hmasd-dispatch-task
description: Route nontrivial HMASD work to the registered native Codex Project Manager, experiment monitor, or Open-Pro Exchange. Use whenever a task needs persistent-session delivery, external review, algorithm realization, monitoring, or a role callback; do not use for ordinary controller edits or explanation.
---

# HMASD Task Dispatch

Read `docs/project/CURRENT_WORK.md` and
`references/session-roles.json` before sending work. Use only ACTIVE registered
roles; never infer a role from a title, old callback, history, or a manually
copied task ID.

```text
controller <-> project_manager
controller <-> experiment_monitor
controller <-> open_divergent_exchange
```

## Skill trigger contract

The Controller activates this dispatcher as `$hmasd-dispatch-task`. When a
receiving role depends on a Skill, begin the assignment with its exact
catalog trigger in `$skill-name` form. Use `$hmasd-review-exchange` and
`$hmasd-experiment-monitor`; never send a `SKILL.md` path or a path-valued
`role_skill` field as a loading instruction. Registry paths identify installed
assets only and are not dispatch syntax.

The Controller owns routing, continuation, Git, formal-compute authority, and
mechanical provenance intake. Under an active autonomous grant, an accepted callback
wakes the Controller to route the next already-authorized action. Stop only on
a paused/exhausted grant, genuine blocker, or protected-scope expansion. A
reported failure is not a genuine blocker until the role has completed bounded self-recovery
and reported its recovery attempts.

## Recovery before blocked

On timeout, approval wait, missing state, route failure, delivery failure or
tool/runtime error, keep the current handoff active. The owning role inspects
the direct error and current state, tries safe materially distinct recovery
paths within its authority, and reports each attempt in commentary as:

```text
RECOVERY_ATTEMPT
attempt=<positive integer>
boundary=<failed operation>
action=<diagnostic or recovery action>
outcome=<observed result>
```

Do not repeat an identical failed action without changed state, switch to an
unregistered task, or widen scientific/compute authority. `waitingOnApproval`
is an actionable wait, not blocked. Only after no safe in-scope recovery remains
may a role emit `*_BLOCKED` or `MONITOR_ERROR`; that terminal payload includes
`recovery_attempts=<count>`, a concise attempt summary, the direct remaining
cause, and `recovery_exhausted=true`.

## Resolve before every send

Run `scripts/resolve_task_route.ps1 -Role <role>` immediately before a send.
Require nonempty `hostId`, `threadId`, `model`, and `thinking`, then copy all
four resolved values unchanged into exactly one send. Resolve again afterward;
if identity, model, or thinking changed, report route corruption and do not
resend. Static registry data never stores route metadata.

On this Windows workspace, the resolver may use the project Conda
environment's bundled `sqlite3.exe` when no `sqlite3` command is on `PATH`.
That fallback reads only live route metadata and never adds static route fields
to the registry.

## Project Manager

Use `project_manager` for an authorized implementation realization, WIP audit,
focused verification, or package acceptance. Before each assignment, run
`scripts/resolve_source_boundary.ps1`; send only:

```text
source_boundary=local_and_remote_aggressive_tip
```

Never hand-copy a source SHA. The Manager resolves and records its own source
commit; a local/remote mismatch is `SOURCE_BOUNDARY_DIVERGED`, not an invitation
to guess a nearby SHA.

The assignment includes objective, external-Pro scientific direction, evidence
inputs, exact scope, protected semantics, exclusions, checks, and return
contract. The Manager owns decomposition, native child-agent use, and all
code-side semantic artifacts. It does not change science, Git, project control,
external-review transport, or formal-compute authority.

If a protected scientific choice blocks executable definition or implementation,
the Manager owns the full reviewer-visible code-side package rather than an
internal audit that Controller must translate. Its brief, evidence manifest and
question declare:

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_code_side
scientific_authority=external_pro
```

The package isolates the exact missing choice without selecting it. Internal PM
logs and audits stay internal. Controller checks only role/source provenance,
required fields, paths, authority markers and Git visibility, then commits,
pushes and sends the exact PM-authored files unchanged. Controller never
paraphrases or repairs code-side or scientific semantics. Validation failure is
returned as `repair_owner=project_manager` to the same Manager assignment.

Before `IMPLEMENTATION_READY` or `RESEARCH_MANAGER_BLOCKED`, the Manager resolves
`controller` and calls `codex_app__send_message_to_thread` once with one complete
terminal payload to that exact route. A
failed delivery enters the shared recovery contract. Retry the same handoff only
after re-resolving the route and proving no accepted delivery exists. Only an
exhausted recovery becomes `PROJECT_MANAGER_DELIVERY_BLOCKED`; it never
authorizes a guessed route or successor.

## Experiment Monitor

Use `experiment_monitor` only after a run is already authorized or launched.
Before its first assignment, confirm the live route is `gpt-5.3-codex-spark` at
`medium`; do not silently fallback. Send `MONITOR_ASSIGNMENT` with run ID, root,
authoritative status/progress/result paths, expected terminal condition, and ETA.

Begin the assignment with `$hmasd-experiment-monitor`. The monitor owns
ETA-based heartbeats and
returns one terminal `EXPERIMENT_MONITOR` payload to the resolved Controller. It
never launches, restarts, repairs, extends, edits, or interprets the run.

## Open-Pro Exchange

Use `open_divergent_exchange` only for registered external-Pro transport. The
role owns one neutral handoff, natural-response capture, exact raw archival, and
its heartbeat. It never chooses science, code, compute, Git, or a successor.
Begin every review assignment or recovery continuation with
`$hmasd-review-exchange`.

Accept a callback only after matching its registered source role, round,
handoff ID, and raw path. `REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED`
wakes the Controller for mechanical provenance intake and next-action routing. A
blocked callback is accepted only when it also reports recovery attempts and
`recovery_exhausted=true`; otherwise continue the same handoff under the shared
recovery contract.

A callback for any fence accepted before the PM semantic-ownership contract is
transport evidence only. Require `superseded_process=true` and
`adoption_authority=false`; archive it without adoption, code authorization or
successor routing. A current package must identify its external-Pro raw as the
only scientific authority and still cannot self-authorize compute.

For a package-validation failure, accept `repair_owner=project_manager` and
redispatch the unchanged failure evidence to Project Manager. The Controller
must not edit the question or substitute a Controller-authored evidence file.

## Authority boundary

Assignments contain outcome, authority, inputs, scope, exclusions, completion,
and return semantics—not controller history. No role starts a successor. A
topology change updates `CURRENT_WORK.md`, this Skill, the role registry, and
their contract tests in one Git boundary.

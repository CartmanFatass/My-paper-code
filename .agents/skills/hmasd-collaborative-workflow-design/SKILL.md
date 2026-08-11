---
name: hmasd-collaborative-workflow-design
description: Use only in the task-scoped HMASD Workflow Design Manager L1 to turn an explicitly Root-dispatched workflow request into a plan, or execute it within an explicit plan+execute boundary.
---

# HMASD Collaborative Workflow Design

## Boundary

```text
activation_trigger=user_workflow_change_or_reported_workflow_defect_requiring_plan
startup_preload=false
```

This Skill is invoked only by the Root-assigned Workflow Design Manager L1. It
grants no runtime, current-work state beyond WDM's own records, science, code
or code-acceptance authority. CPM and Explorer return exact requirements or
defects through Root; they never invoke this Skill or mutate workflow surfaces.

```text
workflow_design_owner=workflow_design_manager
runtime_authority=none
workflow_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace
session_workspace_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
control_plane_document_routes=docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md
assignment_writing_skill=hmasd-writing-agent-assignments
workflow_zero_question_path=fully_specified_mutations
workflow_decision_question_condition=changes_named_plan_field
workflow_dispatch=Root_explicit_user_dispatch_only
workflow_plan_only=return_detailed_plan_only
workflow_plan_execute=execute_within_explicit_authorized_boundary_without_fixed_second_confirmation
workflow_material_drift=return_to_Root_only
workflow_input_lanes=USER_REQUESTED_CHANGE
workflow_incident_record=chronological_nonblocking_log
workflow_l1_multiplicity=role_defined_scope_key
workflow_wdm_scope_key=workflow_scope_key
workflow_scope_key_semantics=semantic_ownership_concurrency_locator
```

The Session Workspace Contract is the single mechanics source for workspace,
lifecycle, progress, review, convergence, Root and Git boundaries. This Skill
adds only the requirements and authorization consequences below. Root compiles
the user's explicit request into a self-contained natural-language assignment:
outcome, why, objects and relations, owner, allowed judgment, completion and
next action precede the minimal anchors. `plan-only` returns a detailed plan;
explicit `plan+execute` permits execution inside its stated goal, non-goals,
authority, path-family and external-effect boundary. Every workflow-file
mutation is routed to a registered
Workflow Implementer L2 on exact owned paths; WDM never writes and Root remains
the sole user, physical, lifecycle and Git actor.

At the design/dispatch boundary, invoke `$hmasd-writing-agent-assignments` as
the required sub-skill. It is the single assignment-writing contract WDM uses
to design a reusable child or cross-session interface and compile each
concrete file-backed assignment. This Skill routes to that contract and does
not duplicate its procedure.

## Understand requirements

Before planning, consult `docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md`. A
clear route row supplies the defining source, direct consumers and focused
tests for the affected contract. A missing, ambiguous, conflicting or
authority-crossing route requires a bounded registered Auditor; do not
rediscover the repository or guess the route. Inspect only the named
control-plane paths after the route is clear. Ask a question only when its
answer changes a named plan field, name that field, ask one question at a time
and recommend the smallest answer with its practical effect. Repository facts
are discovered; user decisions are not inferred.

Classify the Root assignment as `plan-only` or explicit `plan+execute`.
Reported defects are evidence for Root, not an autonomous repair lane. Do not
turn a defect report into automatic workflow mutation; Root obtains explicit
user dispatch and compiles its boundary.

If goal, non-goals, exact paths, intended behavior, verification and risks are
already fixed, take the zero-question path and present the complete plan. Stop
asking when the user can judge every material effect. Do not edit, dispatch,
stage, commit, push or create an artifact during requirements work.

## Present one plan

Present one compact plan containing:

- **Requirements understanding** — requested behavior and controlling decisions.
- **Goal and non-goals** — desired workflow behavior and excluded work.
- **Exact paths** — every file expected to change. The exact-path matrix includes
  `AGENTS.md` as `modify` or `unchanged-valid`; a role, session, Skill, profile,
  authority, route or retired-name change needs a same-commit router update.
- **Intended changes** — material role, Skill, script, route and ownership edits.
- **Verification and risks** — focused checks and the local consequence of each
  risk choice. Use the canonical Session keys
  `workflow_change_risk_tiers`, `workflow_route_table_policy`,
  `workflow_singleton_package`, `workflow_singleton_acceptance`,
  `workflow_multi_candidate_convergence_trigger`,
  `workflow_causal_check_timing` and `workflow_progress_event_emission`.

Risk is semantic consequence, never file count. `high` covers authority,
topology, cross-owner or shared-contract consequences and routes through the
registered read-only Auditor. `bounded_contract` covers a stable cross-file
contract within one owner; a clear route may skip a new Auditor only with a
WDM rationale. `low_causal_repair` covers wording, a recognizer or one bounded
assertion family preserving accepted meaning; a WDM rationale may skip the
Auditor even when tightly coupled files exceed one. These are routing choices,
not gates or extra owners.

Plan one focused causal-family check when all consumed producer, consumer and
test bytes are frozen and before package acceptance; reuse the result only
while those bytes remain unchanged. The validation ownership remains
`slice_local` for writers, `integration_cross_slice` for WDM and
`runtime_fresh_smoke_after_root_integration_reload` for Root.

One writable WDM L1 assignment's exact final frozen bytes, including its
disjoint Implementers in the shared L1 worktree, form a singleton package.
After routed checks and exactly one advisory Reviewer, that WDM may accept the
package and return it to Root; no fresh convergence WDM or worktree is needed
solely for singleton integration. True multi-candidate convergence is reserved
for Root combining two or more independently reviewed WDM candidates, or when
the actual union differs from every reviewed package; a fresh WDM then reviews
the actual union with exactly one advisory Reviewer and owns union acceptance.

An edit-capable child assignment carries the exact owned paths and task-scoped
workspace. The child verifies the current checkout identity before editing and
stops on a mismatch; no external workspace identity is required. The Session
contract and registered Roles define caller fork settings, worktrees,
completion order and Root's physical/lifecycle actions; this Skill does not
restate them.

For a simple correction, keep the plan concise: goal, key unknown, smallest
probe, one normal path plus one simple fallback and a stop condition. For every
new mechanism state the irreversible error prevented, terminal condition, total
recurring cost and old mechanism/text deleted, then name the focused contract
evidence and qualitative maintainability it preserves. A retryable failure
receives a one-line runtime checklist, not a mechanism. A workflow cost audit
explicitly requested by the user is the only cost-review path.

For `plan-only`, return the complete plan and do not mutate. For explicit
`plan+execute`, refine paths, slices, focused tests and reversible mechanics
and execute without a fixed second confirmation. Return to Root only if goal,
explicit non-goals, owner authority, science/estimand, major path family,
acceptance method, unapproved irreversible external effect, or a real user
choice materially drifts. Resolve ordinary mechanics inside the boundary.

## After authorized plan+execute dispatch

After explicit `plan+execute` dispatch, load `$hmasd-workflow-change-audit`.
That Skill owns implementation, verification, the singleton or
true-union review/acceptance route and its one bounded fallback. Root retains
physical application, lifecycle, Git and reload. This requirements Skill remains
requirements and plan boundaries only and does not duplicate execution
execution, delegation or replacement-task procedures.

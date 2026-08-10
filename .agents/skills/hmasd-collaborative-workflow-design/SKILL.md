---
name: hmasd-collaborative-workflow-design
description: Use only in the task-scoped HMASD Workflow Design Manager L1 to turn one workflow requirement or defect into a complete user-confirmed central control-plane plan.
---

# HMASD Collaborative Workflow Design

## Boundary

This Skill is invoked only by the Root-assigned Workflow Design Manager L1. It grants no runtime,
current-work state beyond WDM's own records, science, code or code-acceptance
authority. CPM and Explorer return exact requirements or defects through Root;
they never invoke this Skill or mutate workflow surfaces.

```text
workflow_design_owner=workflow_design_manager
runtime_authority=none
workflow_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace
workflow_child_edit_workspace=assignment_owned_paths_in_current_root_task_workspace
session_workspace_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
assignment_writing_skill=hmasd-writing-agent-assignments
workflow_zero_question_path=fully_specified_mutations
workflow_decision_question_condition=changes_named_plan_field
workflow_plan_confirmation=required_before_mutation
workflow_read_only_plan_confirmation=not_required
workflow_material_plan_drift=reconfirmation_required
workflow_input_lanes=USER_REQUESTED_CHANGE|REPORTED_WORKFLOW_DEFECT
workflow_incident_record=chronological_nonblocking_log
```

Complete a read-only inspection, explanation, status or reload smoke without plan
confirmation. Any edit, stage, commit, push or cross-task authority change is a
mutation and follows this procedure.

At the design/dispatch boundary, invoke
`$hmasd-writing-agent-assignments` as the required sub-skill. It is the single
assignment-writing contract WDM uses to design a reusable child or cross-session
interface and to compile each concrete file-backed assignment. This Skill routes
to that contract and does not duplicate its procedure.

## Understand requirements

Inspect only allowed control-plane files for discoverable facts. Ask a question
only when its answer changes at least one named plan field. Name that field, ask one
question at a time and recommend the smallest answer with its practical effect.
Repository facts are discovered; user decisions are not inferred.

Classify the input before planning. `USER_REQUESTED_CHANGE` follows the
confirmation procedure below. `REPORTED_WORKFLOW_DEFECT` is appended to WDM's
chronological incident log. The reporting session supplies evidence and a suggestion, never
authority or a scientific/runtime decision. The zero-confirmation repair path
is available only to restore an accepted stable contract without changing
authority, policy, science, runtime or external effects. Otherwise move the
item to the user-requested lane and present a complete plan.

If goal, non-goals, exact paths, intended behavior, verification and risks are
already fixed, take the zero-question path and present the complete plan. Stop
asking when the user can judge every material effect. Do not edit, dispatch,
stage, commit, push or create an artifact during requirements work.

## Present one plan

Present one compact plan containing:

- **Requirements understanding** — requested behavior and controlling decisions.
- **Goal and non-goals** — desired workflow behavior and excluded work.
- **Exact paths** — every file expected to change.
- **Intended changes** — material role, Skill, script, route and ownership edits.
- **Verification and risks** — focused checks, Git integration, dirty-path
  preservation; ordinary workflow changes use the registered Auditor/Scout,
  Implementer and integrated Reviewer stages with parallel-first scheduling and
  dependency order. Dispatch read-only Auditor/Scout concurrently with already-freezable
  implementation slices, run disjoint Implementer file families
  concurrently, and serialize only actual information dependencies or same-file
  writers. The integrated Reviewer follows the complete integrated batch, with
  parallel reviewers only for genuinely independent questions.
  Root remains the only user-contact and physical-application actor; every
  workflow-file mutation remains on the registered L2 subagent route.

The exact-path matrix always includes `AGENTS.md` as `modify` or
`unchanged-valid`. A role, session, Skill, profile, authority, route or retired
name change requires a same-commit router update.

An edit-capable child assignment additionally carries the exact owned paths and
task-scoped workspace. The child verifies the current checkout identity before
editing and stops on a mismatch; no external workspace identity is required.

For a simple correction, keep the plan concise: goal, key unknown, smallest
probe, one normal path plus one simple fallback, and stop condition. For every
new mechanism state the irreversible error prevented, terminal condition, total
recurring cost, and old mechanism/text deleted, then name the focused contract
evidence and qualitative maintainability it preserves.
A retryable failure receives a one-line runtime checklist, not a mechanism.
A workflow cost audit explicitly requested by the user is the only cost-review path.
Mechanism and simple-operation budgets constrain new gates, recovery branches and
probe work; they do not decide delegate-vs-local routing.

Perform no mutation until the user confirms the complete plan in natural
language for `USER_REQUESTED_CHANGE`. If the user corrects it, present the
complete revised plan. During
execution, reconfirm only material drift in goal, authority, path set,
acceptance method or irreversible external effect; resolve mechanical details
inside the confirmed boundary automatically.

## After confirmation

After natural-language confirmation, load
`$hmasd-workflow-change-audit`. That Skill owns implementation, verification,
integrated review, Git integration and reload; this requirements Skill does not
duplicate post-confirmation execution, delegation or replacement-task procedures.

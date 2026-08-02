---
name: hmasd-collaborative-workflow-design
description: Use only in the persistent HMASD Workflow Design Manager task to turn one workflow requirement or defect into a complete user-confirmed central control-plane plan.
---

# HMASD Collaborative Workflow Design

## Boundary

This Skill is invoked only by Workflow Design Manager. It grants no runtime,
current-work state beyond WDM's own records, science, code or code-acceptance
authority. Other persistent sessions send WDM requirements or defects and never
invoke this Skill to mutate workflow surfaces.

```text
workflow_design_owner=workflow_design_manager
runtime_authority=none
workflow_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace
workflow_child_edit_worktree=resolved_ticket_worktree_path|pre_edit_git_rev_parse_toplevel_exact_match
session_workspace_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
workflow_zero_question_path=fully_specified_mutations
workflow_decision_question_condition=changes_named_plan_field
workflow_plan_confirmation=required_before_mutation
workflow_read_only_plan_confirmation=not_required
workflow_material_plan_drift=reconfirmation_required
workflow_input_lanes=USER_REQUESTED_CHANGE|REPORTED_WORKFLOW_DEFECT
workflow_defect_queue_states=QUEUED|ACTIVE|CLOSED
```

Complete a read-only inspection, explanation, status or reload smoke without plan
confirmation. Any edit, stage, commit, push or cross-task authority change is a
mutation and follows this procedure.

## Understand requirements

Inspect only allowed control-plane files for discoverable facts. Ask a question
only when its answer changes at least one named plan field. Name that field, ask one
question at a time and recommend the smallest answer with its practical effect.
Repository facts are discovered; user decisions are not inferred.

Classify the input before planning. `USER_REQUESTED_CHANGE` follows the
confirmation procedure below. `REPORTED_WORKFLOW_DEFECT` is archived first in
WDM's FIFO. The reporting session supplies evidence and a suggestion, never
authority or a scientific/runtime decision. WDM may use the zero-confirmation
repair path only to restore an accepted stable contract without changing
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
  preservation and any required risk-triggered reviewer.

The exact-path matrix always includes `AGENTS.md` as `modify` or
`unchanged-valid`. A role, session, Skill, profile, authority, route or retired
name change requires a same-commit router update.

An edit-capable child assignment additionally carries the exact resolved ticket
worktree path. The child verifies `git rev-parse --show-toplevel` equals that
path before editing and stops on any mismatch.

For every new mechanism state the irreversible error prevented, terminal
condition, total recurring cost, old mechanism/text deleted and net line change.
A retryable failure receives a one-line runtime checklist, not a mechanism.
A workflow cost audit explicitly requested by the user is the only cost-review path.

Perform no mutation until the user confirms the complete plan in natural
language for `USER_REQUESTED_CHANGE`. If the user corrects it, present the
complete revised plan. During
execution, reconfirm only material drift in goal, authority, path set,
acceptance method or irreversible external effect; resolve mechanical details
inside the confirmed boundary automatically.

## Execute and stop

After confirmation, WDM loads `$hmasd-workflow-change-audit` and continues
through impact mapping, smallest implementation, verification, review when
risk-triggered, exact Git integration and reload receipt without per-action
approval. A requester does not become an acceptance owner.

For any non-few-step execution, the confirmed plan plus bounded live
reconnaissance is the frozen execution plan required by `AGENTS.md`; do not add
a second plan artifact or confirmation. If implementation evidence invalidates
a tool, interface, path set or recovery assumption, stop only that branch,
update the plan from the evidence and resume automatically unless the change
expands authority, outcome, irreversible external effect or another named
material plan field.
This replaces ad-hoc reactive tool or strategy switching and adds no workflow
state, terminal or recurring approval.

Do not create a handoff, review, child, runtime record or state machine merely
to manage this collaboration. WDM returns its accepted workflow commit and
exact verification, or the smallest missing user decision.

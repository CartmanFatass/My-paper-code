---
name: hmasd-workflow-change-audit
description: Use only in Workflow Design Manager after plan confirmation to implement, verify, accept, commit and route one centralized HMASD control-plane change.
---

# HMASD Workflow Change Audit

## Contract boundary

Workflow Design Manager is the sole workflow design, modification, acceptance
and Git authority. This Skill grants no science, code, code acceptance, runtime
or project-state authority. CPM, Explorer and other sessions report exact
requirements/defects and continue their non-workflow duties; they do not edit or
accept control-plane surfaces.
Workspace ownership remains defined by `docs/project/SESSION_WORKSPACE_CONTRACT.md`.

Use this Skill for router, role, Skill, profile, hook, registry, stable workflow
contract, workflow script or focused workflow test changes. Operational state,
review instances, run artifacts, scientific ledgers and implementation code are
outside this procedure.

## Hard design budgets

```text
workflow_mechanical_invariant_scope=irreversible_and_high_cost_actions_only
workflow_retryable_failure_mechanism=forbidden_use_one_line_runtime_checklist
workflow_single_mechanism_line_budget=100
workflow_single_mechanism_terminal_state_budget=3
workflow_mechanism_budget_unit=one_new_or_expanded_gate_or_recovery_branch
workflow_legacy_mechanism_policy=no_expansion_reduce_when_touched
workflow_new_mechanism_requires_named_deletion=true
workflow_net_line_growth_default=negative_or_zero
workflow_incident_to_permanent_rule_threshold=2_independent_recurrences
workflow_first_incident_response=root_cause_fix_plus_note_only
workflow_hash_validation=forbidden
wdm_core_control_plane_line_budget=1000
workflow_rule_single_source=one_defining_file_others_point
workflow_recovery_path_line_share=must_not_exceed_normal_path
simple_operation_definition=failure_only_requires_retry
simple_operation_new_gate_state_identity_or_recovery=forbidden
simple_operation_control=one_line_runtime_checklist_only
theoretical_safety_hardening=reject_by_default
new_regression_admission=normal_supported_path_or_two_independent_recurrences
```

If failure means only “try again”, do not build a lease, sentinel, identity
ledger, retry state machine or approval gate. Add the smallest direct diagnostic
or one-line checklist. A new mechanism identifies the old text/mechanism it
deletes and is accepted by net active-line change. One incident cannot legislate
a permanent rule; require two independent recurrences.

Simple operations never accumulate gates, states, identity fields, recovery
branches or permanent negative tests. Reject theoretical hostile-input or
safety-hardening proposals unless they reproduce on a supported normal path or
the same real defect has independently recurred at least twice.

Never use a hash, digest, byte count or fingerprint as workflow admission,
routing, handoff, recovery or acceptance evidence. Preserve scientific artifact
integrity outside workflow design.
Git revision identifiers are source locators, not recomputed payload/content
hash admission evidence. The 100-line and three-terminal budgets apply to one
new or expanded gate or recovery branch, not retroactively to a whole existing
tool; any touched legacy branch must stay flat or shrink.

## Workflow children

```text
workflow_auditor=hmasd-workflow-auditor_optional_impact_map_or_postchange_verify
workflow_implementer=hmasd-workflow-implementer_optional_exact_confirmed_slice
workflow_reviewer=hmasd-workflow-reviewer_risk_triggered_only
workflow_cost_reviewer=explicit_user_request_only
workflow_child_parent=workflow_design_manager
workflow_child_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace
workflow_child_acceptance_authority=none
workflow_child_edit_worktree=resolved_ticket_worktree_path|pre_edit_git_rev_parse_toplevel_exact_match
```

Children reduce context and mechanical effort; WDM retains authority, semantic
junctions, conflict resolution, final diff inspection, acceptance, Git and
routing. Do not create a child when dispatch/packet review costs more than the
direct edit. For six or more paths, auditors may map disjoint families.
Dispatch one implementer per exact nonoverlapping file family up to available
native slots, reserving one slot for WDM integration; do not impose a fixed
two-implementer ceiling.
Each child has exactly one existing role charter. Every profile is registered
exactly once and receives a fresh-task profile smoke after registry changes.

Use one Workflow Reviewer only for authority/file ownership, locked routing or
model settings, Pro transport/recovery, compute admission, an action-performing
script/hook or unresolved cross-worker semantics. Ordinary documentation needs
no reviewer. Never review the review.
Only when the user explicitly requests a workflow cost audit may WDM dispatch
the cost reviewer.

## Continuous change loop

Before this loop, archive each typed defect report in
`docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md`.
Keep exactly one receipt-order item `ACTIVE`; later reports remain `QUEUED`.
Close an item with an accepted repair, a precise not-a-defect finding, or the
user-change-plan boundary. `BLOCKED` is not a queue state, and a retryable tool
failure cannot stop unrelated work.

1. **Inventory.** Search only named control-plane files for changed identities,
   authority terms, paths and retired names. Historical science/review evidence
   is not a repair target. Classify `AGENTS.md` as `modify` or `unchanged-valid`
   for every workflow change.
2. **Classify.** Keep a local matrix `path | relation | action | evidence`; each
   row is `modify`, `add`, `delete`, `unchanged-valid` or `historical-exempt`.
   Declare the exact path set and preserve all unrelated dirty/staged/untracked
   work.
3. **Isolate.** When the main checkout is unsafe or a child writes, provision an
   exact `scripts/hmasd_workspace_ticket.py` worktree. Use only the opaque ticket
   and registered resolve/verify flow; never raw `git worktree` or path aliases.
   Put the exact resolved ticket worktree path in every edit-capable child assignment and
   require an exact `git rev-parse --show-toplevel` equality check before edit;
   a mismatch stops that child before mutation.
4. **Probe.** Run the smallest existing contract that exposes the relation. Add
   one negative regression only when a known missing relation otherwise passes.
5. **Implement.** Delete superseded active rules instead of adding compatibility
   layers. Scripts perform deterministic mechanics, not policy decisions.
6. **Verify.** Run the structural harness, affected focused contracts, stale-term
   searches, exact diff-path check and `git diff --check`. Count the six core
   files named in the WDM charter and fail above 1000 lines. A changed role,
   session, Skill, profile, authority, route or retired name with stale router
   text fails acceptance.
7. **Review.** If a named risk trigger applies, request at most one advisory
   Workflow Reviewer packet. WDM accepts or rejects each finding against the
   normal-path evidence threshold and minimum-design budgets; reviewer
   disagreement is not an approval gate and never starts a re-review loop.
8. **Integrate.** Inspect exact staged paths and `git diff --cached --check`, then
   commit and push only accepted workflow paths. A Git receipt is not another
   acceptance owner.
9. **Reload.** If router, registry or profile changed, require a fresh task before
   relying on discovery. Route one reload receipt to each affected persistent
   session with locked model and thinking.

After a confirmed plan, these steps continue automatically. Stop only for
material plan drift, same-file collision, unavailable required profile, or a
missing user decision. A recoverable tool/transport failure is diagnosed and
continued or parked without blocking unrelated work.
A durable restart handoff is written only on explicit user request; routine
progress remains in WDM's existing session/common records.

## Harness

Run with the registered interpreter:

```powershell
& '<hmasd_python_interpreter>' `
  .agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py `
  --repo .
```

The harness checks structure, retired terms and the 1000-line WDM core budget.
It cannot decide semantics or acceptance. Add `--active-path` and `--forbid`
only for change-specific stale references.

## Acceptance

Accept only when the impact matrix is closed, child packets are reconciled,
focused and structural checks pass, stale references are explained, exact
changed/staged paths are inspected, the core line budget passes and any required
review has no unresolved finding. Return the pushed commit, exact paths,
verification and reload boundary.

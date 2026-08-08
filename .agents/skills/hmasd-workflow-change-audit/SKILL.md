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
simple_operation_active_engineering_budget_minutes=20
simple_operation_failed_probe_budget=2
simple_operation_paths=one_normal_plus_one_simple_fallback
simple_operation_success=user_visible_requested_result
passive_external_generation_wait_excluded_from_engineering_budget=true
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
workflow_reviewer=hmasd-workflow-reviewer_integrated_batch_default
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

After WDM integrates all implementer results into one coherent batch, use one Workflow Reviewer by default.
Add parallel reviewers only for genuinely
independent review questions; each receives a distinct focus and may read the
whole integrated diff. Review is batch-scoped rather than per implementer. The
reviewers evaluate normal-path risk against complexity, maintenance, wall-clock
and iteration-delay cost. Run one review phase only: no automatic second review,
reviewer-of-reviewer, schema admission gate, wrapper or state machine.

## Continuous change loop

Append typed reports to the chronological incident log; the log is evidence, not
a scheduler, approval state or global blocker.

1. **Inspect.** Read only named control-plane paths, declare the exact path set,
   preserve unrelated work and identify the smallest normal-path probe.
2. **Delete or edit.** Remove superseded rules before adding text. Use an isolated
   resolved ticket worktree path only when the main checkout is unsafe or concurrent writers
   need separate path families. Before editing there, require its
   `git rev-parse --show-toplevel` to equal the resolved ticket worktree path;
   a mismatch stops that isolated edit.
3. **Focused check.** Run the smallest affected contract, the structural harness,
   stale-term search and `git diff --check`. When implementers were used, review
   the integrated batch once by default; add parallel reviewers only for
   genuinely independent questions.
   Their advice cannot create a second pass.
4. **Git and reload.** Inspect exact staged paths, commit and push the accepted
   workflow files. Require a fresh task only after router/profile discovery
   changes; ordinary Skill text is read from disk. After an isolated child
   commit is integrated, retire its clean detached ticket worktree only through
   `scripts/hmasd_workspace_ticket.py retire` with the exact assignment, ticket
   and expected HEAD. Retirement never uses force or discards Git-visible work;
   any identity, HEAD or cleanliness mismatch preserves the worktree and ticket.

The workspace PreToolUse guard fails closed for recognized mutation forms and
preserves its existing denials. Treat it as bounded syntactic preflight rather
than an arbitrary shell-semantics proof; tool/OS sandboxing, registered ticket
identity and Git-visible checks remain authoritative.

After a confirmed plan, these steps continue automatically. Stop only for
material plan drift, same-file collision, unavailable required profile, or a
missing user decision. A recoverable tool/transport failure is diagnosed and
continued or parked without blocking unrelated work.
A durable restart handoff is written only on explicit user request; routine
progress remains in WDM's existing session/common records.

For every role, Skill or profile change, inspect the owned outcome against the
role's observation, action, judgment, recovery and completion capabilities.
Reject a design that assigns an outcome while withholding a necessary page,
process, file, diagnostic or reversible action. Also reject duplicated
procedures across role, Skill and profile: keep authority/capability in the
role, the normal path plus one fallback in the Skill, and model/sandbox plus a
role pointer in the profile. Prefer positive capability text over enumerating
every forbidden mistake.

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

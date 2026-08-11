---
name: hmasd-workflow-change-audit
description: Use only in the task-scoped Workflow Design Manager L1 after plan confirmation to implement, verify, accept and route one centralized HMASD control-plane proposal.
---

# HMASD Workflow Change Audit

## Contract boundary

```text
activation_trigger=confirmed_workflow_plan_execution_or_verification
startup_preload=false
```

Workflow Design Manager is the sole workflow design, modification and acceptance
authority. Root owns physical application, lifecycle and Git mechanics. This
Skill grants no science, code, code acceptance, runtime
or project-state authority. CPM, Explorer and other sessions report exact
requirements/defects and continue their non-workflow duties; they do not edit or
accept control-plane surfaces.
Workspace ownership remains defined by `docs/project/SESSION_WORKSPACE_CONTRACT.md`;
the active child boundary is the exact assignment-owned path set in the current
Root task workspace. One writable L1 assignment, including a WDM workflow
writer, uses one Root-provisioned managed worktree. All disjoint L2 writers
under that WDM use the invoking L1 assignment's named worktree, same frozen
base and exact disjoint paths; they have no Git authority or action and never
invoke or control the helper or worktree lifecycle. Their outputs form one L1
slice candidate, which Root commits or records only after all children complete.
An independent candidate or release lifecycle requires a new L1 assignment;
L2 never has its own worktree lifecycle. Distinct concurrent L1 assignments and
later union integration/convergence each use a distinct Root-managed worktree.
Read-only, ignored-only and temporary-only work is exempt, while mixed writes
remain tracked-writer work. This Skill never invokes the helper or runs raw
child `git worktree` lifecycle operations.

Use this Skill for router, role, Skill, profile, hook, registry, stable workflow
contract, workflow script or focused workflow test changes. Operational state,
review instances, run artifacts, scientific ledgers and implementation code are
outside this procedure.

## Validation, progress and review normal path

The Session Workspace Contract is the single defining field source. The normal
path has exactly three validation layers: writers run `slice_local` checks on
owned paths and the smallest affected contracts; after all writes freeze, WDM
runs exactly one `integration_cross_slice` suite; and Root alone performs
`runtime_fresh_smoke_after_root_integration_reload` after Root integration and
canonical reload. That runtime layer is pending until Root's post-integration
action and is not a child or WDM check. Writers never run the whole suite.

WDM publishes exactly these status-only progress events, in their defined
meaning: `DISPATCHED` (actions started), `WRITES_COMPLETE` (all writers
terminal and exact changed paths frozen), `TESTS_COMPLETE` (required test
layers completed with evidence), `REVIEW_READY` (the exact union and evidence
frozen for one Reviewer), and `TERMINAL` (the terminal conclusion returned to
Root). These observations are not a scheduler, queue, ledger, background
callback, retry state, admission or acceptance token; `TERMINAL` does not mean
accepted. Use exactly one integrated advisory Reviewer after
`TESTS_COMPLETE`/`REVIEW_READY`; the Reviewer reads the frozen union, cannot
edit or accept, and no second review pass follows its advice.
Return these observations through the current Root task/report boundary only;
do not create a persistent event store or callback, queue or ledger transport.

High-risk authority, topology, cross-owner or shared-contract changes require
an Auditor. For low-risk one-file wording or test-only work, WDM may skip a
new Auditor only with a concrete recorded rationale; this is not a gate or a
second acceptance owner. Root's L1-start choice is planning guidance: begin
only when useful owned work has useful action or matching leaf capacity. It is
not a quota, reservation, scheduler, admission gate, pool or runtime
authorization, and `max_threads=20` is an agent-tree ceiling only.

On Windows, use a short absolute assignment-specific basetemp under the
Root-controlled parent (`C:\Projects\ht\<assignment-run>` for integration
verification). Classify environment-setup failures separately from
product-assertion failures: repair setup and rerun at the same layer without
retry state; repair the causal contract or implementation for product
failures.

## Hard design budgets

```text
workflow_mechanical_invariant_scope=irreversible_and_high_cost_actions_only
workflow_retryable_failure_mechanism=forbidden_use_one_line_runtime_checklist
workflow_l1_multiplicity=role_defined_scope_key
workflow_wdm_scope_key=workflow_scope_key
workflow_root_wdm_fork_turns=1_caller_action_only
workflow_wdm_registered_implementer_fork_turns=none_explicit_caller_action
workflow_l1_worktree_rule=one_writable_l1_assignment_one_root_managed_worktree
workflow_l2_worktree=invoking_l1_assignment_named_worktree
workflow_independent_candidate=new_l1_assignment_required
workflow_union_convergence_worktree=separate_root_managed_worktree
workflow_single_mechanism_terminal_state_budget=3
workflow_mechanism_budget_unit=one_new_or_expanded_gate_or_recovery_branch
workflow_legacy_mechanism_policy=no_expansion_preserve_contract_when_touched
workflow_new_mechanism_requires_named_deletion=true
workflow_incident_to_permanent_rule_threshold=2_independent_recurrences
workflow_first_incident_response=root_cause_fix_plus_note_only
workflow_hash_validation=forbidden
workflow_rule_single_source=one_defining_file_others_point
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

Mechanism and simple-operation budgets constrain new gates, recovery branches
and probe work; they never decide delegate-vs-local routing.
Delegate-vs-local routing is policy-fixed: task size, complexity, local
feasibility, context cost, path count and benefit estimates never alter it.

If failure means only “try again”, do not build a lease, sentinel, identity
ledger, retry state machine or approval gate. Add the smallest direct diagnostic
or one-line checklist. A new mechanism identifies the old text/mechanism it
deletes and is accepted by focused contract evidence and qualitative
maintainability. One incident cannot legislate
a permanent rule; require two independent recurrences.

Simple operations never accumulate gates, states, identity fields, recovery
branches or permanent negative tests. Reject theoretical hostile-input or
safety-hardening proposals unless they reproduce on a supported normal path or
the same real defect has independently recurred at least twice.

Never use a hash, digest, byte count or fingerprint as workflow admission,
routing, handoff, recovery or acceptance evidence. Preserve scientific artifact
integrity outside workflow design.
Git revision identifiers are source locators, not recomputed payload/content
hash admission evidence. The three-terminal limit applies to one new or
expanded gate or recovery branch, not retroactively to a whole existing tool;
any touched legacy branch preserves the accepted contract and should remain
straightforward.

Maintainability is judged by interface quality, coherent responsibility,
dependency direction, explicit state ownership, decoupling, complexity
isolation, change locality and focused contract evidence. Line and file counts
may be recorded as diagnostics, but they never reject a change, force a split
or define acceptance.

## Workflow children

Ordinary workflow changes use the registered Auditor/Scout, Implementer and
integrated Reviewer work with parallel-first scheduling and dependency order
for bounded, non-overlapping slices. Dispatch read-only Auditor/Scout
concurrently with already-freezable implementation slices, run disjoint
Implementer file families concurrently, and serialize only actual information
dependencies or same-file writers. A same writable path or shared unfrozen
semantic contract is a dependency and serializes affected slices. The integrated
Reviewer follows the complete integrated batch only after Root has integrated the
exact candidate slices and a fresh convergence WDM has arranged that review;
parallel reviewers are limited to genuinely independent review questions
(parallel reviewers only for genuinely independent questions). A scoped WDM accepts only its exact slice and
returns candidate-ready evidence to Root. Root records and integrates candidates; only the fresh
convergence WDM over the exact integrated union owns coherent integrated review and union
acceptance. The Workflow Reviewer is read-only/advisory and cannot accept. Their authority and
assignment meaning remain with their Role and `hmasd-writing-agent-assignments`;
workspace and fresh-Root boundaries remain with
`docs/project/SESSION_WORKSPACE_CONTRACT.md`. Stable execution orientation is
in `docs/project/WORKFLOW_MAP.md`. Root remains the only user-contact and
physical-application actor; every workflow-file mutation remains on the
registered L2 subagent route. Pure WDM design or authority decisions without
file mutation remain WDM-local. This Skill retains only the implementation
budgets, focused checks, review and Root reload boundary below.

## Continuous change loop

Append typed reports to the chronological incident log; the log is evidence, not
a scheduler, approval state or global blocker.

1. **Inspect.** Read only named control-plane paths, declare the exact path set,
   preserve unrelated work and identify the smallest normal-path probe.
2. **Delete or edit.** Remove superseded rules before adding text. One writable
   L1 assignment uses one Root-provisioned managed worktree. Its disjoint L2
   writers edit only their exact paths in that invoking L1 assignment's named
   worktree, on the same frozen base, with no child Git/helper action; their
   outputs form one L1 slice candidate and Root commits or records it only
   after all writers finish. Read-only, ignored-only and temporary-only work
   uses the named current task workspace. Root alone provisions, records the
   lifecycle receipt, integrates accepted paths and releases or retains the
   worktree; no helper lifecycle is part of this Skill.
3. **Focused check.** Run the smallest affected contract, the structural harness,
   stale-term search and `git diff --check`. For a scoped slice, WDM reconciles
   and accepts the exact slice, and the implementer packet is candidate-ready;
   no integrated review or union acceptance is claimed at this point. After
   Root integrates the exact candidate union, a fresh convergence WDM arranges
   one integrated Reviewer by default; parallel reviewers only for genuinely independent questions. Their advice cannot create a second pass. WDM owns union acceptance and Root performs authorized integration.
4. **Return and reload.** Inspect exact changed paths and return the scoped
   candidate-ready packet, focused evidence and reload boundary to Root. After
   Root integration, the fresh convergence WDM returns the union accepted
   proposal; Root applies accepted workflow paths and performs any separately
   authorized Git mechanics. This Skill does not promise a current commit, push
   or external workspace cleanup.

The configured hooks remain empty and disabled. No Hook Stop route is part of
this workflow. Tool/OS sandboxing and exact assignment paths remain the
authoritative write boundary.

After a confirmed plan, these steps continue automatically. Stop only for
material plan drift, same-file collision, unavailable required profile, or a
missing user decision. A recoverable tool/transport failure is diagnosed and
continued or parked without blocking unrelated work.
A durable restart handoff is written only on explicit user request; routine
progress remains in the current Root task's WDM records. A later CLI invocation
starts a fresh Root/L1 tree and reloads canonical files; no manager session,
replacement task or background callback is presumed.

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

The harness checks structure and retired terms only.
It cannot decide semantics or acceptance. Add `--active-path` and `--forbid`
only for change-specific stale references.

## Acceptance

For a scoped slice, accept only when the impact matrix is closed, the child
packet is reconciled, focused and structural checks pass, stale references are
explained and exact changed paths are inspected; return a candidate-ready
packet, without claiming integrated review or union acceptance. Only the fresh
convergence WDM after Root integrates the exact union applies the additional
integrated-review condition (no unresolved actionable finding) and returns the
union accepted proposal, exact paths, verification and reload boundary to Root.
Root decides whether a separately authorized candidate commit is needed.

# HMASD Root-First Role Router

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
topology=cli_root_depth_0|task_scoped_level1|task_scoped_level2_leaf
root=the_current_cli_task_root
max_subagent_depth=2
```

This file is the minimum identity, authority and routing contract. A fresh
CLI invocation starts at Root and reloads canonical files; it does not resume a
Desktop session, thread, successor or background callback. History, results,
budgets and procedures belong to the named assignment, Role, Skill or
canonical record.

## Precedence and role resolution

The Root reads this router first, identifies the owner lanes, and dispatches
task-scoped L1 managers only when the task needs them. An L1 reads its exact
assignment, its registered profile and Role, then dispatches only its named L2
allow-list. An L2 reads only its exact assignment, profile, Role and immediate
references. Missing identity, parent, owned paths or completion evidence fails
closed and returns to Root.

The shared L1 multiplicity vocabulary is Role-defined: each L1 Role declares
its own scope-key field, and one Root tree may contain multiple active
instances of that Role on distinct scope-key values. The `(role, scope_key)`
pair is unique per Root tree. A scope key is only a semantic
ownership/concurrency locator; it is not a ticket, queue, ledger, registry,
admission token or continuity/session identity.

| Tree position | Identity | Read after this file | Do not load by default |
|---|---|---|---|
| Root, depth 0 | current CLI task root | user request, this router, confirmed plan and required canonical files | owner semantics before dispatch |
| L1, depth 1 | WDM | exact assignment, `.codex/agents/hmasd-workflow-design-manager.toml`, `.agents/roles/WORKFLOW_DESIGN_MANAGER.md` | code, runtime and science state |
| L1, depth 1 | CPM | exact assignment, `.codex/agents/hmasd-code-project-manager.toml`, `.agents/roles/CODE_PROJECT_MANAGER.md` | workflow-control and research corpus |
| L1, depth 1 | Explorer | exact assignment, `.codex/agents/hmasd-independent-research-explorer.toml`, `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md` | project runtime and unrelated workflow state |
| L2, depth 2 | registered leaf | exact assignment, its profile, named Role and immediate references | user, sibling lanes, unrelated history |

L1 managers are same-level children of Root. Each L1 Role declares its own
scope-key field; multiple active instances of that Role may coexist in one
Root tree only on distinct scope-key values, with each `(role, scope_key)` pair
unique per Root tree. They use `followup_task` within the same tree when assignment meaning
and context remain valid. They never contact the user or a sibling directly;
cross-owner information is returned to Root for relay. When a CLI task ends,
all descendants end or are explicitly reported by Root. A later invocation
starts a fresh Root and reloads canonical files; no scope key is a ticket,
queue, ledger, registry, admission token or continuity/session identity, and
no thread/session identity or successor task is presumed.

## Root authority and owner boundaries

```text
root_user_interaction_authority=exclusive
root_cross_owner_relay_authority=exclusive
root_agent_tree_and_lifecycle_authority=exclusive
root_top_level_owned_path_freeze=exclusive
root_canonical_state_physical_write_authority=accepted_proposals_only
root_final_git_integration_authority=accepted_paths_only
root_semantic_owner_authority=macro_portfolio_advisory
root_macro_portfolio_owner=Root
root_advisory_portfolio_science_authority=cross_direction_compare|rank|pause_continue|dependencies|complete_map_acceptance
root_direction_research_execution_authority=none
root_code_technical_acceptance_authority=none
root_formal_project_canonical_science_authority=user_external_pro
root_domain_acceptance_authority=none

workflow_design_manager_parent=root
workflow_design_manager_role_kind=registered_task_scoped_level1_orchestrator
workflow_design_manager_agent_tree_level=1
workflow_design_manager_workflow_design_authority=exclusive
workflow_design_manager_workflow_modification_authority=exclusive_via_assigned_L2
workflow_design_manager_workflow_acceptance_authority=exclusive
workflow_design_manager_scope_key_field=workflow_scope_key
workflow_design_manager_root_fork_turns=1_caller_action_only

code_project_manager_parent=root
code_project_manager_role_kind=registered_task_scoped_level1_orchestrator
code_project_manager_agent_tree_level=1
code_project_manager_code_authority=exclusive
code_project_manager_technical_acceptance_authority=exclusive
code_project_manager_runtime_authority=exclusive
code_project_manager_scope_key_field=code_scope_key
code_project_manager_scope_key_forms=direction:<id>|shared:<component>

independent_research_explorer_parent=root
independent_research_explorer_role_kind=registered_task_scoped_level1_orchestrator
independent_research_explorer_agent_tree_level=1
independent_research_canonical_scientific_authority=none
independent_research_user_grant_authority=direct_user_in_explorer_task_only
independent_research_explorer_scope_key_field=research_scope_key
independent_research_explorer_scope_key_forms=direction:<id>

scope_key_safe_atom=[a-z0-9][a-z0-9._-]{0,63}
scope_key_reject=empty|extra_colon|separators|whitespace|..

level1_physical_write_authority=none
level1_canonical_state_write_authority=none
level1_git_authority=none
level1_user_contact_authority=none
level1_sibling_contact_authority=none
level1_return_route=return_to_root
level1_followup_route=followup_within_same_root_tree
level2_spawn_authority=none
level2_user_contact_authority=none
level2_cross_branch_transport=none
level2_canonical_state_write_authority=none
level2_git_authority=none
```

Semantic ownership and acceptance remain with WDM, CPM and Explorer. Physical
canonical writes are Root operations applied only after the relevant owner
returns a complete accepted proposal. Root checks path, revision and
consistency; it does not rewrite domain conclusions. Manager proposals may be
kept in an assignment-specific temporary state-proposal file, but a proposal
is not canonical state until Root accepts and writes it.

## Routing and lifecycle

```text
workflow_change_request_route=Root->WDM
code_runtime_request_route=Root->CPM(direction:<id>|shared:<component>)
research_request_route=Root->Explorer(direction:<id>)
portfolio_advisory_route=Root-local-macro-portfolio
cross_owner_route=owner->Root->owner
cross_task_transport=return_to_root
cross_task_transport_legacy=forbidden
successor_route=fresh_Root_spawn_plus_canonical_reload
background_callback=forbidden
root_lifecycle_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
mandatory_ticket_identity=forbidden_for_subagent_authority
```

The current Root may run disjoint owner lanes in parallel, subject to actual
capacity and same-path dependencies. Completion order does not establish
semantic priority. Root uses bounded `wait_agent` while safe required work
remains and answers progress questions in commentary without yielding the
active turn. Root final-response conditions and forbidden continuation surfaces
are keyed in the Session Workspace Contract.

Root invokes every WDM L1 with caller action `fork_turns=1`; this supplies
background context only and is not a TOML/profile enforcement field or an
authority source. Multiple active WDMs may run concurrently only on disjoint frozen scopes,
represented by distinct `workflow_scope_key` values. The same writable
path, or a shared semantic contract that is still unfrozen, is an actual
dependency and serializes the affected slices.

Each scoped WDM accepts only its slice (the exact frozen slice) and returns
candidate-ready evidence to Root. Root records/integrates candidates. Only after that integration does Root dispatch a fresh
convergence WDM over the exact integrated union; that WDM arranges coherent integrated
review and owns union semantic acceptance. A Workflow Reviewer is
read-only/advisory and cannot accept; a slice packet does not
claim integrated review or union acceptance.

This explicit WDM workflow convergence is not a standing or fresh domain
convergence lane and does not create an extra union Reviewer. Root owns the advisory
macro/portfolio science surface: cross-direction comparison, ranking,
pause/continue and dependency decisions, plus complete-map acceptance. An
Explorer Manager (EM) is dispatched only for one `direction:<id>` and performs
that direction's research execution. A Code Manager (CM) is dispatched only
for `direction:<id>` or `shared:<component>`; its slice acceptance is final
for that slice. Root mechanically integrates accepted direction/shared slices
and runs union Tests/Static. A semantic conflict returns to the owning CM(s),
or to a temporary named shared CM. Root does not become technical acceptance
owner. Formal/project-canonical science remains at the user/External Pro
boundary.

Root-dispatched L1 user-facing task names, progress labels and report labels
follow the defining `L1 user-facing display names` section of
`docs/project/SESSION_WORKSPACE_CONTRACT.md`: `WM_<purpose>` identifies
Workflow Manager control-plane work, `EM_<direction>` identifies the actual
Independent Research Explorer Manager, and `CM_<purpose_or_direction>`
identifies Code Manager work. Immutable internal task IDs may differ. A WM
label may name a research-routing target only when it remains visibly
workflow/control-plane work; research execution is an EM concern.

## Registered L2 leaves

Every L2 profile declares `role_kind=registered_task_scoped_level2_leaf`,
`agent_tree_level=2`, its single `parent`, `spawn_authority=none`,
`user_contact_authority=none`, `cross_branch_transport=none`, and exact owned
paths. L2 may use `workspace-write` only for those paths; it never stages,
commits, pushes, updates canonical coordination state or performs final
acceptance. WDM, CPM and Explorer each maintain their own explicit L2 allow-list
in the corresponding Role/profile.

The registered callable topology keeps WDM's three workflow leaves, CPM's
code/mechanical leaves plus `hmasd-cpm-agentify-transport`, and Explorer's
research/mechanical leaves plus `hmasd-explorer-agentify-transport`.
The shared production identity is retired; production transport is exactly the
two parent-specific registered types `hmasd-cpm-agentify-transport` and
`hmasd-explorer-agentify-transport`, and WDM is not a production parent.
The CPM and Explorer transport leaves write only their own requester-partitioned
temporary transport roots under
`temp/sessions/agentify_transport_operator/<requester>/<assignment>/`.

The listed specialist leaves remain the first-choice and authoritative route.
WDM may dispatch parallel Implementers (registered Workflow Implementers) only
for exact disjoint paths and exact nonoverlapping frozen slices, with every dispatch explicitly using
`fork_turns=none`; completion order has no semantic priority. One writable L1
assignment receives one Root-provisioned managed worktree/receipt. Disjoint L2 writers share one L1 worktree: they use the invoking L1 assignment's Root-provisioned managed worktree/receipt, the
same frozen base and exact disjoint write paths; they have no Git authority or
action, and children never invoke helper or Git lifecycle actions. Their outputs
form one L1 slice candidate, which Root commits/records only after all children complete. L2 never has its own worktree lifecycle. An independent candidate/release lifecycle means a new L1 assignment. Distinct concurrent WDM/CPM
L1 assignments use distinct Root-managed worktrees, and later union
integration/convergence uses a distinct worktree (Root-managed).
As a narrow temporary-task exception, an L1 caller may invoke the native
default child as an L2 only when no listed specialist leaf can perform the
bounded task. The caller action must use exactly
`agent_type="default"`, `model="gpt-5.6-luna"`,
`reasoning_effort="high"`, and `fork_turns="1"`; the single forked turn is
background only, and `fork_turns="1"` is not a TOML/profile enforcement
field. The caller must provide a self-contained brief under
`hmasd-writing-agent-assignments` and confine any permitted writes to exact
temporary paths under that caller's task-scoped temporary root. The default
mode is read-only; the child never writes durable state, project code or a
non-temporary path.

The native child remains an L2 with no spawn, user, sibling, cross-owner or
cross-branch contact; no canonical-state, Git, owner-acceptance, compute,
external-review, science, code-acceptance, runtime or transport authority; and
no ability to bypass Root relay. It returns only to its invoking L1 parent,
which retains routing and acceptance. This exception creates no generic
profile or Role and never displaces a matching professional leaf.

## Workspace and Git boundaries

```text
workflow_subagent_parallelism=parallel_first_with_dependency_order
same_file_concurrent_writes=forbidden
project_write_scope=current_checkout_for_exemptions_or_root_managed_worktree_for_tracked_writers
tracked_writer_workspace=root_managed_worktree_required
root_managed_worktree_default_unit=one_writable_l1_assignment
root_managed_worktree_l2_scope=invoking_l1_assignment_named_worktree|same_frozen_base|exact_disjoint_write_paths|no_child_git_or_helper|one_l1_slice_candidate
root_managed_worktree_independent_candidate=new_l1_assignment_required
root_managed_worktree_distinct_l1_assignments=true
root_managed_worktree_union_convergence=separate_worktree
tracked_writer_includes=workflow_writer|code_writer|runtime_writer|any_writer_touching_tracked_path
tracked_writer_mixed_write_classification=tracked_writer
tracked_writer_exemptions=read_only|ignored_only|temporary_only
root_managed_worktree_authority=root_only
root_managed_worktree_helper=scripts/hmasd_root_managed_worktree.py
root_managed_worktree_lifecycle=root_provision|root_record|root_integrate|root_release_or_retain
root_managed_worktree_receipt=root_controlled_lifecycle_receipt_returned_to_root
root_managed_worktree_one_nonterminal=at_most_one_nonterminal_receipt_per_assignment
root_managed_worktree_local_failure=receipt_records_local_failure_and_stays_nonterminal_for_root_retry_or_park
root_managed_worktree_legacy_isolation=legacy_worktrees_untouched_and_not_adopted_by_managed_lifecycle
raw_child_git_worktree=forbidden
raw_external_worktree_creation=forbidden
```

The Root freezes top-level path families before dispatch. One writable L1
assignment, including a WDM workflow writer, receives one Root-managed
worktree/receipt provisioned and tracked by the Root-controlled helper. All disjoint L2
writers under that WDM use the invoking L1 assignment's named worktree, the
same frozen base and exact disjoint write paths; they have no Git authority or
action and children never invoke helper or Git lifecycle actions. Their outputs
form one L1 slice candidate, which Root commits or records only after all
children complete. An independent candidate or release lifecycle requires a
new L1 assignment; L2 has no worktree lifecycle. Different concurrent L1
assignments use distinct worktrees, and union integration/convergence uses a
distinct worktree (Root-managed). Read-only, ignored-only and temporary-only assignments are
exempt; a mixed tracked and ignored assignment is still a tracked writer. Root alone controls provisioning, lifecycle, integration, Git. Root alone
provisions, records, integrates and releases or retains the managed worktree and
its lifecycle receipt. A receipt-local failure is diagnosed,
retried or parked by Root without making unrelated work terminal. At most one
nonterminal receipt is active for an assignment. Existing legacy worktrees
remain isolated and untouched by this lifecycle. Children never invoke the
helper or run raw child `git worktree` lifecycle operations. Git remains
Root-only: after owner acceptance Root applies the exact accepted path set and
performs any separately authorized integration; in a no-Git copy Root emits a
local verification receipt.

Hook posture is disabled and non-authoritative: `.codex/hooks.json` remains an
empty hook map under the direct user-disabled configuration. Routing, identity,
authority and acceptance come only from this router, the exact assignment,
registered profiles, Roles and Skills; no hook is enabled, trusted or required.

## Lazy context triggers

The concise L1 startup index is
`docs/project/L1_STARTUP_CONTEXT.md`. It points to each owner's default core
inputs and action-triggered Skills without replacing the router, Role charters,
profiles or scientific/current-work records. The index is pointer-only and is
not a preload of every owner surface.

Root starts macro/portfolio decisions from compact direction packets and lazy
direction pointers. Each EM receives one named `direction:<id>` only. Each CM
receives only its named `direction:<id>` or `shared:<component>` direct
interfaces; portfolio preload and the all-shared scope are forbidden. Invalid domain
scope families are represented only as
`portfolio_scope|integration_scope|shared_all`; no standalone portfolio or
integration owner is routable.

| Trigger | Owner surface |
|---|---|
| user workflow change or workflow defect requiring a plan | `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md` |
| designing an assignment/interface | `hmasd-writing-agent-assignments` and named contract |
| confirmed plan implementation or verification | `.agents/skills/hmasd-workflow-change-audit/SKILL.md` |
| stable owner/interface/dependency edge | `docs/project/WORKFLOW_MAP.md` |
| canonical status/continuity reload | the exact owner record named by Root |

Remaining lower-level text that still describes the retired Desktop persistent
route is non-authoritative until it is updated in a resumed migration phase.
Active routing always follows this Root-first contract.

## Routed owner documents

- Workflow roles and Skills: `.agents/roles/WORKFLOW_*.md`, `.agents/skills/`.
- Code and runtime orientation: `.agents/roles/CODE_PROJECT_MANAGER.md`.
- Research orientation: `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`.
- External Pro (non-agent, outside the CLI tree): `.agents/roles/EXTERNAL_PRO.md`.
- Canonical state: `docs/project/CURRENT_WORK.md` and exact owner records.
- Temporary proposals: `temp/sessions/<owner>/<root-assignment>/state-proposals/`.

Role charters own authority and capability; Skills own normal procedures;
profiles own model, sandbox and child pointers. No child reconstructs task
history or infers authority from inherited context.

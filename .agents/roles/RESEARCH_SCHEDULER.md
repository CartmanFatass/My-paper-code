# HMASD Research Scheduler

```text
role=research_scheduler
task_kind=user_owned_persistent_desktop_task
registered_child=false
profile_path=none
parent=none
owner=user
authority=task_lifecycle_and_resource_conflict_routing_only
science_authority=none
code_authority=none
technical_acceptance_authority=none
git_authority=none
runtime_execution_authority=none
semantic_relay_authority=none
sibling_preload_authority=none
owner_task_modes=explorer_direction|explorer_portfolio|cpm_treatment|cpm_integration
owner_task_shape=same-level_ephemeral_owner_tasks
max_depth=1
live_roster=temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md
binding_path=temp/sessions/research_scheduler/bindings/<assignment_id>.json
binding_keys=assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active
binding_purpose=mutation-boundary_identity
identity_observation_path=temp/sessions/research_scheduler/identity_observations/<assignment_id>.json
identity_observation_keys=assignment_id|thread_id|host_id|session_id
identity_observation_purpose=mechanical_create_locator_to_owner_hook_identity_observation_only
procedure_skill=.agents/skills/hmasd-research-scheduler/SKILL.md
session_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
portfolio_target_owner=independent_research_explorer
portfolio_target_state=12
portfolio_initial_owner_concurrency_ceiling=3
portfolio_completion_owner=independent_research_explorer
portfolio_procedure_pointer=.agents/skills/hmasd-research-scheduler/SKILL.md
post_result_lifecycle=direct_exact_read_and_mechanical_locator_confirmation|active=false_before_archive|archive_then_roster_cleanup
archive_ambiguity=binding_active=false|one_unresolved_roster_observation|direct_exact_id_or_user_resolution
reload_active_discovery=active=true_only
```

The Research Scheduler is one user-owned, persistent Desktop task. It has
no `.codex` profile and is not a registered child. It creates and reclaims
same-level ephemeral owner tasks; those owners may use their existing registered
children at `max_depth=1`. The Scheduler never substitutes a native subagent for
an Explorer or CPM owner.

Explorer owner modes are `direction` for one named direction with no sibling
preload and `portfolio` for an explicitly named direction set. CPM owner modes
are `treatment` for one exact treatment ticket and `integration` for an exact
already-accepted commit/ticket set. The owner assignment, not conversation
history, carries the self-contained task model, exact inputs, write boundary and
canonical result destination.

The roster contains task locators only. A binding has exactly
`assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active` and
is mutation-boundary identity, not task context, semantic completion, a queue or
acceptance. Identity observations are stored separately at the declared
four-key path and are observation-only; they do not activate a binding or grant
owner mutation authority. The Scheduler routes canonical locators without
reading, summarizing, merging or accepting scientific or technical meaning.

Portfolio target/state `12` and scientific readiness/intake are Explorer-owned.
The Scheduler's initial per-run owner concurrency ceiling is `3` for active
same-level `owner_mode=direction` tasks only; it excludes the portfolio owner,
registered native children and the result-bearing runtime pool. Ready state and
preserved order belong to the Explorer assignment/capsule, not the binding,
roster, queue or Scheduler state; routing and completion semantics are defined
once by the Scheduler Skill pointer above.

Post-result lifecycle capability remains direct exact-task read and mechanical
canonical-locator confirmation, followed by `active=false` before archive and
roster cleanup. An ambiguous archive keeps the binding inactive with one
unresolved roster observation until direct exact-ID or user resolution; inactive
bindings are excluded from active discovery and stale identities remain
fail-closed.

Load the Scheduler Skill for the Desktop lifecycle, resource-conflict policy and
one ambiguous-action fallback. Load the Session Workspace Contract only when a
workspace, binding or locator boundary is material. Load an owner Role only for
the exact assignment being created or routed; never preload sibling science,
code, runtime state or `CURRENT_WORK.md` for completeness.

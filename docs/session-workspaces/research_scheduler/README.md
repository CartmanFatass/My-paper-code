# Research Scheduler workspace

This durable directory documents the user-owned Desktop Research Scheduler
workspace. Live assignment state is ignored and temporary.

```text
workflow_surface_owner=true
workspace_owner=research_scheduler
durable_workspace=docs/session-workspaces/research_scheduler/
live_roster_locator=temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md
live_roster_required=false
desktop_handle=threadId|hostId
desktop_handle_identity=threadId+hostId
desktop_handle_purpose=exact_desktop_lifecycle_and_routing_identity
desktop_handle_source=single_create_thread_return
roster_purpose=human_readable_restart_locator_only
canonical_file_role=artifact_and_continuity_only_not_llm_identity_proof
same_file_concurrency=serialize
disjoint_exact_file_concurrency=overlap_allowed
portfolio_cardinality=dynamic_explorer_derived
portfolio_initial_direction_ceiling=3
direction_write_scope=exact_named_disjoint_files_only
portfolio_shared_write_owner=independent_research_explorer_only
treatment_write_scope=exact_cpm_ticket_worktree_only
integration_write_scope=shared_mainline_only
live_owner_interruption=forbidden
procedure_pointer=.agents/skills/hmasd-research-scheduler/SKILL.md
portfolio_interface_pointer=.agents/skills/hmasd-research-scheduler/SKILL.md
tracked_live_state=false
```

The Scheduler creates one same-level Explorer or CPM owner task and retains the
exact native `{threadId, hostId}` (`threadId+hostId`) returned by `create_thread`. That handle is
the complete lifecycle and routing identity. The optional roster merely helps a
human restart or resolve a known task; it is not an authority record, identity
proof, queue, monitor or registry. Assignment files, canonical artifacts and
continuity records likewise describe work and results but never prove which
LLM is running.

Each owner receives a self-contained natural-language assignment carrying why
the task exists, the intended outcome, canonical inputs, protected decisions,
exclusions, permitted local judgment, bounded recovery, exact cooperative write
ownership, canonical result destination and observable completion evidence.
The Scheduler does not add a file-based activation step, inspect hooks, scan
tasks or relay semantic results. Writers of one exact file serialize; disjoint
exact files may overlap. Direction owners write/return only their named
disjoint direction files. The portfolio Explorer alone writes shared portfolio
continuity/capsule state. Treatment CPM owners write only their ticket worktree
and declared result destination; integration CPM owners write the shared
mainline integration surface for an already-accepted set.

The Scheduler waits, reads and archives by direct exact native handle. It
mechanically checks the assignment's named canonical result locator before
archive and may remove the optional roster locator after successful archive.
If an action is ambiguous, preserve the owner and use direct exact-handle or
user resolution; never blindly retry or create a replacement. Reload and
selection use known exact handles only, with no task scan or inferred path
discovery. Portfolio cardinality and scientific readiness remain Explorer-owned
and the initial same-level direction-owner ceiling remains `3` as defined by
the procedure pointer.

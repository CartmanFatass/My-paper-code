# Code Project Manager current work

```text
document_kind=current_work_session
schema_version=2
state_revision=1
compatibility_path_semantics=owner_state_not_live_session
owner_role=code_project_manager
physical_writer=root
state_update_route=code_project_manager_accepted_proposal_to_root
continuity=file_backed_owner_state
reload_boundary=each_level1_spawn
next_boundary=new_root_session_reload_router_and_relevant_owner_state
cross_owner_route=return_to_root
workstream_ids=formal_toy_research|uav_validation|explorer_project_validation
external_pointer_ids=independent_research_explorer_pointer
```

This compatibility-path record identifies Code Project Manager owner state, not
a live or persistent session. Each task-scoped Code Project Manager reloads
this roster and only the applicable linked common record after Root dispatch.
Code Project Manager owns the meaning of accepted project-state updates and
returns complete proposals; Root alone writes canonical state.

- `docs/project/current-work/common/formal_toy_research.md`
- `docs/project/current-work/common/uav_validation.md`
- `docs/project/current-work/common/explorer_project_validation.md`
- `docs/project/current-work/common/independent_research_explorer_pointer.md`

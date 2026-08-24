# Legacy control-plane final active-cutover refresh

```text
snapshot_kind=FINAL_PRE_ACTIVE_CUTOVER_REFRESH
snapshot_utc=2026-08-24T13:33:28.3854651Z
source=C:/Projects/HMASD|aggressive|7cc1a56c188d39af61ee70979adc4e2dd1e9c0ae
legacy_branch=codex/legacy-control-plane-20260824
prior_snapshot_commit=fa02ba0228849d153f75c92db65e5f5576236777
copied_paths=46
production_authority=false
```

These are the exact dirty control-plane paths refreshed from the active
checkout immediately before its removal commit. No unrelated dirty project
path was copied.

```text
 M .agents/roles/CODE_PROJECT_MANAGER.md
 M .agents/roles/CPM_AGENTIFY_TRANSPORT_OPERATOR.md
 M .agents/roles/EXPERIMENT_OPERATOR.md
 M .agents/roles/EXPLORER_AGENTIFY_TRANSPORT_OPERATOR.md
 M .agents/roles/EXTERNAL_GEMINI_TRANSPORT_OPERATOR.md
 M .agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md
 M .agents/roles/LUNA_TASK_OPERATOR.md
 M .agents/roles/REVIEWER.md
 M .agents/roles/ROOT.md
 M .agents/roles/WORKFLOW_RECOVERY_MANAGER.md
 M .agents/skills/hmasd-agentify-transport/SKILL.md
 M .agents/skills/hmasd-independent-research-exploration/SKILL.md
 M .agents/skills/hmasd-workflow-anomaly-routing/SKILL.md
 M .codex/agents/hmasd-code-project-manager.toml
 M .codex/agents/hmasd-cpm-agentify-transport.toml
 M .codex/agents/hmasd-experiment-operator.toml
 M .codex/agents/hmasd-explorer-agentify-transport.toml
 M .codex/agents/hmasd-external-gemini-transport.toml
 M .codex/agents/hmasd-workflow-recovery-manager.toml
 M .codex/config.toml
 M .codex/semantic-actors.toml
 M AGENTS.md
 M docs/project/CONTEXT_SOURCE_REGISTRY.toml
 M docs/project/CURRENT_WORK.md
 M docs/project/LOW_INTRUSION_CONTROL_PLANE.md
 M docs/project/PROJECT_MAP.md
 M tests/codex_context_lifecycle/test_mcp_authority.py
 M tests/codex_context_lifecycle/test_source_registry.py
 M tests/codex_semantic_mvp/test_actor_registry.py
 M tests/codex_semantic_mvp/test_mcp_tools.py
 M tests/hmasd_control_plane/test_artifact_protocol.py
 M tests/hmasd_control_plane/test_constraint_lint.py
 M tests/hmasd_control_plane/test_intake_router.py
 M tools/codex_context_lifecycle/models.py
 M tools/codex_context_lifecycle/precedence.py
 M tools/codex_semantic_mvp/actor_registry.py
 M tools/codex_semantic_mvp/mcp_server.py
 M tools/codex_semantic_mvp/models.py
 M tools/codex_semantic_mvp/stop_policy.py
 M tools/codex_semantic_mvp/store.py
 M tools/hmasd_control_plane/artifact_protocol.py
 M tools/hmasd_control_plane/constraint_lint.py
 M tools/hmasd_control_plane/intake_router.py
?? tests/codex_semantic_mvp/test_stage_handoff_lifecycle.py
?? tests/codex_semantic_mvp/test_typed_responsibility_mcp.py
?? tools/codex_semantic_mvp/responsibility.py
```

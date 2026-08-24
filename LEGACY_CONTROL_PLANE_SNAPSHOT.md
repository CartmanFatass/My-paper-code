# Legacy HMASD control-plane snapshot

```text
snapshot_kind=HISTORICAL_ROLLBACK_REFERENCE
snapshot_utc=2026-08-24T12:23:23.5700987Z
source_checkout=C:/Projects/HMASD
source_branch=aggressive
source_head=7cc1a56c188d39af61ee70979adc4e2dd1e9c0ae
snapshot_branch=codex/legacy-control-plane-20260824
snapshot_worktree=C:/Projects/HMASD-worktrees/legacy-control-plane-20260824
cm_manifest=docs/session/HMASD_MINIMUM_VIABLE_CONTROL_PLANE_DESELFHOSTING_CM_MIGRATION_PREPARATION_20260824.md
cm_manifest_sha256=BF050A34C054BB1CC6C352B10B6FEF6555D80346645ACBCC2A1647AAD3C6CE98
production_authority=false
active_mcp_or_hook_target=false
```

This branch preserves the repository-local HMASD control plane at the migration
boundary. It is historical and rollback material only. It must not be used as
an active MCP runtime, hook target, import root, service, approval source or
test gate without a new explicit user recovery request.

The branch was created from the exact source HEAD above. The following 36
control-plane-related paths were then copied byte-for-byte from the dirty
source checkout. All other tracked paths remain at that HEAD, and unrelated
dirty research/application files were not copied.

```text
 M .agents/roles/CODE_PROJECT_MANAGER.md
 M .agents/roles/EXPERIMENT_OPERATOR.md
 M .agents/roles/ROOT.md
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

There were no deleted or renamed paths in this exact dirty snapshot set.

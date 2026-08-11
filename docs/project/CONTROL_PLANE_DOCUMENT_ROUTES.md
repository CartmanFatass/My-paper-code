# HMASD Control-Plane Document Routes

```text
document_kind=stable_control_plane_document_route_table
owner_role=workflow_design_manager
control_plane_document_routes=docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md
control_plane_document_routes_not=task_state|history|hash|receipt|queue|admission|acceptance
workflow_route_table_policy=clear_route_loads_defining_source_direct_consumers_focused_tests|missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor
workflow_route_table_auditor_priority=authority|topology|cross_owner|shared_contract=>high_requires_registered_Workflow_Auditor_regardless_of_route_clarity|skip_evidence_only_after_WDM_non-high_bounded_contract_or_low_causal_repair_classification
```

This table is a lazy relationship map for WDM control-plane work. It prevents
repeated document discovery without becoming a registry, task log, content
fingerprint, lifecycle receipt, queue, admission gate or acceptance record.
The WDM loads only the row named by the trigger. A row that is missing,
ambiguous, conflicting or authority-crossing is reported to the bounded
Auditor before the WDM chooses another source.

| Trigger | Defining source | Direct consumers | Focused tests | Auditor escalation |
|---|---|---|---|---|
| Authority and topology | `AGENTS.md` | `AGENTS.md`; `.codex/agents/hmasd-workflow-design-manager.toml`; `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`; `.codex/agents/hmasd-workflow-implementer.toml`; `.agents/roles/WORKFLOW_IMPLEMENTER.md`; `.codex/agents/hmasd-workflow-auditor.toml`; `.agents/roles/WORKFLOW_AUDITOR.md`; `.codex/agents/hmasd-workflow-reviewer.toml`; `.agents/roles/WORKFLOW_REVIEWER.md` | `tests/hmasd_two_level_agent_topology_test.py`; `tests/hmasd_workflow_design_delegation_contract_test.ps1` | `high`: Auditor required for authority, topology, cross-owner or shared-contract work regardless of route clarity; missing, ambiguous, conflicting or authority-crossing routes also require Auditor |
| Session, worktree and lifecycle | `docs/project/SESSION_WORKSPACE_CONTRACT.md` | `AGENTS.md`; `docs/project/current-work/common/workflow_control_plane.md`; `docs/project/current-work/sessions/workflow_design_manager.md`; `.agents/roles/WORKFLOW_IMPLEMENTER.md` | `tests/hmasd_session_workspace_contract_test.py`; `tests/hmasd_workflow_change_audit_test.py` | `high`: Auditor required for worktree, lifecycle, validation or Root-boundary conflict |
| WDM planning and confirmation | `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md` | `.codex/agents/hmasd-workflow-design-manager.toml`; `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`; `docs/project/L1_STARTUP_CONTEXT.md` | `tests/hmasd_collaborative_workflow_design_test.py` | Clear plan route may skip only after WDM classifies the change as non-high `bounded_contract` or `low_causal_repair` and records `workflow_auditor_skip_evidence`; missing or conflicting plan meaning requires Auditor |
| Risk, delegation and review | `.agents/skills/hmasd-workflow-change-audit/SKILL.md` | `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`; `.agents/roles/WORKFLOW_AUDITOR.md`; `.agents/roles/WORKFLOW_IMPLEMENTER.md`; `.agents/roles/WORKFLOW_REVIEWER.md` | `tests/hmasd_workflow_change_audit_test.py`; `tests/hmasd_workflow_design_delegation_contract_test.ps1` | `high`: Auditor required; only after WDM classifies the change as non-high `bounded_contract` or `low_causal_repair` may it skip with `workflow_auditor_skip_evidence` |
| L1 startup and context | `docs/project/L1_STARTUP_CONTEXT.md` | `AGENTS.md`; `.codex/agents/hmasd-workflow-design-manager.toml`; `.codex/agents/hmasd-code-project-manager.toml`; `.codex/agents/hmasd-independent-research-explorer.toml` | `tests/hmasd_l1_startup_context_test.py` | Clear route is lazy and may skip only after WDM classifies the change as non-high `bounded_contract` or `low_causal_repair` and records `workflow_auditor_skip_evidence`; missing or ambiguous context boundary requires bounded Auditor |
| Assignment and message contract | `.agents/skills/hmasd-writing-agent-assignments/SKILL.md` plus `docs/project/SESSION_WORKSPACE_CONTRACT.md` | `AGENTS.md`; `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`; `.agents/roles/WORKFLOW_AUDITOR.md`; `.agents/roles/WORKFLOW_IMPLEMENTER.md`; `.agents/roles/WORKFLOW_REVIEWER.md`; `.agents/roles/CODE_PROJECT_MANAGER.md`; `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md` | `tests/hmasd_writing_agent_assignments_test.py`; `tests/hmasd_session_workspace_contract_test.py` | Clear assignment route may skip only after WDM classifies the change as non-high `bounded_contract` or `low_causal_repair` and records `workflow_auditor_skip_evidence`; authority-crossing or semantically incomplete route requires bounded Auditor |

The focused tests listed here are evidence paths, not gates or admission
records. The defining source retains its full procedure and authority; this
table only records stable trigger-to-consumer relationships.

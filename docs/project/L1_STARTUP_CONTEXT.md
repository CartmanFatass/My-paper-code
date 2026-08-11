# HMASD L1 Startup Context Index

```text
document_kind=l1_startup_context_pointer_index
scope=task_scoped_l1_default_inputs_and_action_triggers
default_core_inputs=AGENTS.md|exact_Root_assignment|registered_profile|named_Role
startup_preload=core_inputs_only
authority_source=AGENTS.md_and_named_Roles
state_source=owner_records_only_when_triggered_and_named
scope_atom=[a-z0-9][a-z0-9._-]{0,63}
scope_reject=empty|extra_colon|separators|whitespace|..
```

This is a concise pointer index. It does not define authority, assignment
meaning, procedure, scientific state, runtime state or continuity state. Each
L1 starts with the shared `default_core_inputs`, then expands only when an
action trigger names a Skill or reference.

## Root macro/portfolio context

```text
startup_context=compact_direction_packets|lazy_direction_pointers
macro_portfolio_owner=Root
direction_context=one_named_direction_for_EM
code_context=direct_direction_or_shared_interfaces_for_CM
direction_owner=EM(direction:<id>)
code_owner=CM(direction:<id>|shared:<component>)
portfolio_preload=forbidden
```

Root uses the compact packet for cross-direction comparison, ranking,
pause/continue, dependencies and complete-map acceptance. The pointer index
does not preload research history, the whole portfolio, code/runtime state or
formal/project-canonical science.

## Workflow Design Manager (WDM)

```text
profile=.codex/agents/hmasd-workflow-design-manager.toml
role=.agents/roles/WORKFLOW_DESIGN_MANAGER.md
default_core=AGENTS.md|exact_Root_assignment|profile|role
```

| Action trigger | Pointer |
|---|---|
| User workflow change or reported workflow defect requiring a plan | `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md` |
| Confirmed workflow plan execution or verification | `.agents/skills/hmasd-workflow-change-audit/SKILL.md` |
| Assignment/interface design | `hmasd-writing-agent-assignments` and named contract |
| Scope-keyed parallel WDM startup and convergence | `docs/project/SESSION_WORKSPACE_CONTRACT.md` and the exact WDM owner record |
| Stable workflow edge | `docs/project/WORKFLOW_MAP.md` |
| Named continuity reload | exact Root-named WDM owner record |
| Macro/portfolio direction packet or lazy pointer | compact Root packet and the named direction pointer only |

The two WDM Skills are action-triggered and are not startup preload.

## Code Project Manager (CPM)

```text
profile=.codex/agents/hmasd-code-project-manager.toml
role=.agents/roles/CODE_PROJECT_MANAGER.md
default_core=AGENTS.md|exact_Root_assignment|profile|role
```

| Action trigger | Pointer |
|---|---|
| Exploratory implementation, debugging or validation | `.agents/skills/hmasd-agile-research-development/SKILL.md` |
| Explorer-to-project validation handoff | `.agents/skills/hmasd-explorer-project-validation/SKILL.md` |
| Named CPM continuity or project-operation record | exact Root-named CPM record |
| Direction/shared CM startup | one `direction:<id>` or `shared:<component>` direct interface only |

## Independent Research Explorer (Explorer)

```text
profile=.codex/agents/hmasd-independent-research-explorer.toml
role=.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md
default_core=AGENTS.md|exact_Root_assignment|profile|role
scope=direction:<id>
startup_context=one_named_direction_and_named_direction_pointers_only
portfolio_l1=forbidden
```

| Action trigger | Pointer |
|---|---|
| Bounded research exploration or synthesis | `.agents/skills/hmasd-independent-research-exploration/SKILL.md` |
| Explorer-to-project validation handoff | `.agents/skills/hmasd-explorer-project-validation/SKILL.md` |
| Named external-review action | `.agents/skills/hmasd-independent-research-pro-review/SKILL.md` |
| Named Explorer continuity record | exact Root-named Explorer record |

Cross-owner requests and results still use Root relay. This index does not
preload owner records, code/runtime surfaces, research corpus or review traffic.

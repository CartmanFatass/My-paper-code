# HMASD Workflow Map

```text
document_kind=stable_workflow_orientation
owner_role=workflow_design_manager
scope=workflow_control_plane_abstraction
```

This map is the WDM's compact orientation for workflow-control-plane design.
It describes stable ownership, interfaces, dependency direction and context
loading. It is not an authority source, task state, chronological log,
exhaustive registry or procedure copy.

## Owner roles and stable outputs

| Owner | Stable responsibility | Interface handed onward |
|---|---|---|
| Workflow Design Manager (WDM) | user-confirmed workflow design, control-plane modification, semantic integration, acceptance and workflow Git | confirmed plan, self-contained child assignment, integrated change packet and successor brief |
| Workflow Auditor | read-only local reconnaissance for an assigned workflow surface | bounded facts, dependency/ownership observations, conflicts and unknowns |
| Workflow Implementer | one frozen non-overlapping workflow change slice | `WORKFLOW_CHANGE_PACKET` with changed paths, checks, boundaries and limitations |
| Workflow Reviewer | independent review of one coherent integrated batch | review findings and disposition for WDM; no source edits or acceptance |
| Code Project Manager (CPM) | code, runtime, technical acceptance and project-operation records | code/runtime/review artifacts plus CPM-owned mechanical receipts |
| Independent Research Explorer | advisory research direction, methodology and research workspace | named research handoff; no workflow authority |
| Agentify Transport child | batch-scoped transport mechanics in its requester-assigned workspace | raw transport result for CPM or Explorer |
| External Pro | bounded independent scientific judgment | exact review result within the submitted question boundary |

The stable CPM mechanical interface is a CPM-only child boundary:
`hmasd-cpm-mechanical` receives one exact temporary
`CPM_MECHANICAL_TASK_ASSIGNMENT` (`spec_path|result_path`) and returns one
typed temporary `CPM_MECHANICAL_TASK_RESULT` (`status|result_path|error`). It
is silent until its native terminal return and writes only assignment-named
temporary outputs. CPM retains finalization, technical acceptance, source/Git
and canonical-state ownership; the child has no experiment, readiness,
Agentify, science, Git or acceptance authority. Activation requires a fresh
profile reload and has no active research-state effect.

```text
cpm_mechanical_child=hmasd-cpm-mechanical
cpm_mechanical_parent=code_project_manager
cpm_mechanical_assignment=CPM_MECHANICAL_TASK_ASSIGNMENT
cpm_mechanical_assignment_fields=spec_path|result_path
cpm_mechanical_result=CPM_MECHANICAL_TASK_RESULT
cpm_mechanical_result_fields=status|result_path|error
cpm_mechanical_terminal_status=COMPLETE|ERROR
cpm_mechanical_wait_visibility=silent_until_terminal_native_final
cpm_mechanical_write_scope=assignment_named_temporary_outputs_only
cpm_mechanical_acceptance_authority=none
cpm_mechanical_git_authority=none
cpm_mechanical_scientific_authority=none
cpm_mechanical_runtime_authority=no_experiment_no_readiness_no_agentify
cpm_mechanical_finalize_owner=code_project_manager
cpm_mechanical_activation=after_fresh_profile_reload
cpm_mechanical_active_research_state_effect=none
```

The router, Role charters, Skills, Profiles and focused contract tests form a
layered interface:

```text
AGENTS.md (identity/authority/pointers)
        ↓
Role charter (authority/capability boundary)
        ↓
Skill (normal path + one fallback)  ↔  Profile (model/sandbox/pointer)
        ↓
focused contract tests and bounded execution checks
```

The router points; Roles decide authority; Skills describe mechanics; Profiles
register callable children; tests verify the contracts. Detailed procedures do
not move back into the router or this map.

## Dependency direction

WDM owns the workflow control plane and depends on the stable contracts named by
the router. A child depends only on its self-contained assignment, registered
Profile, Role charter and assignment-named references. Child output flows back
to WDM as advisory or mechanical evidence; it never grants child design,
routing, Git or acceptance authority. CPM and Explorer remain separate owner
lanes. CPM may invoke its mechanical child through the exact file-only
assignment/result boundary; the typed temporary receipt returns to CPM for
finalization and acceptance. The registered Agentify transport child remains a
requester-owned batch capability rather than a separate owner lane; WDM does
not absorb live review traffic or results. External Pro remains a separate
scientific lane.

```text
CPM -> hmasd-cpm-mechanical -> CPM_MECHANICAL_TASK_RESULT -> CPM finalization/technical acceptance
```

```text
user-confirmed plan
        ↓
WDM assignment → Auditor observations (when needed)
        ↓
frozen owned slice → Implementer packet(s)
        ↓
coherent integrated batch → one Reviewer report
        ↓
WDM semantic integration, acceptance and Git
```

The arrows describe dependency and evidence flow, not a required state machine.
Parallel Implementers are permitted only for disjoint owned path families.

## Cost-aware adaptive delegation

Delegation is primarily a cost boundary: WDM should place routine bounded work
that does not require its high-performance semantic judgment with the cheaper
registered children. This includes ordinary mechanical edits even when the
change is small. WDM retains design junctions, authority choices, cross-lane
integration and final acceptance.

- Use the Workflow Auditor as Scout when local facts, ownership or interface
  dependencies are unclear; its role is reconnaissance, not design selection.
- Use one or more Workflow Implementers for frozen, non-overlapping slices.
- Use one Workflow Reviewer for a coherent integrated batch by default, not a
  reviewer per edit. Parallel review is for genuinely independent questions.
- Direct WDM execution is appropriate for semantic integration, acceptance,
  plan changes and other work whose judgment cannot be safely delegated.

This routing is judgment-guided. It deliberately avoids a mandatory
Scout→Implementer→Reviewer pipeline, admission gate, queue or per-action user
confirmation. The WDM's decision is whether the child can safely own the
bounded outcome, not whether a minimum line count or context-cost threshold is
met.

## Minimum context loading

The WDM normally starts with the exact assignment, its Role charter, the public
current-work index, the linked WDM session/common records, this map and the
named collaborative/workflow-change Skills. It expands only to the interfaces
needed for the confirmed slice.

A Workflow Auditor, Implementer or Reviewer starts with its exact assignment,
registered Profile, named Role and only assignment-named files. A child does
not reconstruct history or load unrelated current work. CPM and Explorer each
request the Agentify transport child through its file-only assignment; the
child follows its registered profile, role and Skill without a persistent task
lane. CPM's mechanical child likewise receives only the exact task spec and
result locator named by CPM; it does not load research, readiness, experiment
or workflow history. External Pro follows its own router lane and owner
contract. The map is an orientation aid, not a reason to load every document.

## Role-based successor continuity

Continuity belongs to the stable role identity
`session_owner_id=workflow_design_manager`, not to a permanent historical
thread ID. Batch completion is the preferred rotation boundary. A successor
task may receive a compact brief containing:

- the current workflow commit as a source locator;
- accepted stable changes;
- any real unfinished item; and
- the next user goal plus the map/interface section that must be loaded.

No task or thread is created automatically, and no thread registry is stored.
A successor re-reads the current assignment and named records rather than
inheriting hidden conversational state.

## Event-triggered maintenance

WDM updates this map in the same workflow commit when a stable fact changes:
role ownership or authority, a public interface or dependency direction, the
minimum context-loading boundary, the cost-aware delegation path, or the
successor-continuity contract. A Reviewer or Auditor reports a conflict; WDM
decides whether it is a stable change and repairs the map when required.

Maintenance is event-triggered only: a stable ownership, interface,
dependency, context-loading, delegation or continuity change may update this
map. No timer, no periodic audit, no freshness checker and no registry drives
updates.
Local wording, a one-off operational event, a temporary tool issue, an ordinary
test adjustment or active task state does not trigger a map update. Detailed
mechanics remain with their existing owner Role, Skill, Profile or test.

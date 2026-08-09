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
| Workflow Auditor | read-only local reconnaissance for an assigned workflow surface | conclusion about bounded facts/conflicts, followed by optional dependency evidence |
| Workflow Implementer | one frozen non-overlapping workflow change slice | conclusion about the owned outcome and checked consequence, followed by an optional `WORKFLOW_CHANGE_PACKET` factual tail |
| Workflow Reviewer | independent review of one coherent integrated batch | conclusion and advisory disposition for WDM, followed by optional findings evidence; no source edits or acceptance |
| Code Project Manager (CPM) | code, runtime, technical acceptance and project-operation records | code/runtime/review artifacts plus CPM-owned mechanical receipts |
| Independent Research Explorer | advisory research direction, methodology and research workspace | named research handoff; no workflow authority |
| Agentify Transport child | batch-scoped transport mechanics plus ephemeral task-owned tab lifecycle in its requester-assigned workspace; WDM may parent only an exact workflow-acceptance smoke batch | raw transport result for CPM or Explorer, or direct smoke-test evidence for WDM |
| External Pro | bounded independent scientific judgment | exact review result within the submitted question boundary |

The stable CPM mechanical interface is a CPM-only child boundary:
`hmasd-cpm-mechanical` receives one self-contained natural-language mechanical
brief plus one exact temporary `CPM_MECHANICAL_TASK_ASSIGNMENT`
(`spec_path|result_path`). The brief supplies purpose, consumers, protected
meaning, permitted observation/recovery and completion evidence; the spec is a
deterministic execution anchor. The child returns a natural-language mechanical
conclusion followed by temporary `CPM_MECHANICAL_TASK_RESULT`
(`status|result_path|error`) anchors. It is silent until its native terminal
return and writes only assignment-named temporary outputs. CPM retains
sufficiency judgment, finalization, technical acceptance, source/Git and
canonical-state ownership; the child has no experiment, readiness, Agentify,
science, Git or acceptance authority. Activation requires a fresh profile
reload and has no active research-state effect.

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

The Explorer mechanical child is a separate, read-only context-isolation
capability for literal-fact organization. It receives only named frozen
materials, returns a conclusion-first native response and leaves dispatch
economics and semantic sufficiency with Explorer; it is not a scientific
consultant, campaign phase, roster member or acceptance owner. No result file
or new durable or temporary workspace is part of this boundary, and the CPM
mechanical lane remains isolated.

```text
explorer_mechanical_child=hmasd-explorer-mechanical
explorer_mechanical_parent=independent_research_explorer
explorer_mechanical_assignment=native_self_contained_natural_language
explorer_mechanical_result=native_conclusion_first_response
explorer_mechanical_write_scope=none
explorer_mechanical_scientific_authority=none
explorer_mechanical_technical_acceptance_authority=none
explorer_mechanical_cpm_isolation=separate_parent_task_and_state
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
Profile, Role charter and assignment-named references. Child output begins with
a natural-language conclusion and may append a compact factual packet or
receipt tail. It flows back to the parent as advisory, operational or
mechanical evidence; it never grants child design, routing, Git or acceptance
authority. CPM and Explorer remain separate owner lanes. CPM may invoke its
mechanical child through the exact file-only assignment/result boundary; the
conclusion and temporary receipt return to CPM for sufficiency judgment,
finalization and acceptance. The registered Agentify transport child remains a
requester-owned batch capability rather than a separate owner lane; its full
answer, conversation evidence and conclusion return to the requester. The
requester context brief freezes new-versus-exact-continuation, independence and
permitted concurrency. The transport child observes provider-native
conversation identity and realizes explicit intent while owning only ephemeral
task-created tab lifecycle; it does not choose same-direction, independence,
contamination or later-reuse meaning. Tabs are temporary containers rather than
conversation memory or shared persistent state, and multiple requester-
authorized Pro conversations may coexist. The child closes only tabs it created
after full response capture and with no active generation, preserves
default/pre-existing/unowned/active tabs, and returns conversation URLs to the
requester for owner-decided later continuation. WDM does not absorb CPM/Explorer
live review traffic or results. External Pro remains a separate scientific lane.

The Explorer↔CPM direction-local context binding is defined once by
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. Explorer and CPM use
one primary selected direction's smallest canonical context, add only the
smallest set of material relationship edges, and mirror the binding in the
conclusion-first reverse result or Codex-native fallback. An explicitly
multi-direction user question may name several directions without authorizing
portfolio preload. Portfolio/index/README/continuity surfaces remain
pointer-only; a missing binding gets one semantic clarification while
unrelated work continues rather than a new workflow state.

The Explorer mechanical dependency is:

```text
Explorer task model + named frozen materials
        -> hmasd-explorer-mechanical
        -> literal-fact organization conclusion
        -> Explorer semantic sufficiency/intake
```

This dependency carries no scientific evidence vote, roster or barrier and
does not allow the child to read CPM assignments, workspaces or acceptance
state.

Canonical research campaigns retain their exact ordered phase rosters and
barriers. Adaptive scientific questions are a separate prospective capability:
a singleton has no global barrier, while an exact joint roster merges locally
only when every named answer is necessary to one Explorer decision. The matched
research child remains a read-only consultant; Explorer is the sole research
writer and synthesis owner.
This capability adds no dispatcher, queue, registry, monitor, fixed panel or
new acceptance owner.

```text
CPM task model -> hmasd-cpm-mechanical -> conclusion + CPM_MECHANICAL_TASK_RESULT anchors -> CPM sufficiency/finalization/technical acceptance
```

```text
CPM accepted brief + Explorer exact question -> matched read-only research child -> advisory answer -> Explorer synthesis
```

```text
user-confirmed plan
        ↓
WDM assignment → Auditor conclusion/observations (when needed)
        ↓
frozen owned slice → Implementer conclusion + factual tail
        ↓
coherent integrated batch → one Reviewer conclusion/report
        ↓
WDM semantic integration, acceptance and Git
```

The arrows describe dependency and evidence flow, not a required state machine.
Parallel Implementers are permitted only for disjoint owned path families.

The stable assignment dependency is
`parent task model -> hmasd-writing-agent-assignments Skill -> self-contained
assignment -> child judgment/result`. This is context and evidence direction,
not a state machine, queue or admission gate.

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
named collaborative, assignment-writing and workflow-change Skills. It expands
only to the interfaces needed for the confirmed slice.

A Workflow Auditor, Implementer or Reviewer starts with its exact assignment,
registered Profile, named Role and only assignment-named files. A child does
not reconstruct history or load unrelated current work. CPM and Explorer each
request the Agentify transport child through its file-only assignment; the
child follows its registered profile, role and Skill without a persistent task
lane. CPM's mechanical child likewise receives only the exact task spec and
result locator named by CPM; it does not load research, readiness, experiment
or workflow history. Explorer's mechanical child receives only its
self-contained assignment and named frozen materials; it has no result file or
workspace and does not load CPM state. External Pro follows its own router
lane and owner contract. The map is an orientation aid, not a reason to load
every document.

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

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
| Code Project Manager (CPM) | active engineering/runtime orchestrator for code, runtime, technical acceptance and project-operation records | decomposed implementation assignments, code/runtime/review artifacts and CPM-owned mechanical receipts |
| Independent Research Explorer | active scientific/research orchestrator for direction, methodology and research workspace | decomposed research assignments, advisory portfolio/local-research comparisons, intakes and decisions |
| Agentify Transport child | requester-assigned batch transport mechanics; WDM may parent only an exact workflow-acceptance smoke batch | raw transport result for CPM or Explorer, or direct smoke-test evidence for WDM |
| External Pro | bounded independent scientific judgment | exact review result within the submitted question boundary |

CPM-mechanical and Explorer-mechanical wire locators live in
`docs/project/SESSION_WORKSPACE_CONTRACT.md`; their owner Roles retain all
authority and semantic sufficiency decisions.

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

## Persistent owner/orchestrator edge

Explorer and CPM are active owners/orchestrators, not passive relays or
schedulers. They decompose work and delegate bounded detail, synthesize
results, retain owner decisions, and continue unrelated safe work while
children run. The root Explorer owns cross-direction advisory portfolio
comparison; CPM retains architecture, runtime admission, integration and
technical acceptance. Explorer outputs remain advisory portfolio/local-research
comparisons, intakes and decisions. Formal/project canonical science remains
with the user/External Pro contract. Exact assignment, child-lane, waiting and
recovery mechanics remain in the owner Roles and Skills; this paragraph is
orientation only.

## Dependency direction

WDM depends on the stable contracts named by the router. A child depends only on
its self-contained assignment, registered Profile, Role charter and
assignment-named references. Child output flows to the parent as advisory or
mechanical evidence and never grants design, routing, Git or acceptance
authority. CPM and Explorer remain separate owner lanes; Agentify transport is
requester-owned and WDM does not absorb their live review traffic. File/native
wire locators are defined by `docs/project/SESSION_WORKSPACE_CONTRACT.md`.

The Explorer↔CPM direction-local context binding is defined once by
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. Explorer and CPM use
one primary selected direction's smallest canonical context, add only the
smallest set of material relationship edges, and mirror the binding in the
conclusion-first reverse result or Codex-native fallback. An explicitly
multi-direction user question may name several directions without authorizing
portfolio preload. That direction-local handoff boundary is distinct from the
root Explorer's internal cross-direction advisory portfolio comparison.
Portfolio/index/README/continuity surfaces remain
pointer-only; a missing binding gets one semantic clarification while
unrelated work continues rather than a new workflow state.
The same contract is the single source for the human-readable action-bearing
brief/result minimum, parked-versus-pending/retired dispositions and the
Explorer-local Direction Action Map. This map remains an owner-local continuity
view, not a machine schema, queue, scheduler, runtime-admission or acceptance
source; this orientation document does not duplicate it.

For result-bearing experiments, Explorer owns the scientific active roster,
direction-local predecessor context and advisory per-result local-research
intake;
CPM owns runtime-capacity admission, live process/resource
  observations, isolated execution and per-artifact technical acceptance. A
  handoff may describe prospective runtime class/units in prose, but its A/B/C
  scientific evidence level is independent and CPM never infers runtime class or
  barrier closure from science or `local_research/`. The detailed stateless
  observation, pool, barrier, resource and event-driven continuation rules
  remain only in `parallel-research-workflow.md`; this map keeps the owner-lane
  edge and does not create a shared scheduler, merged acceptance or
  cross-direction barrier. Read-only Explorer science lanes remain independent
  of CPM pool/admission by default; only an exact question depending on an
  unreturned CPM result creates a direction-local science barrier. An exclusive
  formal/heavy run reserves only experiment admission; all non-experiment work
  that does not contend for the observed bottleneck continues.

The Explorer mechanical edge is a native assignment to a literal-fact
organization child; its storage boundary is defined by the Session Contract.

Research and CPM operational dependency details remain in their owner contracts;
this map keeps only the owner-lane edge.

```text
confirmed plan -> frozen owned slice -> integrated batch -> WDM acceptance/Git
```

Ordinary workflow stages are mandatory and parallel-first with dependency order;
dispatch read-only Auditor/Scout concurrently with already-freezable
implementation slices, run disjoint Implementer file families concurrently,
and serialize only actual information dependencies or same-file writers. The
integrated Reviewer follows the complete integrated batch; parallel reviewers
remain limited to genuinely independent questions.

The stable assignment dependency is
`parent task model -> hmasd-writing-agent-assignments Skill -> self-contained
assignment -> child judgment/result`. This is context and evidence direction,
not a state machine, queue or admission gate.

## Delegation orientation

Ordinary workflow changes use the registered Auditor/Scout, Implementer and
integrated Reviewer stages with parallel-first scheduling and dependency order.
WDM's local workflow-file modification is reserved for a direct user
instruction explicitly naming WDM direct modification; generic workflow-change
requests follow the default subagent route. Pure design or authority decisions
without file mutation remain WDM-local. The Roles and Audit Skill own detailed
routing mechanics; serialize only actual information dependencies or same-file
writers, and keep parallel reviewers limited to genuinely independent questions.

## Context loading

`AGENTS.md` owns the lazy trigger table. WDM and each child start with the exact
assignment and Role, then expand only to the owner surface named by the active
interface or status dependency. This map is an orientation aid, not a reason to
load every document.

## Role-based successor continuity

Continuity follows the stable role identity
`session_owner_id=workflow_design_manager`; batch completion is the preferred
rotation boundary. Successor brief storage and reload semantics live in the
Session Workspace Contract and WDM current-work records.

## Event-triggered maintenance

WDM updates this map in the same workflow commit when a stable fact changes:
role ownership or authority, a public interface or dependency direction, the
minimum context-loading boundary, the workflow execution policy, or the
successor-continuity contract. A Reviewer or Auditor reports a conflict; WDM
decides whether it is a stable change and repairs the map when required.

Maintenance is event-triggered only: a stable ownership, interface,
dependency, context-loading, delegation or continuity change may update this
map. No timer, no periodic audit, no freshness checker and no registry drives
updates.
Local wording, a one-off operational event, a temporary tool issue, an ordinary
test adjustment or active task state does not trigger a map update. Detailed
mechanics remain with their existing owner Role, Skill, Profile or test.

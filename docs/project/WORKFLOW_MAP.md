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
| Agentify Transport child | requester-assigned batch transport mechanics; WDM may parent only an exact workflow-acceptance smoke batch | raw transport result for CPM or Explorer, or direct smoke-test evidence for WDM |
| Desktop Research Scheduler | user-owned persistent Desktop lifecycle and resource-conflict routing for same-level ephemeral owner tasks | exact owner thread IDs, binding identity and canonical result locators; no science, code or acceptance |
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
portfolio preload. Portfolio/index/README/continuity surfaces remain
pointer-only; a missing binding gets one semantic clarification while
unrelated work continues rather than a new workflow state. This owner-level
binding is not Scheduler semantic relay or sibling preload.

The Desktop Research Scheduler replaces persistent single Explorer/CPM
coordination with one user-visible persistent Desktop task. It creates
same-level ephemeral owner tasks for Explorer `direction|portfolio` work and
CPM `treatment|integration` work. Owner tasks retain their existing registered
children at `max_depth=1`; the Scheduler is not a registered child, has no
`.codex` profile, and never becomes a science, code, runtime, technical
acceptance, Git or semantic-relay owner.

Each owner assignment remains a self-contained natural-language task model.
The bounded Desktop lifecycle, result locator and ambiguous-action fallback are
defined once by `.agents/skills/hmasd-research-scheduler/SKILL.md`; this map
keeps only the stable owner/task edge and does not repeat command-level
procedure.

Explorer direction-local binding remains an owner concern when it is named by
the assignment; the Scheduler does not preload sibling context or relay its
meaning. Portfolio/index/README/continuity surfaces remain pointer-only.

For result-bearing experiments, Explorer owns the scientific active roster,
direction dependencies, prospective class and per-result intake; CPM owns the
runtime observations, isolated execution and per-artifact technical
acceptance. The Scheduler carries only the resource-conflict pointer; the
resource policy is defined once by
`.agents/skills/hmasd-research-scheduler/SKILL.md`. This edge creates no merged
acceptance or cross-direction semantic barrier.

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

The Desktop Research Scheduler starts with its user assignment and Scheduler
Role, then expands lazily only to the Session Workspace Contract, owner-role
contract or resource reference named by that assignment. It never preloads
Explorer, CPM or sibling context.

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

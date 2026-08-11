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
| Root | user communication, task routing, cross-owner relay, lifecycle, Root-managed worktree helper/receipt control and accepted physical writes, including separately authorized final Git integration; no scientific comparison/intake or domain acceptance | owner-routed assignments/results, lifecycle receipts, accepted proposals and accepted-path integration evidence |
| Workflow Design Manager (WDM) | user-confirmed workflow design, control-plane modification through assigned leaves, exact-slice acceptance and later integrated-union semantic acceptance | confirmed plan, self-contained child assignment, candidate-ready slice packets, convergence change packet and successor brief |
| Workflow Auditor | read-only local reconnaissance for an assigned workflow surface | conclusion about bounded facts/conflicts, followed by optional dependency evidence |
| Workflow Implementer | one frozen non-overlapping workflow change slice | conclusion about the owned outcome and checked consequence, followed by an optional `WORKFLOW_CHANGE_PACKET` factual tail |
| Workflow Reviewer | independent review of one coherent integrated batch | conclusion and advisory disposition for WDM, followed by optional findings evidence; no source edits or acceptance |
| Code Project Manager (CPM) | active engineering/runtime orchestrator for code, runtime, technical acceptance and project-operation records | decomposed implementation assignments, code/runtime/review artifacts and CPM-owned mechanical receipts |
| Independent Research Explorer L1 | read-only scientific/research orchestrator for direction, methodology and research workspace; owns decomposition, selection, dependency/concurrency, science synthesis/continuity semantics, cross-direction comparison, advisory portfolio/local-research semantic intake and sole advisory decision authoring | semantically authored complete advisory decisions/handoffs and accepted proposals returned through Root |
| CPM Agentify Transport child (`hmasd-cpm-agentify-transport`) | requester-assigned batch transport mechanics under CPM | raw transport result for CPM |
| Explorer Agentify Transport child (`hmasd-explorer-agentify-transport`) | requester-assigned batch transport mechanics under Explorer | raw transport result for Explorer |
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

## Scope-keyed L1 multiplicity

Owner Roles define their own scope-key field, including any future CPM or
research-scope detail; this map does not name those owner-specific fields. In
one Root tree, `(role, role-defined scope key)` is unique. A scope key locates
semantic ownership and permitted concurrency only: it is not a ticket,
session/thread identity, scheduler, queue, ledger, admission token or
continuity mechanism. WDM uses `workflow_scope_key`; multiple WDM L1s are
valid only for disjoint frozen workflow scopes. A shared writable path or a
still-unfrozen semantic contract is a dependency and is serialized. The
Session Workspace Contract is the defining source for these mechanics.

## Parallel WDM candidate and convergence edge

Root dispatches each WDM with caller action `fork_turns=1` for background
context only. Each WDM dispatches disjoint registered Implementers with
explicit `fork_turns=none`. Root alone controls provisioning, lifecycle
records, integration, release/retention, Git, user contact and cross-owner
relay, and completion order does not establish priority. One writable L1
assignment has one Root-managed worktree; the Session Workspace Contract
defines the shared-L1 conditions, forbids L2 worktree lifecycle control, and
requires a new L1 for an independent candidate or release lifecycle.
Concurrent WDM/CPM L1s and later integration/convergence use separate
worktrees. Each WDM accepts its exact slice and returns a candidate-ready packet;
Root records and integrates the candidate set. A fresh convergence WDM then
works on the exact integrated union, arranges integrated advisory review and
owns union semantic acceptance. Reviewer output is advisory and never accepts.
This map remains an orientation pointer; the Session Workspace Contract is
the single mechanics source and no completed integration or convergence is
implied here.

Any writer that may touch a tracked path, including a WDM workflow writer, uses
a Root-provisioned managed worktree. Read-only, ignored-only and temporary-only
assignments are exempt; mixed tracked and ignored writes remain tracked-writer
assignments. Root alone invokes the helper, owns the lifecycle receipt, applies
accepted paths and releases or retains the worktree. At most one nonterminal
receipt is active per assignment; a local failure remains nonterminal for Root
retry or parking while unrelated work continues. Legacy worktrees stay isolated
and untouched. Children never invoke the helper or run raw child `git worktree`
operations. The Session Workspace Contract is the defining workspace source;
this paragraph is orientation only.

## Persistent owner/orchestrator edge

Explorer and CPM are active owners/orchestrators, not passive relays or
schedulers. They decompose work and delegate bounded detail, synthesize
results, retain owner decisions, and continue unrelated safe work while
children run. Independent Research Explorer L1 alone owns cross-direction
advisory portfolio comparison; CPM retains architecture, runtime admission,
integration and technical acceptance. Explorer outputs remain advisory
portfolio/local-research comparisons, intakes and decisions. Explorer L1 is
read-only and semantically authors the exact advisory decision/handoff; Root
owns user communication, cross-owner relay, lifecycle and accepted physical
writes, but has no scientific comparison/intake authority. Formal/project
canonical science remains with the user/External Pro contract. Exact
assignment, child-lane, waiting and recovery mechanics remain in the owner
Roles and Skills; this paragraph is orientation only.

## Dependency direction

WDM depends on the stable contracts named by the router. A child depends only on
its self-contained assignment, registered Profile, Role charter and
assignment-named references. Child output flows to the parent as advisory or
mechanical evidence and never grants design, routing, Git or acceptance
authority. CPM and Explorer remain separate owner lanes. Cross-owner requests
and results use the Root relay: Explorer -> Root -> CPM and CPM -> Root ->
Explorer; no direct sibling channel is implied. Agentify transport is
parent-specific: CPM uses `hmasd-cpm-agentify-transport` and Explorer's only
external-review transport is `hmasd-explorer-agentify-transport`, with its raw
result returning to Explorer before any Explorer -> Root relay. WDM does not
parent transport and does not absorb their live review traffic. File/native wire
locators are defined by `docs/project/SESSION_WORKSPACE_CONTRACT.md`.

The Root-routed Explorer -> Root -> CPM direction-local context binding is defined once by
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. Explorer and CPM use
one primary selected direction's smallest canonical context, add only the
smallest set of material relationship edges, and mirror the binding in the
conclusion-first reverse result or Codex-native fallback returned through Root. An explicitly
multi-direction user question may name several directions without authorizing
portfolio preload. That direction-local handoff boundary is distinct from
Independent Research Explorer L1's internal cross-direction advisory portfolio
comparison; Root performs no scientific comparison or intake.
Portfolio/index/README/continuity surfaces remain
pointer-only; a missing binding gets one semantic clarification while
unrelated work continues rather than a new workflow state.
The same contract is the single source for the human-readable action-bearing
brief/result minimum, parked-versus-pending/retired dispositions and the
Explorer-local Direction Action Map. This map remains an owner-local continuity
view, not a machine schema, queue, scheduler, runtime-admission or acceptance
source; this orientation document does not duplicate it.

The stable reverse-intake direction is a small Explorer-authored semantic delta
to an assignment-specific temporary patch. The Research Artifact Writer is an
exact-payload mechanical writer; Root retains canonical bytes and owns the
path/revision check and exact-copy installation; Explorer full-reads and owns
semantic acceptance of the candidate. The full map is not transported through
messages or split/encoded payloads. Detailed patch, clarification and event
classification rules remain only in
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`; WDM owns the interface
shape and does not own artifact integrity, map meaning or Explorer acceptance.

For result-bearing experiments, Explorer L1 owns the scientific active roster,
direction-local predecessor context, advisory per-result local-research
semantic intake and sole advisory decision authoring; Explorer L1 remains
read-only and returns complete accepted proposals to Root;
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
organization child; it never replaces Explorer L1 comparison, semantic intake
or advisory decision authority, and its storage boundary is defined by the
Session Contract.

Research and CPM operational dependency details remain in their owner contracts;
this map keeps only the owner-lane edge.

```text
confirmed plan -> disjoint frozen WDM slices -> candidate-ready packets -> Root records/integrates candidate set -> fresh convergence WDM on exact integrated union -> integrated advisory review -> WDM union acceptance -> Root accepted-path Git integration
```

Ordinary workflow stages are mandatory and parallel-first with direct
orchestration and dependency order;
dispatch read-only Auditor/Scout concurrently with already-freezable
implementation slices, run disjoint Implementer file families concurrently,
and serialize only actual information dependencies or same-file writers. The
integrated Reviewer follows the complete integrated union; parallel reviewers
remain limited to genuinely independent questions.

The stable assignment dependency is
`parent task model -> hmasd-writing-agent-assignments Skill -> self-contained
assignment -> child judgment/result`. This is context and evidence direction,
not a state machine, queue or admission gate.

## Delegation orientation

Ordinary workflow changes use the registered Auditor/Scout, Implementer and
integrated Reviewer stages with parallel-first dispatch and dependency order.
Workflow-file changes are performed by assigned Workflow Implementer leaves;
each WDM accepts its exact slice, while a fresh convergence WDM reviews and
semantically accepts the integrated union; Root performs any separately
authorized accepted-path Git mechanics. Pure design or
authority decisions without file mutation remain WDM-local. The Roles and
Audit Skill own detailed routing mechanics; serialize only actual information
dependencies or same-file writers, and keep parallel reviewers limited to
genuinely independent questions.

## Context loading

`AGENTS.md` owns the lazy trigger table and
`docs/project/L1_STARTUP_CONTEXT.md` is the concise pointer index for WDM, CPM
and Explorer default core inputs and action triggers. Each L1 starts with the
exact assignment, registered Profile and Role, then expands only to the Skill
or owner surface named by the active interface or status dependency. The index
and this map are orientation aids, not reasons to load every document.

## Role-based successor continuity

Continuity follows the stable role identity
`session_owner_id=workflow_design_manager`; batch completion is the preferred
rotation boundary. `workflow_scope_key` locates a WDM's semantic scope but is
not a continuity mechanism. Successor brief storage and reload semantics live
in the Session Workspace Contract and WDM current-work records. A fresh Root
task reloads canonical continuity; no active-instance registry is implied.

## Event-triggered maintenance

When a stable fact changes—role ownership or authority, a public interface or
dependency direction, the minimum context-loading boundary, the workflow
execution policy, or the successor-continuity contract—WDM assigns the map
change to a Workflow Implementer and semantically accepts the result. Root
performs any separately authorized accepted-path Git mechanics. A Reviewer or
Auditor reports a conflict; WDM decides whether it is a stable change and
requests the repair when required.

Maintenance is event-triggered only: a stable ownership, interface,
dependency, context-loading, delegation or continuity change may update this
map. No timer, no periodic audit, no freshness checker and no registry drives
updates.
Local wording, a one-off operational event, a temporary tool issue, an ordinary
test adjustment or active task state does not trigger a map update. Detailed
mechanics remain with their existing owner Role, Skill, Profile or test.

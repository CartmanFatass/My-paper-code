# HMASD Workflow Map

```text
document_kind=stable_workflow_orientation
owner_role=workflow_design_manager
scope=workflow_control_plane_abstraction
root_macro_portfolio_owner=Root
em_scope=direction:<id>
cm_scope=direction:<id>|shared:<component>
cm_slice_acceptance=final_for_slice
root_union_action=mechanical_integrate_and_run_Tests_Static
semantic_conflict_route=owning_CM_or_temporary_named_shared_CM
scope_atom=[a-z0-9][a-z0-9._-]{0,63}
scope_reject=empty|extra_colon|separators|whitespace|..
```

This map is the WDM's compact orientation for workflow-control-plane design.
It describes stable ownership, interfaces, dependency direction and context
loading. It is not an authority source, task state, chronological log,
exhaustive registry or procedure copy.

## Owner roles and stable outputs

| Owner | Stable responsibility | Interface handed onward |
|---|---|---|
| Root | user communication, task routing, cross-owner relay, lifecycle, Root-managed worktree helper/receipt control and accepted physical writes, including separately authorized final Git integration; advisory macro/portfolio science (cross-direction comparison, ranking, pause/continue, dependencies and complete-map acceptance); no direction research execution, code technical acceptance or automatic formal/project-canonical science | owner-routed assignments/results, lifecycle receipts, accepted proposals and accepted-path integration evidence |
| Workflow Design Manager (WDM) | user-confirmed workflow design, control-plane modification through assigned leaves, exact-slice acceptance and later integrated-union semantic acceptance | confirmed plan, self-contained child assignment, candidate-ready slice packets, convergence change packet and successor brief |
| Workflow Auditor | read-only local reconnaissance for an assigned workflow surface | conclusion about bounded facts/conflicts, followed by optional dependency evidence |
| Workflow Implementer | one frozen non-overlapping workflow change slice | conclusion about the owned outcome and checked consequence, followed by an optional `WORKFLOW_CHANGE_PACKET` factual tail |
| Workflow Reviewer | independent review of one coherent integrated batch | conclusion and advisory disposition for WDM, followed by optional findings evidence; no source edits or acceptance |
| Code Project Manager (CPM) | active engineering/runtime orchestrator for code, runtime, technical acceptance and project-operation records, scoped only to `direction:<id>` or `shared:<component>` | decomposed implementation assignments, code/runtime/review artifacts and CPM-owned mechanical receipts |
| Independent Research Explorer L1 | read-only research orchestrator for exactly one `direction:<id>`; owns direction research execution and direction-local synthesis/continuity semantics, but no portfolio L1 or cross-direction decision authoring | direction-scoped research evidence and accepted proposals returned through Root |
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

## Validation and progress pointers

`docs/project/SESSION_WORKSPACE_CONTRACT.md` is the defining source for the
three validation layers, the exact five WDM progress observations, failure
classification, Windows basetemp and one-reviewer policy. This map only
orients the edge: writers cover `slice_local`, WDM owns one
`integration_cross_slice` run after writes freeze, and Root owns the pending
`runtime_fresh_smoke_after_root_integration_reload`. The Audit Skill carries
the normal path; the Roles carry capability and authority. Root's useful-work
L1-start guidance and the `max_threads=20` agent ceiling do not create a quota,
pool, scheduler, admission gate or runtime authorization. Progress observations
return through the current Root task/report boundary rather than a persistent
store, callback, queue or ledger.

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

The direction owner key is exactly `direction:<id>` for EM. CM accepts only
`direction:<id>` or `shared:<component>`. The `<id>` and `<component>` atom
must match `[a-z0-9][a-z0-9._-]{0,63}`; empty values, extra colons, separators,
whitespace and `..` are rejected. Portfolio, integration and all-shared scope
families are not valid owner scopes; Root is the sole macro/portfolio owner.

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
The converged package uses exactly one integrated Reviewer after test evidence
is frozen; that Reviewer is read-only/advisory and receives no second pass.
This explicit WDM workflow convergence remains unchanged and is distinct from
domain ownership: no standing/fresh domain-convergence lane or extra union Reviewer is
created for direction/shared code slices.
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
schedulers. Explorer is scoped to one `direction:<id>` and executes and
synthesizes that direction only. CPM is scoped to `direction:<id>` or
`shared:<component>` and retains architecture, scope-local runtime judgment,
integration and technical acceptance for its slice. Root owns macro/portfolio
comparison, ranking, pause/continue, dependencies and complete-map acceptance;
Root mechanically integrates accepted direction/shared slices and runs union
Tests/Static. A semantic conflict returns to its owning CM(s), or to a
temporary named shared CM. There is no standalone portfolio or integration
owner, no standing/fresh domain-convergence lane and no extra union Reviewer. Formal/project
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
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. EM and CPM use one
primary selected direction's smallest canonical context, add only the smallest
set of material relationship edges, and mirror the binding in the
conclusion-first reverse result or Codex-native fallback returned through Root.
For an explicitly multi-direction user question, Root splits the request into
separate exact `direction:<id>` assignments before owner work; no one CM
handles a multi-direction request or result. Each CM result binds one
`direction:<id>` or one named `shared:<component>`, and cross-direction
relations return to Root. This direction-local handoff boundary is distinct
from Root's macro/portfolio advisory surface; Root performs the cross-direction
comparison, ranking, pause/continue, dependency and complete-map decisions.
The EM direction lane performs no portfolio comparison or intake.
Portfolio/index/README/continuity surfaces remain
pointer-only; a missing binding gets one semantic clarification while
unrelated work continues rather than a new workflow state.
The same contract is the single source for the human-readable action-bearing
brief/result minimum, parked-versus-pending/retired dispositions and the
Explorer-local Direction Action Map. This map remains an owner-local continuity
view, not a machine schema, queue, scheduler, runtime-admission or acceptance
source; this orientation document does not duplicate it.

The stable reverse-intake direction is a small EM-authored semantic delta to an
assignment-specific temporary patch. EM authors and accepts only its own exact
`direction:<id>` row/delta; Root alone accepts the complete Direction Action
Map, cross-direction relations, unselected rows, table/map consistency and
portfolio continuity after the affected EM input. The Research Artifact Writer
is an exact-payload mechanical writer; Root retains canonical bytes and owns
the path/revision check and exact-copy installation after EM row/delta
acceptance. The full map is not transported through messages or split/encoded
payloads. Detailed patch, clarification and event classification rules remain only in
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`; WDM owns the interface
shape and does not own artifact integrity, map meaning or Explorer acceptance.

For result-bearing experiments, Explorer L1 owns the scientific active roster,
direction-local predecessor context, advisory per-result local-research
semantic intake and sole advisory decision authoring; Explorer L1 remains
read-only and returns complete accepted proposals to Root;
CPM owns isolated execution and per-artifact technical acceptance, making
scope-local technical/runtime judgments from Root's live process, CPU, memory
and concrete resource-conflict observations. The current runtime contract and
authorization boundary are defined by `.agents/roles/CODE_PROJECT_MANAGER.md`
and `.agents/skills/hmasd-agile-research-development/SKILL.md`; this map does
not duplicate their no-unit-accounting, no-pool, no-reservation or
no-admission-ledger mechanics, or their high-cost runtime authorization rule.
`max_threads=20` denotes agent-tree concurrency only and never runtime
authorization. Read-only Explorer science lanes remain independent of CPM
execution by default; only an exact question depending on an unreturned CPM
result creates a direction-local science barrier. Runtime observation,
authorization and continuation details remain in those canonical owner
contracts.

The Explorer mechanical edge is a native assignment to a literal-fact
organization child; it never replaces Explorer L1 comparison, semantic intake
or advisory decision authority, and its storage boundary is defined by the
Session Contract.

Research and CPM operational dependency details remain in their owner contracts;
this map keeps only the owner-lane edge.

```text
confirmed plan -> disjoint frozen WDM slices -> candidate-ready packets -> Root records/integrates candidate set -> fresh convergence WDM on exact integrated union -> integrated advisory review -> WDM union acceptance -> Root accepted-path Git integration
```

High-risk workflow work uses the registered Auditor, Implementer and integrated
Reviewer with parallel-first direct orchestration and dependency order; a
low-risk one-file wording or test-only slice may skip a new Auditor only when
WDM records a concrete rationale. Ordinary workflow work remains
parallel-first with direct orchestration and dependency order;
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

The Audit Skill carries the risk-tiered Auditor choice; registered Implementer
and integrated Reviewer work use parallel-first dispatch and dependency order.
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
and this map are orientation aids, not reasons to load every document. Root
uses compact direction packets and lazy pointers for macro/portfolio work; EM
loads one named direction, and CM loads only direct direction/shared
interfaces. Neither owner preloads a portfolio or unrelated project/runtime
corpus.

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

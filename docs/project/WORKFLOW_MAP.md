# HMASD Workflow Map

```text
document_kind=stable_workflow_orientation
owner_role=workflow_design_manager
scope=workflow_control_plane_abstraction
control_plane_document_routes=docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md
control_plane_document_routes_not=task_state|history|hash|receipt|queue|admission|acceptance
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
loading, while the route table supplies trigger-to-document lookup. It is not
an authority source, task state, chronological log, exhaustive registry or
procedure copy; the route table is likewise never task state, history, a hash,
receipt, queue, admission or acceptance data.

## Owner roles and stable outputs

| Owner | Stable responsibility | Interface handed onward |
|---|---|---|
| Root | user communication, task routing, cross-owner relay, lifecycle, Root-managed worktree helper/receipt control and accepted physical writes, including separately authorized final Git integration; advisory macro/portfolio science (cross-direction comparison, ranking, pause/continue, dependencies and complete-map acceptance); no direction research execution, code technical acceptance or automatic formal/project-canonical science | owner-routed assignments/results, lifecycle receipts, accepted proposals and accepted-path integration evidence |
| Workflow Design Manager (WDM) | Root-explicit workflow plan-only response or plan+execute control-plane modification within its authorized boundary, singleton frozen-package acceptance, and conditional true multi-candidate union acceptance | detailed plan or self-contained child assignment, package/conditional-convergence packets and successor brief |
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

The stable dispatch edge is `explicit user request -> Root-compiled
natural-language assignment -> plan-only result or WDM plan+execute -> child
judgment/result`. It is not a confirmation token, second gate or state machine.
Within a plan+execute boundary owners refine reversible mechanics automatically;
only material drift returns to Root.

## Validation and progress pointers

`docs/project/SESSION_WORKSPACE_CONTRACT.md` is the defining source for
validation, progress, worktree, lifecycle and review mechanics. The route-table
row for Session/worktree/lifecycle is the lazy lookup boundary, and the Audit
Skill is the normal risk/delegation path; this map records no procedure or
progress state.

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

The Session Workspace Contract defines the mechanics. A singleton package is
one writable WDM L1's exact final frozen bytes, reviewed once by one advisory
Reviewer before that same WDM accepts it for Root integration. A true union
exists only when Root combines at least two independently reviewed candidates
or the integrated bytes differ from every reviewed package; a fresh convergence
WDM then reviews and accepts that exact union. This map is only the stable
relationship pointer and does not imply integration or convergence.

Independent frozen slices are parallel-first with dependency-only serialization
for same-path or unfrozen-contract conflicts; detailed mechanics live in the
Audit Skill and Session Workspace Contract.

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

The Session Contract, route table and Audit Skill are the defining pointers for
workflow risk, causal evidence, delegation, worktree, validation and review.
For a clear bounded route, WDM records the Session field
`workflow_auditor_skip_evidence`; missing, ambiguous, conflicting or
authority-crossing routes remain Auditor-required. The stable assignment edge
is `parent task model -> hmasd-writing-agent-assignments Skill -> self-contained
assignment -> child judgment/result`; this is context and evidence direction,
not a state machine, queue or admission gate.

## Delegation orientation

The route-table row for risk/delegation/review points to the Audit Skill.
Roles and Audit Skill own detailed routing mechanics; this map keeps only the
stable owner/dependency edge and the singleton-versus-true-union relationship
above. Pure design or authority decisions without file mutation remain WDM-local.

## Context loading

`AGENTS.md` owns the lazy trigger table and
`docs/project/L1_STARTUP_CONTEXT.md` is the concise pointer index for owner
inputs and action triggers. The Session Contract, Profiles, Roles and active
route define exact loading boundaries; this map is an orientation aid, not a
reason to preload unrelated documents.

The route-table row for L1 startup/context is the lazy load boundary; it does
not replace the defining source or create state.

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

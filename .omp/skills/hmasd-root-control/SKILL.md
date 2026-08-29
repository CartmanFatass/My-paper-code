---
name: hmasd-root-control
description: Reconcile, prioritize, and advance the durable HMASD workflow from the Root session.
---

# HMASD Root Control

## Purpose

Keep one user-facing Root session aligned with the durable Portfolio, direction,
run, external-operation, runtime, worktree, and Git authorities. Root directly
owns routing, runtime reconciliation, the Portfolio subflow, lifecycle and
capacity adoption, BrowserTransport serialization, external archive validation,
shared Git integration, recovery, user boundaries, and final delivery. There is
no Portfolio agent or Portfolio manager session: Root performs that judgment,
while `PORTFOLIO.md` remains its durable scientific authority and the registry
remains lifecycle/dependency authority.

Root coordinates role work without collapsing its meanings. EM owns science, CM
owns contract realization and technical acceptance, BrowserTransport owns
strict transport facts, and an Experiment Operator owns one exact
result-bearing command. None of those facts silently performs a Portfolio
choice.

## Inputs

- `docs/research/portfolio/PORTFOLIO.md` as the persistent scientific goal,
  cross-direction synthesis, current allocation, and lifecycle-reason authority.
- `docs/research/portfolio/workflow/registry.json` as the four-state lifecycle
  and dependency authority, updated only through `scripts/hmasd_state.py` with
  expected-revision/CAS.
- The direct user's fixed considered set, allocation question, authorized
  capacity, PAUSE/RESUME state, and explicit decision boundaries.
- Candidate `DIRECTION.md` references and SHA-256 values; standard direction
  artifacts under `evidence/`, `external/`, `workflow/research/`, and
  `workflow/engineering/`; direction research and engineering states; and
  common v1 EM/CM result envelopes.
- `.omp/runtime/agents.json` and `.omp/runtime/worktrees.json` when present,
  plus current OMP logical identities, generations, assignments, and Hub jobs.
- Terminal EM, CM, BrowserTransport, and Run facts; process exits; local run
  manifests; Agentify operation/archive references; and exact `omp/workflow`
  Git observations.
- Exact proposed-command estimates when resource cost affects scheduling:
  absolute peak memory, wall-clock time, storage, accelerator needs, and current
  workstation capacity. A relative multiplier alone is not an estimate.
- The previous generation, material transition, or startup/compaction boundary.

Tracked references are repository-relative POSIX paths with no `..`, symlink,
or absolute prefix. Concrete handles, PIDs, absolute worktree paths, and local
tab mappings stay in ignored runtime state.

## Bounded cycle

### 1. Reconcile the OMP substrate

On start, resume, or detected compaction, recover the Root goal from
`PORTFOLIO.md`, never from a prompt summary or Dashboard. Mechanically validate
the registry and referenced paths/hashes. Reconcile direction state, OMP runtime
maps, Hub jobs, worktrees, manifests, external-operation references, exact
archive bytes, and Git once. Classify each observation as current, stale,
missing, conflicted, or materially changed. The Dashboard and Advisor are
read-only evidence and never state or permission.

Reuse a compatible `EM-<direction>` or `CM-<direction>` logical identity only
when its role, direction, generation, assignment-owned paths, and frozen
checkpoint remain compatible. Hub carries compatible material updates; a
materially changed assignment gets a new bounded session rather than being
silently broadened.

### 2. Execute the Portfolio decision frame

Before the first lifecycle, capacity, refill, or direction-dispatch Effect for a
decision, Root states this compact frame in the current OMP history:

- **Fixed user considered set:** the allocation question, every direction, and
  capacity fixed by direct user authority. Only direct user authority changes
  this set; `RESUME`, a recommendation, free capacity, or a later draft does not.
- **Live investments and Effects:** unfinished direction work, retained
  scientific questions, exact reentries, and already-committed Effects that
  constrain allocation.
- **Evidence boundary:** valid comparative scientific evidence, excluded
  transport/engineering/measurement facts, unresolved uncertainty, and the
  supported claim ceiling.
- **Counterfactual allocation:** the strongest real alternative and why the
  proposed allocation is better on decision leverage, independence, cost,
  reversibility, and stop rule.
- **Next observation:** the smallest discriminator that could change allocation,
  its owner, and the Portfolio action each outcome would change.

This frame is a decision discipline, not a new ledger, scheduler, score, or
approval layer. Compare the entire fixed set qualitatively on complementarity,
substitution, common failure risk, decision leverage, cost/stage, reversibility,
stop rule, option value, and independent validation. Do not invent numeric VOI,
success probabilities, votes, Elo, or composite scores.

### 3. Consume terminal facts without conflation

Consume each terminal fact immediately and preserve its namespace:

- An EM result supplies scientific status, bounded claim, decision impact,
  evidence references, and a lifecycle recommendation. An EM recommendation is
  evidence, not a Portfolio action; Root makes the comparative decision.
- A CM result supplies its independent `engineering_status`,
  `observation_status`, and `verification_status`, plus durable result and Git
  references. Root routes a result requiring scientific interpretation back to
  EM. Engineering success or failure is not science or lifecycle.
- A BrowserTransport result supplies one strict operation's provider,
  conversation, archive, commitment, and transport state. Transport success,
  failure, mismatch, loss, or waiver is not science or lifecycle.
- A Run result supplies the observed state of one exact result-bearing command.
  Launch, process, manifest, measurement, and terminal facts are not scientific
  interpretation or lifecycle.
- OMP session liveness, Hub status, runtime-map entries, worktree state, commit,
  conflict, and push state are routing or Git facts. Transport, engineering,
  Run, runtime, and Git facts never become lifecycle or science by inference.

Route each role-owned consequence in the same wake, even while other legs remain
live. A terminal technical leg may release capacity without answering its
scientific investment question.

### 4. Adopt Portfolio actions and lifecycle coherently

For every direction in the fixed considered set, adopt exactly one action:
`NONE`, `ACTIVATE`, `CONTINUE`, `NARROW`, `PARK`, `CLOSE`, `FUSE`, or
`SPINOFF`. One action never implicitly applies to another direction. Adoption
comes from Root's current counterfactual Portfolio judgment, not from copying a
callee's field.

Keep action and durable lifecycle distinct:

- `REGISTERED` is known and eligible with no active investment.
- `ACTIVE` requires a current executable scientific question plus live work or
  one exact operational reentry. An active direction cannot be silently
  starved.
- `PARKED` has no live direction work and preserves its scientific or
  opportunity-cost reason, evidence boundary, and exact
  `reactivation_condition_ref`. `PARKED` is not `CLOSED`.
- `CLOSED` has a terminal investment reason and reopens only through an explicit
  Portfolio decision based on materially new grounds.

Write the considered-set actions, capacity decision, lifecycle reasons, and
cross-direction synthesis coherently to `PORTFOLIO.md`, then replace the
registry through the state CLI with expected revision and writer `Portfolio`
before dispatching work that depends on the change. `Portfolio` names the
durable authority, not an agent. `PARK` moves a direction to `PARKED`; an
explicit qualifying reactivation moves it to `ACTIVE`, never through an
implicit runtime event.

### 5. Refill active allocation

Portfolio is an active allocator, not a passive all-terminal join. After each
terminal EM, CM, Transport, or Run fact, recompute the number of live advancing
direction investments. A terminal leg releases its advancing slot even when
other legs remain live.

When control is not `PAUSED` and advancing work is below authorized capacity,
screen the strongest authorized candidates in the fixed considered set. Adopt
any required lifecycle/action update first, then dispatch the best admissible
successor or replacement to an exact idle EM in the same wake; do not wait for
another Root prompt or for all other legs to finish. For `CONTINUE` or `NARROW`,
provide a current executable successor question. For `ACTIVATE`, reactivate or
activate before dispatch. `PARK`, `CLOSE`, `FUSE`, and `SPINOFF` release or
redirect investment according to the adopted action.

Root may wait only when every authorized slot has live work, or no admissible
candidate survives comparison. In the latter case, name the candidates
considered, the evidence excluding them, the strongest counterfactual, and an
exact reentry. If capacity remains unused, explain why leaving it unused is
preferable to the strongest authorized candidate. Never activate weak work only
to meet a quota.

`PAUSE` retains the same assignments and permits non-sending observation needed
to bring already-committed Effects to safe facts, but it blocks active refill,
new direction dispatch, fresh BrowserTransport sends, experiment launches, and
all other new Effects. `RESUME` continues the retained decision and fixed set;
it does not silently authorize a replacement decision. Root does not refill
paused capacity.

### 6. Route role work with OMP envelopes and meaning

Every cross-role dispatch uses OMP `task` or Hub as carrier, an identity,
generation, and assignment envelope, and a meaning-complete natural-language
body containing:

- objective and decision relevance;
- authorities, inputs, and evidence boundary;
- scope, protected non-goals, and preserved semantics;
- requested role work and role-owned judgment;
- authorized Effects and ownership;
- acceptance evidence and stop condition; and
- return route, durable references, and reentry.

Results use the common v1 result envelope. Literal Codex `[WORK]`, `[RESULT]`,
or `[BROWSER WORK]` headings are historical semantic source material only and
never OMP routing authority, identity, or receipt.

Route scientific questions, principle derivation, evidence synthesis, and result
interpretation to `EM`; contract realization, implementation, code repair, code
verification, and resource-estimator construction to `CM`; strict provider work
to `TRANSPORT`; one exact result-bearing command to `EXPERIMENT_OPERATOR`;
integration, lifecycle, routing, and reconciliation to `ROOT`; and genuine
approval/decision boundaries to `USER`. Persist the route in
`next_action.owner`. A runnable handoff is dispatched in the same wake; an
unavailable dependency or capacity becomes exact `waiting_on` state with the
same next owner. Never leave a material transition ownerless or ask CM to derive
scientific authority.

EM material work and CM-result interpretation return to EM. EM sends engineering
needs through Root using the durable
`workflow/research/engineering-request.md` path-plus-SHA reference; Root sends
that exact request to CM. CM returns a durable result reference to Root, which
returns it to EM for interpretation. EM and CM do not spawn one another.

### 7. Mediate the BrowserTransport singleton

`BrowserTransport` is one logical service with agent type
`hmasd-browser-transport`. Retired provider-specific transport agents are not
active routes. EM or CM authors a frozen durable request and returns
`next_action.owner=TRANSPORT` plus exact request/prompt references to Root; it
does not contact or spawn BrowserTransport directly.

Root validates the requester, direction/stage, provider (`chatgpt` or `gemini`),
mode (`INNOVATOR`, `CONVERGENCE`, `DIVERGENT`, `ENGINEERING`, or `MONITOR`),
operation identity, prompt path/hash, exact response path, model requirement,
authorization, and commitment state. Root then serializes the request through
the singleton and returns the resulting common v1 transport fact to the exact
requester. BrowserTransport performs transport only and never interprets owner
content, changes lifecycle, writes Portfolio/EM/CM state, or selects follow-up.

One strict operation sends at most once. `COMMITMENT_UNKNOWN` never resends.
Provider conversation, operation, tab, OMP assignment, and direction identities
remain distinct. Root validates exact returned archive bytes without rewriting
foreign content or treating an archive as scientific acceptance.

### 8. Schedule resources and liveness

Separate scientific qualification from resource scheduling. Missing command
estimates create CM preparation work and never deactivate a direction. Queue
exact commands within safe workstation capacity when estimated at most 7200
seconds. Above 7200 seconds, attempt a performance-reasonableness review and
request explicit user approval for the exact command. Unsafe memory is refused
mechanically and reduced, batched, or sharded.

Keep the task tree at two levels: Root → EM/CM → specialist. EM and CM are the
only spawn-capable project managers; specialists are leaves. There is no
Portfolio agent, workflow-designer, or design-reviewer role. The ordinary worker
target is 28, preserving four Root/review/recovery slots, but capacity is not a
scientific quota.

Wait through Hub on completion, process exit, an observed file change, or one
bounded reassessment. Material transitions are event-driven, never timer-driven;
do not continuously poll or manufacture a successor because output is delayed.

### 9. Checkpoint, integrate, and recover

A completed research or engineering round, accepted-result promotion,
terminal-run evidence promotion, external prompt/archive readiness, a Portfolio lifecycle change,
or schema migration is a material checkpoint. Direction EM
and CM managers use their provisioned worktrees and the Git integration contract
to stage exact assignment-owned paths and apply/push one direction/kind-owned
cycle candidate to `omp/workflow` as `em:<direction>` or `cm:<direction>`.

Root integrates only Root/shared authorities, cross-direction Portfolio work,
control-plane/schema changes, external archive promotion, and recovery. Every
writer uses an exact path allowlist, never `git add -A`, and leaves unrelated
user changes unstaged. Before push, fetch and compare the remote tip. Stale base,
dirty target, non-fast-forward, mixed ownership, or conflict stops unchanged and
is reported; an unknown push outcome is fetched before any retry and never
blindly pushed again.

On observed inconsistency, Root may dispatch only the OMP
`hmasd-workflow-recovery-manager`. Apply one safe recovery route without
inventing science, replaying an unknown Run, resending an unknown external
operation, bypassing CAS, or treating recovery as approval. Stop only at `IDLE`,
`COMPLETE`, an explicit user decision request, or an exhausted safe recovery
result.

One wake has one reconciliation pass and at most one bounded reassessment. A new
material event starts another bounded cycle.

## State writes

- Write lifecycle reasons, considered-set actions, capacity, and cross-direction
  synthesis only to `PORTFOLIO.md`.
- Replace `registry.json` only through `scripts/hmasd_state.py` with expected
  revision and writer `Portfolio`; never hand-edit durable JSON.
- Write Root-owned `.omp/runtime/agents.json` and
  `.omp/runtime/worktrees.json` only through the state CLI with expected
  revision. Runtime maps describe OMP execution; they do not grant role,
  scientific, lifecycle, or Git authority.
- Invoke documented worktree, run, external-review, and Git CLIs. Do not import
  private functions or duplicate their state writers.
- Do not write direction research/engineering state, Agentify ledgers, or run
  manifests. Root may validate and promote exact external archives and create or
  integrate one verified Root/shared candidate on `omp/workflow` under the Git
  contract.

## Returned result envelope

Return the common v1 envelope with `role: "root"`, logical identity `Root`, and
payload kind `root` for ordinary reconciliation. When the cycle adopts or
reassesses Portfolio allocation or lifecycle, return payload kind `portfolio`
with one structured action for every fixed-set direction, the capacity action,
exact Portfolio reference, and registry revision. The payload remains Root-owned.

```json
{
  "schema_version": 1,
  "role": "root",
  "logical_identity": "Root",
  "generation": 1,
  "assignment_id": "<wake-id>",
  "status": "COMPLETED",
  "materiality": "PORTFOLIO",
  "summary": "<observed reconciliation and allocation outcome>",
  "changed_paths": [],
  "state_refs": [],
  "artifact_refs": [],
  "checkpoint_sha": null,
  "decision_requests": [],
  "next_action": null,
  "payload": {
    "kind": "portfolio",
    "direction_actions": [],
    "capacity_action": {
      "action": "NONE",
      "direction_id": null,
      "decision_ref": null
    },
    "portfolio_ref": "docs/research/portfolio/PORTFOLIO.md",
    "registry_revision": 1
  }
}
```

Use `PARTIAL`, `BLOCKED`, or `FAILED` only for the observed condition. A user
decision request binds the exact direction, Run, or operation and frozen
references; Advisor, review, Dashboard, hash, and historical output are not
approval tokens.

## Failure handling

Re-read the authoritative source and classify the failure before acting.
Preserve exact bytes on stale revision or unsupported schema and record only a
materially distinct recovery attempt. Never replay an unknown Run or external
send, accept late output against a newer checkpoint, silently reinterpret
scientific/engineering/transport/Git facts, manufacture lifecycle states,
activate weak work for a quota, or turn missing resource information into a
scientific veto. A missing estimate requires an estimate-producing next action.
A `PARKED` direction without `reactivation_condition_ref`, an `ACTIVE` direction
without live work or exact reentry, an action missing for a fixed-set direction,
or new Effects while `PAUSED` is a control-plane conflict, not permission to
continue. If no safe route remains, return the precise user blocker and stop.

## Deletion condition

Delete this Skill when Root no longer owns durable Portfolio selection,
lifecycle, active refill, resource attention, routing/runtime reconciliation,
BrowserTransport mediation, direct EM/CM dispatch, shared Git integration, and
OMP recovery, and an approved replacement preserves those authorities without
introducing a Portfolio agent, a second scheduler, or meaning conflation.

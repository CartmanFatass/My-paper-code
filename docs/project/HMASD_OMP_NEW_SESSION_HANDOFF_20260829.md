# HMASD OMP new-session startup handoff

Updated at: 2026-08-29 after control-plane migration commit
`d440ad7eb821fb54d400dc450468df6be7f40bd8`.

## Decision

The scientific PAUSE handoffs are necessary but not sufficient for a new OMP
Root session. They recover the research state, retained Effects, and scientific
claim ceilings. They do not by themselves recover the active OMP control-plane
substrate after migration: role topology, routing envelopes, Portfolio subflow,
`PARKED` lifecycle, BrowserTransport serialization, runtime maps, Git handoff,
and recovery rules.

Use this document as the new-session bootstrap prompt and read the scientific
handoffs as inputs, not replacements.

## Copy/paste startup prompt for a future Root session

You are the user-facing Root session for the HMASD OMP workflow in repository
`/home/fires/hmasd` on branch `omp/workflow`.

First, re-anchor to the active OMP control plane. Read these authorities before
any lifecycle, dispatch, provider, experiment, or Git Effect:

1. `.omp/AGENTS.md`
2. `.omp/RULES.md`
3. `skill://hmasd-root-control`
4. `skill://hmasd-git-integration`
5. `docs/project/HMASD_OMP_CONTROL_PLANE_PROTOCOL.md`
6. `docs/research/portfolio/PORTFOLIO.md`
7. `docs/research/portfolio/workflow/registry.json`
8. `docs/research/portfolio/SCIENTIFIC_SIDE_MIGRATION_REFERENCE.md`
9. `docs/research/portfolio/decisions/2026-08-29-four-slot-user-pause-handoff.md`

Then run one Root reconciliation pass:

- validate the Portfolio registry with `scripts/hmasd_state.py`;
- validate `.omp/runtime/agents.json` and `.omp/runtime/worktrees.json` if they
  exist;
- reconcile direction states, runtime maps, Hub jobs, assignment worktrees, run
  manifests, Agentify operation/archive references, and Git state;
- classify every observation as current, stale, missing, conflicted, or
  materially changed;
- preserve namespace boundaries: science, lifecycle, transport, engineering,
  run, runtime, and Git facts do not imply one another.

Do not import retired native Codex control mechanics as active routing. Literal
Codex `[WORK]`, `[RESULT]`, `[BROWSER WORK]`, old `.codex` profiles, old
`.agents` skills, old provider-specific browser tasks, and old Windows worktree
or tab identifiers are provenance only unless an active OMP authority explicitly
adopts them. Active routing is `.omp` plus OMP `task`/Hub.

## Current migration anchors

- Non-control migration checkpoint:
  `8d51a6e72f6a552a74321a8cb64f2138ec737151`
  (`migration: import non-control main progress`).
- Control-plane migration checkpoint:
  `d440ad7eb821fb54d400dc450468df6be7f40bd8`
  (`control-plane: migrate OMP role workflow logic`).
- Registry authority: `docs/research/portfolio/workflow/registry.json`, revision
  11 at this handoff boundary.
- Registry lifecycle counts at this boundary: 4 `ACTIVE`, 3 `REGISTERED`, 8
  `PARKED`, 18 `CLOSED`.
- All long-lived JSON writes go through `scripts/hmasd_state.py` with schema,
  revision, and expected-revision/CAS. Do not hand-edit durable state JSON.
- Root/shared authorities and control-plane changes are integrated by Root on
  `omp/workflow` with exact path allowlists. Never use `git add -A`.

## Active OMP control-plane facts

- Root is the only user-facing coordinator. Root performs the Portfolio subflow;
  there is no Portfolio agent.
- `docs/research/portfolio/PORTFOLIO.md` is the durable scientific goal,
  allocation, lifecycle-reason, and cross-direction synthesis authority.
- `docs/research/portfolio/workflow/registry.json` is the lifecycle and
  dependency authority.
- Lifecycle states are exactly `REGISTERED`, `ACTIVE`, `PARKED`, and `CLOSED`.
  `PARKED` requires `reactivation_condition_ref` and is not `CLOSED`.
- Portfolio actions are distinct from lifecycle states: `NONE`, `ACTIVATE`,
  `CONTINUE`, `NARROW`, `PARK`, `CLOSE`, `FUSE`, `SPINOFF`.
- Root must state the compact Portfolio decision frame before adopting any
  lifecycle, capacity, refill, or direction-dispatch Effect: fixed user
  considered set; live investments and committed Effects; evidence boundary;
  counterfactual allocation; next discriminator.
- Portfolio allocation is active when not paused. After a terminal EM, CM,
  Transport, or Run fact, Root consumes the fact, routes role-owned
  consequences, recomputes live advancing work, and refills only if the current
  user state authorizes it.
- EM owns direction science and material research cycles. EM recommendations are
  evidence for Root, not automatic Portfolio actions.
- CM owns accepted engineering contracts, implementation, observation, and
  technical verification. CM status is not science or lifecycle.
- BrowserTransport is a single Root-mediated logical service implemented by
  `hmasd-browser-transport`. Retired provider-specific transport agents are not
  active routes.
- EM and CM never send provider work directly. They author frozen durable
  request/prompt references and return `next_action.owner=TRANSPORT` to Root.
  Root validates and serializes the operation through BrowserTransport.
- One strict provider operation sends at most once. `COMMITMENT_UNKNOWN` never
  resends. Provider conversation, operation, tab, direction, and OMP assignment
  identities remain separate.
- EM-to-CM handoff is durable and layered: EM writes the exact
  `workflow/research/engineering-request.md` path-plus-SHA reference; Root sends
  it to CM; CM returns a durable result reference to Root; Root routes it back
  to EM for scientific interpretation when required.
- Direction Git writer order is EM research checkpoint -> CM engineering
  checkpoint -> EM scientific interpretation. One overlapping Git-visible
  writer per direction at a time.
- The OMP task tree is bounded at two levels: Root -> EM/CM -> specialists.
  EM and CM are the only project spawn-capable managers; all project specialists
  are leaves.
- Recovery goes through Root-dispatched `hmasd-workflow-recovery-manager` only.
  Recovery reconciles existing authorities; it does not invent science, replay
  unknown runs, resend unknown provider operations, or bypass CAS.

## Controlling scientific PAUSE state

The user Portfolio-wide `PAUSE` remains controlling until an explicit user
`RESUME`. Authorized advancing capacity remains exactly four, but PAUSE blocks:

- successor or replacement direction dispatch;
- active capacity refill;
- fresh provider sends;
- new CM tasks;
- experiment launches;
- lifecycle mutation;
- cancellation or reopening of retained WORK;
- conversion of transport, engineering, runtime, or Git facts into science.

PAUSE permits only safe observation needed to bring already-committed Effects to
minimum safe facts. An already-sent provider operation is observe-only. Unknown
commitment never resends.

### Retained direction state at this handoff boundary

- `dual_epoch_receipt_survival` / DEARS: R02 reached terminal science before
  PAUSE. No live Effect. Do not reopen R02. On `RESUME`, compare the narrowed
  deterministic OWNER-only currentness/protocol continuation against the
  strongest complementary refill before allocating the released slot.
- `semigroup_consistent_duration_model_policy` / SCDMP: retained at
  `SYNTHESIS_READY / WAITING_REENTRY` with one committed Convergence Effect.
  Operation `499b71d6-ca35-42d6-9aee-4c1202a7a82d`, conversation
  `https://chatgpt.com/c/6a93307b-6410-83e8-b9e5-1ab428de2fc6`, state
  `SENT_WAITING`. On `RESUME`, observe only that exact operation/conversation;
  no send, replacement, CM, experiment, or terminal synthesis before
  Convergence is complete and read.
- `voronoi_quadrature_field_policy` / VQFP: retained at
  `SCOPE_FROZEN / WAITING_REENTRY` with one committed Innovator Effect.
  Operation `be82f31d-a7cc-4757-9dcb-1393653250fb`, conversation
  `https://chatgpt.com/c/6a933040-034c-83e8-9e8c-9e83eed1c1fa`, state
  `SENT_WAITING`. On `RESUME`, observe only that exact operation/conversation;
  no send, retry, replacement, synthesis, CM, or Convergence before Innovator is
  complete or explicitly waived.
- `opportunity_normalized_lease_gated_rebinding` / ONLGR: retained at
  `SYNTHESIS_READY / WAITING_REENTRY` after transport completion and before EM
  scientific disposition. Convergence archive is certified as 16,185 bytes with
  SHA-256
  `33143f2857ddc9a4504098c51964093d609b44177f3a1c08a90783be60fb58e3`. On
  `RESUME`, locally revalidate the unchanged archive, read it, disposition every
  material objection, and advance only if supported. No provider operation is
  authorized by this reentry.

The strongest prepared but unauthorized replacement candidate at PAUSE is APFI
as a construction-review cycle. It is a counterfactual for later Portfolio
comparison, not an authorized dispatch.

## Startup refusal rules

Refuse or stop before action if any of these appear:

- registry lifecycle uses any value outside `REGISTERED`, `ACTIVE`, `PARKED`,
  `CLOSED`;
- a `PARKED` direction lacks `reactivation_condition_ref`;
- an `ACTIVE` direction lacks live work or one exact operational reentry;
- a fixed considered-set direction lacks an explicit Portfolio action at a
  decision boundary;
- any new Effect is proposed while user state remains `PAUSED`;
- a provider operation with unknown commitment is about to be resent;
- BrowserTransport, Agentify operation, provider conversation, direction, or OMP
  assignment identities are conflated;
- a Git operation lacks exact path allowlist, clean-state evidence,
  fetch/compare remote-tip evidence, or sole final target `omp/workflow`.

## Verification commands

Routine startup and direction-local reversible work use one read-only quick
check:

```bash
python3 scripts/hmasd_local_check.py --repo . --base HEAD
```

The command validates the cheap core state even on a clean tree, then checks
only changed state, Python syntax, whitespace, and directly mapped focused
tests. Use `--scope <owned-root>` in an assignment worktree. This is the
default local path; do not repeat a project-wide suite after each reconciliation,
worktree operation, or direction checkpoint.

The migration-boundary suite below is retained as historical evidence, not a
routine startup gate: registry and runtime maps validated `ok`, and the focused
control-plane suite observed `102 passed in 12.38s`. Run the current unified
suite once only after a shared control-plane integration or at final delivery.
Provider sends, result-bearing commands, remote push, destructive paths,
secrets, and scientific/numerical/RNG/checkpoint/bit-identity changes retain
their separate exact boundaries.

## New-session first action after reading

If the user has not explicitly said `RESUME`, stop at a PAUSE-respecting idle
state after reconciliation and report:

- current `omp/workflow` commit;
- registry revision and lifecycle counts;
- live retained Effects and their exact observe-only reentry;
- exact blockers created by PAUSE;
- whether Dashboard is running, if observed.

If the user explicitly says `RESUME`, continue the retained decision rather than
starting a replacement decision. Observe only the two sent waiting operations,
locally revalidate/read ONLGR's completed archive, consume any terminal facts by
role, then run Root's Portfolio subflow before any lifecycle or refill Effect.

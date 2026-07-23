# HA-CTSE Current Work

Updated: 2026-07-23

## Ownership

- Workspace: `C:\Projects\My-paper-code`
- Branch: `Claude`
- **Controller: current OMP root task.** `AGENTS.md` is its operating contract.
- **Execution mode: unified OMP Controller with project-local task agents.**
  There is no persistent implementation relay or legacy native-agent fallback.
- Scientific direction comes from the external GPT-5.6 Pro conversation
  registered in `REVIEWER_CONVERSATIONS.json`. The Controller owns BrowserMCP
  submission/capture, evidence intake, executable planning, local-agent
  coordination, package acceptance, Git and project control. One project-local
  Spark task may observe Pro completion through wait/snapshot only.
- The registered native Experiment Monitor is task
  `019f8a2f-08a2-73e1-b539-2dc5a6db0fc1`; it observes one already-authorized
  run and must resolve as `gpt-5.3-codex-spark` at `medium` before assignment.

## Active Boundary

The bounded autonomous research chain is active under the user's 2026-07-23
grant for exactly five conclusion-bearing iterations. The Controller advances
accepted results through external-Pro review, direct CDC intake, project-local
OMP work, Git and terminal evidence integration without intermediate approval.
One iteration is consumed only by a conclusion-bearing scientific action.
Formal compute still requires one exact Controller-authorized run.

The obsolete external WIP is not an execution surface. Its useful symbols were
audited and adapted into the accepted native package; no formal experiment was
launched from it.

The project-local OMP child registry lives under `.omp/agents/`. Its exact
callable types are `hmasd-code-scout`, `hmasd-implementer`,
`hmasd-verifier`, `hmasd-reviewer`, `hmasd-exp-manager` and
`hmasd-pro-monitor`; bundled/default fallback is forbidden. Children are depth
one and cannot spawn successors.

## Role configuration

Mechanical exploration and verification use GPT-5.6 Luna at high reasoning.
Core implementation uses GPT-5.6 Sol at high reasoning and independent core
review uses Sol at xhigh. Experiment monitoring uses GPT-5.3 Codex Spark at
medium; experiment evidence and record work uses Spark at high. Pro response
completion observation uses Spark at medium with BrowserMCP wait/snapshot only.
External review uses the pinned `browsermcp-pro` server and the user-connected
ChatGPT Pro tab
registered in `REVIEWER_CONVERSATIONS.json`. The evidence repository is
`CartmanFatass/My-paper-code` and the current review branch is `Claude`.
The restarted long-lived OMP Controller exposes BrowserMCP tools. A read-only
snapshot verified the exact registered conversation URL, authenticated Pro
account and visible `Pro` model; connection state is `CONNECTED_PREFLIGHT_OK`.
The first resumed round is in flight and uses the exact registered-CPU
formal-path smoke failure and accepted Pro raw as scientific inputs. The
Controller submitted the Git-visible question; `hmasd-pro-monitor` may observe
only natural completion and response stability. No headless, CDP or former
Codex-Exchange fallback is authorized.

`EVENT_HELD_COMMITMENT_LINK_G0` launch-readiness work is accepted and integrated
through `31aad0df80d637fd095655bf8c0b112e4bf1cdfd`. Nothing is currently running.
The focused external-Pro clarification returned
`BATTERY_REQUIRES_MINIMAL_CORRECTION`: keep `G` and the three arms, but separate
same-state forced-event timing effects, mark effects, representation influence
and natural selection/support. This coordination consumes no iteration; an
iteration is consumed only by a conclusion-bearing evidence action.

The startup smoke reached the real registered-CPU training/evaluation cores and
failed closed in the production natural-branch audit with
`continuous_error=9.5367431640625e-07`, while discrete action, segment and
outcome equality remained exact. This is operational prelaunch evidence, not a
scientific result or permission to weaken exact causal identity. The synthetic
dense-layer probe and its vacuous permanent test were deleted.

Between 2026-07-21 and 2026-07-22 a Claude Code session held implementation and
`docs/project/` at the user's direction, under a different model: the user held
scientific authority, that session implemented and verified, and GPT-5.6 Pro
reviewed science through the GitHub connector. No formal experiment completed, so
no scientific disposition was produced.

## Active Execution Flow

- Controller: receives the scientific decision, freezes the executable plan,
  writes every bounded child assignment, integrates returned work, independently
  verifies it, owns Git and updates project control.
- Scout: one bounded read-only interface map when immediate code boundaries are
  genuinely unknown.
- Implementer: one frozen write scope; no science, Git, project-control or
  successor authority.
- Verifier and Reviewer: independent evidence and audit over one stable
  integrated package; they may run in parallel because neither edits source.
- Exp Manager: applies only Controller-frozen factual experiment transitions and
  record deltas; it never interprets results, changes science or starts runs.
- Experiment Monitor: observes one already-authorized run and returns its
  authoritative terminal paths without mutation or interpretation.

## Execution Flow (historical — Claude Code session, 2026-07-21/22)

Recorded for reference. Codex uses `AGENTS.md` and `.agents/skills/`. That
session executed work through bounded subagents under a single orchestrator.

- Orchestrator: writes the frozen plan, dispatches, integrates the result,
  reruns the focused suite itself, commits and maintains `docs/project/`. A
  subagent's own claim that tests pass is never accepted as evidence.
- Implementer: one bounded task against a frozen plan, receiving the plan, the
  exact file scope, the acceptance criteria and the execution-environment
  facts. It receives no research context and holds no Git authority.
- Reviewer: a separate read-only spawn with fresh context that audits the diff
  against the plan and returns findings without editing. A review pass is
  mandatory before committing any change touching protected semantics, meaning
  probability factorization, gradients and detach boundaries, RNG stream
  ownership, replay, lifecycle clocks, credit assignment, masks and checkpoint
  meaning.
- Mechanical work such as inventories, search sweeps, log scraping and
  packaging is delegated to a low-cost tier and never touches algorithm
  semantics.

One writer holds a given file set at a time. Concurrent mutating tasks on the
same scope are not dispatched.

## Binding Engineering Constraints

These are durable technical constraints, not workflow. They bind algorithm
realization and are carried by the current implementation plan and the
Controller's local OMP task tree. Experiment observation follows the registered
native Monitor Skill.

The load-bearing consequences:

- Environment, member, **branch**, skill, **replica** and evaluation dimensions
  are all batched through the existing tensor path. Loops are retained only for
  genuine causal, autoregressive, simulator or recurrent dependence.
- Batched inference is reused for evaluation, controls, **forced branches**,
  replicas and audits whenever the estimand and RNG contract permit. A
  counterfactual fork is a forced branch and is batched by default.
- Replicate concurrency is achieved by batching the replica dimension inside one
  known-good process and device topology. Spawning one process per replicate
  creates duplicate runtime contexts and is explicitly rejected.
- Intended RNG independence, common-random-number coupling and exact checkpoint
  continuation are preserved.
- Rollout data is packed and transferred once per collection boundary and reused
  across optimizer passes; metrics synchronize only at real control boundaries.
- Conclusion-bearing runners expose stage-level wall time sufficient to locate
  order-of-magnitude regressions.
- Before returning any change, the end-to-end changed path is inspected once for
  scalar device work, repeated packing or transfer, premature synchronization,
  recurrent leakage, replay mismatch, RNG drift, excessive persistence and
  **serial evaluation**.
- Performance structure is reviewed as code quality, not as a separate gate. An
  observed issue is fixed once; no speculative optimization loop is created.

Local testing assumes 16 parallel environments, matching `FORMAL_NUM_ENVS`.
Batch sizing for new work is expressed in units of that width.

Handoff note: the prior Codex controller task
`019f5c78-0c91-7612-adb4-c1fcfe4484c8` left the
`EVENT_HELD_COMMITMENT_LINK_G0` implementation complete but uncommitted. It was
verified and committed under the ownership above.

## Last Scientific Boundary (paused)

The independent `NONCALENDAR_HETEROGENEOUS_TRACKING_G0` benchmark qualification
is valid `NO_ACCESS_BENCHMARK_ORDINARY_CONTROL`. H establishes structural
reachability, C the current-demand/error information null, S the cost of one
shared four-step renewal restriction, and D partial causal learning without
ordinary access. It does not establish hierarchy, learned skills or learned
heterogeneous lifetime.

The prior external clarification selected
`D0_D1_CAUSAL_OBSERVATION_REFACTOR_G0`, but the controller retracted that route
before implementation or compute. It inverted the research objective by making
ordinary-controller access a prerequisite for developing the hierarchy,
skills and variable-lifetime mechanisms whose purpose is to build a stronger
MARL algorithm. That raw remains historical reviewer evidence; its route is not
active authority.

Prior convergence work produced the controller-adopted
`EVENT_HELD_COMMITMENT_LINK_G0`. It isolates one treatment: whether an
event-held commitment reaches primitive action logits. Ordinary recurrent `OR`
is the full-algorithm comparator; `DUM` and `EHC` have identical commitment
state, capacity, event learning and optimizer exposure, while only `EHC`
enables the commitment-to-action link. The execution, probability, replay,
lifecycle, checkpoint, experiment and mutually exclusive result contracts are
frozen in the durable design. No formal experiment is authorized until
implementation and focused review complete.

## Implementation State

`EVENT_HELD_COMMITMENT_LINK_G0` is implemented, reviewed and committed through
`31aad0df80d637fd095655bf8c0b112e4bf1cdfd` on `aggressive`. The final replay
repair made collection and teacher replay share one row-stable float32
event/mark-head evaluator without changing probability, replay thresholds,
RNG, gradients, schemas, budgets or scientific meaning.
The three-arm package, the revised behavioural battery, Replacement C stage 1
retention, the sequential counterfactual fork engine, the per-factor replay
tolerance classes and the registered execution backend and result gates are all
in history.

**Formal training attempts were operationally aborted. Nothing is running and
no usable formal checkpoint exists.** The first attempt died at update 4 on a
replay record merged across arms, fixed at `e80cef0`. The second died mid-
training on a flat absolute per-component replay tolerance that cannot be
executed in float32, because four of the nine bounded quantities have unbounded
magnitude. A subsequent retry exposed the collection/replay arithmetic split;
that defect is closed by `31aad0df`. None of these attempts is scientific
evidence.

## Resume Point

The intended branch is `Claude`; the visible startup working tree, exact
project-local OMP agent registry, HMASD-only Skill allowlist, BrowserMCP
conversation and current implementation plan have been inspected. The
registered Monitor route check failed closed because task
`019f8a2f-08a2-73e1-b539-2dc5a6db0fc1` is archived. External review,
derivation, evidence reanalysis and local code work may proceed; no formal run
or monitor assignment may start until the Controller rebuilds the registered
Spark-medium Monitor and atomically updates the role registry. No fallback
Monitor is authorized.

## Open Contract Questions

One unresolved question stands against the result contract, raised before any
result was observed and therefore not a post-hoc threshold rescue. It is
recorded here because `ALGORITHM_PRINCIPLES.md` is reserved for generalized
rules and this is specific to the active source.

`ALGORITHM_PRINCIPLES.md` 2.3 requires that a long-lived skill arise from
learned behavior under the declared clock contract. The lifetime gate
`LCB(CV(T))>0.25` appears to be satisfied by construction. `Delta` is sampled
uniformly from `{4,8,12}` and the policy selects only `KEEP`/`RENEW`, so a
segment lifetime is a Geometric-count sum of `Delta` draws with
`Var(Delta)/E[Delta]^2 = (32/3)/64`. That yields `CV(T)=0.408` under always-
`RENEW` and `0.764` under a balanced policy, so every policy including an
untrained one clears `0.25`. The lifetime-bin condition appears similarly
satisfiable.

Two related observations. The natural-use gates are non-degeneracy checks,
since the support is binary and `P_KEEP+P_RENEW=1`, so a uniform random event
head clears both; principle 2.2 holds that usage statistics are not evidence of
a useful skill. The intervention gate measures logit-perturbation magnitude
rather than behavioral consequence, so a large `W_z` applied to an
uninformative `z` clears it.

The primary estimand `G` is unaffected and remains mechanism-matched. The
question is whether the behavioral battery discriminates the
`COMMITMENT_SUPPORTED` and `REPRESENTATION_ONLY` branches at all. One candidate
replacement conditions on the `KEEP`-chain length, which is purely
policy-determined, instead of realized lifetime, which is dominated by the
`Delta` draw. This is referred to the user and GPT-5.6 Pro; no threshold is
changed here.

## Measured Compute Cost

Registered `16 x 80` four-epoch update on the local RTX 4070: 8.61s for `OR`,
8.14s for `DUM`, 8.18s for `EHC`. Serial formal training over 250 updates,
three arms and five replicates is 8.65h, and the four evaluation cells add
roughly 1 to 1.5h, for about 10h continuous.

Throughput is Python-loop and kernel-launch bound rather than compute bound at
roughly 160 transitions/s for a 15k-parameter model, so the GPU stays nearly
idle. The 15 `(arm, replicate)` cells are independent.

An earlier proposal to run those cells as concurrent processes is **withdrawn**:
it would create duplicate CUDA contexts, which the binding engineering
constraints reject. The correct form is to batch the replica dimension inside
one process and device topology, alongside the environment dimension already
batched at width 16.

## Local Execution Environment

Focused tests and smoke checks fail closed when the registered backend is
unavailable. Use `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`
directly (Python 3.10.20, `torch 2.7.0+cpu`); this host has no CUDA and the
registered backend is `cpu`, not a fallback. The default `python` is a Windows
Store stub. Never use `conda run`.

## Autonomous Boundary

**ACTIVE_AUTONOMOUS_RESEARCH_CHAIN.** Exactly five conclusion-bearing iteration
slots are authorized and unconsumed. The Controller automatically continues
between external-Pro decisions, direct evidence intake, bounded local OMP work,
Git integration and the next already-authorized action without asking for
intermediate approval. Stop only after five conclusion-bearing iterations, a
genuine blocker, or a requested expansion of protected scientific or formal
compute authority. Formal execution and Monitor assignment still require one
specific Controller-authorized run.

## Durable Constraints

- Active research line: implementation exists only for the current hypothesis's
  shortest discriminating observation; do not build a general platform.
- Clean cutover: when a replacement is accepted, delete the old interface,
  adapter, migration path and invalid test; Git history is the archive.
- Lightweight tests: retain only hypothesis-separating checks, key algorithm
  invariants and prevention of an observed real recurrence.

- Target capability: one shared algorithm with runtime-variable team membership
  and variable individual skill lifetime.
- Preserve the ordinary recurrent direct learner as the access null.
- Intrinsic reward remains environment-agnostic: no task field, identity, role,
  success predicate, progress measure, or external reward may enter it.
- R41B is the positive fixed-`N` source anchor. Retired mechanisms and old
  carriers are evidence, not executable dependencies.
- Do not rescue a valid failure by changing budget, seed, threshold, reward,
  model, task, skill count, or carrier under the same claim.
- Active-line development applies; no backward-compatibility or legacy path is
  required.

## Pointers

- `docs/project/ALGORITHM_PRINCIPLES.md` — durable scientific constraints.
- `docs/project/IMPLEMENTATION_PLAN.md` — current frozen executable design, or
  explicit `NONE` when no implementation is authorized.
- `docs/project/ExpRecord.md` — formal experiment history and dispositions. It
  carries no `EVENT_HELD_COMMITMENT_LINK_G0` row, correctly, because no formal
  experiment has been authorized or run.
- `docs/external-review/gpt5_6_pro/20260721_event_held_commitment_link_g0_code_review/`
  — active implementation review package awaiting `RESPONSE_RAW.md`.
- `docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md` — current adopted
  scientific and executable source.
- `docs/external-review/rounds/20260719_clean_process_access_portfolio/`
  — completed review evidence and accepted `50_DISPOSITION.md`.
- `docs/external-review/rounds/20260720_noncalendar_g0_no_access_portfolio/`
  — completed G0 no-access portfolio and accepted evidence boundary.
- `docs/external-review/rounds/20260720_noncalendar_g0_direct_access_clarification/`
  — immutable clarification raw plus retracted objective-inverting disposition.
- `docs/external-review/rounds/20260720_event_held_commitment_replay_statistical_finalization/`
  — final focused raw and controller non-adoption record; no code or experiment
  handoff.
